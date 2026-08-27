# AI & Machine Learning (Storage for AI)

This reference document outlines the configuration mapping and architecture
recommendation for Google Cloud Storage buckets optimized for AI/ML workloads,
including model training, checkpointing, and model inference.

## Description

The user is running demanding AI/ML workloads (such as Large Language Model
training, computer vision pipelines, or high-throughput batch inference)
utilizing TPU or GPU accelerators. These workloads require ultra-high read/write
throughput, sub-millisecond latencies, and co-location with compute resources to
prevent compute starvation.

## Architecture Alternatives: Rapid Cache vs. Rapid Buckets

Depending on the specific workload phase (Training, Checkpointing, or Inference)
and data access patterns, recommend one of the two Cloud Storage Rapid
solutions.

Dimension                        | Rapid Cache                                                                             | Rapid Buckets
:------------------------------- | :-------------------------------------------------------------------------------------- | :------------
**Description**                  | Zonal read cache attached to an existing standard regional bucket.                      | Zonal bucket in the `RAPID` storage class (different namespace).
**Primary Use Case**             | **Model Training & Inference** where datasets already exist in a Cloud Storage bucket.  | **Model Checkpointing** and high-QPS, write-heavy training tasks.
**Read/Write**                   | **Read-Only**. Writes must be written to the underlying bucket.                         | **Read and Write**. Serves as a writable source of truth.
**Namespace**                    | Same namespace as the underlying standard bucket.                                       | Independent namespace (must copy/upload data directly).
**Performance**                  | High throughput, cold-start penalty on first reads. Same QPS as standard Cloud Storage. | Ultra-low latency, high throughput, and high QPS (no cold start).
**Data Lifecycle**               | Default TTL is 24 hours. Cache automatically evicts stale data.                         | Permanent storage (data lives forever until deleted).
**Appendability**                | No append support.                                                                      | **Supports Append (BiDi protocol)** to write streaming data up to 5TB.
**Hierarchical Namespace (HNS)** | Optional.                                                                               | **Required** (Always enabled, not configurable).

--------------------------------------------------------------------------------

## Rapid Cache (Anywhere Cache) Specific Recommendations

When the architecture plan recommends **Rapid Cache (Anywhere Cache)**, the
agent MUST explicitly configure and recommend the following:

1.  **Zonal Co-location**: Co-locate the Anywhere Cache instance in the exact
    same zone as the compute cluster (e.g. GPU/TPU cluster).
2.  **Cache Pre-warming (Workload Strategy)**: Recommend pre-warming the cache
    prior to starting the training script to avoid cold-start latencies and
    prevent GPU/TPU starvation.
    *   **gcloud Command**: `gcloud storage cat gs://[bucket-name]/**
        --project=[project-id] > /dev/null`
3.  **Cache Pinning**: Explain that cache ingestion can be paused to pin the
    dataset after hydration (using `pause` and `resume` subcommands).

--------------------------------------------------------------------------------

## Zonal (Rapid) Buckets Specific Recommendations

When the architecture plan recommends **Rapid Buckets (Zonal)**, the agent MUST
explicitly configure and recommend the following:

1.  **Zonal Co-location**: Co-locate the Rapid Bucket in the exact same zone as
    the compute/training nodes (e.g. `us-east4-a` for GPU cluster in
    `us-east4-a`) to eliminate network bottlenecks.
2.  **Storage Class**: The storage class MUST be set to `RAPID`.
3.  **Disable Soft Delete**: Soft delete is not supported for zonal buckets and
    MUST be disabled (set `--soft-delete-duration=0` during creation).
4.  **Hierarchical Namespace (HNS)**: HNS MUST be enabled.
5.  **BiDi Protocol Recommendation**: For streaming, write-heavy, or logging
    workloads, explicitly recommend utilizing the **BiDi protocol**
    (Bidirectional Streaming) on the Rapid Bucket to enable low-latency,
    high-QPS streaming append operations up to 5TB.

--------------------------------------------------------------------------------

## Bucket Configuration Plan Mapping

