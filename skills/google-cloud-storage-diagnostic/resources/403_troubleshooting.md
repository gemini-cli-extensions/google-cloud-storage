# Cloud Storage 403 Permission Denied Diagnostic Guide

Use this step-by-step diagnostic guide whenever a principal (User, Service
Account, or Group) receives a `403 Permission Denied` error when accessing a
Google Cloud Storage (GCS) bucket or object. Follow the steps sequentially.

> [!IMPORTANT]
>
> **Always verify whether Uniform Bucket-Level Access (UBLA) is enabled before
> checking Object ACLs.** If UBLA is enabled, object-level ACLs are ignored.

--------------------------------------------------------------------------------

## Step 1: Check for Common Edge Cases First

Before checking IAM policies, check if the request falls into one of these edge
cases:

-   **Signed URLs:** If the user is using a Signed URL, a 403 usually indicates
    that the canonical string used to sign the request does not match the
    incoming request headers (e.g., mismatched `Content-Type`), or the URL has
    expired. Verify the signature generation.
-   **Cookieauth (Browser Access):** Accessing `storage.cloud.google.com` URLs
    in a browser uses cookie authentication. If the user has multiple Google
    Accounts logged in, the browser may send the wrong identity cookie. Also,
    having Data Access Logging enabled can conflict with Cookieauth and cause
    consistent 403 errors in the browser. Advise testing in an Incognito window
    or using the API/CLI (`gcloud`).
-   **Bucket IP Filtering / Firewalls:** Check if the bucket has IP filtering or
    Organization Policy restrictions blocking the caller's source IP address.
-   **Sanctions / Territory Blocks:** Requests originating from embargoed or
    sanctioned regions return 403 regardless of IAM permissions.
-   **Compute Instance API Scopes:** If running inside a Compute Engine VM,
    legacy OAuth API scopes (e.g., `devstorage.read_only`) override IAM roles
    and cause 403s on write/delete operations. Check with the following command:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud compute instances describe {instance_name} --zone={zone} --format="json(serviceAccounts)"
    ```

    And if restricted, explicitly advise updating via:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud compute instances set-service-account INSTANCE --scopes=cloud-platform
    ```

    Do not recommend console workarounds.

-   **Auxiliary Permissions (Recursive Operations):** Operations like `gcloud
    storage rm -r` require `storage.objects.list` in addition to
    `storage.objects.delete`. A principal with only delete access will get 403
    when deleting recursively.

-   **Propagation Delay:** IAM policy modifications take up to 2–7 minutes to
    propagate globally. Check when the binding was added.

-   **IAM Deny Policies:** Explicit IAM Deny policies
    (`iam.googleapis.com/DenyPolicy`) take absolute precedence over standard
    Allow roles and cannot be bypassed.

-   **Client-Side ADC Mismatch:** Verify `gcloud auth list` or active
    Application Default Credentials (`GOOGLE_APPLICATION_CREDENTIALS`) match the
    expected account.

--------------------------------------------------------------------------------

## Step 2: Check IAM Bindings (Bucket and Project Level)

Check the IAM policy on the bucket to see if the principal has the required role
for the operation:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud storage buckets get-iam-policy gs://{bucket_name}
```

### Required Permissions by Operation

| Operation                  | Minimum Role / Permissions Required |
| :------------------------- | :---------------------------------- |
| **Read Object**            | `roles/storage.objectViewer`        |
:                            : (`storage.objects.get`)             :
| **Write Object**           | `roles/storage.objectCreator` or    |
:                            : `roles/storage.objectAdmin`         :
| **List Bucket**            | `roles/storage.objectViewer`        |
:                            : (`storage.objects.list`)            :
| **Delete Object**          | `roles/storage.objectAdmin`         |
:                            : (`storage.objects.delete`)          :
| **Read Bucket Metadata**   | `roles/storage.bucketViewer`        |
:                            : (`storage.buckets.get`)             :
| **Read Bucket IAM Policy** | `roles/iam.securityReviewer`        |
:                            : (`storage.buckets.getIamPolicy`)    :

### Handle Inspection Permission Denials (`403 on get-iam-policy`)

If running `gcloud storage buckets get-iam-policy` returns `403 Permission
Denied`:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud storage buckets get-iam-policy gs://{bucket_name}
```

