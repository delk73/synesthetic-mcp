# AGENTS.md — Repo Snapshot

## Repo Summary
- STDIO entrypoint defaults to newline-delimited JSON-RPC and emits `mcp:ready`/`mcp:shutdown`, while HTTP health serving is gated by `MCP_ENDPOINT` (mcp/__main__.py:55; mcp/__main__.py:205; README.md:80).
- Tool router exposes discovery, validation, diff, and backend populate over STDIO (mcp/stdio_main.py:13; mcp/backend.py:24).
- Schema/example discovery prioritises env overrides before submodule fallbacks with deterministic sorting (mcp/core.py:12; mcp/core.py:38; tests/test_env_discovery.py:7).
- Validation enforces alias resolution, RFC6901 errors, and a shared 1 MiB payload cap reused by backend populate (mcp/validate.py:17; mcp/validate.py:106; mcp/backend.py:34).
- CI checks out submodules, installs the project editable, and runs pytest on Python 3.11–3.13 (.github/workflows/ci.yml:21; .github/workflows/ci.yml:34).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_backend.py:1 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:10 |
| fastapi | HTTP adapter | Optional | mcp/http_main.py:6 |
| uvicorn | HTTP runtime | Optional | README.md:83 |

## Environment Variables
- `MCP_ENDPOINT` (`stdio` default) selects STDIO vs. optional HTTP/TCP (mcp/__main__.py:55; README.md:96).
- `MCP_READY_FILE` (`/tmp/mcp.ready`) signals readiness for compose health checks (mcp/__main__.py:77; docker-compose.yml:29).
- `MCP_HOST` / `MCP_PORT` applied only when HTTP is requested; invalid ports fail startup (mcp/__main__.py:43; tests/test_entrypoint.py:92).
- `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR` override discovery roots (mcp/core.py:12; tests/test_env_discovery.py:29).
- `SYN_BACKEND_URL` unlocks populate; unset returns `unsupported` (mcp/backend.py:30; tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH` customises backend POST path with leading slash guard (mcp/backend.py:17; tests/test_backend.py:36).

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO ready/shutdown handling | ✅ | tests/test_entrypoint.py:31 |
| Env overrides & submodule fallback | ✅ | tests/test_env_discovery.py:7; tests/test_submodule_integration.py:23 |
| STDIO JSON-RPC validation loop | ✅ | tests/test_stdio.py:40 |
| Backend success/error/size/validation guards | ✅ | tests/test_backend.py:28 |
| Diff determinism | ✅ | tests/test_diff.py:11 |
| HTTP endpoint happy path | ❌ | tests/test_entrypoint.py:100 |
| FastAPI adapter smoke (optional) | ⚠️ skipped if FastAPI missing | tests/test_http.py:4 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO default with MCP_ENDPOINT override | Present | docs/mcp_spec.md:25; mcp/__main__.py:55 |
| Env→submodule discovery order | Present | docs/mcp_spec.md:105; mcp/core.py:38 |
| Validation alias & 1 MiB cap | Present | docs/mcp_spec.md:117; mcp/validate.py:17 |
| RFC6902 diff add/remove/replace | Present | docs/mcp_spec.md:61; mcp/diff.py:16 |
| Backend env gating & error model | Present | docs/mcp_spec.md:116; mcp/backend.py:30 |
| CI via editable install | Present | meta/prompts/init_mcp_repo.json:18; .github/workflows/ci.yml:34 |

## Divergences
- Compose always publishes `${MCP_PORT}` even when running in STDIO mode, leaving an unused port exposed (docker-compose.yml:18; mcp/__main__.py:307).
- Optional HTTP/TCP path lacks a passing integration test, so `mode=http` readiness is unverified (mcp/__main__.py:168; tests/test_entrypoint.py:100).

## Recommendations
- Add an HTTP-mode smoke test that runs `python -m mcp` with `MCP_ENDPOINT=http://127.0.0.1:0` and asserts readiness plus `/healthz` response (mcp/__main__.py:140).
- Condition the Compose port mapping on HTTP enablement or document the unused port when STDIO is active (docker-compose.yml:26; README.md:40).
- Reuse the submodule skip guard in `tests/test_stdio.py` to avoid failures when schemas are absent (tests/test_stdio.py:75; tests/test_submodule_integration.py:19).

## Baseline Commit
- 95863497ed75482c9c967f105ea2bfb11c8ac024
