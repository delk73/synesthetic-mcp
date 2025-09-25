### Summary of repo state
- Core transports share the JSON-RPC dispatcher with a 1 MiB guard and emit ISO ready/shutdown logs plus ready-file cleanup under test (`mcp/transport.py:26`; `mcp/__main__.py:165`; `tests/test_stdio.py:171`; `tests/test_socket.py:155`; `tests/test_tcp.py:153`).
- Validation, diff, and discovery stay deterministic with traversal guards and alias handling, reinforced by tests against the submodule fixtures (`mcp/validate.py:92`; `mcp/diff.py:12`; `mcp/core.py:44`; `tests/test_validate.py:32`; `tests/test_submodule_integration.py:33`).
- Backend populate honors payload limits and optional validation before POSTing, while Compose/README/document TCP and socket usage consistently (`mcp/backend.py:45`; `README.md:35`; `docker-compose.yml:21`; `docs/mcp_spec.md:13`).
- Golden STDIO replay covers list/get/validate/diff/backend/malformed flows and asserts alias warnings on stderr (`tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1`).

### Top gaps & fixes (3-5 bullets)
- Add a TCP integration request that exercises `validate_asset` (or alias) to satisfy the v0.2.6 audit clause requiring validate coverage (`docs/mcp_spec.md:13`; `tests/test_tcp.py:108`).
- Assert the Unix socket mode (default 0600) after startup to prove least-privilege defaults in CI (`mcp/socket_main.py:35`; `tests/test_socket.py:106`).
- Cover the `httpx.HTTPError` path in `populate_backend` so the 503 mapping is verified (`mcp/backend.py:60`; `tests/test_backend.py:18`).

### Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON dispatcher with 1 MiB cap & graceful shutdown | Present | `mcp/transport.py:26`; `mcp/__main__.py:165`; `tests/test_stdio.py:189` |
| Socket transport (ordering, shutdown unlink, multi-client) | Present | `mcp/socket_main.py:53`; `tests/test_socket.py:175` |
| Socket default 0600 permission verified | Missing | `mcp/socket_main.py:35`; `tests/test_socket.py:106` |
| TCP transport readiness, concurrency, shutdown logs | Present | `mcp/tcp_main.py:56`; `tests/test_tcp.py:210`; `tests/test_tcp.py:313` |
| TCP validate round-trip in integration suite | Missing | `docs/mcp_spec.md:21`; `tests/test_tcp.py:108` |
| Spec errors returned inside JSON-RPC result payload | Present | `mcp/transport.py:87`; `tests/test_stdio.py:39`; `tests/test_socket.py:120` |
| `validate` alias accepted with warning | Present | `mcp/stdio_main.py:20`; `tests/test_stdio.py:66` |
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py:167`; `tests/test_validate.py:87` |
| Backend HTTP errors surface `{ok:false, status:503}` and are tested | Missing | `mcp/backend.py:60`; `tests/test_backend.py:18` |

### Transports
- STDIO remains default, reusing `process_line` and exiting on stdin close while removing the ready file (`mcp/__main__.py:157`; `tests/test_stdio.py:160`).
- Socket server binds/unlinks the Unix path and handles per-connection threads, but CI lacks a permission-mode assertion (`mcp/socket_main.py:27`; `tests/test_socket.py:175`).
- TCP server binds with `SO_REUSEADDR`, supports concurrent clients, and logs bound host/port, yet integration traffic omits validation (`mcp/tcp_main.py:25`; `tests/test_tcp.py:210`).
- No HTTP/gRPC transports exist, matching the roadmap-only guidance (`mcp/__main__.py:81`; `docs/mcp_spec.md:9`).

### STDIO entrypoint & process model
- CLI resolves schema/example roots, writes `<pid> <ISO8601>` to the ready file, and restores signal handlers on shutdown (`mcp/__main__.py:134`; `tests/test_stdio.py:201`).
- `--validate` flag loads assets, infers schema, and returns deterministic JSON with exit codes 0/1/2 (`mcp/__main__.py:214`; `tests/test_entrypoint.py:83`).
- Deprecation warning for `validate` alias is emitted on stderr while responses stay in stdout (`mcp/stdio_main.py:17`; `tests/test_stdio.py:129`).

### Socket server (multi-client handling, perms, unlink, logs)
- Server unlinks stale paths, sets requested mode, and spawns daemon threads per connection with buffer guards (`mcp/socket_main.py:27`; `mcp/socket_main.py:95`).
- Tests cover ready/shutdown ISO logs, multi-client ordering, and ready-file cleanup (`tests/test_socket.py:100`; `tests/test_socket.py:175`).
- Missing: assertion on `stat.S_IMODE` to prove default 0600 permissions (`tests/test_socket.py:106`).

### TCP server (binding, perms, multi-client, shutdown logs)
- `TCPServer.start()` binds requested or ephemeral ports, exposes the bound address, and closes cleanly on shutdown (`mcp/tcp_main.py:25`; `mcp/tcp_main.py:44`).
- Tests assert ready/shutdown logs, multi-client interleaving, and port logging, including ephemeral port scenarios (`tests/test_tcp.py:90`; `tests/test_tcp.py:210`; `tests/test_tcp.py:260`).
- Missing: validate request in the TCP matrix; current coverage stops at list/get and oversize guard (`tests/test_tcp.py:108`).

### Golden request/response examples
- Golden replay drives list/get/validate/alias/batch/diff/backend/malformed flows with expected stderr for alias warnings (`tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1`).

### Payload size guard
- Frame parsing enforces `MAX_BYTES` before JSON decode, mirrored in socket/TCP receivers and validation/backend paths (`mcp/transport.py:26`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:113`; `mcp/validate.py:92`; `mcp/backend.py:38`).
- Tests intentionally send oversized payloads across STDIO, socket, TCP, and batch validation (`tests/test_stdio.py:189`; `tests/test_socket.py:137`; `tests/test_tcp.py:118`; `tests/test_validate.py:56`; `tests/test_backend.py:44`).

