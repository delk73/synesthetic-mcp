## Summary of repo state
- Transport loop, validation, and backend flows now satisfy the v0.2.5 spec, with alias handling and 1 MiB guards exercised end-to-end (`mcp/stdio_main.py:23-36`, `mcp/transport.py:13-50`, `tests/test_golden.py:45-97`).
- Readiness, shutdown, and ready-file lifecycle logging are consistent across stdio and socket modes (`mcp/__main__.py:115-188`, `tests/test_entrypoint.py:61-74`, `tests/test_socket.py:87-148`).
- Container image runs as non-root and compose health checks rely on the ready file as required (`Dockerfile:1-31`, `docker-compose.yml:12-33`).

## Top gaps & fixes (3-5 bullets)
- Update the published spec heading to v0.2.5 and fold the “Scope (v0.2.5 — Next)” block into the stable section so docs match implementation (`docs/mcp_spec.md:1-2`, `docs/mcp_spec.md:167-215`).
- Bump the README front matter version from 0.1.0 to v0.2.5 to reflect the current release and avoid mixed messaging (`README.md:1-4`).
- Deduplicate the double definition of `test_backend_assets_path_normalization` to keep the backend test suite clear and deterministic (`tests/test_backend.py:46-57`, `tests/test_backend.py:170-181`).

## Alignment with mcp_spec.md (v0.2.5)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing with 1 MiB guard | Present | `mcp/transport.py:13-50`; `tests/test_stdio.py:283-310` |
| Socket multi-client support, perms, unlink | Present | `mcp/socket_main.py:30-123`; `tests/test_socket.py:95-148`; `tests/test_socket.py:199-220` |
| Ready file `<pid> <ISO8601>` lifecycle & logs | Present | `mcp/__main__.py:115-188`; `tests/test_entrypoint.py:61-74` |
| `validate` alias accepted with warning | Present | `mcp/stdio_main.py:23-36`; `tests/test_stdio.py:56-147`; `tests/test_golden.py:66-80` |
| `validate_many` batching & payload guard | Present | `mcp/validate.py:199-218`; `tests/test_validate.py:103-156` |
| Path traversal rejection & schema safety | Present | `mcp/core.py:45-102`; `tests/test_path_traversal.py:25-74` |
| Deterministic listings, errors, diff | Present | `mcp/core.py:88-118`; `tests/test_submodule_integration.py:28-53`; `tests/test_diff.py:1-21` |
| Golden request/response coverage | Present | `tests/fixtures/golden.jsonl:1-10`; `tests/test_golden.py:18-105` |
| Documentation version alignment | Divergent | `docs/mcp_spec.md:1-2`; `README.md:1-4` |

## Transports
- STDIO loop enforces NDJSON framing and payload caps before dispatch (`mcp/stdio_main.py:52-59`, `mcp/transport.py:13-50`).
- Socket server spawns per-connection threads, sets 0600 perms, and unlinks the socket on close (`mcp/socket_main.py:30-123`); tests exercise readiness, payload guard, and concurrent clients (`tests/test_socket.py:87-220`).

## STDIO entrypoint & process model
- Entry point logs readiness with schemas/examples, writes the ready file, and clears it on shutdown (`mcp/__main__.py:115-138`).
- Tests confirm signal handling, ready file lifecycle, and CLI validation exit codes (`tests/test_entrypoint.py:61-159`).

## Socket server (multi-client handling, perms, unlink, logs)
- Accept loop tracks client threads and joins them during close, ensuring graceful shutdown and unlink (`mcp/socket_main.py:59-123`).
- Multi-client test verifies per-connection ordering and continued service for existing clients (`tests/test_socket.py:199-220`).

## Golden request/response examples
- Canonical NDJSON frames for every MCP method plus malformed input live in `tests/fixtures/golden.jsonl` (`tests/fixtures/golden.jsonl:1-10`).
- Slow test replays the fixture, asserts responses, and checks for the alias deprecation warning on stderr (`tests/test_golden.py:18-105`).

