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

| Dimension            | Rapid Cache               | Rapid Buckets             |
| :------------------- | :------------------------ | :------------------------ |
| **Description**      | Zonal read cache attached | Zonal bucket in the       |
:                      : to an existing standard   : `RAPID` storage class     :
:                      : regional bucket.          : (different namespace).    :
| **Primary Use Case** | **Model Training &        | **Model Checkpointing**   |
:                      : Inference** where         : and high-QPS, write-heavy :
:                      : datasets already exist in : training tasks.           :
:                      : a GCS bucket.             :                           :
| **Read/Write**       | **Read-Only**. Writes     | **Read and Write**.       |
:                      : must be written to the    : Serves as a writable      :
:                      : underlying bucket.        : source of truth.          :
| **Namespace**        | Same namespace as the     | Independent namespace     |
:                      : underlying standard       : (must copy/upload data    :
:                      : bucket.                   : directly).                :
| **Performance**      | High throughput,          | Ultra-low latency, high   |
:                      : cold-start penalty on     : throughput, and high QPS  :
:                      : first reads. Same QPS as  : (no cold start).          :
:                      : standard GCS.             :                           :
| **Data Lifecycle**   | Default TTL is 24 hours.  | Permanent storage (data   |
:                      : Cache automatically       : lives forever until       :
:                      : evicts stale data.        : deleted).                 :
| **Appendability**    | No append support.        | **Supports Append (BiDi   |
:                      :                           : protocol)** to write      :
:                      :                           : streaming data up to 5TB. :
| **Hierarchical       | Optional.                 | **Required** (Always      |
: Namespace (HNS)**    :                           : enabled, not              :
:                      :                           : configurable).            :

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

The following table maps GCS features to AI/ML workloads and details their
recommendation status.

| Feature Group   | GCS Feature /  | Status       | Recommendations  | Documentation Link                                                             |
:                 : Setting        :              : & Implementation :                                                                                :
:                 :                :              : Details          :                                                                                :
| :-------------- | :------------- | :----------- | :--------------- | :----------------------------------------------------------------------------- |
| **Core**        | **Storage      | Highly       | Use **STANDARD** | [Storage                                                                       |
:                 : Class**        : Recommended  : for standard     : Classes](https\://cloud.google.com/storage/docs/storage-classes)<br>[Rapid     :
:                 :                :              : buckets, or      : Buckets](https\://cloud.google.com/storage/docs/rapid/rapid-bucket)            :
:                 :                :              : **RAPID**        :                                                                                :
:                 :                :              : storage class    :                                                                                :
:                 :                :              : for zonal Rapid  :                                                                                :
:                 :                :              : Buckets.         :                                                                                :
|                 | **Bucket       | Highly       | **Zonal** (for   | [Locations](https://cloud.google.com/storage/docs/locations)                   |
:                 : Type**         : Recommended  : Rapid Buckets)   :                                                                                :
:                 :                :              : or **Regional**  :                                                                                :
:                 :                :              : (for standard    :                                                                                :
:                 :                :              : GCS/Rapid Cache  :                                                                                :
:                 :                :              : origin) to       :                                                                                :
:                 :                :              : co-locate        :                                                                                :
:                 :                :              : storage and      :                                                                                :
:                 :                :              : compute.         :                                                                                :
| **Serving**     | **CORS &       | Optional /   | Avoid exposing   |                                                                                |
:                 : Signed URLs**  : Not          : AI datasets      :                                                                                :
:                 :                : Recommended  : directly to      :                                                                                :
:                 :                :              : public users.    :                                                                                :
| **Security**    | **Uniform      | **Required** | **Must be        | [Uniform Bucket-Level                                                          |
:                 : Bucket-Level   :              : enabled** for    : Access](https\://cloud.google.com/storage/docs/uniform-bucket-level-access)    :
:                 : Access         :              : baseline access  :                                                                                :
:                 : (UBLA)**       :              : control          :                                                                                :
:                 :                :              : security.        :                                                                                :
|                 | **Encryption   | Highly       | Configure CMEK.  | [CMEK](https://cloud.google.com/storage/docs/encryption/customer-managed-keys) |
:                 : (CMEK)**       : Recommended  : Use KMS Autokey  :                                                                                :
:                 :                :              : for automation.  :                                                                                :
|                 | **Soft         | Good to Have | Optional.        | [Soft Delete](https://cloud.google.com/storage/docs/soft-delete)               |
:                 : Delete**       :              : (Useful but not  :                                                                                :
:                 :                :              : highly           :                                                                                :
:                 :                :              : recommended due  :                                                                                :
:                 :                :              : to potential     :                                                                                :
:                 :                :              : storage cost     :                                                                                :
:                 :                :              : overhead from    :                                                                                :
:                 :                :              : massive AI       :                                                                                :
:                 :                :              : dataset churn).  :                                                                                :
| **Cost**        | **Object       | Highly       | Define OLM rules | [Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)        |
:                 : Lifecycle      : Recommended  : to automatically :                                                                                :
:                 : Management     :              : delete stale     :                                                                                :
:                 : (OLM)**        :              : checkpoints      :                                                                                :
:                 :                :              : (e.g. keep only  :                                                                                :
:                 :                :              : the last 3 days  :                                                                                :
:                 :                :              : of checkpoints)  :                                                                                :
:                 :                :              : to avoid massive :                                                                                :
:                 :                :              : storage bills on :                                                                                :
:                 :                :              : zonal disks.     :                                                                                :
| **Management**  | **Labels &     | Highly       | Apply billing    | [Bucket Labels](https://cloud.google.com/storage/docs/using-bucket-labels)     |
:                 : Tagging**      : Recommended  : and ownership    :                                                                                :
:                 :                :              : labels (e.g.     :                                                                                :
:                 :                :              : `{"workload"\:   :                                                                                :
:                 :                :              : "ai-training"}`) :                                                                                :
:                 :                :              : to accurately    :                                                                                :
:                 :                :              : trace expensive  :                                                                                :
:                 :                :              : high-performance :                                                                                :
:                 :                :              : storage spend.   :                                                                                :
| **Specialized** | **BiDi         | Highly       | Utilize the BiDi | [Hierarchical Namespace](https://cloud.google.com/storage/docs/hns-overview)   |
:                 : (Bidirectional : Recommended  : protocol on      :                                                                                :
:                 : Streaming)**   :              : Rapid Buckets to :                                                                                :
:                 :                :              : enable           :                                                                                :
:                 :                :              : low-latency,     :                                                                                :
:                 :                :              : high-QPS         :                                                                                :
:                 :                :              : streaming and    :                                                                                :
:                 :                :              : append           :                                                                                :
:                 :                :              : operations.      :                                                                                :
| **Monitoring**  | **Cloud        | Highly       | Monitor caching  | [Cloud Monitoring](https://cloud.google.com/storage/docs/monitoring)           |
:                 : Monitoring**   : Recommended  : metrics, hit     :                                                                                :
:                 :                :              : rates, and       :                                                                                :
:                 :                :              : ingress/egress   :                                                                                :
:                 :                :              : bandwidth to     :                                                                                :
:                 :                :              : ensure TPUs/GPUs :                                                                                :
:                 :                :              : are not          :                                                                                :
:                 :                :              : bottlenecked by  :                                                                                :
:                 :                :              : storage.         :                                                                                :

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
