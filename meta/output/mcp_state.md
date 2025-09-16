## Summary of repo state (files, deps, schema discovery presence)
- Core modules implement discovery (`mcp/core.py:38`), validation (`mcp/validate.py:106`), diff (`mcp/diff.py:42`), backend proxy (`mcp/backend.py:24`), stdio loop (`mcp/stdio_main.py:13`), and optional HTTP app (`mcp/http_main.py:6`).
- Blocking server entrypoint resolves schema dirs, host/port, and runs an asyncio health server (`mcp/__main__.py:15`; `mcp/__main__.py:72`).
- Schema discovery honours env overrides before submodule fallbacks and keeps deterministic ordering (`mcp/core.py:12`; `mcp/core.py:18`; `tests/test_submodule_integration.py:28`).
- Requirements pin jsonschema/httpx/pytest with optional imports kept lazy (`requirements.txt:1`; `mcp/http_main.py:6`; `mcp/validate.py:10`).
- Tests span env overrides, validation, diff, backend flows, stdio, HTTP, and entrypoint readiness (`tests/test_env_discovery.py:29`; `tests/test_validate.py:14`; `tests/test_diff.py:4`; `tests/test_backend.py:21`; `tests/test_stdio.py:6`; `tests/test_http.py:4`; `tests/test_entrypoint.py:30`).

## Top gaps & fixes (3–5 bullets)
- Missing – No CLI/agent wiring turns validation failures into non-zero exits; `python -m mcp` only serves the health loop (mcp/__main__.py:119). Add a command (or flag) that invokes `validate_asset` and exits >0 on failure.
- Missing – Entrypoint failure paths (bad schema dir/port) lack automated coverage; only the happy SIGINT shutdown is tested (tests/test_entrypoint.py:30). Add tests that assert setup errors emit `mcp:error` and non-zero exit codes.
- Missing – Provide a checked-in env sample for documented knobs used by compose and server (`docker-compose.yml:7`; `README.md:83`). Add `.env.example` enumerating MCP_HOST/MCP_PORT/SYN_* defaults.

## Alignment with init prompt (bullets: Item → Status → Evidence)
- Minimal dependencies → Present → requirements.txt:1; meta/prompts/init_mcp_repo.json:49.
- Package version export → Present → mcp/__init__.py:5; meta/prompts/init_mcp_repo.json:50.
- Discovery order env→submodule→none → Present → mcp/core.py:12; mcp/core.py:18; meta/prompts/init_mcp_repo.json:22.
- Deterministic schema/example listings → Present → mcp/core.py:50; mcp/core.py:74; tests/test_submodule_integration.py:32.
- Validation alias & RFC6901 errors → Present → mcp/validate.py:18; mcp/validate.py:148; tests/test_validate.py:27; meta/prompts/init_mcp_repo.json:16.
- Diff limited to add/remove/replace → Present → mcp/diff.py:16; mcp/diff.py:45; tests/test_diff.py:11; meta/prompts/init_mcp_repo.json:17.
- Backend env gating with 5s timeout → Present → mcp/backend.py:30; mcp/backend.py:51; tests/test_backend.py:21; meta/prompts/init_mcp_repo.json:18.
- 1 MiB payload guard → Present → mcp/validate.py:23; mcp/backend.py:34; tests/test_validate.py:37; meta/prompts/init_mcp_repo.json:20.
- StdIO + HTTP adapters → Present → mcp/stdio_main.py:13; mcp/http_main.py:6; tests/test_stdio.py:6; tests/test_http.py:4.

## Alignment with spec (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| Env overrides precede submodule | Present | docs/mcp_spec.md:18; mcp/core.py:12; tests/test_env_discovery.py:29 |
| Listings sorted deterministically | Present | docs/mcp_spec.md:57; mcp/core.py:50; tests/test_submodule_integration.py:32 |
| `get_example` returns schema & validated flag | Present | docs/mcp_spec.md:39; mcp/core.py:99; tests/test_submodule_integration.py:43 |
| Validation alias + RFC6901 errors | Present | docs/mcp_spec.md:42; mcp/validate.py:18; mcp/validate.py:148 |
| 1 MiB payload cap enforced | Present | docs/mcp_spec.md:115; mcp/validate.py:106; mcp/backend.py:34 |
| Diff limited to add/remove/replace | Present | docs/mcp_spec.md:59; mcp/diff.py:16; tests/test_diff.py:11 |
| Backend error model & timeout | Present | docs/mcp_spec.md:23; mcp/backend.py:55; tests/test_backend.py:47 |
| Unsupported tool response | Present | docs/mcp_spec.md:79; mcp/stdio_main.py:30 |

## Server entrypoint & process model (bullets: blocking loop, signals, logging, exit codes)
- Blocking loop → Present → `_serve_forever` awaits a stop event until signalled (mcp/__main__.py:72; mcp/__main__.py:102).
- Signal handling → Present → installs SIGINT/SIGTERM handlers and restores previous ones on exit (mcp/__main__.py:81; mcp/__main__.py:107).
- Startup/shutdown logging → Present → logs `mcp:ready` with host/port/schemas_dir and `mcp:shutdown` on teardown (mcp/__main__.py:98; mcp/__main__.py:116).
- Fatal setup exit → Present → startup errors log `mcp:error reason=setup_failed` and exit with code 2 (mcp/__main__.py:119; mcp/__main__.py:125).
- Runtime error exit → Present → unexpected exceptions log `mcp:error reason=runtime_failure` and exit 1 (mcp/__main__.py:134).

