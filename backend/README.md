# Portfolio backend — Flask + PostgreSQL (Neon) + Render

A Flask API that powers two things on the portfolio site:
- a contact form (`messages` table)
- a page-visit counter (`hits` table)

Data is stored in PostgreSQL hosted on **Neon** (free, no expiry). The app
itself runs on **Render** (free web service tier).

## 1. Create the database on Neon

1. Go to neon.tech and sign up (GitHub sign-in works).
2. Create a new project (e.g. "portfolio-db").
3. On the project dashboard, click "Connect" and copy the **pooled
   connection string** (hostname contains `-pooler`). It looks like:
   ```
   postgresql://user:password@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require&channel_binding=require
   ```
   Keep the `sslmode` and `channel_binding` parameters — Neon requires them.

## 2. Run it locally

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="<your Neon pooled connection string>"
python3 app.py
```

The API runs at `http://localhost:5000`. Open `index.html` with VS Code's
Live Server extension (serves at `http://127.0.0.1:5500`) and test the
contact form and hit counter — both write to your real Neon database, so
what you see locally is the same data your live site will show.

## 3. Deploy the app on Render

1. Push this `backend/` folder to a GitHub repo (add a `.gitignore` with
   `venv/` in it first, so your virtual environment isn't committed).
2. On render.com, click "New" -> "Web Service" and connect the repo.
3. Set Root Directory to `backend` (if it's a subfolder).
4. Build Command: `pip install -r requirements.txt`
5. Start Command: `gunicorn app:app`
6. Choose the Free instance type and click "Create Web Service".
7. Once created, go to the service's Environment tab and add:
   - Key: `DATABASE_URL`
   - Value: the same Neon pooled connection string from step 1.
8. Render redeploys automatically. Visit
   `https://your-app-name.onrender.com/api/health` to confirm it's up.

## 4. Connect the frontend

In `index.html`, both places that reference `API_BASE` currently point to
`http://localhost:5000` for local testing:

```js
var API_BASE = "http://localhost:5000";
```

Once your Render service is live, change both occurrences to:

```js
var API_BASE = "https://your-app-name.onrender.com";
```

Also make sure the `CORS` origins list in `app.py` includes your actual
GitHub Pages URL (e.g. `https://bogertcoding.github.io`), then commit and
push - Render redeploys automatically on every push.

## Endpoints

- `POST /api/contact` - accepts `{ "name", "email", "message" }`, stores it, returns a confirmation.
- `GET /api/messages` - lists all received contact messages.
- `GET /api/hits` - increments the visit counter and returns the new total.
- `GET /api/health` - simple check that the server is up.

## Important notes

- **Protect `/api/messages`**: anyone who knows the URL can currently view
  submitted messages. For real use, add an API-key check on this route
  before making the site public.
- **Never commit `DATABASE_URL`** or any credentials into `app.py` or git -
  always set it as an environment variable, both locally and on Render.
- **Render free tier cold starts**: after 15 minutes of inactivity, the
  first request can take 30-60 seconds while the service wakes up. Normal
  behavior on the free tier, not a bug.
- **`/api/hits` counts page loads, not unique visitors** - refreshing the
  page increases the count each time. Deduplicating by visitor would
  require tracking sessions or cookies, which this simple version doesn't do.
