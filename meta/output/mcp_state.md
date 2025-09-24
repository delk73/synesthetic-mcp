## Summary of repo state
- STDIO and socket transports share the NDJSON dispatcher, 1 MiB guard, ready-file lifecycle, and signal-aware shutdown with coverage in integration tests (mcp/stdio_main.py:46; mcp/socket_main.py:53; mcp/__main__.py:104; tests/test_stdio.py:92; tests/test_socket.py:84).
- Socket mode now accepts concurrent Unix-domain clients while preserving per-connection ordering and cleanup (mcp/socket_main.py:36; mcp/socket_main.py:67; tests/test_socket.py:147).
- Schema discovery, validation, diff, and backend tools remain deterministic with local-only references and traversal guards verified by unit tests (mcp/core.py:16; mcp/core.py:85; mcp/validate.py:152; mcp/diff.py:49; tests/test_path_traversal.py:34; tests/test_validate.py:46).

## Top gaps & fixes (3-5 bullets)
- Expand the multi-client socket test to issue overlapping requests from both clients to stress interleaved ordering guarantees (tests/test_socket.py:191).
- Add a regression test that exercises a custom `MCP_SOCKET_MODE` to ensure permissions remain 0600 by default and configurable when overridden (mcp/__main__.py:52; mcp/socket_main.py:34).
- Add a STDIO regression test that confirms the loop exits cleanly when stdin closes without an explicit signal (mcp/stdio_main.py:46).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop & sequential replies | Present | mcp/stdio_main.py:46; tests/test_stdio.py:29 |
| Ready-file lifecycle & SIGINT/SIGTERM handling | Present | mcp/__main__.py:104; mcp/__main__.py:115; tests/test_stdio.py:117 |
| Socket NDJSON transport with multi-client support | Present | mcp/socket_main.py:36; mcp/socket_main.py:67; tests/test_socket.py:147 |
| 1 MiB payload guard (STDIO & socket) | Present | mcp/transport.py:15; mcp/socket_main.py:110; tests/test_stdio.py:220; tests/test_socket.py:114 |
| `validate` alias accepted for `validate_asset` | Present | mcp/stdio_main.py:22; tests/test_stdio.py:56 |
| Path traversal rejection for schemas/examples | Present | mcp/core.py:16; mcp/core.py:63; tests/test_path_traversal.py:34 |
| Local-only `$ref` resolution | Present | mcp/validate.py:52; mcp/validate.py:152 |
| Deterministic listings/errors/diff | Present | mcp/core.py:85; mcp/core.py:122; mcp/validate.py:162; mcp/diff.py:49; tests/test_submodule_integration.py:34; tests/test_validate.py:46 |
| `get_example` validation_failed path | Present | mcp/core.py:147; tests/test_validate.py:32 |
| `validate_many` optional batching | Optional | docs/mcp_spec.md:89; mcp/stdio_main.py:13 |
| Non-root container runtime guidance | Present | Dockerfile:24 |

