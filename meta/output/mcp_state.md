## Summary of repo state
- Runtime/test deps pinned to jsonschema, httpx, pytest (requirements.txt:1).
- Core modules cover discovery, validation, diff, backend, and stdio/HTTP adapters (mcp/core.py:38; mcp/validate.py:81; mcp/diff.py:42; mcp/backend.py:24; mcp/stdio_main.py:13; mcp/http_main.py:6).
- Backend helper enforces env gating, alias-based validation, and payload limits (mcp/backend.py:30; mcp/backend.py:41; mcp/backend.py:34).
- Tests exercise env overrides, validation paths, diff logic, backend flows, adapters, submodule wiring, and the default backend validation path (tests/test_env_discovery.py:7; tests/test_validate.py:14; tests/test_diff.py:4; tests/test_backend.py:20; tests/test_backend.py:95; tests/test_backend.py:128; tests/test_http.py:4; tests/test_stdio.py:6; tests/test_submodule_integration.py:19).
- Synesthetic schemas submodule tracked and consumed via constants and git config (.gitmodules:1; mcp/core.py:8; tests/test_submodule_integration.py:30).
- CI runs pytest on Python 3.11–3.13 with submodules checked out (.github/workflows/ci.yml:15; .github/workflows/ci.yml:21).

## Top gaps & fixes (3-5 bullets up front)
- Divergent – CI sets `PYTHONPATH=.` instead of performing an editable install as required; switch to `pip install -e .` (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).


## Alignment with init prompt (bullet list, file:line evidence)
- Present – Minimal dependencies pinned to jsonschema/httpx/pytest as specified (requirements.txt:1; meta/prompts/init_mcp_repo.json:49).
- Present – Package exposes `__version__` per spec (mcp/__init__.py:1; meta/prompts/init_mcp_repo.json:50).
- Present – Env overrides precede submodule discovery with no fixture fallback (mcp/core.py:12; mcp/core.py:25; meta/prompts/init_mcp_repo.json:22).
- Present – Schema/example listings provide deterministic sorting (mcp/core.py:50; mcp/core.py:74; tests/test_submodule_integration.py:32).
- Present – Validation uses Draft 2020-12 with base-URI injection, alias mapping, and sorted RFC6901 errors (mcp/validate.py:8; mcp/validate.py:112; mcp/validate.py:126; meta/prompts/init_mcp_repo.json:16).
- Present – Diff restricts to add/remove/replace with deterministic ordering (mcp/diff.py:16; mcp/diff.py:50; meta/prompts/init_mcp_repo.json:17).
- Present – Backend gated on `SYN_BACKEND_URL`, enforces 5s timeout, and remains mockable (mcp/backend.py:24; mcp/backend.py:51; tests/test_backend.py:27; meta/prompts/init_mcp_repo.json:18).
- Present – 1 MiB payload guards enforced across validation and backend (mcp/validate.py:23; mcp/backend.py:34; tests/test_validate.py:37; meta/prompts/init_mcp_repo.json:20).
- Present – Stdio loop and optional FastAPI app expose all tools (mcp/stdio_main.py:13; mcp/http_main.py:6; tests/test_stdio.py:6; tests/test_http.py:4).
- Divergent – CI relies on `PYTHONPATH=.` rather than editable install (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).

## Alignment with spec (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Env discovery order env → submodule → empty | Present | docs/mcp_spec.md:18; mcp/core.py:12; tests/test_env_discovery.py:29 |
| Schema listing sorted deterministically | Present | docs/mcp_spec.md:57; mcp/core.py:50; tests/test_submodule_integration.py:32 |
| `get_example` returns schema + validated flag | Present | docs/mcp_spec.md:39; mcp/core.py:99; tests/test_submodule_integration.py:43 |
| Validation alias, Draft 2020-12, RFC6901 errors | Present | docs/mcp_spec.md:42; mcp/validate.py:18; mcp/validate.py:126 |
| 1 MiB payload limit shared by validation/backend | Present | docs/mcp_spec.md:115; mcp/validate.py:23; mcp/backend.py:34 |
| Diff limited to add/remove/replace, deterministic order | Present | docs/mcp_spec.md:59; mcp/diff.py:16; tests/test_diff.py:11 |
| Backend gating, timeout, assets path override | Present | docs/mcp_spec.md:23; mcp/backend.py:30; tests/test_backend.py:35 |
| Error model includes `unsupported` responses | Present | docs/mcp_spec.md:79; mcp/stdio_main.py:30 |

## Test coverage and CI (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides for schema/example dirs | Yes | tests/test_env_discovery.py:29 |
| Submodule discovery and ordering | Yes | tests/test_submodule_integration.py:32 |
| Canonical example validation via alias | Yes | tests/test_validate.py:20 |
| Validation error sorting | Yes | tests/test_validate.py:27 |
| 1 MiB payload guard (validate/backend) | Yes | tests/test_validate.py:37; tests/test_backend.py:54 |
| Diff idempotence and list replacement | Yes | tests/test_diff.py:4 |
| Backend success/error/path override handling | Yes | tests/test_backend.py:27; tests/test_backend.py:35; tests/test_backend.py:46 |
| Backend validation-first short-circuit | Yes | mcp/backend.py:41; tests/test_backend.py:95; tests/test_backend.py:128 |
| HTTP adapter smoke | Yes | tests/test_http.py:4 |
| Stdio loop round-trip | Yes | tests/test_stdio.py:6 |
| CI enforces editable install path | No | .github/workflows/ci.yml:34 |

## Dependencies and runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | mcp/validate.py:8 | Required |
| httpx | mcp/backend.py:7 | Required |
| pytest | tests/test_http.py:1 | Required (tests) |
| referencing | mcp/validate.py:10 | Optional |
| fastapi | mcp/http_main.py:8 | Optional |
| uvicorn | README.md:71 | Optional |

## Environment variables (bullets: name, default, fallback behavior)
- SYN_SCHEMAS_DIR – Overrides schema directory; else fall back to submodule path (mcp/core.py:12).
- SYN_EXAMPLES_DIR – Overrides example directory; else fall back to submodule path (mcp/core.py:25).
- SYN_BACKEND_URL – Enables backend population; absent returns `unsupported` (mcp/backend.py:14; mcp/backend.py:32).
- SYN_BACKEND_ASSETS_PATH – Overrides POST path, default `/synesthetic-assets/`, ensures leading slash (mcp/backend.py:17).

## Documentation accuracy (bullets: README vs. code)
- README feature list mirrors implemented tools (README.md:28; mcp/stdio_main.py:13).
- README environment discovery description matches env→submodule order (README.md:83; mcp/core.py:12).
- Divergent – README structure block nests `meta/` and `prompts/` under `tests/` despite those directories living at repo root (README.md:49; README.md:58; meta/prompts/audit_mcp_state.json:1).

## Detected divergences (prompt vs. spec vs. code)
- CI uses `PYTHONPATH=.` rather than an editable install despite the init constraint (meta/prompts/init_mcp_repo.json:19; .github/workflows/ci.yml:34).
- README structure misstates directory layout for `meta/` and `prompts/` (README.md:49; README.md:58; meta/prompts/audit_mcp_state.json:1).

## Recommendations (concrete next steps)
- Install the project (e.g., `pip install -e .`) in CI before running pytest and drop the `PYTHONPATH` override (.github/workflows/ci.yml:34).
- Fix the README structure block so `meta/` and `prompts/` sit at repo root (README.md:49; README.md:58).
- Extend README Development instructions to mention the required editable install (meta/prompts/init_mcp_repo.json:14; README.md:64).
