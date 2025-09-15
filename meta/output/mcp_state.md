## Summary of repo state
- Pinned runtime/test deps limited to jsonschema, httpx, pytest (requirements.txt:1).
- Core modules cover discovery, validation, diff, backend, and stdio/HTTP entrypoints (mcp/core.py:38; mcp/validate.py:81; mcp/diff.py:42; mcp/backend.py:24; mcp/stdio_main.py:13; mcp/http_main.py:6).
- Tests exercise env overrides, validation paths, diff logic, backend flows, and wiring adapters (tests/test_env_discovery.py:7; tests/test_validate.py:14; tests/test_diff.py:4; tests/test_backend.py:20; tests/test_stdio.py:6; tests/test_http.py:4).
- Synesthetic schemas submodule is present and used for fixtures (mcp/core.py:8; tests/test_submodule_integration.py:19).
- CI runs pytest across Python 3.11–3.13 with submodules checked out (.github/workflows/ci.yml:15; .github/workflows/ci.yml:21).

## Top gaps & fixes (3-5 bullets up front)
- Document `SYN_BACKEND_ASSETS_PATH` in README’s environment section to match spec/backend behavior (docs/mcp_spec.md:24; mcp/backend.py:17; README.md:80).
- Refresh README structure/tests list so listed files match the actual suite (README.md:36; tests/test_http.py:4; tests/test_stdio.py:6; tests/test_submodule_integration.py:19).
- Replace the CI `PYTHONPATH=.` override with an editable install per the “no sys.path hacks; require editable install” constraint (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).
- Remove or explicitly justify `pyproject.toml` to align with the “pin requirements only” phase directive (meta/prompts/init_mcp_repo.json:69; pyproject.toml:1).

## Alignment with init prompt (bullet list, file:line evidence)
- Present – Python ≥3.11 requirement declared (pyproject.toml:8).
- Present – Requirements limited to jsonschema/httpx/pytest as specified (requirements.txt:1; meta/prompts/init_mcp_repo.json:49).
- Present – Env overrides precede submodule discovery with no fixture fallback (mcp/core.py:12; mcp/core.py:25; tests/test_submodule_integration.py:19).
- Present – Draft 2020-12 validation with base URI injection and sorted RFC6901 errors (mcp/validate.py:8; mcp/validate.py:106; mcp/validate.py:122).
- Present – RFC6902 diff restricted to add/remove/replace with deterministic ordering (mcp/diff.py:16; mcp/diff.py:49).
- Present – Backend gated on `SYN_BACKEND_URL`, 5s timeout, and mockable client (mcp/backend.py:24; mcp/backend.py:51; tests/test_backend.py:27).
- Present – 1 MiB payload guards enforced in validation and backend (mcp/validate.py:23; mcp/backend.py:34; tests/test_validate.py:37; tests/test_backend.py:54).
- Present – Stdio loop and optional FastAPI app exposed with smoke tests (mcp/stdio_main.py:13; mcp/http_main.py:6; tests/test_stdio.py:6; tests/test_http.py:4).
- Divergent – CI relies on `PYTHONPATH=.` despite the “no sys.path hacks; require editable install” constraint (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).
- Divergent – `pyproject.toml` adds packaging metadata contrary to the “no other packaging metadata” phase directive (meta/prompts/init_mcp_repo.json:69; pyproject.toml:1).

## Alignment with spec (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Env discovery order env → submodule → empty | Present | docs/mcp_spec.md:18; mcp/core.py:12; tests/test_submodule_integration.py:19 |
| `list_schemas` contract and sorted output | Present | docs/mcp_spec.md:30; mcp/core.py:38; mcp/core.py:50 |
| `get_schema` returns schema/version | Present | docs/mcp_spec.md:33; mcp/core.py:54; tests/test_validate.py:14 |
| `list_examples` sorted by component/path | Present | docs/mcp_spec.md:36; mcp/core.py:63; tests/test_env_discovery.py:35 |
| `get_example` infers schema and validated flag | Present | docs/mcp_spec.md:39; mcp/core.py:78; mcp/core.py:106 |
| Validation Draft 2020-12 with sorted RFC6901 errors | Present | docs/mcp_spec.md:42; mcp/validate.py:8; mcp/validate.py:122 |
| Nested alias ignoring `$schemaRef` | Present | docs/mcp_spec.md:116; mcp/validate.py:18; mcp/validate.py:89 |
| 1 MiB payload limit enforced | Present | docs/mcp_spec.md:115; mcp/validate.py:23; mcp/backend.py:34 |
| Diff limited to add/remove/replace with deterministic order | Present | docs/mcp_spec.md:59; mcp/diff.py:16; mcp/diff.py:49 |
| Backend gating, timeout, error handling, assets path override | Present | docs/mcp_spec.md:23; mcp/backend.py:24; mcp/backend.py:55 |
| Unsupported tool/resource error response | Present | docs/mcp_spec.md:79; mcp/stdio_main.py:30 |

