# ❤️ Digital Wellbeing - Screen Time Tracker

A lightweight, privacy-focused screen time tracker that runs silently in your system tray. Built with Python, it tracks your active windows and provides beautiful insights through an interactive **NiceGUI dashboard**.

## ✨ Features

- **❤️ Beautiful Red Heart Icon**: Light red heart in system tray
- **🖱️ Click to Open Dashboard**: Single click the heart icon to open your stats
- **🎯 Smart Tracking**: Only tracks the **visible foreground window** (what you're actually viewing)
- **🌐 Full Browser Support**: Tracks website titles for Chrome, Edge, Firefox, Brave, Opera, and **Ulaa**
- **💤 Sleep-Aware**: Automatically pauses when PC sleeps/hibernates, resumes on wake
- **🔒 Privacy First**: All data stays on your local machine in a SQLite database
- **📱 System Tray Integration**: Runs in background with minimal resource usage
- **🎨 Beautiful Dashboard**: Modern NiceGUI-powered analytics with gradient cards and charts
- **⚡ Lightweight**: Uses less than 50MB RAM

## 🚀 Quick Start

### 1. Install Dependencies

```bash
py -m pip install -r requirements.txt
```

### 2. Run the Tracker

**For testing (with console):**
```bash
python tracker.pyw
```

**For background mode (no console):**
- Simply double-click `tracker.pyw` in File Explorer
- You'll see a **red heart icon ❤️** appear in your system tray (bottom-right)
- **Click the heart** to open your dashboard!

### 3. View Your Stats

**Option 1: Click the heart icon** in the system tray (easiest!)

**Option 2: Run manually:**
```bash
py dashboard.py
```

This will open your browser at `http://localhost:8080` with an interactive dashboard showing:
- Beautiful gradient stat cards showing total time, apps used, sessions
- Top 5 most used apps with icons and time
- Interactive bar chart of top applications
- Pie chart showing usage distribution
- Daily trends line graph
- Browser activity breakdown (Chrome, Edge, Ulaa, Firefox, etc.)

## 🛠️ Setup for Auto-Start (Optional)

To make the tracker start automatically when Windows boots:

1. Press `Win + R`
2. Type `shell:startup` and press Enter
3. Create a shortcut to `tracker.pyw` in the startup folder
4. Restart your PC to test

Now the tracker will silently start every time you log in!

## 📁 Project Structure

```
ScreenTime/
│
├── tracker.pyw          # Main background tracker (no console)
├── dashboard.py         # Streamlit dashboard for viewing data
├── requirements.txt     # Python dependencies
├── screentime.db        # SQLite database (created automatically)
└── README.md           # This file
```

## 🎮 System Tray Controls

Right-click the system tray icon to:
- **View Stats**: Launch the dashboard (requires Streamlit installed)
- **Exit**: Stop tracking and close the application

## 🔧 Configuration

You can customize tracking behavior by editing `tracker.pyw`:

```python
POLL_INTERVAL = 5   # How often to check active window (seconds)
LOG_INTERVAL = 60   # Minimum session duration to log (seconds)
```

## 📊 Database Schema

The tracker creates two tables:

**logs**: Raw activity logs
- `timestamp`: When the activity occurred
- `app_name`: Process name (e.g., chrome.exe)
- `window_title`: Window title (contains page title for browsers)
- `duration`: How long the window was active (seconds)

**daily_stats**: Aggregated daily statistics
- `date`: Date of activity
- `app_name`: Application name
- `total_seconds`: Total time spent

## 🎨 Dashboard Features

- **Time Period Filters**: View Today, Last 7 Days, Last 30 Days, or All Time
- **Interactive Charts**: Built with Plotly for smooth interactions
- **App Rankings**: See which apps consume most of your time
- **Browser Tracking**: Special section for web browsing activity
- **Export Ready**: Raw data available for further analysis

## 🔒 Privacy & Security

- **Local Only**: No data is sent to any server
- **No Screenshots**: Only window titles and app names are logged
- **Full Control**: You own the database and can delete it anytime
- **Open Source**: Review the code to verify what's tracked

## 🐛 Troubleshooting

**Tracker won't start:**
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check if Python is in your PATH
- Try running `python tracker.pyw` to see error messages

**System tray icon not showing:**
- Check the hidden icons in the system tray (click the ^ arrow)
- Some antivirus software may block system tray access

**Dashboard shows no data:**
- Make sure the tracker has been running for a few minutes
- Check if `screentime.db` exists in the project folder
- Try the "Refresh Data" button in the dashboard

**"View Stats" from tray doesn't work:**
- You need to manually run `streamlit run dashboard.py` from terminal
- The tray option is a convenience feature that may not work on all systems

## 🚀 Advanced Usage

### Export Data to CSV

```python
import sqlite3
import pandas as pd

conn = sqlite3.connect('screentime.db')
df = pd.read_sql_query("SELECT * FROM logs", conn)
df.to_csv('my_screentime.csv', index=False)
conn.close()
```

### Query Specific Apps

```python
import sqlite3

conn = sqlite3.connect('screentime.db')
cursor = conn.cursor()

# Get total time spent on Chrome today
cursor.execute("""
    SELECT SUM(duration) / 3600.0 as hours
    FROM logs
    WHERE app_name = 'chrome.exe'
    AND date(timestamp) = date('now')
""")

hours = cursor.fetchone()[0]
print(f"Chrome usage today: {hours:.2f} hours")
conn.close()
```

## 💡 Alternative: ActivityWatch

If you want a more feature-rich solution with browser extensions for exact URL tracking, check out [ActivityWatch](https://activitywatch.net/). It's built on similar principles but includes:
- Browser extensions for detailed URL tracking
- Cross-platform support (Windows, Mac, Linux)
- More advanced categorization
- Built-in web dashboard

Our tracker is perfect for those who want:
- A lightweight, simple solution
- Full control over the code
- Minimal resource usage
- Custom modifications

## 📝 License

This project is provided as-is for personal use. Feel free to modify and adapt to your needs!

## 🤝 Contributing

Feel free to fork this project and add features like:
- Application categories/tags
- Productivity scoring
- Daily goals and alerts
- Machine learning for pattern detection
- Mobile sync (if you expand to other platforms)

---

**Built with ❤️ for better digital wellbeing**
