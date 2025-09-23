# MCP State Audit (v0.2.4)

## Summary of repo state
The `synesthetic-mcp` repository is in a good state, with a strong alignment to the `mcp_spec.md` for its core features. The implementation correctly handles STDIO transport, payload limits, schema discovery, and validation. Test coverage is robust for the implemented features. The main gaps are the lack of Socket transport and the `validate_many` batching feature, both of which are marked as optional in the spec. A minor divergence exists in how `validate_asset` handles a missing `schema` parameter.

## Top gaps & fixes
1.  **Missing Socket Transport:** The spec defines an optional Unix Domain Socket transport, which is not implemented. This is acceptable as it's not a required feature.
2.  **Missing `validate_many`:** The optional batch validation method `validate_many` is not implemented.
3.  **Divergent `validate_asset` schema handling:** `validate_asset` in `mcp/stdio_main.py` passes an empty string to `validate_asset` if the `schema` parameter is missing, while the spec requires it. This should be fixed to return a `validation_failed` error.
4.  **Missing `get_example` error reason:** The spec doesn't account for a `validation_failed` reason in the `get_example` method, which can occur. The spec should be updated.

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
|---|---|---|
| STDIO JSON-RPC 2.0 Transport | Present | `mcp/stdio_main.py`, `mcp/__main__.py` |
| Socket (UDS) JSON-RPC 2.0 Transport | Missing | No implementation found. |
| 1 MiB Payload Cap (STDIO) | Present | `mcp/stdio_main.py:45`, `tests/test_stdio.py:171` |
| `validate_asset`: `schema` is REQUIRED | Divergent | `mcp/stdio_main.py:25` passes `""` if missing. `tests/test_validate.py:63` confirms this. |
| `validate` alias for `validate_asset` | Present | `mcp/stdio_main.py:24` |
| `validate_many` (Optional) | Missing | No implementation found. |
| Local-only `$ref` resolution | Present | `mcp/validate.py` uses a local registry. |
| Deterministic sorting (lists, errors, diffs) | Present | `mcp/core.py`, `mcp/validate.py`, `mcp/diff.py`, `tests/test_submodule_integration.py:34` |
| STDIO Readiness File (`MCP_READY_FILE`) | Present | `mcp/__main__.py:53`, `tests/test_stdio.py:62` |
| SIGINT/SIGTERM handling | Present | `mcp/__main__.py:78` |

## Transports
- **STDIO:** Present and correctly implemented as the default and only transport.
- **Socket:** Missing. The spec marks this as optional.
- **HTTP/gRPC:** Missing, as expected (roadmap only).

## STDIO server entrypoint & process model
- **NDJSON framing:** Present, handled in `mcp/stdio_main.py`.
- **Blocking loop:** Present, `sys.stdin` is iterated in `mcp/stdio_main.py`.
- **Signals:** `SIGTERM` is handled to allow graceful shutdown. `SIGINT` is caught as `KeyboardInterrupt`.
- **Readiness file:** `MCP_READY_FILE` is written on startup and removed on shutdown.
- **Shutdown semantics:** The server exits when `stdin` closes or on `SIGINT`/`SIGTERM`.
- **stdout vs stderr:** `stdout` is used for JSON-RPC frames, `stderr` for logging.

## Socket server (if present)
Not implemented.

## Golden request/response examples
| Method | Success frame Present/Missing/Divergent | Error frame Present/Missing/Divergent | Evidence |
|---|---|---|---|
| `list_schemas` | Present | N/A | `tests/fixtures/e2e_golden.jsonl` |
| `get_schema` | Present | Present | `tests/test_validate.py:12` (not found) |
| `validate_asset` | Present | Present | `tests/test_validate.py:25`, `tests/test_validate.py:37` |
| `validate` (alias) | Present | Present | `mcp/stdio_main.py:24` |
| `diff_assets` | Present | N/A | `tests/test_diff.py` |
| Malformed frame | N/A | Present | `mcp/stdio_main.py:63` |

