## Summary of repo state
- Transports, lifecycle, and logging remain aligned with v0.2.8 transport requirements; readiness/shutdown metadata and signal exit codes are covered by tests (`mcp/__main__.py:185`, `tests/test_tcp.py:178`, `tests/test_entrypoint.py:105`).
- Schema validation still depends on caller-supplied `schema` and tolerates `$schemaRef`, violating the v0.2.8 `$schema` mandate (`mcp/validate.py:120`, `mcp/validate.py:135`, `docs/mcp_spec.md:12`).
- Documentation and golden fixtures continue to demonstrate `"schema"` usage instead of `$schema`, so repo state diverges from the updated spec (`README.md:153`, `tests/fixtures/golden.jsonl:3`).

## Top gaps & fixes (3-5 bullets)
- Enforce top-level `$schema` in `validate_asset`/`validate_many`, returning `validation_failed` at `/$schema` when absent (`mcp/validate.py:120`, `docs/mcp_spec.md:12`).
- Reject legacy helpers (`schema`, `$schemaRef`) instead of stripping them, and update tests/fixtures accordingly (`mcp/validate.py:135`, `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`).
- Refresh README and golden transcript to show `$schema` payloads and ensure CI covers the new contract (`README.md:153`, `tests/fixtures/golden.jsonl:3`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB payload cap | Present | `mcp/transport.py:28`; `tests/test_stdio.py:355`; `tests/test_socket.py:185`; `tests/test_tcp.py:167` |
| Ready/shutdown logs mirror metadata and precede exit | Present | `mcp/__main__.py:185`; `mcp/__main__.py:304`; `tests/test_entrypoint.py:85`; `tests/test_socket.py:283` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:156`; `mcp/__main__.py:432`; `tests/test_stdio.py:210`; `tests/test_tcp.py:252` |
| Signal exits surface `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:295`; `mcp/__main__.py:439`; `tests/test_entrypoint.py:105`; `tests/test_tcp.py:194` |
| `validate` alias warns + requires schema param | Present | `mcp/stdio_main.py:23`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:68`; `tests/test_stdio.py:35` |
| `validate_many` honours `MCP_MAX_BATCH` | Present | `mcp/validate.py:92`; `mcp/validate.py:113`; `tests/test_validate.py:103`; `tests/test_validate.py:120` |
| Socket perms 0600 + multi-client ordering | Present | `mcp/socket_main.py:27`; `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP multi-client handling + shutdown logs | Present | `mcp/tcp_main.py:25`; `mcp/tcp_main.py:304`; `tests/test_tcp.py:321`; `tests/test_tcp.py:411` |
| Schema traversal guard (local only) | Present | `mcp/core.py:18`; `mcp/core.py:62`; `tests/test_path_traversal.py:34`; `tests/test_path_traversal.py:61` |
| Assets MUST include top-level `$schema`; reject `schema/$schemaRef` | Divergent | `docs/mcp_spec.md:12`; `mcp/validate.py:135`; `tests/test_backend.py:31`; `tests/fixtures/golden.jsonl:3` |

## Transports
- Unified dispatcher processes JSON-RPC for STDIO, socket, and TCP; NDJSON framing exercised end-to-end (`mcp/stdio_main.py:14`, `mcp/socket_main.py:53`, `mcp/tcp_main.py:56`, `tests/test_tcp.py:130`).
- Payload guard is applied before decode in each transport loop (`mcp/transport.py:28`, `mcp/socket_main.py:110`, `mcp/tcp_main.py:113`).
- Tests cover malformed frames, oversize payloads, and normal operations across transports (`tests/test_stdio.py:162`, `tests/test_socket.py:150`, `tests/test_tcp.py:146`).

## STDIO entrypoint & process model
- Entry process logs readiness with schemas/examples metadata, writes ready file, processes stdin until EOF, and mirrors shutdown log (`mcp/__main__.py:185`, `mcp/__main__.py:204`, `tests/test_stdio.py:203`).
- CLI `--validate` path infers schema and returns deterministic exit codes though it still expects legacy fields in sample assets (`mcp/__main__.py:323`, `tests/test_entrypoint.py:210`).

## Socket server (multi-client handling, perms, unlink, logs)
- Server enforces 0600 permissions, spawns per-client threads, drains on shutdown, and unlinks socket path (`mcp/socket_main.py:27`, `mcp/socket_main.py:49`).
- Tests assert permissions, payload guard, multi-client ordering, and shutdown logging (`tests/test_socket.py:146`, `tests/test_socket.py:346`, `tests/test_socket.py:407`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP server binds requested/ephemeral ports, tracks bound address, and drains threads on close (`mcp/tcp_main.py:25`, `mcp/tcp_main.py:54`).
- Tests verify readiness/shutdown logs, SIGINT/SIGTERM cleanup, 1 MiB guard, and multi-client ordering (`tests/test_tcp.py:117`, `tests/test_tcp.py:167`, `tests/test_tcp.py:321`, `tests/test_tcp.py:411`).

## Lifecycle signals
- `_SignalShutdown` ensures SIGINT/SIGTERM propagate as negative exit codes for all transports (`mcp/__main__.py:78`, `mcp/__main__.py:295`).
- Test suites assert signal handling and ready file cleanup (`tests/test_entrypoint.py:105`, `tests/test_tcp.py:194`).

## Shutdown logging invariant
- Shutdown logs reuse transport metadata prior to exit, with stderr flushes to avoid truncation (`mcp/__main__.py:204`, `mcp/__main__.py:252`, `mcp/__main__.py:304`).
- Tests compare ready vs shutdown fields to enforce invariant (`tests/test_entrypoint.py:85`, `tests/test_socket.py:283`).

## Golden request/response examples
- Golden replay covers list/get/validate/alias/batch/example/diff/backend/malformed scenarios but still exercises legacy `schema` fields (`tests/test_golden.py:45`, `tests/fixtures/golden.jsonl:3`, `tests/fixtures/golden.jsonl:10`).

## Payload size guard
- Transport parse path returns `payload_too_large` results without JSON decode (`mcp/transport.py:28`, `mcp/transport.py:75`).
- Validation paths enforce the same limit for assets/batches/backend payloads (`mcp/validate.py:128`, `tests/test_validate.py:56`, `tests/test_backend.py:56`).

## Schema validation contract
- Current validator requires an external `schema` param and strips `$schemaRef`, so assets lacking `$schema` still pass, diverging from v0.2.8 (`mcp/validate.py:120`, `mcp/validate.py:135`).
- Assets and fixtures rely on `schema` or `$schemaRef` (`tests/test_backend.py:31`, `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`).
- No tests assert rejection of missing `$schema`, so spec coverage is absent (`tests/test_validate.py:19`).

## Batching
- `_max_batch` guards `MCP_MAX_BATCH`, enforcing positive integers and returning limit metadata when exceeded (`mcp/validate.py:92`, `mcp/validate.py:113`).
- Batch tests cover mixed results, limit overflow, and oversize asset handling (`tests/test_validate.py:94`, `tests/test_validate.py:120`, `tests/test_validate.py:150`).

## Logging hygiene
- Structured stderr logging with ISO timestamps is centralized in `_log_event` and exercised across transports (`mcp/__main__.py:60`, `mcp/__main__.py:185`).
- Tests confirm timestamps in readiness/shutdown logs and absence of stray stdout output (`tests/test_entrypoint.py:66`, `tests/test_stdio.py:120`).

## Container & health
- Docker image installs dependencies before switching to non-root `USER mcp` and sets HOME accordingly (`Dockerfile:16`, `Dockerfile:27`).
- Test ensures container remains non-root (`tests/test_container.py:4`).
- Ready file lifecycle supports health endpoints via `MCP_READY_FILE` (`mcp/__main__.py:156`, `tests/test_tcp.py:252`).

## Schema discovery & validation
- Discovery prefers env overrides, falls back to submodule, and sorts listings deterministically (`mcp/core.py:41`, `mcp/core.py:53`).
- Path traversal is rejected for schemas/examples (`mcp/core.py:18`, `tests/test_path_traversal.py:34`, `tests/test_path_traversal.py:61`).
- Example inference still maps `SynestheticAsset_*` to legacy alias, relying on `$schemaRef` hints (`mcp/core.py:126`, `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`).

## Test coverage
- Pytest suite spans transports, lifecycle, backend, diff, validation, golden replay, and container posture (`tests/test_tcp.py:63`, `tests/test_backend.py:21`, `tests/test_diff.py:11`, `tests/test_golden.py:45`).
- Coverage lacks assertions for `$schema` enforcement or `$schemaRef` rejection (`tests/test_validate.py:19`, `tests/test_backend.py:96`).

## Dependencies & runtime
- Runtime dependencies stay minimal (`requirements.txt:1-3`), with optional `referencing` for registry support (`mcp/validate.py:67`).
- Setup and entry tooling unchanged (`setup.py:1`, `serve.sh:1`).

## Environment variables
- Implementation reads documented env vars for transport, lifecycle, backend, and batching (`mcp/__main__.py:103`, `mcp/backend.py:18`, `mcp/validate.py:92`).
- README and `.env.example` list the same defaults (`README.md:94`, `.env.example:2`).

## Documentation accuracy
- README quickstart and CLI examples still reference `"schema"` responses, conflicting with `$schema` requirement (`README.md:153`).
- Spec file documents the corrected contract, highlighting doc drift elsewhere (`docs/mcp_spec.md:12`).

## Detected divergences
- Validation accepts assets without `$schema`, trusts a separate `schema` param, and silently strips `$schemaRef` (`mcp/validate.py:120`, `mcp/validate.py:135`, `tests/test_backend.py:31`).
- Fixtures and docs continue to rely on `schema`/`$schemaRef`, so published guidance mismatches spec (`tests/fixtures/golden.jsonl:3`, `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `README.md:153`).

## Recommendations
- Update validator to require `$schema`, reject `schema`/`$schemaRef`, and adjust error payloads to flag `/$schema` per spec (`mcp/validate.py:120`, `mcp/validate.py:135`).
- Revise fixtures/tests/docs to emit `$schema`, adding regression tests for missing/legacy keys (`tests/test_validate.py:19`, `tests/fixtures/golden.jsonl:3`, `README.md:153`).
- Add CI coverage ensuring examples/submodule assets declare `$schema`, preventing regressions (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `.github/workflows/`).
