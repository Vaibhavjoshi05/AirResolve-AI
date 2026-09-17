# Deploying AirResolve on Vercel

This guide provides step-by-step instructions to deploy AirResolve to **Vercel** with one click.

---

## 1. How Vercel Deployment Works

AirResolve is configured for Vercel using:
- **`vercel.json`**: Configures the Python serverless function builder (`@vercel/python`) for `api/index.py` and static hosting for `public/`.
- **`api/index.py`**: Python serverless endpoint hosting the deterministic policy engine, intent detector, and conversational orchestrator.
- **`public/index.html`**: Responsive, airline-branded web dashboard with live chat, passenger switcher, dynamic action chips, eligibility matrix, and step-by-step decision trace.
- **`requirements.txt`**: Pinned dependencies that Vercel automatically installs during build.

---

## 2. One-Click Deployment via Vercel Web Dashboard

### Step 1: Push your code to GitHub
Make sure your project is committed and pushed to your GitHub repository:
```bash
cd "c:\Assignment 3"
git add .
git commit -m "feat: airresolve ready for vercel deployment"
git push -u origin main
```

### Step 2: Import into Vercel
1. Go to [https://vercel.com](https://vercel.com) and log in (e.g. using your GitHub account).
2. On your Vercel dashboard, click **"Add New..."** $\rightarrow$ **"Project"**.
3. Under **"Import Git Repository"**, find and select your `airline-resolution-agent` repository.
4. Click **"Import"**.

### Step 3: Configure & Deploy
1. **Project Name**: `airresolve` (or your choice).
2. **Framework Preset**: Leave as **Other** (Vercel automatically detects `vercel.json`).
3. **Root Directory**: `./` (leave default).
4. Click **"Deploy"**.

Vercel will install the Python dependencies from `requirements.txt`, bundle `api/index.py`, serve the static dashboard from `public/`, and provide a production URL:
```
https://airresolve.vercel.app
```

---

## 3. Alternative: Deploy using Vercel CLI

If you have the Vercel CLI installed:
```bash
# Login to Vercel
vercel login

# Deploy to preview
vercel

# Deploy to production
vercel --prod
```

---

## 4. Verifying the Deployment
Once deployed, open your live Vercel URL:
- **Health Check**: `https://<YOUR_APP>.vercel.app/api/health`
- **Main Web Interface**: `https://<YOUR_APP>.vercel.app/`

You can test all 3 scenarios directly on your deployed Vercel URL!
