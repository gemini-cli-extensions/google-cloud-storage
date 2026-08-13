# Log Storage

This reference document outlines the configuration mapping and architecture
recommendation for Google Cloud Storage buckets optimized for log storage and
ingestion.

## Description

The user is storing high-volume application logs, VPC flow logs, or audit trail
dumps that are typically ingested by SIEM (Security Information and Event
Management) tools or parsed during operational troubleshooting. The primary
goals are minimizing write ingestion costs and eliminating inter-regional
network egress charges, while optimizing storage costs for logs that naturally
grow cold.

## Bucket Configuration Plan Mapping

The following table maps the Log Storage use case to specific GCS features and
details their recommendation status.

| Feature Group  | GCS Feature /  | Status       | Recommendations &   | Documentation Link                                                             |
:                : Setting        :              : Implementation      :                                                                                :
:                :                :              : Details             :                                                                                :
| :------------- | :------------- | :----------- | :------------------ | :----------------------------------------------------------------------------- |
| **Core**       | **Storage      | Highly       | **Autoclass**       | [Autoclass](https://cloud.google.com/storage/docs/autoclass)<br>[Storage       |
:                : Class**        : Recommended  : Storage             : Classes](https\://cloud.google.com/storage/docs/storage-classes)               :
:                :                :              : Class.<br><br>Raw   :                                                                                :
:                :                :              : log ingestion       :                                                                                :
:                :                :              : generates massive   :                                                                                :
:                :                :              : write operations.   :                                                                                :
:                :                :              : Autoclass is ideal  :                                                                                :
:                :                :              : since standard      :                                                                                :
:                :                :              : writes carry no     :                                                                                :
:                :                :              : cost penalty, and   :                                                                                :
:                :                :              : older log chunks    :                                                                                :
:                :                :              : are automatically   :                                                                                :
:                :                :              : transitioned to     :                                                                                :
:                :                :              : colder classes as   :                                                                                :
:                :                :              : they age.           :                                                                                :
|                | **Bucket       | Highly       | **Regional (R)**    | [Locations](https://cloud.google.com/storage/docs/locations)                   |
:                : Type**         : Recommended  : bucket              :                                                                                :
:                :                :              : type.<br><br>Ensure :                                                                                :
:                :                :              : the bucket region   :                                                                                :
:                :                :              : matches the exact   :                                                                                :
:                :                :              : region hosting your :                                                                                :
:                :                :              : compute resources   :                                                                                :
:                :                :              : and SIEM tools.     :                                                                                :
:                :                :              : This completely     :                                                                                :
:                :                :              : eliminates          :                                                                                :
:                :                :              : inter-regional      :                                                                                :
:                :                :              : network egress fees :                                                                                :
:                :                :              : during ingestion    :                                                                                :
:                :                :              : and analytical      :                                                                                :
:                :                :              : querying.           :                                                                                :
| **Security**   | **Uniform      | **Required** | **Must be           | [Uniform Bucket-Level                                                          |
:                : Bucket-Level   :              : enabled.**          : Access](https\://cloud.google.com/storage/docs/uniform-bucket-level-access)    :
:                : Access         :              : Standardizes IAM    :                                                                                :
:                : (UBLA)**       :              : permissions across  :                                                                                :
:                :                :              : the bucket.         :                                                                                :
|                | **Public       | **Required** | **Must be           | [Public Access                                                                 |
:                : Access         :              : enforced.** Logs    : Prevention](https\://cloud.google.com/storage/docs/public-access-prevention)   :
:                : Prevention     :              : contain sensitive   :                                                                                :
:                : (PAP)**        :              : operational details :                                                                                :
:                :                :              : and must never be   :                                                                                :
:                :                :              : exposed publicly.   :                                                                                :
|                | **Encryption   | Highly       | Configure **CMEK    | [CMEK](https://cloud.google.com/storage/docs/encryption/customer-managed-keys) |
:                : (CMEK)**       : Recommended  : via Cloud KMS** by  :                                                                                :
:                :                :              : default. Use KMS    :                                                                                :
:                :                :              : Autokey for         :                                                                                :
:                :                :              : automation, or      :                                                                                :
:                :                :              : prompt the user.    :                                                                                :
|                | **IP           | Good to Have | Limit               | [Bucket IP                                                                     |
:                : Filtering**    :              : administrative      : Filtering](https\://cloud.google.com/storage/docs/ip-filtering-overview)       :
:                :                :              : access and raw log  :                                                                                :
:                :                :              : export operations   :                                                                                :
:                :                :              : to trusted security :                                                                                :
:                :                :              : operations center   :                                                                                :
:                :                :              : (SOC) IP ranges.    :                                                                                :
|                | **Soft         | Optional     | Neither highly      | [Soft Delete](https://cloud.google.com/storage/docs/soft-delete)               |
:                : Delete**       :              : recommended nor     :                                                                                :
:                :                :              : required, but       :                                                                                :
:                :                :              : useful to share     :                                                                                :
:                :                :              : with the customer   :                                                                                :
:                :                :              : as an essential     :                                                                                :
:                :                :              : defensive layer to  :                                                                                :
:                :                :              : recover logging     :                                                                                :
:                :                :              : windows if an       :                                                                                :
:                :                :              : administrative      :                                                                                :
:                :                :              : script executes a   :                                                                                :
:                :                :              : mass purge command. :                                                                                :
| **Cost**       | **Object       | Highly       | Recommended if      | [Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)        |
:                : Lifecycle      : Recommended  : Autoclass is        :                                                                                :
:                : Management     :              : disabled. Establish :                                                                                :
:                : (OLM)**        :              : rules to transition :                                                                                :
:                :                :              : logs to `ARCHIVE`   :                                                                                :
:                :                :              : after 365 days.     :                                                                                :
| **Management** | **Labels &     | Good to Have | Apply tagging (e.g. | [Bucket Labels](https://cloud.google.com/storage/docs/using-bucket-labels)     |
:                : Tagging**      :              : `{"environment"\:   :                                                                                :
:                :                :              : "production"}` and  :                                                                                :
:                :                :              : `{"cost-center"\:   :                                                                                :
:                :                :              : "security-ops"}`)   :                                                                                :
:                :                :              : to parse out        :                                                                                :
:                :                :              : high-volume cloud   :                                                                                :
:                :                :              : infrastructure      :                                                                                :
:                :                :              : spend.              :                                                                                :
|                | **Storage      | Good to Have | Monitor data        | [Inventory                                                                     |
:                : Intelligence** :              : accumulation rates  : Reports](https\://cloud.google.com/storage/docs/insights/inventory-reports)    :
:                :                :              : using Storage       :                                                                                :
:                :                :              : Insights to         :                                                                                :
:                :                :              : identify which      :                                                                                :
:                :                :              : microservices are   :                                                                                :
:                :                :              : dominating storage  :                                                                                :
:                :                :              : metrics.            :                                                                                :
| **Monitoring** | **Cloud        | Highly       | **Configure Cloud   | [Cloud Monitoring](https://cloud.google.com/storage/docs/monitoring)           |
:                : Monitoring**   : Recommended  : Monitoring** to     :                                                                                :
:                :                :              : build dashboards    :                                                                                :
:                :                :              : tracking storage    :                                                                                :
:                :                :              : API call limits,    :                                                                                :
:                :                :              : ingestion errors,   :                                                                                :
:                :                :              : or spikes in daily  :                                                                                :
:                :                :              : write volumes.      :                                                                                :

## Key Pre-Deployment Questions to Ask:

1.  **In which region are your compute workloads and analytical SIEM tools
    hosted?**
    *   *Recommendation*: Co-locate the bucket in the same region to eliminate
        egress fees.
2.  **What is the typical time window before logs are considered cold or no
    longer queryable?**

## Mandatory Recommendations to Include in the Design Plan:

*   **Cloud Monitoring**: You MUST recommend configuring Cloud Monitoring to
    track GCS API limits, ingestion errors, and daily write volumes.
