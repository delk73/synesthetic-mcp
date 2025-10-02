# MCP Repository State Audit (v0.2.7)

## Summary of Repo State
The `synesthetic-mcp` repository is in excellent shape and strongly aligns with the v0.2.7 spec. Implementation of TCP transport, lifecycle signals, and logging invariants is complete and verified by an extensive test suite. All transports (STDIO, Socket, TCP) correctly enforce the 1 MiB payload guard. Documentation in the `README.md` and `docs/mcp_spec.md` is accurate and reflects the current implementation. The container runs as a non-root user, and file permissions are handled correctly.

## Top Gaps & Fixes
No significant gaps were found. The implementation is robust. Minor recommendations focus on maintaining the current high standard.
- **Clarity on Skipped Tests:** Socket and TCP tests are skipped if the environment (e.g., a restrictive sandbox) prevents binding. This is appropriate, but adding a note to the test output or documentation would clarify why these tests might be skipped in certain CI environments.
- **Golden File Maintenance:** The `tests/test_golden.py` replay test is a critical regression guard. It should be explicitly mentioned in developer contribution guides as a file to be updated when making breaking changes to the API surface.
- **JSON-RPC Version Gate:** The test ensuring `jsonrpc: "2.0"` is enforced (`tests/test_stdio.py:312`) is a key compliance check and should be protected from accidental removal.

## Alignment with mcp_spec.md

| Spec Item | Status | Evidence |
|---|---|---|
| TCP transport fully aligned | Present | `mcp/tcp_main.py`, `tests/test_tcp.py` |
| TCP 1 MiB guard | Present | `mcp/transport.py:26`, `tests/test_tcp.py:142` |
| TCP ready/shutdown logs | Present | `mcp/__main__.py:165`, `tests/test_tcp.py:90`, `tests/test_tcp.py:180` |
| Lifecycle signals (SIGINT/SIGTERM) | Present | `mcp/__main__.py:176`, `tests/test_entrypoint.py:118`, `tests/test_socket.py:209` |
| Shutdown logging invariant | Present | `mcp/__main__.py:155`, `tests/test_entrypoint.py:65` |
| Ready file format `<pid> <ISO8601>` | Present | `mcp/__main__.py:139`, `tests/test_stdio.py:208` |
| Docs reflect all transport guards | Present | `README.md`, `docs/mcp_spec.md` |

## Transports
- **STDIO:** Present and fully functional. `mcp/stdio_main.py`, `tests/test_stdio.py`.
- **Socket:** Present, with multi-client support, correct permissions (`0o600`), and cleanup on shutdown. `mcp/socket_main.py`, `tests/test_socket.py`.
- **TCP:** Present, with multi-client support and correct shutdown behavior. `mcp/tcp_main.py`, `tests/test_tcp.py`.
- **HTTP/gRPC:** Correctly marked as roadmap-only. Not implemented.

## Lifecycle and Process
- **Process Model:** STDIO exits on `stdin` close; Socket/TCP servers log readiness and clean up on shutdown. Verified in `tests/test_stdio.py`, `tests/test_socket.py`, and `tests/test_tcp.py`.
- **Signal Handling:** `SIGINT` and `SIGTERM` are handled gracefully, triggering shutdown and returning correct exit codes (`-SIGINT`/`-SIGTERM`). Verified in `tests/test_entrypoint.py`.
- **Shutdown Logging:** The shutdown logging invariant holds. Logs are emitted before exit across all transports. Verified in `tests/test_entrypoint.py`, `tests/test_socket.py`, and `tests/test_tcp.py`.

## Features
- **Payload Size Guard:** The 1 MiB limit is consistently enforced across all transports before request parsing. Evidence: `mcp/transport.py:26`, `tests/test_stdio.py:352`, `tests/test_socket.py:141`, `tests/test_tcp.py:142`.
- **`validate_asset`:** The `schema` parameter is required, and an error is returned if it's missing. Evidence: `mcp/validate.py:145`, `tests/test_stdio.py:30`.
- **`validate` alias:** The alias for `validate_asset` works, logs a deprecation warning to `stderr`, and is tested. Evidence: `mcp/stdio_main.py:24`, `tests/test_stdio.py:88`.
- **Batching (`validate_many`):** Correctly honors the `MCP_MAX_BATCH` environment variable. Evidence: `mcp/validate.py:199`, `tests/test_validate.py:118`.
- **`get_example`:** Returns `validation_failed` for invalid examples. Evidence: `mcp/core.py:188`, `tests/test_validate.py:46`.
- **Schema Resolution:** Strictly local, with path traversal guards in place. Evidence: `mcp/core.py:16`, `tests/test_path_traversal.py`.
- **Determinism:** Sorting is applied to `list_schemas` and `list_examples`. Diff ordering is deterministic. Evidence: `mcp/core.py:90`, `mcp/diff.py:13`.

## Container & Environment
- **Container:** The `Dockerfile` specifies a non-root user (`mcp`). `docker-compose.yml` is well-structured for development and serving.
- **Environment Variables:** All specified variables in `.env.example` and `README.md` are correctly implemented and used.

## Documentation
- **`README.md`:** Accurate, up-to-date, and consistent with `docs/mcp_spec.md`.
- **`docs/mcp_spec.md`:** Provides a clear and accurate specification that matches the v0.2.7 implementation.

## Detected Divergences
None. The implementation is remarkably consistent with the specification.

## Recommendations
1.  **Document Sandbox Skipped Tests:** Add comments in `tests/test_socket.py` and `tests/test_tcp.py` to clarify that tests may be skipped due to sandbox restrictions on network binding. This will prevent confusion during CI runs in restricted environments.
2.  **Formalize Golden File Updates:** Add a section to a future `CONTRIBUTING.md` that explicitly requires developers to update `tests/fixtures/golden.jsonl` when making any change that alters the API's request/response behavior.
3.  **Protect Core Compliance Tests:** Add comments to tests like the `jsonrpc == "2.0"` check to mark them as critical for spec compliance and prevent accidental removal during future refactoring.