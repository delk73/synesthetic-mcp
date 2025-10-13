# MCP Repo State Audit (v0.2.9)

## Summary of repo state
- Version banners in `__init__.py` and `README.md` still read v0.2.7, diverging from v0.2.9 spec.
- Local schema loading persists; remote canonical resolution absent.
- Environment variables `LABS_SCHEMA_BASE` and `LABS_SCHEMA_VERSION` unread in code.
- Examples embed relative `$schema`, not canonical host.
- Ready logs omit `schemas_base` and `schema_version` fields.
- TCP `nc` example uses `localhost` instead of mandated `127.0.0.1`.
- Governance audit endpoint missing.

## Top gaps & fixes (3-5 bullets)
- Update version to v0.2.9 in `__init__.py` and `README.md`.
- Implement reading and logging of `LABS_SCHEMA_BASE` and `LABS_SCHEMA_VERSION` at startup.
- Enable remote canonical schema resolution using environment-driven URLs.
- Update examples to use canonical `$schema` URLs.
- Add governance audit endpoint and TCP `nc 127.0.0.1 8765` example to README.

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec Item | Status | Evidence |
|-----------|--------|----------|
| Schema host/version (v0.2.9) | Missing | No `LABS_SCHEMA_BASE`/`LABS_SCHEMA_VERSION` usage; examples use relative paths (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`) |
| Schema resolution (v0.2.9) | Divergent | Local only; no remote/cache (`mcp/validate.py:50`; `mcp/validate.py:106`) |
| No legacy schema keys | Present | Rejects `"schema"` or `"$schemaRef"` with `validation_failed` at `path="/$schema"` (`mcp/validate.py:171`) |
| Env parity | Missing | `LABS_SCHEMA_BASE` and `LABS_SCHEMA_VERSION` unread (`mcp/__main__.py:185`) |
| Governance parity | Missing | No `governance_audit` endpoint (`docs/mcp_spec.md:101`) |
| Transport compliance | Present | STDIO/Socket/TCP exist (`mcp/stdio_main.py:1`; `mcp/socket_main.py:1`; `mcp/tcp_main.py:1`) |
| Payload cap | Present | 1 MiB guard enforced across all transports (`mcp/transport.py:26`; `tests/test_tcp.py:161`) |
| Alias | Present | `"validate"` aliases `"validate_asset"` with deprecation warning (`mcp/stdio_main.py:23`) |
| Batching | Present | `validate_many` honors `MCP_MAX_BATCH` (`mcp/validate.py:233`) |
| get_example | Present | Returns `validation_failed` when example invalid (`tests/fixtures/golden.jsonl:7`) |
| Determinism | Present | Sorting implemented for listings, diffs, errors (`mcp/core.py:75`; `mcp/diff.py:1`; `mcp/validate.py:195`) |
| Security | Present | Socket/TCP perms default to least-privilege; container runs non-root (`mcp/socket_main.py:20`; `Dockerfile:26`) |
| Process model | Present | STDIO exits on stdin close; Socket/TCP log readiness; unlink/close on shutdown (`mcp/__main__.py:200`; `mcp/socket_main.py:35`; `mcp/tcp_main.py:45`) |
| Logging | Divergent | Missing `schemas_base`/`schema_version`/`cache_dir` fields (`mcp/__main__.py:185`) |
| Signal handling | Present | SIGINT/SIGTERM return documented exit codes (`mcp/__main__.py:195`) |
| Shutdown logging | Divergent | Mirrors but incomplete (missing fields) (`mcp/__main__.py:220`) |
| Ready file format | Present | Exactly `"<pid> <ISO8601 timestamp>"` (`mcp/__main__.py:155`) |
| Golden examples | Present | Covers required methods including alias and malformed (`tests/fixtures/golden.jsonl:1`) |
| Docs TCP nc example | Divergent | Uses `localhost` instead of `127.0.0.1` (`README.md:195`) |
| Version metadata updated to v0.2.9 | Divergent | Still v0.2.7 (`mcp/__init__.py:6`; `README.md:2`) |

## Transports
- STDIO: Present (`mcp/stdio_main.py`)
- Socket: Present (`mcp/socket_main.py`)
- TCP: Present (`mcp/tcp_main.py`)
- HTTP/gRPC: Missing (roadmap-only)

## STDIO entrypoint & process model
- Present: STDIO over JSON-RPC 2.0 (`mcp/stdio_main.py:40`)
- Process model: Exits on stdin close (`mcp/__main__.py:200`)

## Socket server (multi-client handling, perms, unlink, logs)
- Multi-client: Ordering preserved via threading (`mcp/socket_main.py:50`)
- Perms: Default to least-privilege (`mcp/socket_main.py:20`)
- Unlink: On shutdown (`mcp/socket_main.py:35`)
- Logs: Readiness logged (`mcp/__main__.py:280`)

## TCP server (binding, perms, multi-client, shutdown logs)
- Binding: Configurable host/port (`mcp/tcp_main.py:25`)
- Perms: Default to least-privilege (no explicit perms in code, but container non-root)
- Multi-client: Threaded handling (`mcp/tcp_main.py:55`)
- Shutdown logs: Logged before exit (`mcp/__main__.py:295`)

## Lifecycle signals
- SIGINT/SIGTERM: Handled with exit codes -2/-15 (`mcp/__main__.py:195`)

## Shutdown logging invariant
- Divergent: Mirrors ready but omits `schemas_base`/`schema_version` (`mcp/__main__.py:220`)

## Ready file format
- Present: `"<pid> <ISO8601>"` (`mcp/__main__.py:155`)

## Golden request/response examples
- Present: Covers list_schemas, get_schema, validate_asset + alias validate, get_example ok/invalid, diff_assets, malformed JSON-RPC (`tests/fixtures/golden.jsonl`)

## Payload size guard
- Present: 1 MiB enforced across STDIO/Socket/TCP with failing tests (`mcp/validate.py:28`; `tests/test_tcp.py:161`)

## Schema validation contract
- Present: Draft 2020-12 validation (`mcp/validate.py:9`)

## Schema resolver (remote/cached, traversal guards)
- Divergent: Local only; no remote/cache; path traversal blocked (`mcp/validate.py:50`)

## Batching
- Present: `validate_many` honors `MCP_MAX_BATCH` (`mcp/validate.py:233`)

## Determinism & ordering
- Present: Sorting for listings (`mcp/core.py:75`), diffs (`mcp/diff.py`), errors (`mcp/validate.py:195`)

## Logging hygiene (fields, ISO time, stderr separation)
- Divergent: Missing fields; ISO timestamps present; stderr for logs (`mcp/__main__.py:54`)

## Container & health (non-root, probes)
- Non-root: Present (`Dockerfile:26`)
- Probes: Not specified in spec

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_HOST/PORT, MCP_MAX_BATCH)
- LABS_SCHEMA_BASE: Missing
- LABS_SCHEMA_VERSION: Missing
- MCP_HOST/PORT: Present (`mcp/__main__.py:102`)
- MCP_MAX_BATCH: Present (`mcp/validate.py:28`)

## Documentation accuracy (canonical host/version, TCP nc example)
- Divergent: Missing env docs; TCP uses `localhost` not `127.0.0.1` (`README.md:195`)

## Detected divergences
- Version still v0.2.7
- Schema resolution local-only
- Missing env vars usage
- Incomplete logging fields
- TCP nc example wording

## Recommendations
- Update `__version__` and README to v0.2.9 (`mcp/__init__.py:6`; `README.md:2`)
- Implement `LABS_SCHEMA_BASE`/`LABS_SCHEMA_VERSION` reading and remote resolution
- Update examples `$schema` to canonical URLs
- Add `schemas_base`/`schema_version` to logs
- Add TCP `nc 127.0.0.1 8765` example to README
- Implement `governance_audit` endpoint
