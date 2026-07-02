import os
import time
import base64

from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

employees = {}

STALE_SECONDS = 15


@app.route("/")
def employee():
    return render_template("employee.html")


@app.route("/manager")
def manager():
    return render_template("manager.html")


@app.route("/upload", methods=["POST"])
def upload():

    data = request.get_json()

    if not data:
        return jsonify({"success": False})

    name = data.get("name")
    image = data.get("image")

    if not name:
        return jsonify({"success": False})

    employees[name] = {
        "image": image,
        "last_seen": time.time()
    }

    return jsonify({"success": True})


@app.route("/employees")
def employee_list():

    now = time.time()

    result = []

    for name, emp in employees.items():

        online = (now - emp["last_seen"]) < STALE_SECONDS

        result.append({
            "name": name,
            "image": emp["image"],
            "online": online,
            "last_seen": int(now - emp["last_seen"])
        })

    return jsonify(result)


if __name__ == "__main__":

    port = int(os.environ.get("PORT", 5000))

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )