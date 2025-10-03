# AGENTS.md — Repo Snapshot (v0.2.8 Audit)

## Repo Summary
- Transports share a single dispatcher with 1 MiB guards and deterministic request handling across STDIO, socket, and TCP (`mcp/stdio_main.py:14`, `mcp/socket_main.py:53`, `mcp/transport.py:26`).
- Validation mandates top-level `$schema`, rejects legacy markers, and sorts errors for deterministic output (`mcp/validate.py:171`, `mcp/validate.py:181`, `tests/test_validate.py:65`).
- Lifecycle logging, ready files, and signal exits obey the v0.2.8 spec with integration coverage across transports (`mcp/__main__.py:185`, `mcp/__main__.py:303`, `tests/test_tcp.py:420`).
- Version strings still report v0.2.7 even though the implementation meets v0.2.8 requirements (`mcp/__init__.py:6`, `README.md:2`).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | `requirements.txt:1`; `mcp/validate.py:9` |
| httpx | Backend populate client | Required (backend path) | `requirements.txt:2`; `mcp/backend.py:22` |
| pytest | Test runner | Required (tests) | `requirements.txt:3`; `.github/workflows/ci.yml:34` |
| referencing | Local schema registry support | Optional | `mcp/validate.py:10`; `mcp/validate.py:106` |

## Environment Variables
- Transport selection: `MCP_ENDPOINT`, `MCP_HOST`, `MCP_PORT`, `MCP_SOCKET_PATH`, `MCP_SOCKET_MODE` (`mcp/__main__.py:102`).
- Lifecycle: `MCP_READY_FILE` (`mcp/__main__.py:155`, `.env.example:3`).
- Resources: `SYN_SCHEMAS_DIR`, `SYN_EXAMPLES_DIR` (`mcp/core.py:27`, `.env.example:6`).
- Backend: `SYN_BACKEND_URL`, `SYN_BACKEND_ASSETS_PATH` (`mcp/backend.py:12`, `.env.example:8`).
- Batching: `MCP_MAX_BATCH` (`mcp/validate.py:28`).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO transport & lifecycle | ✅ | `tests/test_stdio.py:70`; `tests/test_entrypoint.py:66` |
| Socket transport & concurrency | ✅ | `tests/test_socket.py:146`; `tests/test_socket.py:346` |
| TCP transport & signals | ✅ | `tests/test_tcp.py:167`; `tests/test_tcp.py:321` |
| Validation & batching | ✅ | `tests/test_validate.py:68`; `tests/test_validate.py:123` |
| Backend populate | ✅ | `tests/test_backend.py:31`; `tests/test_backend.py:116` |
| Golden replay | ✅ | `tests/test_golden.py:45`; `tests/fixtures/golden.jsonl:1` |
| Container security | ✅ | `tests/test_container.py:4`; `Dockerfile:24` |

## Spec Alignment (v0.2.8)
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO/socket/TCP enforce 1 MiB | Present | `mcp/transport.py:28`; `tests/test_socket.py:179`; `tests/test_tcp.py:167` |
| Ready/shutdown logs mirror metadata | Present | `mcp/__main__.py:185`; `mcp/__main__.py:303`; `tests/test_entrypoint.py:85` |
| Signal exits surface `-SIGINT`/`-SIGTERM` | Present | `mcp/__main__.py:294`; `tests/test_socket.py:211`; `tests/test_tcp.py:273` |
| Ready file `<pid> <ISO8601>` | Present | `mcp/__main__.py:155`; `tests/test_stdio.py:214` |
| `validate` alias warns + delegates | Present | `mcp/stdio_main.py:23`; `tests/test_tcp.py:539` |
| `$schema` required, legacy keys rejected | Present | `mcp/validate.py:171`; `mcp/validate.py:181`; `tests/test_validate.py:187` |

## Recommendations
- Update version metadata to v0.2.8 in code and docs to prevent consumer confusion (`mcp/__init__.py:6`, `README.md:2`).
- Publish a canonical `$schema` URI table in README so clients know which marker to send (`docs/mcp_spec.md:21`, `README.md:28`).
- Add an automated check that every example fixture retains its `$schema` marker, guarding against regressions (`libs/synesthetic-schemas/examples/SynestheticAsset_Example1.json:2`, `tests/test_golden.py:45`).
