# Deployment & Production Guide — Med Guardian

This file explains how to build and run the Med Guardian app locally and how to deploy it to Railway with DNS mapping for a custom domain. It also lists required environment variables and verification steps.

IMPORTANT: I cannot create or modify Railway projects or DNS records from here. These steps are written so you (or someone with access) can deploy and obtain a public Railway URL such as `https://<your-project>.up.railway.app` and map your custom domain `med-guardian.com` or `app.med-guardian.com` to it.

Contents
- Quick local build & test (PowerShell)
- One-shot build script (Linux Shell / WSL / Git Bash)
- Railway deployment (step-by-step)
- Environment variables and secrets
- Adding Redis / Mongo (Railway add-ons)
- Custom domain / DNS mapping
- Verification & smoke tests
- Troubleshooting

---

Quick local build & test (PowerShell)

Open PowerShell in the repository root and run the following commands. If you're using a virtual environment, activate it first.

1) Build frontend

```powershell
cd 'C:\Users\Dell\Desktop\med-guardian\frontend'
npm install
npm run build
```

2) Start backend (in a new PowerShell window)

```powershell
cd 'C:\Users\Dell\Desktop\med-guardian\backend'
# Activate venv if you have one
# . .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8000
```

3) Quick verify in a browser or curl

Open `http://localhost:5173` (if running Vite dev) or `http://localhost:8000` after you built frontend and serve static files via backend.

API quick checks:

```powershell
curl http://localhost:8000/health
curl "http://localhost:8000/api/trends/latest?city=Chennai&disease=flu"
curl "http://localhost:8000/api/news_trends?city=Chennai&disease=flu&limit=5"
curl http://localhost:8000/metrics
```

---

One-shot build & start (Linux / WSL / Git Bash)

The repository contains `start-prod.sh` which builds the frontend and starts the backend. Run it from the repo root in Git Bash or WSL:

```bash
bash ./start-prod.sh
```

Note: `start-prod.sh` executes `npm ci`/`npm install`, `npm run build` and then starts `uvicorn`. On Windows PowerShell you can run equivalent steps manually (see PowerShell section above).

---

Railway deployment (step-by-step)

1) Create a Railway project
- Sign in to https://railway.app
- Create a New Project -> Deploy from GitHub -> choose `rakshu-kshatriya/med-guardian` repo (main branch)

2) Railway will read `railway.json`. The repo already contains a `startCommand` (we added `bash ./start-prod.sh`). Railway will run the build and start command.

3) Set environment variables in Railway (Project -> Settings -> Variables). Minimum recommended set:

- `PORT` = 8000
- `VITE_API_URL` = https://<your-railway-host>  (after deploy set value to the Railway URL)

Optional but recommended (for full functionality):
- `NEWSAPI_KEY` = <your NewsAPI key>
- `TWITTER_BEARER_TOKEN` = <your Twitter/X bearer token>
- `REDIS_URL` = (Railway Redis add-on or external redis URL)
- `MONGO_URI` = (Railway Mongo add-on or external MongoDB connection string)
- `VITE_GOOGLE_MAPS_API_KEY` = <Google Maps JS API key>

4) Provision add-ons
- In Railway, add Redis and/or Mongo from the Add-ons marketplace if you want caching and persistence. Railway will expose connection strings which you should paste into `REDIS_URL` and `MONGO_URI` variables.

5) Deploy
- Click Deploy. After successful build, Railway will expose a URL like `https://<project-name>.up.railway.app`.

6) Finalize `VITE_API_URL`
- Edit `VITE_API_URL` in Railway Settings to match the Railway app domain (e.g., `https://<project-name>.up.railway.app`) so the frontend knows where to call the backend when served by Railway.

---

Environment variables explained

- `VITE_API_URL` — frontend base URL that points to the backend API. Example: `https://med-guardian-abc123.up.railway.app`.
- `NEWSAPI_KEY` / `TWITTER_BEARER_TOKEN` — third-party keys for live news ingestion.
- `REDIS_URL` — connection string for Redis (used for caching news and preventing rate limits).
- `MONGO_URI` — connection string for MongoDB (used to persist news and trend history).
- `VITE_GOOGLE_MAPS_API_KEY` — Google Maps JS API key to enable the Google Maps UX (fallback to Leaflet/Osm if missing).

---

Custom domain / DNS mapping (example: `med-guardian.com`)

1) Add domain in Railway
- Project -> Domains -> Add a Domain -> enter `app.med-guardian.com` (recommended subdomain) or `med-guardian.com` (apex).

2) Railway will provide DNS records to create. In your DNS provider (where you registered the domain), add the exact records Railway shows. Typical options:
- Subdomain (recommended): add a CNAME:
  - Name: `app` (or `www`) 
  - Type: `CNAME`
  - Value: Railway's provided target (copy/paste exactly) 

- Apex domain: if your DNS provider supports ANAME/ALIAS, use that pointed to Railway's target; otherwise add the A records Railway provides.

3) Wait for DNS propagation (seconds to minutes). Railway will verify the records and issue TLS certificate automatically.

Notes about `railway.app` hostname
- Railway assigns a host like `https://<project>.up.railway.app`. You will get the exact URL after first successful deploy. I cannot create `https://med-guardian.up.railway.app` from here — the hostname is assigned by Railway and depends on your project name and Railway's naming scheme. After deployment you will have a valid Railway URL that you can use or you can map your custom domain.

---

Verification & smoke tests (after deploy)

Replace `<HOST>` with your Railway hostname (example: `med-guardian-abc123.up.railway.app` or your custom domain).

```bash
curl https://<HOST>/health
curl "https://<HOST>/api/trends/latest?city=Chennai&disease=flu"
curl "https://<HOST>/api/news_trends?city=Chennai&disease=flu&limit=5"
curl https://<HOST>/metrics
```

Open the site in the browser to check:
- Home page
- Prediction page: check the 30-day badge and chart
- Trends page: check map (Google Maps if key set, else Leaflet/OSM fallback)
- Data Sources page: download CSV and verify 1000 rows

---

Troubleshooting

- Build fails during `npm ci` on Railway: check `package.json` dependency versions; ensure `node` version compatibility in Railway project settings or add an `.nvmrc` with a supported Node version.
- Map missing / tiles not loading: if `VITE_GOOGLE_MAPS_API_KEY` is set incorrectly, Google map will show messages; Leaflet fallback uses OSM tiles which are public.
- External news providers returning errors: confirm `NEWSAPI_KEY` or `TWITTER_BEARER_TOKEN` are valid and not rate-limited.
- Redis/Mongo not available: if you didn't set `REDIS_URL` or `MONGO_URI` the app will gracefully fallback to synthetic data. To enable caching/persistence, add Railway add-ons and copy credentials.

---

Request me to validate after you deploy
- After you run the deploy, paste the Railway app URL here (for example `https://med-guardian-abc123.up.railway.app`). I will:
  - verify health & metrics
  - exercise prediction and news endpoints
  - validate SSE streaming
  - provide any small fixes necessary (CORS, static path, env variable tweaks)

---

If you want, I can also add a tiny GitHub Actions workflow to auto-deploy on push to `main` using Railway CLI — tell me and I'll add it.

Good luck — paste the local build logs or the Railway URL and I'll validate and finish the final tuning.
