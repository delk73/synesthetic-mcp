# AGENTS.md — Repo Snapshot

## Repo Summary
- **STDIO Transport:** The implementation provides a compliant STDIO JSON-RPC 2.0 transport with NDJSON framing, a 1 MiB payload guard, and correct separation of stdout (frames) and stderr (logs).
- **Validation:** The `validate_asset` method (and its `validate` alias) correctly performs schema validation against local schemas. The `schema` parameter is now correctly enforced as required.
- **Schema Discovery:** Schema and example discovery from environment variables and the `libs/synesthetic-schemas` submodule is correctly implemented and tested.
- **Backend Population:** The `populate_backend` tool is implemented correctly, respecting the `SYN_BACKEND_URL` environment variable to enable/disable the feature.
- **Test Coverage:** The repository has good test coverage for all implemented features, including transport, validation, backend interaction, and discovery.
- **Missing Features:** The optional `socket` transport and `validate_many` batch validation are not implemented.
- **Divergences:** `get_example` does not return a `validation_failed` error for invalid examples.

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt`, `mcp/validate.py` |
| httpx | Backend populate client | Required (backend) | `requirements.txt`, `mcp/backend.py` |
| pytest | Test runner | Required (tests) | `requirements.txt`, `tests/` |
| referencing | JSON Schema registry support | Optional | `mcp/validate.py` |

## Environment Variables
- `MCP_ENDPOINT`: Only `stdio` is supported, as per the spec's requirement for the initial implementation.
- `MCP_READY_FILE`: Correctly used to signal readiness.
- `SYN_SCHEMAS_DIR` & `SYN_EXAMPLES_DIR`: Used to override default schema and example paths.
- `SYN_BACKEND_URL`: Gates the `populate_backend` feature.
- `SYN_BACKEND_ASSETS_PATH`: Correctly overrides the backend POST path.

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, ready file, oversize guard | ✅ | `tests/test_stdio.py` |
| Transport setup & shutdown handling | ✅ | `tests/test_entrypoint.py` |
| Validation aliasing, ordering, payload cap | ✅ | `tests/test_validate.py` |
| Backend success/error/size handling | ✅ | `tests/test_backend.py` |
| Env overrides & submodule fallback | ✅ | `tests/test_env_discovery.py`, `tests/test_submodule_integration.py` |
| Diff determinism | ✅ | `tests/test_diff.py` |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | `mcp/stdio_main.py` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py`, `tests/test_stdio.py` |
| 1 MiB per-request STDIO limit | Present | `mcp/stdio_main.py`, `tests/test_stdio.py` |
| `validate_asset` requires `schema` | Present | `mcp/stdio_main.py:25` |
| Socket Transport | Missing | Not implemented (optional feature). |
| `validate_many` | Missing | Not implemented (optional feature). |
| `get_example` validation failure | Divergent | `mcp/core.py:115` |

## Recommendations
- **Fix `get_example` Divergence:** Modify `mcp.core` to return a `validation_failed` error if an example on disk is invalid.
- **Consider Optional Features:** Plan for the implementation of the `socket` transport and `validate_many` if they are desired for future use cases.
