from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import subprocess
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-key")

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
FRPC_INI = os.getenv("FRPC_INI")
FRPC_CONTAINER = os.getenv("FRPC_CONTAINER")

def parse_ini():
    proxies = []
    current = {}
    with open(FRPC_INI, "r") as f:
        for line in f:
            line = line.strip()
            if line.startswith("[") and line.endswith("]"):
                if current:
                    proxies.append(current)
                current = {"name": line[1:-1]}
            elif "=" in line:
                key, val = line.split("=", 1)
                current[key.strip()] = val.strip()
        if current:
            proxies.append(current)
    return proxies

@app.before_request
def require_login():
    if request.endpoint not in ("login", "static") and not session.get("logged_in"):
        return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="用户名或密码错误")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route("/")
def index():
    proxies = parse_ini()
    return render_template("index.html", proxies=proxies)

@app.route("/add", methods=["POST"])
def add():
    name = request.form["name"]
    local_port = request.form["local_port"]
    remote_port = request.form["remote_port"]

    with open(FRPC_INI, "a") as f:
        f.write(f"\n[{name}]\n")
        f.write("type = tcp\n")
        f.write("local_ip = 127.0.0.1\n")
        f.write(f"local_port = {local_port}\n")
        f.write(f"remote_port = {remote_port}\n")

    return redirect(url_for("index"))

@app.route("/restart")
def restart():
    subprocess.run(["docker", "restart", FRPC_CONTAINER])
    return redirect(url_for("index"))

@app.route("/delete/<name>")
def delete(name):
    lines = open(FRPC_INI).readlines()
    new_lines = []
    skip = False
    for line in lines:
        if line.strip() == f"[{name}]":
            skip = True
            continue
        if skip and line.startswith("["):
            skip = False
        if not skip:
            new_lines.append(line)
    with open(FRPC_INI, "w") as f:
        f.writelines(new_lines)
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)