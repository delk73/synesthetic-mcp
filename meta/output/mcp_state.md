## Summary of repo state
- Transports, lifecycle, and logging align with v0.2.7 readiness/shutdown invariants across STDIO, socket, and TCP (`mcp/__main__.py:185`, `mcp/__main__.py:304`, `tests/test_tcp.py:178`).
- Validation, diff, and backend features remain deterministic with enforced schema guards and sorted outputs (`mcp/validate.py:52`, `mcp/diff.py:16`, `tests/test_validate.py:46`).
- Documentation, env defaults, and container posture reflect the running system configuration (`README.md:35`, `.env.example:2`, `Dockerfile:24`).

## Top gaps & fixes (3-5 bullets)
- No spec deviations observed; keep running transport regression suite to guard multi-client ordering and shutdown logs (`tests/test_socket.py:340`, `tests/test_tcp.py:411`).
- Refresh the golden transcript whenever RPC contracts evolve to preserve deterministic IO (`tests/test_golden.py:45`, `tests/fixtures/golden.jsonl:1`).
- Maintain non-root container user when updating base images or CI tooling (`Dockerfile:24`, `tests/test_container.py:4`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB payload cap | Present | `mcp/transport.py:28`; `tests/test_stdio.py:355`; `tests/test_socket.py:185`; `tests/test_tcp.py:167` |
| Ready/shutdown logs include mode + address/path + dirs + ISO timestamp | Present | `mcp/__main__.py:185`; `mcp/__main__.py:234`; `mcp/__main__.py:304`; `tests/test_entrypoint.py:66`; `tests/test_tcp.py:178` |
| Ready file writes `<pid> <ISO8601>` and clears on exit | Present | `mcp/__main__.py:156`; `mcp/__main__.py:432`; `tests/test_stdio.py:210`; `tests/test_stdio.py:254` |
| Signal exits map to `-SIGINT`/`-SIGTERM` → 128+code | Present | `mcp/__main__.py:295`; `mcp/__main__.py:439`; `tests/test_entrypoint.py:105`; `tests/test_tcp.py:194` |
| `validate` alias warns and requires schema | Present | `mcp/stdio_main.py:23`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:68`; `tests/test_stdio.py:35` |
| `validate_many` enforces `MCP_MAX_BATCH` and payload guard | Present | `mcp/validate.py:92`; `mcp/validate.py:120`; `tests/test_validate.py:103`; `tests/test_validate.py:145` |
| Socket default perms 0600 and supports multi-client ordering | Present | `mcp/socket_main.py:27`; `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP multi-client ordering, guard, and mirrored shutdown logs | Present | `mcp/tcp_main.py:25`; `mcp/tcp_main.py:304`; `tests/test_tcp.py:272`; `tests/test_tcp.py:411` |
| Schema/example traversal blocked (local-only resolution) | Present | `mcp/core.py:18`; `mcp/core.py:62`; `tests/test_path_traversal.py:34`; `tests/test_path_traversal.py:61` |
| JSON-RPC errors reserved for malformed frames | Present | `mcp/transport.py:70`; `mcp/transport.py:100`; `tests/fixtures/golden.jsonl:10`; `tests/test_stdio.py:168` |
| Deterministic listings/diff ordering | Present | `mcp/core.py:53`; `mcp/diff.py:16`; `tests/test_submodule_integration.py:34`; `tests/test_diff.py:16` |

## Transports
- Shared dispatcher handles schema/diff/backend tooling across STDIO, socket, and TCP (`mcp/stdio_main.py:14`, `mcp/socket_main.py:53`, `mcp/tcp_main.py:56`).
- Transport loops stream NDJSON responses and propagate payload guards before decode (`mcp/transport.py:26`, `mcp/socket_main.py:110`, `mcp/tcp_main.py:113`).
- Tests exercise end-to-end round trips for each transport including invalid frames (`tests/test_stdio.py:41`, `tests/test_socket.py:150`, `tests/test_tcp.py:130`).

## STDIO entrypoint & process model
- Entry point logs readiness, writes ready file, processes STDIO frames, and mirrors shutdown logs (`mcp/__main__.py:185`, `mcp/__main__.py:204`).
- STDIO loop honors EOF on stdin and removes the ready file on termination (`tests/test_stdio.py:249`, `tests/test_stdio.py:254`).
- CLI `--validate` path infers schema and returns deterministic exit codes (`mcp/__main__.py:323`, `tests/test_entrypoint.py:210`).

## Socket server (multi-client handling, perms, unlink, logs)
- Server pre-creates/unlinks socket path, enforces chmod, and joins client threads on shutdown (`mcp/socket_main.py:27`, `mcp/socket_main.py:49`).
- Tests assert 0600 permissions, payload guard, and readiness/shutdown logging (`tests/test_socket.py:146`, `tests/test_socket.py:278`).
- Multi-client concurrency preserves per-client ordering and continues serving after peer disconnects (`tests/test_socket.py:346`, `tests/test_socket.py:388`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP server binds requested/ephemeral ports, tracks bound address, and closes sockets with thread draining (`mcp/tcp_main.py:25`, `mcp/tcp_main.py:54`).
- Tests confirm readiness/shutdown logs, SIGINT/SIGTERM exit behavior, and 1 MiB guard enforcement (`tests/test_tcp.py:117`, `tests/test_tcp.py:167`, `tests/test_tcp.py:254`).
- Multi-client workload threads verify ordered responses per connection even under concurrent access (`tests/test_tcp.py:333`, `tests/test_tcp.py:387`).

## Lifecycle signals
- SIGINT/SIGTERM install `_SignalShutdown` sentinel so exit codes propagate uniformly across transports (`mcp/__main__.py:78`, `mcp/__main__.py:295`).
- Tests assert negative signal codes from processes and ready-file cleanup under signals (`tests/test_entrypoint.py:105`, `tests/test_tcp.py:194`).

## Shutdown logging invariant
- Shutdown logs reuse the same mode/address metadata before closing transports (`mcp/__main__.py:204`, `mcp/__main__.py:252`, `mcp/__main__.py:304`).
- Tests compare ready vs shutdown fields to guarantee parity and timing (`tests/test_entrypoint.py:85`, `tests/test_socket.py:283`).

## Golden request/response examples
- Golden harness replays list/get/validate/alias/batch/example/diff/backend/malformed cases for regression coverage (`tests/test_golden.py:45`, `tests/fixtures/golden.jsonl:1`).
- STDERR expectations verify deprecation warnings remain surfaced (`tests/fixtures/golden.jsonl:4`).

## Payload size guard
- Transport parse layer caps payload prior to JSON decode, emitting `payload_too_large` results (`mcp/transport.py:28`, `mcp/transport.py:75`).
- Validation paths also enforce MAX_BYTES when assets/batches overflow (`mcp/validate.py:62`, `tests/test_validate.py:145`).
- Backend populate rejects oversize posts with matching error semantics (`mcp/backend.py:30`, `tests/test_backend.py:56`).

## Schema validation contract
- `validate_asset` requires schema, strips helper fields, and sorts error pointers deterministically (`mcp/validate.py:52`, `mcp/validate.py:83`).
- Example retrieval revalidates payloads and surfaces validation failures with same shape (`mcp/core.py:64`, `tests/test_validate.py:32`).
- Path traversal attempts raise `validation_failed` errors (`mcp/core.py:18`, `tests/test_path_traversal.py:34`).

## Batching
- `_max_batch` reads `MCP_MAX_BATCH`, rejects invalid/zero values, and `validate_many` enforces limit + per-item validation (`mcp/validate.py:92`, `mcp/validate.py:113`).
- Tests cover mixed results, limit enforcement, and oversize asset handling in batches (`tests/test_validate.py:94`, `tests/test_validate.py:120`, `tests/test_validate.py:150`).

## Logging hygiene
- `_log_event` writes machine-readable logs to stderr with ISO-8601 timestamps (`mcp/__main__.py:60`, `mcp/__main__.py:185`).
- Runtime warnings (deprecated alias, ready file issues) log with structured key/value fields (`mcp/stdio_main.py:26`, `mcp/__main__.py:166`).
- Tests assert absence of unsolicited stdout noise beyond JSON-RPC frames (`tests/test_stdio.py:120`, `tests/test_golden.py:63`).

## Container & health
- Docker image installs dependencies before dropping privileges to `USER mcp` (`Dockerfile:16`, `Dockerfile:27`).
- Test suite ensures non-root user remains configured (`tests/test_container.py:4`).
- Ready-file lifecycle supports health checks across transports (`mcp/__main__.py:156`, `tests/test_tcp.py:252`).

## Schema discovery & validation
- Discovery prefers env overrides then submodule, with deterministic ordering of listings (`mcp/core.py:41`, `mcp/core.py:53`).
- Tests verify env override, submodule fallback, and deterministic ordering for schemas/examples (`tests/test_env_discovery.py:29`, `tests/test_submodule_integration.py:34`).
 - Schema inference for examples supports alias mapping (`mcp/core.py:126`, `tests/test_backend.py:103`).

## Test coverage
- Pytest suite covers transports, validation, diff, backend, lifecycle, container, and golden replay (`tests/test_stdio.py:41`, `tests/test_tcp.py:63`, `tests/test_backend.py:21`, `tests/test_golden.py:45`).
- Integration scripts leverage fixtures for schemas/examples ensuring reproducibility (`tests/fixtures/golden.jsonl:1`, `tests/fixtures/schemas/asset.json`).

## Dependencies & runtime
- Minimal runtime deps constrained to `jsonschema` and `httpx`, with optional `referencing` for local registry support (`requirements.txt:1`, `mcp/validate.py:10`).
- Tests rely on `pytest` only; no hidden runtime extras (`requirements.txt:3`, `pytest.ini:1`).

## Environment variables
- README enumerates transport, lifecycle, backend, and batching envs consistent with implementation defaults (`README.md:94`, `README.md:102`, `README.md:106`).
- `.env.example` mirrors defaults for quick setup (`.env.example:2`, `.env.example:9`).
- Code reads env values with validation and fallbacks (`mcp/__main__.py:103`, `mcp/backend.py:18`, `mcp/validate.py:92`).

## Documentation accuracy
- README features align with implemented transports, payload guard, and alias behavior (`README.md:35`, `README.md:177`).
- Spec reference points to pinned `docs/mcp_spec.md` version v0.2.7 consistent with audit scope (`README.md:179`, `docs/mcp_spec.md:1`).

## Detected divergences
- None.

## Recommendations
- Preserve logging/ready invariants by keeping structured stderr assertions in transport tests (`tests/test_entrypoint.py:66`, `tests/test_socket.py:278`).
- Continue validating backend interactions via mocked clients to avoid regressions in optional feature path (`tests/test_backend.py:31`, `tests/test_backend.py:96`).
- Monitor optional `referencing` dependency import path to ensure graceful degradation remains covered (`mcp/validate.py:10`, `tests/test_validate.py:19`).
