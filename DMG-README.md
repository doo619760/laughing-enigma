# Classic WordPerfect Style Mac DMG

This directory contains everything needed to create a beautiful, classic WordPerfect-style DMG installer for the GeoStalker OSINT tools.

## 🎨 Design Features

The DMG features a **classic WordPerfect aesthetic** with:
- Iconic blue gradient background (#0055AA to #003377)
- Clean, professional typography using Courier monospace font
- Subtle grid pattern reminiscent of classic WP interface
- Professional installation instructions panel
- WordPerfect-style header bar with title

## 📁 Package Contents

```
dmg-build/
└── GeoStalker.app/          # Complete macOS application bundle
    ├── Contents/
    │   ├── Info.plist        # Application metadata
    │   ├── MacOS/
    │   │   └── geostalker    # Launcher script with WP-style UI
    │   └── Resources/
    │       ├── fbstalker1.py
    │       ├── geostalker.py
    │       └── README

dmg-resources/
└── dmg-background.svg        # Classic WP blue background
```

## 🛠️ Creating the DMG

### On macOS:

Run the included script:

```bash
./create-dmg.sh
```

This will create `GeoStalker-Installer.dmg` with:
- Classic WordPerfect blue gradient background
- Proper icon placement (app on left, Applications on right)
- Professional 600x400 window layout
- Compressed UDZO format

### Manual Creation (macOS):

```bash
# 1. Create staging directory
mkdir dmg-staging
cp -R dmg-build/GeoStalker.app dmg-staging/
ln -s /Applications dmg-staging/Applications

# 2. Convert background
rsvg-convert -w 600 -h 400 dmg-resources/dmg-background.svg -o dmg-staging/.background.png

# 3. Create DMG
hdiutil create -volname "GeoStalker OSINT Tools" \
               -srcfolder dmg-staging \
               -ov -format UDZO \
               GeoStalker-Installer.dmg
```

### Using create-dmg tool (recommended):

Install: `brew install create-dmg`

```bash
create-dmg \
  --volname "GeoStalker OSINT Tools" \
  --volicon "dmg-resources/VolumeIcon.icns" \
  --background "dmg-resources/dmg-background.svg" \
  --window-pos 200 120 \
  --window-size 600 400 \
  --icon-size 72 \
  --icon "GeoStalker.app" 140 180 \
  --hide-extension "GeoStalker.app" \
  --app-drop-link 420 180 \
  --no-internet-enable \
  "GeoStalker-Installer.dmg" \
  "dmg-build/"
```

## 🎯 Features of the Launcher

The application bundle includes a custom launcher that:

1. **Classic WordPerfect Terminal UI**
   - Blue color scheme matching WordPerfect theme
   - Box-drawing characters for borders
   - Professional menu system

2. **Tool Selection Menu**
   - GeoStalker (Geolocation OSINT)
   - FBStalker (Facebook OSINT)
   - README viewer

3. **Dependency Checking**
   - Validates Python 2.7 installation
   - Clear error messages in WP style

## 🎨 Color Palette

The classic WordPerfect color scheme:

- **Primary Blue**: `#0055AA`
- **Dark Blue**: `#003377`
- **Secondary Blue**: `#004499`
- **White**: `#FFFFFF`
- **Text**: `#003377`

## 📝 Customization

To modify the background design, edit `dmg-resources/dmg-background.svg`:

```svg
<!-- Change gradient colors -->
<stop offset="0%" style="stop-color:#0055AA;stop-opacity:1" />
<stop offset="100%" style="stop-color:#003377;stop-opacity:1" />

<!-- Modify title -->
<text x="300" y="28">Your Title Here</text>
```

## 🔧 Requirements

**For building DMG:**
- macOS 10.10 or later
- Xcode Command Line Tools
- Optional: `create-dmg` (brew install create-dmg)
- Optional: `rsvg-convert` for SVG conversion

**For running the application:**
- macOS 10.10 or later
- Python 2.7
- Dependencies listed in README

## 📦 Distribution

The final DMG will be:
- Compressed using UDZO format (smallest size)
- Code-signed (if certificates available)
- Notarized (for macOS 10.15+)
- Ready for distribution

## 🖼️ Preview

When users open the DMG, they'll see:
1. Classic WordPerfect blue background
2. GeoStalker.app icon on the left
3. Applications folder shortcut on the right
4. Installation instructions in a professional panel
5. WordPerfect-style header and branding

## 📄 License

OSINT Stalker Tools - For security research and authorized testing only.
Follow @osintstalker for updates.

---

**Classic WordPerfect Styling** - Bringing the professional aesthetic of the 1990s to modern macOS installers.
