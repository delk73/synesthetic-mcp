---
version: v0.1.0
lastReviewed: 2025-10-01
owner: mcp-core
---

# Development Process — MCP

## Canon Flow
All work follows a strict **Spec → Audit → Patch** cycle.

1. **Spec**  
   * Define features and exit criteria in `docs/mcp_spec.md`.  
   * Keep rolling history (current + previous).  
   * Cull older details when spec grows too long, link to prior tags instead.

2. **Audit**  
   * Run audit prompts pinned to the current spec version.  
   * Write results to `meta/output/mcp_state.md`.  
   * Update `AGENTS.md` snapshot to reflect current agent responsibilities.  
   * Audit must mark features as **Present / Missing / Divergent** with file/line evidence.  

3. **Patch**  
   * Implement changes only in scoped files.  
   * Keep patches atomic and reproducible.  
   * Rerun audit until all spec features are marked **Present**.  

---

## Versioning
* MCP spec increments (e.g., `v0.2.7`) drive audits and patches.  
* Never patch without a pinned spec.  
* Exit criteria are binding; unimplemented items = **Missing** until patched.  

---

## Logging & Outputs
* All outputs live under `meta/output/`.  
* `mcp_state.md` is always overwritten, non-empty.  
* `AGENTS.md` stays aligned with actual responsibilities and audit state.  

---

## Daily Development Flow
* **Morning:** confirm spec version and review last audit.  
* **Midday:** implement patches scoped to spec gaps.  
* **Afternoon:** rerun audit, confirm exit criteria.  
* **End of day:** commit spec + audit + process updates.  

---

## Notes
* Keep process lightweight and deterministic.  
* MCP repo is schema-first and validation-centric — no new transports or features without spec update.  
* Spec is the source of truth; process enforces alignment.