### Schema validation contract
- `validate_asset` requires schema, strips `$schemaRef`, loads via guarded paths, and sorts errors for determinism (`mcp/validate.py:108`; `mcp/validate.py:130`).
- Negative cases cover missing schema, traversal attempts, and invalid examples returning `validation_failed` (`tests/test_stdio.py:27`; `tests/test_path_traversal.py:25`; `tests/test_validate.py:22`).

### Batching
- `validate_many` enforces `MCP_MAX_BATCH`, propagates per-record errors, and returns `unsupported` when exceeding the limit (`mcp/validate.py:167`).
- Tests adjust `MCP_MAX_BATCH`, assert limit metadata, and confirm oversized member payloads report `payload_too_large` (`tests/test_validate.py:87`; `tests/test_validate.py:109`).

### Logging hygiene
- Ready/shutdown logs include mode, path/host:port, schemas_dir, examples_dir, and ISO timestamps for all transports (`mcp/__main__.py:165`; `mcp/__main__.py:181`).
- Tests parse stderr to assert presence of timestamps and directory fields (`tests/test_entrypoint.py:31`; `tests/test_socket.py:100`; `tests/test_tcp.py:90`).
- Application logs stay on stderr while stdout carries JSON-RPC frames, verified via STDIO and golden tests (`tests/test_stdio.py:118`; `tests/test_golden.py:43`).

### Container & health
- Docker image switches to `USER mcp` after install and sets predictable Python env vars (`Dockerfile:24`).
- Compose service exposes ready file healthcheck and passes through transport env vars (`docker-compose.yml:29`).
- Tests confirm Dockerfile non-root expectation and ready file lifecycle (`tests/test_container.py:1`; `tests/test_stdio.py:201`).

### Schema discovery & validation
- Discovery honors env overrides and rejects traversal, returning deterministic lists sorted by name/version/path (`mcp/core.py:44`; `mcp/core.py:74`; `tests/test_env_discovery.py:16`; `tests/test_path_traversal.py:25`).
- Submodule integration validates examples and aliases when the git submodule is present (`tests/test_submodule_integration.py:23`).

### Test coverage
- STDIO loop, alias warning, payload guard, and ready file cleanup covered via subprocess tests (`tests/test_stdio.py:66`; `tests/test_stdio.py:189`).
- Socket/TCP integration tests exercise concurrency, logging, oversize guard, and shutdown cleanup (`tests/test_socket.py:175`; `tests/test_tcp.py:210`).
- Backend, diff, traversal, and batching scenarios validated (`tests/test_backend.py:14`; `tests/test_diff.py:4`; `tests/test_path_traversal.py:25`; `tests/test_validate.py:87`).
- Missing coverage: TCP validate request and backend HTTPError branch (`tests/test_tcp.py:108`; `mcp/backend.py:60`).

### Dependencies & runtime
- Runtime requirements limited to `jsonschema`, `httpx`, and `pytest`, matching usage in validation and backend modules (`requirements.txt:1`; `mcp/validate.py:8`; `mcp/backend.py:7`).
- Optional `referencing` import is safely guarded for local registry support (`mcp/validate.py:10`).

### Environment variables
- CLI parses transport/socket/TCP env vars and enforces numeric parsing with helpful errors (`mcp/__main__.py:81`; `mcp/__main__.py:118`).
- Docs, README, and `.env.example` enumerate defaults for transports, schemas/examples, backend URL, and batch limits (`README.md:61`; `.env.example:1`; `docker-compose.yml:29`).

### Documentation accuracy
- Spec doc states TCP addition, logging fields, and audit expectations that match implementation/tests (`docs/mcp_spec.md:13`).
- README feature list, transport instructions, and environment tables align with current behavior (`README.md:35`; `README.md:73`).
- Compose scripts (`up.sh`, `down.sh`) reflect transport options and cleanup expectations (`up.sh:1`; `down.sh:1`).

### Detected divergences
- None; transports are limited to STDIO/socket/TCP and adhere to the v0.2.6 contract (`mcp/__main__.py:81`).

### Recommendations
- Add a TCP validate integration test (e.g., send `validate_asset` over the existing client harness) to satisfy the audit clause (`docs/mcp_spec.md:21`; `tests/test_tcp.py:108`).
- Extend socket tests to assert `stat.S_IMODE(os.stat(path).st_mode) == 0o600` after readiness to prove default permissions (`mcp/socket_main.py:35`; `tests/test_socket.py:106`).
- Simulate an `httpx.HTTPError` in backend tests (e.g., mock transport raising) to verify the 503 mapping (`mcp/backend.py:60`; `tests/test_backend.py:18`).
