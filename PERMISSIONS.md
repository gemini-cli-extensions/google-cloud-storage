# GCS Skills Permissions Guide

This guide documents the Google Cloud IAM permissions used by the skills in this
repository. All access is **read-only**—the skills never mutate your resources.
More skills (and their permission requirements) will be added here over time.

## GCS Security Assessment Skill

The GCS Security Assessment skill performs a **read-only** security posture
assessment of Google Cloud Storage projects and buckets. It reads bucket and
object state via Storage Insights → BigQuery and gathers project-level posture
via REST. It never mutates target resources.

### Required

The skill requires an authenticated gcloud session. Run **both**:

```bash
gcloud auth login
gcloud auth application-default login
```

*   **`gcloud auth application-default login`** is required — the skill's
    scripts use Application Default Credentials (ADC) to generate access tokens
    for GCP API calls (the preflight `adc` check).
*   **`gcloud auth login`** is required for the agent to run `gcloud` commands
    during the assessment.

These are authentication requirements, not specific IAM permissions. Any
authenticated identity can run the skill; with no roles it still runs, but every
signal it cannot read is reported as `UNKNOWN`. There is no IAM permission in
the required tier.

### Recommended Permissions

Grant the read-only roles below for a complete assessment. All permissions are
read-only.

> [!IMPORTANT]
> **Permission scope:** Most permissions are granted at the
> **project** level, but three are **organization-scoped** and must be granted
> at the org level: `accesscontextmanager.policies.list`,
> `accesscontextmanager.servicePerimeters.list`, and
> `resourcemanager.folders.get`. Without an org-level grant, VPC Service
> Controls and org-hierarchy checks report `UNKNOWN`. The
> [custom role](#recommended-bundle-into-one-custom-role) below shows how to
> grant these at the org level.

#### Group A — Full bucket & object assessment (Storage Insights telemetry)

Without these, the assessment degrades to project-level only.

Permission                            | Purpose                               | Read-only role
:------------------------------------ | :------------------------------------ | :-------------
`storageinsights.datasetConfigs.list` | Discover/validate SI dataset configs  | `roles/storageinsights.viewer`
`bigquery.datasets.get`               | Read the linked SI BigQuery dataset   | `roles/bigquery.dataViewer`
`bigquery.tables.getData`             | Read the SI telemetry view/table data | `roles/bigquery.dataViewer`
`bigquery.jobs.create`                | Run the read-only telemetry query job | `roles/bigquery.jobUser`

#### Group B — Project-level posture

Used by the project posture evaluation. A missing permission marks that signal
`UNKNOWN`; the assessment continues.

Permission                                    | Purpose                                                  | Read-only role
:-------------------------------------------- | :------------------------------------------------------- | :-------------
`resourcemanager.projects.get`                | Resolve project number/parent                            | `roles/browser`
`resourcemanager.folders.get`                 | Traverse folder hierarchy to resolve org ID (for VPC-SC) | `roles/browser`
`resourcemanager.projects.getIamPolicy`       | Read Data Access audit-log config                        | `roles/iam.securityReviewer`
`orgpolicy.policy.get`                        | Read effective org policies (location/TLS/HTTP/HMAC)     | `roles/orgpolicy.policyViewer`
`accesscontextmanager.policies.list`          | Find the org's access policy                             | `roles/accesscontextmanager.policyReader`
`accesscontextmanager.servicePerimeters.list` | Check if project is in a VPC-SC perimeter                | `roles/accesscontextmanager.policyReader`
`modelarmor.floorSettings.get`                | Read Model Armor floor settings                          | `roles/modelarmor.floorSettingsViewer`
`modelarmor.templates.list`                   | Enumerate Model Armor templates                          | `roles/modelarmor.viewer`
`serviceusage.services.use`                   | Use a quota project for API requests                     | `roles/serviceusage.serviceUsageConsumer`

#### Notes

*   `bigquery.jobs.create` looks like a write but only creates a **read-only**
    query job. There is no read-only alternative for querying the Storage
    Insights views.
*   `accesscontextmanager.*` is evaluated at the **organization** level. Grant
    it there, or VPC Service Controls will report `UNKNOWN`.
*   `serviceusage.services.use` is a very broad permission that allows the
    principal to use services/quota for any project in the org. Consider adding
    this directly to the allowed project.

### Recommended: Bundle into One Custom Role

Rather than granting individual roles, we recommend defining a single read-only
custom role from
[`gcs-security-assessment-role.yaml`](./gcs-security-assessment-role.yaml).

Create the role at the **organization** level so the VPC-SC checks resolve:

```bash
gcloud iam roles create gcsSecurityAssessmentReader \
  --organization=ORG_ID --file=gcs-security-assessment-role.yaml
```

Grant it on the **project** (telemetry, IAM/audit, org policy, Model Armor,
quota project):

```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="user:ASSESSOR@EXAMPLE.COM" \
  --role="organizations/ORG_ID/roles/gcsSecurityAssessmentReader"
```

Also grant it on the **organization** (VPC-SC access policies are org-scoped):

```bash
gcloud organizations add-iam-policy-binding ORG_ID \
  --member="user:ASSESSOR@EXAMPLE.COM" \
  --role="organizations/ORG_ID/roles/gcsSecurityAssessmentReader"
```

**Scope caveat:** a project-only grant works for everything except the
org-scoped permissions noted above. If org-level access isn't available, drop
the `accesscontextmanager.*` and `resourcemanager.folders.get` lines and create
the role with `--project=PROJECT_ID`; VPC Service Controls and org-hierarchy
checks will then report `UNKNOWN`.
