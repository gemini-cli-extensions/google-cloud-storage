# Long-Term Archive & Regulatory Compliance

This reference document outlines the secure-by-default, cost-effective
configuration mapping and architecture recommendation for Google Cloud Storage
buckets optimized for long-term archiving and regulatory compliance mandates.

## Description

The user is retaining data (such as financial statements, medical records, tax
documents, or corporate legal logs) for legal or regulatory requirements
(typically 7-10+ years). The data is accessed very infrequently, but its
integrity must be guaranteed, and it must be protected against accidental or
premature deletion (immutability).

## Bucket Configuration Plan Mapping

The following table maps the Long-Term Archive & Compliance use case to specific
Cloud Storage features and details their recommendation status.

| Feature Group  | Cloud Storage  | Status       | Recommendations &         | Documentation Link                                                                                   |
:                : Feature /      :              : Implementation Details    :                                                                                                      :
:                : Setting        :              :                           :                                                                                                      :
| :------------- | :------------- | :----------- | :------------------------ | :--------------------------------------------------------------------------------------------------- |
| **Core**       | **Storage      | Highly       | **Coldline** or           | [Storage Classes](https://docs.cloud.google.com/storage/docs/storage-classes.md.txt)                 |
:                : Class**        : Recommended  : **Archive** Storage       :                                                                                                      :
:                :                :              : Class.<br><br>Archive     :                                                                                                      :
:                :                :              : storage offers the lowest :                                                                                                      :
:                :                :              : cost per gigabyte, ideal  :                                                                                                      :
:                :                :              : for data kept as a legal  :                                                                                                      :
:                :                :              : requirement that may      :                                                                                                      :
:                :                :              : never be read. Beware of  :                                                                                                      :
:                :                :              : high retrieval and early  :                                                                                                      :
:                :                :              : deletion fees (e.g.       :                                                                                                      :
:                :                :              : minimum 365 days          :                                                                                                      :
:                :                :              : retention for Archive).   :                                                                                                      :
|                | **Bucket       | Highly       | **Regional** or           | [Locations](https://docs.cloud.google.com/storage/docs/locations.md.txt)                             |
:                : Type**         : Recommended  : **Dual-Regional** bucket  :                                                                                                      :
:                :                :              : configuration.            :                                                                                                      :
:                :                :              : Multi-regional            :                                                                                                      :
:                :                :              : configurations should be  :                                                                                                      :
:                :                :              : avoided if national laws  :                                                                                                      :
:                :                :              : mandate physical data     :                                                                                                      :
:                :                :              : residency boundaries.     :                                                                                                      :
| **Serving**    | **Signed       | Good to Have | Gated write access only;  | [Signed URLs](https://docs.cloud.google.com/storage/docs/access-control/signed-urls.md.txt)          |
:                : URLs**         :              : restrict public URLs      :                                                                                                      :
:                :                :              : entirely.                 :                                                                                                      :
| **Security**   | **Uniform      | **Required** | **Must be enabled.**      | [Uniform Bucket-Level                                                                                |
:                : Bucket-Level   :              : Standardizes              : Access](https\://docs.cloud.google.com/storage/docs/uniform-bucket-level-access.md.txt)              :
:                : Access         :              : administrative access     :                                                                                                      :
:                : (UBLA)**       :              : control across the        :                                                                                                      :
:                :                :              : bucket.                   :                                                                                                      :
|                | **Public       | **Required** | **Must be enforced.**     | [Public Access                                                                                       |
:                : Access         :              : Disallows public read     : Prevention](https\://docs.cloud.google.com/storage/docs/public-access-prevention.md.txt)             :
:                : Prevention     :              : permissions.              :                                                                                                      :
:                : (PAP)**        :              :                           :                                                                                                      :
|                | **Encryption   | Highly       | **CMEK via KMS** is       | [CMEK](https://docs.cloud.google.com/storage/docs/encryption/customer-managed-keys.md.txt)           |
:                : (CMEK)**       : Recommended  : standard for compliance   :                                                                                                      :
:                :                :              : workloads. Use KMS        :                                                                                                      :
:                :                :              : Autokey for automated     :                                                                                                      :
:                :                :              : keys, or prompt the user  :                                                                                                      :
:                :                :              : for key paths.            :                                                                                                      :
|                | **IP           | Good to Have | Limit bucket              | [Bucket IP Filtering](https://docs.cloud.google.com/storage/docs/ip-filtering-overview.md.txt)       |
:                : Filtering**    :              : administration endpoints  :                                                                                                      :
:                :                :              : exclusively to verified   :                                                                                                      :
:                :                :              : corporate office IPs or   :                                                                                                      :
:                :                :              : secure VPN ranges.        :                                                                                                      :
|                | **Retention    | Good to Have | Configure Cloud Storage   | [Bucket Lock](https://docs.cloud.google.com/storage/docs/bucket-lock.md.txt)<br>[Object              |
:                : Policy         :              : **Bucket Lock** or        : Lock](https\://docs.cloud.google.com/storage/docs/object-lock.md.txt)                                :
:                : (WORM)**       :              : **Object Lock** to        :                                                                                                      :
:                :                :              : enforce immutability      :                                                                                                      :
:                :                :              : (Write Once, Read         :                                                                                                      :
:                :                :              : Many).<br><br>**Warning\: :                                                                                                      :
:                :                :              : Locking the retention     :                                                                                                      :
:                :                :              : policy is irreversible.   :                                                                                                      :
:                :                :              : Objects cannot be deleted :                                                                                                      :
:                :                :              : by anyone, including      :                                                                                                      :
:                :                :              : owners or Google Cloud    :                                                                                                      :
:                :                :              : Support, until the        :                                                                                                      :
:                :                :              : retention period          :                                                                                                      :
:                :                :              : expires.**                :                                                                                                      :
| **Cost**       | **Object       | Highly       | Configure lifecycle rules | [Lifecycle Management](https://docs.cloud.google.com/storage/docs/lifecycle.md.txt)                  |
:                : Lifecycle      : Recommended  : to automatically purge    :                                                                                                      :
:                : Management     :              : expired archive records   :                                                                                                      :
:                : (OLM)**        :              : (e.g. delete after 7      :                                                                                                      :
:                :                :              : years / 2555 days) to     :                                                                                                      :
:                :                :              : mitigate liability and    :                                                                                                      :
:                :                :              : storage costs.            :                                                                                                      :
| **Management** | **Labels &     | Highly       | Apply governance metadata | [Bucket Labels](https://docs.cloud.google.com/storage/docs/using-bucket-labels.md.txt)               |
:                : Tagging**      : Recommended  : tags (e.g.                :                                                                                                      :
:                :                :              : `{"compliance-type"\:     :                                                                                                      :
:                :                :              : "hipaa"}` or              :                                                                                                      :
:                :                :              : `{"retention-period"\:    :                                                                                                      :
:                :                :              : "7-years"}`) for          :                                                                                                      :
:                :                :              : cost-center and policy    :                                                                                                      :
:                :                :              : tracking.                 :                                                                                                      :
|                | **Storage      | Good to Have | Use Storage Insights      | [Inventory Reports](https://docs.cloud.google.com/storage/docs/insights/inventory-reports.md.txt)    |
:                : Intelligence** :              : Inventory Reports to      :                                                                                                      :
:                :                :              : track record age, verify  :                                                                                                      :
:                :                :              : compliance counts, and    :                                                                                                      :
:                :                :              : manage data wipes.        :                                                                                                      :
| **Compliance** | **Regional     | Highly       | Enforce localized control | [Locations](https://docs.cloud.google.com/storage/docs/locations.md.txt)                             |
:                : Endpoints**    : Recommended  : planes to satisfy         :                                                                                                      :
:                :                :              : sovereignty requirements  :                                                                                                      :
:                :                :              : where data operations     :                                                                                                      :
:                :                :              : must stay within regional :                                                                                                      :
:                :                :              : borders.                  :                                                                                                      :
| **Transfers**  | **Storage      | Good to Have | Use STS for               | [Storage Transfer Service](https://docs.cloud.google.com/storage-transfer/docs/overview.md.txt)      |
:                : Transfer       :              : inter-regional            :                                                                                                      :
:                : Service        :              : migrations, backup, or    :                                                                                                      :
:                : (STS)**        :              : ITAR compliance           :                                                                                                      :
:                :                :              : transfers.                :                                                                                                      :
|                | **SFTP**       | Good to Have | Implement secure SFTP     | [SFTP Gateway                                                                                        |
:                :                :              : transfers if legacy       : (SFTP)](https\://docs.cloud.google.com/integration-connectors/docs/connectors/sftp/configure.md.txt) :
:                :                :              : compliance networks or    :                                                                                                      :
:                :                :              : mainframes upload         :                                                                                                      :
:                :                :              : transaction logs          :                                                                                                      :
:                :                :              : directly.                 :                                                                                                      :
| **Monitoring** | **Cloud        | Highly       | Enable Cloud Storage      | [Cloud Audit Logging](https://docs.cloud.google.com/storage/docs/audit-logging.md.txt)               |
:                : Logging**      : Recommended  : Audit Logs (Data Access & :                                                                                                      :
:                :                :              : Admin Activity) to        :                                                                                                      :
:                :                :              : maintain a complete,      :                                                                                                      :
:                :                :              : audit-safe record of data :                                                                                                      :
:                :                :              : reads, writes, and config :                                                                                                      :
:                :                :              : updates.                  :                                                                                                      :
|                | **Cloud        | Good to Have | Monitor capacity trends   | [Cloud Monitoring](https://docs.cloud.google.com/storage/docs/monitoring.md.txt)                     |
:                : Monitoring**   :              : and set alert systems to  :                                                                                                      :
:                :                :              : fire if unexpected large  :                                                                                                      :
:                :                :              : drops in object count or  :                                                                                                      :
:                :                :              : volume occur.             :                                                                                                      :

## Key Pre-Deployment Questions to Ask:

1.  **What specific compliance standard governs this data (e.g., HIPAA, SEC Rule
    17a-4, GDPR)?**
2.  **Do you require an irreversible compliance lock (Bucket/Object Lock)?**
    *   *If Yes*: Explain that once locked, even the Project Administrator
        cannot shorten the policy or delete the data. Confirm if they wish to
        proceed with "Locked" or "Unlocked" status.
3.  **What is the exact data retention duration (e.g., 7 years)?**
