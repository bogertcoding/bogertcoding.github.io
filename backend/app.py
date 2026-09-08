from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras
import os
import re

app = Flask(__name__)

# Allow requests from your GitHub Pages site (and localhost while testing).
# Replace the github.io URL below with your actual Pages URL.
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:5500",
    "http://127.0.0.1:5500",
    "https://bogertcoding.github.io"
]}})

# Set as an environment variable - never hardcode this.
# Locally: export DATABASE_URL="postgresql://...neon.tech/neondb?sslmode=require"
# On Render: set it under the Web Service's Environment tab.
DATABASE_URL = os.environ.get("DATABASE_URL")

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set. Export it locally, or set it as an "
            "environment variable on Render (pointing at your Neon database)."
        )
    return psycopg2.connect(DATABASE_URL)


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS hits (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            count INTEGER NOT NULL DEFAULT 0
        )
    """)
    # Seed the single hits row if it doesn't exist yet.
    cur.execute("INSERT INTO hits (id, count) VALUES (1, 0) ON CONFLICT (id) DO NOTHING")
    conn.commit()
    cur.close()
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

    conn = get_connection()
    cur = conn.cursor()
    # Postgres uses %s placeholders, not SQLite's ?
    cur.execute(
        "INSERT INTO messages (name, email, message) VALUES (%s, %s, %s)",
        (name, email, message),
    )
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok", "detail": "Message received. Thanks for reaching out!"}), 201


@app.route("/api/messages", methods=["GET"])
def list_messages():
    # Simple endpoint so you (the site owner) can check what came in.
    # In a real deployment you'd protect this with auth - see README.
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        "SELECT id, name, email, message, created_at FROM messages ORDER BY created_at DESC"
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # datetime objects aren't JSON-serializable as-is, so stringify them.
    result = []
    for row in rows:
        row = dict(row)
        row["created_at"] = str(row["created_at"])
        result.append(row)
    return jsonify(result)


@app.route("/api/hits", methods=["GET"])
def hits():
    # Increments the counter every time this endpoint is called, then
    # returns the new total. The frontend calls this once per page load.
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE hits SET count = count + 1 WHERE id = 1")
    cur.execute("SELECT count FROM hits WHERE id = 1")
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return jsonify({"hits": row[0]})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "up"})


# Create tables on startup. This runs both when Flask's dev server calls
# it below AND when gunicorn imports this module in production (gunicorn
# never executes the __main__ block, so without this the tables would
# never get created on Render).
try:
    init_db()
except Exception as e:
    print(f"Warning: could not initialize database on startup: {e}")


if __name__ == "__main__":
    app.run(debug=True, port=5000)
