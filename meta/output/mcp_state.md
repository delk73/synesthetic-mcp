### Summary of repo state
- Shared NDJSON dispatcher applies the 1 MiB guard across STDIO, socket, and TCP while ready/shutdown logs and ready-file cleanup stay consistent under test (`mcp/transport.py:26`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:113`; `mcp/__main__.py:165`; `tests/test_stdio.py:189`; `tests/test_socket.py:100`; `tests/test_tcp.py:90`).
- Validation, discovery, diff, and backend flows remain deterministic with guarded paths, alias handling, and payload checks validated against fixtures (`mcp/validate.py:16`; `mcp/core.py:44`; `mcp/diff.py:42`; `mcp/backend.py:38`; `tests/test_validate.py:56`; `tests/test_path_traversal.py:34`; `tests/test_backend.py:56`).
- Spec/docs/docker assets reflect the v0.2.6 transport matrix and non-root container defaults (`docs/mcp_spec.md:13`; `README.md:35`; `docker-compose.yml:19`; `.env.example:1`; `Dockerfile:24`).

### Top gaps & fixes (3-5 bullets)
- Update the README feature list to call out that the 1 MiB guard covers TCP as well as STDIO/socket, matching the transport tests (`README.md:36`; `tests/test_tcp.py:135`).
- Adjust the README Error Model text so “payload too large” is described as a cross-transport guard rather than STDIO-only (`README.md:138`; `mcp/tcp_main.py:113`).
- Add a quick Serving Locally example for connecting to the TCP transport (e.g., `nc`) to showcase the new endpoint alongside list/validate coverage (`README.md:147`; `tests/test_tcp.py:104`).

### Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO dispatcher, ready file, and guard | Present | `mcp/transport.py:26`; `mcp/__main__.py:165`; `tests/test_stdio.py:189` |
| Socket transport (chmod 0600, multi-client, cleanup) | Present | `mcp/socket_main.py:27`; `mcp/socket_main.py:35`; `tests/test_socket.py:107`; `tests/test_socket.py:175` |
| TCP transport readiness, validate round-trip, concurrency | Present | `mcp/tcp_main.py:56`; `tests/test_tcp.py:135`; `tests/test_tcp.py:210` |
| Ready/shutdown logs include mode + dirs + ISO timestamp | Present | `mcp/__main__.py:165`; `tests/test_entrypoint.py:62` |
| Payload guard across transports and backend | Present | `mcp/tcp_main.py:113`; `mcp/backend.py:38`; `tests/test_backend.py:56` |
| Semantic errors resolved inside JSON-RPC result payloads | Present | `mcp/transport.py:77`; `tests/test_socket.py:120` |
| `validate` alias accepted with warning | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:118` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:167`; `tests/test_validate.py:118` |
| Backend HTTPError maps to `backend_error` 503 | Present | `mcp/backend.py:60`; `tests/test_backend.py:172` |
| Container drops root before serving | Present | `Dockerfile:24` |

### Transports
- STDIO remains the default, reusing the shared dispatcher and ready-file lifecycle before restoring signal handlers (`mcp/__main__.py:157`; `tests/test_stdio.py:201`).
- Socket server unlinks stale paths, applies the configured mode, and serves each client on a thread with deterministic ordering tests (`mcp/socket_main.py:27`; `tests/test_socket.py:175`).
- TCP server binds the requested or ephemeral port with `SO_REUSEADDR`, serves concurrent clients, and reports the bound host/port in logs (`mcp/tcp_main.py:25`; `tests/test_tcp.py:210`; `tests/test_tcp.py:492`).
- No HTTP/gRPC transports exist, aligning with the roadmap-only guidance (`mcp/__main__.py:81`; `docs/mcp_spec.md:9`).

### STDIO entrypoint & process model
- `_run_stdio` writes `<pid> <ISO8601>` to the ready file, logs readiness/shutdown, and cleans up regardless of exit path (`mcp/__main__.py:157`; `mcp/__main__.py:170`; `tests/test_stdio.py:201`).
- `--validate` CLI mode loads JSON, infers schema, and returns deterministic exit codes with schema echoed in the payload (`mcp/__main__.py:299`; `tests/test_entrypoint.py:130`).
- `validate` alias routes to `validate_asset` while emitting the deprecation warning on stderr (`mcp/stdio_main.py:23`; `tests/test_stdio.py:118`).

### Socket server (multi-client handling, perms, unlink, logs)
- `SocketServer.start()` removes stale sockets, binds, and `chmod`s to the requested mode before listening (`mcp/socket_main.py:27`; `mcp/socket_main.py:35`).
- Connections stream NDJSON with guard checks and close cleanup that joins client threads and unlinks the path (`mcp/socket_main.py:53`; `mcp/socket_main.py:95`).
- Tests assert ISO ready/shutdown logs, permission mode 0600, multi-client ordering, and ready-file deletion (`tests/test_socket.py:101`; `tests/test_socket.py:107`; `tests/test_socket.py:175`).

### TCP server (binding, perms, multi-client, shutdown logs)
- `TCPServer.start()` binds host/port, exposes the bound address, and closes clients with shutdown protection (`mcp/tcp_main.py:25`; `mcp/tcp_main.py:44`).
- Integration tests validate payload guard, schema requests, alias warnings, multi-client ordering, and shutdown logs (`tests/test_tcp.py:135`; `tests/test_tcp.py:210`; `tests/test_tcp.py:331`).
- Ephemeral port flow logs the actual bound port and clears ready files on exit (`tests/test_tcp.py:492`; `tests/test_tcp.py:523`).

### Golden request/response examples
- Golden replay drives list/get/validate/diff/backend/malformed flows with expected responses and stderr alias warnings (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

### Payload size guard
- Transport and validation layers enforce `MAX_BYTES` before parsing or POSTing (`mcp/transport.py:26`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:113`; `mcp/validate.py:56`; `mcp/backend.py:38`).
- Tests craft oversized frames across STDIO, socket, TCP, batch validation, and backend populate to assert `payload_too_large` responses (`tests/test_stdio.py:189`; `tests/test_socket.py:137`; `tests/test_tcp.py:135`; `tests/test_validate.py:145`; `tests/test_backend.py:56`).

