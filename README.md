# Google Cloud Storage Skills

[![Install via skills.sh](https://img.shields.io/badge/skills.sh-install-green)](https://skills.sh/gemini-cli-extensions/google-cloud-storage)

This repository contains [Agent Skills](https://agentskills.io/home) for
[Google Cloud Storage](https://cloud.google.com/storage). These skills deliver
vetted GCS expertise directly into your coding agent, letting you use natural
language prompts in your preferred CLI or IDE to work with your storage
resources.

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
-   [GCS Security Assessment Skill](#gcs-security-assessment-skill)
    -   [Required Permissions](#required-permissions)
    -   [Authentication](#authentication)
    -   [Usage Examples](#usage-examples)
-   [Security Reminder: Agent Environment Hardening](#security-reminder-agent-environment-hardening)
-   [Support](#support)
-   [Contributing](#contributing)
-   [License](#license)

## Installation

```bash
npx skills add gemini-cli-extensions/google-cloud-storage
```

From the `npx` install command, you can select the specific skills from this
repo to install. The skills work with any compatible coding agent, including
Gemini CLI, Claude Code, Codex, and Antigravity CLI.

## Available Skills

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

### Authentication

Before running an assessment, authenticate with Google Cloud so the agent can
read your project telemetry and run any remediation you approve. It is
recommended to run **both** of the following commands:

```bash
gcloud auth login
gcloud auth application-default login
```

*   **`gcloud auth application-default login`** is **required**: the skill's
    scripts use Application Default Credentials (ADC) to generate access tokens
    for GCP API calls.
*   **`gcloud auth login`** allows the agent (or you) to run standard `gcloud`
    commands to explore configurations or dig deeper into specific resources
    beyond what the skill scripts cover.

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
