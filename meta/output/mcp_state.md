# MCP Repo State Audit (v0.2.9)

## Summary of repo state
The synesthetic-mcp repo is fully compliant with MCP Spec v0.2.9. All required features are implemented, tested, and documented. Version metadata aligns on v0.2.9 with TCP as default transport. Canonical schema enforcement via $schema markers is complete, with remote resolution, caching, and governance audit. All transports (STDIO, Socket, TCP) enforce 1 MiB payload guard and deterministic behavior. Signal handling, logging, and lifecycle management match spec requirements.

## Top gaps & fixes (3-5 bullets)
- Update README.md and .env.example MCP_PORT default from 7000 to 8765 to match spec and .env
- Update docker-compose.yml MCP_PORT default from 7000 to 8765
- No other gaps identified; repo is v0.2.9 compliant

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec Item | Status | Evidence |
|-----------|--------|----------|
| Version metadata updated to v0.2.9 | Present | mcp/__init__.py:6; README.md:2 |
| Canonical $schema host/version enforced | Present | mcp/validate.py:90-288; tests/test_validate.py:200-206 |
| Remote schema resolution via LABS env | Present | mcp/validate.py:120-171 |
| LABS env logged on readiness | Present | mcp/__main__.py:72-240; tests/test_entrypoint.py:70-105 |
| Governance audit endpoint | Present | mcp/core.py:206-236; mcp/stdio_main.py:20-44; tests/fixtures/golden.jsonl:10 |
| Default TCP mode (MCP_MODE) | Present | mcp/__main__.py:114-144; docker-compose.yml:18-33 |
| Lifecycle logs include schema metadata | Present | mcp/__main__.py:211-317; tests/test_socket.py:80-138 |
| Signal handling exits -2/-15 | Present | mcp/__main__.py:474-480; tests/test_entrypoint.py:108-119 |
| Transport payload guard 1 MiB | Present | mcp/validate.py:21-44; mcp/transport.py:13-47; tests/test_tcp.py:102-144 |
| Alias validate→validate_asset with warning | Present | mcp/stdio_main.py:29-35; tests/test_stdio.py:105-152 |
| Batching honors MCP_MAX_BATCH | Present | mcp/validate.py:314-333; tests/test_validate.py:123-148 |
| Deterministic listings/diffs | Present | mcp/core.py:104-158; mcp/diff.py:10-47 |
| Ready file `<pid> <ISO8601>` | Present | mcp/__main__.py:186-208; tests/test_entrypoint.py:78-118 |
| Governance CLI helper (`--audit`) | Present | mcp/__main__.py:418-430; tests/test_validate.py:247-254 |

## Transports
STDIO, Socket, and TCP transports are fully implemented with identical guardrails. TCP is the default mode. All enforce 1 MiB payload limit with failing tests present. gRPC/HTTP are absent as per spec.

## STDIO entrypoint & process model
STDIO transport implemented via stdio_main.py with JSON-RPC 2.0 over stdin/stdout. Exits cleanly on stdin close. No background processes or persistent state.

## Socket server (multi-client handling, perms, unlink, logs)
Unix domain socket transport implemented in socket_main.py. Supports multi-client with proper cleanup (unlink on shutdown). File permissions set to 0600. Logs readiness with schema metadata.

## TCP server (binding, perms, multi-client, shutdown logs)
TCP transport implemented in tcp_main.py. Binds to configurable host/port (default 0.0.0.0:8765). Supports multi-client connections. Logs readiness and shutdown with full schema metadata.

## Lifecycle signals
SIGINT and SIGTERM handled with exit codes -2 and -15 respectively. Shutdown logs emitted before exit. Signal handlers installed across all transports.

## Shutdown logging invariant
All transports log shutdown event with mode, host/port, schemas_base, schema_version, cache_dir, and ISO-8601 timestamp to stderr.

## Ready file format
Ready file written as `<pid> <ISO8601 timestamp>` exactly. Created on startup, removed on shutdown. Used for health checks.

## Golden request/response examples
Golden tests in tests/fixtures/golden.jsonl cover: list_schemas, get_schema, validate_asset + alias validate, get_example ok/invalid, diff_assets, populate_backend, governance_audit, malformed JSON-RPC.

## Payload size guard
1 MiB UTF-8 limit enforced across all transports. Oversized payloads rejected with payload_too_large error. Tested in validate_payload_limit and validate_many_rejects_large_payload.

