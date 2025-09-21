## Summary of repo state
- STDIO loop enforces NDJSON framing, rejects lines over 1 MiB before parsing, and returns spec-compliant `unsupported` details (docs/mcp_spec.md:38; docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/stdio_main.py:45; tests/test_stdio.py:152; tests/test_stdio.py:171)
- Entrypoint locks transport to STDIO, manages `<pid> <ISO8601>` ready markers, and restores signal handlers on shutdown (docs/mcp_spec.md:49; docs/mcp_spec.md:215; mcp/__main__.py:35; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_stdio.py:62; tests/test_entrypoint.py:31)
- Schema discovery prioritises env overrides before the submodule and now emits `.json`-suffix paths sorted for determinism (docs/mcp_spec.md:117; docs/mcp_spec.md:67; mcp/core.py:12; mcp/core.py:49; tests/test_env_discovery.py:29; tests/test_submodule_integration.py:31)
- Validation shares alias mapping, `$schemaRef` stripping, payload caps, and RFC6901 ordering with backend populate flows (docs/mcp_spec.md:121; docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:106; tests/test_validate.py:37; tests/test_backend.py:55)
- Containers default to `python -m mcp`, Compose wires ready-file health checks, and serve.sh waits for healthy state before tailing logs (Dockerfile:24; docker-compose.yml:23; docker-compose.yml:24; serve.sh:31)

## Top gaps & fixes (3-5 bullets)
- Add README call-out for the 1 MiB STDIO limit so docs match the spec guidance (docs/mcp_spec.md:192; README.md:28)
- Add an explicit regression test covering `validate_asset` with a missing schema to lock the `schema_load_failed` path (docs/mcp_spec.md:99; mcp/validate.py:123; tests/test_validate.py:19)
- Consider exposing both the canonical and display schema paths to avoid clients depending on a non-existent `.json` file (docs/mcp_spec.md:67; mcp/core.py:49)

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:38; tests/test_stdio.py:17 |
| Ready file writes `<pid> <ISO8601>` and clears on shutdown | Present | docs/mcp_spec.md:49; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_stdio.py:62 |
| Spec errors stay in `result`; JSON-RPC error reserved for malformed frames | Present | docs/mcp_spec.md:84; mcp/stdio_main.py:45; mcp/stdio_main.py:66; tests/test_stdio.py:171 |
| Per-request 1 MiB STDIO guard | Present | docs/mcp_spec.md:192; mcp/stdio_main.py:45; tests/test_stdio.py:171 |
| `unsupported` responses expose `detail` | Present | docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32; tests/test_stdio.py:152; tests/test_backend.py:21 |
| Schema listings follow spec sample path format | Present | docs/mcp_spec.md:67; mcp/core.py:49; tests/test_submodule_integration.py:31 |
| Transport limited to STDIO | Present | docs/mcp_spec.md:36; mcp/__main__.py:35; docker-compose.yml:23 |

## STDIO server entrypoint & process model
- NDJSON loop strips newline-delimited stdin, handles one request per line, and blocks on STDIO (docs/mcp_spec.md:38; mcp/stdio_main.py:38)
- `_run_stdio` installs a SIGTERM handler that raises `KeyboardInterrupt` so in-flight work can finish (docs/mcp_spec.md:52; mcp/__main__.py:76)
- Startup logs `mcp:ready mode=stdio` on stderr and writes `<pid> <ISO8601>` to the ready file (docs/mcp_spec.md:214; mcp/__main__.py:88; tests/test_stdio.py:62)
- Shutdown restores previous signal handlers, logs `mcp:shutdown`, and removes the ready marker (docs/mcp_spec.md:215; mcp/__main__.py:99; mcp/__main__.py:105; tests/test_entrypoint.py:31)

## Golden request/response example
| Aspect | Status | Evidence |
| - | - | - |
| Success frame echoes `jsonrpc`, `id`, and wraps tool output in `result` | Present | docs/mcp_spec.md:60; mcp/stdio_main.py:61; tests/test_stdio.py:29 |
| Error frame echoes request `id` via JSON-RPC error object | Present | docs/mcp_spec.md:135; mcp/stdio_main.py:66; tests/test_stdio.py:126 |

## Payload size guard
| Method | Status | Evidence |
| - | - | - |
| STDIO transport pre-parse guard | Present | docs/mcp_spec.md:192; mcp/stdio_main.py:45; tests/test_stdio.py:171 |
| `validate_asset` payload cap | Present | mcp/validate.py:106; tests/test_validate.py:47 |
| `populate_backend` payload cap | Present | mcp/backend.py:38; tests/test_backend.py:55 |

