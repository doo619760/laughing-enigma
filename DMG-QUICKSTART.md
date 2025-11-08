# 🎨 Classic WordPerfect Style Mac DMG - Quick Start

> Bringing the iconic blue aesthetic of 1990s WordPerfect to modern macOS installers

## ✨ What You Get

A professionally styled DMG installer featuring:

- **Authentic WordPerfect blue gradient** (#0066CC → #003377)
- **Classic typography** using Courier and professional fonts
- **Retro UI launcher** with WordPerfect-themed terminal interface
- **Professional layout** with drag-to-Applications installation
- **Period-accurate styling** reminiscent of classic software

## 📦 Package Structure

```
laughing-enigma/
├── dmg-build/
│   └── GeoStalker.app/          # Complete macOS application
│       ├── Contents/
│       │   ├── Info.plist        # App metadata
│       │   ├── MacOS/
│       │   │   └── geostalker    # WP-styled launcher
│       │   └── Resources/
│       │       ├── fbstalker1.py
│       │       ├── geostalker.py
│       │       └── README
│
├── dmg-resources/
│   ├── dmg-background.svg        # Classic WP background
│   ├── dmg-background-enhanced.svg
│   └── PREVIEW.html              # Visual preview
│
├── build-dmg-simple.sh           # Simple builder (uses create-dmg)
├── create-dmg.sh                 # Advanced builder (uses hdiutil)
├── Makefile                      # Build automation
└── DMG-README.md                 # Detailed documentation
```

## 🚀 Quick Build (macOS only)

### Option 1: Using Makefile

```bash
make dmg
```

### Option 2: Using build script

```bash
./build-dmg-simple.sh
```

### Option 3: Manual build

```bash
# Install create-dmg if needed
brew install create-dmg

# Build
create-dmg \
  --volname "GeoStalker OSINT Tools" \
  --background "dmg-resources/dmg-background-enhanced.svg" \
  --window-size 600 400 \
  --icon-size 72 \
  --icon "GeoStalker.app" 140 180 \
  --app-drop-link 420 180 \
  "GeoStalker-Installer.dmg" \
  "dmg-build/"
```

## 🎯 What Makes It WordPerfect Style?

### Color Palette
- **Primary**: #0055AA (Classic WP blue)
- **Dark**: #003377 (Deep blue shadow)
- **Light**: #0066CC (Highlight blue)
- **Accent**: #004499 (Medium blue)

### Typography
- **Monospace**: Courier New (classic WP text)
- **Sans-serif**: Arial/Helvetica (UI elements)
- **Letter spacing**: 2-3px for titles (WP style)

### Visual Elements
- Blue gradient backgrounds
- Subtle grid patterns
- Box-drawing characters in terminal
- Embossed text effects
- Professional panel layouts

## 📸 Preview

Open `dmg-resources/PREVIEW.html` in your browser to see what the DMG will look like!

## 🛠️ Requirements

**To build the DMG:**
- macOS 10.10 or later
- `hdiutil` (built into macOS) OR
- `create-dmg` (`brew install create-dmg`)
- Optional: `rsvg-convert` for SVG conversion

**To run the app:**
- macOS 10.10 or later
- Python 2.7
- Dependencies in README

## 📋 Features

### Application Launcher
The custom launcher provides:
- **Classic blue terminal UI** matching WordPerfect theme
- **Tool selection menu** for GeoStalker and FBStalker
- **Dependency checking** with friendly error messages
- **README viewer** built-in

### DMG Installer
- **Drag & drop** installation
- **Professional background** with instructions
- **Optimized layout** (600x400 window)
- **Compressed UDZO** format for small size

## 🎨 Customization

### Change Colors
Edit `dmg-resources/dmg-background-enhanced.svg`:

```xml
<stop offset="0%" style="stop-color:#0066CC;stop-opacity:1" />
<stop offset="50%" style="stop-color:#0055AA;stop-opacity:1" />
<stop offset="100%" style="stop-color:#003377;stop-opacity:1" />
```

### Modify Layout
Edit build scripts to adjust icon positions:
- App icon: `140, 180`
- Applications link: `420, 180`
- README: `280, 300`

### Update Text
Edit the SVG file `<text>` elements to change:
- Title
- Instructions
- Branding

## 📖 Documentation

- **DMG-README.md** - Complete documentation
- **PREVIEW.html** - Visual preview and features
- **Makefile** - Build commands and targets

## 🔧 Build Commands

```bash
make help      # Show all available commands
make check     # Verify build environment
make prepare   # Prepare application bundle
make dmg       # Build the DMG
make clean     # Clean build artifacts
```

## 🎓 Tips

1. **Test on macOS first** - DMG creation requires macOS
2. **Use enhanced background** - dmg-background-enhanced.svg has better styling
3. **Preview before building** - Open PREVIEW.html to see design
4. **Check dependencies** - Run `make check` to verify environment

## 📦 Distribution

The final `GeoStalker-Installer.dmg` will be:
- Compressed and optimized
- Ready for distribution
- Code-signable (add certificates)
- Notarization-ready (for macOS 10.15+)

## 🌟 Credits

**Classic WordPerfect Styling**
Inspired by the iconic blue interface of WordPerfect 5.1-6.0
Bringing professional 1990s aesthetics to modern installers

**GeoStalker Tools**
OSINT tools for security research
Follow @osintstalker for updates

---

**Happy Building! Enjoy your classic WordPerfect-styled DMG! 💙**

For detailed information, see [DMG-README.md](DMG-README.md)
