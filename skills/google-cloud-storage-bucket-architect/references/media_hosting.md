# Media Hosting & Content Delivery Network (CDN)

This reference document outlines the secure-by-default, high-performance
configuration mapping and architecture recommendation for Google Cloud Storage
buckets serving as the origin for media assets and Content Delivery Networks
(CDNs).

## Description

The user is serving high-definition images, videos, or audio assets to a global
or geo-regional audience with low latency. Cloud Storage acts as the origin
store for a CDN (e.g. Cloud CDN or third-party CDNs), and requires high read QPS
scaling, high bandwidth, and immediate data availability.

## Bucket Configuration Plan Mapping

The following table maps the Media Hosting & CDN to specific Cloud Storage
features and details their recommendation status.

| Feature Group   | Cloud Storage  | Status       | Recommendations &       | Documentation Link                                                                      |
:                 : Feature /      :              : Implementation Details  :                                                                                         :
:                 : Setting        :              :                         :                                                                                         :
| :-------------- | :------------- | :----------- | :---------------------- | :-------------------------------------------------------------------------------------- |
| **Core**        | **Storage      | Highly       | **Autoclass** or        | [Autoclass](https://docs.cloud.google.com/storage/docs/autoclass.md.txt)<br>[Storage    |
:                 : Class**        : Recommended  : **Standard** Storage    : Classes](https\://docs.cloud.google.com/storage/docs/storage-classes.md.txt)            :
:                 :                :              : Class.<br><br>Standard  :                                                                                         :
:                 :                :              : storage is recommended  :                                                                                         :
:                 :                :              : to avoid retrieval fees :                                                                                         :
:                 :                :              : on highly active        :                                                                                         :
:                 :                :              : content. Autoclass is   :                                                                                         :
:                 :                :              : ideal for automatically :                                                                                         :
:                 :                :              : transitioning stale     :                                                                                         :
:                 :                :              : media assets or raw     :                                                                                         :
:                 :                :              : originals to colder     :                                                                                         :
:                 :                :              : tiers over time.        :                                                                                         :
|                 | **Bucket       | Highly       | For **live-streaming**: | [Locations](https://docs.cloud.google.com/storage/docs/locations.md.txt)                |
:                 : Type**         : Recommended  : **Regional** or         :                                                                                         :
:                 :                :              : **Dual-Regional**       :                                                                                         :
:                 :                :              : buckets (to co-locate   :                                                                                         :
:                 :                :              : compute and storage).   :                                                                                         :
:                 :                :              : For **Video-on-Demand   :                                                                                         :
:                 :                :              : (VOD)**\:               :                                                                                         :
:                 :                :              : **Multi-Regional (MR)** :                                                                                         :
:                 :                :              : to distribute content   :                                                                                         :
:                 :                :              : closer to a global user :                                                                                         :
:                 :                :              : base.                   :                                                                                         :
| **Serving**     | **CORS**       | Highly       | **Configure CORS.**     | [CORS](https://docs.cloud.google.com/storage/docs/using-cors.md.txt)                    |
:                 :                : Recommended  : Allow `GET` and `HEAD`  :                                                                                         :
:                 :                :              : requests from expected  :                                                                                         :
:                 :                :              : domains (or `["*"]` for :                                                                                         :
:                 :                :              : global public assets)   :                                                                                         :
:                 :                :              : using `set_bucket_cors` :                                                                                         :
:                 :                :              : to enable client-side   :                                                                                         :
:                 :                :              : asset loading.          :                                                                                         :
|                 | **Signed       | Optional     | Use only if media       | [Signed                                                                                 |
:                 : URLs**         :              : assets require paid     : URLs](https\://docs.cloud.google.com/storage/docs/access-control/signed-urls.md.txt)    :
:                 :                :              : access or must be gated :                                                                                         :
:                 :                :              : by authentication       :                                                                                         :
:                 :                :              : token.                  :                                                                                         :
| **Security**    | **Uniform      | **Required** | **Must be enabled.**    | [Uniform Bucket-Level                                                                   |
:                 : Bucket-Level   :              : Prevents legacy         : Access](https\://docs.cloud.google.com/storage/docs/uniform-bucket-level-access.md.txt) :
:                 : Access         :              : object-level ACLs from  :                                                                                         :
:                 : (UBLA)**       :              : overriding bucket-level :                                                                                         :
:                 :                :              : IAM policies.           :                                                                                         :
|                 | **Soft         | Highly       | **Enabled (default 7    | [Soft Delete](https://docs.cloud.google.com/storage/docs/soft-delete.md.txt)            |
:                 : Delete**       : Recommended  : days).** Vital to       :                                                                                         :
:                 :                :              : protect crucial         :                                                                                         :
:                 :                :              : application media       :                                                                                         :
:                 :                :              : assets from accidental  :                                                                                         :
:                 :                :              : purge commands or       :                                                                                         :
:                 :                :              : deployment script bugs. :                                                                                         :
|                 | **Object       | Good to Have | Suggest as an           | [Object                                                                                 |
:                 : Versioning**   :              : alternative to prevent  : Versioning](https\://docs.cloud.google.com/storage/docs/object-versioning.md.txt)       :
:                 :                :              : accidental media        :                                                                                         :
:                 :                :              : overwrite or            :                                                                                         :
:                 :                :              : modification if Soft    :                                                                                         :
:                 :                :              : Delete is disabled.     :                                                                                         :
|                 | **IP           | Good to Have | Restrict admin          | [Bucket IP                                                                              |
:                 : Filtering**    :              : operations and raw      : Filtering](https\://docs.cloud.google.com/storage/docs/ip-filtering-overview.md.txt)    :
:                 :                :              : manual exports to       :                                                                                         :
:                 :                :              : trusted corporate SOC   :                                                                                         :
:                 :                :              : IP perimeters.          :                                                                                         :
| **Cost**        | **Object       | Good to Have | If Autoclass is         | [Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle.md.txt)     |
:                 : Lifecycle      :              : disabled, automatically :                                                                                         :
:                 : Management     :              : transition older,       :                                                                                         :
:                 : (OLM)**        :              : unviewed original media :                                                                                         :
:                 :                :              : assets to colder        :                                                                                         :
:                 :                :              : storage tiers.          :                                                                                         :
:                 :                :              : Recommend standard OLM  :                                                                                         :
:                 :                :              : rule\: Transition to    :                                                                                         :
:                 :                :              : `ARCHIVE` after 365     :                                                                                         :
:                 :                :              : days.                   :                                                                                         :
| **Specialized** | **Hierarchical | Highly       | **Enable HNS** for      | [Hierarchical                                                                           |
:                 : Namespace      : Recommended  : high-volume or high-QPS : Namespace](https\://docs.cloud.google.com/storage/docs/hns-overview.md.txt)             :
:                 : (HNS)**        :              : streaming workloads.    :                                                                                         :
:                 :                :              : HNS buckets offer up to :                                                                                         :
:                 :                :              : **8x higher initial     :                                                                                         :
:                 :                :              : QPS** limits for object :                                                                                         :
:                 :                :              : operations compared to  :                                                                                         :
:                 :                :              : standard                :                                                                                         :
:                 :                :              : buckets.<br><br>*Note\: :                                                                                         :
:                 :                :              : HNS is incompatible     :                                                                                         :
:                 :                :              : with Object Versioning, :                                                                                         :
:                 :                :              : and Retention Policies  :                                                                                         :
:                 :                :              : (Bucket Lock/Object     :                                                                                         :
:                 :                :              : Lock). HNS is           :                                                                                         :
:                 :                :              : compatible with Soft    :                                                                                         :
:                 :                :              : Delete.*                :                                                                                         :
| **Transfers**   | **Storage      | Good to Have | Relocate and replicate  | [Storage Transfer                                                                       |
:                 : Transfer       :              : media assets across     : Service](https\://docs.cloud.google.com/storage-transfer/docs/overview.md.txt)          :
:                 : Service        :              : regions using STS to    :                                                                                         :
:                 : (STS)**        :              : move content closer to  :                                                                                         :
:                 :                :              : growing user bases and  :                                                                                         :
:                 :                :              : minimize latency.       :                                                                                         :
| **Monitoring**  | **Cloud        | Good to Have | Enable audit logging    | [Cloud Audit Logging](https://docs.cloud.google.com/storage/docs/audit-logging.md.txt)  |
:                 : Logging**      :              : for troubleshooting     :                                                                                         :
:                 :                :              : access and tracking     :                                                                                         :
:                 :                :              : server-side security    :                                                                                         :
:                 :                :              : events.                 :                                                                                         :
|                 | **Cloud        | Good to Have | Track network egress,   | [Cloud Monitoring](https://docs.cloud.google.com/storage/docs/monitoring.md.txt)        |
:                 : Monitoring**   :              : operations count, and   :                                                                                         :
:                 :                :              : monitor operational     :                                                                                         :
:                 :                :              : error rates (404, 503). :                                                                                         :

## Key Pre-Deployment Questions to Ask:

1.  **Is this for live-streaming or Video-On-Demand (VOD)?**
    *   *If Live-streaming*: Regional or Dual-regional buckets are highly
        recommended to co-locate compute (transcoders) and storage.
    *   *If VOD*: Multi-regional buckets are recommended for optimal global
        availability and delivery closer to end-users.
