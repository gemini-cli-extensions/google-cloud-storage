"""Core logic for GCS-OKF navigation and chunk fetching.

OKF Region Concept & Metadata Architecture:
--------------------------------------------
A **Region** is a contiguous, semantically cohesive segment of a GCS object
(defined by inclusive `start_byte` and `end_byte` offsets, a descriptive
`title`, and relevant `keywords`). Regions act as a Table of Contents index
stored in GCS metadata, allowing LLMs to perform targeted byte-range reads
(`expand`) without loading or processing the full file.

1. Self-Contained Region Index Encoding & Compression Architecture:
   - The underlying GCS object data remains completely untouched—we are NOT
     splitting or creating separate GCS files. Instead, each region index
     descriptor (a JSON object containing byte boundaries, titles, and keywords)
     is individually serialized to JSON, Gzip-compressed, Base64-encoded, and
     saved to a dedicated GCS Object Context key (`okf.r.000`, `okf.r.001`, ...)
     on the original blob itself.
   - **Compression Density**: Gzip compression packs 300–600+ bytes of rich raw
     JSON metadata into <150 Base64 bytes, multiplying effective storage per
     key within the GCS 256-byte per-value hard limit.
   - **Airtight Semantic Truncation (Pre-Compression)**: Truncation is never
     applied to raw compressed byte streams (which would corrupt the archive).
     Instead, if the encoded payload exceeds the 250-byte safe threshold,
     fallback truncation trims the underlying Python dictionary fields
     (keywords, title length, id) *before* re-compressing, strictly guaranteeing
     that the resulting Base64 string is <= 256 bytes while remaining a 100%
     valid, decompressable Gzip archive.
   - **Failure Domain Isolation**: If a single region key fails to write or
     becomes corrupted, the rest of the OKF index remains valid (avoiding
     multi-key manifest splicing risks).

2. Staleness Detection, GCS Versioning, & Defense-in-Depth Model:
   - **GCS Versioning & Generation Semantics**: In Google Cloud Storage, objects
     and Object Contexts (`custom_contexts`) are strictly bound to an immutable
     64-bit server generation timestamp (`generation`). When an object is
     overwritten, GCS creates a new generation with empty Object Contexts. The
     live object returns `OKF_NOT_FOUND`, prompting a clean re-indexing pass
     rather than borrowing misaligned byte offsets from older versions.
   - **When OKF Indices Become Stale**:
     1. *ETL & Metadata-Copy Pipelines*: Ingestion scripts copying custom
        metadata forward from v1 to v2 without re-indexing byte boundaries.
     2. *Cross-Bucket Copies, Moves, & STS Transfers*: Operations like `gcloud
        storage cp/mv` or Storage Transfer Service (STS) replicate
        metadata/contexts by default, but GCS assigns a brand new generation in
        the target bucket. The copied `okf.src_generation` references the source
        bucket generation, alerting readers to verify/re-stamp provenance.
     3. *Asynchronous Indexing Race Conditions*: An out-of-band indexing worker
        spends 10–30s computing regions for generation G1, but another process
        overwrites the blob to generation G2 before the index is patched.
   - **Defense-in-Depth Protection**:
     - *Write-Time Atomic OCC Guard*: `write_okf` passes
       `if_generation_match=blob.generation` to `blob.patch()`, leveraging GCS
       server-side Optimistic Concurrency Control (OCC) to atomically reject
       writes with `412 Precondition Failed` if the object changed during index
       generation.
     - *Read-Time Provenance Guard*: `peek` and `list_regions` execute
       `_check_staleness_warning` to verify that `blob.generation` matches
       `okf.src_generation`, warning downstream agents before they invoke
       `expand` on potentially shifted byte ranges.

3. Capacity & Key Count Limits:
   - Enforces GCS custom context budget limits: max 50 context keys and 25,600
     total bytes per object.
   - Deducts pre-existing non-OKF object contexts from available key count and
     byte budget before writing.
   - On missing OKF during read (`peek`/`list_regions`) or capacity overflow on
     `write_okf`, returns detailed diagnostic errors providing exact remaining
     storage space, key slots, and existing context text to help LLMs determine
     whether OKF index generation is viable.
"""

import base64
import datetime
import functools
import gzip
import json
from typing import Any, Mapping, Sequence

