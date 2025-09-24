## Summary of repo state
- STDIO and socket transports share the same JSON-RPC dispatch with 1 MiB guards and ready-file lifecycle validated by integration tests (mcp/stdio_main.py:47; mcp/socket_main.py:77; tests/test_stdio.py:92; tests/test_socket.py:84).
- Schema and example access stay within configured roots with deterministic listings and validation aliasing covered by tests (mcp/core.py:16; mcp/core.py:85; mcp/validate.py:152; tests/test_path_traversal.py:34; tests/test_submodule_integration.py:28).
- Validation, diff, and backend tools enforce ordering and payload limits while returning spec-compliant results (mcp/validate.py:106; mcp/diff.py:49; mcp/backend.py:38; tests/test_validate.py:46; tests/test_backend.py:65).

## Top gaps & fixes (3-5 bullets)
- Socket server handles only one client at a time; move to concurrent connection handling (e.g., threads or selectors) so it meets the spec’s multi-client guarantee (mcp/socket_main.py:32; mcp/socket_main.py:52; docs/mcp_spec.md:54).
- Add a regression test that opens two socket clients simultaneously to prevent future single-client regressions (tests/test_socket.py:95).
- Align README’s serving instructions with available scripts—`./up.sh` does not tail logs and `./serve.sh` is absent—so operators get accurate guidance (README.md:42; README.md:169; up.sh:6).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop with ordered replies | Present | mcp/stdio_main.py:47; tests/test_stdio.py:29 |
| Ready-file lifecycle & signal shutdown | Present | mcp/__main__.py:104; mcp/__main__.py:115; tests/test_entrypoint.py:54 |
| Socket NDJSON transport w/ multi-client support | Divergent | mcp/socket_main.py:32; mcp/socket_main.py:52; docs/mcp_spec.md:54 |
| 1 MiB payload guard (STDIO & socket) | Present | mcp/transport.py:15; mcp/socket_main.py:77; tests/test_stdio.py:220; tests/test_socket.py:114 |
| `validate` alias honored for validate_asset | Present | mcp/stdio_main.py:22; tests/test_stdio.py:70 |
| Schema/example traversal rejection | Present | mcp/core.py:16; tests/test_path_traversal.py:34 |
| Local-only `$ref` resolution via registry | Present | mcp/validate.py:52; mcp/validate.py:152 |
| Deterministic ordering for listings/errors/diff | Present | mcp/core.py:85; mcp/core.py:122; mcp/validate.py:162; mcp/diff.py:49; tests/test_submodule_integration.py:34; tests/test_validate.py:46 |
| `get_example` validation_failed path | Present | mcp/core.py:147; tests/test_validate.py:32 |
| `validate_many` optional batching | Optional | docs/mcp_spec.md:89; mcp/stdio_main.py:13 |
| Container runs non-root & ready healthcheck | Present | Dockerfile:24; docker-compose.yml:26 |

