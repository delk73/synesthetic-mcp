## Summary of repo state
# MCP Repo State Audit (v0.2.9)

## Summary of repo state
- Version remains at 0.2.7, not updated to 0.2.9
- Local schema loading implemented, but remote canonical resolution missing
- Environment variables LABS_SCHEMA_BASE and LABS_SCHEMA_VERSION not read or logged
- Examples use relative $schema paths, not canonical host URLs
- Ready/shutdown logs lack schemas_base and schema_version fields
- TCP nc example missing from README
- Governance audit endpoint not implemented

## Top gaps & fixes (3-5 bullets)
- Update __version__ to "0.2.9" in mcp/__init__.py
- Implement remote schema resolution using LABS_SCHEMA_BASE and LABS_SCHEMA_VERSION
- Update examples to use canonical $schema URLs
- Add schemas_base and schema_version to ready/shutdown logs
- Add TCP nc example to README

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)

| Spec Item | Status | Evidence |
|-----------|--------|----------|
| Schema host/version (v0.2.9) | Missing | No LABS_SCHEMA_BASE/ LABS_SCHEMA_VERSION usage; examples use relative paths |
| Schema resolution (v0.2.9) | Divergent | Local loading only; no remote canonical URLs or cache |
| No legacy schema keys | Present | mcp/validate.py:171 rejects "schema"/"$schemaRef" |
| Env parity | Missing | No LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION in code |
| Governance parity | Missing | No governance_audit endpoint |
| Transport compliance | Present | STDIO, Socket, TCP implemented |
| Payload cap | Present | 1 MiB guard in transport.py:26; tests in test_tcp.py:161 |
| Alias | Present | stdio_main.py:23 accepts "validate" with warning |
| Batching | Present | validate_many honors MCP_MAX_BATCH |
| get_example | Present | Returns validation_failed on invalid; core.py:155 |
| Determinism | Present | Sorting in list_schemas, diff_assets, errors |
| Security | Present | Socket/TCP perms set; container non-root |
| Process model | Present | STDIO exits on stdin close; logs on ready |
| Logging | Divergent | Missing schemas_base/schema_version; stderr logs ok |
| Signal handling | Present | -SIGINT/-SIGTERM codes |
| Shutdown logging | Divergent | Mirrors ready but missing fields |
| Ready file format | Present | <pid> <ISO8601> format |
| Golden examples | Present | Covers required methods including alias and malformed |
| Docs TCP nc example | Missing | No nc command in README.md |
| Audit incomplete | N/A | Report generated |

## Transports
- STDIO: Present via stdio_main.py
- Socket: Present via socket_main.py, multi-threaded but no ordering guarantee
- TCP: Present via tcp_main.py, 1 MiB guard enforced

## STDIO entrypoint & process model
- Present: stdio_main.py handles JSON-RPC loop
- Exits on stdin close: Yes, for line in sys.stdin

## Socket server (multi-client handling, perms, unlink, logs)
- Multi-client: Threaded handling, no explicit ordering
- Perms: os.chmod in socket_main.py:22
- Unlink: unlink on close
- Logs: Ready log emitted

## TCP server (binding, perms, multi-client, shutdown logs)
- Binding: socket.bind in tcp_main.py:23
- Perms: SO_REUSEADDR set
- Multi-client: Threaded
- Shutdown logs: Emitted before exit

## Lifecycle signals
- SIGINT/SIGTERM handled: Yes, _SignalShutdown raised
- Exit codes: -2 for SIGINT, -15 for SIGTERM

## Shutdown logging invariant
- Mirrors ready: Yes, same fields
- Emitted before exit: Yes, in finally block
- No self-kill: No os.kill calls

## Ready file format
- Format: <pid> <ISO8601> in _write_ready_file

## Golden request/response examples
- Covers: list_schemas, get_schema, validate_asset, validate alias, get_example ok/invalid, diff_assets, malformed

## Payload size guard
- Enforced: transport.py checks len(encoded) > MAX_BYTES
- Failing test: test_tcp.py:161 sends oversized payload

## Schema validation contract
- $schema required: validate.py:157
- Rejects legacy keys: validate.py:171
- Canonical host not enforced

## Schema resolver (remote/cached, traversal guards)
- Remote: Missing
- Cached: Local registry built but not from env cache dir
- Traversal: PathOutsideConfiguredRoot raised

## Batching
- Honors MCP_MAX_BATCH: Yes, validate_many checks len(assets) > limit

## Determinism & ordering
- Listings: Sorted in list_schemas/list_examples
- Diffs: Sorted by path/op
- Errors: Sorted by path/msg

## Logging hygiene (fields, ISO time, stderr separation)
- Fields: Divergent, missing schemas_base/schema_version
- ISO time: Yes, _timestamp()
- Stderr: Yes, sys.stderr.write

