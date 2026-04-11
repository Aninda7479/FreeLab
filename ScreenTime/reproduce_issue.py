import requests
import sqlite3
import pandas as pd
from datetime import datetime

# 1. Check DB directly
print("--- Checking Database ---")
try:
    conn = sqlite3.connect('screentime.db')
    cursor = conn.cursor()
    cursor.execute("SELECT count(*) FROM logs")
    count = cursor.fetchone()[0]
    print(f"Total rows in logs: {count}")
    
    if count > 0:
        cursor.execute("SELECT min(timestamp), max(timestamp) FROM logs")
        print(f"Time range in DB: {cursor.fetchone()}")
        
        # Check for this week (Sunday Jan 25 to Sat Jan 31 2026)
        print("Checking for records between 2026-01-25 and 2026-01-31...")
        cursor.execute("SELECT * FROM logs WHERE timestamp >= '2026-01-25' AND timestamp <= '2026-02-01' LIMIT 5")
        rows = cursor.fetchall()
        print(f"Found {len(rows)} rows sample: {rows}")
    else:
        print("Table 'logs' is empty.")
    conn.close()
except Exception as e:
    print(f"DB Error: {e}")

# 2. Check API
print("\n--- Checking API ---")
try:
    response = requests.get('http://localhost:8080/api/daily-trend?from_date=2026-01-25&to_date=2026-01-31')
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"API Error: {e}")
