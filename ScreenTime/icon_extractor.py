"""
Icon Extractor for Screen Time Tracker
Extracts icons from .exe files and converts them to PNG for web display.
"""

import os
import win32api
import win32con
import win32ui
import win32gui
from PIL import Image
import io
import base64
import psutil

ICON_CACHE = {}
EXE_PATH_CACHE = {}
ICON_SIZE = 48  # Size for dashboard display

# Built-in fallback icons for difficult apps (Windows Store apps, etc.)
FALLBACK_ICONS = {
    'whatsapp': 'data:image/png;base64,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'
}

def get_exe_path(app_name):
    """Try to find the full path to an executable using psutil and common paths."""
    # Check cache first
    if app_name in EXE_PATH_CACHE:
        return EXE_PATH_CACHE[app_name]
    
    app_lower = app_name.lower()
    
    # Method 1: Check running processes
    try:
        for proc in psutil.process_iter(['name', 'exe']):
            try:
                if proc.info['name'] and proc.info['name'].lower() == app_lower:
                    if proc.info['exe'] and os.path.exists(proc.info['exe']):
                        EXE_PATH_CACHE[app_name] = proc.info['exe']
                        return proc.info['exe']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
    except Exception as e:
        print(f"Error checking running processes: {e}")
    
    # Method 2: Specific App Locations
    if 'ulaa' in app_lower:
        ulaa_path = os.path.expandvars(r'%LOCALAPPDATA%\Ulaa\Application\ulaa.exe')
        if os.path.exists(ulaa_path):
            EXE_PATH_CACHE[app_name] = ulaa_path
            return ulaa_path
            
    if 'whatsapp' in app_lower:
        # Check for WhatsApp Desktop (conventional win32)
        wa_path = os.path.expandvars(r'%LOCALAPPDATA%\WhatsApp\WhatsApp.exe')
        if os.path.exists(wa_path):
            EXE_PATH_CACHE[app_name] = wa_path
            return wa_path
            
    # Method 3: Common installation directories
    search_paths = [
        os.path.expandvars(r'C:\Program Files'),
        os.path.expandvars(r'C:\Program Files (x86)'),
        os.path.expandvars(r'%LOCALAPPDATA%\Programs'),
        os.path.expandvars(r'%APPDATA%'),
        os.path.expandvars(r'C:\Windows\System32'),
        os.path.expandvars(r'%LOCALAPPDATA%'), # Added for apps like Ulaa/WhatsApp
    ]
    
    # Recursive search with limited depth
    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
        
        try:
            for root, dirs, files in os.walk(base_path):
                # Don't go too deep
                depth = root[len(base_path):].count(os.sep)
                if depth > 3:
                     # Stop walking this branch
                    del dirs[:]
                    continue
                    
                if app_name in files:
                    return os.path.join(root, app_name)
                    
                # Case insensitive check
                for file in files:
                    if file.lower() == app_lower:
                        exe_path = os.path.join(root, file)
                        EXE_PATH_CACHE[app_name] = exe_path
                        return exe_path
        except (PermissionError, OSError):
            continue
    
    return None

def extract_icon_from_exe(exe_path):
    """Extract icon from an exe file and return as base64 PNG."""
    try:
        # Extract icons
        large, small = win32gui.ExtractIconEx(exe_path, 0)
        
        if not large:
            return None
            
        # Use the first large icon
        hicon = large[0]
        
        # Get icon info
        ico_x = win32api.GetSystemMetrics(win32con.SM_CXICON)
        ico_y = win32api.GetSystemMetrics(win32con.SM_CYICON)
        
        # Create a device context and bitmap
        hdc = win32ui.CreateDCFromHandle(win32gui.GetDC(0))
        hbmp = win32ui.CreateBitmap()
        hbmp.CreateCompatibleBitmap(hdc, ico_x, ico_y)
        hdc_compatible = hdc.CreateCompatibleDC()
        
        hdc_compatible.SelectObject(hbmp)
        hdc_compatible.DrawIcon((0, 0), hicon)
        
        # Convert to PIL Image
        bmpstr = hbmp.GetBitmapBits(True)
        img = Image.frombuffer(
            'RGB',
            (ico_x, ico_y),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        # Resize to desired size
        img = img.resize((ICON_SIZE, ICON_SIZE), Image.Resampling.LANCZOS)
        
        # Convert to base64 PNG
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Cleanup
        win32gui.DestroyIcon(hicon)
        for icon in large + small:
            try:
                win32gui.DestroyIcon(icon)
            except:
                pass
        
        return f"data:image/png;base64,{img_str}"
        
    except Exception as e:
        print(f"Error extracting icon from {exe_path}: {e}")
        return None

def get_app_icon(app_name):
    """Get app icon as base64 data URL, with caching."""
    # Check cache first
    if app_name in ICON_CACHE:
        return ICON_CACHE[app_name]
    
    print(f"🔍 Looking for icon: {app_name}")
    
    # Check built-in fallbacks first if extraction is known to be difficult
    app_lower = app_name.lower()
    for key, icon in FALLBACK_ICONS.items():
        if key in app_lower:
            print(f"✅ Using fallback icon for {app_name}")
            ICON_CACHE[app_name] = icon
            return icon
    
    # Try to find and extract icon
    exe_path = get_exe_path(app_name)
    if exe_path:
        print(f"✅ Found exe at: {exe_path}")
        icon_data = extract_icon_from_exe(exe_path)
        if icon_data:
            print(f"✅ Extracted icon for {app_name}")
            ICON_CACHE[app_name] = icon_data
            return icon_data
        else:
            print(f"⚠️ Could not extract icon from {exe_path}")
    else:
        print(f"❌ Could not find exe for {app_name}")
    
    # Cache the failure so we don't keep searching
    ICON_CACHE[app_name] = None
    return None
