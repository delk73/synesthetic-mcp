## Summary of repo state
- STDIO transport matches the spec with an NDJSON loop, 1 MiB guard, and sequential replies that are covered by tests (mcp/stdio_main.py:45, mcp/stdio_main.py:53, tests/test_stdio.py:29).
- Validation, diff, and backend populate tools behave deterministically with local-only schema resolution and thorough test coverage (mcp/validate.py:106, mcp/diff.py:24, mcp/backend.py:28, tests/test_backend.py:28).
- Key gaps are the missing socket transport and absent path-traversal protection around schema/example access (mcp/__main__.py:35, mcp/core.py:58, mcp/core.py:108, mcp/validate.py:47).

## Top gaps & fixes (3-5 bullets)
- Add path normalization/rejection for `..` segments when serving schemas/examples and loading schemas before validation (mcp/core.py:58, mcp/core.py:108, mcp/validate.py:47).
- Implement the optional Unix-domain socket transport or explicitly document it as out of scope for this release (docs/mcp_spec.md:67, mcp/__main__.py:35).
- Provide an explicit STDIO test exercising the `validate` alias to lock in compatibility (mcp/stdio_main.py:22, tests/test_stdio.py:29).
- Align the README’s serve instructions with the existing `up.sh` helper or add the referenced script (README.md:43, up.sh:1).

## Alignment with mcp_spec.md (table: Spec item → Status → Evidence)
| Spec item | Status | Evidence |
| - | - | - |
| STDIO NDJSON loop & sequential responses | Present | mcp/stdio_main.py:45; tests/test_stdio.py:29 |
| Ready file lifecycle & SIGINT/SIGTERM handling | Present | mcp/__main__.py:88; tests/test_entrypoint.py:55; tests/test_stdio.py:82 |
| 1 MiB transport payload cap | Present | mcp/stdio_main.py:53; tests/test_stdio.py:184 |
| "validate" alias accepted for compatibility | Present (needs coverage) | mcp/stdio_main.py:22; docs/mcp_spec.md:94 |
| Socket transport (UDS) | Missing | docs/mcp_spec.md:67; mcp/__main__.py:35 |
| Path-traversal rejection for schemas/examples | Divergent | mcp/core.py:58; mcp/core.py:108; mcp/validate.py:47 |
| `get_example` returns `validation_failed` on invalid payloads | Present | mcp/core.py:120; tests/test_validate.py:32 |
| Local-only `$ref` resolution | Present | mcp/validate.py:52; mcp/validate.py:99 |

## Transports
- STDIO is the sole transport; non-STDIO endpoints raise a setup failure (mcp/__main__.py:35).
- The RPC loop reads/writes newline-delimited JSON objects on stdin/stdout synchronously (mcp/stdio_main.py:45).
- Transport readiness is logged to stderr and gated by the ready file (mcp/__main__.py:88, mcp/__main__.py:89).

## STDIO server entrypoint & process model (bullets: NDJSON framing, blocking loop, signals, readiness file, shutdown semantics, stdout vs stderr)
- NDJSON framing comes from trimming each stdin line, parsing once, and emitting one JSON object per line (mcp/stdio_main.py:45, mcp/stdio_main.py:64).
- The loop is blocking and sequential—`for line in sys.stdin` ensures FIFO handling (mcp/stdio_main.py:47).
- SIGTERM triggers a `KeyboardInterrupt`, allowing graceful shutdown like SIGINT (mcp/__main__.py:76, mcp/__main__.py:92).
- The ready file writes `<pid> <ISO8601>` on startup and is removed on exit (mcp/__main__.py:59, mcp/__main__.py:105).
- Shutdown logs `mcp:shutdown mode=stdio` and restores prior handlers (mcp/__main__.py:99, mcp/__main__.py:100).
- Only JSON-RPC frames hit stdout; logs stay on stderr via `logging` (mcp/stdio_main.py:59, mcp/__main__.py:170).

## Socket server (if present) (bullets: UDS path, perms, multi-client handling, per-connection ordering, unlink on shutdown, readiness/shutdown logs)
- Missing: socket transport is not implemented; STDIO-only enforcement blocks `MCP_ENDPOINT=socket` (mcp/__main__.py:35).

