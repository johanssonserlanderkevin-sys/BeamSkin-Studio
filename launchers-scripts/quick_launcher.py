"""
BeamSkin Studio - Quick Launcher (No Checks)
Shows loading GUI and launches main.py, closes only when main app is ready
"""
import customtkinter as ctk
import subprocess
import sys
import time
import threading
import os

# Theme colors - MATCHING MAIN APP (from settings.py dark theme)
COLORS = {
    "bg": "#0a0a0a",           # app_bg
    "frame_bg": "#141414",     # frame_bg
    "card": "#1e1e1e",         # card_bg
    "accent": "#39E09B",       # accent (green)
    "text": "#f5f5f5",         # text
    "text_secondary": "#999999" # text_secondary
}

class QuickLauncher:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("BeamSkin Studio")
        self.app.geometry("600x400")
        self.app.resizable(False, False)
        self.app.configure(fg_color=COLORS["bg"])
        
        # Keep window on top of all others
        self.app.attributes('-topmost', True)
        
        # Remove window decorations for cleaner look
        self.app.overrideredirect(True)
        
        # Center window
        self.center_window()
        
        # Create UI
        self.create_ui()
        
        # Lift window to front
        self.app.lift()
        self.app.focus_force()
        
    def center_window(self):
        """Center the window on screen"""
        self.app.update_idletasks()
        x = (self.app.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.app.winfo_screenheight() // 2) - (400 // 2)
        self.app.geometry(f"600x400+{x}+{y}")
    
    def create_ui(self):
        """Create the launcher UI"""
        # Main container with border (matching main app accent color)
        main_frame = ctk.CTkFrame(
            self.app, 
            fg_color=COLORS["frame_bg"],
            border_width=2,
            border_color=COLORS["accent"]
        )
        main_frame.pack(fill="both", expand=True)
        
        content_frame = ctk.CTkFrame(main_frame, fg_color=COLORS["bg"])
        content_frame.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Header
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(expand=True)
        
        # Logo/Icon
        ctk.CTkLabel(
            header_frame,
            text="🎨",
            font=ctk.CTkFont(size=72)
        ).pack(pady=(0, 15))
        
        # Title
        ctk.CTkLabel(
            header_frame,
            text="BeamSkin Studio",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(0, 5))
        
        # Subtitle
        ctk.CTkLabel(
            header_frame,
            text="Professional Skin Modding Tool",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack(pady=(0, 25))
        
        # Loading text
        ctk.CTkLabel(
            header_frame,
            text="Loading BeamSkin Studio...",
            font=ctk.CTkFont(size=15),
            text_color=COLORS["text"]
        ).pack(pady=(0, 25))
        
        # Animated progress bar
        self.progress_bar = ctk.CTkProgressBar(
            header_frame,
            width=420,
            height=8,
            corner_radius=4,
            fg_color=COLORS["card"],
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(pady=(0, 15))
        self.progress_bar.set(0)
        
        # Status text
        ctk.CTkLabel(
            header_frame,
            text="Please wait...",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack()
    
    def animate_progress(self):
        """Animate the progress bar smoothly"""
        for i in range(101):
            self.progress_bar.set(i / 100)
            self.app.update()
            time.sleep(0.015)  # Smooth animation
    
    def launch_app(self):
        """Launch the main application and wait for it to start"""
        # Animate progress bar
        self.animate_progress()
        
        # Get the parent directory (go up from launchers-scripts to root)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        main_py_path = os.path.join(parent_dir, "main.py")
        
        # Launch main app without console window
        if sys.platform == 'win32':
            process = subprocess.Popen(
                ["pythonw", main_py_path],
                cwd=parent_dir,  # Set working directory to parent
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            process = subprocess.Popen(
                ["python", main_py_path],
                cwd=parent_dir  # Set working directory to parent
            )
        
        # Wait longer for main app window to appear (5 seconds)
        time.sleep(2.2)
        
        # Close launcher
        self.app.destroy()
    
    def run(self):
        """Start the launcher"""
        # Start launch sequence in background
        threading.Thread(target=self.launch_app, daemon=True).start()
        
        # Run GUI
        self.app.mainloop()


if __name__ == "__main__":
    launcher = QuickLauncher()
    launcher.run()