"""
Screen Time Tracker - NiceGUI Dashboard
Modern, beautiful dashboard for visualizing screen time data.
Run with: python dashboard_nicegui.py
"""

from nicegui import ui, app
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import plotly.express as px
from fastapi.responses import FileResponse
from fastapi import Request
import os
import json

# Import icon extractor for real app icons
try:
    import icon_extractor
    USE_REAL_ICONS = True
    print("✅ Real app icons enabled")
except Exception as e:
    print(f"⚠️ Could not load icon extractor: {e}")
    print("📱 Using emoji fallback icons")
    USE_REAL_ICONS = False

DB_NAME = 'screentime.db'

# App icon mapping - common applications
# App icon mapping - common applications
APP_ICONS = {
    'chrome.exe': '🌐', 'firefox.exe': '🦊', 'msedge.exe': '🌐', 'brave.exe': '🦁',
    'opera.exe': '🎭', 'ulaa.exe': '🌐', 'code.exe': '💻', 'pycharm64.exe': '🐍', 'pycharm.exe': '🐍',
    'intellij idea.exe': '💡', 'visual studio.exe': '💻', 'notepad++.exe': '📝',
    'sublime_text.exe': '📝', 'spotify.exe': '🎵', 'discord.exe': '💬',
    'slack.exe': '💼', 'teams.exe': '💼', 'zoom.exe': '🎥', 'skype.exe': '📞',
    'telegram.exe': '✈️', 'whatsapp.exe': '💬', 'signal.exe': '🔒',
    'outlook.exe': '📧', 'thunderbird.exe': '📧', 'excel.exe': '📊',
    'word.exe': '📄', 'powerpoint.exe': '📊', 'photoshop.exe': '🎨',
    'illustrator.exe': '🎨', 'premiere.exe': '🎬', 'obs64.exe': '🎥',
    'steam.exe': '🎮', 'epicgameslauncher.exe': '🎮', 'battle.net.exe': '🎮',
    'explorer.exe': '📁', 'notepad.exe': '📝', 'calculator.exe': '🔢',
}

def get_app_icon(app_name):
    """Get emoji icon for an app."""
    # Try to get real icon first
    if USE_REAL_ICONS:
        real_icon = icon_extractor.get_app_icon(app_name)
        if real_icon:
            return real_icon
    
    app_lower = app_name.lower()
    if app_lower in APP_ICONS:
        return APP_ICONS[app_lower]
    for key, icon in APP_ICONS.items():
        if key in app_lower or app_lower in key:
            return icon
    if any(b in app_lower for b in ['chrome', 'firefox', 'edge', 'brave']):
        return '🌐'
    elif any(c in app_lower for c in ['code', 'studio', 'pycharm']):
        return '💻'
    return '📱'

def clean_app_name(app_name):
    """Convert .exe name to readable app name."""
    name = app_name.replace('.exe', '')
    special_cases = {
        'msedge': 'Microsoft Edge', 'chrome': 'Google Chrome', 'firefox': 'Mozilla Firefox',
        'brave': 'Brave Browser', 'ulaa': 'Ulaa Browser', 'code': 'VS Code', 'pycharm64': 'PyCharm',
        'explorer': 'File Explorer', 'teams': 'Microsoft Teams', 'outlook': 'Outlook',
        'excel': 'Excel', 'word': 'Word', 'discord': 'Discord', 'slack': 'Slack',
        'spotify': 'Spotify', 'steam': 'Steam',
    }
    name_lower = name.lower()
    for key, value in special_cases.items():
        if key in name_lower:
            return value
    return name.replace('_', ' ').replace('-', ' ').title()