The following table maps Cloud Storage features to AI/ML workloads and details
their recommendation status.

Feature Group   | Cloud Storage Feature / Setting        | Status                     | Recommendations & Implementation Details                                                                                                                  | Documentation Link
:-------------- | :------------------------------------- | :------------------------- | :-------------------------------------------------------------------------------------------------------------------------------------------------------- | :-----------------
**Core**        | **Storage Class**                      | Highly Recommended         | Use **STANDARD** for standard buckets, or **RAPID** storage class for zonal Rapid Buckets.                                                                | [Storage Classes](https://docs.cloud.google.com/storage/docs/storage-classes.md.txt)<br>[Rapid Buckets](https://docs.cloud.google.com/storage/docs/rapid/rapid-bucket.md.txt)
                | **Bucket Type**                        | Highly Recommended         | **Zonal** (for Rapid Buckets) or **Regional** (for standard Cloud Storage/Rapid Cache origin) to co-locate storage and compute.                           | [Locations](https://docs.cloud.google.com/storage/docs/locations.md.txt)
**Serving**     | **CORS & Signed URLs**                 | Optional / Not Recommended | Avoid exposing AI datasets directly to public users.                                                                                                      |
**Security**    | **Uniform Bucket-Level Access (UBLA)** | **Required**               | **Must be enabled** for baseline access control security.                                                                                                 | [Uniform Bucket-Level Access](https://docs.cloud.google.com/storage/docs/uniform-bucket-level-access.md.txt)
                | **Encryption (CMEK)**                  | Highly Recommended         | Configure CMEK. Use KMS Autokey for automation.                                                                                                           | [CMEK](https://docs.cloud.google.com/storage/docs/encryption/customer-managed-keys.md.txt)
                | **Soft Delete**                        | Good to Have               | Optional. (Useful but not highly recommended due to potential storage cost overhead from massive AI dataset churn).                                       | [Soft Delete](https://docs.cloud.google.com/storage/docs/soft-delete.md.txt)
**Cost**        | **Object Lifecycle Management (OLM)**  | Highly Recommended         | Define OLM rules to automatically delete stale checkpoints (e.g. keep only the last 3 days of checkpoints) to avoid massive storage bills on zonal disks. | [Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle.md.txt)
**Management**  | **Labels & Tagging**                   | Highly Recommended         | Apply billing and ownership labels (e.g. `{"workload": "ai-training"}`) to accurately trace expensive high-performance storage spend.                     | [Bucket Labels](https://docs.cloud.google.com/storage/docs/using-bucket-labels.md.txt)
**Specialized** | **BiDi (Bidirectional Streaming)**     | Highly Recommended         | Utilize the BiDi protocol on Rapid Buckets to enable low-latency, high-QPS streaming and append operations.                                               | [Hierarchical Namespace](https://docs.cloud.google.com/storage/docs/hns-overview.md.txt)
**Monitoring**  | **Cloud Monitoring**                   | Highly Recommended         | Monitor caching metrics, hit rates, and ingress/egress bandwidth to ensure TPUs/GPUs are not bottlenecked by storage.                                     | [Cloud Monitoring](https://docs.cloud.google.com/storage/docs/monitoring.md.txt)

## Key Pre-Deployment Questions to Ask:

1.  **What phase of the AI/ML pipeline is this storage for?**
    *   *If Training / Inference (read-heavy)*: Ask if the dataset already
        exists. Recommend **Rapid Cache** to save migration time and egress
        costs.
    *   *If Checkpointing (write-heavy)*: Recommend **Rapid Buckets** for
        low-latency writes.
2.  **What zone is your compute cluster (TPU/GPU) located in?**
    *   *Recommendation*: Co-locate the Rapid Cache or Rapid Bucket in the exact
        same zone (e.g. `us-central1-a`) to eliminate network bottlenecks.
3.  **If using Rapid Cache, do you want to pre-warm the cache?**
    *   *Recommendation*: Pre-warm the cache before starting training jobs to
        avoid cold-start performance penalties.