## Schema validation contract
- Required `schema` parameter raises `schema_load_failed` with `reason: "validation_failed"` when missing or unknown (docs/mcp_spec.md:99; mcp/validate.py:123)
- Alias handling maps `nested-synesthetic-asset` to the canonical schema and ignores `$schemaRef` fields (docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:116; tests/test_validate.py:37)
- Validation errors emit RFC6901 pointers sorted deterministically for reproducible output (docs/mcp_spec.md:121; mcp/validate.py:147; tests/test_validate.py:37)

## Logging hygiene
- STDIO loop writes responses to stdout and flushes per frame while logging goes through `logging` (stderr) (docs/mcp_spec.md:44; mcp/stdio_main.py:68)
- Entrypoint logs readiness and shutdown on stderr, verified via subprocess tests (mcp/__main__.py:88; mcp/__main__.py:99; tests/test_entrypoint.py:55)

## Container & health
| Aspect | Status | Evidence |
| - | - | - |
| Docker image defaults to the blocking STDIO server | Present | Dockerfile:24 |
| Compose `serve` profile runs STDIO command with ready-file health check | Present | docker-compose.yml:23; docker-compose.yml:24 |
| `serve.sh` waits for container health before tailing logs | Present | serve.sh:31 |

## Schema discovery & validation
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` | Overrides schema root before submodule fallback | mcp/core.py:12; tests/test_env_discovery.py:29 |
| `SYN_EXAMPLES_DIR` | Overrides example root before submodule fallback | mcp/core.py:25; tests/test_env_discovery.py:30 |
| Submodule fallback | Uses `libs/synesthetic-schemas` with deterministic ordering | mcp/core.py:38; tests/test_submodule_integration.py:28 |
| Example schema inference | Derives schema from payload, `$schemaRef`, or filename | mcp/core.py:83; tests/test_submodule_integration.py:47 |

## Test coverage
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO loop framing and 1 MiB guard | Yes | tests/test_stdio.py:17; tests/test_stdio.py:171 |
| Ready file creation and shutdown logging | Yes | tests/test_stdio.py:62; tests/test_entrypoint.py:31 |
| Transport rejects non-STDIO endpoints | Yes | tests/test_entrypoint.py:92 |
| Validation aliasing, ordering, and payload cap | Yes | tests/test_validate.py:37; tests/test_validate.py:47 |
| Schema/env discovery determinism | Yes | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:31 |
| Backend populate success/error/size handling | Yes | tests/test_backend.py:21; tests/test_backend.py:55 |
| Diff determinism | Yes | tests/test_diff.py:4 |

## Dependencies & runtime
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:9 |

## Environment variables
- `MCP_ENDPOINT` defaults to `stdio`; any other value aborts startup before serving (docs/mcp_spec.md:36; mcp/__main__.py:35; tests/test_entrypoint.py:92)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables creation while shutdown removes existing markers (docs/mcp_spec.md:175; mcp/__main__.py:45; mcp/__main__.py:105)
- `SYN_SCHEMAS_DIR` must point to a directory or startup fails (docs/mcp_spec.md:176; mcp/__main__.py:22; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR` overrides example discovery ahead of the submodule (docs/mcp_spec.md:177; mcp/core.py:25; tests/test_env_discovery.py:30)
- `SYN_BACKEND_URL` gates backend populate; unset returns `reason: "unsupported"` (docs/mcp_spec.md:178; mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and normalises a leading slash (docs/mcp_spec.md:179; mcp/backend.py:17; tests/test_backend.py:36)

## Documentation accuracy
- README advertises only the STDIO transport and covers ready-file behaviour, matching the spec transport guidance (docs/mcp_spec.md:36; docs/mcp_spec.md:49; README.md:34; README.md:163)
- README environment table aligns with the spec defaults for discovery and backend controls (docs/mcp_spec.md:175; docs/mcp_spec.md:179; README.md:89)
- README error model now uses `detail` for `reason: "unsupported"` like the spec (docs/mcp_spec.md:153; README.md:133)

## Detected divergences
- None

## Recommendations
- Document the 1 MiB STDIO request limit in README to align internal docs with the spec (docs/mcp_spec.md:192; README.md:28)
- Add a regression test for `validate_asset` when `schema` is blank to prove the `schema_load_failed` contract (docs/mcp_spec.md:99; mcp/validate.py:123; tests/test_validate.py:19)
- Provide both canonical `.schema.json` and display `.json` paths (or clarify usage) to help clients locate actual schema files (docs/mcp_spec.md:67; mcp/core.py:49)
