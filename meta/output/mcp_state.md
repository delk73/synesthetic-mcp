## Summary of repo state
- STDIO JSON-RPC loop processes NDJSON sequentially, echoes request ids, and keeps stdout deterministic while logging via stderr (docs/mcp_spec.md:38; docs/mcp_spec.md:44; mcp/stdio_main.py:33; mcp/stdio_main.py:53; tests/test_stdio.py:15; tests/test_entrypoint.py:55)
- Entrypoint enforces STDIO-only transport, maintains `<pid> <ISO8601>` ready markers, and restores signal handlers on shutdown (docs/mcp_spec.md:49; docs/mcp_spec.md:215; mcp/__main__.py:35; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_stdio.py:70; tests/test_entrypoint.py:31)
- Discovery prefers env overrides before the `libs/synesthetic-schemas` submodule and sorts outputs for determinism (docs/mcp_spec.md:117; mcp/core.py:12; mcp/core.py:50; tests/test_env_discovery.py:7; tests/test_submodule_integration.py:32)
- Validation maps aliases to canonical schemas, strips `$schemaRef`, and enforces 1 MiB payload + RFC6901 ordering reused by backend populate (docs/mcp_spec.md:121; docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:106; tests/test_validate.py:37; tests/test_backend.py:41; tests/test_backend.py:55)
- Divergences persist: no 1 MiB pre-parse guard, `unsupported` responses expose `msg`, schema listings keep `.schema.json`, and FastAPI HTTP transport remains available (docs/mcp_spec.md:67; docs/mcp_spec.md:108; docs/mcp_spec.md:192; mcp/stdio_main.py:30; mcp/core.py:47; mcp/http_main.py:6; tests/test_http.py:4)

## Top gaps & fixes (3-5 bullets)
- Implement a pre-parse 1 MiB guard in the STDIO loop and exercise it with an oversized request test (docs/mcp_spec.md:192; mcp/stdio_main.py:33; tests/test_stdio.py:15)
- Replace non-spec `msg` keys on `reason: "unsupported"` payloads with `detail` across STDIO dispatch and backend helpers, updating assertions (docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_backend.py:21)
- Retire or hard-disable the FastAPI adapter and smoke test to keep transport STDIO-only per spec (docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4)
- Decide whether to surface schema paths without the `.schema.json` suffix or document the variant and add tests (docs/mcp_spec.md:67; mcp/core.py:47; tests/test_submodule_integration.py:32)

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:33; tests/test_stdio.py:15 |
| Ready file writes `<pid> <ISO8601>` and clears on shutdown | Present | docs/mcp_spec.md:49; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_stdio.py:70 |
| Spec errors stay inside `result`; JSON-RPC error only on malformed frames | Present | docs/mcp_spec.md:84; docs/mcp_spec.md:100; mcp/stdio_main.py:45; tests/test_stdio.py:109 |
| Discovery outputs sorted deterministically | Present | docs/mcp_spec.md:117; mcp/core.py:50; tests/test_submodule_integration.py:32 |
| Per-request 1 MiB STDIO guard | Missing | docs/mcp_spec.md:192; mcp/stdio_main.py:33 |
| `unsupported` responses use `detail` | Divergent | docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_backend.py:21 |
| Schema listing path matches golden example format | Divergent | docs/mcp_spec.md:67; mcp/core.py:47 |
| Transport limited to STDIO only | Divergent | docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4 |

## STDIO server entrypoint & process model
- NDJSON loop blocks on stdin, strips whitespace, and emits `{"jsonrpc":"2.0","id",...}` frames per request (docs/mcp_spec.md:38; mcp/stdio_main.py:33; tests/test_stdio.py:15)
- `_run_stdio` installs a SIGTERM handler that raises `KeyboardInterrupt` so in-flight work completes before exit (docs/mcp_spec.md:52; mcp/__main__.py:76)
- Startup logs `mcp:ready mode=stdio` on stderr and writes `<pid> <ISO8601>` to the ready file (docs/mcp_spec.md:214; mcp/__main__.py:88; mcp/__main__.py:89; tests/test_stdio.py:62)
- Shutdown restores previous signal handlers, logs `mcp:shutdown`, and removes the ready marker (docs/mcp_spec.md:215; mcp/__main__.py:99; mcp/__main__.py:105; tests/test_entrypoint.py:31)

## Golden request/response example
| Aspect | Status | Evidence |
| - | - | - |
| Success frame echoes `jsonrpc`, `id`, and wraps tool output in `result` | Present | docs/mcp_spec.md:60; mcp/stdio_main.py:45; tests/test_stdio.py:32 |
| Error frame echoes request `id` with JSON-RPC error object | Present | docs/mcp_spec.md:41; mcp/stdio_main.py:47; tests/test_stdio.py:140 |
| Schema listing path mirrors spec sample without `.schema.json` suffix | Divergent | docs/mcp_spec.md:67; mcp/core.py:47 |

## Payload size guard
| Method | Status | Evidence |
| - | - | - |
| STDIO transport pre-parse guard | Missing | docs/mcp_spec.md:192; mcp/stdio_main.py:33 |
| `validate_asset` | Present | mcp/validate.py:106; tests/test_validate.py:47 |
| `populate_backend` | Present | mcp/backend.py:34; tests/test_backend.py:55 |

