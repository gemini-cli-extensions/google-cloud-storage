"""mcp_server.py - GCS-OKF MCP Server.

This script acts as the Model Context Protocol (MCP) server for GCS-OKF.
It exposes the four core OKF verbs (peek, list_regions, expand, write_okf)
as MCP tools. It relies on core.py to handle the actual GCS operations.
"""

import json

from mcp.server import fastmcp

import core

# Initialize the FastMCP server
app = fastmcp.FastMCP("GCS-OKF-Navigator")


@app.tool()
def peek(gs_uri: str) -> str:
  """Returns the Tier 0 Object Knowledge Finder (OKF) summary for a GCS object.

  Use this tool first to retrieve a high-level summary of a GCS object's
  contents
  and evaluate if the object is relevant before fetching detailed region trees
  or content.

  Args:
    gs_uri: The target GCS object URI (e.g. 'gs://bucket_name/object_name').

  Returns:
    Summary text string or diagnostic error detailing context capacity.
  """
  return core.peek(gs_uri)


@app.tool()
def list_regions(gs_uri: str) -> str:
  """Returns the Tier 1/2 OKF Table of Contents (region index) for a GCS object.

  Use this tool to inspect all semantic regions, inclusive byte ranges, titles,
  summaries, and keywords defined on the object.

  Args:
    gs_uri: The target GCS object URI (e.g. 'gs://bucket_name/object_name').

  Returns:
    JSON string of region descriptors or diagnostic error detailing context
    capacity.
  """
  return core.list_regions(gs_uri)


@app.tool()
def expand(gs_uri: str, start_byte: int, end_byte: int) -> str:
  """Fetches a targeted byte-range slice (Tier 2/3) from a GCS object.

  Use this tool after inspecting regions via list_regions to read specific text
  slices.

  Args:
    gs_uri: The target GCS object URI (e.g. 'gs://bucket_name/object_name').
    start_byte: 0-indexed starting byte offset (inclusive).
    end_byte: 0-indexed ending byte offset (inclusive).

  Returns:
    Decoded text content of the requested slice (or Base64 for binary data).
  """
  return core.expand(gs_uri, start_byte, end_byte)


@app.tool()
def write_okf(
    gs_uri: str,
    summary: str,
    regions_json: str,
    created_at: str = "",
    model: str = "",
) -> str:
  """Writes a generated OKF index manifest into GCS object custom metadata contexts.

  Args:
    gs_uri: The target GCS object URI (e.g. 'gs://bucket_name/object_name').
    summary: High-level overview text string for the object.
    regions_json: Valid JSON array string of region objects, e.g.: '[{"id":
      "r1", "start_byte": 0, "end_byte": 100, "title": "Intro", "keywords":
      ["a"]}]'
    created_at: Optional ISO 8601 timestamp string.
    model: Optional AI model identifier string (e.g. 'gemini-1.5-pro').

  Returns:
    Success status message or error message if object context capacity is
    exceeded.
  """
  try:
    regions = json.loads(regions_json)
  except json.JSONDecodeError as e:
    return f"Error parsing regions_json: Invalid JSON string ({str(e)})"

  if not isinstance(regions, list):
    return (
        "Invalid regions_json: Must be a JSON array of region objects, got"
        f" {type(regions).__name__}."
    )

  try:
    return core.write_okf(
        gs_uri, summary, regions, created_at=created_at, model=model
    )
  except Exception as e:  # pylint: disable=broad-exception-caught
    return f"Error writing OKF: {str(e)}"


if __name__ == "__main__":
  # Runs the server using standard stdin/stdout for MCP communication
  app.run()