## Golden request/response examples (table: Method → Success frame Present/Missing/Divergent → Error frame Present/Missing/Divergent → Evidence)
| Method | Success frame | Error frame | Evidence |
| - | - | - | - |
| list_schemas | Present | — | tests/test_stdio.py:29 |
| get_schema | Present | Present | tests/test_validate.py:19; tests/test_validate.py:14 |
| validate_asset | Present | Present | tests/test_stdio.py:108; tests/test_stdio.py:17; tests/test_validate.py:56 |
| validate (alias) | Missing | Missing | mcp/stdio_main.py:22 |
| get_example | Present | Present | tests/test_submodule_integration.py:47; tests/test_validate.py:32 |
| diff_assets | Present | — | tests/test_diff.py:6; mcp/diff.py:43 |
| populate_backend | Present | Present | tests/test_backend.py:28; tests/test_backend.py:57 |
| Malformed JSON-RPC frame | — | Present | tests/test_stdio.py:139 |

## Payload size guard (table: Method → STDIO guard → Socket guard → Evidence)
| Method | STDIO guard | Socket guard | Evidence |
| - | - | - | - |
| STDIO request framing | Present | Missing | mcp/stdio_main.py:53; tests/test_stdio.py:184; mcp/__main__.py:35 |
| validate_asset payload | Present | Missing | mcp/validate.py:114; tests/test_validate.py:56 |
| populate_backend payload | Present | Missing | mcp/backend.py:30; tests/test_backend.py:65 |

## Schema validation contract (bullets: required schema param, alias handling, error ordering, explicit validate_asset behavior)
- The STDIO boundary rejects missing/empty schema parameters with `validation_failed` (mcp/stdio_main.py:24, tests/test_stdio.py:17).
- `validate_asset` enforces the schema requirement again inside the tool and yields `schema_required` (mcp/validate.py:106, tests/test_validate.py:66).
- Alias resolution maps `nested-synesthetic-asset` to the canonical schema before validation (mcp/validate.py:17, tests/test_validate.py:27).
- Errors are normalized to RFC6901 pointers and sorted deterministically (mcp/validate.py:153, tests/test_validate.py:46).
- Oversized payloads produce `payload_too_large` with `reason=validation_failed` (mcp/validate.py:114, tests/test_validate.py:56).

## Optional batching (if present) (table: Shape → Cap enforcement → Evidence)
| Shape | Cap enforcement | Evidence |
| - | - | - |
| validate_many | Missing (optional) | docs/mcp_spec.md:94; mcp/stdio_main.py:13 |

## Logging hygiene (bullets: stdout frames only; stderr logs/diagnostics; deterministic timestamps)
- RPC responses write directly to stdout without logging noise (mcp/stdio_main.py:59).
- Server logs, including readiness and errors, stay on stderr via the logging subsystem (mcp/__main__.py:88, mcp/__main__.py:170).
- Ready file timestamps are ISO-8601 UTC strings (mcp/__main__.py:59, tests/test_stdio.py:91).

## Container & health (table: Aspect → Present/Missing/Divergent → Evidence)
| Aspect | Status | Evidence |
| - | - | - |
| Ready-file healthcheck in Compose | Present | docker-compose.yml:17 |
| Environment passthrough in Compose | Present | docker-compose.yml:12 |
| Container user hardening | Missing | Dockerfile:1 |
| Transport mode logging in container entrypoint | Present | mcp/__main__.py:88 |

## Schema discovery & validation (table: Source → Mechanism → Evidence)
| Source | Mechanism | Evidence |
| - | - | - |
| Environment overrides | Present | mcp/core.py:12; tests/test_env_discovery.py:29 |
| Submodule fallback | Present | mcp/core.py:18; tests/test_submodule_integration.py:23 |
| Local schema registry (`referencing`) | Present | mcp/validate.py:52; mcp/validate.py:99 |
| Path traversal guard | Divergent | mcp/core.py:58; mcp/core.py:108 |
| Backend gating by `SYN_BACKEND_URL` | Present | mcp/backend.py:20; tests/test_backend.py:21 |

