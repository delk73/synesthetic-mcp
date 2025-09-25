**Summary of repo state**
- STDIO, socket, and TCP share an NDJSON dispatcher with a 1 MiB guard and ISO ready/shutdown logging validated end-to-end (`mcp/transport.py:26`; `mcp/__main__.py:54`; `tests/test_stdio.py:101`; `tests/test_socket.py:288`; `tests/test_tcp.py:311`).
- Schema discovery, validation, diffing, and traversal checks remain deterministic with alias folding and sorted outputs (`mcp/core.py:69`; `mcp/validate.py:176`; `mcp/diff.py:22`; `tests/test_validate.py:46`; `tests/test_path_traversal.py:32`).
- Backend population, batching, and golden STDIO flows cover success/error paths including alias warnings and HTTP failures (`mcp/backend.py:34`; `mcp/validate.py:200`; `tests/test_backend.py:172`; `tests/test_golden.py:18`).

**Top gaps & fixes**
- Update README payload-guard text to state that TCP is also protected so docs match implementation (`README.md:36`; `README.md:147`; `mcp/tcp_main.py:114`).
- Extend "Serving Locally" guidance with a TCP client example (e.g., `nc`) to highlight the new transport exercised in tests (`README.md:172`; `tests/test_tcp.py:296`).
- Note in README that SIGINT shutdowns return `-SIGINT`, matching the lifecycle test expectation (`README.md:174`; `tests/test_entrypoint.py:80`).

