# synesthetic-mcp: State Audit (v0.1.0)

## Summary of repo state
- Minimal MCP-style adapter implemented in Python 3.11+ with pinned deps.
- Core tools provided: schema/example discovery, validation (2020-12), diff (RFC6902 add/remove/replace), backend populate (env‑gated), stdio loop, optional FastAPI app.
- Tests and golden fixtures included for validation, diff, backend behavior, and env overrides.
- Determinism rules implemented (sorted listings, sorted error paths, deterministic diff ordering and list handling).

## Alignment with init prompt
- Language/style: Python ≥3.11, KISS, minimal deps in `requirements.txt` — aligned.
- Schemas/examples: read from disk; env overrides `SYN_SCHEMAS_DIR` / `SYN_EXAMPLES_DIR` — aligned (`mcp/core.py`).
- JSON Schema: Draft 2020-12; `$id`/base-URI set from file path when missing — aligned (`mcp/validate.py`).
- Diff: RFC6902 with add/remove/replace only; RFC6901 pointers; deterministic list handling — aligned (`mcp/diff.py`).
- Backend: disabled unless `SYN_BACKEND_URL` set; httpx timeout 5s; no retries; fully mockable — aligned (`mcp/backend.py`, tests use `httpx.MockTransport`).
- Tests: pytest tests with fixtures; no sys.path hacks; deterministic assertions — mostly aligned. See gap on “require editable install”.
- Limits: 1 MiB max payload enforced for validation and backend — aligned.
- Output structure: only the requested files added/updated — aligned.

## Alignment with spec (docs/mcp_spec.md)
- IO contracts implemented for all listed tools with expected shapes and fields.
- Determinism documented and implemented: sorted outputs and error paths; diff ordering and list replacement.
- Error model: `validation_failed`, `backend_error`, `unsupported` reasons surfaced consistently where applicable.
- Runtimes: stdio loop present; FastAPI app factory optional import — aligned.
- Limits and env behavior documented in spec and matched in code.

## Detected gaps or deviations
- Editable install requirement vs “no packaging metadata” constraint:
  - Prompt exit criteria says “requirements install + editable install” should succeed, but repository intentionally omits packaging metadata (no `pyproject.toml`/`setup.cfg`).
  - Current tests do not enforce import via editable install; they import the package from repo root. This may fail CI scenarios expecting `pip install -e .`.
- JSON Schema `$ref` resolution not covered by tests:
  - Implementation sets `$id` to file URI when missing and uses `Draft202012Validator`, which supports relative `$ref` via base URI. However, no fixture asserts multi-file `$ref` behavior/determinism.
- Listing determinism tests are implicit:
  - `test_env_discovery` exercises discovery but does not explicitly assert overall sorting order for `list_schemas`/`list_examples` across multiple entries.
- Stdio/HTTP adapters are untested:
  - Functional but not covered by tests; not strictly required but worth basic smoke tests for contract compliance.

## Recommendations (next steps)
- Resolve editable-install vs packaging constraint (choose one):
  - Option A (preferred for CI): add minimal `pyproject.toml` with `project.name = "mcp"` and `packages = ["mcp"]` to enable `pip install -e .` while keeping scope minimal; update prompt to allow this file.
  - Option B: update prompt/spec to remove “editable install” requirement and explicitly allow running tests from repo root without packaging metadata.
- Add tests for `$ref` resolution:
  - Create a small two-file schema with a relative `$ref` and an example validating that ref resolution works deterministically under Draft 2020‑12.
- Strengthen determinism assertions:
  - Add multi-entry schemas/examples fixtures and tests that `list_schemas` and `list_examples` are sorted by the documented keys.
- Add smoke tests for runtimes (optional):
  - Stdio: feed a couple of newline-delimited requests and assert responses.
  - HTTP: conditionally test `create_app` if FastAPI present; otherwise skip.
- Consider documenting payload limit behavior in README:
  - Add a short note that requests >1 MiB return `ok: false` with `payload_too_large` at `/`.

