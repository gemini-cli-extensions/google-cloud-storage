# Backup and Disaster Recovery

This reference document outlines the secure-by-default, highly durable
configuration mapping and architecture recommendation for Google Cloud Storage
buckets serving as the storage backend for database dumps, virtual machine
snapshots, and system backups.

## Description

The user is storing mission-critical backups and disaster recovery data. This
workload requires high durability, protection against ransomware and accidental
deletion (WORM/Soft Delete), and automated cross-region replication to maintain
recovery objectives (RTO/RPO). Backups are typically written once and read
infrequently, but require rapid access when a restore is triggered.

## Bucket Configuration Plan Mapping

The following table maps the Backup and Disaster Recovery to specific GCS
features and details their recommendation status.

| Feature Group  | GCS Feature /  | Status       | Recommendations &              | Documentation Link                                                                     |
:                : Setting        :              : Implementation Details         :                                                                                        :
| :------------- | :------------- | :----------- | :----------------------------- | :------------------------------------------------------------------------------------- |
| **Core**       | **Storage      | Highly       | **Nearline**, **Coldline**, or | [Storage Classes](https://cloud.google.com/storage/docs/storage-classes)               |
:                : Class**        : Recommended  : **Archive** Storage            :                                                                                        :
:                :                :              : Class.<br><br>Choose based on  :                                                                                        :
:                :                :              : retention duration and restore :                                                                                        :
:                :                :              : probability. Nearline is ideal :                                                                                        :
:                :                :              : for daily/weekly backups       :                                                                                        :
:                :                :              : (30-day minimum), Coldline for :                                                                                        :
:                :                :              : monthly archives (90-day       :                                                                                        :
:                :                :              : minimum), and Archive for      :                                                                                        :
:                :                :              : annual backups (365-day        :                                                                                        :
:                :                :              : minimum).                      :                                                                                        :
|                | **Bucket       | Highly       | **Regional** bucket type.      | [Locations](https://cloud.google.com/storage/docs/locations)                           |
:                : Type**         : Recommended  : Combine with cross-bucket      :                                                                                        :
:                :                :              : replication using Storage      :                                                                                        :
:                :                :              : Transfer Service (STS) to      :                                                                                        :
:                :                :              : replicate to a disaster        :                                                                                        :
:                :                :              : recovery                       :                                                                                        :
:                :                :              : region.<br><br>*Note\:         :                                                                                        :
:                :                :              : Dual-Region or Multi-Region    :                                                                                        :
:                :                :              : buckets are not recommended    :                                                                                        :
:                :                :              : for backups due to higher cost :                                                                                        :
:                :                :              : and lack of flexibility. If    :                                                                                        :
:                :                :              : the user requests dual-region  :                                                                                        :
:                :                :              : (e.g. nam4), explicitly advise :                                                                                        :
:                :                :              : against it and recommend       :                                                                                        :
:                :                :              : Regional + STS instead.*       :                                                                                        :
| **Serving**    | **Signed       | Not          | Typically not required for     | [Signed URLs](https://cloud.google.com/storage/docs/access-control/signed-urls)        |
:                : URLs**         : Recommended  : backup workloads.              :                                                                                        :
|                | **CORS**       | Not          | Typically not required for     | [CORS](https://cloud.google.com/storage/docs/using-cors)                               |
:                :                : Recommended  : backup workloads.              :                                                                                        :
| **Security**   | **Uniform      | **Required** | **Must be enabled.**           | [Uniform Bucket-Level                                                                  |
:                : Bucket-Level   :              : Standardizes IAM permissions   : Access](https\://cloud.google.com/storage/docs/uniform-bucket-level-access)            :
:                : Access         :              : across the bucket, disabling   :                                                                                        :
:                : (UBLA)**       :              : legacy ACLs.                   :                                                                                        :
|                | **Public       | **Required** | **Must be enforced.**          | [Public Access                                                                         |
:                : Access         :              : Disallows public access.       : Prevention](https\://cloud.google.com/storage/docs/public-access-prevention)           :
:                : Prevention     :              :                                :                                                                                        :
:                : (PAP)**        :              :                                :                                                                                        :
|                | **Encryption   | Highly       | **Customer-Managed Encryption  | [CMEK](https://cloud.google.com/storage/docs/encryption/customer-managed-keys)<br>[KMS |
:                : (CMEK)**       : Recommended  : Keys (CMEK)** via Cloud        : Autokey](https\://cloud.google.com/kms/docs/autokey-overview)                          :
:                :                :              : KMS.<br><br>Use KMS Autokey    :                                                                                        :
:                :                :              : for automated provisioning, or :                                                                                        :
:                :                :              : guide the user to assign a     :                                                                                        :
:                :                :              : key.                           :                                                                                        :
|                | **Soft         | Highly       | **Enabled (default 7 days).**  | [Soft Delete](https://cloud.google.com/storage/docs/soft-delete)                       |
:                : Delete**       : Recommended  : Essential baseline defense to  :                                                                                        :
:                :                :              : recover from accidental        :                                                                                        :
:                :                :              : deletions by scripts or        :                                                                                        :
:                :                :              : administrative errors.         :                                                                                        :
|                | **Object       | Good to Have | Suggest as an alternative to   | [Object Versioning](https://cloud.google.com/storage/docs/object-versioning)           |
:                : Versioning**   :              : Soft Delete for recovery.      :                                                                                        :
|                | **Data         | Good to Have | Prompt the user to configure a | [Bucket Lock](https://cloud.google.com/storage/docs/bucket-lock)<br>[Object            |
:                : Retention      :              : Retention Policy (Bucket Lock  : Lock](https\://cloud.google.com/storage/docs/object-lock)                              :
:                : (WORM)**       :              : or Object Lock) if             :                                                                                        :
:                :                :              : immutability is required for   :                                                                                        :
:                :                :              : ransomware protection or       :                                                                                        :
:                :                :              : compliance.<br><br>**Warning\: :                                                                                        :
:                :                :              : Lock mode is permanent and     :                                                                                        :
:                :                :              : irreversible.**                :                                                                                        :
|                | **IP           | Good to Have | Restrict access exclusively to | [Bucket IP Filtering](https://cloud.google.com/storage/docs/ip-filtering-overview)     |
:                : Filtering**    :              : trusted corporate data center  :                                                                                        :
:                :                :              : IPs or secure office           :                                                                                        :
:                :                :              : perimeters.                    :                                                                                        :
| **Cost**       | **Object       | Not          | Start with the correct storage | [Lifecycle Management](https://cloud.google.com/storage/docs/lifecycle)                |
:                : Lifecycle      : Recommended  : class. OLM is generally not    :                                                                                        :
:                : Management     :              : recommended for transitioning  :                                                                                        :
:                : (OLM)**        :              : backups unless specific        :                                                                                        :
:                :                :              : lifecycle needs exist.         :                                                                                        :
| **Management** | **Labels &     | Highly       | **Mandatory** bucket-level     | [Bucket Labels](https://cloud.google.com/storage/docs/using-bucket-labels)             |
:                : Tagging**      : Recommended  : tagging (e.g.,                 :                                                                                        :
:                :                :              : `{"environment"\:              :                                                                                        :
:                :                :              : "production"}` and `{"app"\:   :                                                                                        :
:                :                :              : "core-db-backup"}`) to map and :                                                                                        :
:                :                :              : audit storage spend.           :                                                                                        :
|                | **Storage      | Good to Have | Use Storage Insights to        | [Storage Insights](https://cloud.google.com/storage/docs/insights/inventory-reports)   |
:                : Intelligence** :              : monitor backup volume growth   :                                                                                        :
:                :                :              : and security status.           :                                                                                        :
| **Transfers**  | **Storage      | Highly       | Use STS for automated, secure  | [Storage Transfer Service](https://cloud.google.com/storage-transfer/docs/overview)    |
:                : Transfer       : Recommended  : cross-bucket replication to a  :                                                                                        :
:                : Service        :              : secondary DR region to         :                                                                                        :
:                : (STS)**        :              : simplify disaster recovery.    :                                                                                        :
| **Monitoring** | **Cloud        | Highly       | Enable Cloud Logging for       | [Cloud Logging](https://cloud.google.com/storage/docs/logging)                         |
:                : Logging**      : Recommended  : troubleshooting network        :                                                                                        :
:                :                :              : timeouts or throughput         :                                                                                        :
:                :                :              : bottlenecks during massive     :                                                                                        :
:                :                :              : backup transfers.              :                                                                                        :
|                | **Cloud        | Highly       | Track API call counts and      | [Cloud Monitoring](https://cloud.google.com/storage/docs/monitoring)                   |
:                : Monitoring**   : Recommended  : storage limits. Configure      :                                                                                        :
:                :                :              : alerts to fire if a backup     :                                                                                        :
:                :                :              : bucket registers zero write    :                                                                                        :
:                :                :              : activity within 24 hours.      :                                                                                        :

## Project-Level Security Checks & Recommendations

Before bucket creation, verify the following project-level configurations:

1.  **Restrict Sharing Org Policy**: Ensure
    `constraints/iam.allowedPolicyMemberDomains` is configured to restrict
    sharing outside of authorized organizational domains.
2.  **Access Transparency**: Ensure Access Transparency is enabled on the
    project to audit Google administrator access.
3.  **Location Org Policy**: Check `constraints/gcp.resourceLocations` to ensure
    bucket creation conforms to the organization's regional residency
    guidelines.
4.  **Cloud Audit Logging**: Ensure Cloud Audit Logging is enabled for the
    project to maintain an audit trail.
