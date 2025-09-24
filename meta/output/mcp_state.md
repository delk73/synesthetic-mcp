## Summary of repo state
- STDIO and socket transports enforce NDJSON framing with a 1 MiB guard before dispatch, and integration tests exercise alias warnings plus oversized frames (mcp/transport.py:13, mcp/socket_main.py:95, tests/test_stdio.py:283, tests/test_golden.py:45).
- Readiness logs, signal handling, and ready-file lifecycle are consistent across transports, including PID+ISO timestamps and cleanup during shutdown (mcp/__main__.py:115, mcp/__main__.py:170, tests/test_stdio.py:183, tests/test_socket.py:136).
- Validation, batching, diff, and backend flows stay deterministic while enforcing payload limits and schema safety, with coverage across unit and integration tests (mcp/validate.py:119, mcp/diff.py:16, mcp/backend.py:38, tests/test_validate.py:46, tests/test_backend.py:56).
- Documentation, fixtures, and container tooling reflect the v0.2.5 contract while running non-root with ready-file health checks (docs/mcp_spec.md:1, README.md:2, Dockerfile:24, docker-compose.yml:17).

## Top gaps & fixes (3-5 bullets)
- Add an assertion that the STDIO ready file is removed after shutdown to lock in `_clear_ready_file` behavior (mcp/__main__.py:133, tests/test_stdio.py:155).
- Extend the socket integration test to verify the UDS path is created with default 0600 permissions before unlinking (mcp/socket_main.py:35, tests/test_socket.py:45).
- Cover invalid `MCP_MAX_BATCH` values with a focused test so misconfiguration surfaces deterministically (mcp/validate.py:27, tests/test_validate.py:103).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing with 1 MiB guard | Present | mcp/transport.py:13; tests/test_stdio.py:283 |
| Socket multi-client support, 0600 perms, unlink | Present | mcp/socket_main.py:35; tests/test_socket.py:153; tests/test_socket.py:147 |
| Ready file `<pid> <ISO8601>` lifecycle & logs | Present | mcp/__main__.py:80; tests/test_stdio.py:183 |
| `validate` alias accepted with warning | Present | mcp/stdio_main.py:23; tests/test_stdio.py:56 |
| `validate_many` batching & payload guard | Present | mcp/validate.py:27; mcp/validate.py:182; tests/test_validate.py:103; tests/test_validate.py:128 |
| Path traversal rejection & schema safety | Present | mcp/core.py:16; tests/test_path_traversal.py:34 |
| Deterministic listings, errors, and diff ordering | Present | mcp/core.py:69; mcp/diff.py:16; tests/test_submodule_integration.py:32; tests/test_validate.py:46 |
| Golden request/response coverage | Present | tests/fixtures/golden.jsonl:1; tests/test_golden.py:45 |
| Backend populate guardrails | Present | mcp/backend.py:38; tests/test_backend.py:56 |

## Transports
- STDIO loop strips blank lines, delegates to the shared transport guard, and flushes each JSON-RPC frame in order (mcp/stdio_main.py:51, mcp/transport.py:41).
- Socket acceptor spawns per-connection threads, enforces MAX_BYTES before decoding, and joins client threads on shutdown (mcp/socket_main.py:27, mcp/socket_main.py:95, mcp/socket_main.py:88).

## STDIO entrypoint & process model
- Entry path logs mode, schemas/examples directories, writes the ready file, and traps SIGTERM for graceful exit (mcp/__main__.py:103, mcp/__main__.py:115).
- Integration exercises cover the PID+ISO content, validation flow, and shutdown behavior when stdin closes (tests/test_stdio.py:183, tests/test_stdio.py:207).

## Socket server (multi-client handling, perms, unlink, logs)
- Socket startup binds, chmods with the configured mode, and logs readiness with the socket path (mcp/socket_main.py:27, mcp/__main__.py:165).
- Tests validate concurrent clients maintain ordering and that the socket file and ready file are removed on shutdown (tests/test_socket.py:153, tests/test_socket.py:147).

