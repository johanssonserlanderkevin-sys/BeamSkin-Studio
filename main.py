"""BeamSkin Studio - Entry Point"""
import os
import sys
import threading

# Change working directory
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
print(f"[DEBUG] Working directory: {os.getcwd()}")

def center_window(window):
    """Centers the window on the screen"""
    window.geometry("1600x1000")
    window.update_idletasks()
    
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    x = (screen_width // 2) - (1600 // 2)
    y = (screen_height // 2) - (1000 // 2)
    
    window.geometry(f'1600x1000+{x}+{y}')

if __name__ == "__main__":
    # Import after setting working directory
    from core.updater import check_for_updates, CURRENT_VERSION, set_app_instance
    from core.settings import colors
    from utils.debug import setup_universal_scroll_handler
    
    import gui.app
    
    # Now access the app that was created
    app = gui.app.app
    
    # Give updater access to app and colors for custom UI
    set_app_instance(app, colors)
    
    print(f"\n[DEBUG] ========================================")
    print(f"[DEBUG] BeamSkin Studio Starting...")
    print(f"[DEBUG] Version: {CURRENT_VERSION}")
    print(f"[DEBUG] ========================================\n")
    
    # Center the window on screen FIRST
    print(f"[DEBUG] Centering window...")
    center_window(app)
    
    # Make window appear on top when launched
    print(f"[DEBUG] Bringing window to front...")
    app.lift()
    app.focus_force()
    app.attributes('-topmost', True)  # Temporarily set on top
    app.after(100, lambda: app.attributes('-topmost', False))  # Remove after 100ms so it doesn't stay on top forever
    
    # Show WIP warning AFTER window is visible and positioned (with delay to ensure window is ready)
    print(f"[DEBUG] Scheduling WIP warning check...")
    app.after(200, gui.app.show_startup_warning)
    
    # Create a thread so the UI stays responsive while checking for updates
    print(f"[DEBUG] Starting update check thread...")
    threading.Thread(target=check_for_updates, daemon=True).start()
    
    # CRITICAL: Initialize universal scroll handler
    print(f"[DEBUG] Initializing scroll handler...")
    app.after(100, lambda: setup_universal_scroll_handler(app))
    
    print(f"[DEBUG] Starting main event loop...")
    print(f"[DEBUG] ========================================\n")
    app.mainloop()