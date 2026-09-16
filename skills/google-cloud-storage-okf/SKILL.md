---
name: google-cloud-storage-okf
description: >-
  Experimental, generic, and powerful skill for token-efficient search, semantic
  navigation, and progressive disclosure of unstructured or semi-structured objects
  (PDFs, logs, JSON/CSV dumps, media, large documents) in Google Cloud Storage (GCS)
  using the Open Knowledge Format (OKF). Beyond basic retrieval, agents can
  creatively apply this skill to a broad spectrum of search and reasoning tasks,
  including: (1) high-precision search and point-queries within large objects without
  loading full content into context; (2) multi-hop cross-document search and
  synthesis across multiple cloud objects; (3) searching and temporal reasoning
  across chronologically partitioned log streams, audit trails, and incident
  timelines; and (4) creating reusable Table of Contents metadata for downstream
  agents. Use proactively whenever searching, querying, or interacting with gs://
  URIs where full-object downloads would waste tokens, degrade context quality, or
  exceed window limits.
license: Apache-2.0
metadata:
  version: v1
  publisher: google
  tags:
    - gcs
    - okf
    - search
    - semantic-search
    - open-knowledge-format
    - progressive-disclosure
    - mcp
  category: storage
  support_tier: primary
---

# Google Cloud Storage OKF Skill

Use the `google-cloud-storage-okf` skill to efficiently navigate, inspect, and
extract targeted byte ranges from unstructured Google Cloud Storage (`gs://`)
objects via progressive disclosure, instead of reading or dumping entire files
into the context window.

## Open Knowledge Format (OKF) in GCS

The
[Open Knowledge Format (OKF)](https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing)
establishes an open standard for attaching self-describing, AI-ready semantic
knowledge directly to data assets without mutating raw content.

While OKF at the catalog/dataset level organizes knowledge across tables into
concept documents, **`google-cloud-storage-okf` adapts OKF to object storage**:

-   **Native Embedding**: Stores the OKF manifest directly in the blob's **GCS
    Object Context** (`custom_contexts`), eliminating disconnected sidecar
    files.
-   **Progressive Disclosure**: Provides a structured 3-tier access pattern
    (`peek` → `list_regions` → `expand`) so AI agents can navigate and extract
    information from multi-GB files with minimal context window overhead.

## GCS Object Context vs. Custom Metadata

In Google Cloud Storage (GCS), there is a fundamental distinction between
**Object Context** and **Custom Metadata**:

-   **GCS Object Context (`custom_contexts` / `contexts.custom`)**: A dedicated,
    structured context layer in GCS designed for AI agent knowledge, semantic
    indices, and progressive disclosure manifests. **OKF manifests are targeted
    primarily at GCS Object Context.**
-   **GCS Custom Metadata (`metadata` / `x-goog-meta-*`)**: Traditional
    key-value pairs used for generic user tagging and legacy object attributes.
    Custom metadata is separate from Object Context.

OKF keys (such as `okf.sum`, `okf.r.000`, `okf.created_at`, and
`okf.src_generation`) are written directly to **GCS Object Contexts**
(`custom_contexts`).

### Client SDK Compatibility & Architecture

The skill provides dual-layer compatibility across different versions of the
`google-cloud-storage` Python SDK:

-   **Newer / Latest SDK**: If the client installation exposes higher-level
    typed classes (`ObjectContexts`, `ObjectCustomContextPayload`), the skill
    uses them to populate and read `blob.contexts`.
-   **Standard / Older SDK**: If higher-level classes are not yet exported in
    the local SDK version, the skill drops down to direct REST JSON payload
    injection (`blob._properties["contexts"]` / `blob._patch_property`) and
    signals `blob._changes`. When `blob.patch()` executes, the SDK transmits the
    standard HTTP REST `PATCH` request to GCS.
-   **Read Compatibility**: The skill inspects both `blob.contexts` and raw
    server response fields in `blob._properties["contexts"]`, guaranteeing that
    Object Contexts remain 100% readable and writable across all customer
    environments without startup import failures.

--------------------------------------------------------------------------------

## Core Architecture & Progressive Disclosure

GCS-OKF stores lightweight, self-contained Table of Contents (TOC) metadata
directly inside **GCS Object Context** on the original blob itself without
modifying or duplicating the underlying object data:

-   **Tier 0 (`peek`)**: High-level summary card to quickly gauge relevance.
-   **Tier 1/2 (`list_regions`)**: Semantic Table of Contents detailing
    contiguous regions with inclusive byte ranges, titles, and keywords.