## Container & health (non-root, probes)
- Non-root: USER mcp in Dockerfile
- Probes: Not specified in spec

## Environment variables (LABS_SCHEMA_BASE, LABS_SCHEMA_VERSION, MCP_HOST/PORT, MCP_MAX_BATCH)
- LABS_SCHEMA_BASE: Missing
- LABS_SCHEMA_VERSION: Missing
- MCP_HOST/PORT: Used in tcp_main.py
- MCP_MAX_BATCH: Used in validate.py

## Documentation accuracy (canonical host/version, TCP nc example)
- Canonical host/version: Not documented
- TCP nc example: Missing

## Detected divergences
- Schema resolution uses local paths, not remote canonical
- Ready logs lack required fields
- Examples not using canonical $schema
- Version not updated

## Recommendations
- Update mcp/__init__.py:6 to "0.2.9"
- Add LABS_SCHEMA_BASE and LABS_SCHEMA_VERSION env reading and logging in __main__.py
- Implement remote resolver in validate.py using httpx for canonical URLs
- Update examples $schema to https://delk73.github.io/synesthetic-schemas/schema/0.7.3/...
- Modify ready log to include schemas_base and schema_version
- Add governance_audit method
- Add TCP nc example to README.md

## Top gaps & fixes (3-5 bullets)
- Missing — Add a test or script that scans `libs/synesthetic-schemas/examples` to assert each JSON includes a non-empty `$schema` (spec demands regression guard) (`docs/mcp_spec.md:36`; `libs/synesthetic-schemas/examples/Tone_Example.json:1`)
- Divergent — Bump `__version__` and README front-matter `version` to v0.2.8 so tooling reflects shipped spec level (`mcp/__init__.py:6`; `README.md:2`)
- Divergent — Update README TCP quickstart to match the mandated `nc 127.0.0.1 8765` example (`docs/mcp_spec.md:46`; `README.md:195`)

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| 1 MiB guard across transports | Present | `mcp/transport.py:26`; `mcp/socket_main.py:110`; `tests/test_tcp.py:161` |
| Ready/shutdown logs mirror metadata | Present | `mcp/__main__.py:232`; `mcp/__main__.py:303`; `tests/test_entrypoint.py:66` |
| Signal exits surface `-SIGINT` / `-SIGTERM` | Present | `mcp/__main__.py:424`; `tests/test_socket.py:211`; `tests/test_tcp.py:194` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:155`; `tests/test_stdio.py:214` |
| `validate` alias warns and delegates | Present | `mcp/stdio_main.py:23`; `tests/test_tcp.py:247` |
| `$schema` required, legacy keys rejected | Present | `mcp/validate.py:171`; `mcp/validate.py:181`; `tests/test_validate.py:187` |
| Examples `$schema` regression guard | Missing | `docs/mcp_spec.md:36`; _no automated check in tests_ |
| Docs include TCP `nc 127.0.0.1 8765` example | Divergent | `docs/mcp_spec.md:46`; `README.md:195` |
| Version metadata reflects v0.2.8 | Divergent | `mcp/__init__.py:6`; `README.md:2` |

## Transports
- Present — `process_line` enforces JSON-RPC structure, 1 MiB cap, and result-wrapped errors for STDIO (`mcp/transport.py:26`; `tests/test_stdio.py:107`)
- Present — Socket and TCP reuse the dispatcher, decode NDJSON, and apply the size guard before decode (`mcp/socket_main.py:95`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:98`; `tests/test_socket.py:179`)

## STDIO entrypoint & process model
- Present — Entrypoint logs mode with directories, writes ready file, and clears it on exit (`mcp/__main__.py:185`; `mcp/__main__.py:429`; `tests/test_stdio.py:214`)
- Present — Loop exits cleanly when stdin closes, emitting shutdown log (`tests/test_stdio.py:149`; `tests/test_stdio.py:162`)

## Socket server (multi-client handling, perms, unlink, logs)
- Present — Socket setup enforces `0600` perms, logs ready/shutdown, and unlinks socket on close (`mcp/socket_main.py:27`; `mcp/socket_main.py:51`; `tests/test_socket.py:145`)
- Present — Multi-client ordering succeeds with concurrent readers (`tests/test_socket.py:274`)

## TCP server (binding, perms, multi-client, shutdown logs)
- Present — TCP server binds requested host/port, logs resolved port, and mirrors fields on shutdown (`mcp/tcp_main.py:25`; `mcp/tcp_main.py:283`; `mcp/tcp_main.py:303`; `tests/test_tcp.py:117`)
- Present — Supports concurrent clients with deterministic response ordering (`tests/test_tcp.py:229`)

## Lifecycle signals
- Present — Signal handler escalates to `_SignalShutdown`, producing documented negative return codes verified by tests (`mcp/__main__.py:424`; `tests/test_socket.py:211`; `tests/test_tcp.py:194`)

