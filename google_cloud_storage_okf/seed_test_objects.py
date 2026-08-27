"""Script to stage and teardown test fixtures in GCS for OKF evals.

Supports creating:
1. Pre-indexed objects with OKF manifests in GCS Object Context.
2. Unindexed objects with custom metadata for testing OKF_NOT_FOUND diagnostics.
3. Stale-indexed objects with mismatched okf.src_generation.
4. Multi-region documents for comparative progressive disclosure.
"""

import argparse
from collections.abc import Sequence
import logging
import sys

from google.cloud import storage
import core


def get_target_path(relative_path: str, session_id: str = "") -> str:
  if session_id:
    return f"eval_runs/{session_id}/{relative_path}"
  return relative_path


def stage_system_audit_log(
    client: storage.Client, bucket_name: str, session_id: str = ""
) -> str:
  """Stages gs://<bucket>/indexed/system_audit_2026.log with OKF manifest."""

  path = get_target_path("indexed/system_audit_2026.log", session_id)
  gs_uri = f"gs://{bucket_name}/{path}"
  bucket = client.bucket(bucket_name)
  blob = bucket.blob(path)

  # Generate 4 distinct sections of log content
  init_section = (
      "2026-08-21T00:00:00Z [INFO] System startup initiated. Config loaded from"
      " /etc/cloud/config.yaml.\n"
      * 10
  )
  auth_section = (
      "2026-08-21T00:05:00Z [INFO] IAM token verification succeeded for user"
      " service-account-prod@bigstore.\n"
      * 20
  )
  txn_section = (
      "2026-08-21T00:10:00Z [INFO] Transaction 98472910 committed with"
      " latency=14ms in us-central1.\n"
      * 25
  )
  err_section = (
      "2026-08-21T00:15:00Z [ERROR] Critical exception in PaymentGateway:"
      " Deadlock detected at line 412 in payment_core.go.\nStacktrace:\n  at"
      " ProcessTxn(payment.go:120)\n  at HandleRequest(server.go:88)\n"
      * 15
  )

  content = init_section + auth_section + txn_section + err_section
  content_bytes = content.encode("utf-8")

  # Calculate exact byte boundaries
  b0_start = 0
  b0_end = len(init_section.encode("utf-8")) - 1
  b1_start = b0_end + 1
  b1_end = b1_start + len(auth_section.encode("utf-8")) - 1
  b2_start = b1_end + 1
  b2_end = b2_start + len(txn_section.encode("utf-8")) - 1
  b3_start = b2_end + 1
  b3_end = len(content_bytes) - 1

  blob.upload_from_string(content, content_type="text/plain")

  regions = [
      {
          "id": 0,
          "start_byte": b0_start,
          "end_byte": b0_end,
          "title": "System Initialization & Startup Configuration",
          "keywords": ["init", "startup", "config"],
      },
      {
          "id": 1,
          "start_byte": b1_start,
          "end_byte": b1_end,
          "title": "Authentication & IAM Access Logs",
          "keywords": ["auth", "iam", "token"],
      },
      {
          "id": 2,
          "start_byte": b2_start,
          "end_byte": b2_end,
          "title": "Transaction Processing Audit & Latency Records",
          "keywords": ["transaction", "latency", "payment"],
      },
      {
          "id": 3,
          "start_byte": b3_start,
          "end_byte": b3_end,
          "title": "Critical Error Traces & Stack Dumps",
          "keywords": ["error", "exception", "deadlock", "stacktrace"],
      },
  ]

  summary = (
      "System audit log for 2026 covering API transactions, IAM auth tokens,"
      " and payment gateway error traces."
  )
  core.write_okf(gs_uri, summary, regions)
  logging.info("Staged %s with %d regions", gs_uri, len(regions))
  return gs_uri


