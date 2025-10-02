SHELL := bash
.SHELLFLAGS := -euo pipefail -c

OUT_DIR  ?= build
APP_NAME ?= metakb
STAMP    := $(shell date +%Y%m%d-%H%M%S)
OUT      := $(OUT_DIR)/$(APP_NAME)-$(STAMP).zip

SERVER_DIR := server
ROOT_REQS  := requirements.txt

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