## Test coverage and CI (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for schema/example dirs | Yes | tests/test_env_discovery.py:7 |
| Submodule discovery and deterministic ordering | Yes | tests/test_submodule_integration.py:19 |
| Canonical example validation via alias | Yes | tests/test_validate.py:14 |
| Validation error sorting | Yes | tests/test_validate.py:27 |
| 1 MiB payload guard (validate/backend) | Yes | tests/test_validate.py:37; tests/test_backend.py:54 |
| Diff idempotence and list replacement | Yes | tests/test_diff.py:4 |
| Backend success/error/path override | Yes | tests/test_backend.py:27; tests/test_backend.py:35; tests/test_backend.py:46 |
| HTTP adapter smoke | Yes | tests/test_http.py:4 |
| Stdio loop round-trip | Yes | tests/test_stdio.py:6 |
| Editable install enforced in CI | No | .github/workflows/ci.yml:34 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | mcp/validate.py:8 | Required |
| httpx | mcp/backend.py:7 | Required |
| pytest | tests/test_validate.py:4 | Required (tests) |
| referencing | mcp/validate.py:10 | Optional |
| fastapi | mcp/http_main.py:8 | Optional |
| uvicorn | README.md:68 | Optional |

## Environment variables (bullets: name, default, fallback behavior)
- SYN_SCHEMAS_DIR – overrides schema directory; otherwise use submodule path (mcp/core.py:12).
- SYN_EXAMPLES_DIR – overrides example directory; otherwise use submodule path (mcp/core.py:25).
- SYN_BACKEND_URL – enables backend populate; missing env yields unsupported response (mcp/backend.py:14; mcp/backend.py:31).
- SYN_BACKEND_ASSETS_PATH – overrides backend POST path, default `/synesthetic-assets/`, auto-prefixes slash (mcp/backend.py:17).

## Documentation accuracy (bullets: README vs. code)
- README correctly lists core tools exposed by the adapter (README.md:26; mcp/stdio_main.py:13).
- README env discovery text matches env→submodule ordering (README.md:80; mcp/core.py:12).
- README omits `SYN_BACKEND_ASSETS_PATH` even though spec and backend support it (README.md:80; docs/mcp_spec.md:24; mcp/backend.py:17).
- README structure section lacks newer tests such as HTTP, stdio, and submodule integration (README.md:36; tests/test_http.py:4; tests/test_stdio.py:6; tests/test_submodule_integration.py:19).

## Detected divergences (prompt vs. spec vs. code)
- CI job uses `PYTHONPATH=.` instead of an editable install despite the “no sys.path hacks” constraint (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).
- `pyproject.toml` retains packaging metadata contrary to the “no other packaging metadata” phase directive (meta/prompts/init_mcp_repo.json:69; pyproject.toml:1).

## Recommendations (concrete next steps)
- Update README to document `SYN_BACKEND_ASSETS_PATH` alongside other env knobs (README.md:80; mcp/backend.py:17).
- Extend README structure/tests listing to include `test_http.py`, `test_stdio.py`, and `test_submodule_integration.py` (README.md:36; tests/test_http.py:4).
- Revise CI to install the project (e.g., `pip install -e .`) and drop the `PYTHONPATH` override (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).
- Remove `pyproject.toml` (or relocate metadata outside the repo) to satisfy the “no other packaging metadata” directive if strict adherence is required (meta/prompts/init_mcp_repo.json:69; pyproject.toml:1).
