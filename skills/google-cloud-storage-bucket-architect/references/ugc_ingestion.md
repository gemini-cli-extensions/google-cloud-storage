# Direct User-Generated Content (UGC) Ingestion

This reference document outlines the secure-by-default configuration mapping and
architecture recommendation for Google Cloud Storage buckets receiving direct
client-side uploads from user applications (mobile apps, web browsers, etc.)
bypassing backend servers.

## Description

The user is building a mobile or web application where end-users upload heavy
files (such as profile pictures, documents, or video clips) directly to a GCS
bucket. This is achieved using Signed URLs to authorize uploads and CORS
configuration to allow browser-based calls, avoiding network bottlenecking on
the application's backend web servers.

## Bucket Configuration Plan Mapping

The following table maps the Direct UGC Ingestion use case to specific GCS
features and details their recommendation status.

| Feature Group  | GCS Feature /   | Status       | Recommendations & Implementation | Documentation Link                                                             |
:                : Setting         :              : Details                          :                                                                                :
| :------------- | :-------------- | :----------- | :------------------------------- | :----------------------------------------------------------------------------- |
| **Core**       | **Storage       | Highly       | **Autoclass** or **Standard**    | [Autoclass](https://cloud.google.com/storage/docs/autoclass)<br>[Storage       |
:                : Class**         : Recommended  : Storage Class.<br><br>Standard   : Classes](https\://cloud.google.com/storage/docs/storage-classes)               :
:                :                 :              : storage is recommended if users  :                                                                                :
:                :                 :              : frequently view uploaded content :                                                                                :
:                :                 :              : immediately. Autoclass is ideal  :                                                                                :
:                :                 :              : if files naturally go cold over  :                                                                                :
:                :                 :              : time, avoiding retrieval fee     :                                                                                :
:                :                 :              : traps.                           :                                                                                :
|                | **Bucket Type** | Highly       | **Regional** bucket type. Align  | [Locations](https://cloud.google.com/storage/docs/locations)                   |
:                :                 : Recommended  : storage region with application  :                                                                                :
:                :                 :              : compute to minimize latency.     :                                                                                :
:                :                 :              : Create multiple regional buckets :                                                                                :
:                :                 :              : if the user base is globally     :                                                                                :
:                :                 :              : dispersed.                       :                                                                                :
| **Serving**    | **Signed URLs** | **Required** | **Use Signed URLs** to delegate  | [Signed                                                                        |
:                :                 :              : time-limited read/write access   : URLs](https\://cloud.google.com/storage/docs/access-control/signed-urls)       :
:                :                 :              : to clients, keeping the bucket   :                                                                                :
:                :                 :              : secure while offloading traffic  :                                                                                :
:                :                 :              : from backend servers.            :                                                                                :
|                | **CORS**        | **Required** | **Configure CORS** to allow web  | [CORS](https://cloud.google.com/storage/docs/using-cors)                       |
:                :                 :              : applications hosted on custom    :                                                                                :
:                :                 :              : domains to perform client-side   :                                                                                :
:                :                 :              : uploads and load resources       :                                                                                :
:                :                 :              : directly.                        :                                                                                :
| **Security**   | **Uniform       | **Required** | **Must be enabled.**             | [Uniform Bucket-Level                                                          |
:                : Bucket-Level    :              : Standardizes IAM permissions     : Access](https\://cloud.google.com/storage/docs/uniform-bucket-level-access)    :
:                : Access (UBLA)** :              : across the bucket, disabling     :                                                                                :
:                :                 :              : granular legacy ACLs.            :                                                                                :
|                | **Encryption    | Good to Have | Recommend Customer-Managed       | [CMEK](https://cloud.google.com/storage/docs/encryption/customer-managed-keys) |
:                : (CMEK)**        :              : Encryption Keys (CMEK) primarily :                                                                                :
:                :                 :              : for B2B multi-tenant             :                                                                                :
:                :                 :              : environments with strict         :                                                                                :
:                :                 :              : compliance mandates.             :                                                                                :
|                | **Soft Delete** | Highly       | **Enabled (default 7 days).**    | [Soft Delete](https://cloud.google.com/storage/docs/soft-delete)               |
:                :                 : Recommended  : Provides a safety fallback to    :                                                                                :
:                :                 :              : recover user data from           :                                                                                :
:                :                 :              : accidental deletions or          :                                                                                :
:                :                 :              : compromise, without regulatory   :                                                                                :
:                :                 :              : locking.                         :                                                                                :
|                | **Object        | Good to Have | Recommend only if users          | [Object Versioning](https://cloud.google.com/storage/docs/object-versioning)   |
:                : Versioning**    :              : frequently overwrite files of    :                                                                                :
:                :                 :              : identical names and              :                                                                                :
:                :                 :              : collaborative history is needed, :                                                                                :
:                :                 :              : but govern with strict OLM to    :                                                                                :
:                :                 :              : control cost.                    :                                                                                :
|                | **IP            | Good to Have | Restrict admin API endpoints and | [Bucket IP                                                                     |
:                : Filtering**     :              : internal export operations to    : Filtering](https\://cloud.google.com/storage/docs/ip-filtering-overview)       :
:                :                 :              : trusted NAT IPs.                 :                                                                                :
| **Cost**       | **Object        | Highly       | **Enable                         | [Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)        |
:                : Lifecycle       : Recommended  : abortIncompleteMultipartUpload** :                                                                                :
:                : Management      :              : to clean up abandoned,           :                                                                                :
:                : (OLM)**         :              : incomplete client uploads. If    :                                                                                :
:                :                 :              : Autoclass is disabled,           :                                                                                :
:                :                 :              : automatically transition older,  :                                                                                :
:                :                 :              : unaccessed user data to standard :                                                                                :
:                :                 :              : cold classes (e.g., transition   :                                                                                :
:                :                 :              : to `ARCHIVE` after 365 days).    :                                                                                :
| **Management** | **Labels &      | Good to Have | Apply organizational metadata    | [Bucket Labels](https://cloud.google.com/storage/docs/using-bucket-labels)     |
:                : Tagging**       :              : tags (e.g. `{"data-class"\:      :                                                                                :
:                :                 :              : "ugc"}`) to classify files.      :                                                                                :
|                | **Storage       | Good to Have | Use Storage Insights Inventory   | [Inventory                                                                     |
:                : Intelligence**  :              : Reports to track upload scales,  : Reports](https\://cloud.google.com/storage/docs/insights/inventory-reports)    :
:                :                 :              : distribution statistics, and     :                                                                                :
:                :                 :              : file counts across massive       :                                                                                :
:                :                 :              : environments.                    :                                                                                :
| **Transfers**  | **Storage       | Good to Have | Replicate data to backup regions | [Storage Transfer                                                              |
:                : Transfer        :              : or move ingested data to         : Service](https\://cloud.google.com/storage-transfer/docs/overview)             :
:                : Service (STS)** :              : processing clusters.             :                                                                                :
| **Monitoring** | **Cloud         | Good to Have | Enable audit logging for tracing | [Cloud Audit Logging](https://cloud.google.com/storage/docs/audit-logging)     |
:                : Logging**       :              : client-side errors, upload       :                                                                                :
:                :                 :              : failures, and CORS anomalies.    :                                                                                :
|                | **Cloud         | Highly       | Setup alerts on application      | [Cloud Monitoring](https://cloud.google.com/storage/docs/monitoring)           |
:                : Monitoring**    : Recommended  : error rates (4xx/5xx codes),     :                                                                                :
:                :                 :              : client quota usage, and volume   :                                                                                :
:                :                 :              : changes.                         :                                                                                :
|                | **Pub/Sub       | Good to Have | Trigger downstream processing    | [Pub/Sub                                                                       |
:                : Notifications** :              : (e.g., malware scanning, image   : Notifications](https\://cloud.google.com/storage/docs/pubsub-notifications)    :
:                :                 :              : resizing, indexing)              :                                                                                :
:                :                 :              : automatically when a new object  :                                                                                :
:                :                 :              : is finalized.                    :                                                                                :
