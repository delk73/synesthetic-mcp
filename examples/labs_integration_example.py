#!/usr/bin/env python3
"""
Example: Using MCP get_schema with labs integration

This script demonstrates how the labs repository can successfully
retrieve schemas from the MCP server for Azure OpenAI binding.
"""

import json
import sys
from pathlib import Path

# Add MCP to path for this example
sys.path.insert(0, str(Path(__file__).parent.parent))

from mcp.core import get_schema


def get_schema_from_mcp(name: str, version: str) -> dict:
    """
    Fetch a schema from MCP server.
    
    This function simulates the labs repository's get_schema_from_mcp
    implementation.
    
    Args:
        name: Schema name (e.g., "synesthetic-asset")
        version: Required version (e.g., "0.7.3")
    
    Returns:
        Complete schema metadata including name, version, path, and schema
    
    Raises:
        RuntimeError: If schema retrieval fails
    """
    # Call MCP's get_schema function
    response = get_schema(name, version=version)
    
    # Check for success
    if not response.get("ok"):
        raise RuntimeError(f"Failed to load schema: {response}")
    
    # Validate response has required fields (defensive programming)
    required_fields = ["name", "version", "schema"]
    missing = [f for f in required_fields if f not in response]
    if missing:
        raise ValueError(f"MCP response missing required fields: {missing}")
    
    # Optionally validate version matches request
    if response["version"] != version:
        print(
            f"Warning: Version mismatch - requested {version}, "
            f"got {response['version']}"
        )
    
    return response


def bind_schema_to_azure_openai(schema: dict, version: str) -> dict:
    """
    Simulate Azure OpenAI strict JSON schema mode binding.
    
    Args:
        schema: Full JSON schema definition
        version: Schema version for tracking
    
    Returns:
        Bound schema configuration
    """
    # Azure OpenAI requires strict JSON schema mode
    # Reference: https://learn.microsoft.com/en-us/azure/ai-services/openai/
    
    bound_config = {
        "type": "json_schema",
        "json_schema": {
            "name": schema.get("title", "unknown"),
            "schema": schema,
            "strict": True,
        },
        "metadata": {
            "schema_version": version,
            "schema_id": schema.get("$id"),
        }
    }
    
    return bound_config


def main():
    """
    Main example workflow demonstrating labs integration.
    """
    print("=" * 70)
    print("MCP Schema Retrieval Example - Labs Integration")
    print("=" * 70)
    
    # Step 1: Retrieve schema from MCP
    print("\n[1] Retrieving schema from MCP server...")
    try:
        response = get_schema_from_mcp("synesthetic-asset", version="0.7.3")
        print("✅ Schema retrieved successfully")
    except Exception as e:
        print(f"❌ Failed to retrieve schema: {e}")
        return 1
    
    # Step 2: Validate response structure
    print("\n[2] Validating response structure...")
    print(f"   - ok: {response['ok']}")
    print(f"   - name: {response['name']}")
    print(f"   - version: {response['version']}")
    print(f"   - path: {response['path']}")
    print(f"   - schema: <{len(json.dumps(response['schema']))} bytes>")
    
    if response["name"] != "synesthetic-asset":
        print("❌ Schema name mismatch!")
        return 1
    
    if response["version"] != "0.7.3":
        print("❌ Schema version mismatch!")
        return 1
    
    print("✅ Response structure valid")
    
    # Step 3: Extract schema details
    print("\n[3] Schema details...")
    schema = response["schema"]
    print(f"   - $id: {schema.get('$id')}")
    print(f"   - $schema: {schema.get('$schema')}")
    print(f"   - title: {schema.get('title', 'N/A')}")
    print(f"   - type: {schema.get('type')}")
    print(f"   - properties: {len(schema.get('properties', {}))} fields")
    
    # Step 4: Bind to Azure OpenAI (simulated)
    print("\n[4] Binding to Azure OpenAI strict JSON schema mode...")
    try:
        bound = bind_schema_to_azure_openai(
            schema=response["schema"],
            version=response["version"]
        )
        print("✅ Schema bound successfully")
        print(f"   - Strict mode: {bound['json_schema']['strict']}")
        print(f"   - Tracked version: {bound['metadata']['schema_version']}")
    except Exception as e:
        print(f"❌ Failed to bind schema: {e}")
        return 1
    
    # Step 5: Summary
    print("\n" + "=" * 70)
    print("SUCCESS - All steps completed")
    print("=" * 70)
    print("\nLabs can now:")
    print("  ✅ Retrieve schemas with complete metadata")
    print("  ✅ Extract version information (0.7.3)")
    print("  ✅ Bind schemas to Azure OpenAI strict mode")
    print("  ✅ Track schema governance")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
