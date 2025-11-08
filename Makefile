# Makefile for GeoStalker Classic WordPerfect Style DMG
# Classic blue aesthetic inspired by WordPerfect

.PHONY: all dmg clean help prepare check

# WordPerfect blue colors
BLUE := \033[0;34m
BRIGHT_BLUE := \033[1;34m
WHITE := \033[1;37m
NC := \033[0m

APP_NAME = GeoStalker
DMG_NAME = GeoStalker-Installer.dmg

all: help

help:
	@echo "$(BRIGHT_BLUE)"
	@echo "╔══════════════════════════════════════════════════════════════╗"
	@echo "║  Classic WordPerfect Style DMG Builder                       ║"
	@echo "╚══════════════════════════════════════════════════════════════╝"
	@echo "$(NC)"
	@echo "Available targets:"
	@echo "  $(WHITE)make prepare$(NC)  - Prepare the application bundle"
	@echo "  $(WHITE)make dmg$(NC)      - Build the DMG (requires macOS)"
	@echo "  $(WHITE)make check$(NC)    - Verify the build environment"
	@echo "  $(WHITE)make clean$(NC)    - Clean build artifacts"
	@echo "  $(WHITE)make help$(NC)     - Show this help message"
	@echo ""
	@echo "$(BLUE)Quick start:$(NC) make prepare && make dmg"
	@echo ""

check:
	@echo "$(WHITE)Checking build environment...$(NC)"
	@command -v python2.7 >/dev/null 2>&1 && echo "✓ Python 2.7 found" || echo "✗ Python 2.7 not found"
	@command -v hdiutil >/dev/null 2>&1 && echo "✓ hdiutil found (macOS)" || echo "✗ hdiutil not found (macOS required for DMG)"
	@test -d dmg-build/$(APP_NAME).app && echo "✓ Application bundle ready" || echo "✗ Application bundle not found"
	@test -f dmg-resources/dmg-background.svg && echo "✓ Background image ready" || echo "✗ Background image not found"
	@echo ""

prepare:
	@echo "$(BRIGHT_BLUE)Preparing application bundle...$(NC)"
	@mkdir -p dmg-build/$(APP_NAME).app/Contents/{MacOS,Resources}
	@mkdir -p dmg-resources
	@echo "$(WHITE)✓ Directory structure created$(NC)"
	@test -f dmg-build/$(APP_NAME).app/Contents/MacOS/geostalker && echo "$(WHITE)✓ Launcher ready$(NC)" || echo "$(BLUE)Note: Run initial setup to create launcher$(NC)"
	@test -f dmg-resources/dmg-background.svg && echo "$(WHITE)✓ Background ready$(NC)" || echo "$(BLUE)Note: Background image needs to be created$(NC)"
	@echo "$(WHITE)Application bundle prepared!$(NC)"
	@echo ""

dmg: check
	@echo "$(BRIGHT_BLUE)Building Classic WordPerfect Style DMG...$(NC)"
	@if command -v create-dmg >/dev/null 2>&1; then \
		echo "$(WHITE)Using create-dmg tool...$(NC)"; \
		./build-dmg-simple.sh; \
	else \
		echo "$(WHITE)Using hdiutil...$(NC)"; \
		./create-dmg.sh; \
	fi
	@echo "$(BRIGHT_BLUE)✓ DMG created: $(DMG_NAME)$(NC)"
	@ls -lh $(DMG_NAME)
	@echo ""

clean:
	@echo "$(WHITE)Cleaning build artifacts...$(NC)"
	@rm -rf dmg-staging
	@rm -f $(DMG_NAME)
	@rm -f GeoStalker-Installer-temp.dmg
	@echo "$(WHITE)✓ Clean complete$(NC)"

distclean: clean
	@echo "$(WHITE)Removing all generated files...$(NC)"
	@rm -rf dmg-build
	@rm -rf dmg-resources
	@echo "$(WHITE)✓ Distribution clean complete$(NC)"

.PHONY: package
package: dmg
	@echo "$(BRIGHT_BLUE)Package ready for distribution!$(NC)"
	@echo "$(WHITE)File:$(NC) $(DMG_NAME)"
	@echo "$(BLUE)Upload to your release page or distribution server$(NC)"
