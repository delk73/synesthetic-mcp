## Summary of repo state
- Implementation still targets the v0.2.7 baseline while spec/docs pin v0.2.9 (mcp/__init__.py:6, README.md:2).
- Validation enforces $schema presence and size guard but only resolves local aliases (mcp/validate.py:47-115).
- Lifecycle logging, ready file, and signal handling exist yet omit schema metadata and exit with 128+signal (mcp/__main__.py:185-439).
- Docs and Compose continue to describe stdio default and omit LABS env usage (README.md:35-221, docker-compose.yml:19-32).

## Top gaps & fixes (3-5 bullets)
- Enforce canonical schema host/version using LABS env defaults and update bundled examples (docs/mcp_spec.md:32-48, libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2).
- Add remote canonical resolver with cache guardrails driven by LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION (mcp/validate.py:47-115).
- Switch default transport to TCP via MCP_MODE + startup scripts and revise docs/examples (docs/mcp_spec.md:44-86, mcp/__main__.py:102-110).
- Expand ready/shutdown logs to include schemas_base, schema_version, cache_dir and fix signal exit codes to -2/-15 (docs/mcp_spec.md:52-70, mcp/__main__.py:185-439).
- Implement governance_audit RPC/CLI to satisfy v0.2.9 governance parity (docs/mcp_spec.md:112-124, mcp/stdio_main.py:14-39).

## Alignment with mcp_spec.md
| Spec item | Status | Evidence |
| - | - | - |
| Version metadata set to v0.2.9 | Divergent | mcp/__init__.py:6; README.md:2 |
| Canonical $schema host enforced | Missing | mcp/validate.py:63-109; libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2 |
| Remote schema resolution via LABS env | Missing | mcp/validate.py:47-115; docs/mcp_spec.md:32-48 |
| LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION read & logged | Missing | mcp/__main__.py:185-207; .env.example:1-9 |
| Governance audit endpoint | Missing | mcp/stdio_main.py:14-39; docs/mcp_spec.md:112-124 |
| Default TCP transport when unset | Divergent | mcp/__main__.py:102-110; docker-compose.yml:19-24 |
| Lifecycle logs include schema metadata | Divergent | mcp/__main__.py:185-309; docs/mcp_spec.md:52-70 |
| Signal exits -2 / -15 | Divergent | mcp/__main__.py:436-439; docs/mcp_spec.md:61-66 |
| Payload guard 1 MiB across transports | Present | mcp/transport.py:13-47; tests/test_tcp.py:89-121 |
| TCP multi-client ordering | Present | mcp/tcp_main.py:33-112; tests/test_tcp.py:240-330 |
| Ready file format `<pid> <ISO8601>` | Present | mcp/__main__.py:155-167; tests/test_entrypoint.py:55-112 |
| Legacy schema keys rejected | Present | mcp/validate.py:93-110; tests/test_validate.py:195-203 |

## Transports
- STDIO, socket, and TCP share the same parser/payload limits (mcp/transport.py:13-72; mcp/socket_main.py:65-123).
- TCP server spins threads per client with concurrency tests covering ordering (mcp/tcp_main.py:33-112; tests/test_tcp.py:240-330).
- Endpoint selection still hinges on MCP_ENDPOINT defaulting to stdio (mcp/__main__.py:102-110).

## STDIO entrypoint & process model
- `_run_stdio` emits ready/shutdown logs but without schema_base/schema_version fields (mcp/__main__.py:185-207).
- Dispatcher covers required tools and warns on `validate` alias (mcp/stdio_main.py:14-38).
- Final exit path converts negatives to 128+signal instead of preserving -sig (mcp/__main__.py:436-439).

## Socket server (multi-client handling, perms, unlink, logs)
- Binds Unix socket, chmods to configured mode, and unlinks on close (mcp/socket_main.py:25-78).
- Per-connection threads enforce the shared MAX_BYTES guard (mcp/socket_main.py:86-122).
- Tests verify cleanup and logging yet highlight missing schema metadata (tests/test_socket.py:52-175).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCPServer binds requested host/port and returns bound address (mcp/tcp_main.py:33-68).
- Threads handle each client with the shared payload guard (mcp/tcp_main.py:69-112).
- Tests confirm multi-client behavior and graceful shutdown, but logs lack schema fields (tests/test_tcp.py:66-330).

## Lifecycle signals
- SIGINT/SIGTERM handlers raise `_SignalShutdown` for coordinated shutdown (mcp/__main__.py:77-99).
- Integration tests assert ready/shutdown logs and cleanup across transports (tests/test_entrypoint.py:46-143; tests/test_tcp.py:200-238).
- Exit codes resolve to 128+signal despite spec calling for -2/-15 (mcp/__main__.py:436-439; docs/mcp_spec.md:61-66).

## Shutdown logging invariant
- Tests ensure shutdown entries include ready fields for stdio/tcp/socket (tests/test_entrypoint.py:73-108; tests/test_tcp.py:200-238).
- Required schema_base/schema_version/cache_dir keys are absent, breaking v0.2.9 logging contract (mcp/__main__.py:185-309; docs/mcp_spec.md:52-70).

## Ready file format
- Ready file writes `<pid> <ISO8601>` newline and removes on shutdown (mcp/__main__.py:155-178).
- Tests watch creation/removal on SIGTERM/SIGINT (tests/test_entrypoint.py:55-112; tests/test_tcp.py:200-238).

