# MCP State Audit (v0.2.4)

## Summary of repo state
The `synesthetic-mcp` repository is in a good state, with a solid foundation for the features it implements. The STDIO transport is compliant with the spec, including NDJSON framing, payload size guards, and correct stream separation. The core validation and discovery logic is sound and well-tested. Key areas for improvement are tightening the enforcement of the `schema` parameter at the transport boundary and implementing the optional `socket` transport and `validate_many` batching if they become necessary.

## Top gaps & fixes
1.  **`validate_asset` `schema` parameter enforcement:** The `schema` parameter is not strictly enforced at the `stdio_main.py` boundary, allowing empty strings to pass through. This should be a hard failure at the transport layer.
2.  **Socket Transport Missing:** The spec defines an optional but important socket-based transport, which is not implemented.
3.  **`validate_many` Missing:** The optional batch validation method `validate_many` is not implemented.
4.  **`get_example` spec divergence:** The spec for `get_example` does not list `validation_failed` as a possible error reason, but the implementation can and does produce this.

## Alignment with mcp_spec.md

| Spec item | Status | Evidence |
| :--- | :--- | :--- |
| STDIO NDJSON framing & sequential handling | Present | `mcp/stdio_main.py` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py`, `tests/test_stdio.py` |
| 1 MiB per-request STDIO limit | Present | `mcp/stdio_main.py`, `tests/test_stdio.py` |
| `validate_asset` requires `schema` | Divergent | `mcp/stdio_main.py:25` passes an empty string if missing. |
| Socket Transport | Missing | Not implemented (optional feature). |
| `validate_many` | Missing | Not implemented (optional feature). |
| `get_example` with `validation_failed` | Divergent | `docs/mcp_spec.md` is missing this error case. |

## Transports
The implementation **only** supports the STDIO transport.

### STDIO server entrypoint & process model
- **NDJSON framing:** Correctly implemented in `mcp/stdio_main.py`.
- **Blocking loop:** The main loop in `mcp/stdio_main.py` blocks on `sys.stdin`.
- **Signals:** `SIGINT` and `SIGTERM` are handled in `mcp/__main__.py` to allow graceful shutdown.
- **Readiness file:** The ready file is created and cleared as expected in `mcp/__main__.py`.
- **Shutdown semantics:** The server exits when `stdin` closes.
- **stdout vs stderr:** `stdout` is used for JSON-RPC frames, and `stderr` is used for logging.

### Socket server
The socket server is **not implemented**.

## Golden request/response examples

| Method | Success frame | Error frame | Evidence |
| :--- | :--- | :--- | :--- |
| `list_schemas` | Present | N/A | `tests/test_submodule_integration.py` |
| `get_schema` | Present | Present | `tests/test_validate.py` |
| `validate_asset` | Present | Present | `tests/test_validate.py` |
| `validate` (alias) | Present | Present | `mcp/stdio_main.py` |
| `get_example` | Present | Present | `tests/test_validate.py` |
| `diff_assets` | Present | N/A | `tests/test_diff.py` |
| Malformed frame | N/A | Present | `tests/test_stdio.py` |

## Payload size guard

| Method | STDIO guard | Socket guard | Evidence |
| :--- | :--- | :--- | :--- |
| All | Present | Missing | `mcp/stdio_main.py`, `tests/test_stdio.py` |

## Schema validation contract
- **Required `schema` param:** The `schema` parameter is not properly enforced at the transport layer.
- **Alias handling:** The `validate` alias for `validate_asset` is correctly handled.
- **Error ordering:** Validation errors are sorted by `path` and then `msg`.
- **`validate_asset` behavior:** `validate_asset` is implemented and works as expected, aside from the missing `schema` parameter enforcement.

## Optional batching
The `validate_many` method is **not implemented**.

## Logging hygiene
- **`stdout` frames only:** Correct.
- **`stderr` logs/diagnostics:** Correct.
- **Deterministic timestamps:** Logs use ISO-8601 timestamps.

## Container & health

| Aspect | Present/Missing/Divergent | Evidence |
| :--- | :--- | :--- |
| `docker-compose` services | Present | `docker-compose.yml` |
| Environment variables | Present | `docker-compose.yml` |
| Healthcheck | Present | `docker-compose.yml` |

## Schema discovery & validation

| Source | Mechanism | Evidence |
| :--- | :--- | :--- |
| Environment variables | `SYN_SCHEMAS_DIR` and `SYN_EXAMPLES_DIR` | `mcp/core.py`, `tests/test_env_discovery.py` |
| Submodule | `libs/synesthetic-schemas` | `mcp/core.py`, `tests/test_submodule_integration.py` |

## Test coverage

| Feature | Tested? | Evidence |
| :--- | :--- | :--- |
| STDIO framing, ready file, oversize guard | Yes | `tests/test_stdio.py` |
| Transport setup & shutdown handling | Yes | `tests/test_entrypoint.py` |
| Validation aliasing, ordering, payload cap | Yes | `tests/test_validate.py` |
| Backend success/error/size handling | Yes | `tests/test_backend.py` |
| Env overrides & submodule fallback | Yes | `tests/test_env_discovery.py`, `tests/test_submodule_integration.py` |
| Diff determinism | Yes | `tests/test_diff.py` |

## Dependencies & runtime

| Package | Used in | Required/Optional |
| :--- | :--- | :--- |
| `jsonschema` | `mcp/validate.py` | Required |
| `httpx` | `mcp/backend.py` | Required |
| `pytest` | `tests/` | Required (tests) |
| `referencing` | `mcp/validate.py` | Optional |

## Environment variables

- `MCP_ENDPOINT`: Only `stdio` is supported.
- `MCP_READY_FILE`: Correctly used to signal readiness.
- `SYN_SCHEMAS_DIR` & `SYN_EXAMPLES_DIR`: Used to override default schema and example paths.
- `SYN_BACKEND_URL`: Gates the `populate_backend` feature.
- `SYN_BACKEND_ASSETS_PATH`: Correctly overrides the backend POST path.

## Documentation accuracy
The `README.md` is accurate, but `docs/mcp_spec.md` has a minor divergence in the `get_example` error cases.

## Detected divergences
- The `schema` parameter for `validate_asset` is not strictly enforced at the transport layer.
- The `get_example` method can return a `validation_failed` error, which is not documented in the spec.

## Recommendations
- **Fix `validate_asset` Divergence:** Modify `mcp.stdio_main` to return a `validation_failed` error if the `schema` parameter is missing in a `validate_asset` call.
- **Update Spec:** Add `validation_failed` as a possible reason for failure in the `get_example` method in `docs/mcp_spec.md`.
- **Consider Optional Features:** Plan for the implementation of the `socket` transport and `validate_many` if they are desired for future use cases.