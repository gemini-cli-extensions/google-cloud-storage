# Google Cloud Storage Skills

[![Install via skills.sh](https://img.shields.io/badge/skills.sh-install-green)](https://skills.sh/gemini-cli-extensions/google-cloud-storage)

This repository contains a growing collection of
[Agent Skills](https://agentskills.io/home) for
[Google Cloud Storage](https://cloud.google.com/storage). These skills deliver
vetted GCS expertise directly into your coding agent, letting you use natural
language prompts in your preferred CLI or IDE to work with your storage
resources — from everyday bucket and object management to security assessments
and infrastructure code generation.

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
-   [Example Use Cases](#example-use-cases)
-   [Google Cloud Storage Basics Skill](#google-cloud-storage-basics-skill)
-   [GCS Security Assessment Skill](#gcs-security-assessment-skill)
    -   [Required Permissions](#required-permissions)
    -   [Usage Examples](#usage-examples)
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

-   [**Google Cloud Storage Basics**](#google-cloud-storage-basics-skill) —
    Everyday GCS expertise: create and configure buckets; upload, download, and
    transfer data; control access; manage storage classes, lifecycle, and data
    protection; mount buckets with gcsfuse; and work through the gcloud CLI,
    JSON/XML APIs, client libraries, Terraform, or Cloud Storage MCP servers.
-   [**Cloud Storage FUSE**](./skills/google-cloud-storage-fuse/) — Advanced
    Cloud Storage FUSE (gcsfuse) expertise: guide when to use FUSE vs. direct
    storage reads, optimize mount performance and caching across GKE, Compute
    Engine, and Cloud Run, ensure safe file writes and ML checkpointing, and
    diagnose speed or cost issues using telemetry metrics.
-   [**GCS Security Assessment**](#gcs-security-assessment-skill) — Assesses the
    security posture of Google Cloud Storage projects and buckets, identifying
    toxic combinations of vulnerabilities and checking SAIF compliance.

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

## Example Use Cases

The skills cover the full storage lifecycle — provisioning, data movement,
access control, protection and compliance, cost, security, and automation.
Interact with Google Cloud Storage using natural language, right from your
coding agent:

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
*   **Troubleshooting:** "I got a 403 Forbidden error. Help me diagnose and fix
    it"

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

### Generate infrastructure and application code

*   **Terraform:** "Generate a Terraform configuration to provision a GCS bucket
    in us-central1 for application logs. Make sure public access is prevented
    and Uniform Bucket-Level Access is enabled, and add a lifecycle rule to
    transition logs to Nearline storage after 30 days and delete them after 365
    days"
*   **Client libraries:** "Generate Java code to upload a local directory to my
    'app-backups' bucket in parallel using the Cloud Storage client library"
*   **File-system access:** "Help me mount the 'ml-datasets' bucket as a local
    file system with gcsfuse, with mount options tuned for high-throughput model
    training"

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

## Google Cloud Storage Basics Skill

The Google Cloud Storage Basics skill covers day-to-day work with GCS: bucket
creation and configuration, object and folder management, uploads, downloads,
and large-scale transfers, access control (IAM, ACLs, signed URLs, public access
prevention), storage classes and lifecycle management, data protection
(versioning, encryption, retention, soft delete), gcsfuse mounts, and
performance tuning. It guides your agent across the gcloud CLI, JSON and XML
APIs, client libraries, Terraform, and Cloud Storage MCP servers, backed by the
curated reference docs in
[`skills/google-cloud-storage-basics/`](./skills/google-cloud-storage-basics/).

No permissions are required beyond the [prerequisites](#prerequisites) and
whatever IAM access your identity already has to the buckets you work with.

## GCS Security Assessment Skill

The GCS Security Assessment skill is grounded in Google's
[Secure AI Framework (SAIF)](https://saif.google/secure-ai-framework/saif-map).
Rather than emitting isolated static alerts, it correlates real telemetry
signals gathered from your project to surface **toxic combinations** of
vulnerabilities—scenarios where individually low-risk configurations combine to
create a critical exposure—and provides actionable, verified remediation.

> [!TIP]
> For the best analysis, we highly recommend being a
> [Storage Intelligence](https://docs.cloud.google.com/storage/docs/storage-intelligence/overview)
> customer. When Storage Intelligence is enabled, the skill can query your
> Storage Insights datasets to perform deep, bucket-level and object-level
> assessments. Without it, the skill falls back to a project-level assessment
> only.

### Required Permissions

The only hard requirement is working **Application Default Credentials** (see
[Authentication](#authentication)). There is no required IAM permission—any
authenticated identity can run the skill, though signals it cannot read are
reported as `UNKNOWN`.

For a complete assessment, grant the recommended **read-only** roles covering
Storage Insights telemetry (bucket/object analysis) and project-level posture
(IAM and audit config, org policies, VPC Service Controls, and Model Armor). See
**[PERMISSIONS.md](./PERMISSIONS.md)** for the full permission tables and a
ready-to-apply custom IAM role
([`gcs-security-assessment-role.yaml`](./gcs-security-assessment-role.yaml)).

### Usage Examples

Interact with your coding agent using natural language:

*   **Assess an entire project:** `Assess the security posture of project
    [PROJECT_ID]`
*   **Assess a specific subset of buckets:** `Assess the security posture of
    buckets [BUCKET_1], [BUCKET_2] in project [PROJECT_ID]`
*   **Follow-up investigation:** After an assessment, ask the agent to drill
    into a finding—for example, "Explain why the `ml-training-data` bucket is
    flagged as a toxic combination" or "Show me the exact command to remediate
    the public access finding."

The agent works through a fixed, auditable sequence of phases—discovering scope
and gathering telemetry, classifying buckets, evaluating baseline security,
analyzing toxic combinations, and producing a formatted report—so you can trace
every finding back to a signal it actually collected.

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
