# Quick Start Guide - Screen Time Tracker

## ⚡ TL;DR - Get Started in 3 Steps

### 1️⃣ Start Tracking
Double-click `tracker.pyw` - look for the blue clock icon in your system tray (bottom-right).

### 2️⃣ Wait & Browse
Let it run for 30+ minutes while you use your computer normally.

### 3️⃣ View Stats
Open terminal in this folder and run:
```bash
py dashboard.py
```

The dashboard will open in your browser at `http://localhost:8080` with beautiful gradient cards, charts, and insights!

---

## 🎮 System Tray Controls

Right-click the blue clock icon to:
- **Exit** - Stop tracking and close the app

---

## 🔄 Auto-Start (Recommended)

Make the tracker start automatically when Windows boots:

1. Press **Win + R**
2. Type `shell:startup`
3. Press Enter
4. Drag `tracker.pyw` into this folder (creates shortcut)
5. Restart Windows

Now it runs automatically! No need to remember to start it.

---

## 📊 What Gets Tracked?

- **App Name**: e.g., `chrome.exe`, `Code.exe`, `Spotify.exe`
- **Window Title**: e.g., "YouTube - Google Chrome", "main.py - VSCode"
- **Duration**: How long each window was active

**NOTE**: For browsers, the window title includes the webpage title, so you can see which sites you visit most!

---

## 🔒 Privacy

- ✅ 100% local - no data leaves your computer
- ✅ No screenshots
- ✅ No keylogging
- ✅ Just window titles (what you see in the taskbar)

Delete `screentime.db` anytime to clear all history.

---

## 🐛 Common Issues

**"py is not recognized"**
- Install Python from python.org
- Or use `python -m streamlit run dashboard.py`

**System tray icon not visible**
- Click the ^ arrow in the system tray to see hidden icons

**Dashboard shows "No Data"**
- Make sure tracker is running (check system tray)
- Let it collect data for at least 5-10 minutes
- Click "Refresh Data" button in the dashboard

---

## 📚 Full Documentation

See [README.md](README.md) for detailed information about:
- Customization options
- Advanced queries
- Database schema
- Export to CSV
- And more!

---

**Enjoy tracking your digital life!** 🎉
