# Performance & Cost Diagnosis

Telemetry-driven root-causing for "training through the mount is slow" and "the
GCS bill spiked after we mounted the bucket". The core insight: **the default
mount is coherency-tuned, not performance-tuned** — most regressions on untuned
mounts are the defaults doing exactly what they promise.

**Never hypothesize before reading telemetry.** If client metrics are not
enabled, enabling them is the first remediation step; while waiting for a
remount window, the server-side `storage.googleapis.com/api/request_count`
metric is always available and needs no mount change.

## The coherency-tuned defaults (the usual suspects)

| Knob                           | Default         | Effect on a re-read       |
:                                :                 : workload                  :
| :----------------------------- | :-------------- | :------------------------ |
| File cache (`cache-dir`)       | Off             | Every epoch re-downloads  |
:                                :                 : every byte.               :
| `metadata-cache: ttl-secs`     | 60              | All metadata re-fetched   |
:                                :                 : every minute.             :
| `metadata-cache:               | 34 (~20k files) | Silently evicts on large  |
: stat-cache-max-size-mb`        :                 : file counts → constant    :
:                                :                 : re-stats.                 :
| `metadata-cache:               | 5               | "Not found" results       |
: negative-ttl-secs`             :                 : re-checked every 5 s.     :
| List cache                     | 0 (off)         | Every `ls`/directory walk |
: (`kernel-list-cache-ttl-secs`) :                 : hits the API.             :
| `implicit-dirs`                | false (true in  | When on (flat buckets),   |
:                                : profiles)       : lookups issue extra List  :
:                                :                 : calls.                    :

A ~5M-small-file dataset re-read each epoch against these defaults produces
exactly the classic symptom pair: throughput far below local disk, and an
operations-dominated bill.

## Step 1 — Establish telemetry

| Environment                | How to get client metrics                  |
| :------------------------- | :----------------------------------------- |
| GKE ≥ 1.33.0-gke.2248000   | `gcsfusecsi/*` metrics are in Cloud        |
:                            : Monitoring by default — no action.         :
| Self-managed mount → Cloud | Remount with                               |
: Monitoring                 : `--cloud-metrics-export-interval-secs=60`  :
:                            : (needs `roles/monitoring.metricWriter`;    :
:                            : native metrics are Preview).               :
| Self-managed mount → local | Remount with `--prometheus-port=9920`,     |
: scrape                     : then `curl -s localhost\:9920/metrics`.    :
| No remount possible yet    | Server-side:                               |
:                            : `storage.googleapis.com/api/request_count` :
:                            : grouped by the `method` label.             :

```bash
# Self-managed: remount with metrics, reproduce the workload, then inspect
gcsfuse --prometheus-port=9920 BUCKET /mnt/data
curl -s localhost:9920/metrics | grep -E "file_cache_read_count|gcs_request_count|fs_ops_count"
```

Client metrics only accumulate from mount time — reproduce at least one epoch
(or a representative slice) after enabling before reading the numbers.

Also capture the effective mount configuration (the misconfig surface): the
running `gcsfuse` command line and `--config-file` contents on self-managed
hosts; on GKE, `kubectl get pv PV_NAME -o yaml` (check `spec.mountOptions` and
`spec.csi.volumeAttributes`) plus the pod's `gke-gcsfuse/*` annotations.

## Step 2 — Read the signals

| Metric (Cloud Monitoring / Prometheus form)  | What it tells you             |
| :------------------------------------------- | :---------------------------- |
| `file_cache/read_count`, by `cache_hit`      | Cache hit rate — the headline |
: label                                        : signal.                       :
: (`file_cache_read_count{cache_hit="false"}`) :                               :
| `gcs/request_count` (`gcs_request_count`)    | Requests actually sent to     |
:                                              : Cloud Storage.                :
| `gcs/request_latencies`, `gcs/retry_count`   | Per-request latency and retry |
:                                              : pressure.                     :
| `fs/ops_count` by `fs_op`                    | Operation mix the app drives  |
: (`fs_ops_count{fs_op="LookUpInode"}`)        : (stat-heavy? list-heavy?).    :
| `fs/ops_error_count` by `fs_error_category`  | Errors surfacing to the app.  |
| Server-side `api/request_count` by `method`  | Request mix without any mount |
: (e.g. `ReadObject`)                          : change; also the bridge to    :
:                                              : billing.                      :

On GKE the same client metrics appear prefixed and underscored:
`gcsfusecsi/file_cache_read_count`, `gcsfusecsi/gcs_request_count`,
`gcsfusecsi/fs_ops_count`, etc.

## Step 3 — Map the signature to the misconfiguration

