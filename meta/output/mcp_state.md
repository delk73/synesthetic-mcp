## Summary of repo state
- Present — Shared dispatcher covers STDIO, socket, and TCP with 1 MiB guards before decode (`mcp/transport.py:26`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:113`; `tests/test_tcp.py:161`)
- Present — Validation enforces top-level `$schema`, rejects legacy keys, and sorts errors deterministically (`mcp/validate.py:171`; `mcp/validate.py:181`; `mcp/validate.py:224`; `tests/test_validate.py:54`)
- Present — Lifecycle logs include mode, address, schema/example roots, and ISO timestamps with ready/shutdown parity plus signal-tested exits (`mcp/__main__.py:185`; `mcp/__main__.py:303`; `tests/test_entrypoint.py:66`; `tests/test_socket.py:196`)
- Divergent — Version metadata and README front matter still report v0.2.7 (`mcp/__init__.py:6`; `README.md:2`)
- Missing — No automated regression guard ensures every shipped example retains its `$schema` marker despite spec requirement (`docs/mcp_spec.md:36`; `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`; `tests/test_validate.py:26`)

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