## Golden request/response examples
- Fixture exercises list/get schema, validation (success and alias), batching, examples, diff, backend disabled, and malformed payload cases (tests/fixtures/golden.jsonl:1).
- Replay test streams each record through the STDIO loop, asserting exact responses and expected stderr warnings (tests/test_golden.py:45, tests/test_golden.py:66).

## Payload size guard
- Transport rejects oversized frames pre-parse and returns `payload_too_large` in the result (mcp/transport.py:15, tests/test_stdio.py:283).
- Validator and backend enforce the same 1 MiB cap on assets and batches (mcp/validate.py:128, mcp/backend.py:38, tests/test_validate.py:56, tests/test_backend.py:56).

## Schema validation contract
- STDIO dispatch requires the `schema` param and passes assets through `validate_asset`, which handles alias resolution, traversal guards, and deterministic errors (mcp/stdio_main.py:28, mcp/validate.py:119, mcp/core.py:147).
- Tests cover missing schema, alias validation, invalid examples, and schema traversal rejections (tests/test_stdio.py:17, tests/test_validate.py:46, tests/test_path_traversal.py:34).

## Batching
- `_max_batch` enforces a positive integer limit sourced from `MCP_MAX_BATCH`, and `validate_many` surfaces `unsupported` with the limit when exceeded (mcp/validate.py:27, mcp/validate.py:199).
- Test cases assert mixed results, batch caps, and oversized asset handling within batches (tests/test_validate.py:78, tests/test_validate.py:128).

## Logging hygiene
- Logging configuration outputs structured readiness and shutdown messages without timestamps to keep logs deterministic (mcp/__main__.py:252, mcp/__main__.py:115).
- Tests confirm alias warnings land on stderr while stdout stays limited to JSON-RPC frames (tests/test_stdio.py:117, tests/test_golden.py:66).

## Container & health
- Docker image installs dependencies, drops to user `mcp`, and sets `$HOME` for runtime operations (Dockerfile:24, Dockerfile:27).
- Compose service relies on `/tmp/mcp.ready` for health checks and surfaces transport configuration via environment variables (docker-compose.yml:17, docker-compose.yml:26).

## Schema discovery & validation
- Discovery prioritizes env overrides, then the submodule, and refuses traversal outside configured roots (mcp/core.py:27, mcp/core.py:16).
- Tests cover env override listings, submodule ordering, and validation of discovered examples (tests/test_env_discovery.py:6, tests/test_submodule_integration.py:32).

## Test coverage
- STDIO and socket integration suites cover framing, alias warnings, payload guard, readiness logs, and shutdown (tests/test_stdio.py:56, tests/test_socket.py:45).
- Validation, backend, diff, traversal, and golden replay ensure deterministic behavior across core APIs (tests/test_validate.py:14, tests/test_backend.py:21, tests/test_diff.py:1, tests/test_golden.py:45).

## Dependencies & runtime
- Runtime dependencies remain `jsonschema` and `httpx`, with pytest for tests and optional `referencing` support (requirements.txt:1, mcp/validate.py:8).
- README mirrors the dependency set and runtime expectations (README.md:87).

## Environment variables
- Entry point validates `MCP_ENDPOINT`, socket parameters, and ready file path before launching the transport (mcp/__main__.py:47, mcp/__main__.py:72).
- README documents all transport, discovery, batching, and backend variables with defaults (README.md:94).

## Documentation accuracy
- Spec header and content reflect v0.2.5 behavior, matching implementation features (docs/mcp_spec.md:1, docs/mcp_spec.md:37).
- README front matter and environment table align with the current release and feature set (README.md:2, README.md:94).

## Detected divergences
- None detected.

## Recommendations
1. Check the ready file is deleted on shutdown. Assert STDIO ready-file cleanup in the integration test to lock in the shutdown contract (mcp/__main__.py:133, tests/test_stdio.py:155).
2. Verify socket permissions. Capture the default 0600 socket permission in tests before unlinking the UDS path (mcp/socket_main.py:35, tests/test_socket.py:45).
3. Test bad batch sizes. Add coverage for invalid `MCP_MAX_BATCH` values so the server fails fast when misconfigured (mcp/validate.py:27, tests/test_validate.py:103).