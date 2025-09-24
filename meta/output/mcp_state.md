## Summary of repo state
- STDIO and socket transports share the NDJSON dispatcher, enforce the 1 MiB guard before parsing, and honor the ready-file lifecycle with signal-aware shutdown (mcp/stdio_main.py:46; mcp/socket_main.py:36; mcp/__main__.py:104; tests/test_stdio.py:220; tests/test_socket.py:114).
- Socket mode now launches a thread per connection to satisfy the multi-client requirement while preserving per-connection ordering and unlinking the UDS on shutdown (mcp/socket_main.py:36; mcp/socket_main.py:67; mcp/socket_main.py:48; tests/test_socket.py:147).
- Schema discovery, validation, diff, and backend tooling remain deterministic, local-only, and covered by targeted tests (mcp/core.py:16; mcp/core.py:85; mcp/validate.py:162; mcp/diff.py:49; tests/test_path_traversal.py:34; tests/test_validate.py:46).

## Top gaps & fixes (3-5 bullets)
- Implement `validate_many` with MCP_MAX_BATCH enforcement to meet the v0.2.5 batching requirement (docs/mcp_spec.md:89; mcp/stdio_main.py:13).
- Emit a deprecation warning when the `validate` alias is used, as mandated in v0.2.5 (mcp/stdio_main.py:22; docs/mcp_spec.md:94).
- Add automated coverage ensuring the socket honours custom `MCP_SOCKET_MODE` permissions and that default remains 0600 (mcp/__main__.py:52; mcp/socket_main.py:34).
- Introduce a STDIO regression test asserting the loop exits cleanly when stdin closes without signals (mcp/stdio_main.py:46).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop & sequential responses | Present | mcp/stdio_main.py:46; tests/test_stdio.py:29 |
| Ready file `<pid> <ISO8601>` lifecycle & signal shutdown | Present | mcp/__main__.py:69; mcp/__main__.py:115; tests/test_stdio.py:117 |
| Socket NDJSON transport with multi-client support | Present | mcp/socket_main.py:36; mcp/socket_main.py:67; tests/test_socket.py:147 |
| 1 MiB payload guard (STDIO & socket) | Present | mcp/transport.py:15; mcp/socket_main.py:110; tests/test_stdio.py:220; tests/test_socket.py:114 |
| `validate` alias accepted **and logs deprecation warning** | Divergent | mcp/stdio_main.py:22; docs/mcp_spec.md:94 |
| `validate_many` batching with MCP_MAX_BATCH | Missing | docs/mcp_spec.md:89; mcp/stdio_main.py:13 |
| Path traversal rejection & local-only schemas | Present | mcp/core.py:16; mcp/validate.py:130; tests/test_path_traversal.py:34 |
| Deterministic listings/errors/diff | Present | mcp/core.py:85; mcp/validate.py:162; mcp/diff.py:49; tests/test_submodule_integration.py:34; tests/test_validate.py:46 |
| `get_example` validation_failed path | Present | mcp/core.py:147; tests/test_validate.py:32 |
| Container runs non-root | Present | Dockerfile:24 |