def stage_unindexed_incident_report(
    client: storage.Client, bucket_name: str, session_id: str = ""
) -> str:
  """Stages gs://<bucket>/unindexed/incident_report_q3.txt without OKF."""
  path = get_target_path("unindexed/incident_report_q3.txt", session_id)
  gs_uri = f"gs://{bucket_name}/{path}"
  bucket = client.bucket(bucket_name)
  blob = bucket.blob(path)

  content = (
      "Incident Postmortem: Q3 Storage Outage\nExecutive Summary: On"
      " 2026-07-15, network partition impacted cluster us-east4.\nTimeline:\n "
      " 14:00 - Spike in RPC timeouts.\n  14:15 - Failover engaged.\nAction"
      " Items:\n  1. Increase buffer size for cross-region replication.\n  2."
      " Add automated health-check alarm.\n"
  )
  blob.metadata = {"category": "incident", "year": "2026"}
  blob.upload_from_string(content, content_type="text/plain")
  # Ensure no OKF contexts exist
  setattr(blob, "custom_contexts", {})
  try:
    blob.patch()
  except Exception:  # pylint: disable=broad-exception-caught
    pass
  logging.info("Staged unindexed %s", gs_uri)
  return gs_uri


def stage_stale_inventory_snapshot(
    client: storage.Client, bucket_name: str, session_id: str = ""
) -> str:
  """Stages inventory snapshot with outdated okf.src_generation."""
  path = get_target_path("stale/inventory_snapshot.csv", session_id)
  gs_uri = f"gs://{bucket_name}/{path}"
  bucket = client.bucket(bucket_name)
  blob = bucket.blob(path)

  content = (
      "item_id,sku,warehouse,quantity,last_audit\n"
      "1001,SKU-ALPHA,us-central1,5400,2026-08-01\n"
      "1002,SKU-BETA,us-east4,12000,2026-08-05\n"
      "1003,SKU-GAMMA,europe-west1,320,2026-08-10\n"
  )
  blob.upload_from_string(content, content_type="text/csv")
  blob.reload()

  # Write OKF context with an outdated generation
  stale_gen = "1723300000000000"
  regions = [{
      "id": 0,
      "start_byte": 0,
      "end_byte": len(content.encode("utf-8")) - 1,
      "title": "Inventory SKU Records",
      "keywords": ["inventory", "sku", "warehouse"],
  }]
  core.write_okf(
      gs_uri,
      "Inventory snapshot table covering regional warehouse stock levels.",
      regions,
  )

  # Override okf.src_generation to intentionally create stale condition
  blob.reload()
  contexts = getattr(blob, "custom_contexts", {}) or {}
  contexts_dict = dict(contexts)
  contexts_dict["okf.src_generation"] = stale_gen
  setattr(blob, "custom_contexts", contexts_dict)
  blob.patch()
  logging.info(
      "Staged stale-indexed %s with generation mismatch (%s != %s)",
      gs_uri,
      stale_gen,
      blob.generation,
  )
  return gs_uri


def stage_annual_performance_report(
    client: storage.Client, bucket_name: str, session_id: str = ""
) -> str:
  """Stages annual_performance_2025.txt with multi-quarter regions."""

  path = get_target_path("indexed/annual_performance_2025.txt", session_id)
  gs_uri = f"gs://{bucket_name}/{path}"
  bucket = client.bucket(bucket_name)
  blob = bucket.blob(path)

  q1_content = (
      "=== Q1 2025 Performance ===\nMedian Latency: 12.4ms\nP99 Latency:"
      " 45.2ms\nThroughput: 1.2M QPS\nAvailability: 99.995%\n\n"
  )
  q2_content = (
      "=== Q2 2025 Performance ===\nMedian Latency: 11.8ms\nP99 Latency:"
      " 42.1ms\nThroughput: 1.4M QPS\nAvailability: 99.998%\n\n"
  )
  q3_content = (
      "=== Q3 2025 Performance ===\nMedian Latency: 10.1ms\nP99 Latency:"
      " 38.6ms\nThroughput: 1.6M QPS\nAvailability: 99.999%\n\n"
  )
  q4_content = (
      "=== Q4 2025 Performance ===\nMedian Latency: 9.8ms\nP99 Latency:"
      " 35.0ms\nThroughput: 1.9M QPS\nAvailability: 99.999%\n\n"
  )

  full_content = q1_content + q2_content + q3_content + q4_content
  blob.upload_from_string(full_content, content_type="text/plain")

  q1_bytes = len(q1_content.encode("utf-8"))
  q2_bytes = len(q2_content.encode("utf-8"))
  q3_bytes = len(q3_content.encode("utf-8"))
  q4_bytes = len(q4_content.encode("utf-8"))

  q1_range = (0, q1_bytes - 1)
  q2_range = (q1_range[1] + 1, q1_range[1] + q2_bytes)
  q3_range = (q2_range[1] + 1, q2_range[1] + q3_bytes)
  q4_range = (q3_range[1] + 1, q3_range[1] + q4_bytes)

  regions = [
      {
          "id": 0,
          "start_byte": q1_range[0],
          "end_byte": q1_range[1],
          "title": "Q1 2025 Performance Metrics",
          "keywords": ["Q1", "latency", "throughput"],
      },
      {
          "id": 1,
          "start_byte": q2_range[0],
          "end_byte": q2_range[1],
          "title": "Q2 2025 Performance Metrics",
          "keywords": ["Q2", "latency", "throughput"],
      },
      {
          "id": 2,
          "start_byte": q3_range[0],
          "end_byte": q3_range[1],
          "title": "Q3 2025 Performance Metrics",
          "keywords": ["Q3", "latency", "throughput"],
      },
      {
          "id": 3,
          "start_byte": q4_range[0],
          "end_byte": q4_range[1],
          "title": "Q4 2025 Performance Metrics",
          "keywords": ["Q4", "latency", "throughput"],
      },
  ]

  summary = (
      "Annual system performance report for 2025 broken down into quarterly"
      " latency and throughput metrics."
  )
  core.write_okf(gs_uri, summary, regions)
  logging.info("Staged multi-quarter %s with 4 regions", gs_uri)
  return gs_uri


