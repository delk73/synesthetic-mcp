# MCP Audit Report (v0.2.5)

## Summary of repo state

The MCP repository is mostly aligned with the v0.2.5 spec. Core features like the non-root container, batch limiting, and path traversal safety are implemented and tested. Key divergences are missing tests for the deprecation warning and incomplete payload size guard testing.

## Top gaps & fixes

1.  **Divergent: Alias Deprecation Warning Not Tested.** The `validate` alias logs a deprecation warning, but no test captures `stderr` to confirm this. Add a test to assert the warning is emitted.
2.  **Divergent: Incomplete Payload Size Guard Testing.** The 1 MiB payload limit is not explicitly tested for `validate_many` or the STDIO transport. Add tests to cover these cases.
3.  **Missing: Golden Examples.** The repository lacks a "golden" file with request/response examples as suggested by the exit criteria.

## Alignment with mcp_spec.md

| Spec item | Status | Evidence |
|---|---|---|
| `validate_many` enforces `MCP_MAX_BATCH` | Present | `mcp/validate.py`, `tests/test_validate.py` |
| Container runs as non-root | Present | `Dockerfile`, `tests/test_container.py` |
| Readiness logs include `mode`, `path`, `schemas_dir` | Present | `mcp/__main__.py` |
| `validate` alias logs deprecation warning | Divergent | `mcp/stdio_main.py` (implementation), missing test |
| Path traversal rejection tests | Present | `tests/test_path_traversal.py` |
| Socket multi-client FIFO ordering tests | Present | `tests/test_socket.py` |
| Payload oversize rejection tested across all tools | Divergent | `tests/test_socket.py` (present for socket), missing for `validate_many` and stdio |

## Transports

*   **STDIO:** **Present.** Implemented in `mcp/stdio_main.py`.
*   **Socket:** **Present.** Implemented in `mcp/socket_main.py` and supports multiple clients.

## Golden request/response examples

*   **Status:** **Missing.** No golden request/response file was found.

## Payload size guard

*   **Status:** **Divergent.** The guard is implemented but not tested for all entrypoints. `validate_asset` and the socket transport have checks, but `validate_many` and the stdio transport lack explicit tests.

## Schema validation contract

*   **Status:** **Present.** `validate_asset` requires a schema and returns a `validation_failed` error if it's missing.

## Batching

*   **Status:** **Present.** `validate_many` is implemented and respects `MCP_MAX_BATCH`.

## Logging hygiene

*   **Status:** **Present.** Readiness logs are detailed and sent to stderr.

## Container & health

*   **Status:** **Present.** The container runs as a non-root user.

## Schema discovery & validation

*   **Status:** **Present.** Schema discovery is local-only. Path traversal is rejected.

## Test coverage

*   **Status:** **Divergent.** Coverage is good but has gaps, particularly around `stderr` capture for warnings and payload limits.

## Dependencies & runtime

*   **Status:** **Present.** `requirements.txt` is consistent with the spec.

## Documentation accuracy

*   **Status:** **Present.** `README.md` and `docs/mcp_spec.md` are consistent.

## Detected divergences

1.  The `validate` alias deprecation warning is not tested.
2.  Payload size guards are not tested for all entrypoints (`validate_many`, stdio).

## Recommendations

1.  Add a test to `tests/test_stdio.py` that uses the `validate` alias and asserts that the deprecation warning is written to `stderr`.
2.  Add tests to `tests/test_validate.py` and `tests/test_stdio.py` to ensure oversized payloads are rejected by `validate_many` and the stdio transport.
3.  Create a `golden.jsonl` file in `tests/fixtures` with example requests and responses for all MCP methods.