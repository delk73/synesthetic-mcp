## Summary of repo state
- STDIO entrypoint runs a blocking NDJSON JSON-RPC router that logs readiness/shutdown while processing one request per line (mcp/__main__.py:205; mcp/stdio_main.py:33; tests/test_stdio.py:40)
- Discovery favors environment overrides before the `libs/synesthetic-schemas` submodule with deterministic ordering (mcp/core.py:12; mcp/core.py:50; tests/test_submodule_integration.py:28)
- Validation resolves schema aliases, sorts RFC6901 error pointers, and enforces the shared 1 MiB payload cap (mcp/validate.py:17; mcp/validate.py:106; mcp/backend.py:34)
- Backend populate stays disabled unless `SYN_BACKEND_URL` is set and propagates HTTP outcomes deterministically (mcp/backend.py:30; tests/test_backend.py:21; tests/test_backend.py:95)
- Optional HTTP health server remains reachable via `MCP_ENDPOINT` despite the spec mandating STDIO-only transport (mcp/__main__.py:55; docs/mcp_spec.md:13; README.md:41)

## Top gaps & fixes (3-5 bullets)
- Emit `<pid> <ISO8601>` in the ready file instead of `ready` to meet the spec’s contract (docs/mcp_spec.md:49; mcp/__main__.py:90; tests/test_stdio.py:68)
- Return `{ "reason": "not_found" }` for missing schemas/examples to satisfy the IO contract (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; mcp/core.py:104)
- Preserve the incoming JSON-RPC `id` when emitting errors so clients can correlate failures (docs/mcp_spec.md:41; mcp/stdio_main.py:45)
- Accept the `'all'` sentinel in `list_examples` (the code uses `*`) and align callers/docs accordingly (docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35)

## Alignment with mcp_spec.md and init_mcp_repo.json
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:33; tests/test_stdio.py:14 |
| Ready file writes `<pid> <timestamp>` | Divergent | docs/mcp_spec.md:49; mcp/__main__.py:90 |
| Transport limited to STDIO | Divergent | docs/mcp_spec.md:13; mcp/__main__.py:55; README.md:41 |
| `get_schema`/`get_example` not_found contract | Missing | docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; mcp/core.py:104 |
| `list_examples` supports `'all'` sentinel | Divergent | docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35 |
| JSON-RPC errors echo request id | Divergent | docs/mcp_spec.md:41; mcp/stdio_main.py:45 |
| Env→submodule discovery priority | Present | docs/mcp_spec.md:22; mcp/core.py:12; tests/test_env_discovery.py:7 |
| Backend gating & 1 MiB guard reuse | Present | docs/mcp_spec.md:32; docs/mcp_spec.md:165; mcp/backend.py:30; mcp/backend.py:34; tests/test_backend.py:55 |

## STDIO server entrypoint & process model
- NDJSON framing strips each stdin line, parses JSON, and emits `jsonrpc: "2.0"` envelopes (mcp/stdio_main.py:33; mcp/stdio_main.py:45)
- `_run_stdio` blocks on the router to keep the process attached to STDIO transport (mcp/__main__.py:205; tests/test_stdio.py:40)
- SIGTERM is converted to `KeyboardInterrupt` so in-flight work completes before exit (mcp/__main__.py:194; tests/test_entrypoint.py:58)
- `_write_ready_file` creates the readiness marker on startup and `_clear_ready_file` removes it on shutdown (mcp/__main__.py:85; mcp/__main__.py:222; tests/test_stdio.py:68)
- Shutdown logs after restoring signal handlers confirm graceful teardown (mcp/__main__.py:209; mcp/__main__.py:216; tests/test_entrypoint.py:55)

## Container & health
| Aspect | Present/Missing/Divergent | Evidence |
| - | - | - |
| Docker image uses python:3.11-slim, installs deps, and defaults to `python -m mcp` | Present | Dockerfile:1; Dockerfile:23 |
| `serve` service reuses ready-file healthcheck for liveness | Present | docker-compose.yml:17; docker-compose.yml:29 |
| `serve` always publishes `${MCP_PORT}` even when running STDIO-only | Divergent | docker-compose.yml:26; mcp/__main__.py:307 |
| `serve.sh` builds, waits for healthy container, then tails logs | Present | serve.sh:1; serve.sh:32 |

## Schema discovery & validation
| Source | Mechanism | Evidence |
| - | - | - |
| Env overrides | `_schemas_dir`/`_examples_dir` return environment paths before fallbacks | mcp/core.py:12; tests/test_env_discovery.py:29 |
| Submodule fallback | Discovery uses `libs/synesthetic-schemas` and sorts results deterministically | mcp/core.py:18; tests/test_submodule_integration.py:28 |
| Example schema inference | `$schemaRef`/filename heuristics map assets to canonical names | mcp/core.py:78; tests/test_backend.py:102 |
| Alias validation & size limits | `validate_asset` applies alias map, RFC6901 ordering, and 1 MiB guard | mcp/validate.py:17; mcp/validate.py:151; tests/test_validate.py:27 |
| Backend reuse of validator | Populate infers schema, revalidates by default, and enforces size limit | mcp/backend.py:41; tests/test_backend.py:95 |