> [!WARNING]
> **CRITICAL RULE: DO NOT ASSUME MISSING IAM ROLES WHEN INSPECTION IS
> BLOCKED BY PERIMETERS**
>
> A `403 Permission Denied` on `get-iam-policy` can occur either because the
> active identity lacks `storage.buckets.getIamPolicy` permissions, OR because
> perimeter security controls (**VPC Service Controls**, **Organization Deny
> Policies**, or **IP Filtering**) are actively blocking API calls to the
> bucket.
>
> **DO NOT prescribe granting IAM roles (such as `roles/iam.securityReviewer` or
> custom roles) when perimeter security or log denials are present**, as
> granting IAM roles will NOT bypass VPC-SC or perimeter blocks.
>
> Instead: 1. Check Cloud Audit Logs (`gcloud logging read`) or inspect for
> `vpcServiceControlsUniqueIdentifier` and network rejection status
> (`protoPayload.status.code=7`). 2. If VPC-SC or network perimeter controls are
> suspected or log access is denied, explicitly inform the user that a perimeter
> restriction (such as VPC-SC or IP Filtering) may be blocking access, and that
> adding IAM roles will not resolve perimeter blocks. 3. If perimeter controls
> are ruled out and the caller simply lacks bucket IAM inspection permissions,
> recommend granting the least-privilege role `roles/iam.securityReviewer` (or a
> custom role containing exactly `storage.buckets.getIamPolicy`). **NEVER**
> recommend `roles/storage.bucketViewer` (which contains only
> `storage.buckets.get` and `storage.buckets.list` and cannot view IAM policies)
> or over-privileged roles such as `roles/storage.admin`. 4. Alternatively,
> fallback to project-level IAM policy checks if the caller has project-level
> view access:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud projects get-iam-policy {project_id} \
  --flatten="bindings[].members" \
  --filter="bindings.members:{principal_email}"
```

--------------------------------------------------------------------------------

## Step 3: Check Legacy ACLs & Uniform Bucket-Level Access (UBLA)

Check if Uniform Bucket-Level Access (UBLA) is enabled:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud storage buckets describe gs://{bucket_name} --format="value(uniform_bucket_level_access)"
```