## Test coverage (table: Feature → Tested? → Evidence)
| Feature | Tested? | Evidence |
| - | - | - |
| STDIO framing & ready file | Yes | tests/test_stdio.py:29; tests/test_stdio.py:82 |
| Signal handling & shutdown | Yes | tests/test_entrypoint.py:55 |
| Validation contract & ordering | Yes | tests/test_validate.py:46 |
| Payload guards | Yes | tests/test_stdio.py:184; tests/test_backend.py:65 |
| Backend populate paths | Yes | tests/test_backend.py:28 |
| Schema discovery | Yes | tests/test_env_discovery.py:29; tests/test_submodule_integration.py:23 |
| Socket transport behaviors | No | mcp/__main__.py:35 |
| Path traversal rejection | No | mcp/core.py:58 |

## Dependencies & runtime (table: Package → Used in → Required/Optional)
| Package | Used in | Required/Optional | Evidence |
| - | - | - | - |
| jsonschema | Draft 2020-12 validation | Required | requirements.txt:1; mcp/validate.py:8 |
| httpx | Backend populate client | Required (backend) | requirements.txt:2; mcp/backend.py:5 |
| pytest | Test runner | Required (tests) | requirements.txt:3; tests/test_stdio.py:12 |
| referencing | Local schema registry | Optional | mcp/validate.py:9 |

## Environment variables (bullets: name, default, behavior when missing/invalid)
- `MCP_ENDPOINT`: defaults to `stdio`; any other value raises setup failure (mcp/__main__.py:35).
- `MCP_READY_FILE`: defaults to `/tmp/mcp.ready`; blank disables file creation; file is removed on shutdown (mcp/__main__.py:45, mcp/__main__.py:105).
- `SYN_SCHEMAS_DIR`: must point to an existing directory or startup fails (mcp/__main__.py:22, tests/test_entrypoint.py:78).
- `SYN_EXAMPLES_DIR`: overrides example discovery root when set (mcp/core.py:25, tests/test_env_discovery.py:29).
- `SYN_BACKEND_URL`: gates backend population; unset returns `unsupported` (mcp/backend.py:20, tests/test_backend.py:21).
- `SYN_BACKEND_ASSETS_PATH`: normalized to start with `/` before POST (mcp/backend.py:24, tests/test_backend.py:46).
- `MCP_SOCKET_PATH` / `MCP_SOCKET_MODE`: defined in the spec but unused because socket mode is not implemented (docs/mcp_spec.md:67, mcp/__main__.py:35).

## Documentation accuracy (bullets: README vs. docs/mcp_spec.md)
- README correctly advertises STDIO-only transport and the 1 MiB guard consistent with the spec (README.md:24, docs/mcp_spec.md:43).
- README instructs `./serve.sh`, but the repository only ships `up.sh`; docs and tooling need to agree (README.md:43, up.sh:1).
- README environment table matches the implemented discovery order (README.md:79, mcp/core.py:12).

## Detected divergences
- Schema/example accessors allow `..` traversal because paths are blindly joined before reading (mcp/core.py:58; mcp/core.py:108; mcp/validate.py:47).
- The optional socket transport is absent; the entrypoint rejects anything except STDIO (docs/mcp_spec.md:67; mcp/__main__.py:35).
- Container image runs as root; the spec recommends non-root execution for security hardening (Dockerfile:1; docs/mcp_spec.md:111).

## Recommendations
- Sanitize request-provided paths and schema names by resolving and verifying they stay within the configured roots before reading (mcp/core.py:58; mcp/core.py:108; mcp/validate.py:47).
- Introduce a positive test invocation for the `validate` alias to guarantee backward compatibility (mcp/stdio_main.py:22; tests/test_stdio.py:29).
- Decide on socket support: either implement the UDS transport per spec or clearly document its omission (docs/mcp_spec.md:67; mcp/__main__.py:35).
- Update the README (or add the missing script) so the documented serve workflow matches the checked-in tooling (README.md:43; up.sh:1).
- Add a non-root `USER` directive to the Dockerfile to align with the security guidance (Dockerfile:1; docs/mcp_spec.md:111).
