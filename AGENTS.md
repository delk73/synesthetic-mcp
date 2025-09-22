# AGENTS.md — Repo Snapshot

## Repo Summary
- STDIO loop enforces NDJSON framing, 1 MiB pre-parse guard, and spec-compliant `unsupported` details (docs/mcp_spec.md:38; docs/mcp_spec.md:41; docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/stdio_main.py:45; tests/test_stdio.py:152; tests/test_stdio.py:171)
- Entrypoint locks transport to STDIO, writes `<pid> <ISO8601>` ready markers, and restores signal handlers during shutdown (docs/mcp_spec.md:36; docs/mcp_spec.md:49; docs/mcp_spec.md:215; mcp/__main__.py:35; mcp/__main__.py:53; mcp/__main__.py:105; tests/test_entrypoint.py:31)
- Validation handles schema aliases, `$schemaRef` stripping, payload caps, and RFC6901 ordering across CLI and backend paths (docs/mcp_spec.md:99; docs/mcp_spec.md:198; mcp/validate.py:17; mcp/validate.py:106; tests/test_validate.py:37; tests/test_validate.py:47; tests/test_validate.py:57)
- Backend populate honours env gating, payload limits, validation-before-post, and deterministic mocks (docs/mcp_spec.md:108; docs/mcp_spec.md:178; mcp/backend.py:30; mcp/backend.py:38; mcp/backend.py:49; tests/test_backend.py:21; tests/test_backend.py:55; tests/test_backend.py:95)
- README and spec document the same discovery order, alias behaviour, and 1 MiB STDIO guard implemented in code (docs/mcp_spec.md:28; docs/mcp_spec.md:41; README.md:35; README.md:127; README.md:138; README.md:167)

## Dependencies
| Package | Purpose | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:7 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_entrypoint.py:31 |
| referencing | JSON Schema registry support | Optional | mcp/validate.py:9 |

## Environment Variables
- `MCP_ENDPOINT` defaults to STDIO and rejects other transports (docs/mcp_spec.md:36; mcp/__main__.py:35; tests/test_entrypoint.py:92)
- `MCP_READY_FILE` defaults to `/tmp/mcp.ready`; blank disables creation and shutdown removes it (docs/mcp_spec.md:49; mcp/__main__.py:45; mcp/__main__.py:105)
- `SYN_SCHEMAS_DIR` must exist or startup fails (docs/mcp_spec.md:176; mcp/__main__.py:22; tests/test_entrypoint.py:78)
- `SYN_EXAMPLES_DIR` overrides example discovery (docs/mcp_spec.md:177; mcp/core.py:25; tests/test_env_discovery.py:35)
- `SYN_BACKEND_URL` gates backend populate and returns `reason:"unsupported"` when unset (docs/mcp_spec.md:178; mcp/backend.py:30; tests/test_backend.py:21)
- `SYN_BACKEND_ASSETS_PATH` defaults to `/synesthetic-assets/` and prepends a slash when missing (docs/mcp_spec.md:179; mcp/backend.py:17)

## Tests Overview
| Focus | Status | Evidence |
| - | - | - |
| STDIO framing, ready file, oversize guard | ✅ | tests/test_stdio.py:17; tests/test_stdio.py:62; tests/test_stdio.py:171 |
| Transport setup & shutdown handling | ✅ | tests/test_entrypoint.py:31; tests/test_entrypoint.py:92 |
| Validation aliasing, ordering, payload cap, missing schema | ✅ | tests/test_validate.py:37; tests/test_validate.py:47; tests/test_validate.py:57 |
| Backend success/error/size handling | ✅ | tests/test_backend.py:21; tests/test_backend.py:55; tests/test_backend.py:95 |
| Env overrides & submodule fallback | ✅ | tests/test_env_discovery.py:29; tests/test_submodule_integration.py:34 |
| Diff determinism | ✅ | tests/test_diff.py:4 |

## Spec Alignment
| Spec Item | Status | Evidence |
| - | - | - |
| STDIO NDJSON framing & sequential handling | Present | docs/mcp_spec.md:38; mcp/stdio_main.py:38 |
| Ready file `<pid> <ISO8601>` lifecycle | Present | docs/mcp_spec.md:49; mcp/__main__.py:88; tests/test_stdio.py:62 |
| Transport limited to STDIO | Present | docs/mcp_spec.md:36; mcp/__main__.py:35; docker-compose.yml:23 |
| 1 MiB per-request STDIO limit | Present | docs/mcp_spec.md:41; mcp/stdio_main.py:45; tests/test_stdio.py:171 |
| `unsupported` responses use `detail` | Present | docs/mcp_spec.md:153; mcp/stdio_main.py:30; mcp/backend.py:32 |
| Validation errors use RFC6901 ordering | Present | docs/mcp_spec.md:121; mcp/validate.py:147; tests/test_validate.py:37 |

## Golden Example
| Aspect | Status | Evidence |
| - | - | - |
| Success frame mirrors spec sample | Present | docs/mcp_spec.md:60; mcp/stdio_main.py:61; tests/test_stdio.py:29 |
| Error frame echoes request `id` | Present | docs/mcp_spec.md:135; mcp/stdio_main.py:66; tests/test_stdio.py:126 |

## Payload Guard
| Case | Status | Evidence |
| - | - | - |
| STDIO request size check (1 MiB) | Present | docs/mcp_spec.md:41; mcp/stdio_main.py:45; tests/test_stdio.py:171 |
| Validation payload cap | Present | mcp/validate.py:107; tests/test_validate.py:47 |
| Backend payload cap | Present | mcp/backend.py:38; tests/test_backend.py:55 |

## Recommendations
- Add regression coverage for `MCP_READY_FILE=""` to ensure ready-file suppression works (docs/mcp_spec.md:49; mcp/__main__.py:45; tests/test_stdio.py:62)
- Test `SYN_BACKEND_ASSETS_PATH=custom-assets` to cover the leading-slash normalization branch (mcp/backend.py:17; tests/test_backend.py:36)
- Mock `httpx.HTTPError` in populate to assert the 503 `backend_error` path (docs/mcp_spec.md:108; mcp/backend.py:60; tests/test_backend.py:47)
