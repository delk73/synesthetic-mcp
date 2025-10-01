## Summary of repo state
- JSON-RPC parsing now rejects frames without `jsonrpc: "2.0"`, ensuring transports only run compliant requests (`mcp/transport.py:32`; `tests/test_stdio.py:312`).
- SIGTERM paths across STDIO/socket/TCP verify ready-file cleanup and negative exit codes in addition to the existing SIGINT checks (`tests/test_entrypoint.py:87`; `tests/test_socket.py:209`; `tests/test_tcp.py:180`).
- Transport, validation, diff, and backend flows remain deterministic with shared 1 MiB guards, traversal fences, and golden coverage unchanged (`mcp/transport.py:26`; `mcp/validate.py:176`; `tests/test_golden.py:18`).

## Top gaps & fixes (3-5 bullets)
- All previously identified audit gaps are closed; keep regression suite in place for future transport additions.
- Monitor sandbox limitations that can skip socket/TCP tests; they already fall back to skips when the environment blocks binds (`tests/test_socket.py:233`; `tests/test_tcp.py:217`).
- Continue running the golden replay to guard against regressions in error shaping and logging (`tests/test_golden.py:18`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_socket.py:141`; `tests/test_tcp.py:142` |
| Ready/shutdown logs include mode + address/path + ISO timestamps | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:65`; `tests/test_tcp.py:160` |
| Ready file records `<pid> <ISO8601>` and is cleared on shutdown | Present | `mcp/__main__.py:139`; `tests/test_stdio.py:208`; `tests/test_socket.py:253` |
| Signal shutdown exits use `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:176`; `tests/test_entrypoint.py:131`; `tests/test_socket.py:253`; `tests/test_tcp.py:236` |
| Socket 0600 perms + multi-client ordering | Present | `mcp/socket_main.py:35`; `tests/test_socket.py:109`; `tests/test_socket.py:259` |
| TCP multi-client ordering + readiness logs | Present | `mcp/tcp_main.py:69`; `tests/test_tcp.py:111`; `tests/test_tcp.py:226` |
| Semantic validation errors return in JSON-RPC `result` | Present | `mcp/transport.py:85`; `tests/test_stdio.py:320`; `tests/test_socket.py:144` |
| `validate` alias warns and requires `schema` | Present | `mcp/stdio_main.py:24`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:138` |
| `validate_many` honors `MCP_MAX_BATCH` and payload cap | Present | `mcp/validate.py:199`; `tests/test_validate.py:118`; `tests/test_validate.py:145` |
| Schema/example traversal guards reject escapes | Present | `mcp/core.py:16`; `mcp/core.py:61`; `tests/test_path_traversal.py:31` |
| Golden suite covers list/get/validate/diff/backend/malformed | Present | `tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1` |
| Docs + metadata reflect v0.2.7 with TCP guard guidance | Present | `README.md:2`; `README.md:36`; `README.md:177`; `docs/mcp_spec.md:30` |

## Transports
- JSON-RPC dispatcher now validates the `jsonrpc` version before dispatching, keeping all transports aligned with the spec (`mcp/transport.py:32`).
- Socket/TCP SIGTERM tests assert readiness logs, shutdown logs, exit codes, and ready-file cleanup; they skip gracefully when the sandbox forbids socket binds (`tests/test_socket.py:209`; `tests/test_tcp.py:180`).

## STDIO entrypoint & process model
- STDIO SIGTERM coverage now checks ready-file lifecycle in addition to exit codes (`tests/test_entrypoint.py:118`).
- STDIO loop still exits on stdin close with per-frame flushing and alias warnings (`mcp/stdio_main.py:51`; `tests/test_stdio.py:126`).

## Socket server (multi-client handling, perms, unlink, logs)
- New SIGTERM test verifies cleanup of the unix-domain socket and ready file while retaining existing multi-client ordering tests (`tests/test_socket.py:209`; `tests/test_socket.py:259`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP SIGTERM test covers ready/shutdown logs, exit code, and ready-file removal, complementing existing multi-client coverage (`tests/test_tcp.py:180`; `tests/test_tcp.py:233`).

## Lifecycle signals
- `_SignalShutdown` handling now proved for both SIGINT and SIGTERM across all transports with deterministic cleanup assertions (`mcp/__main__.py:176`; `tests/test_entrypoint.py:131`; `tests/test_socket.py:253`; `tests/test_tcp.py:236`).

## Golden request/response examples
- Golden replay remains unchanged and continues to guard list/get/diff/validate flows and malformed frames (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

## Payload size guard
- Guard logic unchanged; oversize frames and payloads fail fast across transports, validation, and backend populate APIs (`mcp/transport.py:26`; `mcp/validate.py:128`; `mcp/backend.py:38`; `tests/test_stdio.py:330`).

## Schema validation contract
- Alias folding, `$schemaRef` stripping, deterministic error ordering, and invalid example reporting remain covered by regression tests (`mcp/validate.py:137`; `mcp/validate.py:176`; `tests/test_validate.py:32`).

## Batching
- `validate_many` enforces batch limits and propagates per-item payload guard results as before (`mcp/validate.py:199`; `tests/test_validate.py:118`).

## Logging hygiene
- Logs continue to include mode, host/path, schema/example dirs, and ISO timestamps on readiness/shutdown; STDIO keeps JSON-RPC frames on stdout only (`mcp/__main__.py:55`; `tests/test_entrypoint.py:65`; `tests/test_socket.py:244`).

## Container & health
- Docker image still runs non-root and pairs with ready-file health checks tested via the transport suites (`Dockerfile:24`; `tests/test_socket.py:253`).

## Schema discovery & validation
- Env overrides and traversal protections remain deterministic, with submodule fallback intact (`mcp/core.py:27`; `mcp/core.py:69`; `tests/test_env_discovery.py:29`; `tests/test_path_traversal.py:31`).

## Test coverage
- Added JSON-RPC version unit test plus SIGTERM transport tests; existing suites continue to cover multi-client ordering, alias warnings, backend flows, and golden behaviors (`tests/test_stdio.py:312`; `tests/test_socket.py:209`; `tests/test_tcp.py:180`; `tests/test_backend.py:23`).

## Dependencies & runtime
- Runtime/test dependencies unchanged (`requirements.txt:1`; `Dockerfile:16`).

## Environment variables
- Transport env validation and ready-file overrides now exercised for both SIGINT and SIGTERM cases (`mcp/__main__.py:86`; `tests/test_entrypoint.py:118`; `tests/test_socket.py:233`; `tests/test_tcp.py:222`).

## Documentation accuracy
- README and spec stay aligned with TCP guard updates and v0.2.7 metadata (`README.md:36`; `README.md:177`; `docs/mcp_spec.md:30`).

## Detected divergences
- None.

## Recommendations
- Maintain the new JSON-RPC compliance guard by keeping the unit test in CI and extending similar checks if new transports are added (`mcp/transport.py:32`; `tests/test_stdio.py:312`).
- Watch for platform skips in socket/TCP SIGTERM tests and document host requirements when running in restricted sandboxes (`tests/test_socket.py:234`; `tests/test_tcp.py:219`).
- Continue to run the full pytest suite, including golden replay, before releasing new transport features (`tests/test_golden.py:18`).