def cleanup_fixture(
    client: storage.Client,
    bucket_name: str,
    relative_path: str,
    session_id: str = "",
) -> None:
  path = get_target_path(relative_path, session_id)
  bucket = client.bucket(bucket_name)
  blob = bucket.get_blob(path)
  if blob:
    blob.delete()
    logging.info("Deleted gs://%s/%s", bucket_name, path)


def main(argv: Sequence[str] | None = None) -> None:
  parser = argparse.ArgumentParser(
      description="Stage and teardown test fixtures in GCS for OKF evals."
  )
  parser.add_argument(
      "--bucket",
      default="gcs-okf-skill-test",
      help="Target GCS bucket for staging fixtures.",
  )

  parser.add_argument(
      "--action",
      default="setup",
      choices=["setup", "cleanup", "setup_all", "cleanup_all"],
      help="Action to perform.",
  )
  parser.add_argument(
      "--case",
      default="all",
      choices=[
          "navigate_large_log",
          "missing_index",
          "stale_index",
          "multi_region",
          "all",
      ],
      help="Specific test case to setup/cleanup.",
  )
  parser.add_argument(
      "--session_id",
      default="",
      help=(
          "Optional unique session ID prefix to prevent collision across"
          " concurrent runs."
      ),
  )

  args = parser.parse_args(argv)

  if storage is None or core is None:
    logging.warning(
        "GCS SDK or OKF core module not available; skipping fixture staging."
    )
    return

  try:
    client = storage.Client()
  except Exception as e:  # pylint: disable=broad-exception-caught
    logging.warning("Unable to initialize GCS client: %s; skipping.", e)
    return

  bucket_name = args.bucket
  action = args.action
  case = args.case
  session_id = args.session_id

  try:
    if action in ("setup", "setup_all"):
      if case in ("navigate_large_log", "all"):
        stage_system_audit_log(client, bucket_name, session_id)
      if case in ("missing_index", "all"):
        stage_unindexed_incident_report(client, bucket_name, session_id)
      if case in ("stale_index", "all"):
        stage_stale_inventory_snapshot(client, bucket_name, session_id)
      if case in ("multi_region", "all"):
        stage_annual_performance_report(client, bucket_name, session_id)

    elif action in ("cleanup", "cleanup_all"):
      if case in ("navigate_large_log", "all"):
        cleanup_fixture(
            client, bucket_name, "indexed/system_audit_2026.log", session_id
        )
      if case in ("missing_index", "all"):
        cleanup_fixture(
            client, bucket_name, "unindexed/incident_report_q3.txt", session_id
        )
      if case in ("stale_index", "all"):
        cleanup_fixture(
            client, bucket_name, "stale/inventory_snapshot.csv", session_id
        )
      if case in ("multi_region", "all"):
        cleanup_fixture(
            client,
            bucket_name,
            "indexed/annual_performance_2025.txt",
            session_id,
        )
  except Exception as e:  # pylint: disable=broad-exception-caught
    logging.warning("GCS fixture operation failed: %s", e)


if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO)
  main(sys.argv[1:])
