"""
BeamSkin Studio - Modern GUI Launcher
Replaces batch files with a sleek GUI that handles Python installation,
dependency management, and application startup.
"""
import customtkinter as ctk
import subprocess
import sys
import os
import threading
import time
import urllib.request
import tempfile

# Theme colors - MATCHING MAIN APP (from settings.py dark theme)
COLORS = {
    "bg": "#0a0a0a",
    "frame_bg": "#141414",
    "card": "#1e1e1e",
    "card_hover": "#282828",
    "accent": "#39E09B",
    "accent_hover": "#2fc97f",
    "text": "#f5f5f5",
    "text_secondary": "#999999",
    "success": "#39E09B",
    "error": "#ff4444",
    "warning": "#ffa726"
}

class LauncherWindow:
    def __init__(self):
        self.app = ctk.CTk()
        self.app.title("BeamSkin Studio - Launcher")
        self.app.geometry("700x550")
        self.app.resizable(False, False)
        self.app.configure(fg_color=COLORS["bg"])
        
        # Keep window on top of all others
        self.app.attributes('-topmost', True)
        
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
        x = (self.app.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.app.winfo_screenheight() // 2) - (550 // 2)
        self.app.geometry(f"700x550+{x}+{y}")
    
    def create_ui(self):
        """Create the launcher UI"""
        # Main container
        main_frame = ctk.CTkFrame(self.app, fg_color=COLORS["bg"])
        main_frame.pack(fill="both", expand=True, padx=25, pady=25)
        
        # Header
        header_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        header_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            header_frame,
            text="🎨",
            font=ctk.CTkFont(size=56)
        ).pack()
        
        ctk.CTkLabel(
            header_frame,
            text="BeamSkin Studio",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=COLORS["accent"]
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            header_frame,
            text="Professional Skin Modding Tool",
            font=ctk.CTkFont(size=13),
            text_color=COLORS["text_secondary"]
        ).pack()
        
        # Status card
        self.status_card = ctk.CTkFrame(
            main_frame,
            fg_color=COLORS["card"],
            corner_radius=16,
            border_width=2,
            border_color=COLORS["accent"]
        )
        self.status_card.pack(fill="both", expand=True, pady=(0, 20))
        
        # Status content
        status_content = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_content.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Status icon
        self.status_icon = ctk.CTkLabel(
            status_content,
            text="🔍",
            font=ctk.CTkFont(size=64)
        )
        self.status_icon.pack(pady=(20, 15))
        
        # Status text
        self.status_label = ctk.CTkLabel(
            status_content,
            text="Initializing...",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=COLORS["text"]
        )
        self.status_label.pack(pady=(0, 10))
        
        # Detail text
        self.detail_label = ctk.CTkLabel(
            status_content,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=COLORS["text_secondary"]
        )
        self.detail_label.pack(pady=(0, 15))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            status_content,
            width=500,
            height=8,
            corner_radius=4,
            fg_color=COLORS["frame_bg"],
            progress_color=COLORS["accent"]
        )
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0)
        
        # Action button (hidden initially)
        self.action_button = ctk.CTkButton(
            status_content,
            text="",
            command=None,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["bg"],
            width=200,
            height=45,
            corner_radius=10,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        
        # Footer
        footer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer_frame.pack()
        
        ctk.CTkLabel(
            footer_frame,
            text="Please wait while we prepare BeamSkin Studio...",
            font=ctk.CTkFont(size=11),
            text_color=COLORS["text_secondary"]
        ).pack()
        
    def update_status(self, icon, message, detail="", progress=None):
        """Update the status display"""
        self.status_icon.configure(text=icon)
        self.status_label.configure(text=message, text_color=COLORS["text"])
        self.detail_label.configure(text=detail)
        if progress is not None:
            self.progress_bar.set(progress)
        self.app.update()
        
    def show_error(self, message, detail="", button_text="Close", button_command=None):
        """Show error state"""
        self.status_icon.configure(text="❌")
        self.status_label.configure(text=message, text_color=COLORS["error"])
        self.detail_label.configure(text=detail)
        self.progress_bar.set(0)
        
        # Show action button
        if button_command is None:
            button_command = self.app.quit
            
        self.action_button.configure(
            text=button_text,
            command=button_command,
            fg_color=COLORS["error"],
            hover_color="#cc3636"
        )
        self.action_button.pack(pady=10)
        
    def show_success(self, message, detail=""):
        """Show success state"""
        self.status_icon.configure(text="✅")
        self.status_label.configure(text=message, text_color=COLORS["success"])
        self.detail_label.configure(text=detail)
        self.progress_bar.set(1.0)
        
    def show_choice(self, icon, message, detail, yes_text, no_text, yes_command, no_command):
        """Show a choice dialog"""
        self.status_icon.configure(text=icon)
        self.status_label.configure(text=message)
        self.detail_label.configure(text=detail)
        self.progress_bar.set(0)
        
        # Create button frame
        button_frame = ctk.CTkFrame(self.status_card, fg_color="transparent")
        button_frame.pack(pady=10)
        
        ctk.CTkButton(
            button_frame,
            text=yes_text,
            command=lambda: [button_frame.destroy(), yes_command()],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color=COLORS["bg"],
            width=150,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            button_frame,
            text=no_text,
            command=lambda: [button_frame.destroy(), no_command()],
            fg_color=COLORS["card"],
            hover_color=COLORS["card_hover"],
            text_color=COLORS["text"],
            width=150,
            height=40,
            corner_radius=10,
            font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=5)
        
    def run(self):
        """Start the launcher"""
        self.app.mainloop()


class SetupManager:
    """Handles Python installation and dependency management"""
    
    def __init__(self, launcher):
        self.launcher = launcher
        
    def check_python(self):
        """Check if Python is installed"""
        try:
            result = subprocess.run(
                ["python", "--version"],
                capture_output=True,
                text=True,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                return True, version
            return False, None
        except FileNotFoundError:
            return False, None
    
    def open_python_download(self):
        """Open Python download page in browser"""
        import webbrowser
        webbrowser.open("https://www.python.org/downloads/")
    
    def install_packages(self):
        """Install required Python packages"""
        packages = ["pip", "customtkinter", "Pillow", "requests"]
        
        for i, package in enumerate(packages):
            progress = 0.3 + (i + 1) / len(packages) * 0.6  # 30-90%
            
            if package == "pip":
                self.launcher.update_status(
                    "📦",
                    "Updating package manager...",
                    "Upgrading pip to latest version",
                    progress
                )
                
                result = subprocess.run(
                    ["python", "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
            else:
                self.launcher.update_status(
                    "📦",
                    "Installing packages...",
                    f"Installing {package}",
                    progress
                )
                
                result = subprocess.run(
                    ["python", "-m", "pip", "install", "--upgrade", package, "--quiet"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                )
            
            if result.returncode != 0:
                # Don't fail on pip upgrade errors, just continue
                if package == "pip":
                    continue
                raise Exception(f"Failed to install {package}")
            
            time.sleep(0.2)  # Brief pause for visual feedback
    
    def launch_app(self):
        """Launch the main application"""
        self.launcher.update_status(
            "🚀",
            "Starting BeamSkin Studio...",
            "Loading application",
            0.95
        )
        
        time.sleep(0.5)
        
        # Get the parent directory (go up from launchers-scripts to root)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(script_dir)
        main_py_path = os.path.join(parent_dir, "main.py")
        
        # Launch main app without console window (don't wait for it)
        if sys.platform == 'win32':
            # Use CREATE_NO_WINDOW flag on Windows and Popen to not wait
            process = subprocess.Popen(
                ["pythonw", main_py_path],
                cwd=parent_dir,  # Set working directory to parent
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # On other platforms, use regular python
            process = subprocess.Popen(
                ["python", main_py_path],
                cwd=parent_dir  # Set working directory to parent
            )
        
        # Wait for main app window to appear before closing launcher
        time.sleep(2)  # Give app time to initialize and show window
        
        # Now hide and close launcher
        self.launcher.app.withdraw()
        self.launcher.app.quit()


def main():
    """Main launcher sequence"""
    launcher = LauncherWindow()
    setup = SetupManager(launcher)
    
    def startup_sequence():
        """Run the startup checks and launch"""
        try:
            # Check Python
            launcher.update_status(
                "🔍",
                "Checking Python installation...",
                "Verifying Python is available",
                0.1
            )
            time.sleep(0.5)
            
            python_installed, version = setup.check_python()
            
            if not python_installed:
                # Ask user to install Python manually
                def open_python_site():
                    import webbrowser
                    webbrowser.open("https://www.python.org/downloads/")
                    launcher.show_error(
                        "Please Install Python",
                        "Download Python from the opened webpage\nMake sure to check 'Add Python to PATH' during installation\nThen restart this launcher",
                        "Close",
                        launcher.app.quit
                    )
                
                launcher.show_choice(
                    "⚠️",
                    "Python Not Found",
                    "Python is required to run BeamSkin Studio.\nWould you like to open the download page?",
                    "Open Download Page",
                    "Close",
                    open_python_site,
                    launcher.app.quit
                )
                return
            
            else:
                launcher.update_status(
                    "✅",
                    f"Python Found: {version}",
                    "Preparing dependencies...",
                    0.2
                )
                time.sleep(0.3)
                continue_startup()
            
        except Exception as e:
            launcher.show_error(
                "Startup Error",
                str(e)
            )
    
    def continue_startup():
        """Continue with package installation and app launch"""
        try:
            # Install/update packages
            launcher.update_status(
                "📦",
                "Checking dependencies...",
                "This will only take a moment",
                0.25
            )
            time.sleep(0.2)
            
            setup.install_packages()
            
            launcher.update_status(
                "✅",
                "All dependencies ready!",
                "Launching application...",
                0.95
            )
            time.sleep(0.3)
            
            # Launch app
            setup.launch_app()
            
        except Exception as e:
            launcher.show_error(
                "Setup Error",
                str(e)
            )
    
    # Start sequence in background thread
    threading.Thread(target=startup_sequence, daemon=True).start()
    
    # Run GUI
    launcher.run()


if __name__ == "__main__":
    main()