from google.api_core import client_info
from google.api_core import exceptions as gcs_exceptions
from google.cloud import storage

SKILL_USER_AGENT = "gcs-skills/1.0 (skill:google-cloud-storage-okf)"
CLIENT_INFO = client_info.ClientInfo(user_agent=SKILL_USER_AGENT)


GCS_CONTEXT_MAX_VALUE_BYTES = 256
GCS_CONTEXT_SAFE_VALUE_LIMIT = 250
GCS_CONTEXT_MAX_TOTAL_BYTES = 25600
GCS_CONTEXT_MAX_KEYS = 50
OKF_SUMMARY_CHUNK_SIZE = 200
OKF_KEYWORD_TRUNCATION_LIMIT = 3
OKF_TITLE_TRUNCATION_LIMIT = 50


def _check_staleness_warning(
    blob: storage.Blob, contexts: Mapping[str, str]
) -> str | None:
  """Checks if stored OKF provenance matches current blob generation.

  Detects index staleness across three critical scenarios:
    1. ETL/Ingestion pipelines copying custom metadata from previous versions.
    2. Bucket moves, cross-bucket copies, or STS transfers where GCS assigns a
       new destination generation while preserving existing metadata.
    3. Concurrent overwrite race conditions where the object was replaced during
       asynchronous OKF index computation.

  Args:
    blob: The target GCS Blob instance.
    contexts: The dictionary of GCS Object Contexts.

  Returns:
    A descriptive staleness warning string if generation mismatch is detected,
    or None if the index is fresh and matching.
  """
  stored_gen = contexts.get("okf.src_generation")
  curr_gen = getattr(blob, "generation", None)
  if stored_gen and curr_gen is not None and str(curr_gen) != str(stored_gen):
    return (
        f"Stale OKF index: Index created for object generation {stored_gen}, "
        f"but current generation is {curr_gen}."
    )
  return None


def _parse_gs_uri(gs_uri: str) -> tuple[str, str]:
  """Parses a GCS URI of the form 'gs://bucket/blob_name'.

  Args:
    gs_uri: The string URI to parse.

  Returns:
    A tuple of (bucket_name, blob_name).

  Raises:
    ValueError: If the URI format is invalid.
  """
  if not gs_uri or not isinstance(gs_uri, str):
    raise ValueError(
        f"Invalid URI: Expected a non-empty string, got {type(gs_uri).__name__}"
    )
  if not gs_uri.startswith("gs://"):
    raise ValueError(
        f"Invalid URI: Must start with 'gs://'. Provided: '{gs_uri}'"
    )
  path = gs_uri[5:]
  if not path:
    raise ValueError(f"Invalid URI: Missing bucket name in '{gs_uri}'")
  parts = path.split("/", 1)
  bucket = parts[0]
  if not bucket:
    raise ValueError(f"Invalid URI: Missing bucket name in '{gs_uri}'")
  blob_name = parts[1] if len(parts) > 1 else ""
  if not blob_name:
    raise ValueError(f"Invalid URI: Missing object path in '{gs_uri}'")
  return bucket, blob_name


def _format_gcs_error(gs_uri: str, error: Exception) -> str:
  """Formats GCS errors into human- and LLM-friendly diagnostic messages."""
  if isinstance(error, ValueError):
    return str(error)
  if isinstance(error, gcs_exceptions.NotFound):
    msg = error.message if hasattr(error, "message") else str(error)
    return f"GCS Resource Not Found: {msg}"
  if isinstance(error, gcs_exceptions.PreconditionFailed):
    msg = error.message if hasattr(error, "message") else str(error)
    return (
        f"Precondition Failed for '{gs_uri}': Object generation condition"
        f" failed (concurrent modification): {msg}"
    )
  if isinstance(error, (gcs_exceptions.Forbidden, gcs_exceptions.Unauthorized)):
    return f"Permission Denied accessing '{gs_uri}': {str(error)}"
  return f"Error accessing GCS for '{gs_uri}': {str(error)}"


def _get_blob_contexts(blob: storage.Blob) -> dict[str, str]:
  """Extracts existing object contexts dictionary from a GCS blob."""
  custom_contexts = getattr(blob, "custom_contexts", None)
  if isinstance(custom_contexts, dict):
    return dict(custom_contexts)
  return {}


