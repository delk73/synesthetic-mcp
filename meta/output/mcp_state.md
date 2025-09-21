## Summary of repo state
- STDIO entrypoint defaults to newline-delimited JSON-RPC and logs readiness/shutdown, while HTTP health serving is gated behind `MCP_ENDPOINT` (mcp/__main__.py:55; mcp/__main__.py:168; README.md:80).
- Schema and example discovery honor env overrides first and fall back to the submodule with deterministic sorting (mcp/core.py:12; mcp/core.py:38; tests/test_env_discovery.py:7).
- Validation enforces alias resolution, RFC6901 errors, and a 1 MiB payload cap reused by backend populate (mcp/validate.py:17; mcp/validate.py:106; mcp/backend.py:34).
- Backend tooling stays behind `SYN_BACKEND_URL`, with error handling and optional path overrides (mcp/backend.py:24; mcp/backend.py:56; README.md:102).
- CI installs the package in editable mode and runs pytest across Python 3.11–3.13 with submodules enabled (.github/workflows/ci.yml:21; .github/workflows/ci.yml:34).

## Top gaps & fixes (3-5 bullets)
- Add a positive HTTP/TCP smoke test: current coverage only checks the invalid port path when `MCP_ENDPOINT` is set, leaving the happy-path readiness log and health handler unverified (tests/test_entrypoint.py:100; mcp/__main__.py:140).
- Gate Compose port publishing on HTTP mode or clarify its usage; the `serve` service still exposes `${MCP_PORT}` even though STDIO is the default and no socket is opened (docker-compose.yml:18; docker-compose.yml:26).
- Guard the STDIO validation integration test when schemas are unavailable; it relies on the checked-in submodule without a skip like other tests (tests/test_stdio.py:75; tests/test_submodule_integration.py:19).

## Alignment with mcp_spec.md and init_mcp_repo.json (Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO default with optional MCP_ENDPOINT override | Present | docs/mcp_spec.md:25; mcp/__main__.py:55 |
| Env→submodule discovery order & determinism | Present | docs/mcp_spec.md:105; mcp/core.py:38 |
| Validation alias + 1 MiB payload limit | Present | docs/mcp_spec.md:117; mcp/validate.py:17; mcp/validate.py:106 |
| RFC6902 diff limited to add/remove/replace | Present | docs/mcp_spec.md:61; mcp/diff.py:16 |
| Backend disabled without `SYN_BACKEND_URL`, 5 s timeout, error model | Present | docs/mcp_spec.md:116; mcp/backend.py:30; mcp/backend.py:55 |
| Logging and shutdown semantics (`mcp:ready` / `mcp:shutdown`) | Present | docs/mcp_spec.md:25; mcp/__main__.py:205 |
| Tests via editable install across Python 3.11–3.13 | Present | meta/prompts/init_mcp_repo.json:18; .github/workflows/ci.yml:34 |

## STDIO server entrypoint & process model
- Blocking loop delegates to `mcp.stdio_main.main()` after resolving schemas and endpoint mode (mcp/__main__.py:307; mcp/stdio_main.py:33).
- SIGTERM is trapped to raise `KeyboardInterrupt`, ensuring graceful shutdown and log emission (mcp/__main__.py:194; mcp/__main__.py:216).
- Startup/shutdown logs include mode and schemas dir, and readiness touches/removes `MCP_READY_FILE` (mcp/__main__.py:205; mcp/__main__.py:85).
- Fatal setup errors (bad schemas dir or endpoint) emit `mcp:error` and exit `2`; runtime failures exit non-zero (mcp/__main__.py:296; mcp/__main__.py:321).

## Container & health (Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Status | Evidence |
| - | - | - |
| `serve` service runs `python -m mcp` in foreground | Present | docker-compose.yml:25 |
| Healthcheck watches readiness file (`[ -f MCP_READY_FILE ]`) | Present | docker-compose.yml:29; mcp/__main__.py:205 |
| TCP port published only when HTTP enabled | Divergent | docker-compose.yml:18; docker-compose.yml:26 |

