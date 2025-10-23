# ⚡ Quick Start Guide
## Deploy in 15 Minutes!

---

## 🎯 Goal
Get your SECURE ELITE 440 dashboard live on the internet in 15 minutes or less!

---

## 📝 What You Need
- [ ] GitHub account (free) - https://github.com/signup
- [ ] Your dashboard code
- [ ] 15 minutes of time
- [ ] Internet connection

---

## 🚀 The 5-Step Process

### Step 1: Test Locally (2 mins)
```bash
streamlit run app.py
```
✅ Works? Continue!  
❌ Errors? Fix them first!

---

### Step 2: Push to GitHub (5 mins)

**Option A: Use the automated script**
```bash
deploy.bat
```
Follow the prompts!

**Option B: Manual commands**
```bash
# Initialize
git init
git add .
git commit -m "Initial commit"

# Create repo on github.com (click + → New repository)

# Connect and push
git remote add origin https://github.com/USERNAME/REPO.git
git branch -M main
git push -u origin main
```

---

### Step 3: Deploy to Streamlit Cloud (5 mins)

1. Go to: **https://share.streamlit.io**
2. Click: **"Sign in with GitHub"**
3. Click: **"New app"**
4. Fill in:
   ```
   Repository: YOUR_USERNAME/REPO_NAME
   Branch: main
   Main file: app.py
   ```
5. Click: **"Deploy!"**
6. Wait 2-5 minutes ⏳

---

### Step 4: Test Your Live App (2 mins)

Your app URL: `https://your-app-name.streamlit.app`

**Check:**
- ✅ Loads without errors
- ✅ Demo mode active
- ✅ Shows ~230V voltage
- ✅ Shows ~10A current
- ✅ Graphs work
- ✅ Mobile-friendly

---

### Step 5: Share It! (1 min)

**Copy your URL and share:**
- LinkedIn
- Resume
- Portfolio
- Email

**Add badge to README:**
```markdown
[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://your-actual-url.streamlit.app)
```

---

## 🎉 Done!

**Your dashboard is now:**
- ✅ Live on the internet
- ✅ Accessible from anywhere
- ✅ Showcasing your skills
- ✅ Ready to