def _format_missing_okf_error(
    gs_uri: str, blob: storage.Blob, missing_item: str
) -> str:
  """Formats diagnostic error detailing context capacity, existing contexts, and metadata."""
  existing_contexts = _get_blob_contexts(blob)
  used_bytes = sum(
      len(k.encode("utf-8")) + len(str(v).encode("utf-8"))
      for k, v in existing_contexts.items()
  )
  remaining_bytes = GCS_CONTEXT_MAX_TOTAL_BYTES - used_bytes
  remaining_keys = max(0, GCS_CONTEXT_MAX_KEYS - len(existing_contexts))
  contexts_str = (
      json.dumps(existing_contexts, indent=2) if existing_contexts else "None"
  )
  metadata = getattr(blob, "metadata", None)
  metadata_dict = dict(metadata) if isinstance(metadata, dict) else {}
  metadata_clean = {
      str(k): str(v)
      for k, v in metadata_dict.items()
      if isinstance(k, str) and isinstance(v, (str, int, float, bool))
  }
  metadata_str = (
      json.dumps(metadata_clean, indent=2) if metadata_clean else "None"
  )

  attributes: dict[str, Any] = {}
  size = getattr(blob, "size", None)
  if isinstance(size, int):
    attributes["size"] = size
  content_type = getattr(blob, "content_type", None)
  if isinstance(content_type, str):
    attributes["content_type"] = content_type
  generation = getattr(blob, "generation", None)
  if isinstance(generation, (int, str)):
    attributes["generation"] = generation
  updated = getattr(blob, "updated", None)
  if isinstance(updated, str):
    attributes["updated"] = updated
  elif isinstance(updated, datetime.datetime):
    attributes["updated"] = updated.isoformat()

  attributes_str = json.dumps(attributes, indent=2) if attributes else "None"
  return (
      f"OKF_NOT_FOUND: {missing_item} for '{gs_uri}'.\n"
      f"Object Context Capacity: {remaining_bytes} bytes remaining"
      f" ({remaining_keys} of {GCS_CONTEXT_MAX_KEYS} keys remaining,"
      f" {used_bytes} bytes used across {len(existing_contexts)} keys out of"
      f" {GCS_CONTEXT_MAX_TOTAL_BYTES} total bytes).\n"
      f"Existing Object Contexts:\n{contexts_str}\n"
      f"Existing Custom Metadata:\n{metadata_str}\n"
      f"Object Attributes:\n{attributes_str}"
  )


@functools.cache
def _get_storage_client() -> storage.Client:
  """Returns a cached module-level storage.Client instance with telemetry."""
  return storage.Client(client_info=CLIENT_INFO)


def _fetch_blob(gs_uri: str) -> tuple[storage.Blob | None, str | None]:

  """Helper to parse URI and retrieve GCS blob using client.bucket().get_blob().

  Args:
    gs_uri: Target GCS URI.

  Returns:
    Tuple of (Blob, None) on success or (None, error_message) on failure.
  """
  try:
    bucket_name, blob_name = _parse_gs_uri(gs_uri)
  except Exception as e:  # pylint: disable=broad-exception-caught
    return None, _format_gcs_error(gs_uri, e)

  try:
    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.get_blob(blob_name)
  except Exception as e:  # pylint: disable=broad-exception-caught
    return None, _format_gcs_error(gs_uri, e)

  if not blob:
    return None, f"Object '{gs_uri}' not found."

  return blob, None


def peek(gs_uri: str) -> str:
  """Returns the Tier 0 OKF summary from GCS object contexts.

  Args:
    gs_uri: The target Google Cloud Storage URI.

  Returns:
    The summary text string or diagnostic error detailing remaining capacity and
    existing context.
  """
  blob, err = _fetch_blob(gs_uri)
  if err or not blob:
    return err or f"Object '{gs_uri}' not found."

  contexts = _get_blob_contexts(blob)
  stale_warning = _check_staleness_warning(blob, contexts)
  if stale_warning:
    return stale_warning

  # Check direct summary key
  if "okf.sum" in contexts:
    return contexts["okf.sum"]

  # Check Object Context chunked summary format
  sum_chunks_str = contexts.get("okf.sum_chunks")
  if sum_chunks_str and sum_chunks_str.isdigit():
    num_chunks = int(sum_chunks_str)
    summary = "".join(
        contexts.get(f"okf.sum.{i:03d}", "") for i in range(num_chunks)
    )
    if summary:
      return summary

  return _format_missing_okf_error(gs_uri, blob, "Manifest summary missing")


