from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import os
import re

app = Flask(__name__)

# Allow requests from your GitHub Pages site (and localhost while testing).
# Replace the github.io URL below with your actual Pages URL once deployed.
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://bogertcoding.github.io"
]}})

DB_PATH = os.path.join(os.path.dirname(__file__), "contacts.db")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    # Single-row table that just tracks a running visit count.
    conn.execute("""
        CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            count INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Seed the single row if it doesn't exist yet.
    conn.execute("INSERT OR IGNORE INTO hits (id, count) VALUES (1, 0)")
    conn.commit()
    conn.close()


@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.get_json(silent=True) or {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip()
    message = (data.get("message") or "").strip()

    # Basic server-side validation - never trust the frontend alone.
    if not name or not email or not message:
        return jsonify({"error": "All fields are required."}), 400
    if not EMAIL_RE.match(email):
        return jsonify({"error": "That email address doesn't look valid."}), 400
    if len(message) > 2000:
        return jsonify({"error": "Message is too long."}), 400

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO messages (name, email, message) VALUES (?, ?, ?)",
        (name, email, message),
    )
    conn.commit()
    conn.close()

    return jsonify({"status": "ok", "detail": "Message received. Thanks for reaching out!"}), 201


@app.route("/api/messages", methods=["GET"])
def list_messages():
    # Simple endpoint so you (the site owner) can check what came in.
    # In a real deployment you'd protect this with auth - see notes below.
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, name, email, message, created_at FROM messages ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/hits", methods=["GET"])
def hits():
    # Increments the counter every time this endpoint is called, then
    # returns the new total. The frontend calls this once per page load.
    conn = sqlite3.connect(DB_PATH)
    conn.execute("UPDATE hits SET count = count + 1 WHERE id = 1")
    conn.commit()
    row = conn.execute("SELECT count FROM hits WHERE id = 1").fetchone()
    conn.close()
    return jsonify({"hits": row[0]})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "up"})


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)