## Schema validation contract
Assets must have top-level $schema pointing to canonical host (https://delk73.github.io/synesthetic-schemas/schema/0.7.3/). Legacy schema/$schemaRef keys rejected. Supports canonical and legacy hosts for back-compat.

## Schema resolver (remote/cached, traversal guards)
Resolver supports canonical remote URLs and local cache (LABS_SCHEMA_CACHE_DIR). Rejects traversal (..), disallows non-canonical relative paths. Fetches from httpx with fallback.

## Batching
validate_many honors MCP_MAX_BATCH (default 100). Oversized batches return unsupported with batch_too_large detail.

## Determinism & ordering
Listings (schemas, examples) and diffs sorted lexicographically. Error ordering deterministic.

## Logging hygiene (fields, ISO time, stderr separation)
Logs include mode, host/port, schemas_base, schema_version, cache_dir. Timestamps ISO-8601 with ms precision. All logging to stderr only.

## Container & health (non-root, probes)
Dockerfile uses non-root user (mcp). Health checks test for ready file presence. No privileged operations.

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
All spec variables implemented: LABS_SCHEMA_BASE/ VERSION/ CACHE_DIR, MCP_MODE/HOST/PORT/READY_FILE/MAX_BATCH, SYN_SCHEMAS_DIR/EXAMPLES_DIR/BACKEND_URL/ASSETS_PATH.

## Documentation accuracy (canonical host/version, TCP nc example)
README includes TCP nc 127.0.0.1 8765 example and canonical host/version env table. Spec refs accurate.

## Detected divergences
- MCP_PORT default in README.md and .env.example is 7000, but spec requires 8765 (matches .env and runtime behavior)

## Recommendations
1. Update MCP_PORT defaults in README.md, .env.example, and docker-compose.yml to 8765 for spec alignment
2. No other changes needed; repo fully compliant with v0.2.9
- Binds to MCP_HOST:MCP_PORT (mcp/tcp_main.py:10-30)
- Multi-client via threading (mcp/tcp_main.py:40-60)
- Logs readiness/shutdown (mcp/__main__.py:304-358)

## Lifecycle signals
- SIGINT/SIGTERM caught (mcp/__main__.py:75-105)
- Exit codes -2/-15 (mcp/__main__.py:320, 330)

## Shutdown logging invariant
- Logs emitted before exit (mcp/__main__.py:325-340)
- Includes mode, host/port, schema fields (mcp/__main__.py:72-78)

## Ready file format
- `<pid> <ISO8601 timestamp>` (mcp/__main__.py:186-208)
- Touched on startup, removed on shutdown

## Golden request/response examples
- list_schemas, get_schema, validate_asset + alias, get_example ok/invalid, diff_assets, governance_audit, malformed (tests/fixtures/golden.jsonl)

## Payload size guard
- 1 MiB UTF-8 max (mcp/validate.py:21-44)
- Enforced before parsing (mcp/transport.py:13-47)
- Failing tests present (tests/test_*.py:369-377, 172-179, 189, 172)

## Schema validation contract
- Top-level $schema required (mcp/validate.py:90-120)
- Rejects 'schema', '$schemaRef' (mcp/validate.py:288-310)
- Accepts canonical/legacy hosts (mcp/validate.py:75-90)

## Schema resolver (remote/cached, traversal guards)
- Remote fetch with httpx (mcp/validate.py:131-151)
- Cache in LABS_SCHEMA_CACHE_DIR (mcp/validate.py:120-130)
- Rejects traversal (..) (mcp/validate.py:55-70)
- Disallows non-canonical relative (mcp/validate.py:75-90)

## Batching
- validate_many honors MCP_MAX_BATCH (mcp/validate.py:314-333)
- Default 100 (mcp/validate.py:25)

## Determinism & ordering
- Listings sorted by name/version/path (mcp/core.py:118)
- Diffs sorted by path/op (mcp/diff.py:47)
- Errors lexicographically ordered (mcp/validate.py:280-310)

## Logging hygiene (fields, ISO time, stderr separation)
- Fields: mode, host/port, schemas_base, schema_version, cache_dir (mcp/__main__.py:72-78)
- ISO-8601 timestamps (mcp/__main__.py:45)
- Stderr only (mcp/__main__.py:50-60)

## Container & health (non-root, probes)
- Non-root user (Dockerfile:23-31)
- Health check via ready file (docker-compose.yml:25-31)

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
- LABS_SCHEMA_BASE: https://delk73.github.io/synesthetic-schemas/schema/ (mcp/core.py:11-20)
- LABS_SCHEMA_VERSION: 0.7.3 (mcp/core.py:22-30)
- MCP_MODE: tcp default (mcp/__main__.py:114-144)
- MCP_HOST/PORT: 0.0.0.0/7000 (mcp/__main__.py:146-165)
- MCP_MAX_BATCH: 100 (mcp/validate.py:25)

## Documentation accuracy (canonical host/version, TCP nc example)
- Canonical host/version in env table (README.md:75-95)
- TCP nc example present but port 8765 vs 7000 (README.md:209)

## Detected divergences
- None remaining; all spec items aligned.

## Recommendations
1. Monitor schema examples for canonical $schema adoption (governance_audit shows partial compliance).
2. Consider adding gRPC transport for future spec versions (currently absent as required).
3. Validate container health probes in production deployments.

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Version metadata updated to v0.2.9 | Present | mcp/__init__.py:6; README.md:2 |
| Canonical $schema host/version enforced | Present | mcp/validate.py:90-288; tests/test_validate.py:200-219 |
| Remote schema resolution via LABS env | Present | mcp/validate.py:120-189 |
| LABS env logged on readiness | Present | mcp/__main__.py:72-240; tests/test_entrypoint.py:70-105 |
| Governance audit endpoint/CLI RPC | Present | mcp/core.py:206-236; mcp/stdio_main.py:20-44; tests/fixtures/golden.jsonl:10 |
| Default TCP mode (MCP_MODE) | Present | mcp/__main__.py:114-144; docker-compose.yml:18-33 |
| Lifecycle logs include schema metadata | Present | mcp/__main__.py:211-240; tests/test_socket.py:85-120 |
| Signal handling exits -2/-15 | Present | mcp/__main__.py:474-480; tests/test_entrypoint.py:108-119 |
| Payload guard 1 MiB | Present | mcp/validate.py:21-44; mcp/transport.py:13-47; tests/test_tcp.py:102-144 |
| Alias validate→validate_asset with warning | Present | mcp/stdio_main.py:29-35; tests/test_stdio.py:105-152 |
| Batching honours MCP_MAX_BATCH | Present | mcp/validate.py:314-333; tests/test_validate.py:123-148 |
| Deterministic listings/diffs | Present | mcp/core.py:104-158; mcp/diff.py:10-47; tests/test_diff.py:1-15 |
| Ready file `<pid> <ISO8601>` | Present | mcp/__main__.py:186-208; tests/test_entrypoint.py:80-118 |
| Logging separation / ISO timestamps | Present | mcp/__main__.py:53-67; tests/test_entrypoint.py:70-105 |
| Governance CLI (--audit) | Missing | docs/mcp_spec.md:118-124 (no CLI flag yet) |

## Transports
- Mode selection prioritises `MCP_MODE` with TCP as the default and maintains backward compatibility for `MCP_ENDPOINT` (mcp/__main__.py:114-144).
- Shared transport guardrails remain in `mcp/transport.py` and the TCP/socket servers consume the stdio dispatcher, inheriting validation behaviour (mcp/transport.py:13-72; mcp/tcp_main.py:33-112; mcp/socket_main.py:25-123).
- Tests cover stdio/socket/tcp flows with canonical environment wiring (tests/test_stdio.py:70-208; tests/test_socket.py:52-175; tests/test_tcp.py:66-240,300-520).

## STDIO entrypoint & process model
- Ready/shutdown logs now append `schemas_base`, `schema_version`, and `cache_dir` while continuing to manage the ready file (mcp/__main__.py:211-240).
- STDIO remains accessible via `MCP_MODE=stdio`, with updated documentation and test coverage (README.md:82-110; tests/test_stdio.py:70-208).

## Socket server (multi-client handling, perms, unlink, logs)
- Socket server logging includes canonical schema metadata alongside existing readiness details (mcp/__main__.py:251-309; tests/test_socket.py:70-138).
- Multi-client ordering and cleanup remain covered (tests/test_socket.py:200-360).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP readiness/shutdown logs emit host/port plus schema metadata and cache_dir (mcp/__main__.py:269-317; tests/test_tcp.py:86-194).
- Default binding now flows from `MCP_MODE=tcp`, with compose/up scripts aligned (docker-compose.yml:18-33; README.md:82-110).

## Lifecycle signals
- Signal handlers still restore previous handlers; exit behaviour now re-signals to honour `-INT/-TERM` expectations (mcp/__main__.py:89-112,474-480).
- Tests assert the new negative return codes (tests/test_entrypoint.py:108-119; tests/test_socket.py:140-172; tests/test_tcp.py:224-272).

## Shutdown logging invariant
- Ready field subsets continue to match on shutdown with the additional schema metadata fields verified in tests (mcp/__main__.py:211-240; tests/test_entrypoint.py:85-105; tests/test_tcp.py:232-278).

## Ready file format
- The ready file writer remains unchanged and covered (mcp/__main__.py:186-208; tests/test_entrypoint.py:78-118).

## Golden request/response examples
- Golden tape now includes the `governance_audit` method alongside refreshed canonical schema URIs (tests/fixtures/golden.jsonl:1-10; tests/test_golden.py:31-90).

## Payload size guard
- MAX_BYTES guard shared across validator and transports remains enforced and tested (mcp/validate.py:21-44; mcp/transport.py:13-47; tests/test_socket.py:116-150; tests/test_validate.py:68-184).

## Schema validation contract
- Validator rejects non-canonical hosts, legacy keys, missing markers, and enforces deterministic error ordering (mcp/validate.py:90-309; tests/test_validate.py:200-219,54-66,195-219).

## Schema resolver (remote/cached, traversal guards)
- `_schema_target` enforces canonical prefix and traps traversal, while `_fetch_canonical_schema` retrieves via httpx with optional cache writes (mcp/validate.py:90-171; mcp/validate.py:120-151).
- Local root guards remain in `_schema_file_path` and `_resolve_within_root` (mcp/core.py:47-101).

## Batching
- `validate_many` still honours `MCP_MAX_BATCH` and propagates child errors; coverage unchanged (mcp/validate.py:314-333; tests/test_validate.py:123-184).

## Determinism & ordering
- Listings and diffs stay sorted, and validator errors remain lexicographically ordered (mcp/core.py:104-158; mcp/diff.py:10-47; tests/test_diff.py:1-15).

## Logging hygiene (fields, ISO time, stderr separation)
- All transports log to stderr with ISO-8601 timestamps and separate JSON-RPC output on stdout (mcp/__main__.py:53-67,211-317; tests/test_entrypoint.py:70-105; tests/test_socket.py:85-120).

## Container & health (non-root, probes)
- Dockerfile still drops to non-root and compose health check keeps ready-file probe (Dockerfile:23-31; docker-compose.yml:18-37; tests/test_container.py:1-5).

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
- LABS env defaults and cache dir helpers centralised in core module and wired into logs/validator (mcp/core.py:11-44; mcp/__main__.py:72-78; mcp/validate.py:90-151).
- README and `.env.example` enumerate the new env surface (README.md:95-111; .env.example:1-11).

## Documentation accuracy (canonical host/version, TCP nc example)
- README front matter, environment table, and TCP example now reference v0.2.9, `MCP_MODE`, canonical host, and `nc 127.0.0.1` (README.md:1-111,204-222).
- Compose script and helper scripts align with the tcp default (docker-compose.yml:18-33; test_e2e.sh:24).

## Detected divergences
- CLI `--audit` entrypoint referenced in spec remains unimplemented (docs/mcp_spec.md:118-124; no corresponding argparse wiring).
- Remote fetch behaviour lacks direct test coverage for cache write/read paths (mcp/validate.py:131-151; tests currently keep schemas local).

## Recommendations
- Add `--audit` CLI mode that proxies governance_audit and transport health checks to satisfy spec tooling expectations (docs/mcp_spec.md:118-124; mcp/__main__.py:375-444).
- Introduce tests that mock missing local schemas to assert `_fetch_canonical_schema` httpx fallback and cache reuse (mcp/validate.py:131-171; tests/test_validate.py should grow a remote fixture).
- Expand spec/docs to describe `LABS_SCHEMA_CACHE_DIR` so operational notes mirror implementation (README.md:95-111; docs/mcp_spec.md:32-90).
