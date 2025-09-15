## Summary of repo state
- Code present: `mcp/__init__.py`, `mcp/core.py`, `mcp/validate.py`, `mcp/diff.py`, `mcp/backend.py`, `mcp/stdio_main.py`, `mcp/http_main.py`.
- Tests present: `tests/test_validate.py`, `tests/test_diff.py`, `tests/test_backend.py`, `tests/test_env_discovery.py`, `tests/test_submodule_integration.py`.
- Submodule paths referenced and present: `libs/synesthetic-schemas/jsonschema`, `libs/synesthetic-schemas/examples`.
- Requirements pinned: `jsonschema`, `httpx`, `pytest` (no extras) `requirements.txt:1`.
- Spec file present: `docs/mcp_spec.md`.

## Alignment with init prompt (evidence from code)
- Disk discovery with env overrides: `_schemas_dir`, `_examples_dir` implement env → submodule → fixtures `mcp/core.py:15`, `mcp/core.py:28`.
- Deterministic listings: schemas sorted by name/version/path `mcp/core.py:53`; examples by component/path `mcp/core.py:77`.
- JSON Schema (Draft 2020-12) validation with base-URI when `$id` missing `mcp/validate.py:8`, `mcp/validate.py:104`.
- Alias handling: `nested-synesthetic-asset` maps to `synesthetic-asset` `mcp/validate.py:18`.
- Example inference: `$schemaRef` support and `SynestheticAsset_*` → nested alias `mcp/core.py:86`, `mcp/core.py:96`.
- Validation errors: RFC6901 pointers, sorted deterministically `mcp/validate.py:121`, `mcp/validate.py:124`.
- Diff: add/remove/replace only; arrays single replace; output sorted `mcp/diff.py:33`, `mcp/diff.py:50`.
- Backend populate: env-gated, 5s timeout, mockable client `mcp/backend.py:14`, `mcp/backend.py:51`.
- Runtimes: stdio dispatcher and optional HTTP app factory `mcp/stdio_main.py:13`, `mcp/http_main.py:6`.

## Alignment with spec (evidence from code)
- IO contracts implemented: list/get schemas/examples, validate, diff, populate `mcp/core.py:41`, `mcp/validate.py:81`, `mcp/diff.py:42`, `mcp/backend.py:24`.
- Determinism: sorting rules enforced for listings and validation errors `mcp/core.py:53`, `mcp/core.py:77`, `mcp/validate.py:124`.
- Limits: 1 MiB payload enforced for validate and backend `mcp/validate.py:23`, `mcp/backend.py:34`.
- Backend behavior: env-gated with 5s timeout; error mapping for HTTP/network `mcp/backend.py:51`, `mcp/backend.py:56`.

## Detected gaps or intentional divergences
- Spec says no local fixture fallback `docs/mcp_spec.md:20`; code includes fixture fallback `mcp/core.py:24`, `mcp/core.py:37` (divergent).
- Init prompt lists extra deps (`pydantic`, `ruff`, `mypy`) in requirements; they are absent `meta/prompts/init_mcp_repo.json:38`, `requirements.txt:1` (missing vs prompt).
- Init prompt lists example fixtures (`tests/fixtures/examples/asset.valid.json`, `asset.invalid.json`); directory exists but files are absent `tests/fixtures/examples`, `rg` shows none (missing vs prompt).
- Validation error shape: `validate_asset` returns `{ok, errors}` without `reason`; spec Error Model shows a `reason:"validation_failed"` example `mcp/validate.py:125`, `docs/mcp_spec.md:68` (divergent).
- Unsupported tool shape: stdio returns `{ok:false, reason:"unsupported"}` without `msg`; spec shows `msg` field `mcp/stdio_main.py:30`, `docs/mcp_spec.md:81` (divergent).

## Recommendations (concrete next steps)
- Reconcile fixture fallback: either remove fixture fallback in code to match spec, or update spec Boundaries to document env → submodule → fixtures (and keep README consistent).
- Align error shapes with spec: add `reason:"validation_failed"` to `validate_asset` failures and add `msg` to unsupported responses, or update `docs/mcp_spec.md` Error Model to reflect current shapes.
- Address prompt-vs-repo deps: either add `pydantic`, `ruff`, `mypy` to `requirements.txt` or amend `meta/prompts/init_mcp_repo.json` to list only `jsonschema`, `httpx`, `pytest`.
- Add the prompt-listed example fixtures under `tests/fixtures/examples/` or update the prompt to reflect reliance on the submodule for examples.
