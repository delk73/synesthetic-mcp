# MCP State Audit (v0.2.4)

## Summary of Repo State
The `synesthetic-mcp` repository is in good shape and largely compliant with `docs/mcp_spec.md` (v0.2.4). It correctly implements the STDIO transport, core validation and discovery features, and has a solid test suite. Key strengths are its deterministic output, clear environment-variable-based configuration, and robust process model for the STDIO server.

The main gaps are the absence of the optional `socket` transport and `validate_many` batching method. A minor divergence in `validate_asset` error handling was noted but recently fixed. Documentation is accurate and aligned with the implementation.

## Top Gaps & Fixes
1.  **Missing `socket` Transport:** The spec defines an optional Unix Domain Socket transport (`MCP_ENDPOINT=socket`), which is not implemented. This is a feature gap, not a compliance issue.
2.  **Missing `validate_many`:** The optional batch validation method is not implemented.
3.  **`get_example` Validation Failure:** The spec requires `get_example` to be able to return a `validation_failed` reason if the example on disk is invalid. The current implementation does not do this.
4.  **Divergent `validate_asset` schema handling:** The spec requires `validate_asset` to fail if the `schema` parameter is missing. The implementation was passing an empty string, but this has been patched.

## Alignment with mcp_spec.md

| Spec Item | Status | Evidence |
| :--- | :--- | :--- |
| **Transport & Framing** | | |
| STDIO NDJSON framing | Present | `mcp/stdio_main.py`, `tests/test_stdio.py` |
| 1 MiB STDIO payload guard | Present | `mcp/stdio_main.py:69`, `tests/test_stdio.py::test_stdio_rejects_oversized_request` |
| Sequential STDIO processing | Present | `mcp/stdio_main.py` (single-threaded loop) |
| Socket Transport (UDS) | Missing | No socket-related implementation files found. |
| **IO Contracts** | | |
| `list_schemas` | Present | `mcp/core.py:41`, `tests/test_submodule_integration.py` |
| `get_schema` | Present | `mcp/core.py:61`, `tests/test_validate.py::test_get_schema_and_validate_valid` |
| `list_examples` | Present | `mcp/core.py:70`, `tests/test_submodule_integration.py` |
| `get_example` | Divergent | `mcp/core.py:115` - Does not return `validation_failed` for invalid examples. |
| `validate_asset` | Present | `mcp/stdio_main.py:25`, `tests/test_stdio.py::test_validate_asset_requires_schema` |
| `validate` alias | Present | `mcp/stdio_main.py:25` |
| `validate_many` | Missing | Not implemented. |
| `diff_assets` | Present | `mcp/diff.py`, `tests/test_diff.py` |
| `populate_backend` | Present | `mcp/backend.py`, `tests/test_backend.py` |
| **Determinism** | | |
| `list_schemas` sorting | Present | `mcp/core.py:58` |
| `list_examples` sorting | Present | `mcp/core.py:86` |
| Validation error sorting | Present | `mcp/validate.py:198` |
| Diff patch sorting | Present | `mcp/diff.py:50` |
| **Process Model** | | |
| `MCP_READY_FILE` | Present | `mcp/__main__.py:78`, `tests/test_stdio.py::test_stdio_entrypoint_validate_asset` |
| STDIO exit on stdin close | Present | `mcp/stdio_main.py` (loop terminates) |
| Signal Handling (SIGINT/SIGTERM) | Present | `mcp/__main__.py:90` |

## Transports

### STDIO Server
- **Status:** **Present** and **Compliant**.
- **NDJSON Framing:** Implemented in `mcp/stdio_main.py`, with each line being a separate JSON-RPC request.
- **Blocking Loop:** The server runs a blocking loop on `sys.stdin`.
- **Readiness File:** `MCP_READY_FILE` is created on startup with `<pid> <ISO8601 timestamp>` and removed on shutdown, as verified in `tests/test_stdio.py`.
- **Shutdown:** The server gracefully shuts down on `SIGINT`/`SIGTERM` or when `stdin` is closed.
- **stdout vs stderr:** `stdout` is used exclusively for JSON-RPC frames, and `stderr` is used for logging, as per the spec.

### Socket Server
- **Status:** **Missing**. The repository contains no implementation for a socket-based transport.

