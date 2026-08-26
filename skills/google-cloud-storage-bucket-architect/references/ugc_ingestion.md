# Direct User-Generated Content (UGC) Ingestion

This reference document outlines the secure-by-default configuration mapping and
architecture recommendation for Google Cloud Storage buckets receiving direct
client-side uploads from user applications (mobile apps, web browsers, etc.)
bypassing backend servers.

## Description

The user is building a mobile or web application where end-users upload heavy
files (such as profile pictures, documents, or video clips) directly to a Cloud
Storage bucket. This is achieved using Signed URLs to authorize uploads and CORS
configuration to allow browser-based calls, avoiding network bottlenecking on
the application's backend web servers.

## Bucket Configuration Plan Mapping

The following table maps the Direct UGC Ingestion use case to specific Cloud
Storage features and details their recommendation status.

| Feature Group  | Cloud Storage   | Status       | Recommendations & Implementation | Documentation Link                                                                         |
:                : Feature /       :              : Details                          :                                                                                            :
:                : Setting         :              :                                  :                                                                                            :
| :------------- | :-------------- | :----------- | :------------------------------- | :----------------------------------------------------------------------------------------- |
| **Core**       | **Storage       | Highly       | **Autoclass** or **Standard**    | [Autoclass](https://docs.cloud.google.com/storage/docs/autoclass.md.txt)<br>[Storage       |
:                : Class**         : Recommended  : Storage Class.<br><br>Standard   : Classes](https\://docs.cloud.google.com/storage/docs/storage-classes.md.txt)               :
:                :                 :              : storage is recommended if users  :                                                                                            :
:                :                 :              : frequently view uploaded content :                                                                                            :
:                :                 :              : immediately. Autoclass is ideal  :                                                                                            :
:                :                 :              : if files naturally go cold over  :                                                                                            :
:                :                 :              : time, avoiding retrieval fee     :                                                                                            :
:                :                 :              : traps.                           :                                                                                            :
|                | **Bucket Type** | Highly       | **Regional** bucket type. Align  | [Locations](https://docs.cloud.google.com/storage/docs/locations.md.txt)                   |
:                :                 : Recommended  : storage region with application  :                                                                                            :
:                :                 :              : compute to minimize latency.     :                                                                                            :
:                :                 :              : Create multiple regional buckets :                                                                                            :
:                :                 :              : if the user base is globally     :                                                                                            :
:                :                 :              : dispersed.                       :                                                                                            :
| **Serving**    | **Signed URLs** | **Required** | **Use Signed URLs** to delegate  | [Signed                                                                                    |
:                :                 :              : time-limited read/write access   : URLs](https\://docs.cloud.google.com/storage/docs/access-control/signed-urls.md.txt)       :
:                :                 :              : to clients, keeping the bucket   :                                                                                            :
:                :                 :              : secure while offloading traffic  :                                                                                            :
:                :                 :              : from backend servers.            :                                                                                            :
|                | **CORS**        | **Required** | **Configure CORS** to allow web  | [CORS](https://docs.cloud.google.com/storage/docs/using-cors.md.txt)                       |
:                :                 :              : applications hosted on custom    :                                                                                            :
:                :                 :              : domains to perform client-side   :                                                                                            :
:                :                 :              : uploads and load resources       :                                                                                            :
:                :                 :              : directly.                        :                                                                                            :
| **Security**   | **Uniform       | **Required** | **Must be enabled.**             | [Uniform Bucket-Level                                                                      |
:                : Bucket-Level    :              : Standardizes IAM permissions     : Access](https\://docs.cloud.google.com/storage/docs/uniform-bucket-level-access.md.txt)    :
:                : Access (UBLA)** :              : across the bucket, disabling     :                                                                                            :
:                :                 :              : granular legacy ACLs.            :                                                                                            :
|                | **Encryption    | Good to Have | Recommend Customer-Managed       | [CMEK](https://docs.cloud.google.com/storage/docs/encryption/customer-managed-keys.md.txt) |
:                : (CMEK)**        :              : Encryption Keys (CMEK) primarily :                                                                                            :
:                :                 :              : for B2B multi-tenant             :                                                                                            :
:                :                 :              : environments with strict         :                                                                                            :
:                :                 :              : compliance mandates.             :                                                                                            :
|                | **Soft Delete** | Highly       | **Enabled (default 7 days).**    | [Soft Delete](https://docs.cloud.google.com/storage/docs/soft-delete.md.txt)               |
:                :                 : Recommended  : Provides a safety fallback to    :                                                                                            :
:                :                 :              : recover user data from           :                                                                                            :
:                :                 :              : accidental deletions or          :                                                                                            :
:                :                 :              : compromise, without regulatory   :                                                                                            :
:                :                 :              : locking.                         :                                                                                            :
|                | **Object        | Good to Have | Recommend only if users          | [Object Versioning](https://docs.cloud.google.com/storage/docs/object-versioning.md.txt)   |
:                : Versioning**    :              : frequently overwrite files of    :                                                                                            :
:                :                 :              : identical names and              :                                                                                            :
:                :                 :              : collaborative history is needed, :                                                                                            :
:                :                 :              : but govern with strict OLM to    :                                                                                            :
:                :                 :              : control cost.                    :                                                                                            :
|                | **IP            | Good to Have | Restrict admin API endpoints and | [Bucket IP                                                                                 |
:                : Filtering**     :              : internal export operations to    : Filtering](https\://docs.cloud.google.com/storage/docs/ip-filtering-overview.md.txt)       :
:                :                 :              : trusted NAT IPs.                 :                                                                                            :
| **Cost**       | **Object        | Highly       | **Enable                         | [Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle.md.txt)        |
:                : Lifecycle       : Recommended  : abortIncompleteMultipartUpload** :                                                                                            :
:                : Management      :              : to clean up abandoned,           :                                                                                            :
:                : (OLM)**         :              : incomplete client uploads. If    :                                                                                            :
:                :                 :              : Autoclass is disabled,           :                                                                                            :
:                :                 :              : automatically transition older,  :                                                                                            :
:                :                 :              : unaccessed user data to standard :                                                                                            :
:                :                 :              : cold classes (e.g., transition   :                                                                                            :
:                :                 :              : to `ARCHIVE` after 365 days).    :                                                                                            :
| **Management** | **Labels &      | Good to Have | Apply organizational metadata    | [Bucket Labels](https://docs.cloud.google.com/storage/docs/using-bucket-labels.md.txt)     |
:                : Tagging**       :              : tags (e.g. `{"data-class"\:      :                                                                                            :
:                :                 :              : "ugc"}`) to classify files.      :                                                                                            :
|                | **Storage       | Good to Have | Use Storage Insights Inventory   | [Inventory                                                                                 |
:                : Intelligence**  :              : Reports to track upload scales,  : Reports](https\://docs.cloud.google.com/storage/docs/insights/inventory-reports.md.txt)    :
:                :                 :              : distribution statistics, and     :                                                                                            :
:                :                 :              : file counts across massive       :                                                                                            :
:                :                 :              : environments.                    :                                                                                            :
| **Transfers**  | **Storage       | Good to Have | Replicate data to backup regions | [Storage Transfer                                                                          |
:                : Transfer        :              : or move ingested data to         : Service](https\://docs.cloud.google.com/storage-transfer/docs/overview.md.txt)             :
:                : Service (STS)** :              : processing clusters.             :                                                                                            :
| **Monitoring** | **Cloud         | Good to Have | Enable audit logging for tracing | [Cloud Audit Logging](https://docs.cloud.google.com/storage/docs/audit-logging.md.txt)     |
:                : Logging**       :              : client-side errors, upload       :                                                                                            :
:                :                 :              : failures, and CORS anomalies.    :                                                                                            :
|                | **Cloud         | Highly       | Setup alerts on application      | [Cloud Monitoring](https://docs.cloud.google.com/storage/docs/monitoring.md.txt)           |
:                : Monitoring**    : Recommended  : error rates (4xx/5xx codes),     :                                                                                            :
:                :                 :              : client quota usage, and volume   :                                                                                            :
:                :                 :              : changes.                         :                                                                                            :
|                | **Pub/Sub       | Good to Have | Trigger downstream processing    | [Pub/Sub                                                                                   |
:                : Notifications** :              : (e.g., malware scanning, image   : Notifications](https\://docs.cloud.google.com/storage/docs/pubsub-notifications.md.txt)    :
:                :                 :              : resizing, indexing)              :                                                                                            :
:                :                 :              : automatically when a new object  :                                                                                            :
:                :                 :              : is finalized.                    :                                                                                            :