-   **If UBLA is `Enabled=True`:** Object ACLs are completely ignored. All
    access must be evaluated and granted exclusively via IAM. You MUST
    explicitly recommend running the tagged command to verify if they lack the
    required IAM roles that would substitute for their old ACLs:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets get-iam-policy gs://{bucket_name}
    ```

    Do not suggest modifying object ACLs.

-   **If UBLA is `Enabled=False` (Fine-grained ACLs):** If IAM does not grant
    access, inspect the bucket and object-level ACLs. When inspecting ACLs, you
    MUST use `--format="json(acl)"` to ensure you see the full JSON output,
    because the default output truncates long ACL lists.

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets get-iam-policy gs://{bucket_name}

    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets describe gs://{bucket_name} --format="json(acl)"
    ```

    (You can also check the specific object if the bucket ACL doesn't explain
    the denial, using the tagged command:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage objects describe gs://{bucket_name}/{object_name} --format="json(acl)"
    ```

    )

--------------------------------------------------------------------------------

## Step 4: Validate Service Agents

Certain Google Cloud services use specialized service agent accounts to access
GCS on behalf of the user. Ensure the relevant service agent (e.g.,
`service-{PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com`) has the
correct roles (like `roles/storage.admin` or `roles/pubsub.publisher`).

--------------------------------------------------------------------------------

## Step 5: Check VPC Service Controls (VPC-SC)

If the principal has correct IAM/ACL but still gets 403, VPC-SC may be blocking
access. Usually, a VPC-SC block results in a specific error message like: `Error
403: Request is prohibited by organization's policy.
vpcServiceControlsUniqueIdentifier: ...`

Look for rejections in the VPC-SC audit logs by querying the unique ID provided
in the error message:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud logging read \
  'protoPayload.metadata."@type"="type.googleapis.com/google.cloud.audit.VpcServiceControlAuditMetadata" AND protoPayload.metadata.vpcServiceControlsUniqueId="UNIQUE_ID_HERE"' \
  --limit=1 --format=json --project=PROJECT_ID
```

--------------------------------------------------------------------------------

## Step 6: Propose Remediation and Re-Verify

Once the gap is identified, synthesize a response similar to this format:

> "I used the GCS Diagnostic skill to understand the current IAM bindings and
> figure out why principal `{principal_email}` is receiving a 403 Permission
> Denied error. I identified missing roles (`roles/storage.objectViewer`). I
> will run the following command to fix it:"

```bash
# Example for a User:
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud storage buckets add-iam-policy-binding gs://{bucket_name} \
  --member="user:alice@example.com" \
  --role="roles/storage.objectViewer"

# Example for a Service Account:
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud storage buckets add-iam-policy-binding gs://{bucket_name} \
  --member="serviceAccount:service-<project-number>@gcp-sa-storageinsights.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

> [!NOTE]
>
> We do not propose direct IAM remediation in every case. If the root cause is
> an Organization level Deny Policy, VPC-SC, or IP Filtering, IAM roles will not
> fix the issue. Instead, log the failure reason and advise the user to reach
> out to their Organization or Project Administrator for help.

> [!CAUTION]
>
> As mandated at the top of the main `SKILL.md`, **never auto-execute
> remediation or configuration-changing commands.** Print the exact command,
> explain the proposed change, and wait for explicit user confirmation (Y/N)
> before executing any remediation.

--------------------------------------------------------------------------------

## Step 7: Check Audit Logs

Audit logs often contain the exact, explicit reason *why* the 403 occurred
(e.g., if a specific IAM deny policy was hit). Check the Google Cloud Console or
use `gcloud` to review the Cloud Audit Logs for the specific bucket and
principal.

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud logging read "resource.type=gcs_bucket AND resource.labels.bucket_name=\"{bucket_name}\" AND protoPayload.authenticationInfo.principalEmail=\"{principal_email}\"" \
  --project="{project_id}" --limit=10
```

### What to do if Audit Logs are Inaccessible, Excluded, or Empty

> **CRITICAL BUCKET LOG SCOPING RULE**: Always ensure log queries filter
> explicitly by `resource.labels.bucket_name="{bucket_name}"`. Never use audit
> log events from *other* buckets in the project to infer the root cause of
> access denials on the target bucket. If `gcloud logging read` returns `403
> Permission Denied`, `Project not found or deleted`, or an empty array `[]` for
> `{bucket_name}` (due to missing `roles/logging.viewer` permissions, disabled
> audit logs, or log exclusions), explicitly inform the user that you lack log
> visibility for this target bucket and proceed to **Remediation in Log-Denied
> Scenarios** below.

**Remediation in Log-Denied Scenarios:** Explicitly suggest to the user that
they might be hitting an advanced network restriction (such as Bucket-Level IP
Filtering or VPC Service Controls) and explicitly advise them to ask their
Project Owner/Administrator to check the Cloud Audit Logs including the filter
`protoPayload.status.code=7` for identifiers like
`vpcServiceControlsUniqueIdentifier`. Do NOT attempt to run blind remediation
commands or fall into an infinite loop trying to change credentials.

## Step 8: Check Advanced Non-IAM Storage Denials

If standard IAM allow policies, UBLA/ACLs, and VPC-SC checks are satisfied but a
`403 Permission Denied` still occurs, check for these advanced constraints:

### 1. Requester Pays or Disabled Billing

If the bucket has Requester Pays enabled (`requesterPays: true`), or if the
project's billing account is disabled, requests without a billing project
parameter will fail with `403 Permission Denied`.

-   **Diagnostic Command:** Check bucket billing metadata:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets describe gs://{bucket_name} --format="default(requester_pays)"
    ```

-   **Remediation:** Explain that the user must pass their billing project
    explicitly (e.g. `--billing-project={project_id}`).

### 2. Retention Policy / Legal Hold Deletion Block

If a user with full `roles/storage.objectAdmin` (`delete` permissions) receives
a `403 Permission Denied` when attempting to delete or overwrite an object,
check if the bucket or object is protected by a Retention Policy or Legal Hold.

-   **Diagnostic Command:** Check object and bucket retention metadata:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets describe gs://{bucket_name} --format="default(retention_policy)"
    ```

-   **Remediation:** Do not run or suggest any remediation commands for
    retention policies. Explicitly explain that this 403 error is an
    un-bypassable data protection mechanism working as intended, and the object
    cannot be deleted or overwritten until the retention period expires.

### 3. Wrong Identity / Application Default Credentials (ADC) Mismatch

If a user expects access because their personal user account has correct IAM
roles, but their local CLI (`gcloud`) or client library script returns `403`,
check active authentication identities:

-   **Diagnostic Command:** Check active authentication identities:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud auth list
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud config get-value account
    ```

-   **Remediation:** Instruct the user to re-authenticate via `gcloud auth
    login` and `gcloud auth application-default login`.

### 4. Explicit IAM Deny Policies

If the 403 error message explicitly states: `Request is prohibited by
organization's policy` (without listing a VPC-SC ID), or if logging implies a
Deny policy was hit (`iam.googleapis.com/DenyPolicy`), standard allow roles are
entirely overridden. The agent must verify if an explicit Deny policy exists at
the project layer (or higher).

-   **Diagnostic Command:** The agent MUST print this exact command to the user
    verbatim, without summarizing or omitting it (and suggest checking
    `--attachment-point=organizations/{org_id}` if project-level results are
    empty but the 403 error persists):

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud iam policies list \
      --attachment-point=cloudresourcemanager.googleapis.com/projects/{project_id} \
      --kind=denypolicies
    ```

-   **Remediation:** Check the policy returned. Explicitly inform the user that
    Deny policies take precedence over Allow policies. Advise the user to
    contact their Organization Administrator to resolve the conflict.

### 5. Bucket-Level IP Filtering

If a principal has valid IAM permissions but receives a `403 Permission Denied`,
the bucket might have IP filtering enabled blocking the caller's IP address.
Because a direct metadata query (`describe`) against the bucket would also be
blocked by the IP filter, you MUST route your diagnostic check through Cloud
Audit Logs via the Cloud Logging API, which is completely unaffected by the
bucket's local network filter.

-   **Diagnostic Command:** Parse the 403 log entry for the exact violation
    reason (you will need the target project ID):

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud logging read "resource.type=gcs_bucket AND resource.labels.bucket_name=\"{bucket_name}\" AND protoPayload.authenticationInfo.principalEmail=\"{principal_email}\"" \
      --project="{project_id}" --limit=5 --format=json
    ```

    Look for an explicit violation reason in the log payload to confirm the
    request's origin IP breached the bucket's allowed CIDR ranges.

-   **Remediation:** Explicitly advise the user to append their IP address to
    the allowed list without overwriting the existing configuration.

    **CRITICAL RULE - NEVER ADVISE CLEARING OR OVERWRITING EXISTING IP FILTER
    RANGES:** When prescribing IP filter remediation instructions to the user,
    **NEVER instruct the user to clear or wipe out existing
    `allowedIpCidrRanges`**, as clearing existing ranges will immediately lock
    out other authorized users and services. Instruct the user to fetch the
    current `ip_filter_config`, append their new CIDR range (e.g.
    `TARGET_IP_HERE/32`) to the existing `allowedIpCidrRanges` array, and
    re-apply the updated JSON configuration.

    **Handling Lockouts During Remediation:** If bucket management operations
    (`gcloud storage buckets describe` or `gcloud storage buckets update`) fail
    due to IP filter lockouts when attempting remediation, advise the user to
    grant the IAM permission `storage.buckets.exemptFromIpFilter` (or a role
    containing this permission) to the principal modifying the bucket, or
    execute the update command from an allowed network host. The
    `storage.buckets.exemptFromIpFilter` permission exempts the principal from
    IP filter enforcement, enabling them to inspect and update the bucket's IP
    filter config. Do **NOT** try to use this to bypass IP Filter restrictions,
    it should only be used to update the IP Filter configuration itself in a
    bucket lockout scenario.

    Provide instructions to fetch the current configuration, modify it, and
    apply it:

    ```bash
    # 1. Fetch the current configuration:
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets describe gs://{bucket_name} --format="json(ip_filter_config)" > current_filter.json

    # 2. Add TARGET_IP_HERE/32 to the allowedIpCidrRanges list in the JSON above,
    # save it to updated_filter.json, and apply:
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage buckets update gs://{bucket_name} --ip-filter-file=updated_filter.json
    ```
