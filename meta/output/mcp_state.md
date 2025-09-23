# MCP State Audit (v0.2.4)

## Summary of repo state

The `synesthetic-mcp` repository is in a good state, with a solid implementation of the core features specified in `docs/mcp_spec.md`. The STDIO transport is fully compliant, validation logic is robust, and schema/example discovery is working as expected. Test coverage is good for the implemented features. The main gaps are the optional `socket` transport and `validate_many` batching, which are not implemented. There is a minor divergence in `get_example` which does not return a `validation_failed` error for invalid examples.

## Top gaps & fixes (3-5 bullets)

*   **Missing:** The `socket` transport is not implemented. This is an optional feature.
*   **Missing:** The `validate_many` batch validation method is not implemented. This is an optional feature.
*   **Divergent:** The `get_example` method does not return a `validation_failed` error when the example is invalid. It currently returns `"validated": false`.
*   **Fix:** Modify `mcp/core.py` to return a `validation_failed` error from `get_example` if the example is invalid.

## Alignment with mcp_spec.md

| Spec item | Status | Evidence |
| --- | --- | --- |
| STDIO NDJSON framing & sequential handling | Present | `mcp/stdio_main.py` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py`, `tests/test_stdio.py` |
| 1 MiB per-request STDIO limit | Present | `mcp/stdio_main.py`, `tests/test_stdio.py` |
| `validate_asset` requires `schema` | Present | `mcp/stdio_main.py:25` |
| Socket Transport | Missing | Not implemented (optional feature). |
| `validate_many` | Missing | Not implemented (optional feature). |
| `get_example` validation failure | Divergent | `mcp/core.py:115` |

## Transports

### STDIO server entrypoint & process model

*   **NDJSON framing:** Present and correct. The server processes one JSON object per line from stdin.
*   **Blocking loop:** Present. The server uses a blocking loop to read from stdin.
*   **Signals:** Present. The server handles SIGINT/SIGTERM gracefully, finishing in-flight requests before exiting.
*   **Readiness file:** Present. The server writes a ready file to `MCP_READY_FILE` on startup and removes it on shutdown.
*   **Shutdown semantics:** Present. The server exits when stdin is closed.
*   **stdout vs stderr:** Present. stdout is used for JSON-RPC frames only, and stderr is used for logs.

### Socket server

*   **Missing:** The socket server is not implemented.

## Golden request/response examples

| Method | Success frame | Error frame | Evidence |
| --- | --- | --- | --- |
| `list_schemas` | Present | N/A | `tests/test_submodule_integration.py` |
| `get_schema` | Present | Present | `tests/test_validate.py` |
| `validate_asset` | Present | Present | `tests/test_validate.py` |
| `validate` (alias) | Present | N/A | `mcp/stdio_main.py` |
| `get_example` | Present | Divergent | `mcp/core.py:115` |
| `diff_assets` | Present | N/A | `tests/test_diff.py` |
| Malformed frame | Present | N/A | `tests/test_stdio.py` |

## Payload size guard

| Method | STDIO guard | Socket guard | Evidence |
| --- | --- | --- | --- |
| All | Present | Missing | `mcp/stdio_main.py`, `tests/test_stdio.py` |

## Schema validation contract

*   **Required `schema` param:** Present and enforced.
*   **Alias handling:** Present. `validate` is an alias for `validate_asset`.
*   **Error ordering:** Present. Validation errors are sorted by `path` and `msg`.
*   **`validate_asset` behavior:** Present and correct.

## Optional batching

*   **Missing:** `validate_many` is not implemented.

## Logging hygiene

*   **stdout frames only:** Present.
*   **stderr logs/diagnostics:** Present.
*   **Deterministic timestamps:** Present. Logs use ISO-8601 UTC timestamps.

## Container & health

| Aspect | Present/Missing/Divergent | Evidence |
| --- | --- | --- |
| `mcp-stdio` service | Present | `docker-compose.yml` |
| `mcp-socket` service | Missing | `docker-compose.yml` |
| `healthcheck` | Present | `docker-compose.yml` |
| Environment variables | Present | `docker-compose.yml` |
| Non-root user | Present | `Dockerfile` |

## Schema discovery & validation

| Source | Mechanism | Evidence |
| --- | --- | --- |
| Environment variables | `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` | `mcp/core.py`, `tests/test_env_discovery.py` |
| Submodule | `libs/synesthetic-schemas` | `mcp/core.py`, `tests/test_submodule_integration.py` |
| `$ref` resolution | Local-only | `mcp/validate.py` |

## Test coverage

| Feature | Tested? | Evidence |
| --- | --- | --- |
| STDIO transport | Yes | `tests/test_stdio.py` |
| Validation | Yes | `tests/test_validate.py` |
| Backend population | Yes | `tests/test_backend.py` |
| Diffing | Yes | `tests/test_diff.py` |
| Entrypoint | Yes | `tests/test_entrypoint.py` |
| Env discovery | Yes | `tests/test_env_discovery.py` |
| Submodule integration | Yes | `tests/test_submodule_integration.py` |

## Dependencies & runtime

| Package | Used in | Required/Optional |
| --- | --- | --- |
| `jsonschema` | `mcp/validate.py` | Required |
| `httpx` | `mcp/backend.py` | Required |
| `pytest` | `tests/` | Required (tests) |
| `referencing` | `mcp/validate.py` | Optional |

## Environment variables

*   `MCP_ENDPOINT`: `stdio` (default). Only `stdio` is supported.
*   `MCP_READY_FILE`: `/tmp/mcp.ready` (default).
*   `MCP_SOCKET_PATH`: `/tmp/mcp.sock` (default). Not used.
*   `MCP_SOCKET_MODE`: `0600` (default). Not used.
*   `MCP_MAX_BATCH`: `100` (default). Not used.
*   `SYN_SCHEMAS_DIR`: Overrides schema directory.
*   `SYN_EXAMPLES_DIR`: Overrides examples directory.
*   `SYN_BACKEND_URL`: Enables backend population.
*   `SYN_BACKEND_ASSETS_PATH`: Overrides backend POST path.

## Documentation accuracy

*   The `README.md` is minimal. The `docs/mcp_spec.md` is the primary source of truth and is mostly accurate, with the exception of the `get_example` divergence.

## Detected divergences

*   `get_example` returns `"validated": false` for invalid examples instead of a `validation_failed` error.

## Recommendations

*   **Fix `get_example` Divergence:** Modify `mcp/core.py` to return a `validation_failed` error if an example on disk is invalid.
*   **Consider Optional Features:** Plan for the implementation of the `socket` transport and `validate_many` if they are desired for future use cases.