def list_regions(gs_uri: str) -> str:
  """Returns the Tier 1 table of contents (TOC) from compressed region object contexts.

  Args:
    gs_uri: The target Google Cloud Storage URI.

  Returns:
    JSON string of region list or diagnostic error detailing remaining capacity
    and existing context.
  """
  blob, err = _fetch_blob(gs_uri)
  if err or not blob:
    return err or f"Object '{gs_uri}' not found."

  contexts = _get_blob_contexts(blob)
  stale_warning = _check_staleness_warning(blob, contexts)
  if stale_warning:
    return json.dumps({"warning": stale_warning, "regions": []})

  if not contexts:
    return _format_missing_okf_error(gs_uri, blob, "No object contexts found")

  # Check self-contained compressed region keys (okf.r.000, okf.r.001, ...)
  region_keys = sorted([k for k in contexts if k.startswith("okf.r.")])
  if region_keys:
    regions = []
    for k in region_keys:
      val_b64 = contexts[k]
      try:
        decompressed_bytes = gzip.decompress(base64.b64decode(val_b64))
        reg_obj = json.loads(decompressed_bytes.decode("utf-8"))
        regions.append(reg_obj)
      except Exception as e:  # pylint: disable=broad-exception-caught
        regions.append(
            {"error": f"Failed to decompress region context '{k}': {str(e)}"}
        )
    return json.dumps(regions, indent=2)

  return _format_missing_okf_error(
      gs_uri, blob, "Detailed navigation index missing"
  )


def expand(gs_uri: str, start_byte: int, end_byte: int) -> str:
  """Fetches a specific byte-range slice (Tier 2/3) from GCS.

  Both start_byte and end_byte are inclusive 0-indexed byte offsets
  (e.g., start_byte=0, end_byte=0 returns 1 byte; start_byte=0, end_byte=10
  returns 11 bytes).

  Args:
    gs_uri: The target Google Cloud Storage URI.
    start_byte: The 0-indexed starting byte offset (inclusive).
    end_byte: The 0-indexed ending byte offset (inclusive).

  Returns:
    The decoded string content or base64 fallback, or a staleness warning if
    the object generation changed since OKF index creation.
  """
  if start_byte < 0:
    return f"Invalid byte range: start_byte ({start_byte}) must be >= 0."
  if end_byte < 0:
    return f"Invalid byte range: end_byte ({end_byte}) must be >= 0."
  if start_byte > end_byte:
    return (
        f"Invalid byte range: start_byte ({start_byte}) cannot be greater than"
        f" end_byte ({end_byte})."
    )

  blob, err = _fetch_blob(gs_uri)
  if err or not blob:
    return err or f"Object '{gs_uri}' not found."

  contexts = _get_blob_contexts(blob)
  stale_warning = _check_staleness_warning(blob, contexts)
  if stale_warning:
    return stale_warning

  try:
    content_bytes = blob.download_as_bytes(start=start_byte, end=end_byte)
  except Exception as e:  # pylint: disable=broad-exception-caught
    return (
        f"Error reading byte range [{start_byte}:{end_byte}] from '{gs_uri}':"
        f" {str(e)}"
    )

  try:
    return content_bytes.decode("utf-8")
  except UnicodeDecodeError:
    # Fallback to returning base64 if it's non-text (video/audio snippet)
    return base64.b64encode(content_bytes).decode("utf-8")


