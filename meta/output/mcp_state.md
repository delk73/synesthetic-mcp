## Summary of repo state
- STDIO and socket dispatch share the guarded NDJSON loop with multi-client coverage preserving ordering (`mcp/transport.py:13`; `tests/test_socket.py:153`).
- Validation, diff, backend, and discovery flows stay deterministic with payload caps exercised in unit and integration suites (`mcp/validate.py:176`; `mcp/diff.py:42`; `tests/test_validate.py:56`; `tests/test_backend.py:56`).
- v0.2.6 additions (TCP transport, observability upgrades) are absent across code, tests, and docs, leaving the repo aligned with the older v0.2.5 contract (`mcp/__main__.py:47`; `docs/mcp_spec.md:17`; `README.md:35`).

## Top gaps & fixes (3-5 bullets)
- Implement the TCP transport path (`MCP_ENDPOINT=tcp`, host/port env, guard, readiness logs) with integration coverage to satisfy the v0.2.6 contract (`mcp/__main__.py:47`; `docs/mcp_spec.md:19`; `tests/test_entrypoint.py:99`).
- Extend logging so shutdown events carry `schemas_dir`/`examples_dir` and emit ISO-8601 timestamps per spec (`docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:179`; `mcp/__main__.py:252`).
- Move semantic request failures (e.g. non-dict `params`) into `result` frames instead of JSON-RPC errors to obey the API rule (`meta/prompts/mcp_audit.json:10`; `mcp/stdio_main.py:18`; `tests/test_stdio.py:238`).
- Update developer tooling and docs to advertise TCP (scripts, compose, env samples, README front matter) so guidance matches the new transport (`docs/mcp_spec.md:23`; `README.md:2`; `docker-compose.yml:22`; `.env.example:2`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop with 1 MiB guard | Present | `mcp/transport.py:13`; `tests/test_stdio.py:283` |
| Socket multi-client ordering, guard, unlink | Present | `mcp/socket_main.py:67`; `tests/test_socket.py:153` |
| TCP transport (host/port, guard, tests) | Missing | `docs/mcp_spec.md:19`; `mcp/__main__.py:47`; `tests/test_entrypoint.py:99` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:80`; `tests/test_stdio.py:183`; `tests/test_socket.py:147` |
| Ready/shutdown logs include dirs + ISO timestamp | Divergent | `docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252` |
| `validate` alias warning | Present | `mcp/stdio_main.py:25`; `tests/test_stdio.py:117` |
| `validate_many` honours `MCP_MAX_BATCH` | Present | `mcp/validate.py:199`; `tests/test_validate.py:103` |
| `get_example` invalid → `validation_failed` | Present | `mcp/core.py:147`; `tests/test_validate.py:32` |
| Schema traversal guard (schemas & examples) | Present | `mcp/core.py:16`; `tests/test_path_traversal.py:34` |
| Deterministic listings/errors/diff ordering | Present | `mcp/core.py:85`; `mcp/diff.py:49`; `tests/test_submodule_integration.py:22` |
| Spec errors stay in JSON-RPC result | Divergent | `meta/prompts/mcp_audit.json:10`; `mcp/stdio_main.py:18`; `tests/test_stdio.py:238` |
| Payload guard inside validation/backend flows | Present | `mcp/validate.py:128`; `mcp/backend.py:58`; `tests/test_validate.py:56` |
| Container runs non-root | Present | `Dockerfile:24`; `tests/test_container.py:1` |
| Docs/scripts reflect TCP mode | Missing | `docs/mcp_spec.md:23`; `README.md:35`; `.env.example:2` |

## Transports
- Present: STDIO loop processes NDJSON frames via the shared guard and flushes responses synchronously (`mcp/stdio_main.py:51`; `mcp/transport.py:41`).
- Present: Socket server accepts threaded clients, enforces `MAX_BYTES`, and joins threads on shutdown (`mcp/socket_main.py:53`; `tests/test_socket.py:153`).
- Missing: No TCP implementation; `_endpoint` rejects `tcp` and there is no listener binding/guard/test coverage (`mcp/__main__.py:47`; `tests/test_entrypoint.py:99`).

## STDIO entrypoint & process model
- Ready log includes mode plus schema/example roots and writes the PID+ISO ready file (`mcp/__main__.py:115`; `tests/test_stdio.py:183`).
- Shutdown removes the ready file but lacks log fields for directories and timestamp output (`mcp/__main__.py:131`; `mcp/__main__.py:252`).

## Socket server (multi-client handling, perms, unlink, logs)
- Startup unlinks and rebinds the UDS, applying the configured mode before listening (`mcp/socket_main.py:27`; `mcp/socket_main.py:35`).
- Tests cover end-to-end list/get flows, payload guard, concurrent clients, and cleanup of socket + ready file (`tests/test_socket.py:45`; `tests/test_socket.py:147`).
- No automated check currently asserts the chmod result, leaving the least-privilege guarantee untested (`tests/test_socket.py:45`).

## TCP server (binding, perms, multi-client, shutdown logs)
- Missing entirely: there is no TCP accept loop, host/port configuration, or tests despite the v0.2.6 addition (`docs/mcp_spec.md:19`; `mcp/__main__.py:47`; `docker-compose.yml:22`).

## Golden request/response examples
- Golden replay exercises list/get schema, validate/alias, get_example success+failure, diff, backend disabled, and malformed JSON frames through STDIO (`tests/fixtures/golden.jsonl:1`; `tests/test_golden.py:45`).
- No socket/TCP replay exists, so cross-transport parity depends on indirect coverage (`tests/test_socket.py:45`).

## Payload size guard
- Transport rejects oversized frames before parsing, returning `payload_too_large` results (`mcp/transport.py:15`; `tests/test_stdio.py:283`).
- Validation and backend paths reuse the 1 MiB cap for assets and batches (`mcp/validate.py:128`; `mcp/backend.py:58`; `tests/test_backend.py:56`).
- Guarding for TCP cannot be verified without the transport (`docs/mcp_spec.md:19`).

## Schema validation contract
- `validate_asset` demands a schema, filters traversal, normalises `$schemaRef`, and sorts errors deterministically (`mcp/validate.py:120`; `mcp/core.py:126`; `tests/test_validate.py:46`).
- `get_example` infers schema names, validates, and returns `validation_failed` on invalid fixtures (`mcp/core.py:147`; `tests/test_validate.py:32`).

## Batching
- `_max_batch` enforces positive integer configuration and `validate_many` surfaces `unsupported` with the cap when exceeded (`mcp/validate.py:27`; `mcp/validate.py:199`; `tests/test_validate.py:103`).
- Oversized assets inside a batch propagate payload errors per item (`tests/test_validate.py:128`).

## Logging hygiene
- Current logging config omits timestamps and shutdown logs drop schema/example details, diverging from v0.2.6 observability requirements (`docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252`).
- Stderr carries alias warnings while stdout remains JSON-RPC-only (`tests/test_stdio.py:117`; `tests/test_golden.py:66`).

## Container & health
- Docker image installs dependencies, switches to user `mcp`, and defaults to running `python -m mcp` (`Dockerfile:24`; `Dockerfile:32`).
- Compose health check monitors `/tmp/mcp.ready`, but service wiring still assumes STDIO/socket modes only (`docker-compose.yml:15`; `docker-compose.yml:32`).

## Schema discovery & validation
- Discovery honours env overrides, rejects traversal, and maintains deterministic ordering (`mcp/core.py:27`; `tests/test_env_discovery.py:6`).
- Submodule integration test asserts deterministic listings and validates retrieved examples (`tests/test_submodule_integration.py:22`).

## Test coverage
- Extensive coverage exists for STDIO, socket, validation, backend, diff, traversal, and golden flows (`tests/test_stdio.py:56`; `tests/test_socket.py:45`; `tests/test_backend.py:21`).
- No TCP tests exist, and socket permission expectations remain unenforced (`docs/mcp_spec.md:24`; `tests/test_socket.py:45`).

## Dependencies & runtime
- Runtime deps remain `jsonschema` and `httpx` with optional `referencing`; pytest drives the suite (`requirements.txt:1`; `mcp/validate.py:8`).
- CI installs the package editable and runs pytest across Python 3.11–3.13 (`.github/workflows/ci.yml:16`; `.github/workflows/ci.yml:32`).

## Environment variables
- Entry point validates `MCP_ENDPOINT`, socket path, mode, and ready file before launch (`mcp/__main__.py:47`; `mcp/__main__.py:72`).
- `MCP_HOST`/`MCP_PORT` and `MCP_ENDPOINT=tcp` handling are absent from CLI, env sample, and docs (`docs/mcp_spec.md:19`; `.env.example:2`; `README.md:94`).

## Documentation accuracy
- README still labels the project v0.2.5 and only references STDIO/socket transports (`README.md:2`; `README.md:35`).
- Spec file advertises v0.2.6 features that the implementation/tests/docs do not yet satisfy (`docs/mcp_spec.md:19`; `docs/mcp_spec.md:25`).

## Detected divergences
- Semantic request errors surface as JSON-RPC `error` frames instead of `result` payloads, conflicting with the documented API contract (`meta/prompts/mcp_audit.json:10`; `tests/test_stdio.py:238`).
- Logging lacks the required shutdown metadata and ISO timestamps mandated by v0.2.6 (`docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252`).

## Recommendations
- Build the TCP transport stack with shared NDJSON framing, host/port env (`MCP_HOST`, `MCP_PORT`), payload guard, readiness/shutdown logs, and an integration test similar to the socket suite (`docs/mcp_spec.md:19`; `mcp/__main__.py:47`; `tests/test_socket.py:45`).
- Update logging configuration to prepend ISO-8601 timestamps and include `schemas_dir`/`examples_dir` on shutdown records for all transports (`docs/mcp_spec.md:25`; `mcp/__main__.py:131`; `mcp/__main__.py:252`).
- Harden request parsing so invalid `params` (and similar semantic issues) yield `result` objects with `validation_failed`/`unsupported` reasons instead of generic JSON-RPC errors (`meta/prompts/mcp_audit.json:10`; `mcp/transport.py:41`; `tests/test_stdio.py:238`).
- Refresh README, `.env.example`, compose scripts, and helper tooling to document/select TCP alongside STDIO/socket once the server exists (`docs/mcp_spec.md:23`; `README.md:35`; `.env.example:2`; `docker-compose.yml:22`).
