**Summary Of Repo State**
- Files: `README.md`, `docs/mcp_spec.md`, `requirements.txt`, `mcp/*.py`, `tests/*.py`, `meta/prompts/init_mcp_repo.json` present.
- CI: `.github/workflows/ci.yml` present and runs pytest on push/PR (`.github/workflows/ci.yml:3`).
- Submodule content present under `libs/synesthetic-schemas/`.
- Deps pinned: `jsonschema`, `httpx`, `pytest` (`requirements.txt:1`). Python >=3.11 documented (`README.md:60`).

**Top Gaps & Fixes**
- Add payload-limit tests for 1 MiB rejection in validate/backend.
- Add smoke tests for `mcp/stdio_main.py` and optional `mcp/http_main.py`.
- Document `SYN_BACKEND_ASSETS_PATH` in README to match spec/code.

**Alignment With Init Prompt**
- Language ≥3.11: Present (`README.md:60`).
- Deterministic KISS style: Present (sorted outputs in `mcp/core.py:50`, `mcp/validate.py:126`, `mcp/diff.py:50`).
- Env-overridable discovery, submodule fallback only: Present (`mcp/core.py:12`, `mcp/core.py:25`).
- JSON Schema Draft 2020-12 + base-URI: Present (`mcp/validate.py:8`, `mcp/validate.py:106`).
- Diff RFC6902 add/remove/replace; list replace: Present (`mcp/diff.py:25`, `mcp/diff.py:33-39`).
- Backend gated by env; 5s timeout; no retries: Present (`mcp/backend.py:14-21`, `mcp/backend.py:51`).
- Tests via pytest; `__version__` exposed: Present (`mcp/__init__.py:5`).
- 1 MiB limit: Present in code (`mcp/validate.py:23`, `mcp/backend.py:34`); tests Missing.

**Alignment With Spec**
| Spec Item | Status | Evidence |
| - | - | - |
| Env discovery: env → submodule; no fixtures | Present | `docs/mcp_spec.md:18`, `mcp/core.py:12`, `tests/test_submodule_integration.py:7`
| list_schemas contract + sorted | Present | `docs/mcp_spec.md:30`, `mcp/core.py:38`, `mcp/core.py:50`
| get_schema contract | Present | `docs/mcp_spec.md:33`, `mcp/core.py:54`, `tests/test_validate.py:11`
| list_examples + sorted | Present | `docs/mcp_spec.md:36`, `mcp/core.py:63`, `mcp/core.py:74`
| get_example infers schema + validated | Present | `docs/mcp_spec.md:39`, `mcp/core.py:99`, `mcp/core.py:106`
| Validation: Draft 2020-12 + base-URI | Present | `docs/mcp_spec.md:42`, `mcp/validate.py:8`, `mcp/validate.py:106`
| Errors RFC6901, sorted | Present | `docs/mcp_spec.md:55`, `mcp/validate.py:26`, `mcp/validate.py:126`
| Alias nested→canonical; ignore $schemaRef | Present | `docs/mcp_spec.md:116`, `mcp/validate.py:18-20`, `mcp/validate.py:89-95`
| 1 MiB payload limit | Present | `docs/mcp_spec.md:115`, `mcp/validate.py:23`, `mcp/backend.py:34`
| Diff ops add/remove/replace; lists replace; sorted | Present | `docs/mcp_spec.md:59-60`, `mcp/diff.py:21-39`, `mcp/diff.py:49-51`
| Backend gating, timeout; error model | Present | `docs/mcp_spec.md:23`, `mcp/backend.py:30-33`, `mcp/backend.py:69-86`
| Unsupported tool/resource error | Present | `docs/mcp_spec.md:79-83`, `mcp/stdio_main.py:30`
| Exit: `import mcp` exposes __version__ | Present | `docs/mcp_spec.md:133`, `mcp/__init__.py:5`

**Test Coverage And CI**
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for dirs | Yes | `tests/test_env_discovery.py:6`
| Submodule use; sorted listings | Yes | `tests/test_submodule_integration.py:1`
| Validate canonical example via alias | Yes | `tests/test_validate.py:14`
| Validation errors sorted | Yes | `tests/test_validate.py:20`
| Diff idempotence; list replace | Yes | `tests/test_diff.py:1`
| Backend disabled without env | Yes | `tests/test_backend.py:20`
| Backend success/error handling | Yes | `tests/test_backend.py:27`, `tests/test_backend.py:35`
| Payload size limits | Missing | No tests for `payload_too_large`
| Stdio loop behavior | Missing | No tests for `mcp/stdio_main.py`
| HTTP app behavior | Missing | No tests for `mcp/http_main.py`
| CI workflow present | Yes | `.github/workflows/ci.yml:3`

**Dependencies And Runtime**
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | `mcp/validate.py:8` | Required |
| httpx | `mcp/backend.py:7` | Required |
| pytest | `tests/*` | Required (tests) |
| referencing | `mcp/validate.py:10` | Optional (guarded import) |
| fastapi | `mcp/http_main.py:7-12` | Optional (HTTP adapter) |
| uvicorn | `README.md:69` | Optional (dev/server)

**Environment Variables**
- SYN_SCHEMAS_DIR: unset by default; overrides schemas dir; else submodule if present; no fixtures (`mcp/core.py:12-22`).
- SYN_EXAMPLES_DIR: unset by default; overrides examples dir; else submodule if present (`mcp/core.py:25-35`).
- SYN_BACKEND_URL: enables backend; otherwise returns `unsupported` (`mcp/backend.py:14-33`).
- SYN_BACKEND_ASSETS_PATH: POST path override; default `/synesthetic-assets/`; adds leading slash if missing (`mcp/backend.py:17-21`).

**Documentation Accuracy**
- README matches features and discovery order (`README.md:78-91`).
- README omits `SYN_BACKEND_ASSETS_PATH` which exists in code/spec (Add doc).
- Version import guidance correct; `__version__` exported (`README.md:65`, `mcp/__init__.py:5`).

**Detected Divergences**
- None functional. Minor doc gap: `SYN_BACKEND_ASSETS_PATH` not in README while present in code/spec.

**Recommendations**
- Add tests for >1 MiB assets to assert `payload_too_large` in validate/backend paths.
- Add one `stdio_main` round-trip test and optional FastAPI route smoke tests guarded by `importorskip`.
- Update README to document `SYN_BACKEND_ASSETS_PATH` and CI link.