## Shutdown logging invariant
- Present — Shutdown logs flush before exit and retain readiness fields (`mcp/__main__.py:250`; `mcp/__main__.py:303`; `tests/test_entrypoint.py:85`)

## Ready file format
- Present — Writes `<pid> <ISO8601>` and removes file on exit (`mcp/__main__.py:155`; `tests/test_stdio.py:214`; `tests/test_entrypoint.py:105`)

## Golden request/response examples
- Present — Golden replay covers list/get schema, validation alias, batch, examples (valid/invalid), diff, backend, and malformed JSON-RPC (`tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1`)

## Payload size guard
- Present — Validation and backend populate reject oversized assets with `payload_too_large` (`mcp/validate.py:161`; `mcp/backend.py:23`; `tests/test_validate.py:68`; `tests/test_backend.py:71`)
- Present — Transports send `payload_too_large` results for oversized frames (`mcp/socket_main.py:110`; `tests/test_tcp.py:161`)

## Schema validation contract
- Present — Enforces `$schema`, blocks legacy keys, normalizes schema lookup, and sorts errors (`mcp/validate.py:171`; `mcp/validate.py:181`; `mcp/validate.py:224`; `tests/test_validate.py:195`)
- Missing — No suite asserts every example file retains `$schema` despite spec guard requirement (`docs/mcp_spec.md:36`; `tests/test_submodule_integration.py:37`)

## Batching
- Present — `validate_many` clamps non-list params, enforces `MCP_MAX_BATCH`, and surfaces per-item results (`mcp/validate.py:233`; `mcp/validate.py:240`; `tests/test_validate.py:95`; `tests/test_validate.py:123`)

## Logging hygiene
- Present — `_log_event` emits ISO-8601 timestamps to stderr while stdout only carries JSON-RPC frames (`mcp/__main__.py:54`; `mcp/stdio_main.py:45`; `tests/test_stdio.py:96`)
- Present — Deprecated alias warning logged once per call (`mcp/stdio_main.py:26`; `tests/test_stdio.py:136`)

## Container & health
- Present — Dockerfile drops to non-root user `mcp` and compose healthcheck uses ready file (`Dockerfile:23`; `Dockerfile:26`; `docker-compose.yml:30`)
- Present — Compose `serve` service exports transport env vars and runs entrypoint directly (`docker-compose.yml:20`; `docker-compose.yml:36`)

## Schema discovery & validation
- Present — Lists sort deterministically and respect env overrides; path traversal guarded for schemas/examples (`mcp/core.py:64`; `mcp/core.py:119`; `tests/test_env_discovery.py:31`; `tests/test_path_traversal.py:33`)
- Present — Examples validated lazily and return `validation_failed` when invalid (`mcp/core.py:167`; `tests/test_validate.py:32`)

## Test coverage
- Present — Transport loops, signal shutdowns, batching, backend, diff, and schema discovery covered via pytest matrix (`tests/test_socket.py:149`; `tests/test_tcp.py:229`; `tests/test_backend.py:116`; `.github/workflows/ci.yml:9`)

## Dependencies & runtime
- Present — Minimal runtime deps declared (`requirements.txt:1`; `requirements.txt:2`) with pytest for tests (`requirements.txt:3`)
- Optional — `referencing` handled defensively for local registry support (`mcp/validate.py:10`; `mcp/validate.py:106`)

## Environment variables
- Present — Entrypoint resolves transports and directories from env overrides (`mcp/__main__.py:102`; `mcp/__main__.py:139`; `.env.example:2`)
- Present — Backend settings controlled via `SYN_BACKEND_URL` / `SYN_BACKEND_ASSETS_PATH` (`mcp/backend.py:12`; `.env.example:8`)

## Documentation accuracy
- Divergent — README quickstart uses `nc localhost 8765` instead of mandated `nc 127.0.0.1 8765` example (`docs/mcp_spec.md:46`; `README.md:195`)
- Divergent — README metadata banner still marks v0.2.7 (`README.md:2`)
- Present — README documents transports, payload guard, alias status, and env vars (`README.md:28`; `README.md:110`)

## Detected divergences
- Version metadata lags spec level (code/docs show 0.2.7) (`mcp/__init__.py:6`; `README.md:2`)
- TCP client example host deviates from mandated `127.0.0.1` (`docs/mcp_spec.md:46`; `README.md:195`)

## Recommendations
- Add a test (e.g., in `tests/test_validate.py`) to assert each example JSON contains a non-empty `$schema`, failing otherwise (`docs/mcp_spec.md:36`; `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`)
- Update `mcp/__init__.py` and README front matter to v0.2.8 to reflect implemented spec (`mcp/__init__.py:6`; `README.md:2`)
- Adjust README TCP quickstart to use `nc 127.0.0.1 8765` per spec wording (`docs/mcp_spec.md:46`; `README.md:195`)
