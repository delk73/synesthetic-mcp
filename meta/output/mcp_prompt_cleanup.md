# Init Prompt And Docs Cleanup

**Summary**
- Align prompt and docs to current design: submodule-first discovery, minimal dependencies, no local fixtures.
- Document optional extras: fastapi, uvicorn, referencing.
- Clarify discovery behavior when paths are missing.

**Init Prompt Updates (meta/prompts/init_mcp_repo.json)**
- Remove fixtures: drop defaults pointing to `tests/fixtures/*` for `SYN_SCHEMAS_DIR` and `SYN_EXAMPLES_DIR`.
- Discovery order: state env overrides → submodule; if neither exists, operations return not found.
- Dependencies: list minimal only — `jsonschema`, `httpx`, `pytest`.
- Drop extra tooling: remove `pydantic`, `ruff`, `mypy` from requirements.
- Tests language: remove references to "golden fixtures"; rely on submodule + env overrides.
- File list: remove `tests/fixtures/*` entries; keep optional `mcp/http_main.py`.

**README Installation Section Edits (README.md)**
- Dependencies: present minimal deps only and add optional extras:
  - Minimal: `jsonschema`, `httpx`, `pytest`.
  - Optional: `fastapi` (HTTP app), `uvicorn` (dev server), `referencing` (optional import for JSON Schema refs).
- Structure: remove `tests/fixtures/` from the repo layout.
- Discovery order: explicitly list env overrides → submodule → not found (empty listings or get failure).

**Spec Clarifications (docs/mcp_spec.md)**
- Discovery: specify env overrides → submodule; if neither exists, listings may be empty and get operations return not found; no fixture fallback.
- Dependencies: confirm minimal deps and document optional extras (`fastapi`, `uvicorn`, `referencing`).

**Resulting State**
- Init prompt no longer refers to fixtures or extra dev deps.
- README/docs describe submodule-first env discovery with no local fixtures.
- Optional dependencies documented as extras.
