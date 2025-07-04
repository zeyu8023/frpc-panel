from flask import Flask, render_template, request, redirect, url_for, session
from dotenv import load_dotenv
import subprocess
import os

# 加载配置
load_dotenv("/config/.env")

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "default-key")

USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")
FRPC_INI = os.getenv("FRPC_INI", "/data/frpc.ini")
FRPC_CONTAINER = os.getenv("FRPC_CONTAINER", "frpc")

# 解析 frpc.ini
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

# 登录保护（修复跳过登录问题）
@app.before_request
def require_login():
    if request.endpoint and request.endpoint not in ("login", "static") and not session.get("logged_in"):
        return redirect(url_for("login"))

# 登录页面
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == USERNAME and request.form["password"] == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        return render_template("login.html", error="用户名或密码错误")
    return render_template("login.html")

# 登出
@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("login"))

# 首页
@app.route("/")
def index():
    proxies = parse_ini()
    return render_template("index.html", proxies=proxies)

# 添加规则
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

# 删除规则
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

# 重启 frpc 容器
@app.route("/restart")
def restart():
    try:
        subprocess.run(["docker", "restart", FRPC_CONTAINER], check=True)
    except Exception as e:
        return f"重启失败: {e}"
    return redirect(url_for("index"))

# 修改密码
@app.route("/change-password", methods=["GET", "POST"])
def change_password():
    if request.method == "POST":
        old = request.form["old_password"]
        new = request.form["new_password"]
        confirm = request.form["confirm_password"]

        if old != PASSWORD:
            return render_template("change_password.html", error="原密码错误")
        if new != confirm:
            return render_template("change_password.html", error="两次输入的新密码不一致")
        if not new.strip():
            return render_template("change_password.html", error="新密码不能为空")

        # 修改 .env 文件
        with open("/config/.env", "r") as f:
            lines = f.readlines()
        with open("/config/.env", "w") as f:
            for line in lines:
                if line.startswith("PASSWORD="):
                    f.write(f"PASSWORD={new}\n")
                else:
                    f.write(line)

        return render_template("change_password.html", success="密码已修改，请重启容器以生效")

    return render_template("change_password.html")

# 启动 Flask 应用（保持运行）
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
