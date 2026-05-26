# Tech-Intel v2 — Complete API Key Setup Guide

To power the Tech-Intel v2 platform with live data at zero cost, you will need to register for several free-tier APIs. 

Here is the master list of all required keys and exactly how to get them step-by-step.

---

## 🏗️ 1. Database & Core Platform (Supabase)
Supabase acts as our database and backend. It is completely free for Hobby projects.

**Keys Needed:**
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY` (Used by the Frontend)
- `SUPABASE_SERVICE_ROLE_KEY` (Used by the Backend Scripts - KEEP SECRET!)

**How to get them:**
1. Go to [Supabase](https://supabase.com/) and click **Start your project**.
2. Sign in with GitHub.
3. Click **New Project**, name it `tech-intel`, and set a strong database password. Wait ~2 minutes for it to provision.
4. On your project dashboard, click the **Settings** gear icon (bottom left) -> **API**.
5. Copy the **Project URL**, the **anon public** key, and the **service_role secret** key.

---

## 🧠 2. AI & Consensus Engine (Google Gemini)
Used for determining hype scores, generating investor briefs, and resolving contradictory news.

**Keys Needed:**
- `GEMINI_API_KEY`

**How to get it:**
1. Go to [Google AI Studio](https://aistudio.google.com/).
2. Sign in with your Google Account.
3. In the left sidebar, click **Get API key**.
4. Click **Create API key** (you can create a new Google Cloud project or use an existing one).
5. Copy the generated key.

---

## 📈 3. Stock Market & IPO Data (Finnhub & Alpha Vantage)
Used to track live stock prices for tier 1/2/3 companies.

### Finnhub (Primary)
**Keys Needed:**
- `FINNHUB_API_KEY`

**How to get it:**
1. Go to [Finnhub.io](https://finnhub.io/).
2. Click **Get Free API Key**.
3. Register an account with your email.
4. Your API key will be immediately visible on your dashboard.

### Alpha Vantage (Fallback)
**Keys Needed:**
- `ALPHA_VANTAGE_KEY`

**How to get it:**
1. Go to [Alpha Vantage API Key Claim](https://www.alphavantage.co/support/#api-key).
2. Fill out the short form.
3. Your key is generated instantly on the screen.

---

## 📰 4. Tech News & Headlines (TheNewsAPI)
Used alongside free RSS feeds and HackerNews to pull the latest technology articles.

**Keys Needed:**
- `THENEWSAPI_KEY`

**How to get it:**
1. Go to [TheNewsAPI](https://thenewsapi.com/).
2. Click **Sign Up** and create an account.
3. Verify your email address.
4. Log in, and your API token will be on the main dashboard page.

---

## 💻 5. Open Source & Repositories (GitHub)
Used to track when companies release new open-source software and see what is trending.

**Keys Needed:**
- `GITHUB_TOKEN` (or `GH_PAT`)

**How to get it:**
1. Go to your GitHub account settings -> **Developer settings** -> **Personal access tokens** -> **Tokens (classic)** (or click [here](https://github.com/settings/tokens)).
2. Click **Generate new token (classic)**.
3. Give it a name like `Tech-Intel Scraper`.
4. Check the box for `public_repo` (or just `repo:read`).
5. Scroll down, click Generate, and **copy the token immediately** (it starts with `ghp_`).

---

## 🎥 6. Influencer Tracking (YouTube Data API v3)
Used to monitor tech YouTubers (MKBHD, Fireship, etc.) for new videos.

**Keys Needed:**
- `YOUTUBE_API_KEY`

**How to get it:**
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (e.g., `tech-intel-youtube`).
3. Using the search bar at the top, search for **YouTube Data API v3** and click **Enable**.
4. Go to **APIs & Services** -> **Credentials**.
5. Click **Create Credentials** -> **API Key**.
6. Copy the generated key.

---

## 🗣️ 7. Community Signals (Reddit)
Used to track sentiment on r/technology, r/MachineLearning, etc.

**Keys Needed:**
- None! Reddit's API no longer issues credentials to individual developers. We use the public unauthenticated `.json` endpoints.
- `REDDIT_USER_AGENT` (Required: a string identifying your scraper so you don't get blocked)

**How to get it:**
1. No account or API keys required.
2. For `REDDIT_USER_AGENT`, just use a descriptive string like: `python:tech-intel-scraper:v2.0 (by /u/YourRedditUsername)`.

---

## 🚀 8. Startup Launches (Product Hunt) - Optional
Used to track new companies launching products.

**Keys Needed:**
- `PRODUCTHUNT_CLIENT_ID`
- `PRODUCTHUNT_CLIENT_SECRET`

**How to get it:**
1. Go to [Product Hunt API Dashboard](https://www.producthunt.com/v2/oauth/applications).
2. Click **Add an Application**.
3. Name it `TechIntel` and set Redirect URI to `http://localhost`.
4. Copy the Client ID and Client Secret.

---

# 🛠️ Where to Put These Keys Once You Have Them

Once you have gathered these keys, you need to place them in **two** locations to run the project.

### 1. For Local Development (Running on your Mac)
Create two `.env` files in your project:

**File 1: `frontend/.env.local`**
```text
VITE_SUPABASE_URL="https://your-project.supabase.co"
VITE_SUPABASE_ANON_KEY="your-anon-public-key"
```

**File 2: `.env` (in the root directory for Python scripts)**
```text
SUPABASE_URL="https://your-project.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="your-service-role-key"
GEMINI_API_KEY="your-gemini-key"
FINNHUB_API_KEY="your-finnhub-key"
ALPHA_VANTAGE_KEY="your-alpha-vantage-key"
THENEWSAPI_KEY="your-thenewsapi-key"
GITHUB_TOKEN="ghp_your-token"
YOUTUBE_API_KEY="your-youtube-key"
REDDIT_USER_AGENT="python:tech-intel-scraper:v2.0 (by /u/YourUsername)"
PRODUCTHUNT_CLIENT_ID="your-ph-client-id"
PRODUCTHUNT_CLIENT_SECRET="your-ph-client-secret"
```

### 2. For Production (GitHub Actions & Vercel)
- **Vercel**: Go to your Vercel project settings -> Environment Variables. Add `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`.
- **GitHub**: Go to your GitHub repository -> Settings -> Secrets and variables -> Actions -> **New repository secret**. Add every key from the Python list above so the automated background scripts can use them.
