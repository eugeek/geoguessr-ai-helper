# GeoGuessr Helper

Desktop assistant for GeoGuessr that captures screenshots, analyzes them with Google Gemini 2.5 Flash, and displays results in a floating overlay window.

## Features

- **Global Hotkey**: Press `Ctrl+Alt+G` (configurable) to analyze current GeoGuessr screenshot
- **Smart Cropping**: Automatically removes GeoGuessr UI elements (minimap, score, timer)
- **AI Analysis**: Uses Gemini 2.5 Flash to analyze road signs, bollards, vegetation, and architecture
- **Overlay Window**: Shows result in a floating window (always on top) with Google Maps marker
- **Cross-Platform**: Works on Windows, macOS, and Linux

## Quick Start (Windows)

### Download & Run
1. Download `GeoGuessr-Helper.exe` from [Releases](../../releases)
2. Create `.env` file in same folder:
   ```
   GEMINI_API_KEY=your_api_key_here
   HOTKEY=ctrl+alt+g
   ```
3. Run `GeoGuessr-Helper.exe`
4. Press `Ctrl+Alt+G` in GeoGuessr → overlay window appears with location

### Get Gemini API Key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Click "Get API Key"
3. Copy and paste into `.env`

## Manual Setup (Python)

### Requirements
- Python 3.10+
- pip

### 1. Clone/Download
```bash
git clone <repo> find-location
cd find-location
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure
```bash
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### 4. Run
```bash
python main.py
```

## How It Works

1. **Hotkey Press**: Triggers screenshot capture (in background, doesn't interrupt game)
2. **UI Cropping**: Removes GeoGuessr UI (minimap, score, timer) from screenshot
3. **Gemini Analysis**: Sends to Google Gemini 2.5 Flash with custom system prompt
4. **Result**: Overlay window appears with:
   - Country name and confidence percentage
   - Google Maps with location marker
   - Click to open full Google Maps in browser

## Troubleshooting

### "GEMINI_API_KEY not found"
- Create `.env` file in same directory as exe/script
- Format: `GEMINI_API_KEY=sk-...` (no quotes)

### Hotkey not working
**Windows**: Run as administrator for reliable hotkey detection
**macOS**: Allow Terminal in System Preferences > Security & Privacy > Accessibility
**Linux**: May need additional permissions

### Overlay window not appearing
- Check console for error messages
- Make sure Gemini API call succeeded
- Try a different hotkey in `.env`

### Wrong location detected
- Try cropping the screenshot yourself before submitting
- More context (street signs, unique buildings) helps detection
- Confidence % shows how certain the model is

## Command-Line Options

```bash
python main.py
# or with custom hotkey:
HOTKEY=cmd+shift+g python main.py
```

## Building from Source

### Prerequisites
- Python 3.10+
- pip

### Build Windows EXE
```bash
pip install pyinstaller
pyinstaller --onefile --windowed main.py
# EXE in dist/main.exe
```

### Or use GitHub Actions
Push a tag and GitHub automatically builds EXE:
```bash
git tag v1.0.0
git push origin v1.0.0
# Check Releases for EXE download
```

## Architecture

- **main.py** — Hotkey listener + async event loop
- **capture.py** — Screenshot with smart UI cropping
- **analyzer.py** — Gemini API integration
- **overlay.py** — Tkinter overlay window (always on top)
- **config.py** — Environment config loader
