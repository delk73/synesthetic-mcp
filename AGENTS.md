# AGENTS.md — Repo Snapshot

## Repo Summary
- STDIO JSON-RPC loop is deterministic, echoes ids, and keeps stdout frames separate from stderr logging (docs/mcp_spec.md:38; docs/mcp_spec.md:44; mcp/stdio_main.py:33; mcp/stdio_main.py:53; tests/test_stdio.py:15; tests/test_entrypoint.py:55)
- Entrypoint enforces STDIO-only transport, manages `<pid> <ISO8601>` ready files, and restores signal handlers on shutdown (docs/mcp_spec.md:49; docs/mcp_spec.md:215; mcp/__main__.py:35; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_stdio.py:70)
- Discovery honours env overrides before the submodule and sorts schemas/examples for determinism (docs/mcp_spec.md:117; mcp/core.py:12; mcp/core.py:50; tests/test_env_discovery.py:7; tests/test_submodule_integration.py:32)
- Validation aliasing, `$schemaRef` stripping, payload cap, and RFC6901 ordering flow into backend populate (docs/mcp_spec.md:121; docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:106; tests/test_validate.py:37; tests/test_backend.py:41)
- Divergences remain: no 1 MiB STDIO guard, `unsupported` payloads use `msg`, schema paths end with `.schema.json`, and FastAPI HTTP surface stays enabled (docs/mcp_spec.md:67; docs/mcp_spec.md:108; docs/mcp_spec.md:192; mcp/stdio_main.py:30; mcp/core.py:47; mcp/http_main.py:6; tests/test_http.py:4)

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:9 |
| fastapi | HTTP adapter factory | Optional | mcp/http_main.py:6 |
| uvicorn | HTTP runtime (docs only) | Optional | README.md:81 |

## Environment Variables
- `MCP_ENDPOINT` defaults to STDIO; other values abort startup (docs/mcp_spec.md:36; mcp/__main__.py:35; tests/test_entrypoint.py:92)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables creation and shutdown removes it (docs/mcp_spec.md:175; mcp/__main__.py:45; mcp/__main__.py:105)
- `SYN_SCHEMAS_DIR` must exist or startup fails (docs/mcp_spec.md:176; mcp/__main__.py:22; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR` overrides example discovery with deterministic listings (docs/mcp_spec.md:177; mcp/core.py:25; tests/test_env_discovery.py:7)
- `SYN_BACKEND_URL` gates backend populate; unset returns `reason: "unsupported"` (docs/mcp_spec.md:178; mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and forces a leading slash (docs/mcp_spec.md:179; mcp/backend.py:17; tests/test_backend.py:36)

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO ready/shutdown & signal handling | ✅ | tests/test_entrypoint.py:31 |
| STDIO JSON-RPC loop & ready file contents | ✅ | tests/test_stdio.py:41 |
| JSON-RPC error id echo | ✅ | tests/test_stdio.py:124 |
| Env overrides & submodule fallback | ✅ | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:23 |
| Validation aliasing / sorted errors / payload cap | ✅ | tests/test_validate.py:22; tests/test_validate.py:37; tests/test_validate.py:47 |
| Backend success/error/size/validation guards | ✅ | tests/test_backend.py:21; tests/test_backend.py:55 |
| Diff determinism | ✅ | tests/test_diff.py:4 |
| STDIO oversized-request guard | ❌ (missing feature/test) | docs/mcp_spec.md:192; mcp/stdio_main.py:33 |
| HTTP adapter smoke | ⚠️ (non-spec surface) | tests/test_http.py:4 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:33; tests/test_stdio.py:15 |
| Ready file contains `<pid> <ISO8601>` and clears on shutdown | Present | docs/mcp_spec.md:49; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_stdio.py:70 |
| Spec errors stay inside `result` | Present | docs/mcp_spec.md:84; mcp/stdio_main.py:45; tests/test_stdio.py:109 |
| 1 MiB per-request limit at STDIO transport | Missing | docs/mcp_spec.md:192; mcp/stdio_main.py:33 |
| `unsupported` responses use `detail` | Divergent | docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32 |
| Schema listing path matches spec sample | Divergent | docs/mcp_spec.md:67; mcp/core.py:47 |
| Transport limited to STDIO | Divergent | docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4 |

## Golden Example
| Aspect | Status | Evidence |
| - | - | - |
| Success frame mirrors spec sample (`jsonrpc`, `id`, `result`) | Present | docs/mcp_spec.md:60; mcp/stdio_main.py:45; tests/test_stdio.py:32 |
| Error frame echoes request `id` | Present | docs/mcp_spec.md:41; mcp/stdio_main.py:47; tests/test_stdio.py:140 |
| Schema listing path matches spec sample | Divergent | docs/mcp_spec.md:67; mcp/core.py:47 |

## Payload Guard
| Case | Status | Evidence |
| - | - | - |
| STDIO request size check (1 MiB) | Missing | docs/mcp_spec.md:192; mcp/stdio_main.py:33 |
| Validation payload cap | Present | mcp/validate.py:106; tests/test_validate.py:47 |
| Backend payload cap | Present | mcp/backend.py:34; tests/test_backend.py:55 |

## Divergences
- STDIO loop lacks the 1 MiB pre-parse guard mandated by the spec (docs/mcp_spec.md:192; mcp/stdio_main.py:33)
- `reason: "unsupported"` payloads expose `msg` instead of `detail` (docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_backend.py:21)
- `list_schemas` returns `.schema.json` filenames rather than the spec’s sample path format (docs/mcp_spec.md:67; mcp/core.py:47)
- Optional FastAPI adapter leaves a non-compliant HTTP transport available (docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4)

## Recommendations
- Add a pre-parse 1 MiB guard to the STDIO loop and cover it with an oversized-request test (docs/mcp_spec.md:192; mcp/stdio_main.py:33; tests/test_stdio.py:15)
- Switch `unsupported` payloads to the `detail` field and update associated tests/assertions (docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_backend.py:21)
- Either match the spec’s schema path format or document/test the `.schema.json` suffix (docs/mcp_spec.md:67; mcp/core.py:47; tests/test_submodule_integration.py:32)
- Remove or fence the FastAPI adapter and HTTP smoke test to keep the deployment STDIO-only (docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4; README.md:81)
