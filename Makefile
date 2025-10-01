OUT_DIR  ?= build
APP_NAME ?= metakb
STAMP    := $(shell date +%Y%m%d-%H%M%S)
OUT      := $(OUT_DIR)/$(APP_NAME)-$(STAMP).zip

.PHONY: ebzip clean

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
