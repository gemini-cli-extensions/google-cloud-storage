# Phase 2: Draft Bucket Create Plan

This phase focuses on identifying the user's intended workload, mapping it to a
specific use case, and proposing a secure-by-default bucket configuration. This
configuration is created in a list format as a draft first, further instructions
will determine how the bucket is actually created.

## Step 1: Apply Secure-by-Default Settings

Regardless of the identified use case, the agent MUST explicitly configure and
recommend the following settings by default. If the user wants to change them,
the agent must obtain explicit confirmation and warn the user of potential
security risks.

*   **Uniform Bucket-Level Access (UBLA)**: Enabled.
*   **Enforced Restrict Encryption Types**: Restrict Customer-Supplied
    Encryption Keys (CSEK) unless explicitly required.
*   **Soft Delete**: Enabled with the default retention duration (7 days) to
    protect against accidental deletions.
    *   **Exception**: For **Rapid/Zonal** buckets, soft delete is NOT
        supported. You MUST explicitly disable it (set retention duration to 0).

### Public Access Prevention (PAP)

*   **Enforce PAP**: Enforced.
*   *Exception*: If and only if the identified use case explicitly requires
    public access (e.g. Static Website Hosting, Public Media Hosting) and the
    user has indicated this, PAP can be disabled.

--------------------------------------------------------------------------------

## Step 2: Determine the Use Case

Analyze the user's prompt and requirements to identify the most appropriate use
case. Refer to the table below to select the corresponding reference file, which
contains detailed configuration recommendations. You MUST include all "Highly
Recommended" and "Required" features, settings, and recommendations (including
monitoring, logging, and storage intelligence tools like Cloud Monitoring and
Storage Insights) from the selected reference file in your draft plan, even if
the user did not explicitly request them.

| Use Case     | Reference File                       | Description    | Example       |
:              :                                      :                : Prompts /     :
:              :                                      :                : Keywords      :
| :----------- | :----------------------------------- | :------------- | :------------ |
| **Sensitive  | `references/sensitive_data.md`       | Heavily        | "medical      |
: Data &       :                                      : regulated data : records",     :
: Compliance** :                                      : (PII, HIPAA,   : "PII", "SSN", :
:              :                                      : financial)     : "credit       :
:              :                                      : requiring      : card", "user  :
:              :                                      : strict         : account       :
:              :                                      : exfiltration   : data",        :
:              :                                      : prevention and : "compliance   :
:              :                                      : access         : audit"        :
:              :                                      : controls.      :               :
| **Media      | `references/media_hosting.md`        | Storage for    | "host         |
: Hosting &    :                                      : images,        : videos",      :
: CDN**        :                                      : videos, or     : "streaming    :
:              :                                      : audio assets   : assets", "CDN :
:              :                                      : acting as the  : origin",      :
:              :                                      : origin for a   : "serve static :
:              :                                      : CDN (e.g.,     : images        :
:              :                                      : Cloud CDN).    : globally"     :
| **Direct UGC | `references/ugc_ingestion.md`        | Allowing       | "upload files |
: Ingestion**  :                                      : client         : directly from :
:              :                                      : apps/browsers  : mobile app",  :
:              :                                      : to upload      : "signed URLs  :
:              :                                      : files directly : for user      :
:              :                                      : to GCS (often  : uploads",     :
:              :                                      : via signed     : "direct image :
:              :                                      : URLs) without  : ingestion"    :
:              :                                      : hitting app    :               :
:              :                                      : servers.       :               :
| **Static     | `references/static_website.md`       | Hosting static | "host static  |
: Website      :                                      : HTML/CSS/JS    : website",     :
: Hosting**    :                                      : files with     : "deploy       :
:              :                                      : custom domain  : single page   :
:              :                                      : mapping,       : app",         :
:              :                                      : accessible     : "landing page :
:              :                                      : publicly.      : on GCS",      :
:              :                                      :                : "custom       :
:              :                                      :                : domain        :
:              :                                      :                : index.html"   :
| **Long-Term  | `references/archiving_compliance.md` | Retention of   | "7 year       |
: Archive &    :                                      : data for legal : retention",   :
: Compliance** :                                      : or regulatory  : "SEC 17a-4    :
:              :                                      : requirements   : compliance",  :
:              :                                      : (7-10+ years)  : "WORM         :
:              :                                      : using Object   : storage",     :
:              :                                      : Retention      : "archive old  :
:              :                                      : (WORM) and     : tax           :
:              :                                      : Autoclass.     : documents"    :
| **Backup &   | `references/backup_dr.md`            | Highly durable | "database     |
: Disaster     :                                      : storage for    : backups",     :
: Recovery**   :                                      : backups,       : "ransomware   :
:              :                                      : database       : protection",  :
:              :                                      : dumps, and VM  : "disaster     :
:              :                                      : snapshots with : recovery      :
:              :                                      : protection     : replication", :
:              :                                      : against        : "immutable    :
:              :                                      : ransomware.    : backup"       :
| **Log        | `references/log_storage.md`          | High-volume,   | "VPC flow     |
: Storage**    :                                      : cost-effective : logs", "store :
:              :                                      : storage for    : app logs",    :
:              :                                      : application    : "audit trail  :
:              :                                      : logs, network  : dumps", "SIEM :
:              :                                      : logs, or audit : ingestion     :
:              :                                      : logs to be     : storage"      :
:              :                                      : parsed by      :               :
:              :                                      : SIEM.          :               :
| **AI &       | `references/storage_for_ai.md`       | Storage for    | "training     |
: Machine      :                                      : training       : dataset       :
: Learning**   :                                      : datasets,      : storage",     :
:              :                                      : model          : "model        :
:              :                                      : checkpoints,   : checkpoints", :
:              :                                      : or inference   : "Vertex AI    :
:              :                                      : assets,        : storage",     :
:              :                                      : optimized for  : "mount GCS    :
:              :                                      : high           : FUSE"         :
:              :                                      : throughput.    :               :