## Schema discovery & validation (Source → Mechanism → Evidence)
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR` | Direct env override of lookup dirs | mcp/core.py:12; tests/test_env_discovery.py:29 |
| Submodule fallback | Uses `libs/synesthetic-schemas` paths when present | mcp/core.py:18; tests/test_submodule_integration.py:28 |
| Missing schemas dir | Raises setup failure before starting loop | mcp/__main__.py:30; tests/test_entrypoint.py:78 |
| Schema alias inference | Maps examples to nested alias before validation | mcp/core.py:93; mcp/validate.py:17 |
| Local registry | Optional referencing registry seeded from submodule | mcp/validate.py:52 |

## Test coverage (Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for schemas/examples | Yes | tests/test_env_discovery.py:7 |
| Submodule discovery & determinism | Yes | tests/test_submodule_integration.py:23 |
| STDIO ready/shutdown on SIGINT | Yes | tests/test_entrypoint.py:31 |
| Invalid schema dir exits non-zero | Yes | tests/test_entrypoint.py:78 |
| Invalid port rejected when HTTP requested | Yes | tests/test_entrypoint.py:92 |
| STDIO MCP loop validates asset via JSON-RPC | Yes | tests/test_stdio.py:40 |
| Backend success/error/validation guards | Yes | tests/test_backend.py:28 |
| Diff determinism | Yes | tests/test_diff.py:11 |
| HTTP/TCP happy path (`mode=http`) | No | tests/test_entrypoint.py:100 |
| HTTP adapter (FastAPI) smoke | Skipped if dependency missing | tests/test_http.py:4 |

## Dependencies & runtime (Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | Draft 2020-12 validation (mcp/validate.py:8) | Required |
| httpx | Backend populate client (mcp/backend.py:7) | Required |
| pytest | Test runner (requirements.txt:3; pytest.ini:1) | Required (tests) |
| referencing | Local schema registry (mcp/validate.py:10) | Optional |
| fastapi | HTTP adapter factory (mcp/http_main.py:6) | Optional |
| uvicorn | Suggested HTTP runtime (README.md:83) | Optional |

## Environment variables
- `MCP_ENDPOINT` (default `stdio`) selects transport and HTTP opt-in (mcp/__main__.py:55; README.md:96).
- `MCP_READY_FILE` (default `/tmp/mcp.ready`) is created on readiness and removed on shutdown for health checks (mcp/__main__.py:77; docker-compose.yml:29).
- `MCP_HOST` / `MCP_PORT` apply when HTTP/TCP is requested; invalid ports raise setup failures (mcp/__main__.py:43; tests/test_entrypoint.py:92).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR` override discovery; missing paths cause startup errors (mcp/core.py:12; mcp/__main__.py:30).
- `SYN_BACKEND_URL` gates populate; unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH` customizes POST path with leading slash normalization (mcp/backend.py:17; tests/test_backend.py:36).

## Documentation accuracy (README vs. docs)
- README quickstart highlights STDIO-first behavior and optional HTTP override, matching the spec entrypoint description (README.md:40; README.md:80; docs/mcp_spec.md:25).
- Environment table documents new MCP knobs alongside schema/back-end variables (README.md:94; mcp/__main__.py:55).
- Spec discovery order and validation rules align with implementation and tests (docs/mcp_spec.md:105; docs/mcp_spec.md:117; mcp/core.py:38).

## Detected divergences
- Compose still publishes `${MCP_PORT}` even when running in STDIO mode, exposing an unused TCP port unless HTTP is explicitly enabled (docker-compose.yml:18; mcp/__main__.py:307).
- HTTP/TCP happy path lacks automated verification, leaving the optional health server untested (mcp/__main__.py:168; tests/test_entrypoint.py:100).

## Recommendations
- Add an integration test that runs `python -m mcp` with `MCP_ENDPOINT=http://127.0.0.1:0` and asserts the readiness log plus `/healthz` response (mcp/__main__.py:140; tests/test_entrypoint.py:100).
- Update `docker-compose.yml` to conditionally publish `${MCP_PORT}` only when `MCP_ENDPOINT` requests HTTP/TCP, or annotate the README accordingly (docker-compose.yml:18; README.md:40).
- Mirror the submodule skip guard in `tests/test_stdio.py` so environments without `libs/synesthetic-schemas` skip gracefully (tests/test_stdio.py:75; tests/test_submodule_integration.py:19).