def write_okf(
    gs_uri: str,
    summary: str,
    regions: Sequence[Mapping[str, Any]],
    created_at: str = "",
    model: str = "",
) -> str:
  """Writes the OKF manifest to GCS Object Contexts using compressed keys.

  Compression & Concurrency Architecture:
    - Encodes each region descriptor as base64(gzip(json)), compressing
      300-600+ bytes of metadata to fit comfortably within the GCS 256-byte
      per-value limit.
    - If an encoded region payload exceeds 250 bytes, semantic truncation is
      applied to the underlying Python dictionary (trimming keywords, title,
      or ID) before re-compressing, guaranteeing valid, decompressable Gzip
      archives under 256 bytes without corrupting byte streams.
    - Uses GCS Optimistic Concurrency Control (OCC) by passing
      `if_generation_match=blob.generation` to `blob.patch()`, atomically
      preventing write race conditions if the object was replaced or modified
      during asynchronous index computation.
    - Enforces GCS Object Context limits: max 50 context keys and 25,600 total
      bytes per object.

  Args:
    gs_uri: The target Google Cloud Storage URI.
    summary: The Tier 0 OKF summary.
    regions: The list of OKF regions (max ~45-50 regions per object).
    created_at: Optional creation timestamp (defaults to UTC ISO 8601 if empty).
    model: Optional AI model identifier (e.g. 'gemini-1.5-pro').

  Returns:
    Status message string confirming write or detailing capacity/precondition
    errors.
  """

  if not isinstance(regions, list):
    return (
        "Invalid regions data: Expected a list of region objects, got"
        f" {type(regions).__name__}."
    )

  for i, reg in enumerate(regions):
    if not isinstance(reg, dict):
      return (
          f"Invalid region entry at index {i}: Each region must be a"
          f" dictionary, got {type(reg).__name__}."
      )

  blob, err = _fetch_blob(gs_uri)
  if err or not blob:
    return err or f"Object '{gs_uri}' not found."

  if not created_at:
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()

  # Construct OKF Object Context map
  context_map: dict[str, str] = {
      "okf.v": "1.0",
      "okf.created_at": created_at,
  }
  if getattr(blob, "generation", None) is not None:
    context_map["okf.src_generation"] = str(blob.generation)
  if model:
    context_map["okf.model"] = model

  # Helper function to encode a region dictionary to base64(gzip(json))
  def _encode_region(reg_dict: dict[str, Any]) -> str:
    val_json = json.dumps(reg_dict, separators=(",", ":"))
    return base64.b64encode(gzip.compress(val_json.encode("utf-8"))).decode(
        "utf-8"
    )

  # Store summary (single key if <= GCS_CONTEXT_SAFE_VALUE_LIMIT chars,
  # or chunked if longer)
  summary_bytes = summary.encode("utf-8")
  if len(summary_bytes) <= GCS_CONTEXT_SAFE_VALUE_LIMIT:
    context_map["okf.sum"] = summary
  else:
    summary_chunks = [
        summary_bytes[i : i + OKF_SUMMARY_CHUNK_SIZE].decode(
            "utf-8", errors="ignore"
        )
        for i in range(0, len(summary_bytes), OKF_SUMMARY_CHUNK_SIZE)
    ]
    context_map["okf.sum_chunks"] = str(len(summary_chunks))
    for i, s_chunk in enumerate(summary_chunks):
      context_map[f"okf.sum.{i:03d}"] = s_chunk

  # Build self-contained compressed region key-value pairs
  # (okf.r.000, okf.r.001, ...)
  context_map["okf.region_count"] = str(len(regions))
  for i, reg in enumerate(regions):
    reg_id = str(reg.get("id", f"r{i}"))
    reg_dict = {
        "id": reg_id,
        "start_byte": reg.get("start_byte", 0),
        "end_byte": reg.get("end_byte", 0),
    }
    if "title" in reg:
      reg_dict["title"] = reg["title"]
    if "keywords" in reg:
      reg_dict["keywords"] = reg["keywords"]

    val_b64 = _encode_region(reg_dict)

    # Guard: GCS_CONTEXT_MAX_VALUE_BYTES (256) is the hard per-value limit.
    # If the payload exceeds GCS_CONTEXT_SAFE_VALUE_LIMIT (250),
    # apply airtight step-by-step fallback truncation:
    # 1. Truncate keywords list to OKF_KEYWORD_TRUNCATION_LIMIT (3) items.
    # 2. Trim title to OKF_TITLE_TRUNCATION_LIMIT (50).
    # 3. Drop keywords completely if still exceeding limit.
    # 4. Progressively trim title down to 20 chars, then drop title if needed.
    # 5. Shorten reg_id if still exceeding limit.
    if len(val_b64) > GCS_CONTEXT_SAFE_VALUE_LIMIT:
      if "keywords" in reg_dict and isinstance(reg_dict["keywords"], list):
        reg_dict["keywords"] = reg_dict["keywords"][
            :OKF_KEYWORD_TRUNCATION_LIMIT
        ]
        val_b64 = _encode_region(reg_dict)
      if len(val_b64) > GCS_CONTEXT_SAFE_VALUE_LIMIT and "title" in reg_dict:
        reg_dict["title"] = str(reg_dict["title"])[:OKF_TITLE_TRUNCATION_LIMIT]
        val_b64 = _encode_region(reg_dict)
      if len(val_b64) > GCS_CONTEXT_SAFE_VALUE_LIMIT and "keywords" in reg_dict:
        del reg_dict["keywords"]
        val_b64 = _encode_region(reg_dict)
      if len(val_b64) > GCS_CONTEXT_SAFE_VALUE_LIMIT and "title" in reg_dict:
        reg_dict["title"] = str(reg_dict["title"])[:20]
        val_b64 = _encode_region(reg_dict)
      if len(val_b64) > GCS_CONTEXT_SAFE_VALUE_LIMIT and "title" in reg_dict:
        del reg_dict["title"]
        val_b64 = _encode_region(reg_dict)
      if len(val_b64) > GCS_CONTEXT_SAFE_VALUE_LIMIT:
        reg_dict["id"] = f"r{i}"
        val_b64 = _encode_region(reg_dict)

    if len(val_b64) > GCS_CONTEXT_MAX_VALUE_BYTES:
      return (
          f"Error: Region {reg_id} exceeds hard GCS value size limit of"
          f" {GCS_CONTEXT_MAX_VALUE_BYTES} bytes even after truncation."
      )

    context_map[f"okf.r.{i:03d}"] = val_b64

  # Fetch existing blob contexts to account for already used space
  existing_contexts = _get_blob_contexts(blob)

  # Calculate space and keys consumed by non-OKF pairs already on the object
  non_okf_keys_count = sum(
      1 for k in existing_contexts if not k.startswith("okf.")
  )
  available_keys = GCS_CONTEXT_MAX_KEYS - non_okf_keys_count
  okf_keys_count = len(context_map)

  if okf_keys_count > available_keys:
    return (
        f"Error: OKF index context key count ({okf_keys_count} keys) exceeds"
        f" remaining GCS object context key capacity ({available_keys} keys"
        f" available out of {GCS_CONTEXT_MAX_KEYS} max total keys,"
        f" {non_okf_keys_count} keys used by non-OKF contexts). Please"
        " consolidate or reduce the number of regions (max 50 contexts per"
        " object)."
    )

  non_okf_used_bytes = sum(

      len(k.encode("utf-8")) + len(str(v).encode("utf-8"))
      for k, v in existing_contexts.items()
      if not k.startswith("okf.")
  )

  available_bytes = GCS_CONTEXT_MAX_TOTAL_BYTES - non_okf_used_bytes
  okf_payload_bytes = sum(
      len(k.encode("utf-8")) + len(v.encode("utf-8"))
      for k, v in context_map.items()
  )

  if okf_payload_bytes > available_bytes:
    return (
        f"Error: OKF index context payload ({okf_payload_bytes} bytes) exceeds"
        f" remaining GCS object context capacity ({available_bytes} bytes"
        f" available out of {GCS_CONTEXT_MAX_TOTAL_BYTES} total,"
        f" {non_okf_used_bytes} bytes used by non-OKF contexts). Please"
        " consolidate or reduce the number of regions."
    )

  # Prepare updated context dictionary
  updated_contexts: dict[str, Any] = dict(existing_contexts)

  for k in existing_contexts:
    if k.startswith("okf."):
      updated_contexts[k] = None
  updated_contexts.update(context_map)

  try:
    setattr(blob, "custom_contexts", updated_contexts)
    if getattr(blob, "generation", None) is not None:
      blob.patch(if_generation_match=blob.generation)
    else:
      blob.patch()
  except gcs_exceptions.PreconditionFailed as e:
    msg = e.message if hasattr(e, "message") else str(e)
    return (
        f"Precondition Failed: Target object '{gs_uri}' was modified or"
        f" replaced during OKF generation (generation mismatch): {msg}"
    )
  except Exception as e:  # pylint: disable=broad-exception-caught
    return (
        f"Permission Denied or Error writing Object Context to '{gs_uri}':"
        f" {str(e)}"
    )

  return f"Successfully wrote OKF metadata to {gs_uri}"