## Transports
- STDIO is the default endpoint and rejects unsupported transports during setup (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- Socket mode reuses the dispatcher, honours `MCP_SOCKET_PATH`/`MCP_SOCKET_MODE`, spawns per-connection threads, and cleans up the filesystem entry (mcp/socket_main.py:34; mcp/socket_main.py:83; tests/test_socket.py:131).

## STDIO entrypoint & process model
- NDJSON framing reads one stripped line from stdin and writes one JSON frame per line (mcp/stdio_main.py:46; mcp/stdio_main.py:53).
- Blocking loop preserves request order and exits on `KeyboardInterrupt`; spec expects exit on stdin close (mcp/stdio_main.py:46).
- SIGTERM handling raises `KeyboardInterrupt` for graceful shutdown (mcp/__main__.py:92).
- Ready file writes `<pid> <ISO8601>` on readiness and is cleared on shutdown (mcp/__main__.py:69; mcp/__main__.py:115; tests/test_stdio.py:121).
- Logging stays on stderr; stdout carries frames only (mcp/stdio_main.py:53; mcp/__main__.py:104).

## Socket server (multi-client handling, perms, unlink, logs)
- Binds the configured path, applies `MCP_SOCKET_MODE` (default 0600), and listens with backlog for concurrent clients (mcp/socket_main.py:34; mcp/socket_main.py:36).
- Each connection runs in `_handle_connection` on its own thread, preserving per-connection ordering and applying the 1 MiB guard (mcp/socket_main.py:67; mcp/socket_main.py:95; tests/test_socket.py:147).
- Shutdown joins active threads, unlinks the socket path, and logs `mcp:shutdown mode=socket` (mcp/socket_main.py:39; mcp/socket_main.py:48; mcp/__main__.py:161).
- Readiness log includes mode, path, and schemas_dir as required (mcp/__main__.py:147; tests/test_socket.py:84).

## Golden request/response examples
| Method | Success frame | Error frame | Evidence |
| - | - | - | - |
| list_schemas | Present | — | tests/test_stdio.py:29 |
| get_schema | Present | Present | tests/test_validate.py:19; tests/test_validate.py:14 |
| validate_asset | Present | Present | tests/test_stdio.py:144; tests/test_stdio.py:17 |
| validate (alias) | Present (no deprecation log) | Present | mcp/stdio_main.py:22; tests/test_stdio.py:56 |
| get_example | Present | Present | tests/test_submodule_integration.py:47; tests/test_validate.py:32 |
| diff_assets | Present | — | tests/test_diff.py:11 |
| populate_backend | Present | Present | tests/test_backend.py:31; tests/test_backend.py:57 |
| Malformed JSON-RPC frame | — | Present | tests/test_stdio.py:175; tests/test_socket.py:102 |

## Payload size guard
| Method | STDIO guard | Socket guard | Evidence |
| - | - | - | - |
| JSON-RPC frame ingest | Present | Present | mcp/transport.py:15; mcp/socket_main.py:110; tests/test_stdio.py:220; tests/test_socket.py:114 |
| validate_asset payload | Present | Present | mcp/validate.py:114; tests/test_validate.py:56; mcp/socket_main.py:118 |
| populate_backend payload | Present | n/a (HTTP) | mcp/backend.py:38; tests/test_backend.py:65 |

## Schema validation contract
- `schema` parameter enforced at dispatch; missing or blank returns `validation_failed` (mcp/stdio_main.py:25; tests/test_stdio.py:17).
- `validate` alias routes to `validate_asset`, but no deprecation warning is emitted (mcp/stdio_main.py:22).
- Validation errors emit RFC6901 paths sorted deterministically (mcp/validate.py:159; mcp/validate.py:162; tests/test_validate.py:46).
- `validate_asset` uses local schema resolution, alias mapping, and payload limit enforcement (mcp/validate.py:47; mcp/validate.py:114; mcp/validate.py:130).

## Batching
| Shape | Cap enforcement | Evidence |
| - | - | - |
| validate_many | Missing | docs/mcp_spec.md:89; mcp/stdio_main.py:13 |

## Logging hygiene
- Startup logs include mode, socket path, and schemas_dir; timestamps are ISO-8601 in the ready file (mcp/__main__.py:147; mcp/__main__.py:75).
- stdout remains frame-only; stderr captures logs and exceptions (mcp/stdio_main.py:53; tests/test_stdio.py:42).

## Container & health
| Aspect | Status | Evidence |
| - | - | - |
| Non-root runtime | Present | Dockerfile:24 |
| Ready-file healthcheck | Present | docker-compose.yml:26 |
| Transport/env wiring | Present | docker-compose.yml:18 |

## Schema discovery & validation
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` override | Validated path; failure aborts startup | mcp/__main__.py:23; tests/test_entrypoint.py:81 |
| Submodule fallback | Uses libs directory when env absent | mcp/core.py:33; tests/test_submodule_integration.py:28 |
| Example listing | Deterministic ordering with optional filters | mcp/core.py:106; tests/test_env_discovery.py:35 |
| Schema alias inference | `$schemaRef` / filename heuristics | mcp/core.py:126; tests/test_backend.py:118 |

## Test coverage
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO loop & guard | ✅ | tests/test_stdio.py:29; tests/test_stdio.py:220 |
| Socket lifecycle & guard | ✅ | tests/test_socket.py:84; tests/test_socket.py:114 |
| Socket multi-client handling | ✅ | tests/test_socket.py:147 |
| Path traversal rejection | ✅ | tests/test_path_traversal.py:34 |
| Validation contract & ordering | ✅ | tests/test_validate.py:46 |
| Backend populate flows & limits | ✅ | tests/test_backend.py:28; tests/test_backend.py:65 |
| Diff determinism | ✅ | tests/test_diff.py:11 |
| Ready file & signals | ✅ | tests/test_entrypoint.py:54 |

## Dependencies & runtime
| Package | Used in | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Schema validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local registry | Optional | mcp/validate.py:9 |

## Environment variables
- `MCP_ENDPOINT`: defaults to `stdio`; invalid values raise setup failure (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- `MCP_SOCKET_PATH`: default `/tmp/mcp.sock`; used verbatim for binding (mcp/__main__.py:47; tests/test_socket.py:95).
- `MCP_SOCKET_MODE`: default `0600`; parsed as octal; invalid values error (mcp/__main__.py:52).
- `MCP_READY_FILE`: default `/tmp/mcp.ready`; blank disables ready file (mcp/__main__.py:61).
- `SYN_SCHEMAS_DIR`: required when submodule absent; must exist (mcp/__main__.py:24; tests/test_entrypoint.py:81).
- `SYN_EXAMPLES_DIR`: overrides example lookup; falls back otherwise (mcp/core.py:40).
- `SYN_BACKEND_URL`: enables backend POST; unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH`: normalized to leading slash (mcp/backend.py:17; tests/test_backend.py:46).

## Documentation accuracy
- README reflects the available transport scripts, socket option, and 1 MiB guard consistently with the spec (README.md:34; README.md:169; docs/mcp_spec.md:31).
- README still mentions `validate_many` as absent; spec now requires it—ensure docs are updated once implemented (docs/mcp_spec.md:89).

## Detected divergences
- `validate` alias lacks the required deprecation warning for v0.2.5 (mcp/stdio_main.py:22; docs/mcp_spec.md:94).

## Recommendations
- Implement `validate_many` with MCP_MAX_BATCH enforcement and add coverage for happy-path and batch-limit failures (docs/mcp_spec.md:89; tests directory).
- Emit and test a deprecation warning when the `validate` alias is used to align with v0.2.5 requirements (mcp/stdio_main.py:22).
- Add tests validating socket permission overrides and STDIO shutdown on stdin close to harden transport compliance (mcp/socket_main.py:34; mcp/stdio_main.py:46).
