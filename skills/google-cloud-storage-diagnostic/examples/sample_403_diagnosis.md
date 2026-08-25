# Sample Diagnostic Report: GCS 403 Permission Denied

This example demonstrates the expected output structure and tone when diagnosing
a Cloud Storage `403 Permission Denied` issue.

--------------------------------------------------------------------------------

## 1. Context & Scope Discovered

-   **Principal:**
    `serviceAccount:etl-runner@data-pipeline-prod.iam.gserviceaccount.com`
-   **Target Bucket / Object:**
    `gs://analytics-raw-events-prod/2026/data.parquet`
-   **Operation:** Read (`storage.objects.get`) via tagged command:

    ```bash
    CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
    gcloud storage cp
    ```

-   **Bucket Policy Mode:** Uniform Bucket-Level Access (UBLA) **Enabled**

--------------------------------------------------------------------------------

## 2. Root Cause Analysis

Telemetry inspection confirms that the bucket has **Uniform Bucket-Level Access
(UBLA)** enabled. Under UBLA, fine-grained Access Control Lists (ACLs) granted
directly on objects are ignored.

Although `etl-runner@data-pipeline-prod.iam.gserviceaccount.com` held an
object-level ACL (`READER`), it lacks a bucket-level IAM role granting
`storage.objects.get` (such as `roles/storage.objectViewer`). Consequently,
Cloud Storage rejects the read request with `403 Permission Denied`.

--------------------------------------------------------------------------------

## 3. Prescriptive Remediation

To restore read access under UBLA, grant `roles/storage.objectViewer` at the
bucket level:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="${CLOUDSDK_METRICS_ENVIRONMENT:+$CLOUDSDK_METRICS_ENVIRONMENT }gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-diagnostic)" \
gcloud storage buckets add-iam-policy-binding \
  gs://analytics-raw-events-prod \
  --member="serviceAccount:etl-runner@data-pipeline-prod.iam.gserviceaccount.com" \
  --role="roles/storage.objectViewer"
```

> **Confirmation Required:** Would you like me to execute this `gcloud storage
> buckets add-iam-policy-binding` command on your behalf? (Please reply **Y** or
> **N**.)
