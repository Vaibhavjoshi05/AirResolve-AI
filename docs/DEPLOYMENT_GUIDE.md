# Deployment Guide: Streamlit Community Cloud vs. Render

This guide helps you choose the best hosting platform for **AirResolve** and provides step-by-step instructions to deploy in under 3 minutes.

---

## 1. Quick Recommendation: Which One Should You Use?

| Platform | Best If You Want To: | Time to Deploy | Cost | Recommended? |
| :--- | :--- | :--- | :--- | :---: |
| **Streamlit Community Cloud** | Deploy the Python Streamlit app (`app.py`) with zero configuration. | **~90 seconds** | 100% Free | ⭐ **TOP CHOICE for `app.py`** |
| **Render** (`render.com`) | Deploy either `app.py` or the custom web portal (`public/index.html` + Flask API) as a cloud web service. | **~3 minutes** | Free Tier Available | 🚀 **Great for full web services** |

> **Summary Verdict**:
> - If your primary demonstration is **`app.py`**, choose **Streamlit Community Cloud**. It is natively optimized for Streamlit, sets up in 3 clicks directly from your GitHub repo, and handles web sockets and state seamlessly.
> - If you want to host the **Custom Web Dashboard & REST API (`public/index.html` + `api/index.py`)**, choose **Render** (or Vercel).

---

## 2. Option A: Deploy on Streamlit Community Cloud (Recommended for `app.py`)

### Step 1: Push Your Code to GitHub
Ensure your repository is pushed to GitHub:
```powershell
cd "c:\Assignment 3"
git add .
git commit -m "feat: ready for cloud deployment"
git push origin master
```

### Step 2: Open Streamlit Community Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io/) and click **Sign in with GitHub**.
2. Click the **"New app"** button in the top-right corner.

### Step 3: Fill in Deployment Settings
* **Repository**: Select your repository (e.g., `your-username/airline-resolution-agent` or `Assignment-3`).
* **Branch**: `master` (or `main`).
* **Main file path**: `app.py`
* **App URL** (Optional): Choose a custom URL or leave default.

### Step 4: Click "Deploy!"
Streamlit Cloud automatically reads [requirements.txt](file:///c:/Assignment%203/requirements.txt), installs dependencies, and launches your app.
* Your live URL will look like:
  ```
  https://airresolve-assignment3.streamlit.app
  ```

---

## 3. Option B: Deploy on Render (`render.com`)

### Method 1: Blueprint Deploy (Zero-Config via `render.yaml`)
Because [render.yaml](file:///c:/Assignment%203/render.yaml) is already configured in the repository:
1. Push your repository to GitHub.
2. Go to [dashboard.render.com](https://dashboard.render.com/) and click **"New" $\rightarrow$ "Blueprint"**.
3. Connect your GitHub repository.
4. Render automatically detects [render.yaml](file:///c:/Assignment%203/render.yaml) and offers to deploy:
   - **`airresolve-streamlit`**: The Streamlit interface (`app.py`).
   - **`airresolve-portal`**: The Flask API and modern web portal (`api/index.py`).
5. Click **"Apply"**.

---

### Method 2: Manual Web Service on Render (Step-by-Step)
If you prefer setting up manually:
1. Log into [dashboard.render.com](https://dashboard.render.com/).
2. Click **"New +" $\rightarrow$ "Web Service"**.
3. Select **"Build and deploy from a Git repository"** and connect your GitHub repo.
4. Fill in the following fields:

#### To Deploy Streamlit on Render:
* **Name**: `airresolve-streamlit`
* **Region**: Oregon (US West) or Singapore
* **Branch**: `master`
* **Runtime**: `Python 3`
* **Build Command**:
  ```bash
  pip install -r requirements.txt
  ```
* **Start Command**:
  ```bash
  streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.enableCORS false --server.enableXsrfProtection false
  ```
* **Plan**: Free ($0/month).
* Click **"Create Web Service"**.

#### To Deploy the Modern Web Portal & Flask API on Render:
* **Name**: `airresolve-web`
* **Build Command**: `pip install -r requirements.txt`
* **Start Command**:
  ```bash
  gunicorn api.index:app --bind 0.0.0.0:$PORT --workers 2 --threads 4
  ```
* Click **"Create Web Service"**.

---

## 4. Key Differences to Note for Your Reviewer

| Feature | Streamlit Community Cloud | Render (Free Tier) |
| :--- | :--- | :--- |
| **Cold Start Delay** | Fast (~10-15 seconds if asleep) | Slower (~45-60 seconds if asleep) |
| **Shareable Link** | `https://<your-app>.streamlit.app` | `https://<your-app>.onrender.com` |
| **WebSockets Support** | Built-in native optimization | Standard HTTP/WS |
| **Best Presentation** | Clean Python data app | Full cloud container service |
