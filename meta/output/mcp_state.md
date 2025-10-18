# MCP Repo State Audit (v0.2.9)

## Summary of repo state
- Present — Version metadata, docs, and readiness flows align on v0.2.9 with canonical schema defaults (`mcp/__init__.py:6`, `README.md:95-111`, `tests/fixtures/golden.jsonl:10`).
- Present — Schema validation enforces canonical host, alias handling, payload cap, and traversal guards with comprehensive tests (`mcp/validate.py:26-376`, `tests/test_validate.py:62-260`, `tests/test_path_traversal.py:58-116`).
- Present — STDIO, socket, and TCP transports share the JSON-RPC pipeline, emit LABS metadata, and manage ready-file cleanup on signals (`mcp/transport.py:26-105`, `mcp/__main__.py:211-347`, `tests/test_stdio.py:200-265`, `tests/test_tcp.py:66-205`).
- Present — Governance audit, backend gating, and golden fixtures validate compliance behaviours (`mcp/core.py:210-240`, `tests/test_backend.py:25-210`, `tests/test_golden.py:18-99`).

## Top gaps & fixes (3-5 bullets)
- Update README’s submodule instructions to cite the pinned commit `8286df4a4197f2fb45a8bd6c4a805262cba2e934` instead of `0fdc842` (`README.md:136-142`, `.git/modules/libs/synesthetic-schemas/HEAD:1`).
- Align `.env` with documented defaults by appending the trailing slash to `LABS_SCHEMA_BASE` (`.env:9`, `docs/mcp_spec.md:96-108`).
- Add a regression test for `_tcp_port()` when `MCP_PORT` is unset to lock the 8765 fallback (`mcp/__main__.py:176-184`, `tests/test_tcp.py:89-205`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Version metadata v0.2.9 | Present | `mcp/__init__.py:6`, `README.md:2` |
| Canonical `$schema` host enforced | Present | `mcp/validate.py:97-148`, `tests/test_validate.py:226-235` |
| Legacy schema keys rejected | Present | `mcp/validate.py:297-302`, `tests/test_validate.py:238-249` |
| Remote schema resolution & cache | Present | `mcp/validate.py:150-210`, `tests/test_validate.py:252-260` |
| LABS env logged on readiness | Present | `mcp/__main__.py:215-347`, `tests/test_entrypoint.py:64-116` |
| Governance audit RPC | Present | `mcp/core.py:210-240`, `tests/test_golden.py:52-92` |
| Default transport `MCP_MODE=tcp` | Present | `mcp/__main__.py:125-145`, `README.md:82-104` |
| Default TCP port 8765 | Present | `mcp/__main__.py:30`, `docker-compose.yml:24-37`, `docs/mcp_spec.md:98-123` |
| Lifecycle logs include schema metadata | Present | `mcp/__main__.py:215-347`, `tests/test_socket.py:140-211` |
| Signals exit with -2 / -15 | Present | `mcp/__main__.py:482-503`, `tests/test_entrypoint.py:91-169` |
| 1 MiB payload guard | Present | `mcp/transport.py:26-79`, `tests/test_tcp.py:168-182` |
| Alias `validate` warning | Present | `mcp/stdio_main.py:29-33`, `tests/test_stdio.py:120-155` |
| `validate_many` honours `MCP_MAX_BATCH` | Present | `mcp/validate.py:354-376`, `tests/test_validate.py:131-156` |
| Deterministic listings/diffs | Present | `mcp/core.py:108-162`, `mcp/diff.py:16-51`, `tests/test_submodule_integration.py:28-42` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:186-204`, `tests/test_stdio.py:218-233` |
| Governance CLI helper (`--audit`) | Present | `mcp/__main__.py:418-446`, `tests/test_golden.py:52-82` |

## Submodule alignment (libs/synesthetic-schemas commit hash, version.json match)
- Present — Submodule HEAD resolves to `8286df4a4197f2fb45a8bd6c4a805262cba2e934` (`.git/modules/libs/synesthetic-schemas/HEAD:1`).
- Present — `version.json` publishes schemaVersion `0.7.3` matching the spec target (`libs/synesthetic-schemas/version.json:2`).
- Present — `make preflight` enforces schema publication parity and runs the MCP suite (`Makefile:5-34`).

## Transports
- Present — All transports delegate to the shared JSON-RPC pipeline with the 1 MiB guard (`mcp/transport.py:26-105`, `mcp/stdio_main.py:20-58`, `mcp/socket_main.py:27-122`, `mcp/tcp_main.py:25-127`).
- Present — Integration tests exercise readiness logs, payload checks, and teardown for STDIO, socket, and TCP (`tests/test_stdio.py:200-265`, `tests/test_socket.py:140-221`, `tests/test_tcp.py:66-205`).

## STDIO entrypoint & process model
- Present — STDIO mode logs LABS metadata, writes/removes the ready file, and exits cleanly on stdin close (`mcp/__main__.py:211-268`, `tests/test_stdio.py:200-265`).
- Present — Deprecated `validate` emits a warning while delegating to `validate_asset` (`mcp/stdio_main.py:29-34`, `tests/test_stdio.py:120-155`).

## Socket server (multi-client handling, perms, unlink, logs)
- Present — Socket server enforces 0600 permissions, tracks client threads, and unlinks the path on shutdown (`mcp/socket_main.py:27-104`, `tests/test_socket.py:140-221`).
- Present — Additional tests cover concurrent clients and cleanup paths (`tests/test_socket.py:312-400`).

## TCP server (binding, perms, multi-client, shutdown logs)
- Present — TCP server binds requested host/port, logs readiness with LABS metadata, and drains client threads on shutdown (`mcp/tcp_main.py:25-121`, `mcp/__main__.py:304-347`).
- Present — End-to-end tests cover payload guard, multi-client concurrency, and ready-file cleanup (`tests/test_tcp.py:66-520`).

## Lifecycle signals
- Present — Signal handlers convert SIGINT/SIGTERM into `_SignalShutdown`, preserving exit codes -2/-15 (`mcp/__main__.py:89-111`, `mcp/__main__.py:482-503`, `tests/test_entrypoint.py:91-169`, `tests/test_socket.py:202-221`, `tests/test_tcp.py:184-205`).

## Shutdown logging invariant
- Present — Ready/shutdown events log consistent metadata plus ISO timestamps, verified across transports (`mcp/__main__.py:215-347`, `tests/test_entrypoint.py:70-116`, `tests/test_tcp.py:248-288`).

## Ready file format
- Present — Ready file writes `<pid> <ISO8601>` and is removed on shutdown (`mcp/__main__.py:186-208`, `tests/test_stdio.py:218-265`, `tests/test_tcp.py:72-205`).

## Golden request/response examples
- Present — Golden replay covers schema listing, validation (including alias), examples, diff, backend guard, audit, and malformed frames (`tests/test_golden.py:18-99`, `tests/fixtures/golden.jsonl:1-11`).

## Payload size guard
- Present — MAX_BYTES check protects validation and transports with corresponding error payloads (`mcp/validate.py:32-83`, `mcp/transport.py:26-79`, `tests/test_validate.py:76-192`, `tests/test_tcp.py:168-182`).

## Schema validation contract
- Present — Validator enforces canonical `$schema`, alias remapping, legacy key rejection, and deterministic error ordering (`mcp/validate.py:97-340`, `tests/test_validate.py:62-260`).
- Present — Core APIs respect configured roots for schemas/examples and return validation errors on traversal attempts (`mcp/core.py:62-162`, `tests/test_path_traversal.py:58-116`).

## Schema resolver (remote/cached, traversal guards)
- Present — Canonical resolver supports cache, remote fetch fallback, and blocks traversal outside configured roots (`mcp/validate.py:150-210`, `tests/test_validate.py:252-260`, `tests/test_path_traversal.py:90-116`).

## Batching
- Present — `_max_batch` honours `MCP_MAX_BATCH` and surfaces `batch_too_large` when exceeded (`mcp/validate.py:36-46`, `mcp/validate.py:344-376`, `tests/test_validate.py:131-156`).

## Determinism & ordering
- Present — Listings, examples, diffs, and validation errors sort lexicographically for stable outputs (`mcp/core.py:108-162`, `mcp/diff.py:16-51`, `tests/test_validate.py:62-74`, `tests/test_submodule_integration.py:28-42`, `tests/test_diff.py:1-24`).

## Logging hygiene (fields, ISO time, stderr separation)
- Present — `_log_event` writes ISO-8601 UTC timestamps to stderr with schema metadata fields, and tests assert timestamp parsing (`mcp/__main__.py:53-78`, `mcp/__main__.py:215-347`, `tests/test_tcp.py:120-205`, `tests/test_socket.py:140-211`).

## Container & health (non-root, probes)
- Present — Docker image installs dependencies before dropping to user `mcp`, and tests assert non-root execution (`Dockerfile:23-30`, `tests/test_container.py:1-5`).
- Present — Compose service exposes readiness probe via ready file and binds default TCP port (`docker-compose.yml:24-40`).

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
- Present — Runtime reads and normalises transport, host/port, and ready-file configuration (`mcp/__main__.py:125-185`).
- Present — Schema helpers use LABS variables for canonical base, version, cache directory, and root discovery (`mcp/core.py:16-105`, `mcp/validate.py:36-46`, `mcp/validate.py:97-210`).
- Present — Documentation and samples list the same defaults for operators (`README.md:95-111`, `.env.example:2-13`).

## Documentation accuracy (canonical host/version, TCP `nc` example)
- Present — Spec and README document canonical LABS host/version, TCP defaults, and the `nc 127.0.0.1 8765` quick check (`docs/mcp_spec.md:96-123`, `README.md:95-226`).

## Detected divergences

## Recommendations
1. Update README to reflect the current submodule commit and avoid confusion during audits (`README.md:136-142`, `.git/modules/libs/synesthetic-schemas/HEAD:1`).
2. Normalize `.env`’s `LABS_SCHEMA_BASE` to include the canonical trailing slash for parity with docs and logs (`.env:9`, `mcp/core.py:16-24`).
3. Add a test case covering `_tcp_port()` when `MCP_PORT` is unset to guard the 8765 fallback (`mcp/__main__.py:176-184`, `tests/test_tcp.py:89-205`).