## Container & health (table: Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Status | Evidence |
| - | - | - |
| Compose `serve` service | Present | docker-compose.yml:14 |
| Foreground server command | Present | docker-compose.yml:23 |
| Port exposure | Present | docker-compose.yml:24 |
| Healthcheck (`/healthz`) | Present | docker-compose.yml:26; mcp/__main__.py:40 |
| Serve script traps & tails logs | Present | serve.sh:16; serve.sh:45 |

## Schema discovery & validation (table: Source → Mechanism → Evidence)
| Source | Mechanism | Evidence |
| - | - | - |
| Env overrides | Present – `SYN_SCHEMAS_DIR`/`SYN_EXAMPLES_DIR` override before submodule usage | mcp/core.py:12; mcp/core.py:27 |
| Submodule fallback | Present – uses `libs/synesthetic-schemas` when dirs exist | mcp/core.py:18; tests/test_submodule_integration.py:28 |
| Missing directory handling | Present – startup raises when no schema directory available | mcp/__main__.py:21; mcp/__main__.py:25 |
| Validation aliasing | Present – nested assets map to canonical schema | mcp/validate.py:18; mcp/validate.py:123 |
| Validation wiring (CriticAgent-equivalent) | Missing – server only runs health loop; no CLI exits on validation failure | mcp/__main__.py:119 |

## Test coverage & CI (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| Env overrides | Present | tests/test_env_discovery.py:7 |
| Submodule integration | Present | tests/test_submodule_integration.py:23 |
| Validation success/error/payload | Present | tests/test_validate.py:14; tests/test_validate.py:27; tests/test_validate.py:37 |
| Diff determinism | Present | tests/test_diff.py:4 |
| Backend success/error/path/limits | Present | tests/test_backend.py:21; tests/test_backend.py:47; tests/test_backend.py:55 |
| Backend validation guard | Present | tests/test_backend.py:95 |
| HTTP adapter smoke | Present | tests/test_http.py:4 |
| Stdio loop round-trip | Present | tests/test_stdio.py:6 |
| Entrypoint ready/shutdown | Present | tests/test_entrypoint.py:30 |
| Entrypoint failure exits | Missing | tests/test_entrypoint.py:30 |
| CI runs pytest on 3.11–3.13 with submodules | Present | .github/workflows/ci.yml:15; .github/workflows/ci.yml:21; .github/workflows/ci.yml:37 |

## Dependencies & runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional |
| - | - | - |
| jsonschema | Validation via Draft 2020-12 | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend client and tests | Required | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test suite | Required-for-tests | requirements.txt:3; tests/test_backend.py:1 |
| referencing | Local registry support | Optional | mcp/validate.py:10 |
| fastapi | HTTP adapter factory | Optional | mcp/http_main.py:8 |
| uvicorn | Runtime suggested in docs | Optional | README.md:72 |

## Environment variables (bullets: name, default, fallback, error behavior)
- `SYN_SCHEMAS_DIR` – Overrides schema directory; missing or non-dir causes startup error (mcp/core.py:12; mcp/__main__.py:21).
- `SYN_EXAMPLES_DIR` – Overrides examples directory with submodule fallback when unset (mcp/core.py:27; mcp/core.py:31).
- `SYN_BACKEND_URL` – Enables backend POSTs; absent returns `unsupported` (mcp/backend.py:30; mcp/backend.py:32).
- `SYN_BACKEND_ASSETS_PATH` – Customizes POST path, defaulting to `/synesthetic-assets/` (mcp/backend.py:17; mcp/backend.py:55).
- `MCP_HOST` – Defaults to `0.0.0.0`; configurable via env (mcp/__main__.py:29).
- `MCP_PORT` – Defaults to `7000`; validated as int within 0–65535 (mcp/__main__.py:30; mcp/__main__.py:35).

## Documentation accuracy (bullets: README vs. code/spec)
- README lists minimal dependencies and optional extras consistent with requirements and imports (README.md:63; mcp/validate.py:10; mcp/http_main.py:8).
- README describes env override order matching implementation (README.md:83; mcp/core.py:12).
- README’s serving instructions align with compose/serve script behavior (README.md:135; docker-compose.yml:23; serve.sh:23).

## Detected divergences
- None beyond noted missing items.

## Recommendations (concrete next steps)
- Add a CLI/flag to `python -m mcp` (or sibling script) that validates assets and exits non-zero on failure to satisfy validation wiring expectations (mcp/__main__.py:119).
- Extend entrypoint tests to cover misconfiguration errors (invalid `SYN_SCHEMAS_DIR`, bad `MCP_PORT`) and assert `mcp:error` logs with exit codes (mcp/__main__.py:21; mcp/__main__.py:35; tests/test_entrypoint.py:30).
- Check in `.env.example` enumerating MCP_HOST/MCP_PORT and SYN_* variables referenced by compose and docs (`docker-compose.yml:18`; README.md:83).
