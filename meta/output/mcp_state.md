# MCP Repo State Audit (v0.2.9)

## Summary of repo state
- Present — Version metadata, docs, and governance surface align on v0.2.9 with canonical schema defaults and audit responses (mcp/__init__.py:6; README.md:95; mcp/core.py:210-240; tests/fixtures/golden.jsonl:10).
- Present — Canonical $schema enforcement, resolver guards, payload cap, and batching controls are implemented and exercised by tests (mcp/validate.py:32-375; mcp/transport.py:26-105; tests/test_validate.py:62-193).
- Present — STDIO, socket, and TCP transports emit readiness/shutdown logs with schema metadata, manage ready files, and honour signal semantics (mcp/__main__.py:211-356; tests/test_entrypoint.py:39-119; tests/test_tcp.py:113-190).
- Divergent — TCP fallback port remains 7000 in code while spec/docs/docker-compose expect 8765 (mcp/__main__.py:30; docs/mcp_spec.md:98; docker-compose.yml:24-37).

## Top gaps & fixes (3-5 bullets)
- Divergent — Update `DEFAULT_TCP_PORT` to 8765 so runtime matches documented default (mcp/__main__.py:30; README.md:103; docs/mcp_spec.md:98).
- Missing coverage — Add a regression test that asserts `_tcp_port()` returns 8765 when `MCP_PORT` is unset to catch future drift (mcp/__main__.py:176-184; tests/test_tcp.py:89-123).
- Follow-up — After correcting the default, rerun `pytest` (Makefile:32-34) and adjust readiness log assertions if they rely on the literal port value (tests/test_tcp.py:120-190).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Version metadata v0.2.9 | Present | mcp/__init__.py:6; README.md:2 |
| Canonical `$schema` host enforced | Present | mcp/validate.py:97-148; tests/test_validate.py:226-235 |
| Legacy schema keys rejected | Present | mcp/validate.py:297-302; tests/test_validate.py:238-249 |
| Remote schema resolution & cache | Present | mcp/validate.py:150-205; tests/test_validate.py:252-260 |
| LABS env logged on readiness | Present | mcp/__main__.py:215-347; tests/test_entrypoint.py:70-105 |
| Governance audit RPC | Present | mcp/core.py:210-240; tests/fixtures/golden.jsonl:10 |
| Default transport `MCP_MODE=tcp` | Present | mcp/__main__.py:125-145; README.md:97 |
| Default TCP port 8765 | Divergent | mcp/__main__.py:30; docker-compose.yml:24-37; docs/mcp_spec.md:98 |
| Lifecycle logs include schema metadata | Present | mcp/__main__.py:215-347; tests/test_socket.py:138-211 |
| Signals exit with -2 / -15 | Present | mcp/__main__.py:482-503; tests/test_entrypoint.py:91-116 |
| 1 MiB payload guard | Present | mcp/transport.py:26-79; mcp/validate.py:32-83; tests/test_socket.py:186-198 |
| `validate_many` honours `MCP_MAX_BATCH` | Present | mcp/validate.py:354-376; tests/test_validate.py:131-156 |
| Deterministic listings/diffs | Present | mcp/core.py:108-162; mcp/diff.py:16-51; tests/test_validate.py:62-74 |
| Ready file `<pid> <ISO8601>` | Present | mcp/__main__.py:186-194; tests/test_stdio.py:218-233 |
| Governance CLI helper (`--audit`) | Present | mcp/__main__.py:418-446; tests/test_golden.py:52-82 |

## Submodule alignment (libs/synesthetic-schemas commit hash, version.json match)
- Present — Submodule HEAD is pinned to 8286df4a4197f2fb45a8bd6c4a805262cba2e934 with schemaVersion 0.7.3 (.git/modules/libs/synesthetic-schemas/HEAD:1; libs/synesthetic-schemas/version.json:2).
- Present — `make preflight` enforces canonical host publication and MCP test suite (Makefile:5-34).

## Transports
- Present — Shared JSON-RPC parsing enforces MAX_BYTES across STDIO, socket, and TCP handlers (mcp/transport.py:26-105; mcp/stdio_main.py:20-38; mcp/socket_main.py:27-122; mcp/tcp_main.py:25-127).
- Present — Integration tests cover each transport’s lifecycle and guardrails (tests/test_stdio.py:49-389; tests/test_socket.py:68-223; tests/test_tcp.py:66-450).

## STDIO entrypoint & process model
- Present — STDIO mode logs readiness, writes the ready file, and exits cleanly when stdin closes (mcp/__main__.py:211-248; tests/test_stdio.py:200-265).
- Present — Deprecated `validate` alias warns via stderr while dispatching to `validate_asset` (mcp/stdio_main.py:29-33; tests/test_stdio.py:105-155).

## Socket server (multi-client handling, perms, unlink, logs)
- Present — Socket server sets 0600 permissions, handles client threads, and unlinks the path on shutdown (mcp/socket_main.py:27-76; tests/test_socket.py:68-223).
- Present — Multi-client concurrency and cleanup are validated (tests/test_socket.py:312-400).

## TCP server (binding, perms, multi-client, shutdown logs)
- Present — TCP server binds requested host/port, logs readiness/shutdown with schema metadata, and closes clients on exit (mcp/tcp_main.py:25-127; mcp/__main__.py:304-347).
- Present — Tests cover multi-client exchanges, payload guard, and shutdown cleanup (tests/test_tcp.py:113-450).
- Divergent — Default fallback still binds port 7000 instead of 8765 when `MCP_PORT` is unset (mcp/__main__.py:30; docs/mcp_spec.md:98).

