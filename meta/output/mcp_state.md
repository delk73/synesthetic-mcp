# MCP Repo State Audit (v0.2.9)

## Summary of repo state
- Present — Version metadata and README pin the adapter at v0.2.9 with canonical schema defaults (`mcp/__init__.py:6`, `README.md:2`, `README.md:95`).
- Present — Validation enforces canonical `$schema`, rejects legacy keys, caps payloads at 1 MiB, and blocks traversal with regression coverage (`mcp/validate.py:292`, `mcp/validate.py:300`, `tests/test_validate.py:80`, `tests/test_path_traversal.py:36`).
- Present — STDIO/socket/TCP reuse the JSON-RPC parser, emit LABS logging fields, and clean up ready-files on shutdown signals (`mcp/transport.py:26`, `mcp/__main__.py:319`, `tests/test_stdio.py:205`, `tests/test_tcp.py:184`).
- Missing — `get_schema` currently ignores the spec-required `resolution` modes (`preserve`/`inline`/`bundled`) and always returns the raw schema (`docs/mcp_spec.md:67`, `mcp/core.py:128`, `tests/test_labs_integration.py:15`).

## Top gaps & fixes (3-5 bullets)
- Missing — Implement the `resolution` parameter in `get_schema` with `preserve`/`inline`/`bundled` outputs and extend dispatch/tests to exercise each mode (`docs/mcp_spec.md:67`, `mcp/core.py:128`, `tests/test_labs_integration.py:15`).
- Divergent — README still instructs checking out submodule commit `0fdc842`, while the repo pins `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`README.md:136`, `.git/modules/libs/synesthetic-schemas/HEAD:1`).
- Missing — Public docs omit the `resolution` parameter entirely, leaving downstream clients without guidance once the API lands (`docs/get_schema_api.md:15`, `docs/mcp_spec.md:67`).
- Missing — Add a regression that starts the TCP server with `MCP_PORT` unset to lock the 8765 fallback (`mcp/__main__.py:176`, `tests/test_tcp.py:68`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Version metadata v0.2.9 | Present | `mcp/__init__.py:6`, `README.md:2` |
| Canonical `$schema` host enforced | Present | `mcp/validate.py:292`, `tests/test_validate.py:231` |
| Legacy schema keys rejected | Present | `mcp/validate.py:300`, `tests/test_validate.py:245` |
| Remote schema resolution & cache fallback | Present | `mcp/validate.py:169`, `tests/test_validate.py:256` |
| LABS env logged on readiness | Present | `mcp/__main__.py:319`, `tests/test_entrypoint.py:70` |
| `get_schema` resolution modes (`preserve`/`inline`/`bundled`) | Missing | `docs/mcp_spec.md:67`, `mcp/core.py:128` |
| Default transport `MCP_MODE=tcp` | Present | `mcp/__main__.py:125`, `README.md:97` |
| Default TCP port 8765 | Present | `mcp/__main__.py:176`, `docker-compose.yml:24` |
| Lifecycle logs include schema metadata | Present | `mcp/__main__.py:319`, `tests/test_socket.py:137` |
| Signals exit with -2 / -15 | Present | `mcp/__main__.py:482`, `tests/test_entrypoint.py:115` |
| 1 MiB payload guard | Present | `mcp/transport.py:28`, `tests/test_tcp.py:169` |
| Alias `validate` warning | Present | `mcp/stdio_main.py:35`, `tests/test_stdio.py:150` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:192`, `tests/test_stdio.py:225` |