-   **Tier 2/3 (`expand`)**: Precise byte-range reader retrieving targeted
    slices based on region boundaries.
-   **Generative Layer (`write_okf`)**: Persists newly generated OKF indices
    into GCS Object Context.

```
+-------------------------------------------------------------+
| 1. peek(gs_uri)                                             |
|    -> Evaluate relevance & inspect existing Object Contexts |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 2. list_regions(gs_uri)                                     |
|    -> Locate specific chapters/sections and byte boundaries |
+-------------------------------------------------------------+
                              |
                              v
+-------------------------------------------------------------+
| 3. expand(gs_uri, start_byte, end_byte)                     |
|    -> Read exact byte-range slice into context              |
+-------------------------------------------------------------+
```

--------------------------------------------------------------------------------

## Setup (Read Before Any OKF Call)

Every OKF verb is served by the `google-cloud-storage-okf` MCP server. If that
server is not registered with your MCP client, the tools do not exist in your
session and no OKF work is possible.

### Tool Availability Gate

**Before the first OKF step of any task, you MUST confirm that the MCP tools
`peek`, `list_regions`, `expand`, and `write_okf` are all present in your tool
list.** They may carry a harness-specific server-name prefix; a prefixed name
counts as present.

-   **All four present**: proceed with the OKF workflow.
-   **Any one missing**: do NOT start the workflow. Tell the user the server is
    not registered with this client, relay the **One-Time Setup** steps below,
    and **STOP**. Do not resume OKF work until all four tools are bound.

### Never Bypass the MCP Server

**NEVER** import or execute `scripts/core.py` or `scripts/mcp_server.py`
directly as a substitute for the MCP tools — for example `python3 -c "import
core; core.peek(...)"`, or launching `mcp_server.py` as a module in a subshell
and driving it by hand. The server MUST be registered with the harness so that
every OKF call goes through MCP.

### One-Time Setup

1.  Install the **whole skill directory**, including `scripts/`, wherever your
    harness discovers skills. A `SKILL.md`-only copy cannot run the server.

2.  Install the server's two Python dependencies, the MCP SDK and the GCS client
    library, using the `python3` that will run the server:

    ```bash
    python3 -m pip install mcp google-cloud-storage
    ```

3.  Authenticate and pick a project. The server reads Application Default
    Credentials and needs a Google Cloud project to bill and quota its requests:

    ```bash
    gcloud auth application-default login
    gcloud config set project <project-id>
    ```

    Instead of a machine-wide project, you can pass one to this server only
    through the `env` block in step 4.

4.  Register the canonical server command with your MCP client, then restart the
    client. Use an absolute path for `<abs skill_dir>` and the same `python3` as
    in step 2; the `env` block is optional:

    ```json
    {
      "mcpServers": {
        "google-cloud-storage-okf": {
          "command": "python3",
          "args": ["<abs skill_dir>/scripts/mcp_server.py"],
          "env": {"GOOGLE_CLOUD_PROJECT": "<project-id>"}
        }
      }
    }
    ```

    Each harness has its own place for this snippet, and your harness knows
    where that is.

If the client reports that the server failed to connect, run the command from
step 4 by hand and read the traceback; a missing dependency or an incomplete
install shows up there directly.

### Credential, Project, and Permission Errors

If any OKF tool returns an error about credentials, a missing project (for
example `Project was not passed and could not be determined from the
environment`), or permission denied (401 or 403), the environment is not set up,
not the request. Relay the error verbatim together with the matching fix from
step 3 and **STOP**:

-   Missing or expired credentials: `gcloud auth application-default login`.
-   Missing project: `gcloud config set project <project-id>`, or the `env`
    block in step 4.
-   Permission denied: the authenticated principal needs read access to the
    object, and `storage.objects.update` for `write_okf`; ask the user to grant
    it.

Do **NOT** change the user's gcloud configuration or credentials yourself, do
NOT guess a project, and do NOT retry the operation through `gcloud storage`,
`gsutil`, or client libraries as a workaround.

--------------------------------------------------------------------------------

## MCP Tools Reference

### 1. Peek Tool (`peek`)

Retrieves the Tier 0 summary of the GCS object from its Object Context.

-   **Args**:
    -   `gs_uri`: Target GCS URI (e.g.,
        `'gs://my-bucket/documents/report.pdf'`).
