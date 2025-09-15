# AGENTS.md — Repo Baseline

## Repo Summary
- Minimal MCP adapter exposing discovery, validation, diff, backend populate, and stdio/HTTP entrypoints (mcp/core.py:38; mcp/validate.py:81; mcp/diff.py:42; mcp/backend.py:24; mcp/stdio_main.py:13; mcp/http_main.py:6).
- Runtime/test deps pinned to jsonschema, httpx, pytest with optional extras noted in docs (requirements.txt:1; README.md:65; docs/mcp_spec.md:109).
- Synesthetic schemas checked in via git submodule and consumed through env/submodule discovery order (.gitmodules:1; mcp/core.py:12; tests/test_submodule_integration.py:19).
- CI runs pytest on Python 3.11–3.13 with submodules enabled (.github/workflows/ci.yml:15; .github/workflows/ci.yml:21).

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_backend.py:1 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:10 |
| fastapi | HTTP adapter | Optional | README.md:66; mcp/http_main.py:8 |
| uvicorn | HTTP runtime | Optional | README.md:71 |

## Environment Variables
- SYN_SCHEMAS_DIR — overrides schema directory before submodule fallback (mcp/core.py:12).
- SYN_EXAMPLES_DIR — overrides examples directory before submodule fallback (mcp/core.py:25).
- SYN_BACKEND_URL — enables backend POSTs; missing returns unsupported (mcp/backend.py:14; mcp/backend.py:32).
- SYN_BACKEND_ASSETS_PATH — customizes POST path, default `/synesthetic-assets/` (mcp/backend.py:17).

## Tests Overview
| Focus | Test(s) | Evidence |
| - | - | - |
| Env overrides | tests/test_env_discovery.py | tests/test_env_discovery.py:7 |
| Submodule integration | tests/test_submodule_integration.py | tests/test_submodule_integration.py:19 |
| Validation success/error/payload limit | tests/test_validate.py | tests/test_validate.py:14 |
| Diff determinism | tests/test_diff.py | tests/test_diff.py:4 |
| Backend success/error/path/validation guard | tests/test_backend.py | tests/test_backend.py:27; tests/test_backend.py:95 |
| HTTP adapter smoke | tests/test_http.py | tests/test_http.py:4 |
| Stdio loop round-trip | tests/test_stdio.py | tests/test_stdio.py:6 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| Env → submodule discovery order | Present | docs/mcp_spec.md:18; mcp/core.py:12 |
| Sorted schema/example listings | Present | docs/mcp_spec.md:57; mcp/core.py:50 |
| Validation alias + RFC6901 errors | Present | docs/mcp_spec.md:42; mcp/validate.py:18 |
| 1 MiB payload cap | Present | docs/mcp_spec.md:115; mcp/backend.py:34 |
| Diff limited to add/remove/replace | Present | docs/mcp_spec.md:59; mcp/diff.py:16 |
| Backend error model | Present | docs/mcp_spec.md:79; mcp/backend.py:60 |

## Divergences
- CI relies on `PYTHONPATH=.` instead of an editable install despite init prompt guidance (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).

## Recommendations
- Update CI to install the project (e.g., `pip install -e .`) and drop the `PYTHONPATH` override (.github/workflows/ci.yml:34).

## Baseline Commit
- b4df97aac523c741d1e9d2d442dba43e58369ead
