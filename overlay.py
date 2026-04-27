import threading
import time
import logging
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
    #header { background: #2c3e50; padding: 15px 20px; display: flex; align-items: center; justify-content: space-between; }
    #title { font-size: 16px; font-weight: bold; }
    #btn { background: #27ae60; border: none; color: white; padding: 10px 20px; font-size: 14px; border-radius: 6px; cursor: pointer; }
    #btn:hover { background: #2ecc71; }
    #btn:disabled { background: #7f8c8d; cursor: default; }
    #content { flex: 1; display: flex; align-items: center; justify-content: center; color: #7f8c8d; font-size: 16px; }
</style>
</head>
<body>
    <div id="header">
        <span id="title">GeoGuessr Helper</span>
        <button id="btn" onclick="analyze()">📍 Analyze</button>
    </div>
    <div id="content">Press Analyze to detect location</div>
    <script>
        function analyze() {
            document.getElementById('btn').disabled = true;
            document.getElementById('btn').innerText = '⏳ Analyzing...';
            pywebview.api.analyze();
        }
    </script>
</body>
</html>"""

INJECT_BUTTON_JS = """
(function() {
    var old = document.getElementById('_geo_btn');
    if (old) old.remove();
    var btn = document.createElement('button');
    btn.id = '_geo_btn';
    btn.innerText = '📍 Analyze';
    btn.style.cssText = [
        'position:fixed', 'top:15px', 'right:15px', 'z-index:2147483647',
        'background:#27ae60', 'color:white', 'border:none',
        'padding:10px 18px', 'font-size:14px', 'font-weight:bold',
        'border-radius:8px', 'cursor:pointer',
        'box-shadow:0 2px 12px rgba(0,0,0,0.4)',
        'font-family:Arial,sans-serif'
    ].join(';');
    btn.onmouseover = function() { this.style.background='#2ecc71'; };
    btn.onmouseout = function() { this.style.background='#27ae60'; };
    btn.onclick = function() {
        this.innerText = '⏳ Analyzing...';
        this.disabled = true;
        pywebview.api.analyze();
    };
    document.body.appendChild(btn);
})();
"""

RESET_BUTTON_JS = """
var b = document.getElementById('_geo_btn');
if (b) { b.disabled = false; b.innerText = '📍 Analyze'; }
"""


class GeoApi:
    def __init__(self, callback):
        self._callback = callback

    def analyze(self):
        threading.Thread(target=self._callback, daemon=True).start()


def create_window(analyze_callback):
    global _window
    import webview
    api = GeoApi(analyze_callback)
    _window = webview.create_window(
        "GeoGuessr Helper",
        html=INITIAL_HTML,
        js_api=api,
        width=520,
        height=700,
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
    maps_url = f"https://www.google.com/maps/@{result.lat},{result.lon},15z"
    _window.load_url(maps_url)

    def inject():
        time.sleep(3)
        try:
            _window.evaluate_js(INJECT_BUTTON_JS)
        except Exception as e:
            logger.error(f"Button inject error: {e}")

    threading.Thread(target=inject, daemon=True).start()


def reset_button():
    global _window
    if not _window:
        return
    try:
        _window.evaluate_js(RESET_BUTTON_JS)
    except Exception:
        pass
