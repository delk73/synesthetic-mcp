## Summary of repo state
- STDIO transport stays spec-compliant with NDJSON framing, sequential handling, and a 1 MiB pre-parse guard (docs/mcp_spec.md:38; docs/mcp_spec.md:41; mcp/stdio_main.py:38; mcp/stdio_main.py:45; tests/test_stdio.py:17; tests/test_stdio.py:171)
- Entrypoint locks transport to STDIO, writes `<pid> <ISO8601>` ready markers, and restores signal handlers on shutdown (docs/mcp_spec.md:36; docs/mcp_spec.md:49; docs/mcp_spec.md:215; mcp/__main__.py:35; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_entrypoint.py:31)
- Validation shares alias mapping, `$schemaRef` stripping, payload caps, and RFC6901 ordering across CLI and backend flows (docs/mcp_spec.md:99; docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:106; tests/test_validate.py:37; tests/test_validate.py:47; tests/test_validate.py:57)
- Backend populate honours env gating, per-request size limits, and validation-before-post semantics with deterministic mocks (docs/mcp_spec.md:108; docs/mcp_spec.md:178; mcp/backend.py:30; mcp/backend.py:38; mcp/backend.py:49; tests/test_backend.py:21; tests/test_backend.py:55; tests/test_backend.py:95)
- Docs and README now describe the same discovery order, alias behaviour, and 1 MiB STDIO guard as the implementation (docs/mcp_spec.md:28; docs/mcp_spec.md:41; README.md:35; README.md:127; README.md:138; README.md:167)

## Top gaps & fixes (3-5 bullets)
- Add an entrypoint test for `MCP_READY_FILE=""` to prove ready-file suppression and log-only shutdown (docs/mcp_spec.md:49; mcp/__main__.py:45; tests/test_stdio.py:62)
- Exercise `SYN_BACKEND_ASSETS_PATH=custom-assets` (no leading slash) so the normalization branch stays covered (mcp/backend.py:17; tests/test_backend.py:36)
- Add a network-failure populate test that asserts `reason:"backend_error"`, `status:503` from the `httpx.HTTPError` path (docs/mcp_spec.md:108; mcp/backend.py:60; tests/test_backend.py:47)

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential loop | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:38; tests/test_stdio.py:17 |
| Ready file lifecycle `<pid> <ISO8601>` | Present | docs/mcp_spec.md:49; mcp/__main__.py:88; mcp/__main__.py:105; tests/test_stdio.py:62 |
| Transport limited to STDIO | Present | docs/mcp_spec.md:36; mcp/__main__.py:35; tests/test_entrypoint.py:92 |
| Spec errors stay in `result`; JSON-RPC error only on malformed frames | Present | docs/mcp_spec.md:84; mcp/stdio_main.py:45; mcp/stdio_main.py:66; tests/test_stdio.py:126 |
| Per-request 1 MiB payload guard | Present | docs/mcp_spec.md:41; mcp/stdio_main.py:45; tests/test_stdio.py:171 |
| `unsupported` responses include `detail` | Present | docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_stdio.py:152 |
| Deterministic schema/example ordering | Present | docs/mcp_spec.md:117; mcp/core.py:54; tests/test_submodule_integration.py:34 |
| Validation errors emit RFC6901 pointers sorted by path/msg | Present | docs/mcp_spec.md:121; mcp/validate.py:147; tests/test_validate.py:37 |

## STDIO server entrypoint & process model
- NDJSON loop reads one request per line from stdin and skips empties before dispatch (docs/mcp_spec.md:38; mcp/stdio_main.py:38)
- `_run_stdio` installs a SIGTERM handler that raises `KeyboardInterrupt` so in-flight work finishes (docs/mcp_spec.md:52; mcp/__main__.py:76)
- Startup logs `mcp:ready mode=stdio` on stderr and writes `<pid> <ISO8601>` to the ready file (docs/mcp_spec.md:214; mcp/__main__.py:88; tests/test_stdio.py:62)
- Shutdown restores previous signal handlers, logs `mcp:shutdown`, and removes the ready marker (docs/mcp_spec.md:215; mcp/__main__.py:99; mcp/__main__.py:105; tests/test_entrypoint.py:59)

## Golden request/response example
| Aspect | Status | Evidence |
| - | - | - |
| Success frame mirrors spec sample with `jsonrpc`, `id`, and `result` wrapper | Present | docs/mcp_spec.md:60; mcp/stdio_main.py:61; tests/test_stdio.py:29 |
| Error frame echoes the request `id` via JSON-RPC error object | Present | docs/mcp_spec.md:135; mcp/stdio_main.py:66; tests/test_stdio.py:126 |

## Payload size guard
| Method | Status | Evidence |
| - | - | - |
| STDIO transport pre-parse guard | Present | docs/mcp_spec.md:41; mcp/stdio_main.py:45; tests/test_stdio.py:171 |
| `validate_asset` payload cap | Present | mcp/validate.py:107; tests/test_validate.py:47 |
| `populate_backend` payload cap | Present | mcp/backend.py:38; tests/test_backend.py:55 |

