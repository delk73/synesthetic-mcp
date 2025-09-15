**Summary Of Repo State**
- Files: `README.md`, `docs/mcp_spec.md`, `requirements.txt`, `mcp/*.py`, `tests/*.py`, `meta/prompts/init_mcp_repo.json` present. No `.github/workflows/` found.
- Submodule: `libs/synesthetic-schemas` present; declared in `.gitmodules`.
- Deps: `jsonschema`, `httpx`, `pytest` pinned. Optional extras documented in README/spec; not required at runtime.
- Python: README and spec state >=3.11.

**Top Gaps & Fixes**
- Missing CI: add GitHub Actions to run `pytest -q` on push/PR.
- Missing payload-limit tests: assert 1 MiB rejection in `validate_asset` and `populate_backend`.
- Missing adapter tests: smoke tests for `stdio_main` loop and optional `http_main` routes.

**Alignment With Init Prompt**
- Language: Python >=3.11 — Present.
- Deterministic KISS style — Present (sorting and minimal surface in `mcp/*`).
- Schemas/examples from disk; env overrides — Present (`mcp/core.py`; `tests/test_env_discovery.py`).
- Runtime environment-agnostic — Present (no sys.path hacks; stdio/http optional).
- JSON Schema Draft 2020-12 w/ base-URI — Present (`mcp/validate.py`).
- Diff RFC6902 add/remove/replace; deterministic lists — Present (`mcp/diff.py`).
- Backend disabled unless `SYN_BACKEND_URL`; timeout 5s; no retries — Present (`mcp/backend.py`; `tests/test_backend.py`).
- Tests via pytest; editable import works (`__version__`) — Present (`mcp/__init__.py`; README).
- 1 MiB payload limit — Present in code, tests Missing.
- Files scaffolded — Present without local fixtures; prompt updated to match.

**Alignment With Spec**
| Spec Item | Status | Evidence |
| - | - | - |
| Env discovery order (env → submodule; no local fixture fallback) | Present | docs/mcp_spec.md; mcp/core.py; tests/test_submodule_integration.py |
| list_schemas contract + sorted by name/version/path | Present | docs/mcp_spec.md; mcp/core.py |
| get_schema contract | Present | docs/mcp_spec.md; mcp/core.py; tests/test_validate.py |
| list_examples contract + sorted by component/path | Present | docs/mcp_spec.md; mcp/core.py; tests/test_submodule_integration.py |
| get_example infers schema; returns validated flag | Present | docs/mcp_spec.md; mcp/core.py; tests/test_submodule_integration.py |
| Validation: Draft 2020-12, base-URI if $id missing | Present | docs/mcp_spec.md; mcp/validate.py |
| Validation errors: RFC6901 paths, sorted | Present | docs/mcp_spec.md; mcp/validate.py; tests/test_validate.py |
| Alias: nested-synesthetic-asset → synesthetic-asset | Present | docs/mcp_spec.md; mcp/validate.py; tests/test_validate.py |
| Ignore top-level $schemaRef in examples | Present | docs/mcp_spec.md; mcp/validate.py |
| 1 MiB max payload | Present | docs/mcp_spec.md; mcp/validate.py; mcp/backend.py |
| Diff: only add/remove/replace; lists replace; sorted output | Present | docs/mcp_spec.md; mcp/diff.py; tests/test_diff.py |
| Backend: disabled without URL; timeout 5s; no retries | Present | docs/mcp_spec.md; mcp/backend.py; tests/test_backend.py |
| Backend errors map to reason backend_error | Present | docs/mcp_spec.md; mcp/backend.py |
| Unsupported tool/resource error | Present | docs/mcp_spec.md; mcp/stdio_main.py |
| Deterministic ordering guarantees | Present | docs/mcp_spec.md; mcp/core.py; mcp/validate.py; mcp/diff.py |
| Exit: `import mcp` exposes __version__ | Present | docs/mcp_spec.md; mcp/__init__.py |

**Test Coverage And CI**
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for schema/example dirs | Yes | tests/test_env_discovery.py |
| Use submodule when present; sorted listings | Yes | tests/test_submodule_integration.py |
| Validate valid canonical example via alias | Yes | tests/test_validate.py |
| Validation errors sorted deterministically | Yes | tests/test_validate.py |
| Diff idempotence and list replacement | Yes | tests/test_diff.py |
| Backend disabled without env | Yes | tests/test_backend.py |
| Backend success and error handling | Yes | tests/test_backend.py |
| Payload size limits (validate/backend) | Missing | No tests asserting `payload_too_large` |
| Stdio loop behavior | Missing | No tests for `mcp/stdio_main.py` |
| HTTP app behavior | Missing | No tests for `mcp/http_main.py` |
| CI workflow | Missing | No `.github/workflows` directory |

**Dependencies And Runtime**
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | mcp/validate.py | Required |
| httpx | mcp/backend.py | Required |
| pytest | tests/* | Required (tests) |
| referencing | mcp/validate.py | Optional (guarded import) |
| fastapi | mcp/http_main.py | Optional (HTTP adapter) |
| uvicorn | README only | Optional (dev/runtime) |

**Environment Variables**
- SYN_SCHEMAS_DIR: default unset; if set, used as schemas dir. Fallback to submodule if present; no fixture fallback (`mcp/core.py`).
- SYN_EXAMPLES_DIR: default unset; if set, used as examples dir. Fallback to submodule if present (`mcp/core.py`).
- SYN_BACKEND_URL: enables backend when set; otherwise returns `unsupported` (`mcp/backend.py`; tests cover both states).
- SYN_BACKEND_ASSETS_PATH: POST path override; default `/synesthetic-assets/` with leading slash normalization (`mcp/backend.py`).

**Documentation Accuracy**
- README features match code: validation, diff, backend populate, stdio loop, optional HTTP app (README; `mcp/*`).
- README and spec discovery notes match code: env → submodule; no fixture fallback; behavior when missing paths clarified (README; docs/mcp_spec.md; `mcp/core.py`).
- Optional extras documented; not required in `requirements.txt`.
- Version import instruction valid; `__version__` defined.

**Detected Divergences**
- None material. Prior prompt-vs-code differences (fixtures, pydantic, env defaults) were resolved by updating `meta/prompts/init_mcp_repo.json` and docs.

**Recommendations**
- Add CI: create `.github/workflows/ci.yml` to run `pip install -r requirements.txt` and `pytest -q` on `push`/`pull_request`.
- Add size-limit tests: generate >1 MiB asset to assert `payload_too_large` in `validate_asset` and via `populate_backend`.
- Add adapter tests: one `stdio_main` request/response JSON-RPC smoke test; optional FastAPI route test guarded by `pytest.importorskip("fastapi")`.
