"""
capture_client.py

Runs on an employee's machine. Takes periodic screenshots of their screen
(where they're already in their Google Meet) and uploads them to the
central dashboard server.

Install:
    pip install mss requests pillow

Run:
    python capture_client.py --name Abhi --server http://SERVER_IP:5000

--name    : label shown on the dashboard for this person
--server  : the dashboard server's address (see dashboard_server.py)
--interval: seconds between screenshots (default 2)

Note: this captures the whole screen by default. If you only want the
Meet window, crop the image before sending (see CROP section below).
"""

import argparse
import io
import time

import requests
from mss import mss
from PIL import Image


def capture_and_send(name: str, server_url: str, interval: float):
    with mss() as sct:
        monitor = sct.monitors[1]  # primary monitor; use [0] for all monitors combined

        print(f"Capturing screen for '{name}', sending to {server_url} every {interval}s")
        print("Press Ctrl+C to stop.")

        while True:
            try:
                shot = sct.grab(monitor)
                img = Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")

                # --- OPTIONAL CROP: uncomment and adjust to capture only a
                # specific region (e.g. just the Meet window area) instead
                # of the whole screen:
                # img = img.crop((left, top, right, bottom))

                img.thumbnail((960, 540))  # downscale before upload to save bandwidth

                buf = io.BytesIO()
                img.save(buf, format="JPEG", quality=60)
                buf.seek(0)

                requests.post(
                    f"{server_url}/upload",
                    files={"image": (f"{name}.jpg", buf, "image/jpeg")},
                    data={"name": name},
                    timeout=5,
                )
            except Exception as e:
                print(f"capture/upload error: {e}")

            time.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", required=True, help="Label shown on the dashboard")
    parser.add_argument("--server", required=True, help="Dashboard server URL, e.g. http://192.168.1.10:5000")
    parser.add_argument("--interval", type=float, default=2.0, help="Seconds between screenshots")
    args = parser.parse_args()

    capture_and_send(args.name, args.server, args.interval)
