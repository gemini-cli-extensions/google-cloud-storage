# Google Cloud Storage Skills

[![Install via skills.sh](https://img.shields.io/badge/skills.sh-install-green)](https://skills.sh/gemini-cli-extensions/google-cloud-storage)

This repository contains a growing collection of
[Agent Skills](https://agentskills.io/home) for
[Google Cloud Storage](https://cloud.google.com/storage). These skills deliver
vetted GCS expertise directly into your coding agent, letting you use natural
language prompts in your preferred CLI or IDE to work with your storage
resources — from everyday bucket and object management to file-system mounts
with Cloud Storage FUSE, access-error diagnostics, security assessments, and
infrastructure code generation.

> [!NOTE]
> This repository is under active development. More skills will be added
> over time.

> [!IMPORTANT]
> **We Want Your Feedback!** Please share your thoughts with us by
> opening an issue on
> [GitHub](https://github.com/gemini-cli-extensions/google-cloud-storage/issues).
> Your input is invaluable and helps us improve the project for everyone.

## Contents

-   [Installation](#installation)
-   [Available Skills](#available-skills)
-   [Prerequisites](#prerequisites)
-   [Authentication](#authentication)
-   [Additional Setup: GCS Security Assessment](#additional-setup-gcs-security-assessment)
-   [Example Use Cases](#example-use-cases)
-   [Security Reminder: Agent Environment Hardening](#security-reminder-agent-environment-hardening)
-   [Support](#support)
-   [Contributing](#contributing)
-   [License](#license)

## Installation

### Installing using [open agent skills tool](https://github.com/vercel-labs/skills)

```bash
npx skills add gemini-cli-extensions/google-cloud-storage
```

From the `npx` install command, you can select the specific skills from this
repo to install. The skills work with any compatible coding agent, including
Gemini CLI, Claude Code, Codex, and Antigravity CLI.

### Installing via a compatible Agent Plugins client

This repository is also a valid
[Agent Plugins](https://github.com/agentplugins/agent-plugins-spec) (v1) plugin.
Any
[Agent Plugins–compatible client](https://agent-plugins.org/compatible-clients)
(VS Code, Cursor, GitHub Copilot, Codex, Kiro, …) can install it directly using
its own built-in plugin command, by pointing at this repository:

```
https://github.com/gemini-cli-extensions/google-cloud-storage
```

## Available Skills

-   [**Google Cloud Storage Basics**](./skills/google-cloud-storage-basics/) —
    Everyday GCS expertise: create and configure buckets; upload, download, and
    transfer data; control access; manage storage classes, lifecycle, cost, and
    data protection — via the gcloud CLI, JSON/XML APIs, client libraries,
    Terraform, or Cloud Storage MCP servers.
-   [**Google Cloud Storage Bucket Architect**](./skills/google-cloud-storage-bucket-architect/)
    — Creates Google Cloud Storage (GCS) buckets: analyzes the workload
    (sensitive data, media hosting, ingestion, web hosting, archiving, backup,
    logging, analytics, AI/ML, or general-purpose), validates project-level
    security settings, and designs a secure-by-default, cost-effective
    configuration (location, storage class, security, lifecycle) before creating
    it via gcloud, JSON/REST API, Terraform, or SDK client libraries (C++, Java,
    Python, and Go).
-   [**Google Cloud Storage FUSE**](./skills/google-cloud-storage-fuse/) — Mount
    buckets as a POSIX file system with gcsfuse: decide when to use FUSE vs.
    direct storage reads, deploy tuned mounts on GKE, Compute Engine, and Cloud
    Run, size the file, stat, and list caches, keep file writes and ML
    checkpointing safe, and diagnose slow or costly mounts with gcsfuse metrics.
-   [**Google Cloud Storage Diagnostic**](./skills/google-cloud-storage-diagnostic/)
    — Root-cause access failures: diagnose 403 Permission Denied and other
    access errors by analyzing IAM policy bindings, ACLs, Uniform Bucket-Level
    Access, Bucket-Level IP Filtering, and VPC Service Controls perimeters, then
    walk through a verified fix.
-   [**GCS Security Assessment**](./skills/gcs-security-assessment/) — Assess
    the security posture of GCS projects and buckets against Google's
    [Secure AI Framework (SAIF)](https://saif.google/secure-ai-framework/saif-map):
    correlate real telemetry signals to surface **toxic combinations** of
    vulnerabilities — scenarios where individually low-risk configurations
    combine into a critical exposure — with actionable, verified remediation.
    Needs [additional setup](#additional-setup-gcs-security-assessment) for a
    complete assessment.

## Prerequisites

Ensure you have the following:

*   **A Google Cloud project** with the resources you want to work with.
*   **Google Cloud SDK (gcloud CLI):**
    [Install and initialize](https://cloud.google.com/sdk/docs/install) the
    gcloud CLI and ensure
    [Application Default Credentials (ADC)](https://cloud.google.com/docs/authentication/provide-credentials-adc)
    are configured.
*   **A compatible coding agent**, such as Gemini CLI, Claude Code, Codex, or
    Antigravity CLI.

## Authentication

Before using the skills, authenticate with Google Cloud so your agent can read
your storage resources and run any changes you approve. It is recommended to run
**both** of the following commands:

```bash
gcloud auth login
gcloud auth application-default login
```

*   **`gcloud auth application-default login`** is **required**: skill scripts
    use Application Default Credentials (ADC) to generate access tokens for GCP
    API calls.
*   **`gcloud auth login`** allows the agent (or you) to run standard `gcloud`
    commands to explore configurations or dig deeper into specific resources
    beyond what the skill scripts cover.

## Additional Setup: GCS Security Assessment

The GCS Security Assessment skill runs with nothing more than working
Application Default Credentials (see [Authentication](#authentication)) — there
is no required IAM permission. However, signals the skill cannot read are
reported as `UNKNOWN`, so for a complete assessment grant the recommended
**read-only** roles covering Storage Insights telemetry (bucket/object analysis)
and project-level posture (IAM and audit config, org policies, VPC Service
Controls, and Model Armor). See **[PERMISSIONS.md](./PERMISSIONS.md)** for the
full permission tables and a ready-to-apply custom IAM role
([`gcs-security-assessment-role.yaml`](./gcs-security-assessment-role.yaml)).

> [!TIP]
> For the best analysis, we highly recommend being a
> [Storage Intelligence](https://docs.cloud.google.com/storage/docs/storage-intelligence/overview)
> customer. When Storage Intelligence is enabled, the skill can query your
> Storage Insights datasets to perform deep, bucket-level and object-level
> assessments. Without it, the skill falls back to a project-level assessment
> only.

The other skills need no permissions beyond the [prerequisites](#prerequisites)
and whatever IAM access your identity already has to the buckets you work with.

## Example Use Cases

The skills cover the full storage lifecycle — provisioning, data movement,
file-system access, access control, troubleshooting, protection and compliance,
cost, security, and automation. Interact with Google Cloud Storage using natural
language, right from your coding agent:

### Design and provision storage for any workload

*   **Quick start:** "Create a new GCS bucket named 'audio-video-assets' in the
    'my-gcp-project' project"
*   **Sensitive data:** "Create a secure GCS bucket to store PII and other
    sensitive data. Make sure the data is protected against exfiltration and
    unauthorized public exposure"
*   **Media serving:** "I am building a high-performance media streaming service
    that delivers millions of high-definition images and videos to a global
    audience. Set up a Cloud Storage bucket as the origin, paired with a global
    Content Delivery Network (CDN), to minimize latency and ensure optimal
    streaming performance at scale"
*   **AI/ML workloads:** "I have a large-scale model training and checkpointing
    use case. Help me set up GCS to optimize performance"

### Mount buckets as a file system

*   **Workload fit:** "Should my ML training workload use Cloud Storage FUSE,
    native gs:// reads, or Filestore? It reads millions of small files every
    epoch"
*   **Tuned mounts:** "Help me mount the 'ml-datasets' bucket as a local file
    system with gcsfuse, with mount options tuned for high-throughput model
    training"
*   **GKE deployment:** "Deploy a gcsfuse mount on my GKE training cluster with
    the CSI driver, with caches sized for repeated reads of the training
    dataset"
*   **Performance diagnosis:** "My training job reads from a gcsfuse mount and
    GPU utilization is low. Diagnose whether the mount is the bottleneck and
    tune it"
*   **Cost diagnosis:** "My GCS bill spiked after we moved to gcsfuse. Figure
    out which mount options are causing the excess operations"

### Move, replicate, and migrate data at scale

*   **Cloud migration:** "Migrate the data in my S3 bucket 'legacy-exports' into
    a new GCS bucket"
*   **Disaster recovery:** "Set up continuous replication of bucket 'ops-bucket'
    to bucket 'vault-bucket-isolated', and ensure all the existing historical
    data is copied as well"
*   **Zero-downtime moves:** "Relocate my 'analytics-archive' bucket from
    us-east1 to us-central1 without downtime"

### Control who can access your data

*   **Temporary sharing:** "How can I temporarily give one of my users access to
    upload a large video to my bucket?"
*   **Least privilege:** "Give the analytics team read-only access to the
    'reports' bucket without granting them anything else in the project"

### Diagnose and fix access errors

*   **403 Permission Denied:** "User alice@example.com is getting a 403
    Permission Denied when trying to list objects in gs://my-team-bucket. Help
    me diagnose and fix it"
*   **Confusing denials:** "Diagnose why reading gs://data-bucket/object.txt
    fails even though I have object viewer permissions"
*   **IP filtering lockout:** "I am getting a 403 error on gs://my-secure-bucket
    due to IP filtering restrictions"
*   **Service agents:** "Pub/Sub notifications on my bucket stopped working
    after we enabled CMEK. Check whether the service agents have the right
    permissions"

### Protect data and meet compliance requirements

*   **Recovery:** "I accidentally deleted objects from the 'prod-reports'
    bucket. Can I get them back?"
*   **Immutability:** "Configure my 'audit-logs' bucket so objects cannot be
    deleted or modified for 7 years"

### Optimize storage costs

*   **Cost analysis:** "Analyze my buckets and recommend storage classes and
    lifecycle rules to reduce storage costs"
*   **Usage insight:** "Find my largest and least-accessed datasets across all
    buckets in the project"

### Assess and harden your security posture

*   **Targeted assessment:** "Assess the security posture of buckets [BUCKET_1],
    [BUCKET_2] in project [PROJECT_ID]"
*   **Project-wide assessment:** "Run a security assessment of project
    [PROJECT_ID] and show me the exact commands to remediate any toxic
    combinations you find"
*   **Follow-up investigation:** "Explain why the 'ml-training-data' bucket is
    flagged as a toxic combination, and show me the exact command to remediate
    the public access finding"

### Generate infrastructure and application code

*   **Terraform:** "Generate a Terraform configuration to provision a GCS bucket
    in us-central1 for application logs. Make sure public access is prevented
    and Uniform Bucket-Level Access is enabled, and add a lifecycle rule to
    transition logs to Nearline storage after 30 days and delete them after 365
    days"
*   **Client libraries:** "Generate Java code to upload a local directory to my
    'app-backups' bucket in parallel using the Cloud Storage client library"

### Set up and secure Cloud Storage MCP servers

*   **Guarded setup:** "Set up the Cloud Storage MCP server for my coding agent,
    and integrate Model Armor with it to screen tool calls for prompt injection"
*   **Authentication and tools:** "How do I authenticate and authorize with the
    remote Cloud Storage MCP server, and what tools are available on it?"
*   **Choosing a server:** "For downloading large files from my buckets, which
    Cloud Storage MCP server should I use?"
*   **Read-only enforcement:** "Lock down the Cloud Storage remote MCP server
    with an IAM deny policy so my agent can only call read-only tools"

### Build event-driven and AI-powered workflows

*   **Event notifications:** "Send a Pub/Sub notification whenever new objects
    land in my 'ingest' bucket so my pipeline can process them"
*   **Agentic workflows:** "Scan the 'retail-raw-products' bucket for assets
    related to 'ProductX', draft a promotional social media campaign listing,
    and write the draft output file to bucket 'retail-campaigns'"

## Security Reminder: Agent Environment Hardening

Your agent can execute tools and commands on your behalf. Protect your Google
Cloud resources by enforcing **The Principle of Least Privilege** across all
CLIs, MCP servers and other resources available to your agents.

*   **Service Accounts:** Use
    [service accounts](https://docs.cloud.google.com/docs/authentication/use-service-account-impersonation)
    instead of end user credentials to access Google Cloud resources.
*   **Limited Permissions:** Assign roles with
    [limited permissions](https://docs.cloud.google.com/iam/docs/roles-overview)
    to the service account that you're using for authentication.
*   **Principal Access Boundaries:** Prevent unwanted cross-org agent access by
    using
    [Principal Access Boundary policies](https://docs.cloud.google.com/iam/docs/principal-access-boundary-policies#use-case-one-project)
    to scope your agent to projects you intend it to access.
*   [Include a condition in the policy binding](https://docs.cloud.google.com/iam/docs/principal-access-boundary-policies#use-case-one-project)
    to ensure that the policy only applies to the service accounts that you
    intend to restrict.

You can read more
[here](https://docs.cloud.google.com/data-cloud-extension/vs-code/prompt-injection-risk)
on how to mitigate prompt injection attacks with Google Cloud MCP.

## Support

If you need help or encounter issues with these skills, search for existing
issues or open a new one in the
[GitHub Issue Tracker](https://github.com/gemini-cli-extensions/google-cloud-storage/issues).

## Contributing

We welcome contributions to improve these skills. You can help by:

*   [Reporting bugs or inaccuracies](https://github.com/gemini-cli-extensions/google-cloud-storage/issues)
    in the skill files.
*   Suggesting new skills to add to this repository by filing a feature request.

## License

You are free to copy, modify, and distribute these skills under the terms of the
Apache 2.0 license. See the `LICENSE` file for details.