### Schema validation contract
- `validate_asset` requires a non-empty schema, resolves aliases, strips `$schemaRef`, and sorts error pointers deterministically (`mcp/validate.py:90`; `mcp/validate.py:130`).
- Path traversal and missing schema cases return `validation_failed` with targeted errors, exercised across API and transport tests (`tests/test_stdio.py:27`; `tests/test_path_traversal.py:34`; `tests/test_validate.py:66`).

### Batching
- `validate_many` enforces `MCP_MAX_BATCH`, returns `unsupported` with the limit, and propagates per-item errors (`mcp/validate.py:167`).
- Tests override the batch limit and assert both limit metadata and oversized entry handling (`tests/test_validate.py:118`; `tests/test_validate.py:150`).

### Logging hygiene
- `_log_event` records mode, location, and directories with ISO timestamps for ready/shutdown across transports (`mcp/__main__.py:165`; `mcp/__main__.py:181`).
- Integration tests read stderr to confirm timestamps, directories, and shutdown coverage while stdout carries JSON-RPC frames only (`tests/test_entrypoint.py:62`; `tests/test_socket.py:100`; `tests/test_tcp.py:90`; `tests/test_golden.py:45`).

### Container & health
- Docker image installs dependencies, adds user `mcp`, and switches to the non-root user before executing (`Dockerfile:23`; `Dockerfile:27`).
- Compose `serve` service exposes transport env vars, mounts `/tmp` for ready-file health checks, and ships a file-based health probe (`docker-compose.yml:19`; `docker-compose.yml:30`; `docker-compose.yml:34`).

### Schema discovery & validation
- Listings gather schemas/examples from env overrides or the submodule with deterministic sorting, rejecting traversal attempts (`mcp/core.py:44`; `mcp/core.py:70`; `tests/test_env_discovery.py:32`; `tests/test_path_traversal.py:34`).
- Submodule integration test validates that examples load and pass validation when the fixtures are present (`tests/test_submodule_integration.py:28`).

### Test coverage
- STDIO subprocess tests cover alias warning, ready-file lifecycle, and oversized frames (`tests/test_stdio.py:66`; `tests/test_stdio.py:189`).
- Socket and TCP integration suites exercise readiness logs, multi-client concurrency, payload guards, alias warnings, and shutdown cleanup (`tests/test_socket.py:175`; `tests/test_tcp.py:210`; `tests/test_tcp.py:331`).
- Backend, diff, traversal, batching, and golden flows are covered by targeted unit and integration tests (`tests/test_backend.py:28`; `tests/test_diff.py:4`; `tests/test_path_traversal.py:34`; `tests/test_validate.py:118`; `tests/test_golden.py:18`).

### Dependencies & runtime
- Runtime deps are restricted to `jsonschema` and `httpx`, with `pytest` for tests and optional `referencing` guarded at import (`requirements.txt:1`; `mcp/validate.py:8`; `mcp/backend.py:7`; `mcp/validate.py:10`).

### Environment variables
- CLI validates transport env vars (`MCP_ENDPOINT`, socket path/mode, TCP host/port) and surfaces errors before startup (`mcp/__main__.py:81`; `mcp/__main__.py:95`; `mcp/__main__.py:118`).
- README, Compose, and `.env.example` document the transport, backend, and batching env knobs with defaults (`README.md:94`; `docker-compose.yml:19`; `.env.example:1`).

### Documentation accuracy
- README already describes transports and env vars but still frames the payload guard as “STDIO/socket” only instead of including TCP (`README.md:36`; `README.md:138`).

### Detected divergences
- None; only STDIO/socket/TCP transports are implemented per spec with consistent behavior across docs and tests (`mcp/__main__.py:81`; `docs/mcp_spec.md:13`).

### Recommendations
- Refresh README feature and error-model descriptions so the 1 MiB guard is documented for all transports, matching the TCP guard implementation and tests (`README.md:36`; `README.md:138`; `tests/test_tcp.py:135`).
- Extend the Serving Locally section with a brief TCP connection example (e.g. `nc <host> <port>`) to demonstrate the new transport beyond STDIO/socket (`README.md:147`; `tests/test_tcp.py:104`).
- Keep the existing integration suites in CI to ensure the guard, alias warning, and backend error flows remain covered across transports (`tests/test_stdio.py:118`; `tests/test_socket.py:137`; `tests/test_backend.py:172`).
