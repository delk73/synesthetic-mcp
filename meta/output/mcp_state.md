## Summary of repo state
- MCP now defaults to TCP transport via `MCP_MODE` while still honoring legacy `MCP_ENDPOINT`, and docs/scripts were refreshed to match the new default (mcp/__main__.py:114-144; README.md:82-110; docker-compose.yml:18-33).
- Canonical schema enforcement rides on LABS env wiring, remote/cached resolution, and lifecycle logs that emit base/version/cache_dir across all transports (mcp/validate.py:90-288; mcp/__main__.py:211-240; tests/test_validate.py:200-219; tests/test_entrypoint.py:70-115).
- Governance coverage now includes canonicalised examples, a `governance_audit` RPC, and golden replay coverage for the new method (libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2; mcp/core.py:206-236; mcp/stdio_main.py:20-44; tests/fixtures/golden.jsonl:10).

## Top gaps & fixes (3-5 bullets)
- Expose `mcp --audit` CLI wiring to mirror spec v0.2.9 tooling expectations (docs/mcp_spec.md:118-124) so governance_audit is reachable outside JSON-RPC.
- Add unit coverage that forces local schema misses to assert httpx/caching fallback paths in `_fetch_canonical_schema` (mcp/validate.py:131-151) and prevent regressions.
- Extend docs/mcp_spec.md to mention `LABS_SCHEMA_CACHE_DIR`, staying in sync with README/env guidance (README.md:95-111; docs/mcp_spec.md:32-90).

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