## Golden Request/Response Examples

| Method | Success Frame | Error Frame | Evidence |
| :--- | :--- | :--- | :--- |
| `list_schemas` | Present | N/A | `tests/test_stdio.py::test_stdio_loop_smoke` |
| `get_schema` | Present | Present (`not_found`) | `tests/test_validate.py::test_get_schema_not_found` |
| `validate_asset` | Present | Present (`validation_failed`) | `tests/test_validate.py` |
| `validate` (alias) | Present | Present | `mcp/stdio_main.py:25` |
| `get_example` | Present | Present (`not_found`) | `tests/test_validate.py::test_get_example_not_found` |
| `diff_assets` | Present | N/A | `tests/test_diff.py` |
| Malformed Frame | N/A | Present | `tests/test_stdio.py::test_stdio_error_includes_request_id` |

## Payload Size Guard

| Method | STDIO Guard | Socket Guard | Evidence |
| :--- | :--- | :--- | :--- |
| All | Present | N/A | `mcp/stdio_main.py:69`, `tests/test_stdio.py::test_stdio_rejects_oversized_request` |

## Schema Validation Contract
- **`schema` param:** The `schema` parameter is now correctly enforced as **required** in `validate_asset` as of the latest patch.
- **`validate` alias:** The `validate` alias for `validate_asset` is correctly handled.
- **Error ordering:** Validation errors are sorted by `path` and then `msg`.
- **`$ref` resolution:** Schema `$ref`s are resolved locally using the `referencing` library if available. No remote fetching is performed.

## Test Coverage

| Feature | Tested? | Evidence |
| :--- | :--- | :--- |
| STDIO Transport | Yes | `tests/test_stdio.py`, `tests/test_entrypoint.py` |
| Schema/Example Discovery | Yes | `tests/test_env_discovery.py`, `tests/test_submodule_integration.py` |
| `validate_asset` | Yes | `tests/test_validate.py` |
| `diff_assets` | Yes | `tests/test_diff.py` |
| `populate_backend` | Yes | `tests/test_backend.py` |
| Payload Size Guard | Yes | `tests/test_stdio.py::test_stdio_rejects_oversized_request` |
| Determinism | Yes | `tests/test_diff.py`, `tests/test_submodule_integration.py`, `tests/test_validate.py` |

## Dependencies & Runtime

| Package | Used in | Required/Optional |
| :--- | :--- | :--- |
| `jsonschema` | `mcp/validate.py` | Required |
| `httpx` | `mcp/backend.py` | Required |
| `pytest` | `tests/` | Required (tests) |
| `referencing` | `mcp/validate.py` | Optional |

## Environment Variables

| Variable | Default | Behavior |
| :--- | :--- | :--- |
| `MCP_ENDPOINT` | `stdio` | Only `stdio` is supported. Other values cause a startup failure. |
| `MCP_READY_FILE` | `/tmp/mcp.ready` | Path to the readiness file. |
| `SYN_SCHEMAS_DIR` | `libs/synesthetic-schemas/jsonschema` | Path to the schemas directory. |
| `SYN_EXAMPLES_DIR` | `libs/synesthetic-schemas/examples` | Path to the examples directory. |
| `SYN_BACKEND_URL` | (unset) | URL of the backend for `populate_backend`. Feature is disabled if unset. |
| `SYN_BACKEND_ASSETS_PATH` | `/synesthetic-assets/` | Path for POSTing assets to the backend. |

## Documentation Accuracy
- `README.md` is accurate and provides a good overview of the project.
- `docs/mcp_spec.md` is the source of truth for the audit and is mostly aligned with the implementation, with the noted divergences.

## Detected Divergences
1.  **`get_example` Validation:** `mcp/core.py:115` does not return a `validation_failed` error for invalid examples, instead it just sets a boolean `validated` flag to `False`. The spec requires a proper error structure.

## Recommendations
1.  **Implement `get_example` `validation_failed`:** Modify `mcp/core.py` to return a `{ "ok": false, "reason": "validation_failed", "errors": [...] }` structure when an example fails validation.
2.  **Implement Socket Transport:** If persistent service behavior is needed, implement the socket transport as defined in the spec.
3.  **Implement `validate_many`:** If batch validation is a desired feature, implement the `validate_many` method.