def format_duration_short(seconds):
    """Format seconds into compact format."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = int(seconds % 60)
        return f"{int(minutes)}m {secs}s" if secs > 0 else f"{int(minutes)}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{int(hours)}h {int(minutes)}m" if minutes > 0 else f"{int(hours)}h"

def load_data():
    """Load data from database."""
    try:
        conn = sqlite3.connect(DB_NAME)
        logs_df = pd.read_sql_query("SELECT * FROM logs", conn)
        conn.close()
        
        if not logs_df.empty:
            logs_df['timestamp'] = pd.to_datetime(logs_df['timestamp'])
            logs_df['end_time'] = logs_df['timestamp'] + pd.to_timedelta(logs_df['duration'], unit='s')
            logs_df['date'] = logs_df['timestamp'].dt.date
            logs_df['end_date'] = logs_df['end_time'].dt.date
            
            # Identify rows that cross midnight
            cross_midnight = logs_df[logs_df['date'] != logs_df['end_date']]
            
            if not cross_midnight.empty:
                new_rows = []
                indices_to_drop = []
                
                for idx, row in cross_midnight.iterrows():
                    start = row['timestamp']
                    end = row['end_time']
                    duration = row['duration']
                    
                    # Midnight calculation (naive, assumes only 1 crossing for now)
                    midnight = datetime.combine(row['end_date'], datetime.min.time())
                    
                    # Split
                    seconds_today = (midnight - start).total_seconds()
                    seconds_tomorrow = (end - midnight).total_seconds()
                    
                    # Only split if both parts are positive (sanity check)
                    if seconds_today > 0 and seconds_tomorrow > 0:
                        # Row 1: Start to Midnight
                        r1 = row.copy()
                        r1['duration'] = int(seconds_today)
                        r1['date'] = row['date'] # Explicitly set date
                        # r1['timestamp'] is already correct
                        
                        # Row 2: Midnight to End
                        r2 = row.copy()
                        r2['timestamp'] = midnight
                        r2['duration'] = int(seconds_tomorrow)
                        r2['date'] = row['end_date'] # Explicitly set new date
                        
                        new_rows.append(r1)
                        new_rows.append(r2)
                        indices_to_drop.append(idx)
                
                if new_rows:
                    # Drop original rows and append new split rows
                    logs_df = logs_df.drop(indices_to_drop)
                    logs_df = pd.concat([logs_df, pd.DataFrame(new_rows)], ignore_index=True)
                    # Re-sort might be nice but not strictly required by downstream logic
                    # logs_df = logs_df.sort_values('timestamp')

        return logs_df
    except Exception as e:
        print(f"Error loading data: {e}")
        return pd.DataFrame()

def filter_data(df, period, offset=0, target_date=None, from_date=None, to_date=None):
    """Filter data by time period with offset support or specific target date/range."""
    if df.empty:
        return df
    
    today = datetime.now().date()
    
    # 1. Exact Date Match
    if target_date:
        if isinstance(target_date, str):
            try:
                t_date = datetime.strptime(target_date, '%Y-%m-%d').date()
            except:
                return df[0:0] 
        else:
            t_date = target_date
        return df[df['date'] == t_date]
        
    # 2. Date Range Match (Fixed Week support)
    if from_date and to_date:
        try:
            start = datetime.strptime(from_date, '%Y-%m-%d').date() if isinstance(from_date, str) else from_date
            end = datetime.strptime(to_date, '%Y-%m-%d').date() if isinstance(to_date, str) else to_date
            return df[(df['date'] >= start) & (df['date'] <= end)]
        except:
             return df[0:0]

    # 3. Legacy Period/Offset Logic
    
    # Calculate reference 'today' based on offset (shifting by weeks)
    # Reference end date (usually 'today' in the window)
    ref_date = today + timedelta(days=(offset * 7))
    
    p = period.lower()
    
    if p in ["today"]:
        return df[df['date'] == ref_date]
    elif p in ["last 7 days", "7days"]:
        # 7 days ENDING on ref_date
        week_ago = ref_date - timedelta(days=7)
        return df[(df['date'] > week_ago) & (df['date'] <= ref_date)]
    elif p in ["last 30 days", "30days"]:
        month_ago = ref_date - timedelta(days=30)
        return df[(df['date'] > month_ago) & (df['date'] <= ref_date)]
    return df

# --- API Endpoints ---

@app.get('/')
def index():
    """Serve the main static dashboard HTML."""
    if os.path.exists('static/index.html'):
        return FileResponse('static/index.html')
    return "Dashboard HTML not found", 404

# --- API Endpoints for Popup & Tracker ---

@app.get('/quick-access')
def quick_access():
    """Serve the quick access popup HTML."""
    if os.path.exists('static/popup.html'):
        return FileResponse('static/popup.html')
    return "Popup not found", 404

# --- Sync Endpoints ---
@app.get('/api/sync/pull')
def sync_pull():
    """Return all daily_stats for other devices to pull."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # Pull stats for all devices
    c.execute("SELECT date, app_name, total_seconds, device_id, platform FROM daily_stats")
    rows = c.fetchall()
    conn.close()
    
    stats = []
    for r in rows:
        stats.append({
            'date': r[0],
            'app_name': r[1],
            'total_seconds': r[2],
            'device_id': r[3],
            'platform': r[4]
        })
    return {'status': 'success', 'data': stats}

