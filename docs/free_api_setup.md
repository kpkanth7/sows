# Free API Setup Guide for Tech-Intel v2

The core principle of Tech-Intel v2 is **Zero Cost**. To achieve this, we use the free tiers of several powerful APIs. Follow these steps to obtain your keys.

## 1. Supabase (Database)
- **URL**: [https://supabase.com/](https://supabase.com/)
- **Cost**: Free (Hobby Tier)
- **Limits**: 500MB DB size, 5GB bandwidth/month
- **Steps**:
  1. Sign in with GitHub
  2. Create a new project (name it "tech-intel")
  3. Wait for the database to provision
  4. Go to **Project Settings -> API**
  5. Copy the **Project URL**, **anon public key**, and **service_role secret key**

## 2. Finnhub (Stock Data)
- **URL**: [https://finnhub.io/](https://finnhub.io/)
- **Cost**: Free
- **Limits**: 60 API calls per minute
- **Steps**:
  1. Click "Get Free API Key"
  2. Register an account
  3. Your API key will be immediately available on your dashboard

## 3. Google AI Studio (Gemini 1.5 Flash)
- **URL**: [https://aistudio.google.com/](https://aistudio.google.com/)
- **Cost**: Free (Free Tier)
- **Limits**: 15 RPM (Requests Per Minute), 1 million tokens per day
- **Steps**:
  1. Sign in with your Google account
  2. Click "Get API key" in the left sidebar
  3. Click "Create API key" (in a new or existing Google Cloud project)
  4. Copy the key

## 4. TheNewsAPI (Tech News)
- **URL**: [https://thenewsapi.com/](https://thenewsapi.com/)
- **Cost**: Free (Basic Plan)
- **Limits**: 100 requests per day
- **Steps**:
  1. Click "Sign Up"
  2. Register and verify your email
  3. Your API token is on the main dashboard

## 5. GitHub Personal Access Token
- **URL**: [https://github.com/settings/tokens](https://github.com/settings/tokens)
- **Cost**: Free
- **Limits**: 5,000 requests per hour
- **Steps**:
  1. Go to GitHub Settings -> Developer settings -> Personal access tokens -> Tokens (classic)
  2. Click "Generate new token (classic)"
  3. Select the `public_repo` (or just `repo:read`) scope
  4. Generate and copy the token (starts with `ghp_`)

## 6. YouTube Data API v3 (Influencers)
- **URL**: [https://console.cloud.google.com/](https://console.cloud.google.com/)
- **Cost**: Free
- **Limits**: 10,000 quota units per day
- **Steps**:
  1. Create a new Google Cloud Project
  2. Go to "APIs & Services" -> "Library"
  3. Search for "YouTube Data API v3" and click "Enable"
  4. Go to "Credentials" -> "Create Credentials" -> "API key"
  5. Copy the key

## 7. Reddit API (Community Signals)
- **URL**: [https://www.reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
- **Cost**: Free (for non-commercial, under 100 req/min)
- **Limits**: 100 requests per minute
- **Steps**:
  1. Scroll to the bottom and click "are you a developer? create an app..."
  2. Select **script** as the app type
  3. Enter any redirect uri (e.g., `http://localhost:8080`)
  4. Create app. You will get a **Client ID** (under the app name) and a **Client Secret**.

## 8. Alpha Vantage (Backup Stock Data)
- **URL**: [https://www.alphavantage.co/support/#api-key](https://www.alphavantage.co/support/#api-key)
- **Cost**: Free
- **Limits**: 25 requests per day
- **Steps**:
  1. Fill out the short form (student/developer)
  2. Get the API key instantly

## 9. Product Hunt (Optional - Startup Releases)
- **URL**: [https://www.producthunt.com/v2/oauth/applications](https://www.producthunt.com/v2/oauth/applications)
- **Steps**:
  1. Click "Add an Application"
  2. Enter a name and redirect URI (`http://localhost`)
  3. Copy the Client ID and Client Secret