| Signature               | Root cause          | Fix (exact keys)             |
| :---------------------- | :------------------ | :--------------------------- |
| `cache_hit="false"` on  | File cache off (no  | `cache-dir` + `file-cache:   |
: ~all reads; download    : `cache-dir`) or     : max-size-mb` sized to the    :
: volume ≈ dataset ×      : undersized          : dataset (`-1` = fill the     :
: epochs                  :                     : cache dir). Parallel         :
:                         :                     : downloads auto-enable with   :
:                         :                     : the cache.                   :
| Stat/metadata-dominated | 60 s TTL expiring + | `metadata-cache: ttl-secs:   |
: request mix;            : 34 MiB stat cache   : -1` and                      :
: `fs_ops_count`          : (~20k entries)      : `stat-cache-max-size-mb\:    :
: LookUpInode-heavy;      : thrashing against a : -1` - **immutable data       :
: slowness scales with    : large file count    : only**; budget ~1.5 GiB RAM  :
: file count              :                     : per million files (~1,720    :
:                         :                     : bytes/file). Scope with      :
:                         :                     : `only-dir` if only a subset  :
:                         :                     : of the bucket is needed.     :
| List-dominated mix      | List cache off; or  | `file-system:                |
: (`objects.list` /       : `implicit-dirs` on  : kernel-list-cache-ttl-secs\: :
: ListObjects methods);   : a flat bucket       : -1` - **read-only mounts     :
: directory walks slow    : adding List calls   : only**; prefer HNS buckets   :
:                         : per lookup          : over `implicit-dirs`.        :
| Sidecar OOMKilled       | Sidecar memory or   | Leave limits unset (default  |
: (Exit 137) or severe    : CPU limits set too  : "0" on GKE ≥ 1.29.1); or set :
: CPU throttling during   : low on GKE          : memory limit > stat/file     :
: reads                   :                     : cache budget.                :

Attribution logic for the bill: no file cache → every epoch re-reads all objects
(`objects.get`, Class B, billed per operation); expiring metadata + evicting
stat cache → re-stats (`objects.get` metadata, Class B); list cache off /
implicit-dirs → repeated `objects.list` (Class A, ~12.5× the per-op price of
Class B on standard buckets). Deletes are free.

## Step 4 — Apply the fix

```yaml
# tuned.yaml - read-heavy, immutable dataset re-read across epochs
cache-dir: /mnt/local-ssd/gcsfuse-cache
file-cache:
  max-size-mb: -1              # or size to the dataset
metadata-cache:
  ttl-secs: -1                 # immutable data only
  stat-cache-max-size-mb: -1   # ~1.5 GiB RAM per 1M files
file-system:
  kernel-list-cache-ttl-secs: -1   # read-only mounts only
# only-dir: dataset/train      # optional: scope namespace on 10M+ object buckets
```

```bash
gcsfuse --config-file=tuned.yaml BUCKET /mnt/data
```

> [!WARNING]
> **Staleness trade-off:** `-1` TTLs mean this mount never sees
> changes made to the bucket by other clients. Apply only to data that is
> immutable for the life of the mount, and prefer mounting read-only (`-o ro`).
> If the bucket is mutable, size TTLs to the acceptable staleness window
> instead.

Config hygiene while editing: `metadata-cache: type-cache-max-size-mb` is a
no-op since v3.8.0 (type cache merged into stat cache) — delete it from any
config that still sets it. On GKE, apply the same keys as PV `mountOptions`
entries (`file-cache:max-size-mb:...` colon syntax) — see
[GKE Training Deployment](gke-training-deployment.md). On Rapid (zonal) buckets
the file cache and buffered reads are no-ops by default (the kernel read path
replaces them) — this runbook's cache fixes apply to standard buckets.

## Step 5 — Verify and state the expected billing delta

Re-run one epoch, then check:

-   `file_cache_read_count{cache_hit="true"}` ≈ 100% of reads from epoch 2
    onward (first epoch populates the cache).
-   `gcs/request_count` drops to roughly one GET per object per mount lifetime
    (plus the initial listing) instead of per epoch.
-   On the bill: the **Class B line** (`objects.get` — data reads and metadata
    stats) drops roughly in proportion to the former epoch count; the **Class A
    line** (`objects.list`) drops if list caching or HNS addressed a list-heavy
    signature. Confirm server-side with `api/request_count` by `method`
    before/after.

## Documentation

-   [Cloud Storage FUSE metrics](https://cloud.google.com/storage/docs/cloud-storage-fuse/metrics)
-   [Config file reference](https://cloud.google.com/storage/docs/cloud-storage-fuse/config-file)
-   [File caching](https://cloud.google.com/storage/docs/cloud-storage-fuse/file-caching)
-   [Performance tuning](https://cloud.google.com/storage/docs/cloud-storage-fuse/performance)
-   [Cloud Storage pricing (operation classes)](https://cloud.google.com/storage/pricing)
-   [Google Cloud metrics list (api/request_count)](https://cloud.google.com/monitoring/api/metrics_gcp_p_z)