## Schema validation contract
- Missing or blank `schema` surfaces `reason:"validation_failed"` with `schema_load_failed` messaging (docs/mcp_spec.md:99; mcp/validate.py:123; tests/test_validate.py:57)
- Alias handling maps `nested-synesthetic-asset` to the canonical schema and ignores top-level `$schemaRef` (docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:116; tests/test_validate.py:37)
- Errors emit RFC6901 pointers sorted by `(path, msg)` for deterministic ordering (docs/mcp_spec.md:121; mcp/validate.py:147; tests/test_validate.py:37)

## Logging hygiene
- STDIO loop writes JSON-RPC frames to stdout and never logs there; flushing happens per response (docs/mcp_spec.md:44; mcp/stdio_main.py:68)
- Entrypoint uses `logging` (stderr) for readiness and shutdown logs verified under subprocess (mcp/__main__.py:88; mcp/__main__.py:99; tests/test_entrypoint.py:55)

## Container & health
| Aspect | Status | Evidence |
| - | - | - |
| Docker image defaults to `python -m mcp` | Present | Dockerfile:24 |
| Compose `serve` service runs STDIO command with ready-file health check | Present | docker-compose.yml:23; docker-compose.yml:25 |
| `serve.sh` waits for a healthy container before tailing logs | Present | serve.sh:31; serve.sh:45 |

## Schema discovery & validation
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` | Overrides schema root before submodule fallback | mcp/core.py:12; tests/test_env_discovery.py:29 |
| `SYN_EXAMPLES_DIR` | Overrides example root before submodule fallback | mcp/core.py:25; tests/test_env_discovery.py:35 |
| Submodule fallback | Uses `libs/synesthetic-schemas` directories when present | mcp/core.py:18; tests/test_submodule_integration.py:29 |
| Example schema inference | Derives schema from payload, `$schemaRef`, or filename | mcp/core.py:87; tests/test_submodule_integration.py:47 |

## Test coverage
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO framing, success/error paths, and oversize guard | Yes | tests/test_stdio.py:17; tests/test_stdio.py:126; tests/test_stdio.py:171 |
| Ready file creation, shutdown logging, signal handling | Yes | tests/test_stdio.py:62; tests/test_entrypoint.py:31 |
| Transport rejects non-STDIO endpoints | Yes | tests/test_entrypoint.py:92 |
| Validation aliasing, ordering, payload cap, missing schema | Yes | tests/test_validate.py:37; tests/test_validate.py:47; tests/test_validate.py:57 |
| Schema/env discovery determinism | Yes | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:34 |
| Backend populate success/error/size handling | Yes | tests/test_backend.py:21; tests/test_backend.py:55; tests/test_backend.py:95 |
| Diff determinism | Yes | tests/test_diff.py:4 |

## Dependencies & runtime
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:9 |

## Environment variables
- `MCP_ENDPOINT` defaults to STDIO; any other value raises a setup failure before starting the loop (docs/mcp_spec.md:36; mcp/__main__.py:35; tests/test_entrypoint.py:92)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables creation while shutdown removes the marker (docs/mcp_spec.md:49; mcp/__main__.py:45; mcp/__main__.py:105)
- `SYN_SCHEMAS_DIR` must exist or startup aborts with `reason=setup_failed` (docs/mcp_spec.md:176; mcp/__main__.py:22; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR` overrides example discovery before submodule fallback (docs/mcp_spec.md:177; mcp/core.py:25; tests/test_env_discovery.py:35)
- `SYN_BACKEND_URL` gates backend populate and returns `reason:"unsupported"` when unset (docs/mcp_spec.md:178; mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and prepends a slash when missing (docs/mcp_spec.md:179; mcp/backend.py:17)

## Documentation accuracy
- README features and serving guidance now call out the 1 MiB STDIO guard consistent with the spec (docs/mcp_spec.md:41; README.md:35; README.md:138; README.md:167)
- README environment notes match discovery priority and env behaviour in the spec and code (docs/mcp_spec.md:28; docs/mcp_spec.md:176; README.md:160)
- Alias handling and error model examples align with the spec and implementation (docs/mcp_spec.md:198; docs/mcp_spec.md:153; README.md:127; README.md:134)

## Detected divergences
- None

## Recommendations
- Add a regression test covering `MCP_READY_FILE=""` to confirm no file is written and shutdown still logs (docs/mcp_spec.md:49; mcp/__main__.py:45; tests/test_stdio.py:62)
- Add a populate test using `SYN_BACKEND_ASSETS_PATH=custom-assets` to verify the leading-slash normalization (mcp/backend.py:17; tests/test_backend.py:36)
- Mock a network failure in `populate_backend` to assert the 503 `backend_error` response path (docs/mcp_spec.md:108; mcp/backend.py:60; tests/test_backend.py:47)