If the user's workload does not clearly fit any of the above, default to a
generic secure configuration and ask the user for clarification.

--------------------------------------------------------------------------------

## Handling Conflicts with Best Practices

If the user's prompt explicitly requests an architectural configuration (e.g.,
location, bucket type, replication) that contradicts the "Highly Recommended" or
"Required" settings in the matched use case reference file (or is explicitly
listed as "Do not use"), the agent MUST:

1.  **Advise Against**: Explicitly explain to the user why their requested
    configuration is not recommended for this use case, referencing the specific
    reasons in the reference document (e.g., cost, performance, replication
    limitations).
2.  **Recommend Best Practice**: Propose the recommended configuration from the
    reference document as the primary plan. Clearly label any alternative plan
    as discouraged and explicitly require risk confirmation acknowledgement from
    the user if they attempt to override strict requirements from the primary
    plan.

--------------------------------------------------------------------------------

## Location/Region Handling

If the user specifies a location for the bucket:

*   **Do NOT run commands** like `gcloud compute regions list` or `gcloud
    compute zones list` to verify locations.
*   **Invalid Locations**: If the user requests an invalid or unsupported GCS
    location (e.g., "Kenya"), you MUST:
    1.  Explicitly state that the requested location is not a valid Google Cloud
        Storage location.
    2.  Provide the link to the official Cloud Storage Locations documentation:
        https://cloud.google.com/storage/docs/locations.
    3.  Suggest alternative valid locations (e.g., the nearest region) and ask
        the user to select a valid location.
    4.  Do NOT generate creation commands for the invalid location.

--------------------------------------------------------------------------------

## Zonal (Rapid) Buckets Constraints

If the user requires a Zonal bucket (also known as a Rapid bucket, typically
used for AI/ML co-location):

*   **Storage Class**: You MUST explicitly set the storage class to `RAPID`. Do
    not default to `STANDARD`.
*   **Soft Delete**: You MUST explicitly disable soft delete (set duration to
    0). Soft delete is not supported for zonal buckets.
*   **Hierarchical Namespace (HNS)**: Enabled (Required for zonal buckets).
*   **Uniform Bucket Level Access (UBLA)**: Enabled (Required for zonal
    buckets).
*   **Location/Region Verification**: Trust the location and zone specified in
    the user's prompt (e.g. `us-east4` / `us-east4-a`). Do NOT waste time
    searching and verifying the location/zone exists. Error handling will be
    done later if the command/snippet fails.

--------------------------------------------------------------------------------

## Retention Policy Decisions (Bucket Lock vs. Object Lock)

Use retention configurations to protect data from deletion or modification for
compliance or regulatory reasons.

### 1. Bucket Lock (Bucket-level Retention Policy)