## Submodule alignment (libs/synesthetic-schemas commit hash, version.json match)
- Present — Submodule HEAD resolves to the audited commit `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`.git/modules/libs/synesthetic-schemas/HEAD:1`).
- Present — `version.json` advertises schemaVersion `0.7.3`, matching the adapter defaults and preflight target (`libs/synesthetic-schemas/version.json:2`, `Makefile:8`).

## Transports
- Present — STDIO, socket, and TCP servers all call the shared parser with the transport-wide 1 MiB cap (`mcp/transport.py:26`, `mcp/stdio_main.py:20`, `mcp/socket_main.py:53`, `mcp/tcp_main.py:56`).
- Present — Integration tests assert readiness logs, payload errors, and teardown paths across transports (`tests/test_stdio.py:205`, `tests/test_socket.py:137`, `tests/test_tcp.py:137`).

## STDIO entrypoint & process model
- Present — `_run_stdio` logs LABS metadata, writes the ready file, and flushes shutdown logs on exit (`mcp/__main__.py:211`, `tests/test_stdio.py:205`).
- Present — Deprecated `validate` emits a warning before delegating to `validate_asset` (`mcp/stdio_main.py:35`, `tests/test_stdio.py:150`).

## Socket server (multi-client handling, perms, unlink, logs)
- Present — Socket server enforces 0600 permissions, tracks client threads, and unlinks the socket on close (`mcp/socket_main.py:35`, `mcp/socket_main.py:51`, `tests/test_socket.py:152`).
- Present — Concurrency and shutdown flow verified with multiple clients and signal handling (`tests/test_socket.py:312`, `tests/test_socket.py:305`).

## TCP server (binding, perms, multi-client, shutdown logs)
- Present — TCP server binds requested host/port, logs canonical LABS metadata, and drains client threads on shutdown (`mcp/tcp_main.py:31`, `mcp/__main__.py:319`, `mcp/tcp_main.py:53`).
- Present — Tests cover multi-client traffic, payload guard behaviour, and signal-driven teardown (`tests/test_tcp.py:137`, `tests/test_tcp.py:169`, `tests/test_tcp.py:184`).

## Lifecycle signals
- Present — Signal handlers raise `_SignalShutdown` and main translates SIGINT/SIGTERM into exit codes -2/-15 with cleanup verified in tests (`mcp/__main__.py:89`, `mcp/__main__.py:482`, `tests/test_entrypoint.py:115`).

## Shutdown logging invariant
- Present — Ready/shutdown logs always include mode plus LABS metadata and ISO timestamps across transports (`mcp/__main__.py:215`, `mcp/__main__.py:339`, `tests/test_tcp.py:185`).

## Ready file format
- Present — Ready file contents are `<pid> <ISO8601>` and cleared on shutdown (`mcp/__main__.py:192`, `tests/test_stdio.py:225`, `tests/test_tcp.py:204`).

## get_schema implementation and modes
- Present — Core function returns schema metadata, extracts version from `$id`, and rejects traversal attempts (`mcp/core.py:151`, `tests/test_path_traversal.py:39`).
- Missing — `resolution` parameter is ignored by dispatch; only `name` and `version` are processed (`mcp/core.py:128`, `mcp/stdio_main.py:24`).
- Missing — No implementation for `inline` or `bundled` outputs; responses always mirror on-disk schema with `$ref`s intact (`mcp/core.py:168`, `tests/test_labs_integration.py:15`).
- Missing — Golden fixtures and docs do not cover the spec-required resolution modes (`tests/fixtures/golden.jsonl:2`, `docs/get_schema_api.md:13`).

## Golden request/response examples
- Present — Golden replay validates list/validate/diff/audit flows and deprecated alias logging (`tests/test_golden.py:18`, `tests/fixtures/golden.jsonl:1`).
- Missing — No golden coverage for `get_schema` `resolution` modes, so new behaviours would lack regression data (`tests/fixtures/golden.jsonl:2`, `docs/mcp_spec.md:67`).

## Payload size guard
- Present — MAX_BYTES enforces 1 MiB across validation and transports with consistent error payloads (`mcp/validate.py:32`, `mcp/transport.py:28`, `tests/test_validate.py:80`, `tests/test_tcp.py:169`).

## Schema validation contract
- Present — Validator normalises schema aliases, rejects legacy keys, and sorts errors deterministically (`mcp/validate.py:298`, `mcp/validate.py:333`, `tests/test_validate.py:74`).
- Present — Path resolution stays within configured roots for schemas and examples, returning validation errors on traversal (`mcp/core.py:62`, `tests/test_path_traversal.py:36`).

## Schema resolver (remote/cached, traversal guards)
- Present — Resolver loads canonical schemas via cache/remote fallback, mapping `$schema` markers to canonical filenames and blocking non-canonical prefixes (`mcp/validate.py:169`, `mcp/validate.py:287`, `tests/test_validate.py:256`).
- Present — LABS environment helpers normalise base/version values with trailing slash enforcement (`mcp/core.py:16`, `mcp/core.py:30`).

## Batching
- Present — `_max_batch` reads `MCP_MAX_BATCH`, errors on invalid values, and `validate_many` surfaces `batch_too_large` when the limit is exceeded (`mcp/validate.py:36`, `mcp/validate.py:354`, `tests/test_validate.py:138`).

## Determinism & ordering
- Present — Schema listings and diffs are sorted lexicographically, with tests asserting deterministic ordering (`mcp/core.py:124`, `mcp/diff.py:50`, `tests/test_submodule_integration.py:34`, `tests/test_diff.py:15`).

## Logging hygiene (fields, ISO time, stderr separation)
- Present — `_log_event` writes ISO-8601 UTC timestamps to stderr alongside schema metadata, and readiness tests parse timestamps for validity (`mcp/__main__.py:57`, `mcp/__main__.py:215`, `tests/test_entrypoint.py:70`).
- Present — Shutdown paths flush stderr and include schema metadata before closing transports (`mcp/__main__.py:234`, `mcp/__main__.py:338`, `tests/test_tcp.py:185`).

## Container & health (non-root, probes)
- Present — Dockerfile drops privileges to user `mcp`, satisfying non-root execution expectations (`Dockerfile:24`, `tests/test_container.py:4`).
- Present — Compose service exposes ready-file health checks and binds default host/port via environment overrides (`docker-compose.yml:24`, `docker-compose.yml:35`).

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
- Present — CLI normalises legacy `MCP_ENDPOINT`, transport selection, host/port, and ready-file paths (`mcp/__main__.py:125`, `mcp/__main__.py:170`, `mcp/__main__.py:162`).
- Present — Schema helpers honour LABS base/version/cache overrides with default fallbacks (`mcp/core.py:16`, `mcp/core.py:34`, `mcp/core.py:30`).
- Present — Docs and `.env.example` mirror these defaults for operators (`README.md:95`, `.env.example:2`).

## Documentation accuracy (canonical host/version, TCP `nc` example)
- Present — README documents the LABS environment table and the `nc 127.0.0.1 8765` TCP quick check (`README.md:95`, `README.md:209`).
- Missing — API docs omit the `resolution` parameter despite the spec mandate (`docs/get_schema_api.md:15`, `docs/mcp_spec.md:67`).

## Detected divergences
- Divergent — README’s submodule checkout instructions reference commit `0fdc842` instead of the pinned `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`README.md:136`, `.git/modules/libs/synesthetic-schemas/HEAD:1`).
- Missing — `get_schema` resolution support is absent across implementation, tests, golden fixtures, and docs (`mcp/core.py:128`, `tests/test_labs_integration.py:15`, `tests/fixtures/golden.jsonl:2`, `docs/get_schema_api.md:15`).

## Recommendations
1. Implement `get_schema` resolution modes end-to-end (core logic, STDIO/TCP/socket dispatch, golden fixtures, and tests) to satisfy the v0.2.9 contract (`docs/mcp_spec.md:67`, `mcp/core.py:128`, `tests/test_labs_integration.py:15`).
2. Correct README submodule guidance to match the pinned commit and avoid operators checking out the wrong revision (`README.md:136`, `.git/modules/libs/synesthetic-schemas/HEAD:1`).
3. Add regression coverage for `_tcp_port` defaulting to 8765 and document the `resolution` parameter in `docs/get_schema_api.md` once the implementation lands (`mcp/__main__.py:176`, `tests/test_tcp.py:68`, `docs/get_schema_api.md:15`).
