## Summary of repo state
- Runtime/test deps pinned in `requirements.txt` (requirements.txt:1).
- Source modules implement discovery, validation, diff, backend, stdio, HTTP entrypoints (mcp/core.py:12; mcp/validate.py:81; mcp/diff.py:42; mcp/backend.py:24; mcp/stdio_main.py:13; mcp/http_main.py:6).
- Tests cover validation, diff, backend, env discovery, stdio, HTTP (tests/test_validate.py:14; tests/test_diff.py:4; tests/test_backend.py:20; tests/test_env_discovery.py:7; tests/test_stdio.py:6; tests/test_http.py:4).
- Submodule assets expected under `libs/synesthetic-schemas` and used in tests (mcp/core.py:8; tests/test_validate.py:21; tests/test_submodule_integration.py:19).
- CI workflow runs pytest on Python 3.11–3.13 with submodules checked out ( .github/workflows/ci.yml:15; .github/workflows/ci.yml:21).

## Top gaps & fixes (3-5 bullets up front)
- Update README environment section to document `SYN_BACKEND_ASSETS_PATH` per spec and backend implementation (docs/mcp_spec.md:24; mcp/backend.py:17; README.md:78).
- Change CI to install the package (`pip install -e .`) instead of exporting `PYTHONPATH=.` contrary to the init prompt (meta/prompts/init_mcp_repo.json:66; .github/workflows/ci.yml:34).
- Extend backend tests to cover custom `SYN_BACKEND_ASSETS_PATH` behavior for the POST path override (docs/mcp_spec.md:24; mcp/backend.py:17; tests/test_backend.py:27).

## Alignment with init prompt (bullet list, file:line evidence)
- Present – Python ≥3.11 declared (pyproject.toml:8; README.md:60).
- Present – Runtime deps limited to jsonschema/httpx and pytest for tests (requirements.txt:1; meta/prompts/init_mcp_repo.json:48).
- Present – Env override → submodule discovery with no fixture fallback (mcp/core.py:12; mcp/core.py:25; tests/test_submodule_integration.py:19).
- Present – JSON Schema Draft 2020-12 validation with base URI injection and sorted errors (mcp/validate.py:8; mcp/validate.py:106; mcp/validate.py:122).
- Present – RFC6902 diff limited to add/remove/replace with deterministic ordering (mcp/diff.py:21; mcp/diff.py:49).
- Present – Backend tool gated on `SYN_BACKEND_URL`, 5s timeout, mockable client (mcp/backend.py:14; mcp/backend.py:51; tests/test_backend.py:27).
- Present – 1 MiB payload guard shared across validation/backend (mcp/validate.py:23; mcp/backend.py:34; tests/test_validate.py:37; tests/test_backend.py:43).
- Present – Stdio loop and optional FastAPI app available (mcp/stdio_main.py:13; mcp/http_main.py:6; tests/test_stdio.py:6; tests/test_http.py:4).
- Divergent – CI relies on `PYTHONPATH=.` rather than editable install as required (“no sys.path hacks”) (meta/prompts/init_mcp_repo.json:66; .github/workflows/ci.yml:34).

## Alignment with spec (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Env discovery order env → submodule; no fixtures | Present | docs/mcp_spec.md:18; mcp/core.py:12; tests/test_submodule_integration.py:19 |
| list_schemas contract and sorted output | Present | docs/mcp_spec.md:30; mcp/core.py:38; mcp/core.py:50 |
| get_schema returns schema/version | Present | docs/mcp_spec.md:33; mcp/core.py:54; tests/test_validate.py:14 |
| list_examples sorted by component/path | Present | docs/mcp_spec.md:36; mcp/core.py:63; tests/test_submodule_integration.py:35 |
| get_example infers schema & validated flag | Present | docs/mcp_spec.md:39; mcp/core.py:78; mcp/core.py:106 |
| Validation Draft 2020-12 with base URI & sorted RFC6901 errors | Present | docs/mcp_spec.md:42; mcp/validate.py:8; mcp/validate.py:122 |
| Nested alias + ignore `$schemaRef` | Present | docs/mcp_spec.md:116; mcp/validate.py:18; mcp/validate.py:89 |
| 1 MiB payload limit enforced | Present | docs/mcp_spec.md:115; mcp/validate.py:23; mcp/backend.py:34 |
| Diff only add/remove/replace sorted by path/op | Present | docs/mcp_spec.md:59; mcp/diff.py:16; mcp/diff.py:49 |
| Backend gating, timeout, error model | Present | docs/mcp_spec.md:23; mcp/backend.py:24; mcp/backend.py:69 |
| Unsupported tool/resource error response | Present | docs/mcp_spec.md:79; mcp/stdio_main.py:30 |
| Optional backend assets path override env | Present | docs/mcp_spec.md:24; mcp/backend.py:17 |