## Transports
- STDIO remains default and rejects unsupported endpoints during startup (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- Socket mode reuses the same dispatch and logging, but the server blocks on a single client connection until it closes (mcp/socket_main.py:52).

## STDIO server entrypoint & process model (bullets: NDJSON framing, blocking loop, signals, readiness file, shutdown semantics, stdout vs stderr)
- NDJSON framing: reads one stripped line per request and writes one JSON response per line (mcp/stdio_main.py:47; mcp/stdio_main.py:53).
- Blocking loop & ordering: `for line in sys.stdin` processes sequentially in FIFO order (mcp/stdio_main.py:47).
- Signals: SIGTERM is trapped and re-raised as `KeyboardInterrupt` so the loop exits gracefully (mcp/__main__.py:92).
- Ready file: writes `<pid> <ISO8601>` on readiness and removes it on exit (mcp/__main__.py:69; mcp/__main__.py:115; tests/test_stdio.py:121).
- Shutdown semantics: logs `mcp:shutdown mode=stdio` and restores prior handlers before exiting (mcp/__main__.py:113; mcp/__main__.py:118).
- stdout vs stderr: JSON-RPC frames go to stdout while logs go through `logging` to stderr (mcp/stdio_main.py:53; mcp/__main__.py:234).

## Socket server (if present) (bullets: UDS path, perms, multi-client handling, per-connection ordering, unlink on shutdown, readiness/shutdown logs)
- UDS path & perms: binds `MCP_SOCKET_PATH` and applies `MCP_SOCKET_MODE` (mcp/socket_main.py:29; mcp/socket_main.py:31; mcp/__main__.py:257).
- Multi-client handling: Divergent—`listen(1)` with synchronous `_serve_connection` blocks other clients until the current one disconnects (mcp/socket_main.py:32; mcp/socket_main.py:52).
- Per-connection ordering: responses stream in request order within a connection (mcp/socket_main.py:72; mcp/socket_main.py:85).
- Unlink on shutdown: socket file removed in `close()` and after shutdown (mcp/socket_main.py:35; mcp/socket_main.py:43; tests/test_socket.py:143).
- Readiness/shutdown logs & ready file: logs `mcp:ready mode=socket path=...` and clears ready file on close (mcp/__main__.py:147; mcp/__main__.py:161; tests/test_socket.py:84).

## Golden request/response examples (table: Method → Success frame Present/Missing/Divergent → Error frame Present/Missing/Divergent → Evidence)
| Method | Success frame | Error frame | Evidence |
| - | - | - | - |
| list_schemas | Present | — | tests/test_stdio.py:29; tests/fixtures/e2e_golden.jsonl:1 |
| get_schema | Present | Present | tests/test_validate.py:19; tests/test_validate.py:14 |
| validate_asset | Present | Present | tests/test_stdio.py:144; tests/test_stdio.py:17 |
| validate (alias) | Present | — (shares validate_asset errors) | tests/test_stdio.py:70 |
| get_example | Present | Present | tests/test_submodule_integration.py:47; tests/test_validate.py:32 |
| diff_assets | Present | — | tests/test_diff.py:11 |
| populate_backend | Present | Present | tests/test_backend.py:28; tests/test_backend.py:57 |
| Malformed JSON-RPC frame | — | Present | tests/test_stdio.py:175; tests/test_socket.py:102 |

## Payload size guard (table: Method → STDIO guard → Socket guard → Evidence)
| Method | STDIO guard | Socket guard | Evidence |
| - | - | - | - |
| Frame ingestion | Present | Present | mcp/transport.py:15; mcp/socket_main.py:77; tests/test_stdio.py:220; tests/test_socket.py:114 |
| validate_asset payload | Present | Present | mcp/validate.py:114; tests/test_validate.py:56; mcp/socket_main.py:85 |
| populate_backend payload | Present | n/a (HTTP only) | mcp/backend.py:38; tests/test_backend.py:65 |

## Schema validation contract (bullets: required schema param, alias handling, error ordering, explicit validate_asset behavior)
- Required schema param: dispatch rejects missing/empty schema with a `/schema` error before validation (mcp/stdio_main.py:25; tests/test_stdio.py:17).
- Alias handling: `validate` routes to `validate_asset` for backward compatibility (mcp/stdio_main.py:22; tests/test_stdio.py:70).
- Error ordering: validation errors are converted to RFC6901 pointers and sorted deterministically (mcp/validate.py:162; tests/test_validate.py:46).
- validate_asset behavior: enforces payload limit, strips `$schemaRef`, and resolves aliases locally (mcp/validate.py:114; mcp/validate.py:123; mcp/validate.py:130).

## Optional batching (if present) (table: Shape → Cap enforcement → Evidence)
| Shape | Cap enforcement | Evidence |
| - | - | - |
| validate_many | Optional (not implemented) | docs/mcp_spec.md:89; mcp/stdio_main.py:13 |

## Logging hygiene (bullets: stdout frames only; stderr logs/diagnostics; deterministic timestamps)
- stdout carries only JSON-RPC frames; tests assert structured responses without log noise (mcp/stdio_main.py:53; tests/test_stdio.py:42).
- stderr receives readiness and shutdown logs from `logging.info` (mcp/__main__.py:104; tests/test_entrypoint.py:58).
- Ready file timestamp is written in ISO-8601 UTC for external health probes (mcp/__main__.py:75; tests/test_stdio.py:127).

## Container & health (table: Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Status | Evidence |
| - | - | - |
| Non-root runtime | Present | Dockerfile:24 |
| Ready-file healthcheck | Present | docker-compose.yml:26 |
| Transport env passthrough (compose) | Present | docker-compose.yml:18 |
| Optional backend env passthrough | Present | docker-compose.yml:24 |

## Schema discovery & validation (table: Source → Mechanism → Evidence)
| Source | Mechanism | Evidence |
| - | - | - |
| `SYN_SCHEMAS_DIR` override | Absolute path validated before use | mcp/__main__.py:23 |
| Submodule fallback | Uses `libs/synesthetic-schemas` when env unset | mcp/core.py:33; tests/test_submodule_integration.py:28 |
| Example discovery | Component filter with deterministic sorting | mcp/core.py:106; tests/test_env_discovery.py:35 |
| Schema alias inference | `$schemaRef` and filename heuristics | mcp/core.py:126; tests/test_backend.py:118 |

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO loop & guard | ✅ | tests/test_stdio.py:29; tests/test_stdio.py:220 |
| Socket transport lifecycle | ✅ | tests/test_socket.py:45 |
| Path traversal rejection | ✅ | tests/test_path_traversal.py:34 |
| Validation contract | ✅ | tests/test_validate.py:46 |
| Backend populate flows | ✅ | tests/test_backend.py:28 |
| Diff determinism | ✅ | tests/test_diff.py:11 |
| Ready file & signals | ✅ | tests/test_entrypoint.py:54 |

## Dependencies & runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Schema validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local registry support | Optional | mcp/validate.py:9 |

## Environment variables (bullets: name, default, behavior when missing/invalid)
- `MCP_ENDPOINT` defaults to `stdio`; only `stdio` or `socket` accepted, otherwise startup fails (mcp/__main__.py:36; tests/test_entrypoint.py:95).
- `MCP_SOCKET_PATH` defaults to `/tmp/mcp.sock`; value is taken verbatim for socket binding (mcp/__main__.py:47; mcp/socket_main.py:29).
- `MCP_SOCKET_MODE` defaults to `0600`; invalid octal raises a setup failure (mcp/__main__.py:52).
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables ready-file writes (mcp/__main__.py:61).
- `SYN_SCHEMAS_DIR` must be an existing directory; missing directories abort startup (mcp/__main__.py:24; tests/test_entrypoint.py:81).
- `SYN_EXAMPLES_DIR` overrides example lookup; absent fallbacks to the submodule (mcp/core.py:40).
- `SYN_BACKEND_URL` gates backend POST support; unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH` is normalized to a leading slash before POST (mcp/backend.py:17; tests/test_backend.py:47).

## Documentation accuracy (bullets: README vs. docs/mcp_spec.md)
- README correctly calls out STDIO default, optional socket mode, and 1 MiB guard matching the spec (README.md:30; docs/mcp_spec.md:31).
- README references `./serve.sh` and claims `./up.sh` tails logs, but the repo only provides `up.sh` without log tailing, so the guide diverges from reality (README.md:42; README.md:169; up.sh:6).

## Detected divergences
- Socket transport blocks additional clients instead of supporting concurrent connections as required (mcp/socket_main.py:32; docs/mcp_spec.md:54).

## Recommendations
- Implement a multi-client socket server (e.g., thread-per-connection or selector-driven loop) to satisfy the concurrency requirement (mcp/socket_main.py:32; docs/mcp_spec.md:54).
- Add a test that connects two clients simultaneously to the socket transport to guard against regressions (tests/test_socket.py:95).
- Update README serving instructions to match the available scripts or add the missing helper so operators follow accurate steps (README.md:42; README.md:169; up.sh:6).