@app.post('/api/sync/push')
async def sync_push(request: Request):
    """Receive daily_stats from another device and merge into local DB."""
    try:
        data = await request.json()
        stats = data.get('data', [])
        
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        inserted_count = 0
        for s in stats:
            # We assume valid json keys
            date = s.get('date')
            app_name = s.get('app_name')
            total_seconds = s.get('total_seconds', 0)
            device_id = s.get('device_id', 'unknown')
            platform = s.get('platform', 'unknown')
            
            if not date or not app_name:
                continue
                
            # Upsert
            c.execute('''INSERT INTO daily_stats (date, app_name, total_seconds, device_id, platform) 
                         VALUES (?, ?, ?, ?, ?)
                         ON CONFLICT(date, app_name, device_id) 
                         DO UPDATE SET total_seconds = excluded.total_seconds 
                         WHERE excluded.total_seconds > daily_stats.total_seconds''',
                      (date, app_name, total_seconds, device_id, platform))
            inserted_count += 1
            
        conn.commit()
        conn.close()
        return {'status': 'success', 'merged_records': inserted_count}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

@app.get('/api/stats')
def get_stats(period: str = '7days', offset: int = 0, from_date: str = None, to_date: str = None):
    """Get overall statistics with trend comparison."""
    logs_df = load_data()
    if logs_df.empty:
        return {
            'total_time': 0,
            'apps_count': 0,
            'change_percent': 0,
            'change_direction': 'same',
            'period': period
        }
    
    # Current period
    filtered_df = filter_data(logs_df, period, offset, from_date=from_date, to_date=to_date)
    
    if filtered_df.empty:
        return {
            'total_time': 0,
            'apps_count': 0,
            'change_percent': 0,
            'change_direction': 'same',
            'period': period
        }
    
    total_time = int(filtered_df['duration'].sum())
    apps_count = int(filtered_df['app_name'].nunique())
    
    # Calculate previous period for comparison
    today = datetime.now().date()
    previous_df = pd.DataFrame()
    p = period.lower()
    
    if p in ["today"]:
        yesterday = today - timedelta(days=1)
        previous_df = logs_df[logs_df['date'] == yesterday]
    elif p in ["last 7 days", "7days"]:
        two_weeks_ago = today - timedelta(days=14)
        week_ago = today - timedelta(days=7)
        previous_df = logs_df[(logs_df['date'] > two_weeks_ago) & (logs_df['date'] <= week_ago)]
    elif p in ["last 30 days", "30days"]:
        two_months_ago = today - timedelta(days=60)
        month_ago = today - timedelta(days=30)
        previous_df = logs_df[(logs_df['date'] > two_months_ago) & (logs_df['date'] <= month_ago)]
    
    # Calculate change percentage
    change_percent = 0
    change_direction = 'same'
    
    if not previous_df.empty:
        previous_time = int(previous_df['duration'].sum())
        if previous_time > 0:
            change_percent = abs(int(((total_time - previous_time) / previous_time) * 100))
            if total_time > previous_time:
                change_direction = 'up'
            elif total_time < previous_time:
                change_direction = 'down'
    
    return {
        'total_time': total_time,
        'apps_count': apps_count,
        'change_percent': change_percent,
        'change_direction': change_direction,
        'period': period
    }