## Test coverage and CI (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for schema/example dirs | Yes | tests/test_env_discovery.py:7 |
| Submodule discovery & deterministic ordering | Yes | tests/test_submodule_integration.py:19 |
| Validate canonical example via alias | Yes | tests/test_validate.py:14 |
| Validation error sorting | Yes | tests/test_validate.py:27 |
| 1 MiB payload guard (validate/backend) | Yes | tests/test_validate.py:37; tests/test_backend.py:43 |
| Diff idempotence and list replace | Yes | tests/test_diff.py:4 |
| Backend success/error handling | Yes | tests/test_backend.py:27 |
| HTTP adapter smoke (importorskip) | Yes | tests/test_http.py:4 |
| Stdio loop round-trip | Yes | tests/test_stdio.py:6 |
| Backend assets path override | Missing | tests/test_backend.py:27 (default only) |
| CI workflow executes pytest matrix | Yes | .github/workflows/ci.yml:15 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | mcp/validate.py:8 | Required |
| httpx | mcp/backend.py:7 | Required |
| pytest | tests/test_validate.py:4 | Required (tests) |
| referencing | mcp/validate.py:10 | Optional |
| fastapi | mcp/http_main.py:7 | Optional |
| uvicorn | README.md:68 | Optional (runtime tooling) |

## Environment variables (bullets: name, default, fallback behavior)
- SYN_SCHEMAS_DIR – overrides schema directory when set; otherwise use submodule path (mcp/core.py:12).
- SYN_EXAMPLES_DIR – overrides examples directory when set; otherwise use submodule path (mcp/core.py:25).
- SYN_BACKEND_URL – enables backend tool; when unset populate_backend returns unsupported (mcp/backend.py:14; mcp/backend.py:31).
- SYN_BACKEND_ASSETS_PATH – overrides backend POST path, defaults to `/synesthetic-assets/` and prepends `/` if missing (mcp/backend.py:17).

## Documentation accuracy (bullets: README vs. code)
- README feature list matches implemented tools (README.md:26; mcp/stdio_main.py:13; mcp/http_main.py:6).
- Environment discovery section aligns with env→submodule behavior (README.md:80; mcp/core.py:12).
- README omits `SYN_BACKEND_ASSETS_PATH` despite spec/code support (README.md:78; docs/mcp_spec.md:24; mcp/backend.py:17).
- README structure diagram is missing newer tests such as `test_http.py`, `test_stdio.py`, `test_submodule_integration.py` (README.md:36; tests/test_http.py:4; tests/test_stdio.py:6; tests/test_submodule_integration.py:19).

## Detected divergences (prompt vs. spec vs. code)
- Divergent – CI sets `PYTHONPATH=.` instead of relying on editable install as mandated by the prompt (meta/prompts/init_mcp_repo.json:66; .github/workflows/ci.yml:34).

## Recommendations (concrete next steps)
- Update README to document `SYN_BACKEND_ASSETS_PATH` and refresh the test list to reflect current files (mcp/backend.py:17; README.md:36).
- Modify CI to run `pip install -e .` and drop the `PYTHONPATH` override to satisfy the init prompt requirement (meta/prompts/init_mcp_repo.json:66; .github/workflows/ci.yml:34).
- Add a backend test that sets `SYN_BACKEND_ASSETS_PATH` to confirm the request path handling logic (mcp/backend.py:17; tests/test_backend.py:27).
