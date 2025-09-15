## Summary of repo state
- Code present: `mcp/__init__.py`, `mcp/core.py`, `mcp/validate.py`, `mcp/diff.py`, `mcp/backend.py`, `mcp/stdio_main.py`, `mcp/http_main.py`.
- Tests present: `tests/test_validate.py`, `tests/test_diff.py`, `tests/test_backend.py`, `tests/test_env_discovery.py`, `tests/test_submodule_integration.py`.
- Submodule paths referenced and present: `libs/synesthetic-schemas/jsonschema`, `libs/synesthetic-schemas/examples`.
- Requirements pinned: `jsonschema`, `httpx`, `pytest` (no extras).
- Spec file present: `docs/mcp_spec.md`.

## Alignment with init prompt (evidence from code)
- Language/deps: Python 3.11+, minimal deps pinned in `requirements.txt` (JSON Schema, httpx, pytest) `requirements.txt:1`.
- Discovery order: env → submodule → fixtures implemented in `mcp/core.py:15`, `mcp/core.py:21`, `mcp/core.py:25` and `mcp/core.py:28`, `mcp/core.py:34`, `mcp/core.py:38`.
- Deterministic listings: schemas sorted by name/version/path `mcp/core.py:53`; examples by component/path `mcp/core.py:77`.
- JSON Schema (Draft 2020-12): uses `Draft202012Validator` `mcp/validate.py:8`.
- Base-URI for $ref: sets `$id` from file path when missing `mcp/validate.py:104`–`mcp/validate.py:113`.
- Ref registry: loads all schemas by `$id` into `referencing.Registry` when available `mcp/validate.py:55`–`mcp/validate.py:77`.
- Alias handling: `nested-synesthetic-asset` → `synesthetic-asset` `mcp/validate.py:18`–`mcp/validate.py:20`.
- Example inference: treats `SynestheticAsset_*.json` as nested alias `mcp/core.py:96`–`mcp/core.py:99` and ignores `$schemaRef` during validation `mcp/validate.py:88`–`mcp/validate.py:94`.
- Validation errors: RFC6901 pointers via absolute path `mcp/validate.py:120`–`mcp/validate.py:122`; sorted by path then message `mcp/validate.py:124`.
- Diff: add/remove/replace only; dict keys sorted; arrays single replace; patch sorted by path/op `mcp/diff.py:21`–`mcp/diff.py:36`, `mcp/diff.py:49`–`mcp/diff.py:51`.
- Backend gating: disabled unless `SYN_BACKEND_URL` set `mcp/backend.py:21`–`mcp/backend.py:24`; 5s timeout `mcp/backend.py:50`–`mcp/backend.py:54`.
- Stdio loop: minimal dispatcher returning unsupported for unknown method `mcp/stdio_main.py:13`–`mcp/stdio_main.py:31`.
- HTTP app factory: optional FastAPI import with clear ImportError `mcp/http_main.py:7`–`mcp/http_main.py:12`.
- Tests cover: validation success/failure ordering `tests/test_validate.py:14`–`tests/test_validate.py:24`, `tests/test_validate.py:27`–`tests/test_validate.py:34`; diff idempotence/list replacement `tests/test_diff.py:4`–`tests/test_diff.py:19`; backend env/paths/errors `tests/test_backend.py:20`–`tests/test_backend.py:39`; env discovery overrides `tests/test_env_discovery.py:7`–`tests/test_env_discovery.py:36`; submodule integration (skipped if absent) `tests/test_submodule_integration.py:19`–`tests/test_submodule_integration.py:41`.

## Alignment with spec (evidence from code)
- IO contracts: functions and shapes implemented per `docs/mcp_spec.md` (list/get, validate, diff, populate) reflected in `mcp/core.py`, `mcp/validate.py`, `mcp/diff.py`, `mcp/backend.py`.
- Determinism: sorting rules implemented for lists and errors `mcp/core.py:53`, `mcp/core.py:77`, `mcp/validate.py:124`, `mcp/diff.py:49`.
- Limits: 1 MiB payload enforced for validation and backend `mcp/validate.py:23`–`mcp/validate.py:44`, `mcp/backend.py:26`–`mcp/backend.py:33`.
- Backend behavior: env-gated, 5s timeout, no retries; error mapping for HTTP/network `mcp/backend.py:50`–`mcp/backend.py:66`, success/error shapes `mcp/backend.py:69`–`mcp/backend.py:86`.
- Schema/example discovery order matches spec `docs/mcp_spec.md:14`–`docs/mcp_spec.md:22` and implementation `mcp/core.py:15`–`mcp/core.py:38`.

## Detected gaps or deviations (code vs. prompt/spec)
- Missing packages from init prompt: `pydantic`, `ruff`, `mypy` not present in `requirements.txt` (prompt expects them) `meta/prompts/init_mcp_repo.json:38` vs. `requirements.txt:1`–`requirements.txt:3`.
- Missing fixture examples listed in init prompt: `tests/fixtures/examples/asset.valid.json`, `asset.invalid.json` not in repo (only `tests/fixtures/schemas/asset.schema.json` exists).
- Validation error shape: `validate_asset` returns `{ok, errors}` without `reason` `mcp/validate.py:125`; spec’s Error Model shows `reason:"validation_failed"` for validation errors `docs/mcp_spec.md:40`–`docs/mcp_spec.md:48`.
- Unsupported tool message: stdio returns only `{ok:false, reason:"unsupported"}` `mcp/stdio_main.py:30`; spec shows an additional `msg` field for unsupported `docs/mcp_spec.md:56`–`docs/mcp_spec.md:62`.
- Fallback examples dir absence: default `tests/fixtures/examples` path is referenced `mcp/core.py:10`, `mcp/core.py:28`–`mcp/core.py:38` but not present in repo; code handles absence by returning empty lists, tests rely on submodule or env-provided examples.

## Recommendations (concrete next steps)
- Add missing prompt-listed deps or update prompt: include `pydantic`, `ruff`, `mypy` in `requirements.txt` or adjust `meta/prompts/init_mcp_repo.json` to match minimal current deps.
- Add fixture examples per prompt: create `tests/fixtures/examples/asset.valid.json` and `asset.invalid.json` to satisfy discovery fallback and tests coverage opportunity.
- Align unsupported error shape with spec: include `msg` for unsupported in stdio dispatcher and HTTP (if applicable), or update `docs/mcp_spec.md` to match actual return shapes.
- Consider adding `reason:"validation_failed"` to `validate_asset` error output to match the spec’s Error Model, or revise the spec to reflect current `{ok, errors}` contract.
- Optionally add a minimal `tests/fixtures/examples` directory (even empty with README) to make discovery paths fully present in-repo.
