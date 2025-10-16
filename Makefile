SHELL := /bin/bash

.PHONY: update-submodule update-submodule-pin preflight

preflight:
	@set -euo pipefail; \
	echo "🧩 MCP Preflight Validation"; \
	VER="$$(jq -r '.schemaVersion' libs/synesthetic-schemas/version.json)"; \
	PH="https://schemas.synesthetic.dev/$$VER"; \
	CAN="https://delk73.github.io/synesthetic-schemas/schema/$$VER"; \
	echo "🔍 schemaVersion=$$VER"; \
	\
	echo "🔍 Checking submodule pin..."; \
	git -C libs/synesthetic-schemas rev-parse HEAD; \
	\
	echo "🔍 Verifying placeholder host in source schemas..."; \
	grep -q "$$PH" libs/synesthetic-schemas/jsonschema/synesthetic-asset.schema.json && echo "✅ Placeholder host found" || { echo "❌ Missing placeholder host in sources"; exit 1; }; \
	\
	echo "🔍 Running schema preflight in submodule..."; \
	$(MAKE) -C libs/synesthetic-schemas preflight-fix; \
	\
	echo "📦 Publishing schemas (placeholder → canonical)..."; \
	$(MAKE) -C libs/synesthetic-schemas publish-schemas; \
	\
	echo "🔍 Checking canonical host in published docs..."; \
	test -f "libs/synesthetic-schemas/docs/schema/$$VER/synesthetic-asset.schema.json" || { echo "❌ Missing published schema"; exit 1; }; \
	grep -q "$$CAN" libs/synesthetic-schemas/docs/schema/$$VER/synesthetic-asset.schema.json && echo "✅ Canonical host found in published docs" || { echo "❌ Canonical host missing after publish"; exit 1; }; \
	\
	echo "🧩 Validating schemas against canonical base URL..."; \
	( cd libs/synesthetic-schemas && python scripts/validate_schemas.py "$$CAN/" ); 
	\
	echo "🧠 Running MCP test suite..."; \
	pytest -q --maxfail=1 --disable-warnings; \
	echo "✅ MCP preflight complete."



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