-   **Returns**:
    -   High-level summary string if OKF Object Context exists.
    -   Stale index warning if the underlying object generation changed.
    -   Diagnostic `OKF_NOT_FOUND` error detailing remaining Object Context
        capacity and pre-existing Object Context entries.

### 2. List Regions Tool (`list_regions`)

Retrieves the Tier 1/2 Table of Contents (region index) stored in the object's
Object Context.

-   **Args**:
    -   `gs_uri`: Target GCS URI.
-   **Returns**:
    -   Formatted JSON string containing a list of region descriptors, each
        with:
    -   `id`: Region identifier (e.g., `'r0'`, `'r1'`).
    -   `start_byte`: 0-indexed starting byte offset (inclusive).
    -   `end_byte`: 0-indexed ending byte offset (inclusive).
    -   `title`: Descriptive section/chapter title.
    -   `keywords`: List of relevant keywords/tags.
    -   Stale index warning JSON (`{"warning": "...", "regions": []}`) if
        generation changed.
    -   Diagnostic `OKF_NOT_FOUND` error if regions are missing.

### 3. Expand Tool (`expand`)

Fetches a specific byte-range slice from the GCS object payload.

-   **Args**:
    -   `gs_uri`: Target GCS URI.
    -   `start_byte`: 0-indexed start offset (inclusive).
    -   `end_byte`: 0-indexed end offset (inclusive).
-   **Returns**:
    -   UTF-8 decoded text slice (or Base64-encoded string for binary data).
    -   Stale index warning string if the underlying object generation changed
        since OKF index creation.

### 4. Write OKF Tool (`write_okf`)

Writes an OKF manifest into GCS Object Context (`okf.r.000`, `okf.sum`, etc.).

-   **Args**:

    -   `gs_uri`: Target GCS URI.

    -   `summary`: High-level overview string of the object.

    -   `regions_json`: JSON array string of region descriptors (e.g., `'[{"id":
        "r0", "start_byte": 0, "end_byte": 1024, "title": "Introduction",
        "keywords": ["overview"]}]'`).

        -   **Grounded Byte Boundaries**: Offsets MUST be 0-indexed integers
            satisfying `0 <= start_byte <= end_byte < object_size`. Regions MUST
            be listed in ascending order by `start_byte` and cannot overlap (for
            inclusive byte ranges, next `start_byte` must be at least previous
            `end_byte + 1`). `write_okf` strictly validates against actual
            object size and rejects inverted, negative, out-of-order,
            overlapping, or out-of-bounds byte ranges.

    -   `created_at`: (Optional) ISO 8601 timestamp string (defaults to current
        UTC time).
-   **Returns**:

    -   Success message or error message if Object Context capacity is exceeded.

--------------------------------------------------------------------------------

## OKF Generation Workflow (Handling `OKF_NOT_FOUND`)

When calling `peek` or `list_regions` on an object that lacks OKF Object
Contexts, the tool returns a comprehensive `OKF_NOT_FOUND` diagnostic payload
including Object Context capacity, existing contexts, custom metadata, and
object attributes:

```text
OKF_NOT_FOUND: Manifest summary missing for 'gs://my-bucket/archive.log'.
Object Context Capacity: 25530 bytes remaining (out of 25600 total, 70 bytes used across 3 keys).
Existing Object Contexts:
{
  "source": "ingestion-pipeline",
  "log-type": "application-debug",
  "environment": "production"
}
Existing Custom Metadata:
{
  "category": "system-logs",
  "retention": "30d"
}
Object Attributes:
{
  "size": 1048576,
  "content_type": "text/plain",
  "generation": 1723334400000000,
  "updated": "2026-08-10T12:00:00Z"
}
```

### Steps to Generate and Commit OKF:

1.  **Leverage Pre-existing Object Context, Custom Metadata & Attributes**:

    -   Inspect the returned `Existing Object Contexts`, `Existing Custom
        Metadata`, and `Object Attributes` from the diagnostic message.
    -   Use these rich signals (e.g., `environment`, `category`, `log-type`,
        `content_type`, `size`) to inform and enrich your generated summary,
        region titles, and keywords.

