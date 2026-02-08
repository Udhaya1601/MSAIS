from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
import jwt
import datetime
import os

app = Flask(__name__)
CORS(app)

# ==========================
# CONFIG
# ==========================
app.config["SECRET_KEY"] = "msais_secret_key_123"

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",      # <-- your MySQL password if any
    "database": "msais_db",
    "auth_plugin": "mysql_native_password"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

# ==========================
# PATH TO FRONTEND FOLDER
# ==========================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

print("Frontend dir:", FRONTEND_DIR)
if os.path.exists(FRONTEND_DIR):
    print("Frontend files:", os.listdir(FRONTEND_DIR))
else:
    print("⚠️ Frontend folder not found!")

# ==========================
# HOME
# ==========================
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "MSAIS Backend Running"})

# ==========================
# REGISTER USER
# ==========================
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(force=True, silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    password = (data.get("password") or "").strip()

    if not name or not email or not password:
        return jsonify({"status": "error", "message": "Missing fields"}), 400

    username = email.split("@")[0]

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id FROM users WHERE email=%s OR username=%s", (email, username))
        if cur.fetchone():
            return jsonify({"status": "exists"})

        cur.execute(
            "INSERT INTO users (name, email, username, password, role) VALUES (%s,%s,%s,%s,%s)",
            (name, email, username, password, "user")
        )
        conn.commit()
        return jsonify({"status": "registered"})
    finally:
        cur.close()
        conn.close()

# ==========================
# LOGIN
# ==========================
@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(force=True, silent=True) or {}
    identifier = (data.get("username") or "").strip()  # username or email
    password = (data.get("password") or "").strip()

    if not identifier or not password:
        return jsonify({"status": "failed", "message": "Missing credentials"}), 400

    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute(
            "SELECT * FROM users WHERE (username=%s OR email=%s) AND password=%s",
            (identifier, identifier, password)
        )
        user = cur.fetchone()

        if not user:
            return jsonify({"status": "failed"})

        token = jwt.encode(
            {
                "id": user["id"],
                "role": user["role"],
                "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=5),
            },
            app.config["SECRET_KEY"],
            algorithm="HS256",
        )

        return jsonify({
            "status": "success",
            "token": token,
            "name": user["name"],
            "role": user["role"],
        })
    finally:
        cur.close()
        conn.close()

# ==========================
# ADMIN: LIST USERS (Database module)
# ==========================
@app.route("/admin/users", methods=["GET"])
def admin_list_users():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        cur.execute("SELECT id, name, email, username, role FROM users ORDER BY id DESC")
        users = cur.fetchall()
        return jsonify({"status": "success", "users": users})
    finally:
        cur.close()
        conn.close()

# ==========================
# SERVE FRONTEND FILES
# ==========================
@app.route("/login.html")
def serve_login():
    return send_from_directory(FRONTEND_DIR, "login.html")

@app.route("/admin_dashboard.html")
def serve_admin_dashboard():
    return send_from_directory(FRONTEND_DIR, "admin_dashboard.html")

@app.route("/user_dashboard.html")
def serve_user_dashboard():
    return send_from_directory(FRONTEND_DIR, "user_dashboard.html")

# ==========================
# CATCH-ALL: SERVE ANY FRONTEND FILE
# ==========================
@app.route("/<path:filename>")
def serve_any_frontend_file(filename):
    return send_from_directory(FRONTEND_DIR, filename)

# ==========================
# RUN
# ==========================
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