## Schema validation contract
- Required `schema` parameter: `_load_schema` raises `schema_load_failed` when blank/unknown, returning `reason: "validation_failed"` (docs/mcp_spec.md:99; mcp/validate.py:106; mcp/validate.py:123)
- Alias handling maps `nested-synesthetic-asset` to the canonical schema and ignores `$schemaRef` during validation (docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:116; tests/test_validate.py:22)
- Error ordering emits RFC6901 pointers sorted by path then message for determinism (docs/mcp_spec.md:121; mcp/validate.py:147; tests/test_validate.py:37)

## Logging hygiene
- STDIO loop writes JSON-RPC frames to stdout only and flushes per message (docs/mcp_spec.md:44; mcp/stdio_main.py:53)
- Logging uses Python `logging` (stderr by default) and is observed on stderr in process tests (mcp/__main__.py:170; tests/test_entrypoint.py:55)

## Container & health
| Aspect | Status | Evidence |
| - | - | - |
| Docker image defaults to `python -m mcp` STDIO server | Present | Dockerfile:24 |
| Compose `serve` profile wires ready-file health check | Present | docker-compose.yml:14; docker-compose.yml:24 |
| `serve.sh` waits for healthy container before tailing logs | Present | serve.sh:31; serve.sh:45 |

## Schema discovery & validation
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` | Overrides schema root before submodule fallback | mcp/core.py:12; tests/test_env_discovery.py:29 |
| `SYN_EXAMPLES_DIR` | Overrides examples root before submodule fallback | mcp/core.py:25; tests/test_env_discovery.py:30 |
| Submodule fallback | Uses `libs/synesthetic-schemas` with deterministic ordering | mcp/core.py:18; tests/test_submodule_integration.py:28 |
| Example schema inference | Derives schema from payload, `$schemaRef`, or filename | mcp/core.py:83; tests/test_submodule_integration.py:46 |

## Test coverage
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO loop, ready file contents, and validate flow | Yes | tests/test_stdio.py:41 |
| JSON-RPC error id echo | Yes | tests/test_stdio.py:124 |
| Signal handling and shutdown logging | Yes | tests/test_entrypoint.py:31 |
| Schema/env overrides and deterministic listings | Yes | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:32 |
| Validation aliasing, error ordering, payload cap | Yes | tests/test_validate.py:22; tests/test_validate.py:37; tests/test_validate.py:47 |
| Backend success/error/size/validation guards | Yes | tests/test_backend.py:21; tests/test_backend.py:55 |
| Diff determinism | Yes | tests/test_diff.py:4 |
| STDIO 1 MiB guard | No | docs/mcp_spec.md:192; mcp/stdio_main.py:33 |

## Dependencies & runtime
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | Draft 2020-12 validation | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | Optional JSON Schema registry | mcp/validate.py:9 |
| fastapi | Optional HTTP adapter | mcp/http_main.py:6 |
| uvicorn | Optional HTTP runtime docs | README.md:81 |

## Environment variables
- `MCP_ENDPOINT` defaults to STDIO; any other value aborts startup (docs/mcp_spec.md:36; mcp/__main__.py:35; tests/test_entrypoint.py:92)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables file creation and shutdown removes existing marker (docs/mcp_spec.md:175; mcp/__main__.py:45; mcp/__main__.py:105)
- `SYN_SCHEMAS_DIR` must point to a directory or startup fails (docs/mcp_spec.md:176; mcp/__main__.py:22; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR` overrides example discovery with deterministic ordering (docs/mcp_spec.md:177; mcp/core.py:25; tests/test_env_discovery.py:7)
- `SYN_BACKEND_URL` gates backend populate (`unsupported` when unset) (docs/mcp_spec.md:178; mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and normalises a leading slash (docs/mcp_spec.md:179; mcp/backend.py:17; tests/test_backend.py:36)

## Documentation accuracy
- README advertises optional FastAPI/uvicorn usage even though the spec restricts transport to STDIO (docs/mcp_spec.md:36; README.md:81)
- README correctly documents ready file behavior and environment overrides matching the spec tables (docs/mcp_spec.md:175; README.md:55)
- README omits the 1 MiB STDIO limit called out in the spec (docs/mcp_spec.md:192; README.md:15)

## Detected divergences
- No pre-parse 1 MiB guard in STDIO transport (docs/mcp_spec.md:192; mcp/stdio_main.py:33)
- `reason: "unsupported"` payloads surface `msg` instead of spec `detail` (docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_backend.py:21)
- Schema listing paths retain `.schema.json` suffix, diverging from spec example (docs/mcp_spec.md:67; mcp/core.py:47)
- FastAPI adapter exposes a non-spec HTTP transport (docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4)

## Recommendations
- Add a 1 MiB size guard before JSON parsing in `mcp/stdio_main.main` and cover it with an oversized-request regression test (docs/mcp_spec.md:192; mcp/stdio_main.py:33; tests/test_stdio.py:15)
- Update `unsupported` payloads to use `detail` and adjust backend/tests to match the spec model (docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_backend.py:21)
- Decide whether to match the spec schema path format or document/test the intentional `.schema.json` suffix (docs/mcp_spec.md:67; mcp/core.py:47; tests/test_submodule_integration.py:32)
- Remove or fence the FastAPI adapter and HTTP smoke test so deployments remain STDIO-only as required (docs/mcp_spec.md:36; mcp/http_main.py:6; tests/test_http.py:4; README.md:81)
