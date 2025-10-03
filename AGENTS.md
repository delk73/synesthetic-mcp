# AGENTS.md — Repo Snapshot (v0.2.8 Audit)

## Repo Summary
- Shared dispatcher serves STDIO/socket/TCP with deterministic 1 MiB guards (`mcp/transport.py:26`; `mcp/socket_main.py:110`; `mcp/tcp_main.py:113`)
- Validation enforces `$schema`, blocks legacy keys, and sorts errors deterministically (`mcp/validate.py:171`; `mcp/validate.py:181`; `mcp/validate.py:224`)
- Lifecycle logs, ready files, and signal shutdowns follow spec across transports (`mcp/__main__.py:185`; `mcp/__main__.py:303`; `tests/test_tcp.py:177`)
- Regression guard for example `$schema` markers is absent despite spec requirement (`docs/mcp_spec.md:36`; `tests/test_submodule_integration.py:37`)
- Version banner still reads v0.2.7, creating divergence with the implemented v0.2.8 behaviors (`mcp/__init__.py:6`; `README.md:2`)

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

## Spec Alignment (v0.2.8)
| Spec Item | Status | Evidence |
| - | - | - |
| 1 MiB guard across STDIO/socket/TCP | Present | `mcp/transport.py:26`; `tests/test_tcp.py:161` |
| Ready/shutdown logs mirror metadata | Present | `mcp/__main__.py:232`; `tests/test_entrypoint.py:85` |
| Signal exits emit `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:424`; `tests/test_socket.py:211` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:155`; `tests/test_stdio.py:214` |
| `validate` alias warns + delegates | Present | `mcp/stdio_main.py:23`; `tests/test_tcp.py:247` |
| `$schema` required, legacy keys rejected | Present | `mcp/validate.py:171`; `mcp/validate.py:181`; `tests/test_validate.py:195` |
| Examples `$schema` regression guard | Missing | `docs/mcp_spec.md:36`; _no automated check_ |
| Docs show TCP `nc 127.0.0.1 8765` example | Divergent | `docs/mcp_spec.md:46`; `README.md:195` |
| Version metadata updated to v0.2.8 | Divergent | `mcp/__init__.py:6`; `README.md:2` |

## Recommendations
- Add a guard (test or lint) that walks `libs/synesthetic-schemas/examples` and fails when `$schema` is missing (`docs/mcp_spec.md:36`; `libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`)
- Update `__version__` and README front matter to v0.2.8 for alignment with spec (`mcp/__init__.py:6`; `README.md:2`)
- Adjust README TCP quickstart to use the mandated `nc 127.0.0.1 8765` snippet (`docs/mcp_spec.md:46`; `README.md:195`)
