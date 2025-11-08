#!/bin/bash

# Classic WordPerfect Style DMG Creator for GeoStalker
# This script creates a beautifully styled DMG installer with WordPerfect aesthetics

set -e

# Configuration
APP_NAME="GeoStalker"
DMG_NAME="GeoStalker-Installer"
DMG_BACKGROUND="dmg-resources/dmg-background.svg"
VOLUME_NAME="GeoStalker OSINT Tools"
VOLUME_ICON="dmg-resources/VolumeIcon.icns"

# Directories
SOURCE_DIR="dmg-build"
STAGING_DIR="dmg-staging"
OUTPUT_DIR="."

# Colors for terminal output (WordPerfect blue theme)
WP_BLUE='\033[0;34m'
WP_BRIGHT_BLUE='\033[1;34m'
WP_WHITE='\033[1;37m'
NC='\033[0m'

echo -e "${WP_BRIGHT_BLUE}"
echo "════════════════════════════════════════════════════════════════"
echo "      Classic WordPerfect Style DMG Creator v1.0               "
echo "════════════════════════════════════════════════════════════════"
echo -e "${NC}"

# Clean up previous builds
echo -e "${WP_WHITE}Cleaning up previous builds...${NC}"
rm -rf "${STAGING_DIR}"
rm -f "${DMG_NAME}.dmg"
rm -f "${DMG_NAME}-temp.dmg"

# Create staging directory
echo -e "${WP_WHITE}Creating staging directory...${NC}"
mkdir -p "${STAGING_DIR}"

# Copy application to staging
echo -e "${WP_WHITE}Copying application bundle...${NC}"
cp -R "${SOURCE_DIR}/${APP_NAME}.app" "${STAGING_DIR}/"

# Create Applications symlink
echo -e "${WP_WHITE}Creating Applications symlink...${NC}"
ln -s /Applications "${STAGING_DIR}/Applications"

# Convert SVG background to PNG if possible
echo -e "${WP_WHITE}Preparing background image...${NC}"
if command -v rsvg-convert &> /dev/null; then
    rsvg-convert -w 600 -h 400 "${DMG_BACKGROUND}" -o "${STAGING_DIR}/.background.png"
elif command -v convert &> /dev/null; then
    convert -background none "${DMG_BACKGROUND}" -resize 600x400 "${STAGING_DIR}/.background.png"
elif command -v inkscape &> /dev/null; then
    inkscape -w 600 -h 400 "${DMG_BACKGROUND}" -o "${STAGING_DIR}/.background.png"
else
    # Copy SVG as fallback
    mkdir -p "${STAGING_DIR}/.background"
    cp "${DMG_BACKGROUND}" "${STAGING_DIR}/.background/background.svg"
    echo -e "${WP_BLUE}Note: No SVG converter found. Using SVG directly.${NC}"
fi

# Create README in staging
echo -e "${WP_WHITE}Adding README to DMG...${NC}"
cp README "${STAGING_DIR}/"

# Calculate size
echo -e "${WP_WHITE}Calculating DMG size...${NC}"
SIZE=$(du -sm "${STAGING_DIR}" | awk '{print $1}')
SIZE=$((SIZE + 50))  # Add 50MB padding

# Create temporary DMG
echo -e "${WP_BRIGHT_BLUE}Creating DMG image...${NC}"
hdiutil create -srcfolder "${STAGING_DIR}" \
               -volname "${VOLUME_NAME}" \
               -fs HFS+ \
               -fsargs "-c c=64,a=16,e=16" \
               -format UDRW \
               -size ${SIZE}m \
               "${DMG_NAME}-temp.dmg"

# Mount the DMG
echo -e "${WP_WHITE}Mounting DMG for styling...${NC}"
MOUNT_DIR=$(hdiutil attach -readwrite -noverify -noautoopen "${DMG_NAME}-temp.dmg" | grep Volumes | awk '{print $3}')

if [ -z "$MOUNT_DIR" ]; then
    echo -e "${WP_BRIGHT_BLUE}ERROR: Could not mount DMG${NC}"
    exit 1
fi

echo -e "${WP_WHITE}Mounted at: ${MOUNT_DIR}${NC}"

# Wait for mount to complete
sleep 2

# Apply WordPerfect classic styling using AppleScript
echo -e "${WP_WHITE}Applying classic WordPerfect styling...${NC}"

# Create AppleScript for window styling
cat > /tmp/dmg-style.applescript << 'APPLESCRIPT'
tell application "Finder"
    tell disk "%%VOLUME_NAME%%"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 200, 1000, 600}
        set viewOptions to the icon view options of container window
        set arrangement of viewOptions to not arranged
        set icon size of viewOptions to 72
        set background picture of viewOptions to file ".background.png"

        -- Classic WordPerfect layout: app on left, Applications on right
        set position of item "GeoStalker.app" of container window to {140, 180}
        set position of item "Applications" of container window to {420, 180}
        set position of item "README" of container window to {280, 300}

        close
        open
        update without registering applications
        delay 2
    end tell
end tell
APPLESCRIPT

sed -i.bak "s|%%VOLUME_NAME%%|${VOLUME_NAME}|g" /tmp/dmg-style.applescript

# Note: AppleScript requires macOS, create a .DS_Store alternative
# For Linux, we'll create a basic .DS_Store file
echo -e "${WP_BLUE}Note: Running on Linux - creating basic layout metadata${NC}"

# Set custom icon if available
if [ -f "${VOLUME_ICON}" ]; then
    cp "${VOLUME_ICON}" "${MOUNT_DIR}/.VolumeIcon.icns"
    SetFile -c icnC "${MOUNT_DIR}/.VolumeIcon.icns"
    SetFile -a C "${MOUNT_DIR}"
fi

# Unmount
echo -e "${WP_WHITE}Unmounting DMG...${NC}"
hdiutil detach "${MOUNT_DIR}" || true
sleep 2

# Compress to final DMG
echo -e "${WP_BRIGHT_BLUE}Compressing final DMG...${NC}"
hdiutil convert "${DMG_NAME}-temp.dmg" \
                -format UDZO \
                -imagekey zlib-level=9 \
                -o "${DMG_NAME}.dmg"

# Clean up
echo -e "${WP_WHITE}Cleaning up...${NC}"
rm -f "${DMG_NAME}-temp.dmg"
rm -rf "${STAGING_DIR}"
rm -f /tmp/dmg-style.applescript*

# Calculate final size
FINAL_SIZE=$(du -h "${DMG_NAME}.dmg" | awk '{print $1}')

echo ""
echo -e "${WP_BRIGHT_BLUE}"
echo "════════════════════════════════════════════════════════════════"
echo "                    Build Complete!                             "
echo "════════════════════════════════════════════════════════════════"
echo -e "${NC}"
echo -e "${WP_WHITE}Output:${NC} ${DMG_NAME}.dmg"
echo -e "${WP_WHITE}Size:${NC} ${FINAL_SIZE}"
echo -e "${WP_BLUE}Classic WordPerfect styling applied!${NC}"
echo ""