## Transports
- STDIO remains default via `MCP_ENDPOINT` selection and fails fast on unsupported transports (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- Socket mode shares the dispatcher, enforces socket permissions, and tears down resources after serving (mcp/socket_main.py:34; mcp/socket_main.py:83; tests/test_socket.py:131).

## STDIO server entrypoint & process model (bullets: NDJSON framing, blocking loop, signals, readiness file, shutdown semantics, stdout vs stderr)
- NDJSON framing processes one stripped line at a time and writes one JSON object per stdout line (mcp/stdio_main.py:46; mcp/stdio_main.py:53).
- Blocking loop over `sys.stdin` preserves FIFO request handling (mcp/stdio_main.py:46).
- SIGTERM converts to `KeyboardInterrupt` so in-flight work completes before exit (mcp/__main__.py:92).
- Ready file writes `<pid> <ISO8601>` on readiness and clears on shutdown (mcp/__main__.py:69; mcp/__main__.py:115; tests/test_stdio.py:121).
- Shutdown restores prior handlers and logs `mcp:shutdown` to stderr (mcp/__main__.py:115; tests/test_stdio.py:117).
- stdout carries frames only; readiness/shutdown logs route through `logging` on stderr (mcp/stdio_main.py:53; mcp/__main__.py:104).

## Socket server (if present) (bullets: UDS path, perms, multi-client handling, per-connection ordering, unlink on shutdown, readiness/shutdown logs)
- Binds `MCP_SOCKET_PATH` and applies the requested file mode (`0600` default) before listening (mcp/socket_main.py:34; mcp/socket_main.py:36).
- Each accepted connection runs in a daemon thread, enabling concurrent clients while preserving per-connection order via `_serve_connection` (mcp/socket_main.py:67; mcp/socket_main.py:95; tests/test_socket.py:147).
- Shutdown sets `_closing`, joins live threads, and unlinks the socket path (mcp/socket_main.py:39; mcp/socket_main.py:48; mcp/socket_main.py:51).
- Logs readiness/shutdown with path metadata and removes the ready file (mcp/__main__.py:147; mcp/__main__.py:161; tests/test_socket.py:84).

## Golden request/response examples (table: Method → Success frame Present/Missing/Divergent → Error frame Present/Missing/Divergent → Evidence)
| Method | Success frame | Error frame | Evidence |
| - | - | - | - |
| list_schemas | Present | — | tests/test_stdio.py:29 |
| get_schema | Present | Present | tests/test_validate.py:19; tests/test_validate.py:14 |
| validate_asset | Present | Present | tests/test_stdio.py:144; tests/test_stdio.py:17 |
| validate (alias) | Present | Present | tests/test_stdio.py:56; mcp/stdio_main.py:25 |
| get_example | Present | Present | tests/test_submodule_integration.py:47; tests/test_validate.py:32 |
| diff_assets | Present | — | tests/test_diff.py:11 |
| populate_backend | Present | Present | tests/test_backend.py:31; tests/test_backend.py:57 |
| Malformed JSON-RPC frame | — | Present | tests/test_stdio.py:175; tests/test_socket.py:102 |

## Payload size guard (table: Method → STDIO guard → Socket guard → Evidence)
| Method | STDIO guard | Socket guard | Evidence |
| - | - | - | - |
| JSON-RPC frame ingest | Present | Present | mcp/transport.py:15; mcp/socket_main.py:110; tests/test_stdio.py:220; tests/test_socket.py:114 |
| validate_asset payload | Present | Present | mcp/validate.py:114; tests/test_validate.py:56; mcp/socket_main.py:118 |
| populate_backend payload | Present | n/a (HTTP) | mcp/backend.py:38; tests/test_backend.py:65 |

## Schema validation contract (bullets: required schema param, alias handling, error ordering, explicit validate_asset behavior)
- Required schema param enforced before dispatch; missing values yield `/schema` validation_failed (mcp/stdio_main.py:25; tests/test_stdio.py:17).
- `validate` alias routes to the same logic as `validate_asset` (mcp/stdio_main.py:22; tests/test_stdio.py:56).
- Errors convert to RFC6901 pointers and sort deterministically (mcp/validate.py:159; mcp/validate.py:162; tests/test_validate.py:46).
- `validate_asset` enforces payload limits, strips `$schemaRef`, and constrains schema lookup to configured roots (mcp/validate.py:114; mcp/validate.py:123; mcp/validate.py:130).

## Optional batching (if present) (table: Shape → Cap enforcement → Evidence)
| Shape | Cap enforcement | Evidence |
| - | - | - |
| validate_many | Optional (not implemented) | docs/mcp_spec.md:89; mcp/stdio_main.py:13 |

## Logging hygiene (bullets: stdout frames only; stderr logs/diagnostics; deterministic timestamps)
- STDIO responses remain on stdout while logs use `logging` on stderr (mcp/stdio_main.py:53; tests/test_stdio.py:42).
- Entry points log readiness/shutdown with structured messages (mcp/__main__.py:104; mcp/__main__.py:161; tests/test_entrypoint.py:58).
- Ready file timestamps are written in ISO-8601 UTC for health checks (mcp/__main__.py:75; tests/test_stdio.py:127).

## Container & health (table: Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Status | Evidence |
| - | - | - |
| Non-root runtime | Present | Dockerfile:24 |
| Ready-file healthcheck (compose) | Present | docker-compose.yml:26 |
| Transport/env passthrough (serve service) | Present | docker-compose.yml:18 |

## Schema discovery & validation (table: Source → Mechanism → Evidence)
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` override | Absolute path validated before use | mcp/__main__.py:23 |
| Submodule fallback | Defaults to libs directory when env unset | mcp/core.py:33; tests/test_submodule_integration.py:28 |
| Example discovery | Component filter with deterministic sort | mcp/core.py:106; tests/test_env_discovery.py:35 |
| Schema alias inference | `$schemaRef` and filename heuristics | mcp/core.py:126; tests/test_backend.py:118 |

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO loop & payload guard | ✅ | tests/test_stdio.py:29; tests/test_stdio.py:220 |
| Socket lifecycle & guard | ✅ | tests/test_socket.py:84; tests/test_socket.py:114 |
| Socket multi-client handling | ✅ | tests/test_socket.py:147 |
| Path traversal rejection | ✅ | tests/test_path_traversal.py:34 |
| Validation contract & ordering | ✅ | tests/test_validate.py:46 |
| Backend populate flows & limits | ✅ | tests/test_backend.py:28; tests/test_backend.py:65 |
| Diff determinism | ✅ | tests/test_diff.py:11 |
| Ready file & signal handling | ✅ | tests/test_entrypoint.py:54 |

## Dependencies & runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Schema validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry | Optional | mcp/validate.py:9 |

## Environment variables (bullets: name, default, behavior when missing/invalid)
- `MCP_ENDPOINT`: defaults to `stdio`; rejects unsupported transports with setup failure (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- `MCP_SOCKET_PATH`: defaults to `/tmp/mcp.sock`; used verbatim for UDS binding (mcp/__main__.py:47; tests/test_socket.py:95).
- `MCP_SOCKET_MODE`: defaults to `0600`; invalid values raise setup errors (mcp/__main__.py:52).
- `MCP_READY_FILE`: defaults to `/tmp/mcp.ready`; blank disables ready-file writes (mcp/__main__.py:61).
- `SYN_SCHEMAS_DIR`: must point to an existing directory; missing dirs abort startup (mcp/__main__.py:24; tests/test_entrypoint.py:81).
- `SYN_EXAMPLES_DIR`: overrides example lookup; falls back to submodule when unset (mcp/core.py:40).
- `SYN_BACKEND_URL`: gates backend POST; unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH`: normalized to a leading slash before POST (mcp/backend.py:17; tests/test_backend.py:46).

## Documentation accuracy (bullets: README vs. docs/mcp_spec.md)
- README Quickstart and serving instructions now match available scripts and logging behavior, aligning with the spec guidance (README.md:39; README.md:169; up.sh:4).
- README continues to describe STDIO default, optional socket mode, and 1 MiB guard consistent with the spec (README.md:34; docs/mcp_spec.md:31).

## Detected divergences
- None.

## Recommendations
- Enhance the socket concurrency test to issue overlapping requests from both clients to harden against future ordering regressions (tests/test_socket.py:191).
- Add automated coverage for custom `MCP_SOCKET_MODE` values to ensure permission changes remain safe (mcp/__main__.py:52; mcp/socket_main.py:34).
- Introduce a STDIO regression test asserting the loop exits cleanly when stdin closes without signals (mcp/stdio_main.py:46).
