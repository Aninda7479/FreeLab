"""
Digital Wellbeing Tracker - Background Service
Runs silently in the system tray and logs active window information.
Features:
- Red heart system tray icon
- Click to open dashboard
- Smart sleep/wake detection
- Browser title tracking (Chrome, Edge, Ulaa)
- Only tracks visible foreground window
"""

import time
import threading
import sqlite3
import psutil
import win32gui
import win32process
import win32api
import win32con
from datetime import datetime
from pystray import Icon, MenuItem, Menu
from PIL import Image, ImageDraw
import subprocess
import os
import sys

# Configuration
DB_NAME = 'screentime.db'
POLL_INTERVAL = 5  # seconds
MIN_SESSION_LENGTH = 5  # minimum seconds to log

# --- DATABASE SETUP ---
def init_db():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Main logs table with timestamp aggregation
    c.execute('''CREATE TABLE IF NOT EXISTS logs 
                 (timestamp TEXT, app_name TEXT, window_title TEXT, duration INTEGER, device_id TEXT DEFAULT 'windows_main', platform TEXT DEFAULT 'windows')''')
    
    # Daily aggregates for faster querying
    c.execute('''CREATE TABLE IF NOT EXISTS daily_stats
                 (date TEXT, app_name TEXT, total_seconds INTEGER, device_id TEXT DEFAULT 'windows_main', platform TEXT DEFAULT 'windows',
                  PRIMARY KEY (date, app_name, device_id))''')
    
    conn.commit()
    conn.close()

def log_activity(app_name, window_title, duration, session_start_time=None):
    """Log activity to the database."""
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Use session start time if provided, otherwise use current time
    if session_start_time:
        timestamp = datetime.fromtimestamp(session_start_time).strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.fromtimestamp(session_start_time).strftime("%Y-%m-%d")
    else:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date = datetime.now().strftime("%Y-%m-%d")
    
    c.execute("INSERT INTO logs (timestamp, app_name, window_title, duration, device_id, platform) VALUES (?, ?, ?, ?, 'windows_main', 'windows')", 
              (timestamp, app_name, window_title, duration))
    
    # Update daily stats
    c.execute('''INSERT INTO daily_stats (date, app_name, total_seconds, device_id, platform) 
                 VALUES (?, ?, ?, 'windows_main', 'windows')
                 ON CONFLICT(date, app_name, device_id) 
                 DO UPDATE SET total_seconds = total_seconds + ?''',
              (date, app_name, duration, duration))
    
    conn.commit()
    conn.close()

def run_maintenance():
    """Delete logs older than 1 day and daily_stats older than 1 year."""
    try:
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        # Delete raw logs older than 1 day (24 hours)
        c.execute("DELETE FROM logs WHERE timestamp < datetime('now', '-1 day')")
        # Delete aggregated stats older than 1 year
        c.execute("DELETE FROM daily_stats WHERE date < date('now', '-1 year')")
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Maintenance error: {e}")

# --- TRACKING LOGIC ---
def get_active_window_info():
    """Get the currently active (foreground) window's process name and title."""
    try:
        # Get the foreground window (the one that's actually visible and active)
        hwnd = win32gui.GetForegroundWindow()
        
        # Check if window is actually visible and not minimized
        if not win32gui.IsWindowVisible(hwnd):
            return None, None
            
        # Get the Process ID (PID) from the window handle
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        process = psutil.Process(pid)
        app_name = process.name()
        
        # Get the visible window title (contains website title for browsers)
        window_title = win32gui.GetWindowText(hwnd)
        
        # Filter out empty titles
        if not window_title or window_title.strip() == "":
            return None, None
        
        return app_name, window_title
    except Exception as e:
        return None, None

def is_system_awake():
    """Check if the system is awake (not sleeping/hibernating)."""
    try:
        # Try to get system power status
        # This is a simple check - if we can execute normally, system is awake
        return True
    except:
        return False

