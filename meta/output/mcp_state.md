# MCP State Audit (v0.2.3)

## Summary of repo state

The `synesthetic-mcp` repository is in a good state. The implementation aligns well with the `docs/mcp_spec.md` (v0.2.3). The project features a comprehensive test suite, clear documentation, and a well-organized structure. The core STDIO JSON-RPC server is implemented as specified, including critical features like the ready file, payload size limits, and graceful shutdown. Schema and example discovery mechanisms are robust, with support for environment variable overrides and fallback to the submodule.

## Top gaps & fixes

1.  **Divergence: `validate_asset` does not explicitly reject missing `schema` parameter.** The spec requires the `schema` parameter for `validate_asset`. The implementation in `mcp/stdio_main.py` passes an empty string if the parameter is missing, and `mcp/validate.py` fails during schema loading. This should be an explicit check at the beginning of `validate_asset`.
    *   **Fix:** Add a check at the start of `mcp.validate.validate_asset` to ensure `schema` is a non-empty string, returning a `validation_failed` error if not.
2.  **Divergence: `get_example` can return `validation_failed` which is not in the spec.** The `get_example` function in `mcp/core.py` calls `validate_asset` and can return its result. The spec for `get_example` only defines `not_found` as a failure reason.
    *   **Fix:** The spec should be updated to include the possibility of a `validation_failed` reason in the response for `get_example`.
3.  **Missing Test Coverage:** The existing `AGENTS.md` file correctly identifies missing test coverage for `MCP_READY_FILE=""` (disabling ready file creation), `SYN_BACKEND_ASSETS_PATH` normalization, and `httpx.HTTPError` handling in `populate_backend`.
    *   **Fix:** Add tests to cover these cases.

## Alignment with mcp_spec.md

| Spec item | Status | Evidence |
| :--- | :--- | :--- |
| STDIO NDJSON framing & sequential handling | Present | `docs/mcp_spec.md:38`, `mcp/stdio_main.py:38` |
| Ready file `<pid> <ISO8601>` lifecycle | Present | `docs/mcp_spec.md:49`, `mcp/__main__.py:88`, `tests/test_stdio.py:62` |
| Transport limited to STDIO | Present | `docs/mcp_spec.md:36`, `mcp/__main__.py:35`, `docker-compose.yml:23` |
| 1 MiB per-request STDIO limit | Present | `docs/mcp_spec.md:41`, `mcp/stdio_main.py:45`, `tests/test_stdio.py:171` |
| `unsupported` responses use `detail` | Present | `docs/mcp_spec.md:153`, `mcp/stdio_main.py:30`, `mcp/backend.py:32` |
| Validation errors use RFC6901 ordering | Present | `docs/mcp_spec.md:121`, `mcp/validate.py:147`, `tests/test_validate.py:37` |
| `validate_asset` requires `schema` | Divergent | `docs/mcp_spec.md:99`, `mcp/stdio_main.py:25` (passes empty string) |

## STDIO server entrypoint & process model

*   **NDJSON framing:** The server reads newline-delimited JSON objects from stdin (`mcp/stdio_main.py:39`).
*   **Blocking loop:** The server processes requests sequentially in a single thread (`mcp/stdio_main.py:38`).
*   **Signals:** The server handles `SIGINT` and `SIGTERM` for graceful shutdown, finishing in-flight requests (`mcp/__main__.py:80`).
*   **Readiness file:** The server creates a ready file at `MCP_READY_FILE` (default `/tmp/mcp.ready`) containing the PID and timestamp, and removes it on shutdown (`mcp/__main__.py:53`, `mcp/__main__.py:73`).
*   **Shutdown semantics:** On `KeyboardInterrupt` (raised by the signal handler), the server cleans up the ready file and exits gracefully (`mcp/__main__.py:99`).

## Golden request/response example

| Aspect | Status | Evidence |
| :--- | :--- | :--- |
| Success frame mirrors spec sample | Present | `docs/mcp_spec.md:60`, `mcp/stdio_main.py:61`, `tests/test_stdio.py:29` |
| Error frame echoes request `id` | Present | `docs/mcp_spec.md:135`, `mcp/stdio_main.py:66`, `tests/test_stdio.py:126` |

## Payload size guard

| Method | Present/Missing/Divergent | Evidence |
| :--- | :--- | :--- |
| STDIO request size check (1 MiB) | Present | `docs/mcp_spec.md:41`, `mcp/stdio_main.py:45`, `tests/test_stdio.py:171` |
| Validation payload cap | Present | `mcp/validate.py:107`, `tests/test_validate.py:47` |
| Backend payload cap | Present | `mcp/backend.py:38`, `tests/test_backend.py:55` |

