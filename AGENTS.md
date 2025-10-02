# AGENTS.md — Repo Snapshot (v0.2.8 Audit)

## Repo Summary
- Transports, lifecycle management, and logging remain compliant with v0.2.8 transport expectations (`mcp/__main__.py:185`, `tests/test_tcp.py:178`).
- Validation flow still depends on external `schema` params and tolerates `$schemaRef`, diverging from the `$schema`-only contract (`mcp/validate.py:120`, `mcp/validate.py:135`, `docs/mcp_spec.md:12`).
- Docs and fixtures continue to demonstrate legacy `schema` usage, so guidance no longer matches the spec (`README.md:153`, `tests/fixtures/golden.jsonl:3`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:8` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:30` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `tests/test_tcp.py:63` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:67`; `mcp/validate.py:109` |

## Environment Variables
- Transport selection and endpoints: `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (`mcp/__main__.py:103`).
- Lifecycle readiness: `MCP_READY_FILE` (`mcp/__main__.py:156`, `.env.example:3`).
- Resources: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` (`mcp/core.py:41`, `.env.example:6`).
- Backend: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH` (`mcp/backend.py:18`, `.env.example:8`).
- Limits: `MCP_MAX_BATCH` (`mcp/validate.py:92`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | `tests/test_stdio.py:173` |
| Socket transport & concurrency | ✅ | `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP transport & signals | ✅ | `tests/test_tcp.py:117`; `tests/test_tcp.py:411` |
| Validation & batching | ✅ (legacy schema key) | `tests/test_validate.py:46`; `tests/test_validate.py:103` |
| Backend populate | ✅ | `tests/test_backend.py:21`; `tests/test_backend.py:96` |
| Golden replay | ✅ (legacy schema key) | `tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:3` |
| Container security | ✅ | `tests/test_container.py:4`; `Dockerfile:27` |

## Spec Alignment (v0.2.8)
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP 1 MiB guard | Present | `mcp/transport.py:28`; `tests/test_socket.py:185`; `tests/test_tcp.py:167` |
| Ready/shutdown logs include mode/path + dirs + ISO timestamp | Present | `mcp/__main__.py:185`; `mcp/__main__.py:304`; `tests/test_entrypoint.py:85` |
| Signal exits return `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:295`; `tests/test_tcp.py:194` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `mcp/__main__.py:156`; `tests/test_stdio.py:210` |
| `validate` alias warns; schema param required | Present | `mcp/stdio_main.py:23`; `tests/test_stdio.py:68` |
| Assets require top-level `$schema`, reject `schema/$schemaRef` | Divergent | `docs/mcp_spec.md:12`; `mcp/validate.py:135`; `tests/test_backend.py:31`; `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2` |

## Recommendations
- Require `$schema` within `validate_asset`/`validate_many`, rejecting legacy keys with `validation_failed` at `/$schema` (`mcp/validate.py:120`, `docs/mcp_spec.md:12`).
- Migrate fixtures, golden records, and README examples to `$schema`, adding tests that fail on legacy inputs (`tests/fixtures/golden.jsonl:3`, `README.md:153`, `tests/test_validate.py:19`).
- Audit the schema submodule for `$schemaRef` usage and update inference logic/tests accordingly (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `mcp/core.py:126`).