def tracker_loop(stop_event, pause_event):
    """Main tracking loop that monitors active windows."""
    last_app = None
    last_title = None
    session_start = time.time()
    last_maintenance = time.time()
    
    print("🎯 Digital Wellbeing Tracker started!")
    print("📊 Tracking foreground window only (what you're actually viewing)")
    print("💤 Smart sleep/wake detection enabled")
    
    while not stop_event.is_set():
        # Check if 1 hour has passed since last maintenance
        if time.time() - last_maintenance > 3600:
            run_maintenance()
            last_maintenance = time.time()

        # Check if tracking is paused (during sleep/hibernate)
        if pause_event.is_set():
            # System is sleeping, pause tracking
            if last_app and last_title:
                # Save the current session before pausing
                duration = int(time.time() - session_start)
                if duration >= MIN_SESSION_LENGTH:
                    log_activity(last_app, last_title, duration, session_start)
                    print(f"💾 Saved session before sleep: {last_app} - {duration}s")
                last_app = None
                last_title = None
            
            # Wait until unpaused
            while pause_event.is_set() and not stop_event.is_set():
                time.sleep(1)
            
            # Resume tracking
            print("🌅 System woke up, resuming tracking...")
            session_start = time.time()
            continue
        
        # Get currently visible foreground window
        app_name, window_title = get_active_window_info()
        
        if app_name and window_title:
            # Check if we're still on the same app/window
            if app_name == last_app and window_title == last_title:
                # Continue timing the current session
                pass
            else:
                # Window changed - log the previous session
                if last_app and last_title:
                    duration = int(time.time() - session_start)
                    if duration >= MIN_SESSION_LENGTH:
                        log_activity(last_app, last_title, duration, session_start)
                        print(f"✅ Logged: {last_app[:20]} - {window_title[:40]} ({duration}s)")
                
                # Start new session
                last_app = app_name
                last_title = window_title
                session_start = time.time()
        else:
            # No valid window detected (e.g., desktop, screensaver)
            if last_app and last_title:
                duration = int(time.time() - session_start)
                if duration >= MIN_SESSION_LENGTH:
                    log_activity(last_app, last_title, duration, session_start)
                last_app = None
                last_title = None
        
        # Measure actual sleep time to detect hibernation/suspend
        sleep_start = time.time()
        time.sleep(POLL_INTERVAL)
        sleep_end = time.time()
        
        actual_sleep = sleep_end - sleep_start
        
        # If sleep took significantly longer than expected (e.g., > 10 seconds for a 5s sleep)
        # It means the system was likely sleeping/hibernating
        if actual_sleep > POLL_INTERVAL + 5:
            print(f"⏰ Time gap detected: {int(actual_sleep)}s (System sleep/hibernate?)")
            
            # Log the session ending BEFORE the sleep
            if last_app and last_title:
                # Calculate duration up to the moment we went to sleep
                # sleep_start is the approximate time the system suspended
                duration = int(sleep_start - session_start)
                if duration >= MIN_SESSION_LENGTH:
                    log_activity(last_app, last_title, duration, session_start)
                    print(f"💤 Saved pre-sleep session: {last_app} - {duration}s")
            
            # Reset state for when we wake up
            last_app = None
            last_title = None
            session_start = sleep_end
            continue
    
    # Log final session when stopping
    if last_app and last_title:
        duration = int(time.time() - session_start)
        if duration >= MIN_SESSION_LENGTH:
            log_activity(last_app, last_title, duration, session_start)
            print(f"💾 Final session saved: {last_app} - {duration}s")

# --- SYSTEM POWER MONITORING ---
def power_monitor_loop(pause_event, stop_event):
    """Monitor system power events (sleep/wake)."""
    try:
        import win32api
        import win32con
        import win32gui_struct
        
        # This is a simplified version - just monitor for system events
        # In a full implementation, you'd register for WM_POWERBROADCAST events
        last_check = time.time()
        
        while not stop_event.is_set():
            current_time = time.time()
            
            # If more than 30 seconds have passed since last check,
            # system might have been sleeping
            if current_time - last_check > 30:
                print("⚠️ Gap detected - system may have been sleeping")
                pause_event.set()
                time.sleep(2)
                pause_event.clear()
            
            last_check = current_time
            time.sleep(10)
    except:
        # If power monitoring fails, just continue
        pass