## Payload size guard
| Method | STDIO guard | Socket guard | Evidence |
|---|---|---|---|
| All | Present | N/A | `mcp/stdio_main.py:45`, `tests/test_stdio.py:171` |
| `validate_asset` | Present | N/A | `mcp/validate.py:107`, `tests/test_validate.py:47` |
| `populate_backend` | Present | N/A | `mcp/backend.py:38`, `tests/test_backend.py:55` |

## Schema validation contract
- **Required `schema` param:** Divergent. `mcp/stdio_main.py` sends an empty string if the param is missing, which `validate_asset` then rejects. The rejection is correct, but the spec implies the check should be earlier.
- **Alias handling:** Present. `validate` is an alias for `validate_asset`.
- **Error ordering:** Present. Validation errors are sorted by path and message.
- **`validate_asset` behavior:** Present and correct, aside from the schema param issue.

## Optional batching (if present)
Not implemented.

## Logging hygiene
- **`stdout` frames only:** Present.
- **`stderr` logs/diagnostics:** Present.
- **Deterministic timestamps:** Present, ISO-8601 format is used in the ready file.

## Container & health
| Aspect | Present/Missing/Divergent | Evidence |
|---|---|---|
| `docker-compose` services | Present | `docker-compose.yml` |
| Healthcheck | Present | `docker-compose.yml` checks for `MCP_READY_FILE`. |
| Environment variables | Present | `docker-compose.yml` passes through environment variables. |

## Schema discovery & validation
| Source | Mechanism | Evidence |
|---|---|---|
| Environment variables | `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` | `mcp/core.py`, `tests/test_env_discovery.py` |
| Submodule | `libs/synesthetic-schemas` | `mcp/core.py`, `tests/test_submodule_integration.py` |
| `$ref` resolution | Local-only via `referencing` library | `mcp/validate.py` |

## Test coverage
| Feature | Tested? | Evidence |
|---|---|---|
| STDIO transport | Yes | `tests/test_stdio.py` |
| `validate_asset` | Yes | `tests/test_validate.py` |
| `diff_assets` | Yes | `tests/test_diff.py` |
| `populate_backend` | Yes | `tests/test_backend.py` |
| Schema/example discovery | Yes | `tests/test_env_discovery.py`, `tests/test_submodule_integration.py` |
| CLI entrypoint | Yes | `tests/test_entrypoint.py` |
| Payload size limits | Yes | `tests/test_stdio.py`, `tests/test_validate.py`, `tests/test_backend.py` |

## Dependencies & runtime
| Package | Used in | Required/Optional |
|---|---|---|
| `jsonschema` | `mcp/validate.py` | Required |
| `httpx` | `mcp/backend.py` | Required (for backend) |
| `pytest` | `tests/` | Required (for tests) |
| `referencing` | `mcp/validate.py` | Optional |

## Environment variables
- `MCP_ENDPOINT`: Honored, but only `stdio` is supported.
- `MCP_READY_FILE`: Honored.
- `MCP_SOCKET_PATH`: Not used (no socket transport).
- `MCP_SOCKET_MODE`: Not used.
- `MCP_MAX_BATCH`: Not used.
- `SYN_SCHEMAS_DIR`: Honored.
- `SYN_EXAMPLES_DIR`: Honored.
- `SYN_BACKEND_URL`: Honored.
- `SYN_BACKEND_ASSETS_PATH`: Honored.

## Documentation accuracy
- `README.md` is accurate and consistent with `docs/mcp_spec.md` regarding the implemented features.
- Both documents correctly describe the STDIO transport, payload limits, and schema discovery.

## Detected divergences
- `validate_asset`'s `schema` parameter is not strictly required at the JSON-RPC method level, but is required by the validation logic itself. This is a minor divergence from the spec's intent.

## Recommendations
1.  **Fix `validate_asset` schema handling:** Modify `mcp/stdio_main.py` to check for the `schema` parameter in `validate_asset` and `validate` calls and return a proper JSON-RPC error if it's missing.
2.  **Update spec for `get_example`:** Add `validation_failed` to the possible error reasons for `get_example` in `docs/mcp_spec.md`.
3.  **Implement optional features:** If desired, implement the `socket` transport and the `validate_many` method.
