# AGENTS.md — Repo Snapshot

## Repo Summary
- STDIO entrypoint runs a blocking NDJSON JSON-RPC loop that logs readiness/shutdown (mcp/stdio_main.py:33; mcp/__main__.py:205; tests/test_stdio.py:40)
- Discovery prefers env overrides before the `libs/synesthetic-schemas` submodule with deterministic ordering (mcp/core.py:12; mcp/core.py:50; tests/test_submodule_integration.py:28)
- Validation maps aliases, sorts RFC6901 error pointers, and enforces the shared 1 MiB limit reused by backend populate (mcp/validate.py:17; mcp/validate.py:151; mcp/backend.py:34)
- Backend populate stays gated by `SYN_BACKEND_URL`, re-validates payloads by default, and propagates HTTP outcomes deterministically (mcp/backend.py:30; mcp/backend.py:41; tests/test_backend.py:95)
- Optional HTTP health server is still exposed behind `MCP_ENDPOINT`, keeping Compose health checks usable but diverging from the STDIO-only spec (mcp/__main__.py:55; docker-compose.yml:29)

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:9 |
| fastapi | HTTP adapter factory | Optional | mcp/http_main.py:5 |
| uvicorn | HTTP runtime (docs only) | Optional | README.md:79 |

## Environment Variables
- `MCP_ENDPOINT` defaults to `stdio`, enables optional HTTP/TCP endpoints, and rejects unsupported schemes (mcp/__main__.py:55; mcp/__main__.py:66)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables file creation though shutdown clears it when present (mcp/__main__.py:77; mcp/__main__.py:222)
- `MCP_HOST`/`MCP_PORT` apply only with HTTP and invalid ports abort startup (mcp/__main__.py:43; tests/test_entrypoint.py:92)
- `SYN_SCHEMAS_DIR`/`SYN_EXAMPLES_DIR` override discovery roots ahead of the submodule (mcp/core.py:12; mcp/core.py:25; tests/test_env_discovery.py:29)
- `SYN_BACKEND_URL` unlocks populate while unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and is normalised to keep a leading slash (mcp/backend.py:17; tests/test_backend.py:36)

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO ready/shutdown & signal handling | ✅ | tests/test_entrypoint.py:31 |
| STDIO JSON-RPC loop & ready file creation | ✅ | tests/test_stdio.py:40 |
| Env overrides & submodule fallback | ✅ | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:23 |
| Validation aliases / sorted errors / 1 MiB limit | ✅ | tests/test_validate.py:14; tests/test_validate.py:37 |
| Backend success/error/size/validation guards | ✅ | tests/test_backend.py:21; tests/test_backend.py:55 |
| Diff determinism | ✅ | tests/test_diff.py:4 |
| HTTP entrypoint readiness | ❌ (only optional FastAPI smoke) | tests/test_entrypoint.py:92; tests/test_http.py:4 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:33 |
| Ready file must contain `<pid> <timestamp>` | Divergent | docs/mcp_spec.md:49; mcp/__main__.py:90 |
| Transport limited to STDIO | Divergent | docs/mcp_spec.md:13; mcp/__main__.py:55 |
| `get_schema`/`get_example` return `reason: not_found` | Missing | docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57 |
| `list_examples` accepts `'all'` sentinel | Divergent | docs/mcp_spec.md:91; mcp/core.py:71 |
| JSON-RPC errors echo request id | Divergent | docs/mcp_spec.md:41; mcp/stdio_main.py:45 |

## Divergences
- Ready file writes `ready` instead of `<pid> <ISO8601 timestamp>` (docs/mcp_spec.md:49; mcp/__main__.py:90)
- Optional HTTP server remains exposed despite STDIO-only requirement (docs/mcp_spec.md:13; mcp/__main__.py:55)
- `get_schema`/`get_example` omit `reason: "not_found"` on misses (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57)
- JSON-RPC error responses drop the request id (docs/mcp_spec.md:41; mcp/stdio_main.py:45)
- `list_examples` uses `*` sentinel instead of `'all'` (docs/mcp_spec.md:91; mcp/core.py:71)
- Compose publishes `${MCP_PORT}` even when running STDIO-only (docker-compose.yml:26; mcp/__main__.py:307)
- Baseline prompt `init_mcp_repo.json` referenced by tooling is missing from `meta/prompts` (meta/prompts/audit_mcp_state.json:4; meta/prompts/finalize_docs.json:1)

## Recommendations
- Emit `<pid> <ISO8601>` in the ready file and update tests/docs accordingly (docs/mcp_spec.md:49; mcp/__main__.py:85)
- Return `{ "reason": "not_found" }` from schema/example lookups plus regression tests (docs/mcp_spec.md:87; mcp/core.py:57; tests/test_validate.py:14)
- Echo the request `id` in JSON-RPC error payloads and cover it in `tests/test_stdio.py` (docs/mcp_spec.md:41; mcp/stdio_main.py:45; tests/test_stdio.py:14)
- Align `list_examples` with the `'all'` sentinel (docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35)
- Tightly scope or explicitly document the HTTP server and condition Compose port exposures (docs/mcp_spec.md:13; mcp/__main__.py:55; docker-compose.yml:26)

## Baseline Commit
- 95863497ed75482c9c967f105ea2bfb11c8ac024
