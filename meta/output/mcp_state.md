## Summary of repo state
- STDIO entrypoint runs a blocking NDJSON JSON-RPC loop that logs readiness/shutdown while processing one request per line (mcp/stdio_main.py:33; mcp/__main__.py:205; tests/test_stdio.py:14)
- Discovery prefers env overrides before the `libs/synesthetic-schemas` submodule with deterministic ordering (mcp/core.py:12; mcp/core.py:42; tests/test_submodule_integration.py:28)
- Validation maps aliases, sorts RFC6901 error pointers, and enforces the shared 1 MiB limit reused by backend populate (mcp/validate.py:17; mcp/validate.py:106; mcp/backend.py:34)
- Backend populate stays gated by `SYN_BACKEND_URL`, re-validates payloads by default, and propagates HTTP outcomes deterministically (mcp/backend.py:30; mcp/backend.py:41; tests/test_backend.py:95)
- Optional HTTP health server remains exposed via `MCP_ENDPOINT`, keeping Compose health checks but diverging from the STDIO-only spec (mcp/__main__.py:55; docker-compose.yml:26; README.md:41)

## Top gaps & fixes (3-5 bullets)
- Emit `<pid> <ISO8601>` in the ready file and update tests/docs to match the spec (docs/mcp_spec.md:49; mcp/__main__.py:90; tests/test_stdio.py:68)
- Return `{ "reason": "not_found" }` for missing schemas/examples with regression coverage (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; mcp/core.py:104)
- Echo the JSON-RPC request `id` on error frames and exercise the path in the STDIO tests (docs/mcp_spec.md:41; mcp/stdio_main.py:47; tests/test_stdio.py:14)
- Accept the `'all'` sentinel for `list_examples` and align callers/docs (docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35)
- Document or remove the optional HTTP listener and avoid publishing ports when serving STDIO-only (docs/mcp_spec.md:13; mcp/__main__.py:55; docker-compose.yml:27)

## Alignment with mcp_spec.md and init_mcp_repo.json (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing, sequential handling, and `jsonrpc: "2.0"` envelopes | Present | docs/mcp_spec.md:36; mcp/stdio_main.py:33; tests/test_stdio.py:32 |
| Ready file writes `<pid> <ISO8601 timestamp>` | Divergent | docs/mcp_spec.md:49; mcp/__main__.py:90 |
| Transport limited to STDIO (no HTTP/TCP listeners) | Divergent | docs/mcp_spec.md:13; mcp/__main__.py:55; tests/test_http.py:4 |
| `get_schema` / `get_example` return `{ "reason": "not_found" }` on misses | Missing | docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; mcp/core.py:104 |
| `list_examples` accepts the `'all'` sentinel | Divergent | docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35 |
| JSON-RPC errors echo the request `id` | Divergent | docs/mcp_spec.md:41; mcp/stdio_main.py:47 |
| `init_mcp_repo.json` baseline prompt retained in `meta/prompts/` | Missing | meta/prompts/implement_loop.json:12; meta/prompts (no init_mcp_repo.json) |

## STDIO server entrypoint & process model (bullets: NDJSON framing, blocking loop, signals, readiness file, shutdown semantics)
- NDJSON framing strips newline-delimited stdin, parses JSON, and emits `jsonrpc: "2.0"` responses (mcp/stdio_main.py:33; tests/test_stdio.py:32)
- `_run_stdio` invokes the loop synchronously to keep the process bound to STDIO transport (mcp/__main__.py:205; tests/test_stdio.py:95)
- SIGTERM is converted to `KeyboardInterrupt` so in-flight work completes before exit (mcp/__main__.py:194; tests/test_entrypoint.py:58)
- `_write_ready_file` touches the readiness marker with `ready` and `_clear_ready_file` removes it on shutdown (mcp/__main__.py:85; mcp/__main__.py:222; tests/test_stdio.py:68)
- Shutdown logs after restoring signal handlers confirm graceful teardown (mcp/__main__.py:215; tests/test_entrypoint.py:55)

## Golden request/response example (table: Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Present/Missing/Divergent | Evidence |
| - | - | - |
| Success frame echoes `jsonrpc` and request `id` while wrapping tool result | Present | docs/mcp_spec.md:60; mcp/stdio_main.py:45; tests/test_stdio.py:32 |
| Response `schemas[].path` matches spec sample without `.schema` suffix | Divergent | docs/mcp_spec.md:67; mcp/core.py:42; libs/synesthetic-schemas/jsonschema/synesthetic-asset.schema.json |
| Error frame echoes request `id` alongside `error` content | Divergent | docs/mcp_spec.md:41; mcp/stdio_main.py:47 |

## Container & health (table: Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Present/Missing/Divergent | Evidence |
| - | - | - |
| Docker image installs deps then defaults to `python -m mcp` | Present | Dockerfile:16; Dockerfile:23 |
| Compose service reuses ready-file healthcheck for STDIO loop | Present | docker-compose.yml:21; docker-compose.yml:29 |
| Compose always publishes `${MCP_PORT}` even for STDIO-only mode | Divergent | docker-compose.yml:26; mcp/__main__.py:55 |
| `serve.sh` builds, waits for health, then tails logs | Present | serve.sh:19; serve.sh:45 |

