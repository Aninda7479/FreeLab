import pandas as pd
import sqlite3
from datetime import datetime
import dashboard

# Mock data loading to test logic
print("Testing dashboard logic...")

try:
    df = dashboard.load_data()
    print(f"Data loaded, shaped: {df.shape}")
    
    # Test browser activity
    print("-" * 20)
    print("Testing Javascript Browser Activity Logic:")
    period = 'Today'
    browser_data = dashboard.filter_data(df, period)
    browser_apps = ['chrome.exe', 'firefox.exe', 'msedge.exe', 'brave.exe', 'opera.exe', 'ulaa.exe']
    browser_data = browser_data[browser_data['app_name'].str.lower().isin(browser_apps)]
    
    if not browser_data.empty:
        browser_data = browser_data.copy()
        # mimicking the fix I made
        browser_data['window_title'] = browser_data['window_title'].fillna('')
        browser_data['site'] = browser_data['window_title'].str.split('-').str[0].str.strip()
        browser_data['site'] = browser_data['site'].fillna('Unknown')
        
        site_browser_time = browser_data.groupby(['site', 'app_name'])['duration'].sum().reset_index()
        site_browser_time = site_browser_time.sort_values('duration', ascending=False).head(10)
        
        print("Browser Activity Data:")
        print(site_browser_time)
        
        result = []
        for _, row in site_browser_time.iterrows():
            result.append({
                'site': str(row['site']) if row['site'] else 'Unknown',
                'browser': dashboard.clean_app_name(row['app_name']),
                'icon': dashboard.get_app_icon(row['app_name']),
                'duration': int(row['duration'])
            })
        print("Browser JSON Result Sample:", result[:2])
    else:
        print("No browser data for today")

except Exception as e:
    print(f"Error: {e}")
