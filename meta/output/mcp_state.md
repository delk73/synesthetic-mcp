## Summary of repo state
- Validation now enforces the v0.2.8 `$schema` contract, rejecting legacy `schema`/`$schemaRef` keys before JSON Schema evaluation (`mcp/validate.py:146`, `mcp/validate.py:150`, `tests/test_validate.py:185`).
- Examples, fixtures, and golden transcripts emit `$schema` markers, keeping transport and backend flows deterministic with updated assets (`libs/synesthetic-schemas/examples/Control-Bundle_Example.json:2`, `tests/fixtures/golden.jsonl:3`, `tests/test_backend.py:98`).
- Transports, lifecycle logging, and payload guards remain unchanged and fully covered by the existing suite (`mcp/__main__.py:185`, `tests/test_socket.py:146`, `tests/test_tcp.py:167`).

## Top gaps & fixes (3-5 bullets)
- Cross-check asset `$schema` values against the requested schema name to detect mismatched payloads early (`mcp/validate.py:146`).
- Document canonical `$schema` URIs for each schema to guide clients on expected values (`README.md:38`, `docs/mcp_spec.md:20`).
- Extend CI linting to assert every example under `libs/synesthetic-schemas/examples/` continues to embed `$schema` (e.g., lightweight checker in `.github/workflows/`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB payload cap | Present | `mcp/transport.py:28`; `tests/test_stdio.py:355`; `tests/test_socket.py:185`; `tests/test_tcp.py:167` |
| Ready/shutdown logs mirror metadata and precede exit | Present | `mcp/__main__.py:185`; `mcp/__main__.py:304`; `tests/test_entrypoint.py:85`; `tests/test_socket.py:283` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:156`; `mcp/__main__.py:432`; `tests/test_stdio.py:210`; `tests/test_tcp.py:252` |
| Signal exits surface `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:295`; `mcp/__main__.py:439`; `tests/test_entrypoint.py:105`; `tests/test_tcp.py:194` |
| `validate` alias warns and relies on asset $schema | Present | `mcp/stdio_main.py:23`; `mcp/stdio_main.py:28`; `tests/test_stdio.py:29`; `tests/test_stdio.py:108` |
| `validate_many` honours `MCP_MAX_BATCH` | Present | `mcp/validate.py:92`; `mcp/validate.py:113`; `tests/test_validate.py:103`; `tests/test_validate.py:120` |
| Socket perms 0600 + multi-client ordering | Present | `mcp/socket_main.py:27`; `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP multi-client handling + shutdown logs | Present | `mcp/tcp_main.py:25`; `mcp/tcp_main.py:304`; `tests/test_tcp.py:321`; `tests/test_tcp.py:411` |
| Schema traversal guard (local only) | Present | `mcp/core.py:18`; `mcp/core.py:62`; `tests/test_path_traversal.py:34`; `tests/test_path_traversal.py:61` |
| Assets MUST include top-level `$schema`; reject `schema/$schemaRef` | Present | `mcp/validate.py:146`; `mcp/validate.py:150`; `tests/test_validate.py:185`; `tests/fixtures/golden.jsonl:3`; `libs/synesthetic-schemas/examples/Control-Bundle_Example.json:2` |

## Transports
- Unified dispatcher continues to serve STDIO, socket, and TCP endpoints with NDJSON framing and shared tooling (`mcp/stdio_main.py:14`, `mcp/socket_main.py:53`, `mcp/tcp_main.py:56`).
- Pre-decode payload guard defends every transport path, producing deterministic `payload_too_large` results (`mcp/transport.py:28`, `tests/test_tcp.py:167`).
- Integration tests still cover malformed frames, multi-client sequences, and shutdown behavior across transports (`tests/test_stdio.py:162`, `tests/test_socket.py:346`, `tests/test_tcp.py:321`).

## STDIO entrypoint & process model
- Entry process logs readiness/shutdown with schema/example directories, writes the ready file, and drains stdin before exit (`mcp/__main__.py:185`, `mcp/__main__.py:204`, `tests/test_stdio.py:203`).
- CLI `--validate` path validates assets using their `$schema` markers and returns the raw result (`mcp/__main__.py:360`, `tests/test_entrypoint.py:244`).

## Socket server (multi-client handling, perms, unlink, logs)
- Socket listeners create 0600 endpoints, spawn per-client threads, and unlink on shutdown (`mcp/socket_main.py:27`, `mcp/socket_main.py:49`).
- Tests assert permissions, multi-client ordering, and shutdown logging invariants (`tests/test_socket.py:146`, `tests/test_socket.py:346`, `tests/test_socket.py:407`).

## TCP server (binding, perms, multi-client, shutdown logs)
- TCP server binds requested/ephemeral ports, tracks the bound address, and drains worker threads on close (`mcp/tcp_main.py:25`, `mcp/tcp_main.py:54`).
- Tests exercise oversize payload handling, multi-client concurrency, and signal-driven shutdown (`tests/test_tcp.py:167`, `tests/test_tcp.py:321`, `tests/test_tcp.py:411`).

## Lifecycle signals
- `_SignalShutdown` propagates SIGINT/SIGTERM to negative exit codes while preserving shutdown logs (`mcp/__main__.py:78`, `mcp/__main__.py:295`).
- Suites confirm exit codes and ready-file cleanup after signals (`tests/test_entrypoint.py:105`, `tests/test_tcp.py:194`).

## Shutdown logging invariant
- All transports log readiness/shutdown with identical metadata prior to exit (`mcp/__main__.py:185`, `mcp/__main__.py:304`).
- Tests compare ready vs shutdown payloads to guarantee parity and ordering (`tests/test_entrypoint.py:85`, `tests/test_socket.py:283`).

## Golden request/response examples
- Golden transcript mirrors the updated `$schema` contract across validate, alias, batching, and backend flows (`tests/fixtures/golden.jsonl:3`, `tests/test_golden.py:45`).

## Payload size guard
- Transport parser surfaces `payload_too_large` without JSON decoding (`mcp/transport.py:28`, `mcp/transport.py:75`).
- Validation helpers and backend population enforce the same limit for asset payloads (`mcp/validate.py:136`, `tests/test_validate.py:156`, `tests/test_backend.py:59`).

## Schema validation contract
- `validate_asset` requires `$schema`, rejects legacy keys, and strips the marker before Draft 2020-12 validation (`mcp/validate.py:146`, `mcp/validate.py:157`).
- Tests cover missing `$schema`, legacy key rejection, and reused batching flows (`tests/test_validate.py:185`, `tests/test_validate.py:193`).

## Batching
- `validate_many` delegates to `validate_asset`, so per-item `$schema` enforcement and payload guards apply consistently (`mcp/validate.py:199`, `tests/test_validate.py:103`).
- Batch limit handling remains unchanged and covered by regression tests (`tests/test_validate.py:118`).

## Logging hygiene
- Structured stderr logging with ISO timestamps remains centralised in `_log_event` and exercised across transports (`mcp/__main__.py:60`, `tests/test_entrypoint.py:66`).
- Golden tests and stdio integration confirm stdout contains JSON-RPC frames only (`tests/test_stdio.py:120`, `tests/test_golden.py:63`).

## Container & health
- Dockerfile continues to drop privileges to `USER mcp` after installing dependencies (`Dockerfile:24`).
- Container test ensures non-root operation (`tests/test_container.py:4`).
- Ready-file lifecycle supports health checks across transports (`mcp/__main__.py:156`, `tests/test_tcp.py:252`).

## Schema discovery & validation
- Discovery prefers env overrides, then falls back to the updated submodule data, with deterministic ordering (`mcp/core.py:41`, `mcp/core.py:53`).
- Example inference now prefers `$schema` markers and retains filename fallback for legacy files (`mcp/core.py:126`).
- Example and schema fixtures embed `$schema`, ensuring discovery matches the enforced contract (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `tests/fixtures/examples/AssetExample.json:2`).

## Test coverage
- Test suite spans transports, validation, backend, diff, golden replay, and lifecycle behavior (`tests/test_tcp.py:63`, `tests/test_backend.py:21`, `tests/test_diff.py:11`).
- New tests assert rejection of missing `$schema` and legacy keys, ensuring regression coverage (`tests/test_validate.py:185`, `tests/test_validate.py:193`).

## Dependencies & runtime
- Runtime dependencies remain `jsonschema` and `httpx`, with optional `referencing` for local registries (`requirements.txt:1-3`, `mcp/validate.py:67`).
- No new packages were added during the contract update.

## Environment variables
- Implementation still honours documented env vars for transports, resources, backend, and batching (`mcp/__main__.py:103`, `mcp/backend.py:18`, `mcp/validate.py:92`).
- README and `.env.example` reflect these defaults (`README.md:93`, `.env.example:2`).

## Documentation accuracy
- README features and schema alias sections now call out the strict `$schema` requirement (`README.md:38`, `README.md:138`).
- Spec front matter reiterates the mandate and legacy key rejection (`docs/mcp_spec.md:20`).

## Detected divergences
- None.

## Recommendations
- Validate that asset `$schema` values resolve to known schema identifiers to catch mismatches early (`mcp/validate.py:146`).
- Consider tooling to rewrite legacy assets automatically when ingesting third-party data, backed by the new enforcement tests (`tests/test_validate.py:193`).
- Keep `$schema` compliance checks in CI to ensure new fixtures or docs do not regress (`tests/fixtures/golden.jsonl:3`, `libs/synesthetic-schemas/examples`).