2.  **Evaluate Splitting Heuristics**:

    -   **Small Objects (< 20 KB)**: If the entire object easily fits in context
        and is small, read directly via `expand(gs_uri, 0, size - 1)` or
        standard tools without forcing OKF indexing.
    -   **Large/Medium Objects (> 20 KB to multi-GB)**: Segment the object into
        semantic, logical regions (e.g., chapters, log phases, data tables,
        video keyframe intervals) using inclusive byte ranges. This is a
        critical step, think of it as generating the most useful summary and
        Table of Contents for the object. If needed, make a couple of detailed
        plans first on how to split the object. For example, splitting naively
        by paragraphs on a text document is not great. You want to keep
        collecting paragraphs together that are semantically related so it
        surfaces as one semantic region. Look to see what tools you have at your
        disposal for best semantic splitting -- for example, you may have a PDF
        parser or even a local small model like Gemma. You split the object once
        and every agent uses it later on so it is ok to pay a high cost for this
        splitting.
    -   **Homogeneous Logs / Structured Dumps**: Split based on timestamp
        boundaries or major processing milestones.

3.  **Format and Commit OKF Manifest to Object Context**:

    -   Create a concise `summary` string (under ~200-250 bytes is optimal).
    -   Assemble the region list into valid JSON:

        ```json
        [
          {
            "id": "r0",
            "start_byte": 0,
            "end_byte": 4095,
            "title": "Header & Config",
            "keywords": ["config", "init", "schema"]
          },
          {
            "id": "r1",
            "start_byte": 4096,
            "end_byte": 18432,
            "title": "Main Execution Trace",
            "keywords": ["trace", "rpc", "errors"]
          }
        ]
        ```

    -   Call `write_okf(gs_uri=gs_uri, summary=summary,
        regions_json=regions_json)`.

--------------------------------------------------------------------------------

## Parallel Processing with Sub-Agents

When processing multi-file buckets or directories with multiple unindexed
objects, agents should **avoid single-threaded sequential processing** and
instead invoke parallel worker sub-agents via `invoke_subagent`:

### Multi-File Batch Parallelism

When indexing multiple objects under a GCS prefix or bucket:

1.  **List Candidate URIs**: Identify all unindexed objects in the target
    bucket/prefix.
2.  **Partition Batches**: Split the list of URIs into balanced batches across
    worker sub-agents (e.g., 5–10 objects per sub-agent).
3.  **Dispatch Parallel Sub-Agents**: Invoke worker sub-agents concurrently
    using `invoke_subagent`:
    -   Each sub-agent is assigned an isolated batch of URIs.
    -   Each sub-agent runs the OKF generation flow (`peek` -> inspect
        attributes -> generate semantic regions -> `write_okf`).
4.  **Aggregate Results**: Workers report completion status and persisted region
    counts back to the lead agent.

--------------------------------------------------------------------------------

## Telemetry & Attribution

Outbound Google Cloud Storage API calls from the skill, MCP server, cURL, or
custom scripts are stamped with the standard GCS Skills User-Agent telemetry
header:

```http
User-Agent: gcs-skills/1.0 (skill:google-cloud-storage-okf)
```

When integrating via the `gcloud storage` CLI, pass the standard metrics
environment variable:

```bash
CLOUDSDK_METRICS_ENVIRONMENT="gcs-skills gcs-skills/1.0 (skill:google-cloud-storage-okf)"
```

--------------------------------------------------------------------------------

## Guardrails & Best Practices

-   **Never Bypass the MCP Server**: Only invoke OKF through the MCP tools;
    never run or import `scripts/core.py` or `scripts/mcp_server.py` directly as
    a substitute (see **Setup**).
-   **Never Reconfigure the User's Environment**: On credential, project, or
    permission errors, relay the fix and stop; never change gcloud configuration
    or credentials yourself (see **Setup**).
-   **Never Overwrite Object Payload**: OKF operations only read byte ranges and
    write non-destructive Object Contexts. Never delete or overwrite the
    original GCS object.
-   **Avoid Massive Full-Blob Dumps**: Do NOT stream or dump large unverified
    objects into the agent context. Always use `list_regions` followed by
    targeted `expand` calls.
-   **Respect Object Context Capacity Budgets**:
    -   Hard key limit per GCS object: `50` Object Context keys across all
        entries (limits an object to ~45–50 OKF regions maximum).
    -   Hard total byte limit per GCS object: `25,600` bytes across all Object
        Context keys.
    -   Hard limit per Object Context value: `256` bytes (compression & fallback
        truncation are handled automatically by `write_okf`).
-   **Detect Stale Indices**: If `peek` or `list_regions` returns a `Stale OKF
    index` warning (indicating the underlying blob generation changed since
    indexing), re-evaluate and re-generate the OKF index.
