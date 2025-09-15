**Summary Of Repo State**
- Files: `README.md`, `docs/mcp_spec.md`, `requirements.txt`, `mcp/*.py`, `tests/*.py`, `meta/prompts/init_mcp_repo.json` present. No `.github/workflows/` found.
- Submodule: `libs/synesthetic-schemas` present; declared in `.gitmodules` (.gitmodules:1).
- Deps: `jsonschema`, `httpx`, `pytest` pinned (requirements.txt:1). No `fastapi` (HTTP app optional). No `referencing` (optional import guarded).
- Python: README and spec state >=3.11 (docs/mcp_spec.md:94; README.md:60).

**Top Gaps & Fixes**
- Missing CI: Add GitHub Actions workflow to run `pytest -q` on pushes/PRs.
- Missing payload-limit tests: Add tests for 1 MiB rejection in `validate_asset` and `populate_backend`.
- Missing adapter tests: Add smoke tests for `stdio_main` JSON-RPC loop and optional `http_main` routes.
- Divergent env defaults vs init prompt: Code prefers submodule over fixture defaults; update prompt/docs or add fixtures/examples + env defaults.
- Prompt vs deps: Prompt listed pydantic/ruff/mypy; code intentionally minimal. Align prompt or add tooling.

**Alignment With Init Prompt**
- Language: Python >=3.11 — Present (docs/mcp_spec.md:94; README.md:60).
- Deterministic KISS style — Present (mcp/diff.py:42; mcp/validate.py:126; mcp/core.py:40,71).
- Schemas/examples from disk; env overrides — Present (mcp/core.py:14,18,27,31; tests/test_env_discovery.py:29,32,35).
- Runtime environment-agnostic — Present (no sys.path hacks; stdio/http optional: mcp/stdio_main.py:15-31; mcp/http_main.py:8-13).
- JSON Schema Draft 2020-12 w/ base-URI — Present (mcp/validate.py:8,106-114).
- Diff RFC6902 add/remove/replace; deterministic lists — Present (mcp/diff.py:26,28,35,49).
- Backend disabled unless `SYN_BACKEND_URL`; timeout 5s; no retries — Present (mcp/backend.py:15,32,51; tests/test_backend.py:21-25,28-41).
- Tests via pytest; editable import works (`__version__`) — Present (mcp/__init__.py:6; README.md:65; tests/* present).
- 1 MiB payload limit — Present (mcp/validate.py:23,42,86; mcp/backend.py:34-38) but tests Missing.
- Files scaffolded — Partially Divergent: fixtures/examples requested in prompt are missing; submodule used instead (tests/fixtures/examples missing; tests/test_submodule_integration.py:7-17; .gitmodules:1).
- Env defaults — Divergent: prompt suggested defaults to fixtures; code uses submodule if present, no fixture fallback (mcp/core.py:14-25,31-40).
- Requirements content — Divergent: prompt listed pydantic/ruff/mypy; current `requirements.txt` is minimal (requirements.txt:1).

**Alignment With Spec**
| Spec Item | Status | Evidence |
| - | - | - |
| Env discovery order (env → submodule; no local fixture fallback) | Present | docs/mcp_spec.md:18; mcp/core.py:14-25,31-40; tests/test_submodule_integration.py:25-33 |
| list_schemas contract + sorted by name/version/path | Present | docs/mcp_spec.md:29; mcp/core.py:38-41; tests/test_submodule_integration.py:28-33 |
| get_schema contract | Present | docs/mcp_spec.md:32; mcp/core.py:54-61; tests/test_validate.py:12-17 |
| list_examples contract + sorted by component/path | Present | docs/mcp_spec.md:35; mcp/core.py:63-71; tests/test_submodule_integration.py:35-41 |
| get_example infers schema; returns validated flag | Present | docs/mcp_spec.md:38; mcp/core.py:99-119,106; tests/test_submodule_integration.py:42-48 |
| Validation: Draft 2020-12, base-URI if $id missing | Present | docs/mcp_spec.md:96; mcp/validate.py:8,106-114 |
| Validation errors: RFC6901 paths, sorted | Present | docs/mcp_spec.md:63,118; mcp/validate.py:118-126; tests/test_validate.py:26-34 |
| Alias: nested-synesthetic-asset → synesthetic-asset | Present | docs/mcp_spec.md:101-104; mcp/validate.py:18-23; tests/test_validate.py:20-24 |
| Ignore top-level $schemaRef in examples | Present | docs/mcp_spec.md:104; mcp/validate.py:53-61 |
| 1 MiB max payload | Present | docs/mcp_spec.md:98; mcp/validate.py:23,42,86; mcp/backend.py:34-38 |
| Diff: only add/remove/replace; lists replace; sorted output | Present | docs/mcp_spec.md:44,90; mcp/diff.py:26,28,35,49; tests/test_diff.py:12-19 |
| Backend: disabled without URL; timeout 5s; no retries | Present | docs/mcp_spec.md:97; mcp/backend.py:15,32,51; tests/test_backend.py:21-41 |
| Backend errors map to reason backend_error | Present | docs/mcp_spec.md:72-88; mcp/backend.py:56-66,86-94 |
| Unsupported tool/resource error | Present | docs/mcp_spec.md:78-82; mcp/stdio_main.py:30 |
| Deterministic ordering guarantees | Present | docs/mcp_spec.md:60,118-119; mcp/core.py:40,71; mcp/validate.py:126; mcp/diff.py:49 |
| Exit: `import mcp` exposes __version__ | Present | docs/mcp_spec.md:116; mcp/__init__.py:6 |

**Test Coverage And CI**
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for schema/example dirs | Yes | tests/test_env_discovery.py:29-35 |
| Use submodule when present; sorted listings | Yes | tests/test_submodule_integration.py:25-41 |
| Validate valid canonical example via alias | Yes | tests/test_validate.py:18-24 |
| Validation errors sorted deterministically | Yes | tests/test_validate.py:26-34 |
| Diff idempotence and list replacement | Yes | tests/test_diff.py:4-19 |
| Backend disabled without env | Yes | tests/test_backend.py:21-25 |
| Backend success and error handling | Yes | tests/test_backend.py:28-41 |
| Payload size limits (validate/backend) | Missing | No tests asserting `payload_too_large` |
| Stdio loop behavior | Missing | No tests for `mcp/stdio_main.py` |
| HTTP app behavior | Missing | No tests for `mcp/http_main.py` |
| CI workflow | Missing | No `.github/workflows` directory |

**Dependencies And Runtime**
| Package | Used in | Required/Optional |
| - | - | - |
| `jsonschema` | mcp/validate.py:8,118-120 | Required |
| `httpx` | mcp/backend.py:5,51 | Required |
| `pytest` | tests/* | Required (tests) |
| `referencing` | mcp/validate.py:10-13,59,73,76 | Optional (guarded import) |
| `fastapi` | mcp/http_main.py:8-13 | Optional (HTTP adapter) |
| `uvicorn` | Mentioned in README only (README.md:69) | Optional (dev/runtime) |

**Environment Variables**
- SYN_SCHEMAS_DIR: default unset; if set, used as schemas dir (mcp/core.py:14-17). Fallback to submodule path if present; no fixture fallback (mcp/core.py:18-25).
- SYN_EXAMPLES_DIR: default unset; if set, used as examples dir (mcp/core.py:27-30). Fallback to submodule path if present (mcp/core.py:31-40).
- SYN_BACKEND_URL: enables backend when set; otherwise returns `unsupported` (mcp/backend.py:15,32; tests/test_backend.py:21-25).
- SYN_BACKEND_ASSETS_PATH: POST path override; default `/synesthetic-assets/` with leading slash normalization (mcp/backend.py:18-24).

**Documentation Accuracy**
- README features match code: validation, diff, backend populate, stdio loop, optional HTTP app (README.md:24-33,66-71; mcp/*).
- README submodule notes match discovery behavior (README.md:76-88; mcp/core.py:14-40).
- Version import instruction valid; `__version__` defined (README.md:65; mcp/__init__.py:6).
- README structure approximates repo; CI not documented and not present.
- Minimal deps in README/spec match requirements (docs/mcp_spec.md:95; requirements.txt:1).

**Detected Divergences**
- Env defaults vs init prompt: Prompt suggested defaulting to fixtures; code uses submodule and no fixture fallback — Divergent (meta/prompts/init_mcp_repo.json:38-45 vs mcp/core.py:14-25,31-40).
- Required packages in prompt vs repo: Prompt listed pydantic/ruff/mypy; repo uses minimal deps — Divergent (meta/prompts/init_mcp_repo.json:49-50 vs requirements.txt:1).
- Prompt-requested example fixtures missing: `tests/fixtures/examples/*.json` not present — Divergent (meta/prompts/init_mcp_repo.json:63-65; repo layout).

**Recommendations**
- Add CI: create `.github/workflows/ci.yml` to run `pip install -r requirements.txt` and `pytest -q` on `push`/`pull_request`.
- Add size-limit tests: craft >1 MiB payload to assert `payload_too_large` in `validate_asset` and `populate_backend`.
- Add adapter tests: simulate one `stdio_main` request/response and, optionally, FastAPI route smoke tests guarded by `pytest.importorskip("fastapi")`.
- Clarify env defaults: either update `meta/prompts/init_mcp_repo.json` to reflect submodule-first policy (no fixture defaults) or add example fixtures and set prompt/README accordingly.
- Align deps statement: update init prompt to “minimal deps: jsonschema, httpx, pytest; optional: fastapi, referencing” or add the extra dev deps if required.