## Schema discovery & validation (table: Source → Mechanism → Evidence)
| Source | Mechanism | Evidence |
| - | - | - |
| Environment overrides | `_schemas_dir`/`_examples_dir` favor `SYN_*` directories before fallbacks | mcp/core.py:12; tests/test_env_discovery.py:29 |
| Submodule fallback | Discovery uses `libs/synesthetic-schemas` with deterministic sort order | mcp/core.py:18; tests/test_submodule_integration.py:28 |
| Example schema inference | `$schemaRef`/filename heuristics map assets to canonical names | mcp/core.py:83; tests/test_backend.py:102 |
| Alias validation & RFC6901 sorting | `validate_asset` maps aliases, enforces 1 MiB, sorts pointers | mcp/validate.py:17; mcp/validate.py:151; tests/test_validate.py:27 |
| Backend reuse of validator | Populate infers schema, re-validates by default, enforces size limit | mcp/backend.py:41; tests/test_backend.py:95 |

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO ready/shutdown & signal handling | Yes | tests/test_entrypoint.py:31 |
| STDIO JSON-RPC loop & ready file creation | Yes | tests/test_stdio.py:68 |
| Env overrides & submodule fallback | Yes | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:23 |
| Validation aliases, sorted errors, 1 MiB limit | Yes | tests/test_validate.py:14; tests/test_validate.py:37 |
| Backend success/error/size/validation guards | Yes | tests/test_backend.py:21; tests/test_backend.py:55 |
| Diff determinism | Yes | tests/test_diff.py:4 |
| HTTP entrypoint readiness/behavior | No (FastAPI smoke only) | tests/test_entrypoint.py:92; tests/test_http.py:4 |

## Dependencies & runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | Local schema registry support | Optional | mcp/validate.py:9 |
| fastapi | Optional HTTP adapter factory | Optional | mcp/http_main.py:5 |
| uvicorn | Optional HTTP runtime mentioned in docs | Optional | README.md:79 |

## Environment variables (bullets: name, default, behavior when missing/invalid)
- `MCP_ENDPOINT`: defaults to `stdio`; other values enable HTTP/TCP endpoints or URLs and unsupported schemes abort startup (mcp/__main__.py:55; mcp/__main__.py:66)
- `MCP_READY_FILE`: defaults to `/tmp/mcp.ready`; blank disables file creation while shutdown removes it when present (mcp/__main__.py:77; mcp/__main__.py:222)
- `MCP_HOST` / `MCP_PORT`: only honored when HTTP is selected; invalid ports raise setup failures (mcp/__main__.py:43; tests/test_entrypoint.py:92)
- `SYN_SCHEMAS_DIR`: overrides schema discovery and must exist or startup exits with setup error (mcp/__main__.py:30; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR`: overrides example discovery; falls back to submodule when unset (mcp/core.py:25; tests/test_env_discovery.py:29)
- `SYN_BACKEND_URL`: enables populate; missing returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH`: defaults to `/synesthetic-assets/` and ensures a leading slash for POSTs (mcp/backend.py:17; tests/test_backend.py:36)

## Documentation accuracy (bullets: README vs. docs/mcp_spec.md)
- README advertises enabling HTTP/TCP mode despite the spec mandating STDIO-only transport (README.md:41; docs/mcp_spec.md:13)
- README’s environment table omits the spec-required `<pid> <timestamp>` ready-file content while implementation writes `ready` (README.md:92; docs/mcp_spec.md:49; mcp/__main__.py:90)
- README claims Compose run exposes ready file but not the unconditional port binding in `docker-compose.yml` (README.md:170; docker-compose.yml:26)
- `meta/prompts` reference `init_mcp_repo.json` but the prompt file is absent, leaving no recorded baseline (meta/prompts/audit_mcp_state.json:3; meta/prompts directory listing)

## Detected divergences
- Ready file contains `ready` instead of `<pid> <ISO8601 timestamp>` (docs/mcp_spec.md:49; mcp/__main__.py:90)
- Optional HTTP listener contradicts the STDIO-only transport requirement (docs/mcp_spec.md:13; mcp/__main__.py:55)
- Missing `reason: "not_found"` in schema/example miss responses (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; mcp/core.py:104)
- JSON-RPC error responses drop the request `id` (docs/mcp_spec.md:41; mcp/stdio_main.py:47)
- `list_examples` expects `'all'` but implementation uses `*` (docs/mcp_spec.md:91; mcp/core.py:71)
- Compose publishes `${MCP_PORT}` even when serving STDIO-only (docker-compose.yml:26; mcp/__main__.py:55)
- Baseline prompt `init_mcp_repo.json` referenced by tooling is missing (meta/prompts/implement_loop.json:12; meta/prompts directory listing)

## Recommendations
- Write `<pid> <ISO8601>` into the ready file and adjust readiness tests/docs accordingly (docs/mcp_spec.md:49; mcp/__main__.py:85; tests/test_stdio.py:68)
- Return `{ "reason": "not_found" }` from `get_schema`/`get_example` plus regression tests for missing resources (docs/mcp_spec.md:87; docs/mcp_spec.md:95; mcp/core.py:57; tests/test_validate.py:14)
- Include the request `id` in JSON-RPC error payloads and assert it in the STDIO loop tests (docs/mcp_spec.md:41; mcp/stdio_main.py:47; tests/test_stdio.py:14)
- Support the `'all'` sentinel for `list_examples`, update callers/docs, and keep deterministic ordering (docs/mcp_spec.md:91; mcp/core.py:71; tests/test_submodule_integration.py:35)
- Remove or clearly fence the HTTP listener and condition Compose port exposure to STDIO-only runs (docs/mcp_spec.md:13; mcp/__main__.py:55; docker-compose.yml:26)
- Restore `meta/prompts/init_mcp_repo.json` or update references to avoid stale baseline assumptions (meta/prompts/audit_mcp_state.json:3; meta/prompts/implement_loop.json:12)
