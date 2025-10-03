## Summary of repo state
- STDIO, socket, and TCP share the same JSON-RPC dispatcher with 1 MiB guards and deterministic request handling across transports (`mcp/stdio_main.py:14`, `mcp/socket_main.py:53`, `mcp/tcp_main.py:56`, `mcp/transport.py:26`).
- Validation now enforces the v0.2.8 `$schema` contract and rejects legacy markers before Draft 2020-12 evaluation (`mcp/validate.py:171`, `mcp/validate.py:181`, `tests/test_validate.py:187`, `tests/test_validate.py:202`).
- Lifecycle logging, ready-file management, and signal exits satisfy the spec invariants with coverage in process, socket, and TCP tests (`mcp/__main__.py:185`, `mcp/__main__.py:304`, `tests/test_entrypoint.py:66`, `tests/test_socket.py:196`, `tests/test_tcp.py:420`).

## Top gaps & fixes (3-5 bullets)
- Bump published version strings to v0.2.8 so tooling and docs match the implemented contract (`mcp/__init__.py:6`, `README.md:2`).
- Document canonical `$schema` URIs (or a mapping table) for client authors; spec calls the requirement out but README stops at a high-level feature list (`docs/mcp_spec.md:21`, `README.md:28`).
- Add a CI hook that scans `libs/synesthetic-schemas/examples` to ensure each example retains a top-level `$schema` marker to prevent silent fixture regressions (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `tests/test_golden.py:45`).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| 1 MiB guard enforced on STDIO/socket/TCP | Present | `mcp/transport.py:28`; `tests/test_stdio.py:358`; `tests/test_socket.py:179`; `tests/test_tcp.py:167` |
| Ready/shutdown logs mirror mode + location + dirs with ISO timestamps | Present | `mcp/__main__.py:185`; `mcp/__main__.py:303`; `tests/test_entrypoint.py:66`; `tests/test_socket.py:196` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:155`; `tests/test_stdio.py:214`; `tests/test_tcp.py:252` |
| Signal exits return `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:294`; `tests/test_socket.py:211`; `tests/test_tcp.py:273` |
| `validate` alias warns while delegating to `$schema` validation | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:108`; `tests/test_tcp.py:539` |
| `$schema` required; legacy `schema`/`$schemaRef` rejected | Present | `mcp/validate.py:171`; `mcp/validate.py:181`; `tests/test_validate.py:187`; `tests/test_validate.py:202` |
| Schema access confined to configured roots | Present | `mcp/core.py:16`; `tests/test_path_traversal.py:33`; `tests/test_path_traversal.py:76` |
| `validate_many` enforces `MCP_MAX_BATCH` and per-item guards | Present | `mcp/validate.py:230`; `mcp/validate.py:241`; `tests/test_validate.py:123`; `tests/test_validate.py:151` |
| Socket transport enforces 0600 perms and multi-client ordering | Present | `mcp/socket_main.py:27`; `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP transport handles concurrent clients and logs bound host/port | Present | `mcp/tcp_main.py:25`; `tests/test_tcp.py:331`; `tests/test_tcp.py:420` |
| Spec errors stay inside JSON-RPC `result`; malformed frames get JSON-RPC `error` | Present | `mcp/transport.py:92`; `tests/fixtures/golden.jsonl:10`; `tests/test_socket.py:162` |

## Transports
- Shared dispatcher keeps tool surface identical across transports, so validations, diff, and backend work in every mode (`mcp/stdio_main.py:14`, `mcp/socket_main.py:53`, `mcp/tcp_main.py:56`).
- Payload-size enforcement occurs before JSON decoding, producing deterministic `payload_too_large` responses (`mcp/transport.py:28`, `tests/test_stdio.py:358`).
- End-to-end suites cover malformed params, concurrency, and shutdown flows for each transport (`tests/test_socket.py:162`, `tests/test_socket.py:346`, `tests/test_tcp.py:321`).

## STDIO entrypoint & process model
- `_run_stdio` logs readiness, writes the ready file, drains stdin, and mirrors shutdown metadata before returning (`mcp/__main__.py:180`, `mcp/__main__.py:202`).
- Ready-file behaviour and exit codes are verified by integration tests that close stdin and watch the file vanish post-shutdown (`tests/test_stdio.py:207`, `tests/test_entrypoint.py:66`).
- The CLI `--validate` path emits the validation payload verbatim, matching spec expectations for tooling integration (`mcp/__main__.py:322`, `tests/test_entrypoint.py:240`).

## Socket server (multi-client handling, perms, unlink, logs)
- Startup unlinks stale sockets, binds, enforces `0600`, and tracks worker threads for cleanup (`mcp/socket_main.py:27`, `mcp/socket_main.py:49`).
- Tests assert permission bits, simultaneous client ordering, and unlink-on-shutdown semantics (`tests/test_socket.py:146`, `tests/test_socket.py:346`, `tests/test_socket.py:292`).

## TCP server (binding, perms, multi-client, shutdown logs)
- Server binds requested or ephemeral ports, advertises the actual address, and drains threads during close (`mcp/tcp_main.py:25`, `mcp/tcp_main.py:56`, `mcp/tcp_main.py:44`).
- End-to-end tests cover payload caps, multi-client interleaving, alias warnings, and shutdown logging (`tests/test_tcp.py:167`, `tests/test_tcp.py:321`, `tests/test_tcp.py:539`).

## Lifecycle signals
- Custom signal handler raises `_SignalShutdown` so transports can log shutdown before returning negative exit codes (`mcp/__main__.py:77`, `mcp/__main__.py:294`).
- Signal-driven exits propagate through the transports with assertions on return codes and ready-file cleanup (`tests/test_entrypoint.py:84`, `tests/test_socket.py:211`, `tests/test_tcp.py:273`).

## Shutdown logging invariant
- Ready/shutdown logs share the same field set for each transport, emitted before resources are torn down (`mcp/__main__.py:185`, `mcp/__main__.py:303`).
- Tests compare the field sets to guarantee parity and ordering under SIGINT/SIGTERM (`tests/test_entrypoint.py:66`, `tests/test_socket.py:280`, `tests/test_tcp.py:542`).

## Golden request/response examples
- Golden transcript exercises schema listing, get, validate + alias, batching, example validation (success + failure), diff, backend populate, and malformed frames (`tests/test_golden.py:45`, `tests/fixtures/golden.jsonl:1`).
- Stderr expectations in the golden file ensure deprecated alias warnings continue to fire (`tests/fixtures/golden.jsonl:4`).

## Payload size guard
- Transport parser rejects oversized frames pre-parse, mapping to `validation_failed` results (`mcp/transport.py:28`, `tests/test_stdio.py:358`).
- Asset validation and backend population use the same guard to prevent large payload infusion (`mcp/validate.py:161`, `mcp/backend.py:36`, `tests/test_backend.py:71`).

## Schema validation contract
- `$schema` strings must be non-empty, resolve within configured roots, and cannot coexist with legacy keys (`mcp/validate.py:171`, `mcp/validate.py:181`, `mcp/validate.py:175`).
- Tests cover missing `$schema`, empty markers, legacy keys, oversized payloads, and alias routing to canonical schemas (`tests/test_validate.py:81`, `tests/test_validate.py:187`, `tests/test_validate.py:202`).

## Batching
- `validate_many` enforces array input, batch size limits, and per-item validation using the same guardrail as single validation (`mcp/validate.py:230`, `mcp/validate.py:241`).
- Regression tests cover mixed success, batch limit errors, and oversized members returning `payload_too_large` errors (`tests/test_validate.py:95`, `tests/test_validate.py:123`, `tests/test_validate.py:151`).

## Logging hygiene
- `_log_event` centralises ISO-8601 stderr logging, while stdout remains reserved for JSON-RPC frames (`mcp/__main__.py:54`, `tests/test_stdio.py:299`).
- Deprecated alias warnings and ready/shutdown records are asserted in integration suites to prevent regressions (`tests/test_stdio.py:108`, `tests/test_tcp.py:539`).

## Container & health
- Docker image drops privileges to a dedicated `mcp` user after dependency installation (`Dockerfile:24`, `Dockerfile:27`).
- Tests ensure the Dockerfile continues to run as non-root and that ready-file semantics support external health checks (`tests/test_container.py:4`, `tests/test_entrypoint.py:66`).

## Schema discovery & validation
- Env overrides take precedence, with deterministic ordering for schema/example listings and `$schema`-aware example inference (`mcp/core.py:27`, `mcp/core.py:69`, `mcp/core.py:126`).
- Tests cover env override behaviour, submodule fallback ordering, traversal rejection, and example validation (`tests/test_env_discovery.py:7`, `tests/test_submodule_integration.py:28`, `tests/test_path_traversal.py:52`).

## Test coverage
- Suites span validation, transports, backend population, diff determinism, golden flows, and container hardening (`tests/test_validate.py:19`, `tests/test_stdio.py:43`, `tests/test_tcp.py:321`, `tests/test_backend.py:31`, `tests/test_diff.py:4`, `tests/test_golden.py:45`).
- CI runs the full pytest suite across Python 3.11–3.13 to keep behaviour portable (`.github/workflows/ci.yml:16`, `.github/workflows/ci.yml:34`).

## Dependencies & runtime
- Runtime stack is limited to `jsonschema` and `httpx`, with `pytest` for tests and optional `referencing` for local registries (`requirements.txt:1`, `requirements.txt:2`, `requirements.txt:3`, `mcp/validate.py:10`).
- Optional dependency handling degrades gracefully when `referencing` is unavailable (`mcp/validate.py:10`, `mcp/validate.py:106`).

## Environment variables
- Transport selection and TCP/socket configuration are wire up via `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (`mcp/__main__.py:102`, `mcp/__main__.py:116`).
- Resource and backend overrides flow through `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR`, `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH`, and batching limit via `MCP_MAX_BATCH` (`mcp/core.py:27`, `mcp/backend.py:12`, `mcp/backend.py:15`, `mcp/validate.py:28`, `.env.example:2`).

## Documentation accuracy
- Spec doc is updated to v0.2.8, listing the stricter `$schema` requirement and transport invariants (`docs/mcp_spec.md:2`, `docs/mcp_spec.md:35`).
- README front matter still reports v0.2.7 despite the implementation carrying v0.2.8 changes, creating a version mismatch for consumers (`README.md:2`).

## Detected divergences
- Version metadata lags behind the v0.2.8 implementation in both the package `__version__` and README front matter (`mcp/__init__.py:6`, `README.md:2`).

## Recommendations
- Update version strings and any release notes to advertise v0.2.8 so clients can detect the stricter `$schema` enforcement (`mcp/__init__.py:6`, `README.md:2`).
- Add a lightweight check (e.g., pytest or CI script) that asserts every shipped example retains `$schema` to guard against regressions in fixtures and docs (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `tests/test_validate.py:32`).
- Extend README with a canonical `$schema` reference table so integrators know which URI to send for each asset class (`docs/mcp_spec.md:21`, `README.md:28`).