**Alignment with mcp_spec.md**
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop with 1 MiB guard | Present | `mcp/transport.py:26`; `tests/test_stdio.py:56` |
| Socket multi-client ordering + 0600 perms | Present | `mcp/socket_main.py:18`; `tests/test_socket.py:108`; `tests/test_socket.py:228` |
| TCP transport logs + guard + alias coverage | Present | `mcp/tcp_main.py:25`; `tests/test_tcp.py:381`; `tests/test_tcp.py:402` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:134`; `tests/test_tcp.py:317` |
| `validate` alias warns to stderr | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:137` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:200`; `tests/test_validate.py:118` |
| Backend HTTPError → 503 mapping | Present | `mcp/backend.py:55`; `tests/test_backend.py:172` |
| Container runs as non-root | Present | `Dockerfile:25` |
| Docs state guard limited to STDIO/socket | Divergent | `README.md:36`; `README.md:147`; `mcp/tcp_main.py:114` |

**Transports**
- STDIO is default and processes newline-delimited JSON-RPC, returning deterministic results and exiting when stdin closes (`mcp/stdio_main.py:18`; `tests/test_stdio.py:143`).
- Socket server enforces payload limits, spawns per-client threads, and removes the socket file on shutdown with tests covering concurrent clients (`mcp/socket_main.py:17`; `tests/test_socket.py:228`; `tests/test_socket.py:294`).
- TCP server mirrors socket behavior, supports dynamic ports, and preserves ordering across multiple clients (`mcp/tcp_main.py:25`; `tests/test_tcp.py:210`; `tests/test_tcp.py:296`).

**STDIO entrypoint & process model**
- Readiness and shutdown logs include mode, schema/example directories, and ISO timestamps before signals are handled (`mcp/__main__.py:120`; `tests/test_entrypoint.py:62`).
- SIGINT maps to SIGTERM to guarantee cleanup, and ready-file writes `<pid> <ISO8601>` before unlinking (`mcp/__main__.py:69`; `mcp/__main__.py:134`; `tests/test_entrypoint.py:80`).

**Socket server (multi-client handling, perms, unlink, logs)**
- Server binds, chmods, and listens with a configurable mode defaulting to 0600, and integration tests assert both the file mode and unlink on shutdown (`mcp/socket_main.py:24`; `tests/test_socket.py:108`; `tests/test_socket.py:173`).
- Multi-client test ensures requests can interleave while maintaining per-connection ordering (`tests/test_socket.py:228`).

**TCP server (binding, perms, multi-client, shutdown logs)**
- TCP server binds requested host/port (or OS-assigned), logs ready/shutdown with bound port, and closes clients gracefully (`mcp/tcp_main.py:25`; `tests/test_tcp.py:447`).
- Multi-client threads confirm ordering and continued service after concurrent sessions (`tests/test_tcp.py:233`; `tests/test_tcp.py:296`).

**Golden request/response examples**
- Golden replay exercises schema listing/get, validate/alias, batch validation, example retrieval (success + invalid), diff, backend populate, and malformed input (`tests/test_golden.py:18`; `tests/fixtures/golden.jsonl:1`).

**Payload size guard**
- Payload guard enforced before parsing across transports and validation/backends, with tests covering oversize requests and assets (`mcp/transport.py:26`; `mcp/validate.py:128`; `mcp/backend.py:42`; `tests/test_validate.py:56`; `tests/test_backend.py:38`).

**Schema validation contract**
- Alias folding and `$schemaRef` stripping implemented with deterministic error ordering (`mcp/validate.py:17`; `mcp/validate.py:136`; `tests/test_validate.py:46`).
- Path traversal safeguards prevent schemas/examples outside configured roots (`mcp/core.py:16`; `tests/test_path_traversal.py:31`).

**Batching**
- `validate_many` enforces limits from `MCP_MAX_BATCH`, returns per-item results, and handles oversize payloads (`mcp/validate.py:200`; `tests/test_validate.py:118`; `tests/test_validate.py:145`).

**Logging hygiene**
- `_log_event` emits ISO timestamps and key fields, and startup logs stay on stderr while stdout only carries JSON-RPC frames (`mcp/__main__.py:54`; `tests/test_stdio.py:101`).

**Container & health**
- Docker image installs dependencies, drops to `USER mcp`, and compose health check watches the ready file (`Dockerfile:25`; `docker-compose.yml:35`).

**Schema discovery & validation**
- Env overrides determine schema/example roots with deterministic listings and inferred schema names for examples (`mcp/core.py:27`; `mcp/core.py:126`; `tests/test_env_discovery.py:32`).

**Test coverage**
- Transport suites cover guards, alias warnings, multi-client scenarios, ready file cleanup, and TCP validate flows (`tests/test_stdio.py:105`; `tests/test_socket.py:228`; `tests/test_tcp.py:389`).
- Backend, diff, batching, traversal, and golden tests keep deterministic behavior under regression (`tests/test_backend.py:172`; `tests/test_diff.py:11`; `tests/test_path_traversal.py:32`).

**Dependencies & runtime**
- Runtime pinned to `jsonschema`, `httpx`, and `pytest`, all installed in the container (`requirements.txt:1`; `Dockerfile:12`).

**Environment variables**
- Transport, ready-file, and batch env vars are validated and influence behavior, with tests covering invalid endpoint and env overrides (`mcp/__main__.py:81`; `mcp/validate.py:27`; `tests/test_entrypoint.py:94`; `tests/test_env_discovery.py:29`).

**Documentation accuracy**
- Spec doc reflects v0.2.6 transport/logging additions (`docs/mcp_spec.md:12`).
- README still scopes the payload guard to STDIO/socket, missing TCP mention (`README.md:36`; `README.md:147`).

**Detected divergences**
- Only documentation gap: README under-reports TCP coverage of the 1 MiB guard (`README.md:36`; `mcp/tcp_main.py:114`).

**Recommendations**
- Clarify README payload guard text and error model bullets to include TCP, matching code/tests (`README.md:36`; `README.md:147`; `tests/test_tcp.py:381`).
- Add a TCP connection example (e.g., `nc host port`) under Serving Locally to surface the new transport (`README.md:172`; `tests/test_tcp.py:296`).
- Mention SIGINT exit semantics so operators expect `-SIGINT` exit codes after signal-driven shutdowns (`README.md:174`; `tests/test_entrypoint.py:80`).
