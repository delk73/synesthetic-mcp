# get_schema API Documentation

## Overview

The `get_schema` method retrieves a JSON schema by name from the MCP server's schema directory.

## Request Format

```json
{
  "jsonrpc": "2.0",
  "id": "<request-id>",
  "method": "get_schema",
  "params": {
    "name": "synesthetic-asset",     // Required: schema name
    "version": "0.7.3"                // Optional: version hint (logged but not used for routing)
  }
}
```

### Parameters

- **`name`** (required, string): The schema name without the `.schema.json` suffix
  - Example: `"synesthetic-asset"`, `"control"`, `"haptic"`
  - Must not contain path traversal characters (`../`, absolute paths)
  
- **`version`** (optional, string): Version hint for future version routing
  - Currently logged for observability but does not affect schema selection
  - Intended for forward compatibility when multiple schema versions are supported
  - Example: `"0.7.3"`

## Response Format

### Success Response

```json
{
  "jsonrpc": "2.0",
  "id": "<request-id>",
  "result": {
    "ok": true,
    "name": "synesthetic-asset",
    "version": "0.7.3",
    "path": "/path/to/schemas/synesthetic-asset.schema.json",
    "schema": {
      "$id": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      // ... full schema definition
    }
  }
}
```

#### Response Fields

- **`ok`** (boolean): Always `true` for success
- **`name`** (string): The requested schema name (echoed back)
- **`version`** (string): Schema version extracted from:
  1. Schema's top-level `version` field (if present), OR
  2. The version segment in the schema's `$id` URL
  - Example: `"0.7.3"` extracted from `https://schemas.synesthetic.dev/0.7.3/...`
- **`path`** (string): Absolute filesystem path to the schema file
- **`schema`** (object): The complete JSON schema definition

### Error Responses

#### Schema Not Found

```json
{
  "jsonrpc": "2.0",
  "id": "<request-id>",
  "result": {
    "ok": false,
    "reason": "not_found"
  }
}
```

#### Invalid Path (Path Traversal Attempt)

```json
{
  "jsonrpc": "2.0",
  "id": "<request-id>",
  "result": {
    "ok": false,
    "reason": "validation_failed",
    "errors": [
      {
        "path": "/name",
        "msg": "invalid_path"
      }
    ]
  }
}
```

## Version Extraction Logic

The server extracts the version using the following priority:

1. **Top-level `version` field**: If the schema JSON contains a root-level `"version": "1.2.3"` field
2. **`$id` URL parsing**: Extracts version from the `$id` URL path
   - Pattern: `https://host/<VERSION>/schema-name.schema.json`
   - Example: `0.7.3` from `https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json`
3. **Empty string**: If neither is available (edge case)

## Use Cases

### Azure OpenAI Strict JSON Schema Mode

Labs repository uses this endpoint to fetch schemas for binding to Azure OpenAI's strict JSON schema mode:

```python
# labs/generator/external.py
response = get_schema_from_mcp("synesthetic-asset", version="0.7.3")

if not response.get("ok"):
    raise RuntimeError(f"Failed to load schema: {response}")

schema_version = response["version"]  # "0.7.3"
schema_def = response["schema"]       # Full schema object

# Bind to Azure OpenAI
bind_schema_to_openai(schema_def, version=schema_version)
```

## Backward Compatibility

The `version` parameter is optional. Clients that don't send it will still receive the complete response with version extracted from the schema itself:

```json
// Old-style request (still supported)
{
  "method": "get_schema",
  "params": {"name": "synesthetic-asset"}
}

// Response includes version anyway
{
  "result": {
    "ok": true,
    "name": "synesthetic-asset",
    "version": "0.7.3",  // Extracted from $id
    "path": "...",
    "schema": {...}
  }
}
```

## Future: Multi-Version Support

The `version` parameter is designed for forward compatibility when the MCP server supports multiple schema versions:

```json
// Future: Request specific version
{
  "method": "get_schema",
  "params": {
    "name": "synesthetic-asset",
    "version": "0.8.0"  // Route to different schema file
  }
}
```

Currently, the server:
- Logs the requested version for observability
- Returns the only available version (from local schemas directory)
- Does NOT route to different files based on version

## Implementation Details

### Core Function Signature

```python
def get_schema(name: str, version: str | None = None) -> Dict[str, Any]:
    """
    Retrieve a schema by name.
    
    Args:
        name: Schema name (e.g., "synesthetic-asset")
        version: Optional version hint (currently logged but not used for routing)
    
    Returns:
        Dict with ok, schema, name, version, and path fields
    """
```

### STDIO Dispatch

```python
def dispatch(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    if method == "get_schema":
        name = params.get("name", "")
        version = params.get("version")
        if version:
            logging.info(f"mcp:get_schema name={name} version={version}")
        return get_schema(name, version)
```

## Testing

See `tests/test_labs_integration.py` for comprehensive test coverage:

- Version parameter handling
- Metadata field presence (`name`, `version`, `path`)
- Version extraction from `$id` URLs
- Backward compatibility (no version parameter)
- Error responses

## Related Endpoints

- **`list_schemas`**: Enumerate all available schemas with version metadata
- **`validate_asset`**: Validate an asset against its `$schema` reference
- **`governance_audit`**: Verify schema governance compliance

## References

- MCP Specification: `docs/mcp_spec.md`
- Schema Repository: `libs/synesthetic-schemas/`
- Labs Integration: External repository using this API