## Test coverage
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO ready/shutdown & signal handling | Yes | tests/test_entrypoint.py:31 |
| STDIO validate request + ready file creation | Yes | tests/test_stdio.py:40 |
| Env overrides and submodule fallback | Yes | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:23 |
| Validation aliases & payload limit | Yes | tests/test_validate.py:14; tests/test_validate.py:37 |
| Backend success/error/size/validation guards | Yes | tests/test_backend.py:21; tests/test_backend.py:55 |
| Diff determinism | Yes | tests/test_diff.py:4 |
| HTTP entrypoint readiness | No (only optional FastAPI smoke) | tests/test_entrypoint.py:92; tests/test_http.py:4 |

## Dependencies & runtime
| Package | Used in | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate HTTP client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test suite runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | Local registry support when available | Optional | mcp/validate.py:9 |
| fastapi | Optional HTTP adapter factory | Optional | mcp/http_main.py:5 |
| uvicorn | Mentioned for local HTTP dev | Optional | README.md:79 |

## Environment variables
- `MCP_ENDPOINT` defaults to `stdio`, toggles optional HTTP/TCP endpoints, and rejects unsupported schemes or incomplete URLs (mcp/__main__.py:55; mcp/__main__.py:66; tests/test_entrypoint.py:92)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank values disable file creation while shutdown removes the marker (mcp/__main__.py:77; mcp/__main__.py:222)
- `MCP_HOST`/`MCP_PORT` only apply when HTTP is selected; invalid ports abort startup (mcp/__main__.py:43; mcp/__main__.py:312; tests/test_entrypoint.py:92)
- `SYN_SCHEMAS_DIR` overrides schema discovery and must exist or startup fails (mcp/__main__.py:30; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR` overrides example discovery with submodule fallback when unset (mcp/core.py:25; tests/test_env_discovery.py:29)
- `SYN_BACKEND_URL` gates backend populate, returning `unsupported` when missing (mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and normalises leading slashes for POSTs (mcp/backend.py:17; tests/test_backend.py:36)

## Documentation accuracy
- README advertises enabling HTTP/TCP mode even though the spec confines transport to STDIO (README.md:41; docs/mcp_spec.md:13)
- README’s environment table omits the spec-required pid/timestamp ready-file content while the implementation writes `ready` (README.md:92; docs/mcp_spec.md:49; mcp/__main__.py:90)
- README claims `docker compose up serve` runs the STDIO loop but does not mention the unconditional port publication (README.md:170; docker-compose.yml:26)
- `meta/prompts` references an audit baseline yet the original `init_mcp_repo.json` prompt is absent, leaving no recorded starting state (meta/prompts/audit_mcp_state.json:4; meta/prompts/finalize_docs.json:1; meta/prompts/implement_loop.json:1)

## Detected divergences
- Ready file contains `ready` instead of `<pid> <ISO8601 timestamp>` (docs/mcp_spec.md:49; mcp/__main__.py:90)
- Optional HTTP listener contradicts the STDIO-only transport requirement (docs/mcp_spec.md:13; mcp/__main__.py:55)
- Missing `reason: "not_found"` in schema/example misses the IO contract (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; mcp/core.py:104)
- JSON-RPC error responses drop the request id (docs/mcp_spec.md:41; mcp/stdio_main.py:45)
- `list_examples` expects `'all'` but implementation uses `*` (docs/mcp_spec.md:91; mcp/core.py:71)
- Compose publishes `${MCP_PORT}` even when serving STDIO only (docker-compose.yml:26; mcp/__main__.py:307)
- Baseline prompt `init_mcp_repo.json` referenced by automation is missing from `meta/prompts` (meta/prompts/audit_mcp_state.json:4; meta/prompts/finalize_docs.json:1; meta/prompts/implement_loop.json:1)

## Recommendations
- Write `<pid> <ISO8601>` into the ready file and adapt tests/docs to keep health checks spec-compliant (docs/mcp_spec.md:49; mcp/__main__.py:85; tests/test_stdio.py:68)
- Return `{ "reason": "not_found" }` from `get_schema`/`get_example` and add regression tests covering absent assets (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; tests/test_validate.py:14)
- Include the request `id` in JSON-RPC error payloads and exercise that path in `tests/test_stdio.py` (docs/mcp_spec.md:41; mcp/stdio_main.py:45; tests/test_stdio.py:14)
- Accept `'all'` as the list sentinel (in addition to `*` if desired) and update callers/docs to match the spec (docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35)
- Either remove the HTTP server or fence it behind an explicit non-spec flag and document the divergence while conditioning Compose port exposure (docs/mcp_spec.md:13; mcp/__main__.py:55; docker-compose.yml:26)
