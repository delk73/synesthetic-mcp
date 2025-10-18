# Issue Resolution: Labs Schema Retrieval from MCP Server

## Summary

✅ **RESOLVED** - The MCP server's `get_schema` endpoint has been enhanced to provide complete metadata required by the labs repository for Azure OpenAI strict JSON schema mode binding.

## What Was Fixed

### 1. Missing Metadata Fields
**Problem:** Response was missing `name` and `path` fields
**Solution:** Added both fields to the response

### 2. Empty Version Field
**Problem:** Version was empty string (`""`) for canonical schemas
**Solution:** Extract version from `$id` URL when top-level `version` field is missing

### 3. Version Parameter Support
**Problem:** Function didn't accept `version` parameter that labs was sending
**Solution:** Added optional `version` parameter (currently logged, preparing for future routing)

## New Response Format

```json
{
  "jsonrpc": "2.0",
  "id": "...",
  "result": {
    "ok": true,
    "name": "synesthetic-asset",           // ✓ Now included
    "version": "0.7.3",                     // ✓ Extracted from $id
    "path": "/path/to/schema.json",        // ✓ Now included
    "schema": {                             // ✓ Full schema
      "$id": "https://schemas.synesthetic.dev/0.7.3/synesthetic-asset.schema.json",
      "$schema": "https://json-schema.org/draft/2020-12/schema",
      // ... full schema definition
    }
  }
}
```

## Answers to Your Questions

### 1. Does MCP support versioned schemas?

**Yes, partially:**
- ✅ Accepts `version` parameter in requests
- ✅ Extracts and returns version in response
- ✅ Logs version for observability
- ⏳ Future: Will route to different schema files based on version
- **Current:** Returns the single available version

### 2. What should the response format be?

**Implemented as shown above:**
- `name`: Schema name (echoed from request)
- `version`: Extracted from schema's `$id` URL or `version` field
- `path`: Absolute filesystem path to schema file
- `schema`: Complete JSON schema definition

### 3. Should labs omit the version parameter?

**No - keep sending it:**
- Provides visibility in MCP logs
- Forward-compatible for future version routing
- Documents intent clearly
- No performance cost

## For Labs Team

### Immediate Action Required
**None!** The fix is backward compatible and ready to use.

### What Changed
Your existing code will now work correctly:

```python
# Your current code
response = get_schema_from_mcp("synesthetic-asset", version="0.7.3")

# Now returns complete metadata
assert response["ok"] == True
assert response["name"] == "synesthetic-asset"     # ✓ Now present
assert response["version"] == "0.7.3"              # ✓ Now present
assert response["path"]                            # ✓ Now present
assert response["schema"]                          # ✓ Always present

# Azure OpenAI binding now works
bind_schema_to_openai(
    schema=response["schema"],
    version=response["version"]
)
```

### Recommended Update (Optional)

Add assertions to catch any future issues:

```python
def get_schema_from_mcp(name: str, version: str) -> dict:
    response = mcp_client.call("get_schema", {"name": name, "version": version})
    
    if not response.get("ok"):
        raise RuntimeError(f"Failed to load schema: {response}")
    
    # Validate response has required fields
    required_fields = ["name", "version", "schema"]
    missing = [f for f in required_fields if f not in response]
    if missing:
        raise ValueError(f"MCP response missing fields: {missing}")
    
    # Validate version matches request
    if response["version"] != version:
        logging.warning(
            f"Version mismatch: requested {version}, got {response['version']}"
        )
    
    return response
```

## Testing

All tests pass (63 tests):
- ✅ Version parameter handling
- ✅ Metadata completeness
- ✅ Version extraction from `$id`
- ✅ Backward compatibility
- ✅ Error responses
- ✅ Golden fixture replay
- ✅ All transport modes (STDIO, Socket, TCP)

## Version Extraction Logic

The MCP server extracts version using this priority:

1. **Top-level `version` field** (if present)
2. **Parse `$id` URL** to extract version segment
   - Example: `https://schemas.synesthetic.dev/0.7.3/asset.schema.json` → `"0.7.3"`
3. **Empty string** (fallback for malformed schemas)

For canonical synesthetic schemas (v0.7.3), version is extracted from the `$id` URL.

## Backward Compatibility

✅ **100% backward compatible**

- Old clients that don't send `version` parameter: **Still work**
- Responses now include additional fields: **Non-breaking**
- All existing fields remain: **No changes**

## Documentation

New documentation added:
- `docs/get_schema_api.md` - Complete API specification
- `CHANGELOG_v0.2.10.md` - Detailed change log

## Next Steps

### For MCP Server Deployment
1. Deploy updated MCP server
2. Verify logs show version parameter (if labs sends it)
3. Monitor for any unexpected issues

### For Labs Integration
1. **No changes required** - your code will work immediately
2. Optional: Add validation assertions (see above)
3. Optional: Add logging for version metadata

### Future Enhancement
When multi-version support is needed:
- MCP will route to version-specific schema directories
- Current `version` parameter will control routing
- Error response if requested version unavailable

## Files Modified

- `mcp/core.py` - Enhanced `get_schema` function
- `mcp/stdio_main.py` - Updated dispatcher
- `tests/test_validate.py` - Updated tests
- `tests/test_labs_integration.py` - New integration tests
- `tests/fixtures/golden.jsonl` - Updated fixture
- `docs/get_schema_api.md` - New API docs
- `CHANGELOG_v0.2.10.md` - Release notes

## Contact

For questions or issues:
- Check logs for version parameter: `mcp:get_schema name=... version=...`
- Review `docs/get_schema_api.md` for complete API reference
- Run tests: `pytest tests/test_labs_integration.py -xvs`
