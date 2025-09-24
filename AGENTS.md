# AGENTS.md — Repo Snapshot

## Repo Summary
- **STDIO Transport:** NDJSON loop with 1 MiB guard, readiness file, and STDERR logging are implemented and covered by tests (mcp/stdio_main.py:45, mcp/stdio_main.py:53, mcp/__main__.py:88, tests/test_stdio.py:29).
- **Tools:** Validation, diff, and backend populate follow the spec with deterministic ordering and local-only schema resolution (mcp/validate.py:106, mcp/diff.py:43, mcp/backend.py:28, tests/test_validate.py:46).
- **Schema Discovery:** Environment overrides and submodule fallback are honored and verified (mcp/core.py:12, mcp/core.py:18, tests/test_env_discovery.py:29).
- **Gaps:** Socket transport is not implemented, and schema/example access lacks path-traversal guards (docs/mcp_spec.md:67, mcp/core.py:58, mcp/core.py:108).
- **Risk:** Docker image runs as root despite security guidance recommending non-root execution (Dockerfile:1, docs/mcp_spec.md:111).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:5 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry support | Optional | mcp/validate.py:9 |

## Environment Variables
- `MCP_ENDPOINT`: defaults to STDIO; any other value raises during startup (mcp/__main__.py:35).
- `MCP_READY_FILE`: `/tmp/mcp.ready` by default, populated with `<pid> <ISO8601>` and removed on shutdown (mcp/__main__.py:59, mcp/__main__.py:105).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR`: override discovery roots and must exist when set (mcp/core.py:12, mcp/__main__.py:22, tests/test_env_discovery.py:29).
- `SYN_BACKEND_URL`: gates backend POST; missing returns `unsupported` (mcp/backend.py:20, tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH`: normalized to a leading slash before POST (mcp/backend.py:24, tests/test_backend.py:46).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: unused because socket mode is absent (docs/mcp_spec.md:67, mcp/__main__.py:35).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing & payload guard | ✅ | tests/test_stdio.py:29; tests/test_stdio.py:184 |
| Ready file & shutdown | ✅ | tests/test_stdio.py:82; tests/test_entrypoint.py:55 |
| Validation contract & ordering | ✅ | tests/test_validate.py:46 |
| Backend populate flows & guard | ✅ | tests/test_backend.py:28; tests/test_backend.py:65 |
| Schema discovery (env + submodule) | ✅ | tests/test_env_discovery.py:29; tests/test_submodule_integration.py:23 |
| Diff determinism | ✅ | tests/test_diff.py:6 |
| Socket transport | ⚠️ Missing | mcp/__main__.py:35 |
| Path traversal rejection | ⚠️ Missing | mcp/core.py:58 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO NDJSON transport | Present | mcp/stdio_main.py:45; tests/test_stdio.py:29 |
| Ready file lifecycle | Present | mcp/__main__.py:88; tests/test_stdio.py:82 |
| 1 MiB guard | Present | mcp/stdio_main.py:53; tests/test_stdio.py:184 |
| `validate` alias | Present (needs test) | mcp/stdio_main.py:22 |
| Socket transport | Missing | docs/mcp_spec.md:67; mcp/__main__.py:35 |
| Path traversal rejection | Divergent | mcp/core.py:58; mcp/core.py:108; mcp/validate.py:47 |

## Recommendations
- Harden path handling by rejecting or resolving `..` before reading schemas/examples or loading schemas (mcp/core.py:58; mcp/core.py:108; mcp/validate.py:47).
- Add a regression test that exercises the `validate` alias over STDIO to lock in support (mcp/stdio_main.py:22; tests/test_stdio.py:29).
- Implement (or explicitly defer) the socket transport expected by the spec (docs/mcp_spec.md:67; mcp/__main__.py:35).
- Run the container as a non-root user to satisfy the security guidance (Dockerfile:1; docs/mcp_spec.md:111).
- Bring the README serve instructions in line with the checked-in tooling or supply the referenced helper (README.md:43; up.sh:1).
