"""Script to fetch aggregated object-level telemetry for buckets in a Storage Insights dataset."""

import argparse
from collections.abc import Mapping, Sequence
import json
import textwrap
from typing import Any

# pylint: disable=g-import-not-at-top
try:
  from google3.blobstore2.storage_management.gemini.si_agent.skills.security_assessment.scripts import cloud_rest_helpers_nodeps
  from google3.blobstore2.storage_management.gemini.si_agent.skills.security_assessment.scripts import validation
except ImportError:
  import cloud_rest_helpers_nodeps  # type: ignore
  import validation  # type: ignore
# pylint: enable=g-import-not-at-top

_SKILL = "security-assessment"
_SCRIPT = "fetch-object-telemetry"


def fetch_object_telemetry(
    project_id: str,
    dataset_name: str,
    bucket_names: Sequence[str] | None = None,
) -> Sequence[Mapping[str, Any]]:
  """Fetches object telemetry signals from BigQuery.

  Queries the latest snapshot from the Storage Insights
  object_attributes_latest_snapshot_view.

  Args:
    project_id: The GCP project ID.
    dataset_name: The linked dataset name.
    bucket_names: Optional list of bucket names to filter on.

  Returns:
    A list of dictionaries containing telemetry signals per object.

  Raises:
    cloud_rest_helpers_nodeps.CloudRestError: If the REST query fails.
    RuntimeError: If the query job does not complete in time.
  """
  validation.validate_inputs(project_id, dataset_name, bucket_names)

  if not bucket_names:
    bucket_filter = ""
    query_parameters = []
  else:
    bucket_filter = "WHERE bucket IN UNNEST(@bucket_names)"
    query_parameters = [{
        "name": "bucket_names",
        "parameterType": {
            "type": "ARRAY",
            "arrayType": {"type": "STRING"},
        },
        "parameterValue": {
            "arrayValues": [
                {"value": bucket_name} for bucket_name in bucket_names
            ]
        },
    }]

  query = textwrap.dedent(f"""
      SELECT
        bucket,
        COUNT(*) AS total_objects,
        COUNTIF(securityInsights.publicAccessInsight.readPublicAccess = 'PUBLIC') AS public_read_objects,
        COUNTIF(securityInsights.publicAccessInsight.writePublicAccess = 'PUBLIC') AS public_write_objects,
        COUNTIF(retentionExpirationTime IS NOT NULL) AS objects_with_retention,
        COUNTIF(encryptionType = 'CMEK') AS cmek_objects,
        COUNTIF(encryptionType = 'CSEK') AS csek_objects,
        COUNTIF(encryptionType = 'GMEK') AS gmek_objects
      FROM
        `{project_id}.{dataset_name}.object_attributes_latest_snapshot_view`
      {bucket_filter}
      GROUP BY
        bucket
  """).strip()

  payload = {
      "query": query,
      "useLegacySql": False,
  }
  if query_parameters:
    payload["parameterMode"] = "NAMED"
    payload["queryParameters"] = query_parameters

  with cloud_rest_helpers_nodeps.get_authorized_session(
      skill=_SKILL, script=_SCRIPT, project_id=project_id
  ) as session:
    schema_fields, rows = cloud_rest_helpers_nodeps.execute_bigquery_query(
        project_id=project_id,
        payload=payload,
        session=session,
        skill=_SKILL,
        script=_SCRIPT,
    )

  telemetry = []
  for r in rows:
    r_f = r.get("f", [])
    row_dict = {
        f["name"]: cloud_rest_helpers_nodeps.parse_bq_value(
            r_f[i].get("v") if i < len(r_f) else None, f
        )
        for i, f in enumerate(schema_fields)
    }
    telemetry.append({
        "bucket": row_dict.get("bucket"),
        "total_objects": row_dict.get("total_objects"),
        "public_read_objects": row_dict.get("public_read_objects"),
        "public_write_objects": row_dict.get("public_write_objects"),
        "objects_with_retention": row_dict.get("objects_with_retention"),
        "cmek_objects": row_dict.get("cmek_objects"),
        "csek_objects": row_dict.get("csek_objects"),
        "gmek_objects": row_dict.get("gmek_objects"),
    })

  return telemetry


def main() -> None:
  parser = argparse.ArgumentParser(
      description=(
          "Script to fetch aggregated object-level telemetry for buckets in a"
          " Storage Insights dataset."
      )
  )
  parser.add_argument(
      "--project_id", type=str, required=True, help="The GCP project ID."
  )
  parser.add_argument(
      "--dataset_name", type=str, required=True, help="The linked dataset name."
  )
  parser.add_argument(
      "--bucket_names",
      type=str,
      help=(
          "Comma-separated list of bucket names to query. If not provided, all"
          " buckets in the dataset are analyzed."
      ),
  )
  args = parser.parse_args()

  bucket_names = (
      [b.strip() for b in args.bucket_names.split(",")]
      if args.bucket_names
      else None
  )

  telemetry = fetch_object_telemetry(
      project_id=args.project_id,
      dataset_name=args.dataset_name,
      bucket_names=bucket_names,
  )
  print(json.dumps(telemetry, indent=2))


if __name__ == "__main__":
  main()
