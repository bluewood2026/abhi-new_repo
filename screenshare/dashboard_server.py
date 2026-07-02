"""
dashboard_server.py

Central server that receives screenshots from each employee's
capture_client.py and displays them all in a live-updating grid,
like the existing management dashboard.

Install:
    pip install flask

Run:
    python dashboard_server.py

Then open http://SERVER_IP:5000 in a browser (this is the manager's view).
Run this on a machine that stays on and is reachable on your network by
everyone running capture_client.py (e.g. the manager's own computer, or a
small always-on office server).
"""

import os
import time

from flask import Flask, request, send_from_directory, Response

app = Flask(__name__)

UPLOAD_DIR = "screens"
os.makedirs(UPLOAD_DIR, exist_ok=True)

last_seen = {}  # name -> timestamp of last received screenshot

STALE_AFTER_SECONDS = 10  # mark a tile "stale" if no update in this long


@app.route("/upload", methods=["POST"])
def upload():
    name = request.form.get("name", "unknown")
    file = request.files.get("image")
    if file:
        safe_name = "".join(c for c in name if c.isalnum() or c in ("-", "_")) or "unknown"
        file.save(os.path.join(UPLOAD_DIR, f"{safe_name}.jpg"))
        last_seen[safe_name] = time.time()
    return "ok"


@app.route("/screens/<name>.jpg")
def get_screen(name):
    return send_from_directory(UPLOAD_DIR, f"{name}.jpg")


@app.route("/")
def dashboard():
    tiles_html = ""
    for name in sorted(last_seen.keys()):
        age = time.time() - last_seen[name]
        if age < STALE_AFTER_SECONDS:
            status, color = "live", "#4ade80"
        else:
            status, color = f"stale ({int(age)}s ago)", "#f87171"

        tiles_html += f"""
        <div class="tile">
            <h3>{name} <span class="status" style="color:{color}">{status}</span></h3>
            <img src="/screens/{name}.jpg?t={int(time.time())}">
        </div>
        """

    if not tiles_html:
        tiles_html = "<p style='color:#888'>Waiting for capture_client.py to connect from each machine...</p>"

    html = f"""
    <html>
    <head>
        <title>Manager View - All Meetings</title>
        <meta http-equiv="refresh" content="3">
        <style>
            body {{ background: #111; color: #eee; font-family: sans-serif; margin: 0; padding: 16px; }}
            h1 {{ font-size: 18px; }}
            .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; margin-top: 16px; }}
            .tile img {{ width: 100%; border-radius: 6px; display: block; }}
            .tile h3 {{ margin: 0 0 6px 2px; font-size: 14px; font-weight: 600; }}
            .status {{ font-size: 12px; font-weight: normal; margin-left: 6px; }}
        </style>
    </head>
    <body>
        <h1>Manager View - All Meetings</h1>
        <div class="grid">{tiles_html}</div>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


if __name__ == "__main__":
    # host="0.0.0.0" makes it reachable from outside the container
    # PORT is set automatically by Render; falls back to 5000 for local testing
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
