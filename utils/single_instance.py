"""
Single Instance Lock - Prevents multiple instances of BeamSkin Studio from running
"""
import os
import sys
import tempfile
from tkinter import messagebox

class SingleInstanceLock:
    """Ensures only one instance of the application can run at a time"""
    
    def __init__(self, app_name="BeamSkinStudio"):
        self.app_name = app_name
        self.lock_file = None
        self.lock_file_path = None
        
        # Platform-specific lock file location
        if sys.platform == "win32":
            # Windows: Use temp directory
            lock_dir = tempfile.gettempdir()
        else:
            # Linux/Mac: Use temp directory
            lock_dir = tempfile.gettempdir()
        
        self.lock_file_path = os.path.join(lock_dir, f"{app_name}.lock")
    
    def acquire(self):
        """Try to acquire the lock. Returns True if successful, False if another instance is running"""
        try:
            # Check if lock file exists
            if os.path.exists(self.lock_file_path):
                # Try to read the PID from the lock file
                try:
                    with open(self.lock_file_path, 'r') as f:
                        pid = int(f.read().strip())
                    
                    # Check if the process is still running
                    if self._is_process_running(pid):
                        print(f"[DEBUG] Another instance is running (PID: {pid})")
                        return False
                    else:
                        # Stale lock file, remove it
                        print(f"[DEBUG] Removing stale lock file (PID: {pid} not running)")
                        os.remove(self.lock_file_path)
                except (ValueError, IOError):
                    # Invalid lock file, remove it
                    print(f"[DEBUG] Removing invalid lock file")
                    try:
                        os.remove(self.lock_file_path)
                    except:
                        pass
            
            # Create lock file with current PID
            with open(self.lock_file_path, 'w') as f:
                f.write(str(os.getpid()))
            
            self.lock_file = self.lock_file_path
            print(f"[DEBUG] Lock acquired: {self.lock_file_path}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to acquire lock: {e}")
            return True  # Allow app to run if lock mechanism fails
    
    def release(self):
        """Release the lock by removing the lock file"""
        if self.lock_file and os.path.exists(self.lock_file):
            try:
                os.remove(self.lock_file)
                print(f"[DEBUG] Lock released: {self.lock_file}")
            except Exception as e:
                print(f"[ERROR] Failed to release lock: {e}")
    
    def _is_process_running(self, pid):
        """Check if a process with the given PID is running"""
        try:
            if sys.platform == "win32":
                # Windows: Use tasklist
                import subprocess
                result = subprocess.run(
                    ['tasklist', '/FI', f'PID eq {pid}'],
                    capture_output=True,
                    text=True
                )
                return str(pid) in result.stdout
            else:
                # Linux/Mac: Use kill signal 0
                os.kill(pid, 0)
                return True
        except (OSError, subprocess.SubprocessError):
            return False
    
    def __enter__(self):
        """Context manager entry"""
        return self.acquire()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.release()


def check_single_instance(app_name="BeamSkinStudio"):
    """
    Check if another instance is running and show error dialog if so.
    Returns True if this is the only instance, False otherwise.
    """
    lock = SingleInstanceLock(app_name)
    
    if not lock.acquire():
        # Another instance is running - try to bring it to front
        print(f"[DEBUG] Another instance detected, attempting to bring it to front...")
        
        try:
            # Try to bring the existing window to front
            if sys.platform == "win32":
                # Windows: Try to find and activate the window
                try:
                    import win32gui
                    import win32con
                    
                    def callback(hwnd, extra):
                        if app_name.lower() in win32gui.GetWindowText(hwnd).lower():
                            # Found the window, bring it to front
                            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                            win32gui.SetForegroundWindow(hwnd)
                            return False
                        return True
                    
                    win32gui.EnumWindows(callback, None)
                except ImportError:
                    print("[DEBUG] pywin32 not available, cannot bring window to front")
        except Exception as e:
            print(f"[DEBUG] Could not bring existing window to front: {e}")
        
        # Show error dialog
        try:
            # Import tkinter for message box
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # Hide the root window
            root.attributes('-topmost', True)  # Make dialog appear on top
            
            messagebox.showerror(
                "Already Running",
                f"{app_name} is already running!\n\n"
                "Please close the existing instance before starting a new one.",
                parent=root
            )
            root.destroy()
        except Exception as e:
            print(f"[ERROR] Failed to show dialog: {e}")
            print(f"[ERROR] {app_name} is already running!")
        
        return False
    
    return True


# Global lock instance to be used in main.py
_global_lock = None

def acquire_global_lock(app_name="BeamSkinStudio"):
    """Acquire a global lock. Call this at program start."""
    global _global_lock
    _global_lock = SingleInstanceLock(app_name)
    return _global_lock.acquire()

def release_global_lock():
    """Release the global lock. Call this at program exit."""
    global _global_lock
    if _global_lock:
        _global_lock.release()