*   **Granularity**: Bucket-level. Applies to **all** objects in the bucket.
*   **Enforcement**: Once set, objects cannot be deleted or overwritten until
    the retention period expires.
*   **Locking**: Once locked, the retention period cannot be shortened or
    removed, and the policy cannot be unlocked.
*   **Best Use Case**: Uniform compliance requirements for all data (e.g.,
    keeping all transaction logs for 7 years).

### 2. Object Lock (Object Retention)

*   **Granularity**: Object-level. Enabled on the bucket, but configured
    individually per object.
*   **Enforcement**: Different objects can have different retention dates or no
    retention.
*   **Limitations**: Must be enabled at bucket creation time unless using the
    Google Cloud Console.
*   **Best Use Case**: WORM (Write Once, Read Many) compliance where different
    files have different lifespans (e.g., legal documents with varying case
    closure dates).

--------------------------------------------------------------------------------

## IP Filtering Decisions & Limitations

IP filtering allows you to restrict access to your bucket to specific public IP
ranges or VPC networks. If the user's workload requires IP filtering (e.g.,
sensitive data use case), the agent MUST consider the following limitations:

*   **Maximum IP CIDR blocks**: A maximum of 200 IP CIDR blocks (public and VPC)
    can be specified per bucket.
*   **Maximum VPC networks**: A maximum of 25 VPC networks can be specified per
    bucket.
*   **Regional endpoints**: Regional endpoints only work with IP filtering when
    using Private Service Connect (PSC).
*   **IPv6 and gRPC**: IP filtering with gRPC direct path is not supported on
    IPv4-only VMs. If using gRPC direct path, IPv6 must be enabled on the VPC
    network.
*   **Google Cloud Service Compatibility**: Enabling IP filtering restricts
    access for several Google Cloud services. **Do NOT use IP filtering** if the
    bucket needs to be accessed by:
    *   **BigQuery**: For loading data, exporting table data, exporting query
        results, or querying external tables.
    *   **App Engine**: Standard environment applications, unless they access
        GCS through a VPC.
    *   **Cloud Shell**: IP filtering does not support Cloud Shell.

--------------------------------------------------------------------------------

## Step 3: Present the Draft Plan

The agent MUST present the draft plan to the user in a structured format and
explicitly ask for confirmation before proceeding, unless the user has already
explicitly requested the final commands or code snippet in their initial prompt.
If the user requested the final output directly, the agent may present the plan
and immediately proceed to Phase 3 to generate the output in the same response,
while still warning that they should review the plan.

> [!CAUTION]
>
> If the draft plan includes **Bucket Lock (Retention Policy)** or **Object Lock
> (Per-Object Retention)**, the agent **MUST** explicitly warn the user that
> locking the policy is irreversible. Clearly state that once locked, the
> retention period cannot be shortened or removed, and data cannot be deleted or
> overwritten by anyone—including project administrators and Google Cloud
> Support—until the retention period expires. Proceed only after explicitly
> confirming whether the user wants to set the policy to "Locked" or "Unlocked"
> and for how long.

### Example Presentation Format

```markdown
### Draft Bucket Creation Plan

Based on your requirements, we will configure a bucket optimized for **[Use Case Name]** (refer to `references/[use_case_file].md` for details).

**Proposed Configurations:**

*   **Bucket Name**: `[proposed-bucket-name]`
*   **Project**: `[project-id]`
*   **Location**: `[location]` (Default: Multi-region US if unspecified by user and use case reference)
*   **Storage Class**: `[storage-class]` (Default: STANDARD)
*   **UBLA**: Enabled (✅ Secure Default)
*   **Public Access Prevention (PAP)**: Enforced (✅ Secure Default)
*   **Encryption Enforcement**: CSEK Restricted (✅ Secure Default)
*   **Soft Delete**: Enabled (7 Days) (✅ Secure Default)
*   **Use-case specific settings**:
    *   `[Setting 1 (e.g., Lifecycle rule: delete after 30 days)]`
    *   `[Setting 2 (e.g., Autoclass: enabled)]`
*   **Other Recommendations**:
    *   `[Monitoring or logging recommendations (e.g., Cloud Monitoring, Cloud Logging, Storage Insights)]`

Does this draft plan look correct? Please confirm if you'd like to proceed or if you want to make any adjustments.
```

## Documentation

-   [Enforce Bucket Encryption Types](https://cloud.google.com/storage/docs/encryption/enforce-encryption-types)
