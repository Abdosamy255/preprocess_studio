# Guide: Making Preprocess Studio Public

## Step 1: Push to GitHub (Free & Quick)

### 1.1 Create a GitHub Account
If you don't have one, go to https://github.com and sign up.

### 1.2 Create a New Repository
1. Click the **+** icon in the top-right corner
2. Select **New repository**
3. Name it: `preprocess-studio`
4. Description: "A modern web-based ML data preprocessing tool built with FastAPI"
5. Choose **Public** visibility
6. Initialize with README (or skip if you already have one)
7. Click **Create repository**

### 1.3 Push Your Code

Open PowerShell in your project folder and run:

```powershell
# Initialize git
git init

# Add your GitHub username and email
git config user.name "Your Name"
git config user.email "your.email@example.com"

# Add all files
git add .

# Create first commit
git commit -m "Initial commit: Preprocess Studio - FastAPI ML web app"

# Add remote (replace YOUR_USERNAME with your GitHub username)
git remote add origin https://github.com/YOUR_USERNAME/preprocess-studio.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### 1.4 Verify on GitHub
Go to `https://github.com/YOUR_USERNAME/preprocess-studio` to confirm your code is public.

---

## Step 2: Deploy the App (Get a Live URL)

Choose one of these options:

### Option A: Render (Recommended - Free tier available)

1. Go to https://render.com
2. Sign up with GitHub account
3. Click **New +** → **Web Service**
4. Connect your GitHub repository
5. Fill in the details:
   - **Name**: preprocess-studio
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port 10000`
6. Click **Deploy**
7. Wait 2-5 minutes for deployment
8. Your app will be live at: `https://preprocess-studio-xxxx.onrender.com`

### Option B: Heroku (Requires credit card)

1. Go to https://www.heroku.com
2. Sign up (requires credit card even for free tier)
3. Create a new app
4. Connect to GitHub
5. Add `Procfile` to your project:
   ```
   web: uvicorn app:app --host 0.0.0.0 --port $PORT
   ```
6. Deploy

### Option C: Railway (Simple & Free)

1. Go to https://railway.app
2. Sign up with GitHub
3. Create new project from GitHub repo
4. Railway will auto-detect and deploy
5. Your app will be live at: `https://your-project.railway.app`

### Option D: PythonAnywhere (Simple for beginners)

1. Go to https://www.pythonanywhere.com
2. Create free account
3. Upload your code
4. Configure WSGI file
5. Your app will be live at: `https://yourusername.pythonanywhere.com`

---

## Step 3: Update Your LinkedIn Profile

Once deployed, you have:
- **GitHub URL**: `https://github.com/YOUR_USERNAME/preprocess-studio`
- **Live Demo URL**: `https://your-deployed-app.com` (from Render/Heroku/Railway)

Share on LinkedIn:
```
✨ Just launched Preprocess Studio - a modern ML web app built with FastAPI!

Converted from Streamlit to a custom HTML/CSS/JavaScript frontend with a clean API architecture.

Features:
📤 CSV upload with multi-encoding support
📊 Interactive data exploration & visualizations
🤖 Model training (Random Forest, Gradient Boosting, Logistic Regression)
🎯 Real-time predictions
💾 Model download

Tech: FastAPI • pandas • scikit-learn • vanilla JavaScript

🔗 GitHub: [link to repo]
🚀 Live Demo: [link to deployed app]

#MachineLearning #FastAPI #WebDevelopment #Python #DataScience
```

---

## Important Notes

⚠️ **For deployment, modify `app.py` slightly:**

Change this line:
```python
@app.get("/")
async def index():
    html_file = os.path.join(TEMPLATES_DIR, "index.html")
```

To handle relative paths correctly on deployed servers. Your current setup should work, but test on Render first.

⚠️ **Data Persistence:**
- Models are stored in memory, so they're lost on server restart
- For production, consider adding a database (PostgreSQL, MongoDB)

⚠️ **File Upload Limits:**
- Render/Heroku have limits (usually ~32MB)
- For larger files, consider cloud storage (AWS S3, etc.)

---

## Quick Start (TL;DR)

1. **Push to GitHub:**
   - `git init` → `git add .` → `git commit -m "..."` → `git push`

2. **Deploy on Render:**
   - Connect GitHub repo
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `uvicorn app:app --host 0.0.0.0 --port 10000`

3. **Share on LinkedIn:**
   - GitHub repo URL
   - Live demo URL from Render
   - A polished project description

Done! 🚀