## Schema validation contract

*   **Required schema param:** The `schema` parameter for `validate_asset` is required by the spec, but the implementation does not enforce this, leading to a `schema_load_failed` error instead of a more direct error message. This is a **Divergent** behavior.
*   **Alias handling:** The `nested-synesthetic-asset` alias is correctly mapped to the `synesthetic-asset` schema for validation (`mcp/validate.py:17`).
*   **Error ordering:** Validation errors are sorted by `path` and then `msg` as required (`mcp/validate.py:147`).
*   **`validate_asset` support:** The `validate_asset` method is implemented and callable.

## Logging hygiene

*   **stdout vs stderr separation:** The implementation correctly sends only JSON-RPC frames to `stdout` (`mcp/stdio_main.py:52`) and all logging to `stderr` (`mcp/__main__.py:178`).

## Container & health

| Aspect | Present/Missing/Divergent | Evidence |
| :--- | :--- | :--- |
| Dockerfile | Present | `Dockerfile` |
| docker-compose.yml | Present | `docker-compose.yml` |
| Healthcheck | Present | `docker-compose.yml:28` (checks for `MCP_READY_FILE`) |

## Schema discovery & validation

| Source | Mechanism | Evidence |
| :--- | :--- | :--- |
| Environment variables | `SYN_SCHEMAS_DIR` and `SYN_EXAMPLES_DIR` override default paths. | `mcp/core.py:13`, `mcp/core.py:25` |
| Submodule | Falls back to `libs/synesthetic-schemas` if environment variables are not set. | `mcp/core.py:17`, `mcp/core.py:29` |
| Validation | Uses `jsonschema` Draft 2020-12. | `mcp/validate.py:8` |

## Test coverage

| Feature | Tested? | Evidence |
| :--- | :--- | :--- |
| STDIO framing, ready file, oversize guard | Yes | `tests/test_stdio.py` |
| Transport setup & shutdown handling | Yes | `tests/test_entrypoint.py` |
| Validation aliasing, ordering, payload cap | Yes | `tests/test_validate.py` |
| Backend success/error/size handling | Yes | `tests/test_backend.py` |
| Env overrides & submodule fallback | Yes | `tests/test_env_discovery.py`, `tests/test_submodule_integration.py` |
| Diff determinism | Yes | `tests/test_diff.py` |
| `validate_asset` with missing schema | Yes | `tests/test_validate.py:57` |

## Dependencies & runtime

| Package | Used in | Required/Optional |
| :--- | :--- | :--- |
| jsonschema | `mcp/validate.py` | Required |
| httpx | `mcp/backend.py` | Required |
| pytest | `tests/` | Required (tests) |
| referencing | `mcp/validate.py` | Optional |

## Environment variables

*   `MCP_ENDPOINT`: Must be `stdio`. Any other value causes a startup failure.
*   `MCP_READY_FILE`: Path to the ready file. If empty, the file is not created. Defaults to `/tmp/mcp.ready`.
*   `SYN_SCHEMAS_DIR`: Overrides the schema directory. Startup fails if the directory is missing.
*   `SYN_EXAMPLES_DIR`: Overrides the examples directory.
*   `SYN_BACKEND_URL`: Enables the `populate_backend` method. If unset, the method returns an `unsupported` error.
*   `SYN_BACKEND_ASSETS_PATH`: Custom path for backend POST requests. Defaults to `/synesthetic-assets/`.

## Documentation accuracy

*   `README.md` and `docs/mcp_spec.md` are mostly consistent. The `README.md` provides a good overview of the project and its features, while the spec provides detailed technical contracts.
*   The `README.md` accurately reflects the implemented features, including the STDIO-only transport and the 1 MiB payload guard.

## Detected divergences

*   **`validate_asset` schema parameter:** The `schema` parameter is required by the spec but not explicitly enforced as such in the implementation.
*   **`get_example` error response:** The `get_example` method can return a `validation_failed` error, which is not documented in the spec.

## Recommendations

*   Modify `mcp.validate.validate_asset` to explicitly check for a non-empty `schema` string and return a `validation_failed` error if it is missing or empty.
*   Update the `docs/mcp_spec.md` to include `validation_failed` as a possible failure reason for the `get_example` method.
*   Add a test case for `MCP_READY_FILE=""` to ensure the ready file creation is correctly skipped.
*   Add a test case for `SYN_BACKEND_ASSETS_PATH` to verify the leading-slash normalization.
*   Add a test case that mocks `httpx.HTTPError` in `populate_backend` to ensure the `backend_error` with status 503 is returned correctly.