# --- NETWORK DISCOVERY ---
def mdns_broadcast_loop(stop_event):
    """Broadcast presence via zero configuration networking (mDNS)."""
    try:
        from zeroconf import ServiceInfo, Zeroconf
        import socket
        
        # Get local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
            
        desc = {'service': 'Digital Wellbeing Tracker', 'platform': 'windows'}
        
        info = ServiceInfo(
            "_screentime._tcp.local.",
            "WindowsTracker._screentime._tcp.local.",
            addresses=[socket.inet_aton(IP)],
            port=8080,
            properties=desc,
            server="windowstracker.local."
        )
        
        zeroconf = Zeroconf()
        print(f"📡 mDNS Broadcast started on {IP}:8080 (WindowsTracker)")
        zeroconf.register_service(info)
        
        while not stop_event.is_set():
            time.sleep(5)
            
        zeroconf.unregister_service(info)
        zeroconf.close()
    except Exception as e:
        print(f"❌ mDNS Error: {e}")

# --- SYSTEM TRAY (GUI) ---
def create_heart_icon():
    """Generate a red heart icon for the system tray."""
    width = 64
    height = 64
    image = Image.new('RGBA', (width, height), (0, 0, 0, 0))  # Transparent background
    d = ImageDraw.Draw(image)
    
    # Draw a heart shape in light red/pink
    # Create heart using two circles and a triangle
    heart_color = (255, 100, 100, 255)  # Light red/pink
    
    # Left circle of heart
    d.ellipse((10, 15, 30, 35), fill=heart_color)
    # Right circle of heart
    d.ellipse((34, 15, 54, 35), fill=heart_color)
    # Bottom triangle/rectangle to complete heart
    d.polygon([(10, 25), (54, 25), (32, 50)], fill=heart_color)
    
    return image

# Global variable to track dashboard process
dashboard_process = None

def open_dashboard(icon, item):
    """Open the dashboard in browser."""
    global dashboard_process
    try:
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.py')
        if os.path.exists(dashboard_path):
            # Check if dashboard is already running
            if dashboard_process is None or dashboard_process.poll() is not None:
                # Start the dashboard in a new process if not already running
                dashboard_process = subprocess.Popen(['py', dashboard_path], 
                               creationflags=subprocess.CREATE_NO_WINDOW,
                               cwd=os.path.dirname(__file__))
                
                # Give it a moment to start
                time.sleep(2)
            
            # Open browser to the dashboard
            import webbrowser
            webbrowser.open('http://localhost:8080')
            
            print("🌐 Dashboard opened in browser!")
        else:
            print("❌ Dashboard file not found!")
    except Exception as e:
        print(f"❌ Error opening dashboard: {e}")

