import threading
import logging
import os
from analyzer import GeoResult

logger = logging.getLogger(__name__)

_window = None

INITIAL_HTML = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { background: #1a1a1a; display: flex; flex-direction: column; height: 100vh; font-family: Arial, sans-serif; color: white; }
    #header { background: #2c3e50; padding: 10px 14px; display: flex; align-items: center; justify-content: space-between; flex-shrink: 0; }
    #title { font-size: 14px; font-weight: bold; }
    #coords { font-size: 10px; color: #bdc3c7; margin-top: 2px; }
    .hbtn { border: none; color: white; padding: 7px 13px; border-radius: 5px; cursor: pointer; font-size: 13px; font-weight: bold; }
    #btn { background: #27ae60; }
    #btn:hover:not(:disabled) { background: #2ecc71; }
    #btn:disabled { background: #7f8c8d; cursor: default; }
    #sbtn { background: #34495e; margin-left: 6px; }
    #sbtn:hover { background: #4a6278; }
    #content { flex: 1; display: flex; align-items: center; justify-content: center; color: #7f8c8d; font-size: 14px; }

    /* Modal */
    #modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 999; align-items: center; justify-content: center; }
    #modal.open { display: flex; }
    #modal-box { background: #2c3e50; border-radius: 8px; padding: 20px; width: 320px; }
    #modal-box h3 { margin-bottom: 16px; font-size: 15px; }
    .field { margin-bottom: 12px; }
    .field label { font-size: 11px; color: #bdc3c7; display: block; margin-bottom: 4px; }
    .field input { width: 100%; background: #1a1a1a; border: 1px solid #4a6278; color: white; padding: 7px 9px; border-radius: 4px; font-size: 13px; }
    .modal-btns { display: flex; gap: 8px; margin-top: 16px; justify-content: flex-end; }
    .modal-btns button { padding: 7px 16px; border: none; border-radius: 5px; cursor: pointer; font-size: 13px; }
    #save-btn { background: #27ae60; color: white; }
    #cancel-btn { background: #7f8c8d; color: white; }
    #save-status { font-size: 11px; color: #2ecc71; margin-top: 8px; min-height: 16px; }
</style>
</head>
<body>
<div id="header">
    <div>
        <div id="title">GeoGuessr Helper</div>
        <div id="coords">Press Analyze to start</div>
    </div>
    <div>
        <button class="hbtn" id="btn" onclick="analyzeClick()">📍 Analyze</button>
        <button class="hbtn" id="sbtn" onclick="openSettings()">⚙️</button>
    </div>
</div>
<div id="content">Click Analyze or press hotkey</div>

<div id="modal">
    <div id="modal-box">
        <h3>⚙️ Settings</h3>
        <div class="field">
            <label>Gemini API Key</label>
            <input type="password" id="api-key" placeholder="AIza..."/>
        </div>
        <div class="field">
            <label>Model</label>
            <input type="text" id="model" placeholder="gemini-2.5-flash-lite"/>
        </div>
        <div id="save-status"></div>
        <div class="modal-btns">
            <button id="cancel-btn" onclick="closeSettings()">Cancel</button>
            <button id="save-btn" onclick="saveSettings()">Save</button>
        </div>
    </div>
</div>

<script>
    function analyzeClick() {
        document.getElementById('btn').disabled = true;
        document.getElementById('btn').innerText = '⏳ Analyzing...';
        pywebview.api.analyze();
    }

    function openSettings() {
        pywebview.api.get_settings().then(function(s) {
            document.getElementById('api-key').value = s.api_key || '';
            document.getElementById('model').value = s.model || '';
            document.getElementById('save-status').innerText = '';
            document.getElementById('modal').classList.add('open');
        });
    }

    function closeSettings() {
        document.getElementById('modal').classList.remove('open');
    }

    function saveSettings() {
        var key = document.getElementById('api-key').value.trim();
        var model = document.getElementById('model').value.trim();
        pywebview.api.save_settings(key, model).then(function(ok) {
            document.getElementById('save-status').innerText = ok ? '✓ Saved. Restart to apply.' : '✗ Error saving.';
        });
    }
</script>
</body>
</html>"""

RESET_BUTTON_JS = """
document.getElementById('btn').disabled = false;
document.getElementById('btn').innerText = '📍 Analyze';
"""


class GeoApi:
    def __init__(self, callback):
        self._callback = callback

    def analyze(self):
        threading.Thread(target=self._callback, daemon=True).start()

    def get_settings(self):
        from config import GEMINI_API_KEY, MODEL
        return {"api_key": GEMINI_API_KEY or "", "model": MODEL or ""}

    def save_settings(self, api_key: str, model: str) -> bool:
        try:
            env_path = ".env"
            lines = []
            if os.path.exists(env_path):
                with open(env_path) as f:
                    lines = f.readlines()

            keys = {"GEMINI_API_KEY": api_key, "MODEL": model}
            updated = set()
            new_lines = []
            for line in lines:
                key = line.split("=")[0].strip()
                if key in keys:
                    new_lines.append(f"{key}={keys[key]}\n")
                    updated.add(key)
                else:
                    new_lines.append(line)

            for key, val in keys.items():
                if key not in updated:
                    new_lines.append(f"{key}={val}\n")

            with open(env_path, "w") as f:
                f.writelines(new_lines)
            return True
        except Exception as e:
            logger.error(f"Save settings error: {e}")
            return False


def create_window(analyze_callback):
    global _window
    import webview
    api = GeoApi(analyze_callback)
    _window = webview.create_window(
        "GeoGuessr Helper",
        html=INITIAL_HTML,
        js_api=api,
        width=420,
        height=580,
        on_top=True,
        x=20,
        y=20,
        resizable=True,
    )
    return _window


def show_result(result: GeoResult):
    global _window
    if not _window:
        return
    maps_url = f"https://maps.google.com/maps?q={result.lat},{result.lon}&z=14&output=embed"
    country = result.country.replace("'", "\\'")
    explanation = result.explanation.replace("'", "\\'").replace("\n", " ")
    js = f"""
    document.getElementById('title').innerText = '📍 {country} · {result.confidence}%';
    document.getElementById('coords').innerText = '{result.lat:.6f}, {result.lon:.6f}';
    document.getElementById('content').innerHTML = '<iframe src=\\"{maps_url}\\" style=\\"width:100%;height:100%;border:none;\\" allowfullscreen></iframe>';
    """
    try:
        _window.evaluate_js(js)
    except Exception as e:
        logger.error(f"JS error: {e}")


def reset_button():
    global _window
    if not _window:
        return
    try:
        _window.evaluate_js(RESET_BUTTON_JS)
    except Exception:
        pass


def hide():
    global _window
    if _window:
        try:
            _window.hide()
        except Exception:
            pass


def show():
    global _window
    if _window:
        try:
            _window.show()
        except Exception:
            pass