@app.get('/api/top-apps')
def get_top_apps(period: str = '7days', limit: int = 10, offset: int = 0, target_date: str = None, from_date: str = None, to_date: str = None):
    """Get top applications by usage."""
    logs_df = load_data()
    if logs_df.empty:
        return []
    
    filtered_df = filter_data(logs_df, period, offset, target_date, from_date=from_date, to_date=to_date)
    if filtered_df.empty:
        return []
    
    top_apps = filtered_df.groupby('app_name')['duration'].sum().sort_values(ascending=False).head(limit)
    
    result = []
    for app, duration in top_apps.items():
        result.append({
            'app_name': app,
            'display_name': clean_app_name(app),
            'icon': get_app_icon(app),
            'duration': int(duration)
        })
    
    return result

@app.get('/api/daily-trend')
def get_daily_trend(period: str = '7days', offset: int = 0, from_date: str = None, to_date: str = None):
    """Get daily screen time trend."""
    logs_df = load_data()
    if logs_df.empty:
        return []
    
    filtered_df = filter_data(logs_df, period, offset, from_date=from_date, to_date=to_date)
    if filtered_df.empty:
        return []
    
    daily_trend = filtered_df.groupby('date')['duration'].sum().reset_index()
    daily_trend = daily_trend.sort_values('date')
    
    result = []
    for _, row in daily_trend.iterrows():
        result.append({
            'date': row['date'].strftime('%Y-%m-%d'),
            'duration': int(row['duration'])
        })
    
    return result
    
@app.get('/api/browser-activity')
def get_browser_activity(period: str = '7days', limit: int = 10):
    """Get browser activity data."""
    logs_df = load_data()
    if logs_df.empty:
        return []
    
    filtered_df = filter_data(logs_df, period)
    if filtered_df.empty:
        return []
    
    browser_apps = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe', 'ulaa.exe']
    browser_data = filtered_df[filtered_df['app_name'].str.lower().isin(browser_apps)]
    
    if browser_data.empty:
        return []
    
    # Extract site name
    browser_data = browser_data.copy()
    browser_data['window_title'] = browser_data['window_title'].fillna('')
    browser_data['site'] = browser_data['window_title'].str.split('-').str[0].str.strip()
    browser_data['site'] = browser_data['site'].fillna('Unknown')
    
    # Group by site and browser
    site_browser_time = browser_data.groupby(['site', 'app_name'])['duration'].sum().reset_index()
    site_browser_time = site_browser_time.sort_values('duration', ascending=False).head(limit)
    
    result = []
    for _, row in site_browser_time.iterrows():
        result.append({
            'site': str(row['site']) if row['site'] else 'Unknown',
            'browser': clean_app_name(row['app_name']),
            'icon': get_app_icon(row['app_name']),
            'duration': int(row['duration'])
        })
    
    return result

# Serve static files as well if needed (e.g. for css within popup)
if os.path.exists('static'):
    app.add_static_files('/static', 'static')

# Run the app
if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Screen Time Tracker',
        favicon='⏱️',
        dark=False,
        reload=False,
        show=False,  # Don't auto-open browser (tracker.pyw will handle it)
        host='0.0.0.0', # Allow connections from LAN
        port=8080
    )
