#!/bin/bash

# Simple DMG builder using create-dmg tool
# Install: brew install create-dmg
# Classic WordPerfect Style

set -e

# WordPerfect blue colors for output
WP_BLUE='\033[0;34m'
WP_BRIGHT_BLUE='\033[1;34m'
WP_WHITE='\033[1;37m'
NC='\033[0m'

echo -e "${WP_BRIGHT_BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║     Classic WordPerfect Style DMG Builder v1.0               ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check for create-dmg
if ! command -v create-dmg &> /dev/null; then
    echo -e "${WP_WHITE}Installing create-dmg...${NC}"
    echo "Please run: brew install create-dmg"
    echo ""
    echo "Or download from: https://github.com/create-dmg/create-dmg"
    exit 1
fi

# Convert SVG to PNG for background
echo -e "${WP_WHITE}Converting background image...${NC}"
mkdir -p dmg-resources

# Use enhanced background if available
if [ -f "dmg-resources/dmg-background-enhanced.svg" ]; then
    SVG_SOURCE="dmg-resources/dmg-background-enhanced.svg"
else
    SVG_SOURCE="dmg-resources/dmg-background.svg"
fi

if command -v rsvg-convert &> /dev/null; then
    rsvg-convert -w 600 -h 400 "$SVG_SOURCE" \
                 -o dmg-resources/dmg-background.png
elif command -v convert &> /dev/null; then
    convert "$SVG_SOURCE" \
            -resize 600x400 \
            dmg-resources/dmg-background.png
else
    echo -e "${WP_BLUE}Warning: No SVG converter found. Will use SVG directly.${NC}"
    BACKGROUND="$SVG_SOURCE"
fi

# Set background
if [ -f "dmg-resources/dmg-background.png" ]; then
    BACKGROUND="dmg-resources/dmg-background.png"
else
    BACKGROUND="$SVG_SOURCE"
fi

# Clean previous build
rm -f GeoStalker-Installer.dmg

echo -e "${WP_BRIGHT_BLUE}Creating DMG with WordPerfect styling...${NC}"

# Create DMG using create-dmg
create-dmg \
  --volname "GeoStalker OSINT Tools" \
  --background "${BACKGROUND}" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 72 \
  --icon "GeoStalker.app" 140 180 \
  --hide-extension "GeoStalker.app" \
  --app-drop-link 420 180 \
  --eula "README" \
  --format UDZO \
  "GeoStalker-Installer.dmg" \
  "dmg-build/"

echo ""
echo -e "${WP_BRIGHT_BLUE}"
cat << "EOF"
╔══════════════════════════════════════════════════════════════╗
║                   Build Complete!                            ║
╚══════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"
echo -e "${WP_WHITE}Output:${NC} GeoStalker-Installer.dmg"
echo -e "${WP_BLUE}Classic WordPerfect blue styling applied!${NC}"
echo ""