## Golden request/response examples
- Golden suite exercises list/get schema, validate/alias, get_example ok/invalid, diff, populate_backend, and malformed payloads (tests/test_golden.py:24-94; tests/fixtures/golden.jsonl:1-9).
- Responses remain deterministic but still use relative jsonschema paths (tests/fixtures/golden.jsonl:3-7).

## Payload size guard
- MAX_BYTES constant enforces 1 MiB limit prior to parsing (mcp/validate.py:21-44).
- Transports short-circuit oversize frames with payload_too_large responses (mcp/transport.py:13-47; mcp/socket_main.py:99-118).
- Tests cover validator and transport guards (tests/test_validate.py:68-184; tests/test_tcp.py:103-120).

## Schema validation contract
- Validator requires object payloads, mandates $schema, and rejects legacy keys (mcp/validate.py:63-110; tests/test_validate.py:187-203).
- Errors sorted for deterministic output (mcp/validate.py:111-121; tests/test_validate.py:54-66).
- Canonical host/version enforcement is absent; relative `jsonschema/...` markers remain accepted (mcp/validate.py:70-105; libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2).

## Schema resolver (remote/cached, traversal guards)
- `_schema_file_path` enforces root containment to block traversal (mcp/core.py:32-60).
- `_schema_name_from_marker` strips fragments and prevents `../` escapes (mcp/validate.py:70-105).
- No remote fetch/cache integration or LABS env wiring per v0.2.9 spec (mcp/validate.py:47-115; docs/mcp_spec.md:32-48).

## Batching
- `_max_batch` reads MCP_MAX_BATCH with validation and defaults to 100 (mcp/validate.py:21-40).
- `validate_many` stops at the configured limit and propagates payload errors (mcp/validate.py:123-160).
- Tests cover mixed outcomes, limit rejection, and oversize items (tests/test_validate.py:95-184).

## Determinism & ordering
- `list_schemas` orders results by name/version/path (mcp/core.py:78-112).
- `diff_assets` sorts operations deterministically (mcp/diff.py:10-47; tests/test_diff.py:1-15).
- Golden fixtures assert repeatable RPC responses (tests/test_golden.py:24-88).

## Logging hygiene (fields, ISO time, stderr separation)
- UTC ISO timestamps emitted via `_timestamp` (mcp/__main__.py:50-60).
- Logs go to stderr while stdout carries JSON-RPC frames only (mcp/__main__.py:54-67; mcp/stdio_main.py:41-57).
- Schema base/version/cache_dir never appear, leaving logging incomplete (mcp/__main__.py:185-309; docs/mcp_spec.md:52-70).

## Container & health (non-root, probes)
- Docker image drops to user `mcp` after install (Dockerfile:23-31).
- Compose service exposes ready-file healthcheck (docker-compose.yml:29-37).
- Ready file path configurable via MCP_READY_FILE (mcp/__main__.py:131-175).

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_MODE, MCP_HOST/PORT, MCP_MAX_BATCH)
- LABS env vars unused in code or env samples, blocking canonical host adoption (mcp/validate.py:21-160; .env.example:1-9; docs/mcp_spec.md:32-48).
- MCP_MODE ignored; selection still via MCP_ENDPOINT defaulting stdio (mcp/__main__.py:102-110; docs/mcp_spec.md:44-54).
- MCP_HOST/MCP_PORT honored for TCP binding (mcp/__main__.py:139-152; tests/test_tcp.py:66-148).
- MCP_MAX_BATCH respected with validation and tests (mcp/validate.py:21-43; tests/test_validate.py:123-148).

## Documentation accuracy (canonical host/version, TCP nc example)
- README frontmatter and feature list still reference v0.2.7 (README.md:2; README.md:35-38).
- TCP quickstart uses `nc localhost` instead of `127.0.0.1` and omits LABS env guidance (README.md:202-225; docs/mcp_spec.md:44-86).
- Documentation reiterates stdio default contrary to spec (README.md:34-221; docs/mcp_spec.md:44-54).

## Detected divergences
- Version banner and __version__ remain at v0.2.7 (README.md:2; mcp/__init__.py:6).
- Default transport controlled by MCP_ENDPOINT=stdio rather than MCP_MODE=tcp (mcp/__main__.py:102-110; docker-compose.yml:19-24).
- Ready/shutdown logs lack schema metadata fields required by v0.2.9 (mcp/__main__.py:185-309; docs/mcp_spec.md:52-70).
- Exit path returns 128+signal codes instead of -2/-15 (mcp/__main__.py:436-439; docs/mcp_spec.md:61-66).
- Validator accepts relative schemas and never consults LABS env or remote host (mcp/validate.py:47-115; libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2).
- Governance audit RPC/CLI absent (mcp/stdio_main.py:14-39; docs/mcp_spec.md:112-124).

## Recommendations
- Bump version metadata to v0.2.9 across package/docs and refresh README quickstart (mcp/__init__.py:6; README.md:2).
- Wire LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION through validation, logging, and examples with canonical URL enforcement (mcp/validate.py:47-121; mcp/__main__.py:185-309).
- Introduce remote schema resolver with safe caching and rejection of non-canonical hosts (docs/mcp_spec.md:32-48; mcp/validate.py:47-115).
- Adopt MCP_MODE default tcp in code, scripts, and docs while keeping MCP_ENDPOINT alias for back-compat (mcp/__main__.py:102-110; docker-compose.yml:19-24).
- Extend logging to include schemas_base/schema_version/cache_dir and fix signal exit codes to meet spec (mcp/__main__.py:185-439; docs/mcp_spec.md:52-70).
- Add governance_audit RPC plus CLI flag mirroring spec expectations (docs/mcp_spec.md:112-124; mcp/stdio_main.py:14-39).