## Payload size guard
- Transport rejects oversize frames before parsing and responds with `payload_too_large` (`mcp/transport.py:13-50`, `tests/test_stdio.py:283-310`).
- Validator and backend paths enforce the same 1 MiB limit on assets and payloads (`mcp/validate.py:120-133`, `mcp/backend.py:33-53`; `tests/test_validate.py:56-63`, `tests/test_backend.py:63-77`).

## Schema validation contract
- Schema parameter is mandatory and checked before validation (`mcp/stdio_main.py:27-35`, `tests/test_stdio.py:17-27`).
- Path traversal is rejected for schemas/examples (`mcp/core.py:45-86`, `tests/test_path_traversal.py:25-74`).
- Alias mapping validates nested assets against the canonical schema with deterministic error ordering (`mcp/validate.py:17-178`, `tests/test_validate.py:46-64`).

## Batching
- `MCP_MAX_BATCH` defaults to 100, rejects non-positive values, and returns `unsupported` when exceeded (`mcp/validate.py:27-205`).
- Tests cover mixed results, batch limit enforcement, and oversize asset rejection inside `validate_many` (`tests/test_validate.py:78-157`).

## Logging hygiene
- STDIO loop writes JSON frames to stdout only; logs (ready, warning, shutdown) land on stderr (`mcp/stdio_main.py:52-59`, `mcp/__main__.py:115-182`).
- Tests assert the alias warning and shutdown logs appear on stderr without contaminating stdout (`tests/test_stdio.py:117-147`, `tests/test_golden.py:66-97`).

## Container & health
- Dockerfile installs dependencies, drops to user `mcp`, and sets default CMD to the blocking server (`Dockerfile:1-31`).
- Compose service uses the ready file for a healthcheck and exposes transport configuration via environment variables (`docker-compose.yml:17-33`).

## Schema discovery & validation
- Discovery prioritizes env overrides, then the submodule, with deterministic sorting for listings (`mcp/core.py:60-118`).
- Tests cover env override behavior and submodule fallbacks (`tests/test_env_discovery.py:6-26`, `tests/test_submodule_integration.py:16-53`).

## Test coverage
- Transport, validation, backend, and process-model paths are exercised via targeted unit/integration tests and the golden replay (`tests/test_stdio.py:56-310`, `tests/test_socket.py:87-220`, `tests/test_backend.py:1-181`, `tests/test_golden.py:18-105`).

## Dependencies & runtime
- Runtime deps remain `jsonschema`, `httpx`, plus optional `referencing`; pytest is the test runner (`requirements.txt:1-4`, `mcp/validate.py:8-114`).
- Docker image pins Python 3.11 slim and installs the project in editable mode (`Dockerfile:1-24`).

## Environment variables
- Spec and README document all transport, discovery, batching, and backend env vars (`docs/mcp_spec.md:160-177`, `README.md:86-105`).
- Entry point validates transport selection and socket mode at startup (`mcp/__main__.py:47-138`).

## Documentation accuracy
- Docs describe the correct behavior but still label v0.2.5 features as “next”; header remains v0.2.4 (`docs/mcp_spec.md:1-2`, `docs/mcp_spec.md:167-215`).
- README front matter also references version 0.1.0 despite the implementation meeting v0.2.5 criteria (`README.md:1-4`).

## Detected divergences
- Documentation versioning lags the implementation: spec header still reads v0.2.4 and README front matter reports 0.1.0 (`docs/mcp_spec.md:1-2`, `README.md:1-4`).
- Test suite includes a duplicate backend normalization test definition that should be consolidated (`tests/test_backend.py:46-57`, `tests/test_backend.py:170-181`).

## Recommendations
- Promote the v0.2.5 requirements from the “Scope” block into the main spec and update the heading/version metadata (`docs/mcp_spec.md:1-2`, `docs/mcp_spec.md:167-215`).
- Refresh README metadata to match the current version so contributors see the correct release number (`README.md:1-4`).
- Remove the duplicate `test_backend_assets_path_normalization` definition to keep the test suite tidy and future-proof (`tests/test_backend.py:46-57`, `tests/test_backend.py:170-181`).
