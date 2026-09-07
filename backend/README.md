# Portfolio contact form backend

A small Flask API that receives contact-form submissions from the portfolio
site and stores them in a local SQLite database.

## Run it locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 app.py
```

The API will be running at `http://localhost:5000`.

Open `index.html` in your browser (e.g. with VS Code's "Live Server"
extension, which serves it at `http://127.0.0.1:5500`) and submit the
contact form — it will POST to your local Flask server.

## Endpoints

- `POST /api/contact` — accepts `{ "name", "email", "message" }`, stores it, returns a confirmation.
- `GET /api/messages` — lists all received messages (for you to check submissions).
- `GET /api/health` — simple check that the server is up.

## Deploying so it's live (not just local)

GitHub Pages can only serve static files, so this Flask app needs to run
somewhere else. Free options that work well for a small project like this:

1. **Render** (render.com) — connect your GitHub repo, choose "Web Service",
   set the start command to `gunicorn app:app`, and it builds/deploys
   automatically on every push.
2. **PythonAnywhere** — free tier, good for small Flask apps, slightly more
   manual setup via their web dashboard.
3. **Railway** — similar to Render, connect repo and deploy.

Once deployed, you'll get a URL like `https://your-app.onrender.com`.

Then, in `index.html`, update this line near the bottom of the file:

```js
var API_BASE = "http://localhost:5000";
```

to your live backend URL:

```js
var API_BASE = "https://your-app.onrender.com";
```

And update the `CORS` origins list in `app.py` to include your actual
GitHub Pages URL (e.g. `https://bogertcoding.github.io`) so the browser
allows the request.

## Important notes

- **SQLite file storage**: most free hosts (like Render's free tier) use
  ephemeral disks, meaning your `contacts.db` file may reset when the app
  restarts. Fine for learning; for something permanent, you'd move to a
  hosted database like a free PostgreSQL instance (Render and Railway both
  offer one).
- **Protect `/api/messages`**: right now anyone who knows the URL can view
  submitted messages. For a real deployment, add a simple check (like an
  API key in a header) before exposing this endpoint publicly, or remove
  it and just check the database directly.
- **Environment variables**: don't commit secrets (API keys, email
  credentials) directly into `app.py`. Use environment variables instead.
