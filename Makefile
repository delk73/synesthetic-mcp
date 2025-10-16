SHELL := /bin/bash

.PHONY: update-submodule update-submodule-pin

# Update schemas submodule and validate integration
update-submodule:
	@set -euo pipefail; \
	echo "🔄 Updating synesthetic-schemas submodule..."; \
	if [ ! -d libs/synesthetic-schemas/.git ]; then \
		echo "Initializing submodule..."; \
		git submodule update --init --recursive; \
	else \
		git submodule update --recursive --remote; \
	fi; \
	echo "📦 Submodule now at:"; \
	git -C libs/synesthetic-schemas rev-parse HEAD; \
	\
	echo "🧩 Running preflight in submodule..."; \
	$(MAKE) -C libs/synesthetic-schemas preflight-fix; \
	\
	echo "🧪 Running MCP test suite..."; \
	pytest -q --maxfail=1 --disable-warnings; \
	echo "✅ Submodule update + MCP tests complete."

# Pin submodule to a specific commit
update-submodule-pin:
	@set -euo pipefail; \
	if [ -z "$${COMMIT:-}" ]; then \
		echo "Usage: make update-submodule-pin COMMIT=<hash>"; exit 2; \
	fi; \
	git -C libs/synesthetic-schemas fetch origin; \
	git -C libs/synesthetic-schemas checkout "$${COMMIT}"; \
	git add libs/synesthetic-schemas; \
	git commit -m "chore: bump synesthetic-schemas to $${COMMIT}" || true; \
	git push; \
	$(MAKE) update-submodule
