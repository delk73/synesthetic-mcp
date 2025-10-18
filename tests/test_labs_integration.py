"""
Integration tests for labs schema retrieval workflow.

Simulates the exact request/response pattern used by labs when fetching
schemas for Azure OpenAI strict JSON schema mode binding.
"""
from __future__ import annotations

import json

from mcp.core import get_schema
from mcp.stdio_main import dispatch


def test_labs_get_schema_request_with_version():
    """
    Simulate labs calling get_schema with version parameter.
    
    Labs sends:
      {"jsonrpc": "2.0", "id": "...", "method": "get_schema",
       "params": {"name": "synesthetic-asset", "version": "0.7.3"}}
    
    Expected response should include:
      - ok: true
      - name: "synesthetic-asset"
      - version: "0.7.3" (extracted from $id)
      - path: (schema file path)
      - schema: (full schema object)
    """
    # Simulate the dispatch layer (what stdio_main.py calls)
    params = {"name": "synesthetic-asset", "version": "0.7.3"}
    result = dispatch("get_schema", params)
    
    # Verify all expected fields are present
    assert result["ok"] is True, f"Expected ok=True, got: {result}"
    assert result["name"] == "synesthetic-asset", f"Missing or incorrect name: {result.get('name')}"
    assert result["version"] == "0.7.3", f"Missing or incorrect version: {result.get('version')}"
    assert "path" in result, "Missing path field"
    assert "schema" in result, "Missing schema field"
    
    # Verify schema content
    schema = result["schema"]
    assert isinstance(schema, dict), "Schema should be a dict"
    assert "$id" in schema, "Schema should have $id"
    assert "0.7.3" in schema["$id"], f"Schema $id should contain version: {schema.get('$id')}"


def test_labs_get_schema_direct_core_call():
    """
    Test the core function directly as labs might use it.
    """
    # Direct call with version
    result = get_schema("synesthetic-asset", version="0.7.3")
    
    assert result["ok"] is True
    assert result["name"] == "synesthetic-asset"
    assert result["version"] == "0.7.3"
    assert result["path"] is not None
    assert result["schema"] is not None


def test_labs_schema_not_found_response():
    """
    Verify error response format when schema doesn't exist.
    """
    result = get_schema("nonexistent-schema", version="0.7.3")
    
    assert result["ok"] is False
    assert result["reason"] == "not_found"
    # Error response should not have name/version/path fields
    assert "name" not in result
    assert "schema" not in result


def test_backward_compatibility_no_version():
    """
    Ensure existing callers that don't send version still work.
    """
    params = {"name": "synesthetic-asset"}
    result = dispatch("get_schema", params)
    
    assert result["ok"] is True
    assert result["name"] == "synesthetic-asset"
    assert result["version"] == "0.7.3"  # Still extracted from $id
    assert "schema" in result


def test_all_canonical_schemas_have_version():
    """
    Verify that all canonical schemas return version info.
    """
    from mcp.core import list_schemas
    
    schemas_list = list_schemas()
    assert schemas_list["ok"] is True
    
    for schema_info in schemas_list["schemas"]:
        name = schema_info["name"]
        result = get_schema(name)
        
        if result["ok"]:
            # Should have version either from top-level field or $id
            version = result.get("version", "")
            assert version != "", f"Schema {name} should have version info"
