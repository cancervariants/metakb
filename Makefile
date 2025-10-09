SHELL := bash
.SHELLFLAGS := -euo pipefail -c

OUT_DIR  ?= build
APP_NAME ?= metakb
STAMP    := $(shell date +%Y%m%d-%H%M%S)
OUT      := $(OUT_DIR)/$(APP_NAME)-$(STAMP).zip

SERVER_DIR := server
ROOT_REQS  := requirements.txt
PYTHON := python3
VENV := $(SERVER_DIR)/.venv


.PHONY: ebzip clean requirements

# Make source archive for manual deployment on elasticbeanstalk
ebzip: $(OUT)
	@echo "Created $(OUT)"

$(OUT):
	@mkdir -p $(OUT_DIR)
	@echo "Zipping $(SRC_DIR) -> $@"
	@git ls-files -z | xargs -0 zip -q $(OUT)
	@echo "Size: $$(du -h $@ | cut -f1)"

clean:
	@rm -f $(OUT_DIR)/*.zip

# Update requirements.txt file used for elastic beanstalk deployment
requirements:
	@command -v uv >/dev/null || { echo "uv not found -- it's required for this step"; exit 1; }
	cd $(SERVER_DIR) && uv sync --extra deploy --upgrade
	@tmp=$$(mktemp); dest="$$(pwd)/$(ROOT_REQS)"; \
	cd $(SERVER_DIR) && uv pip freeze --exclude-editable > "$$tmp"; \
	mv "$$tmp" "$$dest"; \
	echo "Updated $$dest"
	uv sync --all-extras
	echo "Restored full dev environment"


# ============================================================
# TypeScript model generation (local development)
# ============================================================

typescript-models: $(VENV)/bin/activate
	@echo "Checking for json2ts..."
	@if [ ! -f node_modules/.bin/json2ts ]; then \
		echo "json2ts not found. Installing dev dependencies with pnpm..."; \
		pnpm install --workspace-root; \
	fi
	@echo "Installing Python codegen dependencies..."
	cd $(SERVER_DIR) && . .venv/bin/activate && pip install -q .[codegen]
	@echo "Generating TypeScript models..."
	PATH=node_modules/.bin:$$PATH cd scripts && . ../server/.venv/bin/activate && python generate_ts_models.py
	@echo "TypeScript models updated successfully."

$(VENV)/bin/activate:
	@echo "Creating virtual environment in $(VENV)..."
	cd $(SERVER_DIR) && python3 -m venv .venv