def refresh_dashboard(icon, item):
    """Refresh the dashboard by restarting the process and opening in browser."""
    global dashboard_process
    try:
        # Kill existing dashboard process if running
        if dashboard_process is not None and dashboard_process.poll() is None:
            print("🛑 Stopping existing dashboard process...")
            try:
                # Kill the entire process tree (including child processes)
                parent = psutil.Process(dashboard_process.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
                dashboard_process.wait(timeout=5)
            except (psutil.NoSuchProcess, subprocess.TimeoutExpired):
                pass
            dashboard_process = None
            time.sleep(1)
        
        # Also kill any other stray dashboard.py processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and 'dashboard.py' in ' '.join(proc.info['cmdline']):
                    print(f"🛑 Killing stray dashboard process: {proc.info['pid']}")
                    proc.kill()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        time.sleep(1)
        
        # Start fresh dashboard process
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.py')
        if os.path.exists(dashboard_path):
            print("🚀 Starting new dashboard process...")
            dashboard_process = subprocess.Popen(['py', dashboard_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW,
                           cwd=os.path.dirname(__file__))
            
            # Give it a moment to start
            time.sleep(2)
            
            # Open browser to the dashboard
            import webbrowser
            webbrowser.open('http://localhost:8080')
            
            print("🔄 Dashboard refreshed with latest code!")
        else:
            print("❌ Dashboard file not found!")
    except Exception as e:
        print(f"❌ Error refreshing dashboard: {e}")

# Ensure requests is available
try:
    import requests
except ImportError:
    pass

def ensure_dashboard_running():
    """Check if dashboard is running, start if not."""
    global dashboard_process
    url = "http://localhost:8080/api/stats"
    
    # Check if already accessible
    try:
        requests.get(url, timeout=0.5)
        return True
    except:
        pass
        
    print("⚠️ Dashboard not responding, starting it...")
    
    # Start it
    try:
        dashboard_path = os.path.join(os.path.dirname(__file__), 'dashboard.py')
        if os.path.exists(dashboard_path):
            # Kill any strays first to be safe
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    if proc.info['cmdline'] and 'dashboard.py' in ' '.join(proc.info['cmdline']):
                        proc.kill()
                except:
                    pass
            
            dashboard_process = subprocess.Popen(['py', dashboard_path], 
                           creationflags=subprocess.CREATE_NO_WINDOW,
                           cwd=os.path.dirname(__file__))
            
            # Wait for it to come up (max 5 seconds)
            for _ in range(10):
                time.sleep(0.5)
                try:
                    requests.get(url, timeout=0.5)
                    print("✅ Dashboard started successfully")
                    return True
                except:
                    continue
    except Exception as e:
        print(f"❌ Failed to start dashboard: {e}")
        
    return False

def show_popup(icon, item):
    """Show the Quick Access popup using Edge/Chrome in App Mode positioned at bottom right."""
    try:
        # Step 1: Ensure Backend is Running
        if not ensure_dashboard_running():
            print("❌ Cannot show popup: Backend failed to start")
            return

        url = "http://localhost:8080/quick-access"
        
        # Window dimensions
        width = 375
        height = 600 # Slightly shorter since notifications removed
        
        # Get Screen Resolution
        try:
            import ctypes
            user32 = ctypes.windll.user32
            screen_w = user32.GetSystemMetrics(0)
            screen_h = user32.GetSystemMetrics(1)
            
            # Allow for taskbar (approx 50px) and margin
            x_pos = screen_w - width - 20
            y_pos = screen_h - height - 50
        except:
            # Fallback if ctypes fails
            x_pos = 1500
            y_pos = 400
            
        # Try launching Edge in app mode with position
        cmd = f'start msedge --app={url} --window-size={width},{height} --window-position={x_pos},{y_pos}'
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print(f"❌ Error showing popup: {e}")
        # Fallback to standard open
        import webbrowser
        webbrowser.open("http://localhost:8080/quick-access")

def on_exit(icon, item):
    """Exit the application."""
    global dashboard_process
    print("👋 Digital Wellbeing Tracker stopped.")
    
    # Clean up dashboard process if running
    if dashboard_process is not None and dashboard_process.poll() is None:
        print("🛑 Stopping dashboard process...")
        try:
            # Kill the entire process tree (including child processes)
            parent = psutil.Process(dashboard_process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
            dashboard_process.wait(timeout=5)
        except (psutil.NoSuchProcess, subprocess.TimeoutExpired):
            pass
    
    # Also kill any other stray dashboard.py processes to ensure clean exit
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.info['cmdline'] and 'dashboard.py' in ' '.join(proc.info['cmdline']):
                print(f"🛑 Killing stray dashboard process: {proc.info['pid']}")
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
    
    stop_event.set()
    icon.stop()

if __name__ == "__main__":
    init_db()
    
    # Event flags
    stop_event = threading.Event()
    pause_event = threading.Event()  # For sleep/wake handling
    
    # Run tracker in a separate thread
    tracker_thread = threading.Thread(
        target=tracker_loop, 
        args=(stop_event, pause_event), 
        daemon=True
    )
    tracker_thread.start()
    
    # Run power monitor in separate thread (optional)
    power_thread = threading.Thread(
        target=power_monitor_loop,
        args=(pause_event, stop_event),
        daemon=True
    )
    power_thread.start()
    
    # Run mDNS broadcast
    mdns_thread = threading.Thread(
        target=mdns_broadcast_loop,
        args=(stop_event,),
        daemon=True
    )
    mdns_thread.start()
    
    # Setup System Tray
    image = create_heart_icon()
    menu = Menu(
        MenuItem('📊 Quick Access', show_popup, default=True),
        MenuItem('❤️ Open Dashboard', open_dashboard),
        MenuItem('🔄 Refresh Dashboard', refresh_dashboard),
        MenuItem('Exit', on_exit)
    )
    icon = Icon("Digital Wellbeing", image, "Digital Wellbeing Tracker", menu)
    
    print("❤️ System tray icon loaded (red heart)")
    print("💡 Click the heart icon to open your dashboard!")
    
    # Run the tray icon (this blocks until exit)
    icon.run()
