# AGENTS.md — Repo Snapshot (v0.2.9 Audit)

## Repo Summary
- Version banner still reads v0.2.7, diverging from v0.2.9 spec (`mcp/__init__.py:6`; `README.md:2`)
- Local schema loading persists; remote canonical resolution absent (`mcp/validate.py:50`; `mcp/validate.py:106`)
- Environment variables LABS_SCHEMA_BASE and LABS_SCHEMA_VERSION unread (`mcp/__main__.py:185`)
- Examples embed relative $schema, not canonical host (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`)
- Ready logs omit schemas_base and schema_version fields (`mcp/__main__.py:185`)
- TCP nc example absent from README (`README.md:195`)
- Governance audit endpoint missing (`docs/mcp_spec.md:101`)

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:9` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:23` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `.github/workflows/ci.yml:34` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:106` |

## Environment Variables
- Transport selection: `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (`mcp/__main__.py:102`)
- Lifecycle health: `MCP_READY_FILE` (`mcp/__main__.py:155`; `.env.example:3`)
- Resource roots: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` (`mcp/core.py:64`; `.env.example:6`)
- Backend options: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH` (`mcp/backend.py:12`; `.env.example:8`)
- Batching: `MCP_MAX_BATCH` (`mcp/validate.py:28`)
- Missing: `LABS_SCHEMA_BASE`, `LABS_SCHEMA_VERSION` (spec v0.2.9)

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | `tests/test_stdio.py:70`; `tests/test_entrypoint.py:66` |
| Socket transport & concurrency | ✅ | `tests/test_socket.py:145`; `tests/test_socket.py:274` |
| TCP transport, multi-client, signals | ✅ | `tests/test_tcp.py:117`; `tests/test_tcp.py:229`; `tests/test_tcp.py:194` |
| Validation & batching | ✅ | `tests/test_validate.py:54`; `tests/test_validate.py:123` |
| Backend populate | ✅ | `tests/test_backend.py:31`; `tests/test_backend.py:116` |
| Golden replay | ✅ | `tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1` |
| Container security | ✅ | `tests/test_container.py:4`; `Dockerfile:26` |

## Spec Alignment (v0.2.9)
| Spec Item | Status | Evidence |
| - | - | - |
| Schema host/version (v0.2.9) | Missing | No LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION |
| Schema resolution (v0.2.9) | Divergent | Local only; no remote/cache |
| No legacy schema keys | Present | `mcp/validate.py:171` |
| Env parity | Missing | LABS vars unread |
| Governance parity | Missing | No governance_audit |
| Transport compliance | Present | STDIO/Socket/TCP exist |
| Payload cap | Present | `mcp/transport.py:26`; `tests/test_tcp.py:161` |
| Alias | Present | `mcp/stdio_main.py:23` |
| Batching | Present | `mcp/validate.py:233` |
| get_example | Present | `mcp/core.py:155` |
| Determinism | Present | Sorting in code |
| Security | Present | Non-root container |
| Process model | Present | STDIO exits on close |
| Logging | Divergent | Missing fields |
| Signal handling | Present | `-SIGINT`/`-SIGTERM` |
| Shutdown logging | Divergent | Mirrors but incomplete |
| Ready file format | Present | `<pid> <ISO8601>` |
| Golden examples | Present | Covers required |
| Docs TCP nc example | Missing | No nc in README |
| Version metadata updated to v0.2.9 | Divergent | Still v0.2.7 |

## Recommendations
- Update `__version__` and README to v0.2.9 (`mcp/__init__.py:6`; `README.md:2`)
- Implement LABS_SCHEMA_BASE/LABS_SCHEMA_VERSION reading and remote resolution
- Update examples $schema to canonical URLs
- Add schemas_base/schema_version to logs
- Add TCP nc example to README
- Implement governance_audit endpoint