## Lifecycle signals
- Present — SIGINT/SIGTERM install custom handlers, propagate `_SignalShutdown`, and re-signal the process for negative exit codes (mcp/__main__.py:89-115; mcp/__main__.py:482-503).
- Present — Tests assert -2/-15 exits across transports (tests/test_entrypoint.py:91-116; tests/test_socket.py:202-222; tests/test_tcp.py:271-289).

## Shutdown logging invariant
- Present — Shutdown logs mirror readiness fields (mode, host/path, schemas_base, schema_version, cache_dir) with ISO timestamps (mcp/__main__.py:215-347).
- Present — Tests verify ready vs shutdown field parity (tests/test_entrypoint.py:85-107; tests/test_tcp.py:272-280).

## Ready file format
- Present — Ready file writes `<pid> <ISO8601>` on startup and removes it on shutdown (mcp/__main__.py:186-208; mcp/__main__.py:487-488).
- Present — Tests assert exact format and cleanup (tests/test_stdio.py:218-265; tests/test_tcp.py:452-455).

## Golden request/response examples
- Present — Golden tape covers list/get schema, validate/alias, get_example ok/invalid, diff, backend populate, governance audit, and malformed JSON-RPC (tests/fixtures/golden.jsonl:1-11; tests/test_golden.py:18-99).

## Payload size guard
- Present — Validator rejects payloads exceeding 1 MiB before validation and transports short-circuit oversized frames (mcp/validate.py:32-83; mcp/transport.py:26-79; mcp/tcp_main.py:98-123).
- Present — Tests exercise oversized payload handling in STDIO, socket, TCP, and backend flows (tests/test_validate.py:76-193; tests/test_socket.py:186-198; tests/test_tcp.py:168-182; tests/test_backend.py:73-81).

## Schema validation contract
- Present — Assets require top-level `$schema`, canonical host, and reject legacy keys; errors sort deterministically (mcp/validate.py:266-342; tests/test_validate.py:62-223).
- Present — Nested alias mapping normalizes examples to canonical schema names (mcp/validate.py:26-312; tests/test_validate.py:62-87).

## Schema resolver (remote/cached, traversal guards)
- Present — `_schema_target` enforces canonical prefix, normalizes aliases, and blocks traversal (mcp/validate.py:97-148).
- Present — Remote fetch uses httpx with optional cache writes, while `_schema_file_path` prevents escaping configured roots (mcp/validate.py:150-205; mcp/core.py:47-105).
- Present — Tests cover cache directory writes and rejection of non-canonical hosts/relative escapes (tests/test_validate.py:203-260).

## Batching
- Present — `validate_many` enforces `MCP_MAX_BATCH`, aggregates per-item results, and surfaces payload errors (mcp/validate.py:344-376; tests/test_validate.py:131-193).

## Determinism & ordering
- Present — Schema/example listings and diff operations sort lexicographically and normalize root patch paths (mcp/core.py:108-162; mcp/diff.py:16-51).
- Present — Tests confirm deterministic error ordering and diff payloads (tests/test_validate.py:62-74; tests/test_golden.py:18-82).

## Logging hygiene (fields, ISO time, stderr separation)
- Present — `_log_event` emits ISO-8601 UTC timestamps to stderr with structured fields (mcp/__main__.py:53-70).
- Present — Transport logs include mode, schemas_dir/examples_dir, schemas_base, schema_version, and cache_dir (mcp/__main__.py:215-347; tests/test_entrypoint.py:70-105).

## Container & health (non-root, probes)
- Present — Dockerfile installs dependencies as root, then drops privileges to user `mcp`; compose healthcheck uses ready file (Dockerfile:23-30; docker-compose.yml:33-43).
- Present — Test suite asserts non-root container configuration (tests/test_container.py:4-5).

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
- Present — Core helpers expose LABS defaults, cache directory, and schema prefix for logging and resolution (mcp/core.py:16-45; mcp/validate.py:90-151).
- Present — Entrypoint derives transports and port/host from env with `MCP_MODE` defaulting to tcp (mcp/__main__.py:125-185).
- Present — Docs and `.env.example` enumerate required variables and defaults (README.md:95-111; .env.example:1-13).

## Documentation accuracy (canonical host/version, TCP nc example)
- Present — README includes canonical host/version env table and `nc 127.0.0.1 8765` example (README.md:95-228).
- Present — Spec document ties implementation to v0.2.9 requirements and exit criteria (docs/mcp_spec.md:94-155).
- Divergent — README/docker-compose assume port 8765 while code defaults to 7000 (README.md:103; docker-compose.yml:24-37; mcp/__main__.py:30).

## Detected divergences
- Divergent — Runtime default TCP port is 7000, conflicting with spec, docs, and container defaults expecting 8765 (mcp/__main__.py:30; docs/mcp_spec.md:98; docker-compose.yml:24-37).

## Recommendations
- Update `DEFAULT_TCP_PORT` to 8765 and add regression coverage for the fallback to ensure parity with documentation and deployments (mcp/__main__.py:30; tests/test_tcp.py:89-123).
- Re-run `make preflight` after the change to verify schema publication and test suite integrity (Makefile:5-34).
- Confirm readiness/shutdown log assertions remain valid after adjusting the default port (tests/test_tcp.py:113-190; tests/test_entrypoint.py:70-105).
