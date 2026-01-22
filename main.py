import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
from config import VEHICLE_IDS
from file_ops import generate_mod
import threading
import sys
import webbrowser
import time
import os
import json
import shutil
from tkinter import messagebox
import io
from datetime import datetime
import re
import copy
import requests

def setup_universal_scroll_handler():
    """
    Sets up intelligent scroll handling that automatically detects
    which scrollable frame the mouse is over and scrolls that frame.
    """
    # Remove any existing scroll bindings first
    app.unbind_all("<MouseWheel>")
    app.unbind_all("<Button-4>")
    app.unbind_all("<Button-5>")
    
    def universal_scroll(event):
        """Handle scroll events intelligently based on mouse position"""
        # Get widget under mouse
        x, y = app.winfo_pointerxy()
        widget = app.winfo_containing(x, y)
        
        if not widget:
            return
        
        # Find the nearest scrollable parent
        scrollable_frame = None
        current = widget
        
        while current:
            # Check if this widget is a scrollable frame
            if isinstance(current, ctk.CTkScrollableFrame):
                scrollable_frame = current
                break
            try:
                current = current.master
            except:
                break
        
        # If we found a scrollable frame, scroll it
        if scrollable_frame:
            try:
                # Calculate scroll amount
                if event.num == 4 or event.delta > 0:
                    # Scroll up 
                    scrollable_frame._parent_canvas.yview_scroll(-25, "units")
                elif event.num == 5 or event.delta < 0:
                    # Scroll down
                    scrollable_frame._parent_canvas.yview_scroll(25, "units")
                return "break"
            except:
                pass
    
    # Bind to all scroll events
    app.bind_all("<MouseWheel>", universal_scroll, add="+")
    app.bind_all("<Button-4>", universal_scroll, add="+")  # Linux scroll up
    app.bind_all("<Button-5>", universal_scroll, add="+")  # Linux scroll down

# Read version from version.txt
def read_version():
    print(f"[DEBUG] ========== READING VERSION FILE ==========")
    try:
        print(f"[DEBUG] Opening version.txt...")
        with open('version.txt', 'r') as f:
            content = f.read().strip()
            print(f"[DEBUG] Raw content: '{content}'")
            if "Version:" in content:
                version = content.replace("Version:", "").strip()
                print(f"[DEBUG] Removed 'Version:' prefix, result: '{version}'")
                return version
            print(f"[DEBUG] No 'Version:' prefix found, returning as-is")
            return content
    except Exception as e:
        print(f"[DEBUG] ERROR reading version.txt: {e}")
        return "Unknown"

CURRENT_VERSION = read_version()
print(f"[DEBUG] Current version set to: {CURRENT_VERSION}")
print(f"[DEBUG] ========== VERSION READ COMPLETE ==========\n")

def center_window(window):
    """Centers the window on the screen"""
    # Set initial geometry first
    window.geometry("1600x1000")
    
    # Force window to process geometry
    window.update_idletasks()
    
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate position for 1600x1000 window
    x = (screen_width // 2) - (1600 // 2)
    y = (screen_height // 2) - (1000 // 2)
    
    # Apply centered geometry
    window.geometry(f'1600x1000+{x}+{y}')

VEHICLE_FOLDER = os.path.join(os.getcwd(), "vehicles")
os.makedirs(VEHICLE_FOLDER, exist_ok=True)

def create_vehicle_folders(carid):
    """
    Creates:
    vehicles/<carid>/SKINNAME
    """
    car_folder = os.path.join(VEHICLE_FOLDER, carid)
    skin_folder = os.path.join(car_folder, "SKINNAME")
    os.makedirs(skin_folder, exist_ok=True)

def delete_vehicle_folders(carid):
    """
    Deletes:
    vehicles/<carid>/
    imagesforgui/vehicles/<carid>/
    """
    # Delete vehicle folder
    car_folder = os.path.join(VEHICLE_FOLDER, carid)
    if os.path.exists(car_folder):
        shutil.rmtree(car_folder)
    
    # Delete preview image folder
    image_folder = os.path.join("imagesforgui", "vehicles", carid)
    if os.path.exists(image_folder):
        shutil.rmtree(image_folder)
        print(f"Deleted preview image folder: {image_folder}")


def edit_material_json(json_path, skinname_folder, carid):
    """
    Edits the material JSON file to keep only the targeted skin sections,
    renames them to use 'skinname' as a placeholder, and updates the baseColorMap path.
    
    Rules:
    1. Only keep sections where the key ends with the same skin name
    2. Rename all kept entries to use '.skin.skinname' as placeholder
    3. Update name and mapTo fields to match the new key
    4. Update baseColorMap in Stage 2 (index 1) to the placeholder path format
    5. The generator will later replace 'skinname' with the actual skin name
    6. Keep all other properties unchanged
    """
    # Use 'skinname' as the placeholder
    skinname = "skinname"
    
    try:
        print(f"\n--- Starting JSON Edit Process ---")
        print(f"Reading JSON file: {json_path}")
        print(f"Target Car ID: {carid}")
        print(f"Using placeholder: 'skinname' (will be replaced by generator)")
        
        # Read the raw file content
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean the JSON content
        print("Cleaning JSON (removing comments and fixing trailing commas)...")
        
        # Remove single-line comments (// ...)
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            # Remove // comments but preserve strings that might contain //
            if '//' in line:
                # Simple approach: find // outside of strings
                in_string = False
                escape = False
                comment_pos = -1
                for i, char in enumerate(line):
                    if escape:
                        escape = False
                        continue
                    if char == '\\':
                        escape = True
                        continue
                    if char == '"':
                        in_string = not in_string
                    if not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                        comment_pos = i
                        break
                if comment_pos >= 0:
                    line = line[:comment_pos]
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Remove block comments (/* ... */)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Fix trailing commas before } or ]
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Parse the cleaned JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not parse JSON even after cleaning - {e}")
            print("Attempting to save cleaned version for manual inspection...")
            cleaned_path = json_path + ".cleaned"
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cleaned JSON saved to: {cleaned_path}")
            raise
        
        print(f"Original JSON contains {len(data)} entries")
        
        # Find all skin names in the JSON
        # Extract the skin name suffix (e.g., ".skin.customskin")
        skin_suffixes = set()
        for key in data.keys():
            # Check if it's a skin key (contains ".skin.")
            if ".skin." in key:
                # Extract everything after ".skin."
                parts = key.split(".skin.")
                if len(parts) == 2:
                    skin_suffixes.add(f".skin.{parts[1]}")
        
        if not skin_suffixes:
            print("WARNING: No skin entries found in JSON")
            return
        
        # Use the first skin suffix found
        target_suffix = list(skin_suffixes)[0]
        print(f"Target skin suffix: {target_suffix}")
        
        # Filter and rename data
        filtered_data = {}
        for key, value in data.items():
            if key.endswith(target_suffix):
                # Extract the prefix (everything before ".skin.")
                parts = key.split(".skin.")
                if len(parts) == 2:
                    prefix = parts[0]
                    # Create new key with the new skinname
                    new_key = f"{prefix}.skin.{skinname}"
                    
                    print(f"Processing: {key} → {new_key}")
                    
                    # Deep copy the value to avoid modifying original
                    new_value = copy.deepcopy(value)
                    
                    # Update name and mapTo fields
                    if "name" in new_value:
                        new_value["name"] = new_key
                        print(f"  Updated name: {new_key}")
                    
                    if "mapTo" in new_value:
                        new_value["mapTo"] = new_key
                        print(f"  Updated mapTo: {new_key}")
                    
                    # Update baseColorMap in Stage 2 (index 1)
                    if "Stages" in new_value and isinstance(new_value["Stages"], list):
                        if len(new_value["Stages"]) > 1:  # Stage 2 exists
                            stage2 = new_value["Stages"][1]
                            if "baseColorMap" in stage2:
                                old_path = stage2["baseColorMap"]
                                # Construct new path based on the prefix
                                # Extract the base material name from prefix (e.g., ccf_main → ccf)
                                base_name = prefix.split('_')[0]
                                new_path = f"vehicles/{carid}/{skinname}/{base_name}_skin_{skinname}.dds"
                                stage2["baseColorMap"] = new_path
                                print(f"  Updated baseColorMap in Stage 2:")
                                print(f"    Old: {old_path}")
                                print(f"    New: {new_path}")
                    
                    filtered_data[new_key] = new_value
        
        print(f"\nFiltered JSON contains {len(filtered_data)} entries")
        
        # Write the edited JSON back to the folder
        json_filename = os.path.basename(json_path)
        output_path = os.path.join(skinname_folder, json_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4)
        
        print(f"Edited JSON saved to: {output_path}")
        print(f"--- JSON Edit Complete ---\n")
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format - {e}")
        raise Exception(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        print(f"ERROR during JSON editing: {e}")
        raise
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON format - {e}")
        raise Exception(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        print(f"ERROR during JSON editing: {e}")
        raise


def check_for_updates():
    """Check for updates from GitHub repository"""
    print(f"\n[DEBUG] ========== UPDATE CHECK STARTED ==========")
    print(f"[DEBUG] Current version: {CURRENT_VERSION}")
    
    # link to your RAW version.txt
    url = "https://raw.githubusercontent.com/johanssonserlanderkevin-sys/BeamSkin-Studio/main/version.txt"
    print(f"[DEBUG] Checking URL: {url}")
    
    try:
        print(f"[DEBUG] Sending HTTP request...")
        response = requests.get(url, timeout=5)
        print(f"[DEBUG] Response status code: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text.strip()
            print(f"[DEBUG] Raw content from GitHub: '{content}'")
            
            # This logic removes "Version: " if it exists in the file
            if "Version:" in content:
                latest_version = content.replace("Version:", "").strip()
                print(f"[DEBUG] Removed 'Version:' prefix")
            else:
                latest_version = content
            
            print(f"[DEBUG] Latest version: {latest_version}")
            print(f"[DEBUG] Current version: {CURRENT_VERSION}")
            
            # Compare the cloud version to your local CURRENT_VERSION
            if latest_version != CURRENT_VERSION:
                print(f"[DEBUG] UPDATE AVAILABLE! {CURRENT_VERSION} -> {latest_version}")
                # Use app.after to safely trigger the popup from a background thread
                app.after(0, lambda: prompt_update(latest_version))
            else:
                print(f"[DEBUG] Already on latest version")
        else:
            print(f"[DEBUG] Non-200 status code: {response.status_code}")
    except Exception as e:
        print(f"[DEBUG] Update check failed: {e}")
    
    print(f"[DEBUG] ========== UPDATE CHECK COMPLETE ==========\n")

def prompt_update(new_version):
    """Show integrated update notification window"""
    print(f"\n[DEBUG] ========== UPDATE PROMPT ==========")
    print(f"[DEBUG] Showing update dialog for version: {new_version}")
    
    # Create update window
    update_window = ctk.CTkToplevel(app)
    update_window.title("Update Available")
    update_window.geometry("500x350")
    update_window.resizable(False, False)
    update_window.transient(app)
    update_window.grab_set()
    
    # Center the update window
    update_window.update_idletasks()
    width = update_window.winfo_width()
    height = update_window.winfo_height()
    x = (update_window.winfo_screenwidth() // 2) - (width // 2)
    y = (update_window.winfo_screenheight() // 2) - (height // 2)
    update_window.geometry(f"{width}x{height}+{x}+{y}")
    
    # Main frame with less padding
    main_frame = ctk.CTkFrame(update_window, fg_color=colors["frame_bg"])
    main_frame.pack(fill="both", expand=True, padx=15, pady=15)
    
    # Title
    title_label = ctk.CTkLabel(
        main_frame,
        text="🎉 Update Available!",
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=colors["accent"]
    )
    title_label.pack(pady=(5, 15))
    
    # Version info frame
    info_frame = ctk.CTkFrame(main_frame, fg_color=colors["card_bg"], corner_radius=10)
    info_frame.pack(fill="x", padx=10, pady=10)
    
    current_label = ctk.CTkLabel(
        info_frame,
        text=f"Current Version: {CURRENT_VERSION}",
        font=ctk.CTkFont(size=13),
        text_color=colors["text"]
    )
    current_label.pack(pady=(10, 5))
    
    arrow_label = ctk.CTkLabel(
        info_frame,
        text="↓",
        font=ctk.CTkFont(size=16, weight="bold"),
        text_color=colors["accent"]
    )
    arrow_label.pack(pady=2)
    
    new_label = ctk.CTkLabel(
        info_frame,
        text=f"New Version: {new_version}",
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=colors["accent"]
    )
    new_label.pack(pady=(5, 10))
    
    # Message
    message_label = ctk.CTkLabel(
        main_frame,
        text="Would you like to open the GitHub page to download it?",
        font=ctk.CTkFont(size=12),
        text_color=colors["text"]
    )
    message_label.pack(pady=(10, 15))
    
    # Buttons frame
    button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
    button_frame.pack(fill="x", pady=(5, 10), padx=10)
    
    def download_update():
        print(f"[DEBUG] User chose to download update")
        print(f"[DEBUG] Opening GitHub page...")
        webbrowser.open("https://github.com/johanssonserlanderkevin-sys/BeamSkin-Studio")
        print(f"[DEBUG] GitHub page opened")
        update_window.destroy()
    
    def skip_update():
        print(f"[DEBUG] User declined update")
        update_window.destroy()
    
    # Download Update button
    download_btn = ctk.CTkButton(
        button_frame,
        text="Download Update",
        command=download_update,
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        text_color=colors["accent_text"],
        height=45,
        corner_radius=8,
        font=ctk.CTkFont(size=14, weight="bold")
    )
    download_btn.pack(side="left", expand=True, fill="x", padx=(0, 5))
    
    # Maybe Later button
    later_btn = ctk.CTkButton(
        button_frame,
        text="Maybe Later",
        command=skip_update,
        fg_color=colors["card_bg"],
        hover_color=colors["card_hover"],
        text_color=colors["text"],
        height=45,
        corner_radius=8,
        font=ctk.CTkFont(size=14)
    )
    later_btn.pack(side="right", expand=True, fill="x", padx=(5, 0))
    
    print(f"[DEBUG] Update window displayed")
    print(f"[DEBUG] ========== UPDATE PROMPT COMPLETE ==========\n")


# Example usage and testing function
def test_editor():
    """Test function to demonstrate usage"""
    # Example: edit_material_json("path/to/skin.materials.json", "output_folder", "mycar")
    pass


if __name__ == "__main__":
    test_editor()


def edit_jbeam_material(jbeam_path, skinname_folder, carid):
    """
    Edits the JBEAM file according to specifications:
    1. Keep only the FIRST skin entry encountered
    2. Rename it to carid_skin_skinname
    3. Update "authors" field to placeholder "Author Name"
    4. Update "name" field to placeholder "Skin Name"
    5. Update "globalSkin" to "skinname"
    6. Preserve all other fields (information.value, slotType, etc.)
    
    Note: "Author Name" and "Skin Name" are placeholders that will be replaced
    during mod generation with actual values from the Generator tab.
    """
    try:
        print(f"\n--- Starting JBEAM Edit Process ---")
        print(f"Reading JBEAM file: {jbeam_path}")
        print(f"Target Car ID: {carid}")
        print(f"Using placeholders: 'Author Name' and 'Skin Name' (will be replaced by generator)")
        
        # Read the raw file content
        with open(jbeam_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean the JBEAM content (remove comments)
        print("Cleaning JBEAM (removing comments)...")
        
        # Remove single-line comments (// ...)
        lines = content.split('\n')
        cleaned_lines = []
        for line in lines:
            if '//' in line:
                in_string = False
                escape = False
                comment_pos = -1
                for i, char in enumerate(line):
                    if escape:
                        escape = False
                        continue
                    if char == '\\':
                        escape = True
                        continue
                    if char == '"':
                        in_string = not in_string
                    if not in_string and i < len(line) - 1 and line[i:i+2] == '//':
                        comment_pos = i
                        break
                if comment_pos >= 0:
                    line = line[:comment_pos]
            cleaned_lines.append(line)
        
        content = '\n'.join(cleaned_lines)
        
        # Remove block comments (/* ... */)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        
        # Fix trailing commas before } or ]
        content = re.sub(r',(\s*[}\]])', r'\1', content)
        
        # Parse the cleaned JSON
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"ERROR: Could not parse JBEAM even after cleaning - {e}")
            print("Attempting to save cleaned version for manual inspection...")
            cleaned_path = jbeam_path + ".cleaned"
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Cleaned JBEAM saved to: {cleaned_path}")
            raise
        
        print(f"Original JBEAM contains {len(data)} entries")
        
        # STEP 1: Find all skin entries (keys containing "_skin_")
        skin_entries = []
        for key in data.keys():
            if "_skin_" in key:
                skin_entries.append((key, data[key]))
        
        if not skin_entries:
            print("WARNING: No skin entries found in JBEAM")
            return
        
        print(f"Found {len(skin_entries)} skin entries")
        
        # STEP 2: Keep only the FIRST skin entry
        first_skin_key, first_skin_value = skin_entries[0]
        print(f"\n✓ Canonical skin identified: {first_skin_key}")
        
        if len(skin_entries) > 1:
            removed_skins = [key for key, _ in skin_entries[1:]]
            print(f"✗ Removing {len(removed_skins)} other skin(s): {', '.join(removed_skins)}")
        
        # STEP 3: Create the new skin entry
        new_key = f"{carid}_skin_skinname"
        new_value = copy.deepcopy(first_skin_value)
        
        print(f"\n✓ Renaming: {first_skin_key} → {new_key}")
        
        # STEP 4: Update authors and name fields to placeholders
        if "information" in new_value and isinstance(new_value["information"], dict):
            if "authors" in new_value["information"]:
                old_author = new_value["information"]["authors"]
                new_value["information"]["authors"] = "Author Name"
                print(f"  ✓ Updated authors: '{old_author}' → 'Author Name' (placeholder)")
            
            if "name" in new_value["information"]:
                old_name = new_value["information"]["name"]
                new_value["information"]["name"] = "Skin Name"
                print(f"  ✓ Updated name: '{old_name}' → 'Skin Name' (placeholder)")
            
            # Preserve value field
            if "value" in new_value["information"]:
                print(f"  ✓ Preserved value: {new_value['information']['value']}")
        
        # STEP 5: Update globalSkin to "skinname"
        if "globalSkin" in new_value:
            old_global_skin = new_value["globalSkin"]
            new_value["globalSkin"] = "skinname"
            print(f"  ✓ Updated globalSkin: '{old_global_skin}' → 'skinname'")
        
        # STEP 6: Preserve all other fields (slotType, etc.)
        if "slotType" in new_value:
            print(f"  ✓ Preserved slotType: '{new_value['slotType']}'")
        
        # Create the filtered data with only the new skin entry
        filtered_data = {new_key: new_value}
        
        print(f"\n--- Summary ---")
        print(f"Original skins: {len(skin_entries)}")
        print(f"Final skins: 1")
        print(f"Removed: {len(skin_entries) - 1}")
        
        # Write the edited JBEAM back to the folder, keeping original filename
        jbeam_filename = os.path.basename(jbeam_path)
        output_path = os.path.join(skinname_folder, jbeam_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4)
        
        print(f"Edited JBEAM saved to: {output_path}")
        print(f"--- JBEAM Edit Complete ---\n")
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JBEAM format - {e}")
        raise Exception(f"Invalid JBEAM format: {str(e)}")
    except Exception as e:
        print(f"ERROR during JBEAM editing: {e}")
        raise


# -----------------------
# Theme System
# -----------------------
SETTINGS_FILE = "app_settings.json"

# Default settings
app_settings = {
    "theme": "dark",  # "dark" or "light"
    "first_launch": True  # Show WIP warning on first launch
}

# Load settings
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r") as f:
            app_settings = json.load(f)
    except:
        pass

def save_settings():
    """Save app settings to file"""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(app_settings, f, indent=4)




# -----------------------
# Theme System - UPDATED
# -----------------------

# Theme color definitions
THEMES = {
    "dark": {
        "app_bg": "#0a0a0a",
        "frame_bg": "#141414",
        "card_bg": "#1e1e1e",
        "card_hover": "#282828",
        "text": "#f5f5f5",
        "text_secondary": "#999999",
        "accent": "#39E09B",
        "accent_hover": "#2fc97f",
        "accent_text": "#0a0a0a",
        "tab_selected": "#1e1e1e",
        "tab_selected_hover": "#282828",
        "tab_unselected": "#141414",
        "tab_unselected_hover": "#1e1e1e",
        "border": "#2a2a2a",
        "error": "#ff4444",
        "error_hover": "#cc3636",
        "success": "#39E09B",
        "warning": "#ffa726",
        "topbar_bg": "#181818",
        "sidebar_bg": "#121212"
    },
    "light": {
        "app_bg": "#fafafa",
        "frame_bg": "#f0f0f0",
        "card_bg": "#ffffff",
        "card_hover": "#f5f5f5",
        "text": "#1a1a1a",
        "text_secondary": "#888888",
        "accent": "#39E09B",
        "accent_hover": "#2fc97f",
        "accent_text": "#0a0a0a",
        "tab_selected": "#ffffff",
        "tab_selected_hover": "#f5f5f5",
        "tab_unselected": "#f0f0f0",
        "tab_unselected_hover": "#ffffff",
        "border": "#e0e0e0",
        "error": "#ff4444",
        "error_hover": "#cc3636",
        "success": "#39E09B",
        "warning": "#ffa726",
        "topbar_bg": "#f5f5f5",
        "sidebar_bg": "#eeeeee"
    }
}
current_theme = app_settings["theme"]
colors = THEMES[current_theme]


ADDED_VEHICLES_FILE = "added_vehicles.json"
added_vehicles = {}  # carid -> carname

# Ensure save file exists
if not os.path.exists(ADDED_VEHICLES_FILE):
    with open(ADDED_VEHICLES_FILE, "w") as f:
        json.dump({}, f)

# Load existing developer-added vehicles
with open(ADDED_VEHICLES_FILE, "r") as f:
    try:
        added_vehicles = json.load(f)
    except:
        added_vehicles = {}

# DO NOT merge added_vehicles into VEHICLE_IDS
# We'll keep them separate to maintain carid -> carname mapping


# -----------------------
# Debug Mode Setup
# -----------------------
debug_mode_enabled = False
debug_window = None
debug_textbox = None

class DebugOutput(io.StringIO):
    """Custom output stream that writes to both console and debug window"""
    def __init__(self):
        super().__init__()
        self.terminal = sys.stdout
        
    def write(self, message):
        self.terminal.write(message)
        if debug_mode_enabled and debug_textbox is not None:
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                debug_textbox.insert("end", f"[{timestamp}] {message}")
                debug_textbox.see("end")
            except:
                pass
    
    def flush(self):
        self.terminal.flush()

def create_debug_window():
    """Create a separate window for debug output"""
    global debug_window, debug_textbox
    
    if debug_window is not None and debug_window.winfo_exists():
        debug_window.lift()
        return
    
    debug_window = ctk.CTkToplevel(app)
    debug_window.title("Debug Console")
    debug_window.geometry("800x600")
    debug_window.configure(fg_color=colors["app_bg"])
    
    # Header
    header_frame = ctk.CTkFrame(debug_window, corner_radius=12, fg_color=colors["frame_bg"])
    header_frame.pack(fill="x", padx=10, pady=10)
    ctk.CTkLabel(header_frame, text="Debug Console", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors["text"]).pack(side="left", padx=20, pady=10)
    
    # Clear button
    def clear_debug():
        debug_textbox.delete("0.0", "end")
        print("Debug console cleared")
    
    ctk.CTkButton(header_frame, text="Clear", width=80, command=clear_debug,
                  fg_color=colors["card_bg"], hover_color=colors["card_hover"], text_color=colors["text"]).pack(side="right", padx=10, pady=10)
    
    # Debug output textbox
    debug_textbox = ctk.CTkTextbox(debug_window, font=ctk.CTkFont(family="Consolas", size=11),
                                    fg_color=colors["frame_bg"], text_color=colors["accent"])
    debug_textbox.pack(fill="both", expand=True, padx=10, pady=(0,10))
    
    print("="*50)
    print("DEBUG MODE ENABLED")
    print("="*50)
    
    def on_debug_window_close():
        global debug_mode_enabled, debug_window
        debug_mode_enabled = False
        debug_mode_var.set(False)
        debug_window.destroy()
        debug_window = None
        print("Debug mode disabled")
    
    debug_window.protocol("WM_DELETE_WINDOW", on_debug_window_close)

def toggle_debug_mode():
    """Toggle debug mode on/off"""
    global debug_mode_enabled
    
    if debug_mode_var.get():
        debug_mode_enabled = True
        create_debug_window()
        print("Debug mode activated")
    else:
        debug_mode_enabled = False
        if debug_window is not None and debug_window.winfo_exists():
            debug_window.destroy()
        print("Debug mode deactivated")

# Redirect stdout to our custom output
sys.stdout = DebugOutput()


# -----------------------
# Hover Preview System
# -----------------------
hover_preview_window = None
hover_timer = None
current_hover_carid = None

def show_hover_preview(carid, x, y):
    """Show preview image for vehicle INSIDE the main window"""
    # 1. Get live mouse position relative to the main window
    mouse_x = app.winfo_pointerx() - app.winfo_rootx()
    mouse_y = app.winfo_pointery() - app.winfo_rooty()

    # 2. Clear previous content
    for child in preview_overlay.winfo_children():
        child.destroy()

    image_path = os.path.join("imagesforgui", "vehicles", carid, "default.jpg")
    
    # Use fallback image if preview doesn't exist
    if not os.path.exists(image_path):
        fallback_path = os.path.join("imagesforgui", "common", "imagepreview", "MissingTexture.jpg")
        if os.path.exists(fallback_path):
            image_path = fallback_path
        else:
            return

    try:
        # Load Image
        img = Image.open(image_path)
        img.thumbnail((300, 300), Image.Resampling.LANCZOS)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

        # Build UI
        header = ctk.CTkFrame(preview_overlay, fg_color=colors["accent"], height=30, corner_radius=8)
        header.pack(fill="x", padx=2, pady=2)
        ctk.CTkLabel(header, text=carid, text_color=colors["accent_text"], font=("Segoe UI", 12, "bold")).pack()
        
        img_label = ctk.CTkLabel(preview_overlay, image=photo, text="")
        img_label.pack(padx=10, pady=5)

        # 3. ADVANCED POSITIONING (The fix for bottom-clipping)
        app.update_idletasks() # Ensure window math is current
        app_w = app.winfo_width()
        app_h = app.winfo_height()
        
        # Force the overlay to calculate its own size based on the image loaded
        preview_overlay.update_idletasks()
        p_width = preview_overlay.winfo_reqwidth()
        p_height = preview_overlay.winfo_reqheight()

        # HORIZONTAL LOGIC
        # Default: 20px to the right of cursor
        pos_x = mouse_x + 20
        # If it hits the right wall, move it to the left of the cursor
        if pos_x + p_width > app_w:
            pos_x = mouse_x - p_width - 20

        # VERTICAL LOGIC (The Bottom Anchor Fix)
        # Default: 10px below the cursor
        pos_y = mouse_y + 10
        # If the bottom of the preview would go off-screen:
        if pos_y + p_height > app_h:
            # Shift the window UP so its bottom is 10px above the cursor
            pos_y = mouse_y - p_height - 10
            
        # FINAL SAFETY: Never let it go off the top (y<0) or left (x<0)
        pos_x = max(10, pos_x)
        pos_y = max(10, pos_y)

        # 4. Display
        preview_overlay.place(x=pos_x, y=pos_y)
        preview_overlay.lift()

    except Exception as e:
        print(f"Internal Preview Error: {e}")

def hide_hover_preview(calling_carid=None, force=False):
    """Hide the internal preview overlay"""
    global hover_timer, current_hover_carid
    
    # Handle the timer
    if force or calling_carid is None or current_hover_carid == calling_carid:
        if hover_timer is not None:
            app.after_cancel(hover_timer)
            hover_timer = None
            
        # This is the fix: hide the internal frame
        preview_overlay.place_forget()
        current_hover_carid = None
        return
    
    # If a specific card is leaving, but we already moved to a new card, don't hide
    if calling_carid is not None and current_hover_carid != calling_carid:
        return

    if hover_timer is not None:
        app.after_cancel(hover_timer)
        hover_timer = None
    
    if hover_preview_window is not None:
        hover_preview_window.destroy()
        hover_preview_window = None
    
    current_hover_carid = None

def schedule_hover_preview(carid, widget):
    """Schedule preview to show after a short delay"""
    global hover_timer, current_hover_carid
    
    # If we are already showing this car, do nothing
    if current_hover_carid == carid:
        return

    # Cancel any pending timers for other cars
    if hover_timer is not None:
        app.after_cancel(hover_timer)
    
    current_hover_carid = carid
    
    # Show preview after a short delay (400ms feels snappier than 1000ms)
    hover_timer = app.after(400, lambda: show_hover_preview(carid, widget.winfo_pointerx(), widget.winfo_pointery()))

    # CORRECTED CODE (The block after the def is shifted right):
def setup_robust_hover(main_card, carid):
    """
    Set up robust hover preview for a card that works on all child elements.
    Uses coordinate-based detection and recursive binding.
    """
    def is_pointer_inside(widget):
        """Math check to see if mouse is inside the card boundaries"""
        try:
            x, y = widget.winfo_pointerxy()
            root_x = widget.winfo_rootx()
            root_y = widget.winfo_rooty()
            width = widget.winfo_width()
            height = widget.winfo_height()
            return (root_x <= x <= root_x + width) and (root_y <= y <= root_y + height)
        except:
            return False
    
    def is_hovering_button(widget):
        """Check if currently hovering over a button"""
        current_widget = widget
        while current_widget:
            if isinstance(current_widget, ctk.CTkButton):
                return True
            try:
                current_widget = current_widget.master
            except:
                break
        return False

    def on_interaction(event):
        # 1. IMMEDIATE HIDE if hovering over a button (check both event widget and hierarchy)
        if isinstance(event.widget, ctk.CTkButton) or is_hovering_button(event.widget):
            hide_hover_preview(force=True)
            return

        # 2. Start timer if inside card
        if is_pointer_inside(main_card):
            main_card.configure(fg_color=colors["card_hover"])
            schedule_hover_preview(carid, main_card)

    def on_leave(event):
        # 3. Check if we actually left the whole card area
        # Add small delay to allow mouse to move to adjacent elements
        app.after(50, check_actual_leave)
    
    def check_actual_leave():
        """Delayed check to see if mouse truly left the card"""
        if not is_pointer_inside(main_card):
            main_card.configure(fg_color=colors["card_bg"])
            hide_hover_preview(calling_carid=carid)

    def bind_recursive(widget):
        """Ensures every label and frame inside the card reports back to the card"""
        widget.bind("<Enter>", on_interaction, add=True)
        widget.bind("<Motion>", on_interaction, add=True) 
        widget.bind("<Leave>", on_leave, add=True)
        for child in widget.winfo_children():
            bind_recursive(child)

    bind_recursive(main_card)

# -----------------------
# Helper function to save added vehicles
# -----------------------
def save_added_vehicles():
    """Save the current added_vehicles dict to the JSON file."""
    with open(ADDED_VEHICLES_FILE, "w") as f:
        json.dump(added_vehicles, f, indent=4)




print("Starting BeamSkin Studio...")

# -----------------------
# Setup
# -----------------------
ctk.set_appearance_mode("dark" if current_theme == "dark" else "light")
ctk.set_default_color_theme("blue")

# -----------------------
# Custom Placeholder Functions
# -----------------------
def on_entry_click(event, entry, placeholder):
    """Clear placeholder text when entry is clicked"""
    print(f"[DEBUG] Entry clicked. Current value: '{entry.get()}'")
    if entry.get() == placeholder:
        print(f"[DEBUG] Clearing placeholder: '{placeholder}'")
        entry.delete(0, "end")
        entry.insert(0, "")
        entry.configure(text_color=colors["text"])
    else:
        print(f"[DEBUG] Not clearing - value is not placeholder")

def on_focusout(event, entry, placeholder):
    """Restore placeholder text if entry is empty"""
    current_value = entry.get()
    print(f"[DEBUG] Focus out. Current value: '{current_value}'")
    if current_value == "":
        print(f"[DEBUG] Restoring placeholder: '{placeholder}'")
        entry.insert(0, placeholder)
        entry.configure(text_color="#888888")
    else:
        print(f"[DEBUG] Not restoring - entry has value")

def get_real_value(entry_widget, placeholder_text):
    """Get the real value from entry, ignoring placeholder text"""
    value = entry_widget.get()
    print(f"[DEBUG] get_real_value called. Value: '{value}', Placeholder: '{placeholder_text}'")
    if value == placeholder_text:
        print(f"[DEBUG] Returning empty string (was placeholder)")
        return ""
    print(f"[DEBUG] Returning actual value: '{value}'")
    return value


# ===========================
# MAIN APP INITIALIZATION
# ===========================
app = ctk.CTk()
app.title("BeamSkin Studio")
app.geometry("1600x1000")
app.minsize(1100, 1000)
app.configure(fg_color=colors["app_bg"])

# ===========================
# VARIABLE DECLARATIONS (Before UI)
# ===========================
mod_name_var = ctk.StringVar()
skin_name_var = ctk.StringVar()
author_var = ctk.StringVar()
dds_path_var = ctk.StringVar()
vehicle_display_var = ctk.StringVar()
output_mode_var = ctk.StringVar(value="steam")
custom_output_var = ctk.StringVar()
dds_preview_label = None
progress_bar = None
export_status_label = None
vehicle_search_var = ctk.StringVar()
carlist_search_var = ctk.StringVar()

# Global variables
selected_carid = None
selected_display_name = None
vehicle_buttons = []
vehicle_panel_visible = False
skin_inputs = []
carlist_items = []

# Project data
project_data = {
    "mod_name": "",
    "author": "",
    "cars": {}
}
selected_car_for_skin = None
current_project_widgets = []


# Additional UI variables
notification_label = None
custom_output_frame = None
dev_list_items = []
dev_search_var = ctk.StringVar()

# Sidebar variables
sidebar_vehicle_buttons = []
sidebar_search_var = ctk.StringVar()
expanded_vehicle_carid = None  # Track which vehicle is expanded

# ===========================
# TOP MENU BAR (Mods Studio 2 Style)
# ===========================
topbar = ctk.CTkFrame(app, height=60, fg_color=colors["topbar_bg"], corner_radius=0)
topbar.pack(fill="x", side="top")
topbar.pack_propagate(False)

# Title
title_container = ctk.CTkFrame(topbar, fg_color="transparent")
title_container.pack(side="left", padx=25, pady=12)

ctk.CTkLabel(
    title_container, 
    text="BeamSkin Studio", 
    font=ctk.CTkFont(size=20, weight="bold"), 
    text_color=colors["accent"]
).pack(anchor="w")

ctk.CTkLabel(
    title_container, 
    text="Professional Skin Modding Tool", 
    font=ctk.CTkFont(size=10), 
    text_color=colors["text_secondary"]
).pack(anchor="w")

# Menu buttons
menu_frame = ctk.CTkFrame(topbar, fg_color="transparent")
menu_frame.pack(side="left", padx=40)

# Generate button (top right) - using lambda to delay function lookup
generate_button_topbar = ctk.CTkButton(
    topbar,
    text="✨ Generate Mod",
    command=lambda: generate_multi_skin_mod(),
    height=40,
    width=150,
    fg_color=colors["accent"],
    hover_color=colors["accent_hover"],
    text_color=colors["accent_text"],
    corner_radius=10,
    font=ctk.CTkFont(size=14, weight="bold")
)
generate_button_topbar.pack(side="right", padx=25)

menu_buttons = {}

def switch_view(view_name):
    """Switch between main views"""
    # Update button colors
    for name, btn in menu_buttons.items():
        if name == view_name:
            btn.configure(fg_color=colors["accent"], text_color=colors["accent_text"])
        else:
            btn.configure(fg_color="transparent", text_color=colors["text_secondary"])
    
    # Show/hide generate button based on view
    if view_name == "generator":
        generate_button_topbar.pack(side="right", padx=25)
    else:
        generate_button_topbar.pack_forget()
    
    # First, hide all content areas
    main_content_area.pack_forget()
    howto_tab.pack_forget()
    carlist_tab.pack_forget()
    settings_tab.pack_forget()
    about_tab.pack_forget()
    sidebar.pack_forget()
    if developer_tab is not None:
        developer_tab.pack_forget()
    
    # Now show the appropriate view
    if view_name == "generator":
        # Generator view: show sidebar + main content
        sidebar.pack(fill="y", side="left")
        main_content_area.pack(fill="both", expand=True, side="left")
    elif view_name == "howto":
        howto_tab.pack(fill="both", expand=True)
    elif view_name == "carlist":
        carlist_tab.pack(fill="both", expand=True)
    elif view_name == "settings":
        settings_tab.pack(fill="both", expand=True)
    elif view_name == "about":
        about_tab.pack(fill="both", expand=True)
    elif view_name == "developer":
        if developer_tab is not None:
            developer_tab.pack(fill="both", expand=True)
    
    # CRITICAL FIX: Refresh scroll bindings after tab switch
    app.update_idletasks()  # Ensure all widgets are ready
    app.after(50, setup_universal_scroll_handler)  # Small delay to ensure everything is loaded



for btn_text, view_name in [("Generator", "generator"), ("How to Use", "howto"), 
                             ("Car List", "carlist"), ("Settings", "settings"), ("About", "about")]:
    is_first = (view_name == "generator")
    btn = ctk.CTkButton(
        menu_frame,
        text=f"   {btn_text}   ",
        width=110,
        height=36,
        fg_color=colors["accent"] if is_first else "transparent",
        hover_color=colors["accent_hover"] if is_first else colors["card_hover"],
        text_color=colors["accent_text"] if is_first else colors["text_secondary"],
        corner_radius=8,
        font=ctk.CTkFont(size=12, weight="bold" if is_first else "normal"),
        command=lambda v=view_name: switch_view(v)
    )
    btn.pack(side="left", padx=3)
    menu_buttons[view_name] = btn

# ===========================
# NOTIFICATION SYSTEM
# ===========================
notification_frame = ctk.CTkFrame(app, fg_color="transparent")
# Don't pack it - we'll use place() to overlay it

# ===========================
# MAIN CONTAINER
# ===========================
main_container = ctk.CTkFrame(app, fg_color=colors["app_bg"])
main_container.pack(fill="both", expand=True)

# ===========================
# LEFT SIDEBAR (Mods Studio 2 Style)
# ===========================
sidebar = ctk.CTkFrame(main_container, width=280, fg_color=colors["sidebar_bg"], corner_radius=0)
sidebar.pack(fill="y", side="left")
sidebar.pack_propagate(False)

# Sidebar header - PROJECT SETTINGS
sidebar_header = ctk.CTkFrame(sidebar, height=40, fg_color="transparent")
sidebar_header.pack(fill="x", padx=15, pady=(10, 0))
sidebar_header.pack_propagate(False)

ctk.CTkLabel(
    sidebar_header,
    text="PROJECT SETTINGS",
    font=ctk.CTkFont(size=13, weight="bold"),
    text_color=colors["text_secondary"],
    anchor="w"
).pack(side="top", fill="x", pady=(5, 0))

# ===========================
# PROJECT INFO (Sidebar)
# ===========================
# ZIP Name
zip_name_label = ctk.CTkLabel(
    sidebar,
    text="ZIP Name",
    font=ctk.CTkFont(size=11, weight="bold"),
    text_color=colors["text"],
    anchor="w"
)
zip_name_label.pack(fill="x", padx=15, pady=(5, 5))

mod_name_entry_sidebar = ctk.CTkEntry(
    sidebar,
    textvariable=mod_name_var,
    height=36,
    fg_color=colors["frame_bg"],
    border_color=colors["border"],
    text_color="#888888"
)
mod_name_entry_sidebar.pack(fill="x", padx=15, pady=(0, 10))

# Setup custom placeholder
placeholder_mod = "Enter mod name..."
mod_name_entry_sidebar.insert(0, placeholder_mod)
mod_name_entry_sidebar.bind("<FocusIn>", lambda e: on_entry_click(e, mod_name_entry_sidebar, placeholder_mod))
mod_name_entry_sidebar.bind("<FocusOut>", lambda e: on_focusout(e, mod_name_entry_sidebar, placeholder_mod))

# Author Name
author_label = ctk.CTkLabel(
    sidebar,
    text="Author",
    font=ctk.CTkFont(size=11, weight="bold"),
    text_color=colors["text"],
    anchor="w"
)
author_label.pack(fill="x", padx=15, pady=(0, 5))

author_entry_sidebar = ctk.CTkEntry(
    sidebar,
    textvariable=author_var,
    height=36,
    fg_color=colors["frame_bg"],
    border_color=colors["border"],
    text_color="#888888"
)
author_entry_sidebar.pack(fill="x", padx=15, pady=(0, 15))

# Setup custom placeholder
placeholder_author = "Your name..."
author_entry_sidebar.insert(0, placeholder_author)
author_entry_sidebar.bind("<FocusIn>", lambda e: on_entry_click(e, author_entry_sidebar, placeholder_author))
author_entry_sidebar.bind("<FocusOut>", lambda e: on_focusout(e, author_entry_sidebar, placeholder_author))

# Output Location in Sidebar
output_label = ctk.CTkLabel(
    sidebar,
    text="Output Location",
    font=ctk.CTkFont(size=11, weight="bold"),
    text_color=colors["text"],
    anchor="w"
)
output_label.pack(fill="x", padx=15, pady=(0, 5))

# Steam option (compact for sidebar)
steam_option_sidebar = ctk.CTkFrame(sidebar, fg_color=colors["frame_bg"], corner_radius=8, height=45)
steam_option_sidebar.pack(fill="x", padx=15, pady=(0, 5))
steam_option_sidebar.pack_propagate(False)

steam_radio_sidebar = ctk.CTkRadioButton(
    steam_option_sidebar,
    text="🎮 Steam Workshop",
    variable=output_mode_var,
    value="steam",
    fg_color=colors["accent"],
    hover_color=colors["accent_hover"],
    text_color=colors["text"],
    font=ctk.CTkFont(size=11)
)
steam_radio_sidebar.pack(side="left", padx=10, pady=10)

# Custom location option (compact for sidebar)
custom_option_sidebar = ctk.CTkFrame(sidebar, fg_color=colors["frame_bg"], corner_radius=8, height=45)
custom_option_sidebar.pack(fill="x", padx=15, pady=(0, 5))
custom_option_sidebar.pack_propagate(False)

custom_radio_sidebar = ctk.CTkRadioButton(
    custom_option_sidebar,
    text="📁 Custom Location",
    variable=output_mode_var,
    value="custom",
    fg_color=colors["accent"],
    hover_color=colors["accent_hover"],
    text_color=colors["text"],
    font=ctk.CTkFont(size=11)
)
custom_radio_sidebar.pack(side="left", padx=10, pady=10)

# Custom output path entry (shown when custom is selected) - APPEARS RIGHT AFTER CUSTOM OPTION
custom_output_frame = ctk.CTkFrame(sidebar, fg_color="transparent")

custom_output_entry = ctk.CTkEntry(
    custom_output_frame,
    textvariable=custom_output_var,
    placeholder_text="Select folder...",
    placeholder_text_color="#888888",
    state="readonly",
    height=32,
    fg_color=colors["frame_bg"],
    border_color=colors["border"],
    text_color=colors["text"],
    font=ctk.CTkFont(size=10)
)
custom_output_entry.pack(side="left", fill="x", expand=True, padx=(15, 5))

custom_browse_btn = ctk.CTkButton(
    custom_output_frame,
    text="📁",
    width=32,
    height=32,
    command=lambda: select_custom_output(),
    fg_color=colors["card_bg"],
    hover_color=colors["card_hover"],
    text_color=colors["text"],
    corner_radius=8,
    font=ctk.CTkFont(size=14)
)
custom_browse_btn.pack(side="right", padx=(0, 15))

# Update the output mode change handler
def update_output_mode():
    if output_mode_var.get() == "custom":
        custom_output_frame.pack(fill="x", pady=(0, 10), after=custom_option_sidebar)
    else:
        custom_output_frame.pack_forget()

# Bind to the variable
output_mode_var.trace_add("write", lambda *args: update_output_mode())

# Separator line
separator = ctk.CTkFrame(sidebar, height=2, fg_color=colors["border"])
separator.pack(fill="x", padx=15, pady=(10, 10))

# Vehicles label
vehicles_label = ctk.CTkLabel(
    sidebar,
    text="Vehicles",
    font=ctk.CTkFont(size=11, weight="bold"),
    text_color=colors["text"],
    anchor="w"
)
vehicles_label.pack(fill="x", padx=15, pady=(0, 5))

# Search box
sidebar_search_entry = ctk.CTkEntry(
    sidebar,
    textvariable=sidebar_search_var,
    height=32,
    fg_color=colors["frame_bg"],
    border_color=colors["border"],
    text_color="#888888"
)
sidebar_search_entry.pack(fill="x", padx=15, pady=(0, 10))

# Setup custom placeholder
placeholder_sidebar_search = "Search vehicles..."
sidebar_search_entry.insert(0, placeholder_sidebar_search)
sidebar_search_entry.bind("<FocusIn>", lambda e: on_entry_click(e, sidebar_search_entry, placeholder_sidebar_search))
sidebar_search_entry.bind("<FocusOut>", lambda e: on_focusout(e, sidebar_search_entry, placeholder_sidebar_search))

# Scrollable vehicle list
sidebar_scroll = ctk.CTkScrollableFrame(
    sidebar,
    fg_color="transparent",
    scrollbar_button_color=colors["card_bg"],
    scrollbar_button_hover_color=colors["card_hover"]
)
sidebar_scroll.pack(fill="both", expand=True, padx=10, pady=10)

def update_sidebar_search(*args):
    """Filter sidebar vehicles"""
    query = get_real_value(sidebar_search_entry, "Search vehicles...").lower()
    for container_frame, carid, display_name, add_btn_frame in sidebar_vehicle_buttons:
        container_frame.pack_forget()
        if not query or query in carid.lower() or query in display_name.lower():
            container_frame.pack(fill="x", pady=2, padx=0)
    try:
        sidebar_scroll._parent_canvas.yview_moveto(0)
    except:
        pass

sidebar_search_var.trace_add("write", update_sidebar_search)

# ===========================
# MAIN CONTENT AREA
# ===========================
main_content_area = ctk.CTkFrame(main_container, fg_color=colors["app_bg"])
main_content_area.pack(fill="both", expand=True, side="left")

# Generator tab IS the main content area
generator_tab = main_content_area

# Other tabs (full width, no sidebar)
howto_tab = ctk.CTkFrame(main_container, fg_color=colors["app_bg"])
carlist_tab = ctk.CTkFrame(main_container, fg_color=colors["app_bg"])
settings_tab = ctk.CTkFrame(main_container, fg_color=colors["app_bg"])
about_tab = ctk.CTkFrame(main_container, fg_color=colors["app_bg"])

preview_overlay = ctk.CTkFrame(
    app, 
    fg_color=colors["card_bg"], 
    border_color=colors["accent"], 
    border_width=2,
    corner_radius=10)

# ===========================
# HELPER FUNCTIONS
# ===========================
def select_dds():
    path = filedialog.askopenfilename(title="Select DDS File", filetypes=[("DDS Files", "*.dds")])
    if path:
        dds_path_var.set(path)
        load_dds_preview(path)
        print(f"DDS file selected: {path}")

def load_dds_preview(file_path):
    global dds_preview_label
    try:
        img = Image.open(file_path)
        w, h = img.size
        print(f"DDS image loaded: {w}x{h}")
        max_size = 200
        if w > h:
            new_w = max_size
            new_h = int(max_size * (h / w))
        else:
            new_h = max_size
            new_w = int(max_size * (w / h))
        img.thumbnail((new_w, new_h), Image.Resampling.LANCZOS)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(new_w, new_h))
        if dds_preview_label:
            dds_preview_label.configure(image=photo, text="")
            dds_preview_label.image = photo
    except Exception as e:
        print(f"Failed to load DDS preview: {e}")
        if dds_preview_label:
            dds_preview_label.configure(text="Preview\nUnavailable", image=None)

def select_custom_output():
    folder = filedialog.askdirectory(title="Select Output Directory")
    if folder:
        custom_output_var.set(folder)
        output_mode_var.set("custom")
        print(f"Custom output directory selected: {folder}")

def update_progress(value):
    if progress_bar and progress_bar.winfo_ismapped():
        progress_bar.set(value)

def bind_tree(widget, event, callback):
    widget.bind(event, callback)
    for child in widget.winfo_children():
        bind_tree(child, event, callback)

def _on_vehicle_mousewheel(event):
    try:
        scroll_amount = int(-1 * (event.delta / 120) * 15)
        vehicle_scroll_frame._parent_canvas.yview_scroll(scroll_amount, "units")
        return "break"
    except:
        pass

# ===========================
# ADDITIONAL FUNCTIONS FROM ORIGINAL
# ===========================

# === toggle_vehicle_panel ===
def toggle_vehicle_panel():
    global vehicle_panel_visible
    if vehicle_panel_visible:
        vehicle_panel.pack_forget()
        vehicle_panel_visible = False
        select_vehicle_button.configure(
            text="Select Vehicle",
            fg_color=colors["card_bg"],
            hover_color=colors["card_hover"]
        )
    else:
        vehicle_panel.pack(fill="x", padx=10, pady=(0,10), after=vehicle_display_entry)
        vehicle_panel_visible = True
        vehicle_search_entry.focus_set()
        select_vehicle_button.configure(
            text="Close",
            fg_color=colors["error"],
            hover_color=colors["error_hover"]
        )



# === select_vehicle ===
def select_vehicle(carid):
    global selected_carid
    
    # Store the actual carid globally
    selected_carid = carid
    
    # Find and display the car name
    display_name = carid
    for btn, cid, dname in vehicle_buttons:
        if cid == carid:
            display_name = dname
            break
    
    print(f"Vehicle selected: {display_name} (ID: {carid})")
    vehicle_display_var.set(display_name)  # Show the display name in UI
    
    # Update button colors
    for btn, cid, dname in vehicle_buttons:
        btn.configure(fg_color=colors["card_bg"] if cid != carid else "blue")
    
    toggle_vehicle_panel()



# === update_vehicle_list ===
def update_vehicle_list(*args):
    query = vehicle_search_var.get().lower()
    for btn, carid, display_name in vehicle_buttons:
        btn.master.pack_forget()
        if query in carid.lower() or query in display_name.lower():
            btn.master.pack(fill="x", pady=3, padx=5)
    vehicle_scroll_frame._parent_canvas.yview_moveto(0)



# === clear_project ===
def clear_project():
    """Clear the current project"""
    global project_data, selected_car_for_skin
    project_data = {
        "mod_name": "",
        "author": "",
        "cars": {}
    }
    selected_car_for_skin = None
    mod_name_var.set("")
    author_var.set("")
    skin_name_var.set("")
    dds_path_var.set("")
    dds_preview_label.configure(text="Preview", image=None)
    refresh_project_display()
    show_notification("Project cleared", "info", 2000)



# === save_project ===
def save_project():
    """Save the current project to a file"""
    global project_data
    
    # Save current inputs before saving
    if selected_car_for_skin:
        save_current_car_inputs()
    
    # Update project data with current form values
    project_data["mod_name"] = get_real_value(mod_name_entry_sidebar, "Enter mod name...")
    project_data["author"] = get_real_value(author_entry_sidebar, "Your name...")
    
    if not project_data["cars"]:
        show_notification("No cars in project to save", "warning", 3000)
        return
    
    # Ask for save location
    file_path = filedialog.asksaveasfilename(
        title="Save Project",
        defaultextension=".bsproject",
        filetypes=[("BeamSkin Project", "*.bsproject"), ("All Files", "*.*")]
    )
    
    if file_path:
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(project_data, f, indent=4)
            show_notification(f"✓ Project saved to {os.path.basename(file_path)}", "success", 3000)
            print(f"Project saved to: {file_path}")
        except Exception as e:
            show_notification(f"Failed to save project: {str(e)}", "error", 4000)
            print(f"ERROR saving project: {e}")



# === load_project ===
def load_project():
    """Load a project from a file"""
    global project_data, selected_car_for_skin
    
    # Ask for file to load
    file_path = filedialog.askopenfilename(
        title="Load Project",
        filetypes=[("BeamSkin Project", "*.bsproject"), ("All Files", "*.*")]
    )
    
    if file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                loaded_data = json.load(f)
            
            # Validate loaded data
            if "cars" not in loaded_data:
                show_notification("Invalid project file", "error", 3000)
                return
            
            # Check if all DDS files still exist
            missing_files = []
            for car_id, car_info in loaded_data["cars"].items():
                for skin in car_info.get("skins", []):
                    dds_path = skin.get("dds_path", "")
                    if dds_path and not os.path.exists(dds_path):
                        # Get car name for better error message
                        base_carid = car_info.get("base_carid", car_id)
                        car_name = VEHICLE_IDS.get(base_carid, base_carid)
                        for cid, cname in car_id_list:
                            if cid == base_carid:
                                car_name = cname
                                break
                        
                        missing_files.append({
                            "car": car_name,
                            "car_id": car_id,
                            "skin": skin.get("name", "Unknown"),
                            "path": dds_path
                        })
            
            # If there are missing files, show error and don't load
            if missing_files:
                error_message = "Cannot load project - Missing DDS files:\n\n"
                for missing in missing_files:
                    error_message += f"• {missing['car']} - Skin '{missing['skin']}':\n  {missing['path']}\n\n"
                
                messagebox.showerror(
                    "Missing Files",
                    error_message.strip()
                )
                print(f"Project load failed - Missing files:")
                for missing in missing_files:
                    print(f"  {missing['car']} ({missing['car_id']}) - {missing['skin']}: {missing['path']}")
                return
            
            # Load the project
            project_data = loaded_data
            selected_car_for_skin = None
            
            # Update form fields
            mod_name_var.set(project_data.get("mod_name", ""))
            author_var.set(project_data.get("author", ""))
            skin_name_var.set("")
            dds_path_var.set("")
            dds_preview_label.configure(text="Preview", image=None)
            
            # Refresh display
            refresh_project_display()
            
            car_count = len(project_data["cars"])
            total_skins = sum(len(car_info['skins']) for car_info in project_data['cars'].values())
            show_notification(f"✓ Loaded project: {car_count} cars, {total_skins} skins", "success", 4000)
            print(f"Project loaded from: {file_path}")
            
        except Exception as e:
            show_notification(f"Failed to load project: {str(e)}", "error", 4000)
            print(f"ERROR loading project: {e}")



# === add_car_to_project ===
def add_car_to_project():
    """Add selected car to the project (prevents duplicates)"""
    global selected_car_for_skin
    
    print(f"\n[DEBUG] ========== ADD CAR TO PROJECT ==========")
    print(f"[DEBUG] Selected car ID: {selected_carid}")
    print(f"[DEBUG] Current project cars: {list(project_data['cars'].keys())}")
    
    if not selected_carid:
        print(f"[DEBUG] ERROR: No car selected")
        show_notification("Please select a vehicle first", "error")
        return
    
    # Check if this car is already in the project
    base_carid = selected_carid
    print(f"[DEBUG] Base car ID: {base_carid}")
    
    # Check all cars in project to see if this base_carid exists
    for car_instance_id, car_data in project_data["cars"].items():
        existing_base_carid = car_data.get("base_carid", car_instance_id)
        print(f"[DEBUG] Checking existing car: {car_instance_id}, base: {existing_base_carid}")
        if existing_base_carid == base_carid:
            # Car already exists in project
            car_name = VEHICLE_IDS.get(base_carid, base_carid)
            for cid, cname in car_id_list:
                if cid == base_carid:
                    car_name = cname
                    break
            print(f"[DEBUG] Car already exists: {car_name}")
            show_notification(f"'{car_name}' is already in the project", "warning", 2000)
            return
    
    # Add car with empty skins list and temp input fields
    car_instance_id = base_carid
    print(f"[DEBUG] Adding car with instance ID: {car_instance_id}")
    project_data["cars"][car_instance_id] = {
        "base_carid": base_carid,  # Store original carid for generation
        "skins": [],
        "temp_skin_name": "",
        "temp_dds_path": ""
    }
    selected_car_for_skin = car_instance_id
    print(f"[DEBUG] Selected car for skin: {selected_car_for_skin}")
    
    # Get car name
    car_name = VEHICLE_IDS.get(base_carid, base_carid)
    for cid, cname in car_id_list:
        if cid == base_carid:
            car_name = cname
            break
    
    print(f"[DEBUG] Car name: {car_name}")
    print(f"[DEBUG] Updated project cars: {list(project_data['cars'].keys())}")
    show_notification(f"✓ Added '{car_name}' to project", "success", 2000)
    
    print(f"[DEBUG] Refreshing project display...")
    refresh_project_display()
    print(f"[DEBUG] Loading car inputs...")
    load_car_inputs(car_instance_id)
    print(f"[DEBUG] ========== ADD CAR COMPLETE ==========\n")




# === remove_car_from_project ===
def remove_car_from_project(carid):
    """Remove a car from the project"""
    global selected_car_for_skin
    
    if carid in project_data["cars"]:
        del project_data["cars"][carid]
        
        if selected_car_for_skin == carid:
            selected_car_for_skin = None
            # Clear inputs when removing selected car
            skin_name_var.set("")
            dds_path_var.set("")
            dds_preview_label.configure(text="Preview", image=None)
        
        show_notification(f"Removed '{carid}' from project", "info", 2000)
        refresh_project_display()



# === select_car_for_skin ===
def select_car_for_skin(carid):
    """Select a car to add skins to"""
    global selected_car_for_skin
    
    # Save current car's inputs before switching
    if selected_car_for_skin:
        save_current_car_inputs()
    
    selected_car_for_skin = carid
    
    # Load the new car's inputs
    load_car_inputs(carid)
    
    refresh_project_display()
    
    # No notification - silent selection



# === save_current_car_inputs ===
def save_current_car_inputs():
    """Save current input values to the selected car's temp storage"""
    if selected_car_for_skin and selected_car_for_skin in project_data["cars"]:
        project_data["cars"][selected_car_for_skin]["temp_skin_name"] = skin_name_var.get()
        project_data["cars"][selected_car_for_skin]["temp_dds_path"] = dds_path_var.get()



# === load_car_inputs ===
def load_car_inputs(carid):
    """Load saved input values for the specified car"""
    if carid in project_data["cars"]:
        skin_name_var.set(project_data["cars"][carid]["temp_skin_name"])
        dds_path_var.set(project_data["cars"][carid]["temp_dds_path"])
        
        # Update DDS preview
        if project_data["cars"][carid]["temp_dds_path"]:
            load_dds_preview(project_data["cars"][carid]["temp_dds_path"])
        else:
            dds_preview_label.configure(text="Preview", image=None)



# === add_skin_to_car ===
def add_skin_to_car():
    """Add a skin to the currently selected car"""
    if not selected_car_for_skin:
        show_notification("Please select a car from the project first", "error")
        return
    
    skin_name = skin_name_var.get().strip()
    dds_path = dds_path_var.get().strip()
    
    if not skin_name:
        show_notification("Please enter a skin name", "error")
        return
    
    if not dds_path:
        show_notification("Please select a DDS file", "error")
        return
    
    # Add skin to the selected car
    project_data["cars"][selected_car_for_skin]["skins"].append({
        "name": skin_name,
        "dds_path": dds_path
    })
    
    # Clear inputs for this car
    skin_name_var.set("")
    dds_path_var.set("")
    project_data["cars"][selected_car_for_skin]["temp_skin_name"] = ""
    project_data["cars"][selected_car_for_skin]["temp_dds_path"] = ""
    dds_preview_label.configure(text="Preview", image=None)
    
    show_notification(f"✓ Added skin '{skin_name}' to {selected_car_for_skin}", "success", 2000)
    refresh_project_display()



# === remove_skin_from_car ===
def remove_skin_from_car(carid, skin_index):
    """Remove a skin from a car"""
    if carid in project_data["cars"]:
        skin = project_data["cars"][carid]["skins"][skin_index]
        project_data["cars"][carid]["skins"].pop(skin_index)
        show_notification(f"Removed skin '{skin['name']}' from {carid}", "info", 2000)
        refresh_project_display()



# === refresh_project_display ===
def refresh_project_display():
    """Refresh the project overview display"""
    print(f"\n[DEBUG] ========== REFRESH PROJECT DISPLAY ==========")
    print(f"[DEBUG] Current project data: {list(project_data['cars'].keys())}")
    
    # Clear existing widgets
    for widget in project_overview_frame.winfo_children():
        widget.destroy()
    print(f"[DEBUG] Cleared existing widgets")
    
    if not project_data["cars"]:
        print(f"[DEBUG] No cars in project - showing empty state")
        empty_state = ctk.CTkFrame(project_overview_frame, fg_color="transparent")
        empty_state.pack(expand=True, pady=40)
        
        ctk.CTkLabel(
            empty_state,
            text="📦",
            font=ctk.CTkFont(size=48)
        ).pack()
        
        ctk.CTkLabel(
            empty_state,
            text="No cars added yet",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors["text"]
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            empty_state,
            text="Select a vehicle and click 'Add to Project' to get started",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"]
        ).pack()
        print(f"[DEBUG] ========== REFRESH COMPLETE (EMPTY) ==========\n")
        return
    
    # Get search query
    search_query = get_real_value(project_search_entry, "🔍 Search cars...").lower().strip()
    print(f"[DEBUG] Search query: '{search_query}'")
    
    # Filter cars based on search
    filtered_cars = []
    for car_instance_id, car_info in project_data["cars"].items():
        base_carid = car_info.get("base_carid", car_instance_id)
        car_name = VEHICLE_IDS.get(base_carid, base_carid)
        for cid, cname in car_id_list:
            if cid == base_carid:
                car_name = cname
                break
        
        # Check if search matches car name or ID
        if not search_query or search_query in car_name.lower() or search_query in base_carid.lower():
            filtered_cars.append((car_instance_id, car_info, base_carid, car_name))
    
    print(f"[DEBUG] Filtered {len(filtered_cars)} cars from {len(project_data['cars'])} total")
    print(f"[DEBUG] Filtered car IDs: {[c[0] for c in filtered_cars]}")
    
    # Show "no results" if search filtered everything out
    if not filtered_cars:
        print(f"[DEBUG] No cars match search query")
        no_results = ctk.CTkFrame(project_overview_frame, fg_color="transparent")
        no_results.pack(expand=True, pady=40)
        
        ctk.CTkLabel(
            no_results,
            text="🔍",
            font=ctk.CTkFont(size=48)
        ).pack()
        
        ctk.CTkLabel(
            no_results,
            text="No cars found",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors["text"]
        ).pack(pady=(10, 5))
        
        ctk.CTkLabel(
            no_results,
            text=f"No cars match '{search_query}'",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"]
        ).pack()
        print(f"[DEBUG] ========== REFRESH COMPLETE (NO RESULTS) ==========\n")
        return
    
    # Display filtered cars in 2-column grid
    print(f"[DEBUG] Creating car cards in grid layout...")
    row_frame = None
    for index, (car_instance_id, car_info, base_carid, car_name) in enumerate(filtered_cars):
        print(f"[DEBUG] Creating card #{index+1}: {car_instance_id} ({car_name})")
        # Create new row frame every 2 cars
        if index % 2 == 0:
            row_frame = ctk.CTkFrame(project_overview_frame, fg_color="transparent")
            row_frame.pack(fill="x", pady=3)
            # Configure grid columns to be equal width
            row_frame.grid_columnconfigure(0, weight=1)
            row_frame.grid_columnconfigure(1, weight=1)
        
        # Add instance number if this is a duplicate
        display_name = car_name
        if "_" in car_instance_id and car_instance_id != base_carid:
            instance_num = car_instance_id.split("_")[-1]
            display_name = f"{car_name} (Instance #{instance_num})"
        
        # Determine column (0 or 1)
        column = index % 2
        
        # Modern car card
        is_selected = (selected_car_for_skin == car_instance_id)
        
        car_card = ctk.CTkFrame(
            row_frame,
            corner_radius=10,
            fg_color=colors["accent"] if is_selected else colors["card_bg"],
            border_width=2 if is_selected else 1,
            border_color=colors["accent"] if is_selected else colors["border"],
            cursor="hand2"
        )
        car_card.grid(row=0, column=column, sticky="ew", padx=3)
        
        # Make entire card clickable
        car_card.bind("<Button-1>", lambda e, c=car_instance_id: select_car_for_skin(c))
        
        # Car header with modern layout
        car_header = ctk.CTkFrame(car_card, fg_color="transparent", cursor="hand2")
        car_header.pack(fill="x", padx=10, pady=8)
        car_header.bind("<Button-1>", lambda e, c=car_instance_id: select_car_for_skin(c))
        
        # Left side: Icon + Info
        left_side = ctk.CTkFrame(car_header, fg_color="transparent", cursor="hand2")
        left_side.pack(side="left", fill="x", expand=True)
        left_side.bind("<Button-1>", lambda e, c=car_instance_id: select_car_for_skin(c))
        
        ctk.CTkLabel(
            left_side,
            text="🚗",
            font=ctk.CTkFont(size=18),
            cursor="hand2"
        ).pack(side="left", padx=(0, 8))
        
        info_container = ctk.CTkFrame(left_side, fg_color="transparent", cursor="hand2")
        info_container.pack(side="left", fill="x", expand=True)
        info_container.bind("<Button-1>", lambda e, c=car_instance_id: select_car_for_skin(c))
        
        car_label = ctk.CTkLabel(
            info_container,
            text=display_name,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=colors["accent_text"] if is_selected else colors["text"],
            anchor="w",
            cursor="hand2"
        )
        car_label.pack(anchor="w")
        car_label.bind("<Button-1>", lambda e, c=car_instance_id: select_car_for_skin(c))
        
        id_label = ctk.CTkLabel(
            info_container,
            text=f"ID: {base_carid} • {len(car_info['skins'])} skin(s)",
            font=ctk.CTkFont(size=10),
            text_color=colors["accent_text"] if is_selected else colors["text_secondary"],
            anchor="w",
            cursor="hand2"
        )
        id_label.pack(anchor="w")
        id_label.bind("<Button-1>", lambda e, c=car_instance_id: select_car_for_skin(c))
        
        # Right side: Buttons
        button_container = ctk.CTkFrame(car_header, fg_color="transparent")
        button_container.pack(side="right")
        
        # Selected indicator
        if is_selected:
            ctk.CTkLabel(
                button_container,
                text="● Selected",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=colors["accent_text"]
            ).pack(side="left", padx=(0, 8))
        
        # Remove button
        remove_car_btn = ctk.CTkButton(
            button_container,
            text="✕",
            width=28,
            height=28,
            fg_color=colors["error"],
            hover_color=colors["error_hover"],
            text_color="white",
            corner_radius=6,
            font=ctk.CTkFont(size=14, weight="bold"),
            command=lambda c=car_instance_id: remove_car_from_project(c)
        )
        remove_car_btn.pack(side="right")
        
        # Skins list with modern design
        if car_info["skins"]:
            skins_container = ctk.CTkFrame(
                car_card,
                fg_color=colors["frame_bg"] if not is_selected else colors["accent_hover"],
                corner_radius=8
            )
            skins_container.pack(fill="x", padx=10, pady=(0, 8))
            
            for idx, skin in enumerate(car_info["skins"]):
                skin_row = ctk.CTkFrame(
                    skins_container,
                    fg_color="transparent",
                    height=32
                )
                skin_row.pack(fill="x", padx=6, pady=2)
                
                ctk.CTkLabel(
                    skin_row,
                    text="🎨",
                    font=ctk.CTkFont(size=12)
                ).pack(side="left", padx=(4, 6))
                
                skin_label = ctk.CTkLabel(
                    skin_row,
                    text=skin['name'],
                    text_color=colors["text"],
                    anchor="w",
                    font=ctk.CTkFont(size=11)
                )
                skin_label.pack(side="left", fill="x", expand=True)
                
                remove_skin_btn = ctk.CTkButton(
                    skin_row,
                    text="✕",
                    width=24,
                    height=24,
                    fg_color=colors["error"],
                    hover_color=colors["error_hover"],
                    text_color="white",
                    font=ctk.CTkFont(size=12),
                    corner_radius=6,
                    command=lambda c=car_instance_id, i=idx: remove_skin_from_car(c, i)
                )
                remove_skin_btn.pack(side="right", padx=4)
    
    # Update the current car label
    update_current_car_label()
    print(f"[DEBUG] ========== REFRESH COMPLETE (SUCCESS - {len(filtered_cars)} cars displayed) ==========\n")



# === generate_multi_skin_mod ===
def generate_multi_skin_mod():
    """Generate the mod with all cars and skins"""
    global project_data
    
    print("\n" + "="*50)
    print("MULTI-SKIN MOD GENERATION INITIATED")
    print("="*50)
    
    # Validation
    mod_name = get_real_value(mod_name_entry_sidebar, "Enter mod name...").strip()
    author_name = get_real_value(author_entry_sidebar, "Your name...").strip()
    
    if not mod_name:
        show_notification("Please enter a ZIP name", "error")
        return
    
    if not project_data["cars"]:
        show_notification("Please add at least one car to the project", "error")
        return
    
    # Check if all cars have at least one skin
    cars_without_skins = []
    for carid, car_info in project_data["cars"].items():
        if not car_info["skins"]:
            cars_without_skins.append(carid)
    
    if cars_without_skins:
        show_notification(f"Please add skins to: {', '.join(cars_without_skins)}", "error", 4000)
        return
    
    output_path = custom_output_var.get() if output_mode_var.get() == "custom" else None
    
    # Update project data
    project_data["mod_name"] = mod_name
    project_data["author"] = author_name if author_name else "Unknown"
    
    print(f"Mod Name: {mod_name}")
    print(f"Author: {project_data['author']}")
    print(f"Cars: {len(project_data['cars'])}")
    total_skins = sum(len(car_info['skins']) for car_info in project_data['cars'].values())
    print(f"Total Skins: {total_skins}")
    
    export_status_label.configure(text="Preparing to export...")
    export_status_label.pack(padx=20, pady=(10,5))
    progress_bar.pack(fill="x", padx=20, pady=(0,5))
    progress_bar.set(0)
    generate_button_topbar.configure(state="disabled")  # Changed from generate_button to generate_button_topbar

    def update_status(message):
        """Update the status label text"""
        export_status_label.configure(text=message)

    def thread_fn():
        try:
            print("\nStarting mod generation thread...")
            update_status("Processing skins...")
            
            # Create custom progress callback
            def progress_with_status(value):
                update_progress(value)
                if value < 0.3:
                    update_status("Copying template files...")
                elif value < 0.7:
                    update_status(f"Processing {total_skins} skins...")
                else:
                    update_status("Creating ZIP archive...")
            
            # Import and call the multi-skin generator
            from file_ops import generate_multi_skin_mod as gen_multi
            gen_multi(
                project_data,
                output_path=output_path,
                progress_callback=progress_with_status
            )
            
            update_status("Export completed successfully!")
            print("Mod generation completed successfully!")
            print("="*50 + "\n")
            show_notification(f"✓ Mod '{mod_name}' created with {total_skins} skins!", "success", 5000)
            
            # Ask if user wants to clear project
            app.after(2000, lambda: show_notification("Project kept. Click 'Clear Project' to start new one.", "info", 4000))
            
        except FileExistsError as e:
            update_status("Error: File already exists")
            print(f"ERROR: File already exists - {e}")
            show_notification(f"File already exists: {str(e)}", "error", 5000)
        except Exception as e:
            update_status("Error: Export failed")
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            show_notification(f"Error: {str(e)}", "error", 5000)
        finally:
            progress_bar.set(0)
            generate_button_topbar.configure(state="normal")  # Changed from generate_button to generate_button_topbar
            # Hide progress bar and status after a short delay
            app.after(2000, lambda: progress_bar.pack_forget())
            app.after(2000, lambda: export_status_label.pack_forget())

    threading.Thread(target=thread_fn, daemon=True).start()






# === on_generate ===
def on_generate():
    global selected_carid
    
    print("\n" + "="*50)
    print("GENERATE MOD INITIATED")
    print("="*50)
    
    if not mod_name_var.get():
        print("ERROR: No mod name provided")
        show_notification("Please enter a Mod Name", "error")
        return
    if not skin_name_var.get():
        print("ERROR: No skin name provided")
        show_notification("Please enter a Skin Name", "error")
        return
    if not dds_path_var.get():
        print("ERROR: No DDS file selected")
        show_notification("Please select a DDS file", "error")
        return

    output_path = custom_output_var.get() if output_mode_var.get() == "custom" else None

    if not selected_carid:
        print("ERROR: No vehicle selected")
        show_notification("Invalid vehicle selection", "error")
        return

    print(f"Mod Name: {mod_name_var.get()}")
    print(f"Skin Name: {skin_name_var.get()}")
    print(f"Author: {author_var.get()}")
    print(f"Vehicle ID: {selected_carid}")
    print(f"DDS Path: {dds_path_var.get()}")
    print(f"Output Mode: {output_mode_var.get()}")
    if output_path:
        print(f"Custom Output Path: {output_path}")
    
    export_status_label.configure(text="Preparing to export...")
    export_status_label.pack(padx=20, pady=(10,5))
    progress_bar.pack(fill="x", padx=20, pady=(0,5))
    progress_bar.set(0)
    generate_button.configure(state="disabled")

    def update_status(message):
        """Update the status label text"""
        export_status_label.configure(text=message)

    def thread_fn():
        try:
            print("\nStarting mod generation thread...")
            update_status("Copying template files...")
            
            # Create custom progress callback that also updates status
            def progress_with_status(value):
                update_progress(value)
                if value < 0.3:
                    update_status("Copying template files...")
                elif value < 0.5:
                    update_status("Processing DDS texture...")
                elif value < 0.8:
                    update_status("Updating configuration files...")
                else:
                    update_status("Creating ZIP archive...")
            
            generate_mod(
                mod_name_var.get(),
                selected_carid,
                skin_name_var.get(),
                dds_path_var.get(),
                output_path=output_path,
                progress_callback=progress_with_status,
                author=author_var.get()
            )
            update_status("Export completed successfully!")
            print("Mod generation completed successfully!")
            print("="*50 + "\n")
            show_notification("✓ Mod created and installed successfully!", "success", 5000)
        except FileExistsError as e:
            update_status("Error: File already exists")
            print(f"ERROR: File already exists - {e}")
            show_notification(f"File already exists: {str(e)}", "error", 5000)
        except Exception as e:
            update_status("Error: Export failed")
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()
            show_notification(f"Error: {str(e)}", "error", 5000)
        finally:
            progress_bar.set(0)
            generate_button.configure(state="normal")
            # Hide progress bar and status after a short delay
            app.after(2000, lambda: progress_bar.pack_forget())
            app.after(2000, lambda: export_status_label.pack_forget())

    threading.Thread(target=thread_fn, daemon=True).start()



# === create_modern_card ===
def create_modern_card(parent, title=None, subtitle=None):
    """Create a modern card with optional title and subtitle"""
    card = ctk.CTkFrame(
        parent,
        corner_radius=16,
        fg_color=colors["card_bg"],
        border_width=1,
        border_color=colors["border"]
    )
    
    if title:
        header = ctk.CTkFrame(card, fg_color="transparent")
        header.pack(fill="x", padx=20, pady=(15, 5 if subtitle else 15))
        
        ctk.CTkLabel(
            header,
            text=title,
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color=colors["text"],
            anchor="w"
        ).pack(side="left")
        
        if subtitle:
            ctk.CTkLabel(
                card,
                text=subtitle,
                font=ctk.CTkFont(size=11),
                text_color=colors["text_secondary"],
                anchor="w"
            ).pack(fill="x", padx=20, pady=(0, 15))
    
    return card



# === create_modern_button ===
def create_modern_button(parent, text, command, style="primary", **kwargs):
    """Create a modern styled button"""
    styles = {
        "primary": {
            "fg_color": colors["accent"],
            "hover_color": colors["accent_hover"],
            "text_color": colors["accent_text"],
            "height": 40,
            "corner_radius": 12,
            "font": ctk.CTkFont(size=13, weight="bold"),
            "border_width": 0
        },
        "secondary": {
            "fg_color": colors["card_bg"],
            "hover_color": colors["card_hover"],
            "text_color": colors["text"],
            "height": 38,
            "corner_radius": 12,
            "font": ctk.CTkFont(size=13),
            "border_width": 1,
            "border_color": colors["border"]
        },
        "danger": {
            "fg_color": colors["error"],
            "hover_color": colors["error_hover"],
            "text_color": "white",
            "height": 38,
            "corner_radius": 12,
            "font": ctk.CTkFont(size=13, weight="bold"),
            "border_width": 0
        },
        "ghost": {
            "fg_color": "transparent",
            "hover_color": colors["card_hover"],
            "text_color": colors["text"],
            "height": 36,
            "corner_radius": 10,
            "font": ctk.CTkFont(size=12),
            "border_width": 1,
            "border_color": colors["border"]
        }
    }
    
    button_style = styles.get(style, styles["primary"])
    button_style.update(kwargs)
    
    return ctk.CTkButton(parent, text=text, command=command, **button_style)



# === create_modern_input ===
def create_modern_input(parent, label, variable, **kwargs):
    """Create a modern input field with label"""
    container = ctk.CTkFrame(parent, fg_color="transparent")
    
    ctk.CTkLabel(
        container,
        text=label,
        font=ctk.CTkFont(size=12, weight="bold"),
        text_color=colors["text"],
        anchor="w"
    ).pack(fill="x", pady=(0, 8))
    
    input_style = {
        "fg_color": colors["frame_bg"],
        "border_width": 1,
        "border_color": colors["border"],
        "corner_radius": 10,
        "height": 40,
        "font": ctk.CTkFont(size=13),
        "text_color": colors["text"]
    }
    input_style.update(kwargs)
    
    entry = ctk.CTkEntry(container, textvariable=variable, **input_style)
    entry.pack(fill="x")
    
    return container






# === show_notification ===
def show_notification(message, type="info", duration=3000):
    """
    Overlays a notification at the top of the app.
    Types: 'info', 'success', 'warning', 'error'
    """
    # Create notification frame if it doesn't exist or was destroyed
    global notification_frame
    try:
        if notification_frame.winfo_exists():
            for child in notification_frame.winfo_children():
                child.destroy()
    except:
        notification_frame = ctk.CTkFrame(app, fg_color="transparent")

    # Icon mapping
    icons = {
        "success": "✓",
        "error": "✕",
        "warning": "⚠",
        "info": "ℹ"
    }
    
    # Color schemes
    colors_map = {
        "success": {"bg": colors["success"], "text": colors["accent_text"]},
        "error": {"bg": colors["error"], "text": "white"},
        "warning": {"bg": colors["warning"], "text": colors["accent_text"]},
        "info": {"bg": colors["accent"], "text": colors["accent_text"]}
    }
    
    color_scheme = colors_map.get(type, colors_map["info"])
    icon = icons.get(type, "ℹ")
    
    # Clear previous notification
    for widget in notification_frame.winfo_children():
        widget.destroy()
    
    # Calculate dynamic width based on message length
    # Approximate: 8 pixels per character + padding + icon space
    base_width = 100  # Icon + padding space
    char_width = 9  # Approximate pixels per character
    calculated_width = base_width + (len(message) * char_width)
    
    # Set min and max bounds
    min_width = 300
    max_width = 1200
    notification_width = max(min_width, min(calculated_width, max_width))
    
    # Create notification content with dynamic width
    notification_content = ctk.CTkFrame(
        notification_frame,
        fg_color=color_scheme["bg"],
        corner_radius=12,
        width=notification_width,
        height=50
    )
    notification_content.pack(padx=0, pady=10)
    notification_content.pack_propagate(False)
    
    # Icon
    ctk.CTkLabel(
        notification_content,
        text=icon,
        font=ctk.CTkFont(size=20, weight="bold"),
        text_color=color_scheme["text"],
        width=40
    ).pack(side="left", padx=(15, 5))
    
    # Message
    ctk.CTkLabel(
        notification_content,
        text=message,
        font=ctk.CTkFont(size=13, weight="bold"),
        text_color=color_scheme["text"],
        anchor="w"
    ).pack(side="left", fill="x", expand=True, padx=(5, 15))
    
    # Show notification using place() to overlay it - NO width/height parameters here
    # Position it below the topbar (60px from top), centered
    notification_frame.place(relx=0.5, y=60, anchor="n")
    
    # Raise it to the top of the stacking order
    notification_frame.lift()
    
    # Auto-hide
    if duration > 0:
        app.after(duration, lambda: notification_frame.place_forget())


# === hide_notification ===
def hide_notification():
    """Manually hide the notification"""
    notification_label.pack_forget()



# === show_wip_warning ===
def show_wip_warning():
    """Show Work-In-Progress warning dialog on first launch"""
    global app_settings
    
    print(f"\n[DEBUG] ========== WIP WARNING CHECK ==========")
    print(f"[DEBUG] first_launch setting: {app_settings.get('first_launch', True)}")
    
    if app_settings.get("first_launch", True):
        print(f"[DEBUG] First launch detected - showing WIP warning dialog")
        # Create warning dialog
        dialog = ctk.CTkToplevel(app)
        dialog.title("Welcome to BeamSkin Studio")
        dialog.geometry("600x550")
        dialog.transient(app)
        dialog.grab_set()
        print(f"[DEBUG] Dialog created")
        
        # Center the dialog
        dialog.update_idletasks()
        dialog_x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        dialog_y = (dialog.winfo_screenheight() // 2) - (550 // 2)
        dialog.geometry(f"600x550+{dialog_x}+{dialog_y}")
        print(f"[DEBUG] Dialog centered at ({dialog_x}, {dialog_y})")
        
        # Configure colors
        dialog.configure(fg_color=colors["frame_bg"])
        
        # Main frame
        main_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Warning icon and title
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 20))
        
        ctk.CTkLabel(
            title_frame,
            text="⚠️",
            font=ctk.CTkFont(size=48),
            text_color=colors["text"]
        ).pack()
        
        ctk.CTkLabel(
            title_frame,
            text="Work-In-Progress Software",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=colors["text"]
        ).pack(pady=(10, 0))
        
        # Message
        message_frame = ctk.CTkFrame(main_frame, fg_color=colors["card_bg"], corner_radius=12)
        message_frame.pack(fill="both", expand=True, pady=(0, 20))
        
        message_text = (
            "BeamSkin Studio is currently in active development.\n\n"
            "Please be aware that:\n\n"
            "• Bugs and errors should be expected\n"
            "• Some features may not work as intended\n"
            "• Data loss or unexpected behavior may occur\n"
            "• Regular updates and changes are being made\n\n"
            "Known Limitations:\n\n"
            "• Car variations are NOT supported yet\n"
            "  (e.g., Ambulance, Box Truck, Sedan, Wagon)\n"
            "• Modded cars added via Developer tab\n"
            "  most likely won't work properly\n\n"
            "Thank you for your patience and understanding!"
        )
        
        ctk.CTkLabel(
            message_frame,
            text=message_text,
            font=ctk.CTkFont(size=13),
            text_color=colors["text"],
            justify="left"
        ).pack(padx=20, pady=20)
        
        # Checkbox to not show again
        dont_show_var = ctk.BooleanVar(value=False)
        checkbox = ctk.CTkCheckBox(
            main_frame,
            text="Don't show this message again",
            variable=dont_show_var,
            font=ctk.CTkFont(size=12),
            text_color=colors["text"]
        )
        checkbox.pack(pady=(0, 10))
        
        # OK button
        def on_ok():
            print(f"[DEBUG] User clicked 'I Understand'")
            print(f"[DEBUG] Don't show again checkbox: {dont_show_var.get()}")
            if dont_show_var.get():
                app_settings["first_launch"] = False
                save_settings()
                print("[DEBUG] First launch warning disabled and settings saved")
            dialog.destroy()
            print(f"[DEBUG] Dialog closed")
        
        ctk.CTkButton(
            main_frame,
            text="I Understand",
            command=on_ok,
            fg_color=colors["accent"],
            hover_color=colors["accent_hover"],
            text_color=colors["accent_text"],
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            width=200
        ).pack()
        
        print(f"[DEBUG] Waiting for user to close dialog...")
        # Wait for dialog to close
        app.wait_window(dialog)
        print(f"[DEBUG] ========== WIP WARNING COMPLETE ==========\n")
    else:
        print(f"[DEBUG] Not first launch - skipping WIP warning")
        print(f"[DEBUG] ========== WIP WARNING SKIPPED ==========\n")



# === toggle_theme ===
def toggle_theme():
    """Toggle between light and dark theme"""
    global current_theme, colors
    
    # Ask user if they want to restart
    response = messagebox.askyesno(
        "Restart Required", 
        "Changing the theme requires restarting the application.\n\n"
        "⚠️ WARNING: Any unsaved changes will be lost!\n\n"
        "Do you want to restart now?",
        icon='warning'
    )
    
    if response:
        # Switch theme
        current_theme = "light" if current_theme == "dark" else "dark"
        colors = THEMES[current_theme]
        
        # Save setting
        app_settings["theme"] = current_theme
        save_settings()
        
        print(f"Theme changed to: {current_theme}")
        print("Restarting application...")
        
        # Restart the application
        import sys
        import subprocess
        
        # Close current app
        app.destroy()
        
        # Restart with same script
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit()
    else:
        # User cancelled, revert the switch
        if current_theme == "dark":
            theme_switch.deselect()
        else:
            theme_switch.select()



# === update_progress ===
def update_progress(value):
    if progress_bar.winfo_ismapped():
        progress_bar.set(value)





# Build the Generator Tab UI - wrapped in scrollable frame
generator_scroll = ctk.CTkScrollableFrame(generator_tab, fg_color="transparent")
generator_scroll.pack(fill="both", expand=True, padx=0, pady=0)

# Modern section header
section_header = ctk.CTkFrame(generator_scroll, fg_color="transparent", height=60)
section_header.pack(fill="x", padx=20, pady=(15, 10))
section_header.pack_propagate(False)

ctk.CTkLabel(
    section_header,
    text="Project Settings",
    font=ctk.CTkFont(size=18, weight="bold"),
    text_color=colors["text"]
).pack(side="left", anchor="w")

# Project controls with modern styling
project_controls = ctk.CTkFrame(section_header, fg_color="transparent")
project_controls.pack(side="right")

create_modern_button(project_controls, "💾 Save Project", save_project, style="primary", width=130, height=32).pack(side="left", padx=3)
create_modern_button(project_controls, "📁 Load Project", load_project, style="primary", width=130, height=32).pack(side="left", padx=3)
create_modern_button(project_controls, "Clear", clear_project, style="danger", width=100, height=32).pack(side="left", padx=3)

# Project Overview
ctk.CTkLabel(generator_scroll, text="Project Overview", font=ctk.CTkFont(size=14, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=10, pady=(10,5))

# Search bar for project overview
project_search_frame = ctk.CTkFrame(generator_scroll, fg_color="transparent")
project_search_frame.pack(fill="x", padx=10, pady=(0, 5))

project_search_var = ctk.StringVar()

project_search_entry = ctk.CTkEntry(
    project_search_frame,
    textvariable=project_search_var,
    height=32,
    corner_radius=8,
    fg_color=colors["card_bg"],
    border_color=colors["border"],
    text_color="#888888"
)
project_search_entry.pack(fill="x")

# Setup custom placeholder
placeholder_project_search = "🔍 Search cars..."
project_search_entry.insert(0, placeholder_project_search)
project_search_entry.bind("<FocusIn>", lambda e: on_entry_click(e, project_search_entry, placeholder_project_search))
project_search_entry.bind("<FocusOut>", lambda e: on_focusout(e, project_search_entry, placeholder_project_search))

# Container for 2-column grid
project_overview_container = ctk.CTkScrollableFrame(generator_scroll, height=150, corner_radius=12, fg_color=colors["frame_bg"])
project_overview_container.pack(fill="x", padx=10, pady=(0,10))

# Grid frame inside container
project_overview_frame = ctk.CTkFrame(project_overview_container, fg_color="transparent")
project_overview_frame.pack(fill="both", expand=True, padx=5, pady=5)

# Now attach the search functionality after the frame is created
project_search_entry.bind("<KeyRelease>", lambda e: refresh_project_display())

# Add Skin Section
current_car_label = ctk.CTkLabel(generator_scroll, text="", font=ctk.CTkFont(size=14, weight="bold"), text_color=colors["accent"])

def update_current_car_label():
    """Update the label showing which car is selected"""
    if selected_car_for_skin and selected_car_for_skin in project_data["cars"]:
        # Get base carid
        base_carid = project_data["cars"][selected_car_for_skin].get("base_carid", selected_car_for_skin)
        
        # Get car name
        car_name = VEHICLE_IDS.get(base_carid, base_carid)
        for cid, cname in car_id_list:
            if cid == base_carid:
                car_name = cname
                break
        
        # Add instance number if applicable
        display_text = f"{car_name} ({base_carid})"
        if "_" in selected_car_for_skin and selected_car_for_skin != base_carid:
            instance_num = selected_car_for_skin.split("_")[-1]
            display_text = f"{car_name} - Instance #{instance_num} ({base_carid})"
        
        current_car_label.configure(text=f"Adding Skins to: {display_text}")
        current_car_label.pack(anchor="w", padx=10, pady=(10,0))
    else:
        current_car_label.pack_forget()

# Modern section header
ctk.CTkLabel(
    generator_scroll,
    text="Add Skins to Selected Car",
    font=ctk.CTkFont(size=18, weight="bold"),
    text_color=colors["text"]
).pack(anchor="w", padx=20, pady=(20, 10))

# Modern skin input card
skin_card = create_modern_card(generator_scroll)
skin_card.pack(fill="x", padx=20, pady=(0, 15))

skin_card_content = ctk.CTkFrame(skin_card, fg_color="transparent")
skin_card_content.pack(fill="x", padx=20, pady=20)

# Skin name input
skin_name_input = create_modern_input(skin_card_content, "Skin Name", skin_name_var)
skin_name_input.pack(fill="x", pady=(0, 15))

# DDS texture input with preview
dds_section = ctk.CTkFrame(skin_card_content, fg_color="transparent")
dds_section.pack(fill="x", pady=(0, 15))

ctk.CTkLabel(
    dds_section,
    text="DDS Texture File",
    font=ctk.CTkFont(size=12, weight="bold"),
    text_color=colors["text"],
    anchor="w"
).pack(fill="x", pady=(0, 8))

dds_input_frame = ctk.CTkFrame(dds_section, fg_color="transparent")
dds_input_frame.pack(fill="x", pady=(0, 12))

dds_entry = ctk.CTkEntry(
    dds_input_frame,
    textvariable=dds_path_var,
    state="readonly",
    fg_color=colors["frame_bg"],
    text_color=colors["text"],
    border_width=1,
    border_color=colors["border"],
    corner_radius=10,
    height=40,
    font=ctk.CTkFont(size=12)
)
dds_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))

dds_button = ctk.CTkButton(
    dds_input_frame,
    text="📁 Browse",
    width=100,
    height=40,
    command=select_dds,
    fg_color=colors["frame_bg"],
    hover_color=colors["card_hover"],
    text_color=colors["text"],
    border_width=1,
    border_color=colors["border"],
    corner_radius=10,
    font=ctk.CTkFont(size=12, weight="bold")
)
dds_button.pack(side="right")

# Modern preview with border
preview_container = ctk.CTkFrame(dds_section, fg_color=colors["frame_bg"], corner_radius=14, border_width=2, border_color=colors["border"])
preview_container.pack()

dds_preview_label = ctk.CTkLabel(
    preview_container,
    text="🖼️\n\nPreview\n\nSelect a DDS file",
    fg_color="transparent",
    corner_radius=12,
    width=180,
    height=180,
    text_color=colors["text_secondary"],
    font=ctk.CTkFont(size=12)
)
dds_preview_label.pack(padx=10, pady=10)

# Modern add button
add_skin_button = ctk.CTkButton(
    skin_card_content,
    text="➕ Add Skin to Selected Car",
    command=add_skin_to_car,
    fg_color=colors["accent"],
    hover_color=colors["accent_hover"],
    text_color=colors["accent_text"],
    height=45,
    corner_radius=12,
    font=ctk.CTkFont(size=14, weight="bold")
)
add_skin_button.pack(fill="x", pady=(5, 0))

# Export status and progress
export_status_label = ctk.CTkLabel(generator_scroll, text="", text_color=colors["text"], font=ctk.CTkFont(size=12))
export_status_label.pack(padx=20, pady=(10,5))
export_status_label.pack_forget()

progress_bar = ctk.CTkProgressBar(generator_scroll)
progress_bar.pack_forget()


# Initialize display
refresh_project_display()

# -----------------------
# How to Use Tab
# -----------------------

# Create a frame to hold the chapter buttons and content
howto_main_frame = ctk.CTkFrame(howto_tab, fg_color="transparent")
howto_main_frame.pack(fill="both", expand=True, padx=10, pady=10)

# Chapter navigation frame at the top - TWO ROWS
chapter_nav_frame = ctk.CTkFrame(
    howto_main_frame, 
    fg_color=colors["frame_bg"], 
    corner_radius=12
)
chapter_nav_frame.pack(fill="x", pady=(0,10))

# Create two row frames inside the navigation frame
row1_frame = ctk.CTkFrame(chapter_nav_frame, fg_color="transparent")
row1_frame.pack(fill="x", padx=5, pady=(10, 5))

row2_frame = ctk.CTkFrame(chapter_nav_frame, fg_color="transparent")
row2_frame.pack(fill="x", padx=5, pady=(5, 10))

# Content frame
howto_text = ctk.CTkTextbox(howto_main_frame, width=580, height=900,
                            font=ctk.CTkFont(size=14, weight="bold"), fg_color=colors["frame_bg"], text_color=colors["text"])
howto_text.pack(fill="both", expand=True)

# Chapter content dictionary
chapters = {
    "Chapter 1": ("Skin Modding Basics", """
────────────────────────────
Chapter 1: Skin Modding Basics
────────────────────────────

Before using the tool, you need to create your skin texture.

Recommended Programs
- Paint.NET (Free – recommended for beginners)
- Adobe Photoshop (Paid – requires a DDS plugin)

Required File Format
Your skin must be saved as a .DDS file.
Other formats (PNG, JPG, etc.) will not work.

DDS File Naming:
carid_skin_Skinname.dds

Naming Breakdown
- carid – Vehicle identifier (single word).
  - You can find the correct carid in the "Car List" tab.
- skin – Must stay exactly as written
- Skinname – One word, no spaces

Incorrect file names will cause the skin to not load.
"""),
    "Chapter 2": ("Using the Generator Tab", """
────────────────────────────
Chapter 2: Using the Generator Tab
────────────────────────────

The Generator tab uses a multi-car, multi-skin project system.
You can add multiple vehicles and multiple skins per vehicle,
then export everything into a single mod ZIP file.

Project Settings:

ZIP Name
- One word only
- No spaces or special characters
- This becomes the mod filename
Example: MyCoolSkins

Author
- Your name or creator name
- Appears in all skin information
- Spaces allowed

Adding Vehicles to Project:

1. Click "Select Vehicle" to open the vehicle selector
2. Search for your vehicle by name or car ID
3. Click the vehicle to select it
4. Click "Add Car to Project"
5. The vehicle appears in the Project Overview

You can add the same vehicle multiple times if you want
different sets of skins organized separately.

Adding Skins to Vehicles:

1. Click on a vehicle card in the Project Overview
   to select it for adding skins
2. Enter the Skin Name (display name shown in-game)
   • Spaces allowed
   • Example: My Cool Racing Skin
3. Click Browse and select your .dds file
4. Click "Add Skin to Selected Car"

You can add as many skins as you want to each vehicle.

Project Management:

- Save Project: Save your current work to a .bsproject file
  to continue later
- Load Project: Load a previously saved project
- Clear Project: Start fresh (removes all cars and skins)

Generate Mod:

Once you've added all vehicles and skins:
1. Review your project in the Project Overview
2. Choose output location (Steam or Custom)
3. Click "Generate Mod"

The tool will create a single ZIP file containing all
your skins for all vehicles.
"""),
    "Chapter 3": ("Output Location", """
────────────────────────────
Chapter 3: Output Location
────────────────────────────

Steam (Default)
Exports automatically to:
C:\\Users\\username\\AppData\\Local\\BeamNG\\BeamNG.drive\\current\\mods

Custom Location
Choose your own folder for exporting.
Useful if you have a custom mod directory or want to 
organize your mods differently.
"""),
    "Chapter 4": ("Car List", """
────────────────────────────
Chapter 4: Car List
────────────────────────────

The Car List tab shows all available vehicles.
- Search by car name or car ID
- Click "Copy ID" to copy the car ID to clipboard
- Click "Get UV Map" to extract the vehicle's UV template
- Hover over any vehicle to see a preview image
- Use this when naming your DDS files
"""),
    "Chapter 5": ("Developer Mode", """
────────────────────────────
Chapter 5: Developer Mode (Advanced)
────────────────────────────

Developer Mode allows you to add custom vehicles 
that aren't in the default list.

⚠️ IMPORTANT: Getting the Correct Car ID

The Car ID MUST be exactly correct, or skins won't work.

How to Find the Correct Car ID:
1. Launch BeamNG.drive
2. Load into any map
3. Spawn the vehicle you want to add
4. Open the console (~ key)
5. Look for the message: "Vehicle replaced: carid"
6. The text shown is your exact Car ID

Example console output:
"Vehicle replaced: civetta_scintilla"
Your Car ID is: civetta_scintilla

To Enable Developer Mode:
1. Go to Settings tab
2. Toggle "Developer Mode" on
3. A new "Developer" tab will appear

Adding Custom Vehicles:
1. Get the exact Car ID from BeamNG console (see above)
2. Enter the Car ID exactly as shown (case-sensitive)
   • No spaces
   • Must match console output exactly
3. Enter the Car Name (how it appears in menus)
   • This can be anything you want
   • Spaces allowed
4. Select the vehicle's JSON file (materials.json)
5. Select the vehicle's JBEAM file (.jbeam skin file)
6. (Optional) Select a preview image (.jpg only)
7. Click "Add Vehicle"

What the Tool Does Automatically:
- Identifies the canonical skin variant
- Removes alternative skin variants
- Removes palette-based color logic
- Updates material paths for the new vehicle
- Creates the necessary folder structure
- Processes JSON and JBEAM files
- Adds the vehicle to all menus
- Saves it for future sessions

The tool keeps only the FIRST skin variant found in
your files and removes all others. It also removes
color palette logic that could interfere with custom
skins.

Managing Custom Vehicles:
- View all added vehicles in the Developer tab
- Search added vehicles by name or ID
- Delete vehicles you no longer need
- Hover over vehicles to see preview images
- Changes are saved automatically

Where to Find Vehicle Files:
Vehicle JSON and JBEAM files are typically found in:
C:\\Program Files (x86)\\Steam\\steamapps\\common\\BeamNG.drive\\content\\vehicles\\

Look in the vehicle's folder, then in the "skin" subfolder:
- materials.json (or similar .json file)
- .jbeam file (usually named vehicleid_skin.jbeam)

Preview Images (Optional):
If you want hover previews for your custom vehicle:
- Use a .jpg or .jpeg image
- The tool will copy it to the correct location
- Recommended size: 400x400 or larger
"""),
    "Chapter 6": ("Debug Mode", """
────────────────────────────
Chapter 6: Debug Mode (Advanced)
────────────────────────────

Debug Mode is available when Developer Mode is enabled.
It opens a separate console window showing detailed 
information about what the tool is doing.

To Enable Debug Mode:
1. Enable Developer Mode first
2. Toggle "Debug Mode" in Settings
3. A debug console window will open

What Debug Mode Shows:
- Vehicle selections and additions
- File operations and processing
- JSON/JBEAM editing details
- Canonical skin detection
- Variant removal operations
- Mod generation progress
- Detailed error messages
- All developer actions

Useful For:
- Troubleshooting issues
- Understanding processing steps
- Seeing which skin variants were kept/removed
- Verifying correct Car ID
- Reporting bugs to the developer

The debug console has a "Clear" button to remove 
old messages. Closing the console automatically 
disables debug mode.
"""),
    "Chapter 7": ("Theme Settings", """
────────────────────────────
Chapter 7: Theme Settings
────────────────────────────

You can switch between Dark Mode and Light Mode 
in the Settings tab.

Your theme preference is automatically saved and 
will be remembered when you restart the app.

⚠️ Note: After changing the theme, you'll need to 
restart the application for it to fully apply.
The tool will ask for confirmation before restarting.
"""),
    "Chapter 8": ("Tips & Troubleshooting", """
────────────────────────────
Chapter 8: Tips & Troubleshooting
────────────────────────────

Skin Not Appearing In-Game?
- Verify DDS filename matches the carid EXACTLY
- Check that the ZIP name doesn't already exist
- Restart BeamNG.drive after adding the mod
- Check the mod is in the correct mods folder
- Make sure you selected the correct vehicle in the project

DDS File Issues?
- Ensure you're using DDS format (not PNG/JPG)
- Use BC3/DXT5 compression for best compatibility
- Resolution should be power of 2 (1024, 2048, 4096)
- File name format: carid_skin_skinname.dds

Custom Vehicle Not Working?
- Verify the Car ID is EXACTLY as shown in BeamNG console
- Check "Vehicle replaced: carid" message in-game
- The Car ID is case-sensitive and must match exactly
- Verify JSON and JBEAM files are from the correct vehicle
- Make sure you selected files from the "skin" subfolder
- Enable Debug Mode to see detailed processing information
- Check if canonical skin was detected correctly

Car ID Verification:
If you're unsure about the Car ID:
1. Load BeamNG.drive
2. Spawn the vehicle
3. Open console (~ key)
4. Look for "Vehicle replaced: exactcarid"
5. Use that exact text as your Car ID

ZIP Already Exists Error?
- Choose a different ZIP name
- Delete the old ZIP from the mods folder
- The tool prevents overwriting existing mods

Preview Images Not Showing?
- Make sure you selected a .jpg or .jpeg file
- The image should be at least 400x400 pixels
- Hover over the vehicle card for 1 second to see preview
- Check that the image was added when creating the vehicle

Project Files:
- Save your projects regularly using "Save Project"
- Project files use .bsproject extension
- Projects remember all vehicles and skins
- Load saved projects to continue work later

Performance Tips:
- Close unused tabs to save memory
- Clear debug console regularly if using Debug Mode
- Organize your DDS files in folders by vehicle
- Save projects before generating large mods
"""),
    "Chapter 9": ("Understanding the Processing", """
────────────────────────────
Chapter 9: Understanding the Processing
────────────────────────────

When you add a custom vehicle, the tool automatically
processes the JSON and JBEAM files:

JSON Processing:
1. Finds the first .skin.<variant> in the file
2. That variant becomes the "canonical" skin
3. Removes ALL other skin variants
4. Removes color palette logic (colorPaletteMap, etc.)
5. Updates material names and paths
6. Preserves all other settings exactly

JBEAM Processing:
1. Finds the first _skin_ entry in the file
2. Keeps only that entry, removes all others
3. Updates skin name to placeholder
4. Updates author and skin name fields
5. Preserves all other settings (value, slotType, etc.)

This ensures your custom skins work correctly without
interference from palette systems or multiple variants.

Enable Debug Mode to see exactly what the tool is doing
during processing.
"""),
    "Chapter 10": ("Final Notes", """
────────────────────────────
Chapter 10: Final Notes
────────────────────────────

- Always verify the Car ID using the BeamNG console
- Double-check all names before generating
- Keep backups of your original DDS files
- Save projects regularly to avoid losing work
- Test skins in-game before sharing
- Join the BeamNG modding community for help

Additional Resources:
- BeamNG Forums: forum.beamng.com
- BeamNG Documentation: documentation.beamng.com
- Modding Discord servers

You are now ready to create amazing skins!

────────────────────────────
""")
}

# Store chapter buttons for styling
chapter_buttons = []

def load_chapter(chapter_key):
    """Load a specific chapter into the text box"""
    chapter_title, chapter_content = chapters[chapter_key]
    howto_text.configure(state="normal")
    howto_text.delete("0.0", "end")
    howto_text.insert("0.0", chapter_content)
    howto_text.configure(state="disabled")
    
    # Update button colors
    for btn, key in chapter_buttons:
        if key == chapter_key:
            btn.configure(fg_color=colors["accent"], text_color=colors["accent_text"])
        else:
            btn.configure(fg_color=colors["card_bg"], text_color=colors["text"])
    
    print(f"Loaded: {chapter_key} - {chapter_title}")

def load_all_chapters():
    """Load all chapters into the text box"""
    howto_text.configure(state="normal")
    howto_text.delete("0.0", "end")
    
    # Add a header
    howto_text.insert("0.0", """How to Use Guide

This guide will walk you through the basics of creating a skin and using the modding tool to package it correctly.
Follow each chapter carefully to ensure your skin works in-game.

Use the chapter buttons above to jump to specific sections, or scroll through all chapters below.

""")
    
    # Add all chapters
    for chapter_key in sorted(chapters.keys(), key=lambda x: int(x.split()[1])):
        chapter_title, chapter_content = chapters[chapter_key]
        howto_text.insert("end", chapter_content)
        howto_text.insert("end", "\n")
    
    howto_text.configure(state="disabled")
    
    # Reset button colors
    for btn, key in chapter_buttons:
        btn.configure(fg_color=colors["card_bg"], text_color=colors["text"])
    
    print("Loaded all chapters")

# Create "View All" button in first row
view_all_btn = ctk.CTkButton(
    row1_frame,
    text="📖 View All Chapters",
    command=load_all_chapters,
    width=150,
    height=35,
    fg_color=colors["card_bg"],
    hover_color=colors["card_hover"],
    text_color=colors["text"],
    font=ctk.CTkFont(size=12, weight="bold"),
    corner_radius=8
)
view_all_btn.pack(side="left", padx=5)

# Create chapter navigation buttons - SORTED NUMERICALLY
# Split chapters into two rows (View All + 5 chapters in row 1, 5 chapters in row 2)
sorted_chapters = sorted(chapters.keys(), key=lambda x: int(x.split()[1]))

# First row: View All + Chapters 1-5
for chapter_key in sorted_chapters[:5]:
    chapter_title, _ = chapters[chapter_key]
    
    btn = ctk.CTkButton(
        row1_frame,
        text=chapter_title,
        command=lambda k=chapter_key: load_chapter(k),
        width=150,
        height=35,
        fg_color=colors["card_bg"],
        hover_color=colors["card_hover"],
        text_color=colors["text"],
        font=ctk.CTkFont(size=11),
        corner_radius=8
    )
    btn.pack(side="left", padx=5)
    chapter_buttons.append((btn, chapter_key))

# Second row: Chapters 6-10
for chapter_key in sorted_chapters[5:]:
    chapter_title, _ = chapters[chapter_key]
    
    btn = ctk.CTkButton(
        row2_frame,
        text=chapter_title,
        command=lambda k=chapter_key: load_chapter(k),
        width=150,
        height=35,
        fg_color=colors["card_bg"],
        hover_color=colors["card_hover"],
        text_color=colors["text"],
        font=ctk.CTkFont(size=11),
        corner_radius=8
    )
    btn.pack(side="left", padx=5)
    chapter_buttons.append((btn, chapter_key))

# Load all chapters by default
load_all_chapters()

# -----------------------
# Car ID List Tab
# -----------------------
carlist_search_var = ctk.StringVar()
carlist_search_entry = ctk.CTkEntry(
    carlist_tab,
    textvariable=carlist_search_var,
    placeholder_text="Search Car ID...",
    placeholder_text_color="#888888",
    fg_color=colors["card_bg"],
    text_color=colors["text"]
)
carlist_search_entry.pack(fill="x", padx=10, pady=(10,5))

carlist_scroll = ctk.CTkScrollableFrame(carlist_tab, fg_color=colors["frame_bg"])
carlist_scroll.pack(fill="both", expand=True, padx=10, pady=10)

# No manual scroll bindings - universal scroll handler will manage this

carlist_font = ctk.CTkFont(size=14, weight="bold")
carlist_items = []

car_id_list = [
    ("autobello", "Autobello Piccolina"), ("atv", "FPU Wydra"), ("barstow", "Gavril Barstow"),
    ("bastion", "Bruckell Bastion"), ("bluebuck", "Gavril Bluebuck"), ("bolide", "Civetta Bolide"),
    ("burnside", "Burnside Special"), ("covet", "Ibishu Covet"), ("citybus", "Wentward DT40L"),
    ("bx", "Ibishu BX-Series"), ("dryvan", "Dry Van Trailer"), ("dumptruck", "Hirochi HT-55"),
    ("etk800", "ETK 800 Series"), ("etkc", "ETK K Series"), ("etki", "ETK I Series"),
    ("fullsize", "Gavril Grand Marshal"), ("hopper", "Ibishu Hopper"), ("lansdale", "Soliad Lansdale"),
    ("legran", "Bruckell Legran"), ("midsize", "Newer Ibishu Pessima"), ("miramar", "Ibishu Miramar"),
    ("moonhawk", "Bruckell Moonhawk"), ("md_series", "Gavril MD-Series"), ("midtruck", "Autobello Stambecco"),
    ("nine", "Bruckell Nine"), ("pessima", "Older Ibishu Pessima"), ("pickup", "Gavril D Series"),
    ("pigeon", "Ibishu Pigeon"), ("racetruck", "SP Dunekicker"), ("roamer", "Gavril Roamer"),
    ("rockbouncer", "SP Rockbasher"), ("sbr", "Hirochi SBR4"), ("scintilla", "Civetta Scintilla"),
    ("sunburst2", "Hirochi Sunburst"), ("us_semi", "Gavril T Series"), ("utv", "Hirochi Aurata"),
    ("van", "Gavril H Series"), ("vivace", "Cherrier FCV"), ("wendover", "Soliad Wendover"),
    ("wigeon", "Ibishu Wigeon"), ("wl40", "Hirochi WL-40")
]

def copy_carid(carid):
    app.clipboard_clear()
    app.clipboard_append(carid)
    show_notification(f"✓ Car ID '{carid}' copied to clipboard!", "success", 2000)

def get_uv_map(carid):
    """Search for UV map in BeamNG installation and prompt user to copy it"""
    import zipfile
    import tempfile
    import re
    from tkinter import simpledialog
    
    # BeamNG default installation path
    beamng_path = r"C:\Program Files (x86)\Steam\steamapps\common\BeamNG.drive\content\vehicles"
    zip_file_path = os.path.join(beamng_path, f"{carid}.zip")
    
    # Check if the ZIP file exists
    if not os.path.exists(zip_file_path):
        show_notification(f"❌ Vehicle ZIP not found: {carid}.zip", "error", 4000)
        print(f"UV Map search failed: ZIP file does not exist - {zip_file_path}")
        return
    
    try:
        # First, check if we need to also search in common.zip
        # This applies to vehicles that reference common parts (like ambulance variants)
        search_common = False
        common_search_dirs = []
        
        # Check if any files in the vehicle zip reference common parts
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            for file_path in all_files:
                filename_lower = os.path.basename(file_path).lower()
                # If we find ambulance-related files, also search in common/pickup
                if "ambulance" in filename_lower:
                    search_common = True
                    common_search_dirs.append("vehicles/common/pickup/")
                    break
        
        # Now search for UV maps
        with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
            all_files = zip_ref.namelist()
            
            # Look for UV map files in vehicles/<carid>/ directory
            target_dir = f"vehicles/{carid}/"
            found_files = []
            
            # Search for files containing "skin" and "uv" OR just "uvmap" OR "uv1_layout" (case-insensitive)
            # Exclude files with "color" as they are textures, not UV maps
            for file_path in all_files:
                if file_path.startswith(target_dir):
                    filename_lower = os.path.basename(file_path).lower()
                    
                    # Skip files with "color" in the name (these are texture files)
                    if "color" in filename_lower:
                        continue
                    
                    # Skip files that start with "skin_" (these are skin texture files like skin_camo.dds, skin_zebra.png, etc.)
                    if filename_lower.startswith("skin_"):
                        continue
                    
                    # Skip files that match pattern: <word>_skin_<skinname>_uv (like autobello_skin_doublestripe_uv1.dds)
                    # These are skin textures, not UV layout maps
                    # We detect this by checking if there's text between "_skin_" and "_uv"
                    if re.search(r'_skin_\w+_uv\d*\.', filename_lower):
                        continue
                    
                    # Check if filename contains both "skin" and "uv", OR contains "uvmap", OR contains "uv1_layout"
                    has_skin_and_uv = "skin" in filename_lower and "uv" in filename_lower
                    has_uvmap = "uvmap" in filename_lower
                    has_uv_layout = "uv1_layout" in filename_lower or "uv_layout" in filename_lower
                    
                    if has_skin_and_uv or has_uvmap or has_uv_layout:
                        # Prioritize certain extensions
                        if filename_lower.endswith(('.dds', '.png', '.jpg', '.jpeg')):
                            found_files.append((file_path, zip_file_path))
            
            # If we need to search common.zip, do it now
            if search_common and common_search_dirs:
                common_zip_path = os.path.join(beamng_path, "common.zip")
                if os.path.exists(common_zip_path):
                    print(f"Also searching in common.zip for ambulance UV maps...")
                    with zipfile.ZipFile(common_zip_path, 'r') as common_zip:
                        common_files = common_zip.namelist()
                        
                        for search_dir in common_search_dirs:
                            for file_path in common_files:
                                if file_path.startswith(search_dir):
                                    filename_lower = os.path.basename(file_path).lower()
                                    
                                    # Apply same filters
                                    if "color" in filename_lower:
                                        continue
                                    if filename_lower.startswith("skin_"):
                                        continue
                                    if re.search(r'_skin_\w+_uv\d*\.', filename_lower):
                                        continue
                                    
                                    has_skin_and_uv = "skin" in filename_lower and "uv" in filename_lower
                                    has_uvmap = "uvmap" in filename_lower
                                    has_uv_layout = "uv1_layout" in filename_lower or "uv_layout" in filename_lower
                                    
                                    if has_skin_and_uv or has_uvmap or has_uv_layout:
                                        if filename_lower.endswith(('.dds', '.png', '.jpg', '.jpeg')):
                                            found_files.append((file_path, common_zip_path))
            
            if not found_files:
                show_notification(f"❌ No UV map files found for '{carid}'", "error", 4000)
                print(f"UV Map search failed: No UV files found in {zip_file_path}")
                # Show files that contain "skin" or "uvmap" for debugging
                skin_files = [f for f in all_files if f.startswith(target_dir) and "skin" in os.path.basename(f).lower()]
                uvmap_files = [f for f in all_files if f.startswith(target_dir) and "uvmap" in os.path.basename(f).lower()]
                uv_files = [f for f in all_files if f.startswith(target_dir) and "uv" in os.path.basename(f).lower()]
                print(f"Files with 'skin' in name: {skin_files[:10]}")  # Show first 10
                print(f"Files with 'uvmap' in name: {uvmap_files}")
                print(f"Files with 'uv' in name: {uv_files[:10]}")
                return
            
            # If multiple files found, let user choose
            selected_files = []
            if len(found_files) == 1:
                selected_files = [found_files[0]]
                file_path, source_zip = found_files[0]
                print(f"UV Map found in ZIP: {file_path} (from {os.path.basename(source_zip)})")
            else:
                # Create selection dialog
                print(f"Multiple UV maps found ({len(found_files)}): {[(os.path.basename(f), os.path.basename(z)) for f, z in found_files]}")
                
                # Create a custom dialog window
                dialog = ctk.CTkToplevel(app)
                dialog.title("Select UV Map(s)")
                dialog.geometry("600x400")
                dialog.transient(app)
                dialog.grab_set()
                
                # Center the dialog
                dialog.update_idletasks()
                x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
                y = (dialog.winfo_screenheight() // 2) - (400 // 2)
                dialog.geometry(f"600x400+{x}+{y}")
                
                ctk.CTkLabel(
                    dialog,
                    text=f"Multiple UV maps found for {carid}\nSelect one or more files:",
                    font=ctk.CTkFont(size=14, weight="bold"),
                    text_color=colors["text"]
                ).pack(pady=20)
                
                # Scrollable frame for options
                scroll_frame = ctk.CTkScrollableFrame(dialog, fg_color=colors["frame_bg"])
                scroll_frame.pack(fill="both", expand=True, padx=20, pady=(0,20))
                
                # Dictionary to store checkbox variables
                checkbox_vars = {}
                
                # Add checkboxes for each file
                for file_info in found_files:
                    file_path, source_zip = file_info
                    filename = os.path.basename(file_path)
                    source_name = os.path.basename(source_zip)
                    display_text = f"{filename} (from {source_name})" if source_zip != zip_file_path else filename
                    
                    var = ctk.BooleanVar(value=False)
                    checkbox_vars[file_info] = var
                    
                    checkbox = ctk.CTkCheckBox(
                        scroll_frame,
                        text=display_text,
                        variable=var,
                        font=ctk.CTkFont(size=12),
                        text_color=colors["text"]
                    )
                    checkbox.pack(anchor="w", pady=5, padx=10)
                
                # Buttons frame
                btn_frame = ctk.CTkFrame(dialog, fg_color="transparent")
                btn_frame.pack(fill="x", padx=20, pady=(0,20))
                
                def select_all():
                    for var in checkbox_vars.values():
                        var.set(True)
                
                def deselect_all():
                    for var in checkbox_vars.values():
                        var.set(False)
                
                def on_select():
                    nonlocal selected_files
                    selected_files = [path for path, var in checkbox_vars.items() if var.get()]
                    if selected_files:
                        dialog.destroy()
                    else:
                        show_notification("Please select at least one UV map file", "error", 2000)
                
                def on_cancel():
                    nonlocal selected_files
                    selected_files = []
                    dialog.destroy()
                
                ctk.CTkButton(
                    btn_frame,
                    text="Select All",
                    command=select_all,
                    fg_color=colors["card_bg"],
                    hover_color=colors["card_hover"],
                    text_color=colors["text"],
                    width=100
                ).pack(side="left", padx=5)
                
                ctk.CTkButton(
                    btn_frame,
                    text="Deselect All",
                    command=deselect_all,
                    fg_color=colors["card_bg"],
                    hover_color=colors["card_hover"],
                    text_color=colors["text"],
                    width=100
                ).pack(side="left", padx=5)
                
                ctk.CTkButton(
                    btn_frame,
                    text="OK",
                    command=on_select,
                    fg_color=colors["accent"],
                    hover_color=colors["accent_hover"],
                    text_color=colors["accent_text"],
                    width=100
                ).pack(side="right", padx=5)
                
                ctk.CTkButton(
                    btn_frame,
                    text="Cancel",
                    command=on_cancel,
                    fg_color=colors["error"],
                    hover_color=colors["error_hover"],
                    text_color=colors["accent_text"],
                    width=100
                ).pack(side="right", padx=5)
                
                # Wait for dialog to close
                app.wait_window(dialog)
                
                if not selected_files:
                    print("User cancelled UV map selection")
                    return
            
            print(f"Selected UV Map(s): {[(os.path.basename(f), os.path.basename(z)) for f, z in selected_files]}")
            
            # Ask user where to save the file(s)
            if len(selected_files) == 1:
                # Single file - use save file dialog
                file_path, source_zip = selected_files[0]
                file_ext = os.path.splitext(file_path)[1]
                destination = filedialog.asksaveasfilename(
                    title="Save UV Map As",
                    defaultextension=file_ext,
                    initialfile=os.path.basename(file_path),
                    filetypes=[
                        ("All Files", "*.*"),
                        ("DDS Files", "*.dds"),
                        ("PNG Files", "*.png"),
                        ("JPG Files", "*.jpg")
                    ]
                )
                
                if destination:
                    with zipfile.ZipFile(source_zip, 'r') as source_zip_ref:
                        with source_zip_ref.open(file_path) as source:
                            with open(destination, 'wb') as target:
                                target.write(source.read())
                    
                    show_notification(f"✓ UV map copied successfully!", "success", 3000)
                    print(f"UV Map extracted from {source_zip} to {destination}")
            else:
                # Multiple files - use directory dialog
                destination_folder = filedialog.askdirectory(
                    title="Select Folder to Save UV Maps"
                )
                
                if destination_folder:
                    success_count = 0
                    for file_info in selected_files:
                        file_path, source_zip = file_info
                        filename = os.path.basename(file_path)
                        destination = os.path.join(destination_folder, filename)
                        
                        try:
                            with zipfile.ZipFile(source_zip, 'r') as source_zip_ref:
                                with source_zip_ref.open(file_path) as source:
                                    with open(destination, 'wb') as target:
                                        target.write(source.read())
                            success_count += 1
                            print(f"UV Map extracted: {filename} from {os.path.basename(source_zip)} to {destination}")
                        except Exception as e:
                            print(f"Failed to extract {filename}: {e}")
                    
                    show_notification(f"✓ {success_count} UV map(s) copied successfully!", "success", 3000)
                    print(f"{success_count}/{len(selected_files)} UV maps extracted to {destination_folder}")
                
    except zipfile.BadZipFile:
        show_notification(f"❌ Invalid ZIP file: {carid}.zip", "error", 4000)
        print(f"Error: {zip_file_path} is not a valid ZIP file")
    except Exception as e:
        show_notification(f"❌ Failed to extract UV map: {str(e)}", "error", 4000)
        print(f"Error extracting UV map: {e}")
        import traceback
        traceback.print_exc()


def bind_hover(frame, widgets, normal_color=None, hover_color=None):
    if normal_color is None:
        normal_color = colors["card_bg"]
    if hover_color is None:
        hover_color = colors["card_hover"]
        
    def on_enter(e):
        frame.configure(fg_color=hover_color)
    def on_leave(e):
        frame.configure(fg_color=normal_color)
    
    frame.bind("<Enter>", on_enter)
    frame.bind("<Leave>", on_leave)
    for w in widgets:
        w.bind("<Enter>", on_enter)
        w.bind("<Leave>", on_leave)

for carid, name in car_id_list:
    # Modern card design
    card_frame = ctk.CTkFrame(
        carlist_scroll,
        corner_radius=14,
        fg_color=colors["card_bg"],
        border_width=1,
        border_color=colors["border"]
    )
    card_frame.pack(fill="x", pady=6, padx=10)

    inner_frame = ctk.CTkFrame(
        card_frame,
        corner_radius=14,
        fg_color="transparent"
    )
    inner_frame.pack(fill="x", padx=4, pady=4)

    # Icon + Text container
    text_container = ctk.CTkFrame(inner_frame, fg_color="transparent")
    text_container.pack(side="left", fill="x", expand=True, padx=12, pady=10)
    
    # Car emoji/icon
    ctk.CTkLabel(
        text_container,
        text="🚗",
        font=ctk.CTkFont(size=20),
        anchor="w"
    ).pack(side="left", padx=(0, 10))
    
    # Text stack
    text_stack = ctk.CTkFrame(text_container, fg_color="transparent")
    text_stack.pack(side="left", fill="x", expand=True)
    
    ctk.CTkLabel(
        text_stack,
        text=name,
        anchor="w",
        font=ctk.CTkFont(size=14, weight="bold"),
        text_color=colors["text"]
    ).pack(anchor="w")
    
    ctk.CTkLabel(
        text_stack,
        text=carid,
        anchor="w",
        font=ctk.CTkFont(size=11),
        text_color=colors["text_secondary"]
    ).pack(anchor="w")

    # Buttons container
    btn_container = ctk.CTkFrame(inner_frame, fg_color="transparent")
    btn_container.pack(side="right", padx=8, pady=8)

    # Modern styled buttons
    uv_btn = ctk.CTkButton(
        btn_container,
        text="📐 UV Map",
        width=110,
        height=36,
        fg_color=colors["success"],
        hover_color=colors["accent_hover"],
        text_color=colors["accent_text"],
        corner_radius=10,
        font=ctk.CTkFont(size=12, weight="bold"),
        command=lambda c=carid: get_uv_map(c)
    )
    uv_btn.pack(side="left", padx=4)

    copy_btn = ctk.CTkButton(
        btn_container,
        text="📋 Copy ID",
        width=100,
        height=36,
        fg_color=colors["frame_bg"],
        hover_color=colors["card_hover"],
        text_color=colors["text"],
        corner_radius=10,
        font=ctk.CTkFont(size=12),
        border_width=1,
        border_color=colors["border"],
        command=lambda c=carid: copy_carid(c)
    )
    copy_btn.pack(side="left", padx=4)

    # Use robust hover system
    setup_robust_hover(card_frame, carid)

    carlist_items.append((card_frame, carid, name))

def update_carlist(*args):
    query = carlist_search_var.get().lower()
    for row_frame, carid, name in carlist_items:
        row_frame.pack_forget()
        if query in carid.lower() or query in name.lower():
            row_frame.pack(fill="x", pady=8, padx=8)
    carlist_scroll._parent_canvas.yview_moveto(0)

carlist_search_var.trace_add("write", update_carlist)

# -----------------------
# Settings Tab
# -----------------------
developer_mode_var = ctk.BooleanVar(value=False)
debug_mode_var = ctk.BooleanVar(value=False)

# Frame to hold debug mode toggle (hidden by default)
debug_mode_frame = ctk.CTkFrame(settings_tab, fg_color="transparent")

def toggle_developer_mode():
    global developer_tab
    if developer_mode_var.get():
        print("Developer mode enabled")
        # Create developer tab if it doesn't exist
        if developer_tab is None:
            developer_tab = ctk.CTkFrame(main_container, fg_color=colors["app_bg"])
            setup_developer_tab()
            # Add developer button to menu
            developer_btn = ctk.CTkButton(
                menu_frame,
                text="   Developer   ",
                width=110,
                height=36,
                fg_color="transparent",
                hover_color=colors["card_hover"],
                text_color=colors["text_secondary"],
                corner_radius=8,
                font=ctk.CTkFont(size=12),
                command=lambda: switch_view("developer")
            )
            developer_btn.pack(side="left", padx=3)
            menu_buttons["developer"] = developer_btn
        debug_mode_frame.pack(anchor="w", padx=10, pady=(0,10))
    else:
        print("Developer mode disabled")
        # Remove developer tab
        if developer_tab is not None:
            developer_tab.pack_forget()
            # Remove developer button from menu
            if "developer" in menu_buttons:
                menu_buttons["developer"].destroy()
                del menu_buttons["developer"]
        debug_mode_frame.pack_forget()
        if debug_mode_var.get():
            debug_mode_var.set(False)
            toggle_debug_mode()

ctk.CTkLabel(settings_tab, text="Settings", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=10, pady=(10,5))

# Theme toggle
theme_frame = ctk.CTkFrame(settings_tab, fg_color="transparent")
theme_frame.pack(anchor="w", padx=10, pady=(0,10), fill="x")

ctk.CTkLabel(theme_frame, text="Theme:", text_color=colors["text"]).pack(side="left", padx=(0,10))
ctk.CTkLabel(theme_frame, text="Dark Mode", text_color=colors["text"]).pack(side="left", padx=(0,5))
theme_switch = ctk.CTkSwitch(theme_frame, text="", command=toggle_theme, width=50)
if current_theme == "light":
    theme_switch.select()
theme_switch.pack(side="left", padx=5)
ctk.CTkLabel(theme_frame, text="Light Mode", text_color=colors["text"]).pack(side="left")

# Developer mode toggle
developer_checkbox = ctk.CTkCheckBox(
    settings_tab,
    text="Developer Mode",
    variable=developer_mode_var,
    command=toggle_developer_mode
)
developer_checkbox.pack(anchor="w", padx=10, pady=(0,10))

# Debug mode toggle (only visible when developer mode is on)
debug_checkbox = ctk.CTkCheckBox(
    debug_mode_frame,
    text="Debug Mode (Opens debug console)",
    variable=debug_mode_var,
    command=toggle_debug_mode
)
debug_checkbox.pack(anchor="w")

# -----------------------
# About Tab
# -----------------------
about_frame = ctk.CTkFrame(about_tab, fg_color=colors["frame_bg"])
about_frame.pack(fill="both", expand=True, padx=20, pady=20)

ctk.CTkLabel(about_frame, text="BeamSkin Studio", font=ctk.CTkFont(size=26, weight="bold"), text_color=colors["text"]).pack(pady=(10,5))
ctk.CTkLabel(about_frame, text="Credits:", font=ctk.CTkFont(size=22, weight="bold"), text_color=colors["text"]).pack(pady=(50,5))
ctk.CTkLabel(about_frame, text="Developer:", font=ctk.CTkFont(size=19, weight="bold"), text_color=colors["text"]).pack(pady=(10,0))

socials_frame = ctk.CTkFrame(about_frame, fg_color="transparent", height=0)
socials_frame.pack_forget()

def toggle_socials(frame):
    target_height = 45
    if frame.winfo_ismapped():
        def collapse():
            frame.pack_propagate(False)
            for i in range(frame.winfo_height(), -1, -5):
                frame.configure(height=max(0,i))
                time.sleep(0.01)
            frame.pack_forget()
        threading.Thread(target=collapse, daemon=True).start()
    else:
        frame.configure(height=0)
        frame.pack(fill="x", pady=(2,10))
        frame.pack_propagate(False)
        def expand():
            for i in range(0, target_height+2, 5):
                frame.configure(height=i)
                time.sleep(0.01)
            frame.pack_propagate(True)
        threading.Thread(target=expand, daemon=True).start()

ctk.CTkButton(about_frame, text="@Burzt_YT", font=ctk.CTkFont(size=17, weight="bold"), command=lambda: toggle_socials(socials_frame), fg_color=colors["card_bg"], hover_color=colors["card_hover"], text_color=colors["text"]).pack(pady=(2,0))
ctk.CTkButton(socials_frame, text="Linktree", width=120, font=ctk.CTkFont(size=15), fg_color=colors["accent"],
               hover_color=colors["accent_hover"], text_color=colors["accent_text"],
               command=lambda: [webbrowser.open("https://linktr.ee/burzt_yt"), toggle_socials(socials_frame)]).pack(pady=5)

ctk.CTkLabel(about_frame, text=f"Version: {CURRENT_VERSION}", font=ctk.CTkFont(size=14), text_color=colors["text"]).pack(side="bottom", pady=(0,10))

# -----------------------
# Developer Tab setup
# -----------------------
developer_tab = None

if os.path.exists(ADDED_VEHICLES_FILE):
    try:
        with open(ADDED_VEHICLES_FILE, "r") as f:
            added_vehicles = json.load(f)
    except:
        added_vehicles = {}

def setup_developer_tab():
    global developer_tab
    
    # Clear existing widgets if any
    if developer_tab is not None:
        for widget in developer_tab.winfo_children():
            widget.destroy()
    
    ctk.CTkLabel(developer_tab, text="Add New Vehicle", font=ctk.CTkFont(size=16, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=10, pady=(10,5))
    
    input_frame = ctk.CTkFrame(developer_tab, fg_color=colors["frame_bg"], corner_radius=12)
    input_frame.pack(fill="x", padx=10, pady=(0,10))
    
    carid_var = ctk.StringVar()
    carname_var = ctk.StringVar()
    
    ctk.CTkLabel(input_frame, text="Car ID:", text_color=colors["text"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    carid_entry = ctk.CTkEntry(input_frame, textvariable=carid_var, fg_color=colors["card_bg"], text_color=colors["text"])
    carid_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    ctk.CTkLabel(input_frame, text="Car Name:", text_color=colors["text"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
    carname_entry = ctk.CTkEntry(input_frame, textvariable=carname_var, fg_color=colors["card_bg"], text_color=colors["text"])
    carname_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
    
    json_path_var = ctk.StringVar()
    ctk.CTkLabel(input_frame, text="JSON File:", text_color=colors["text"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
    json_entry = ctk.CTkEntry(input_frame, textvariable=json_path_var, state="readonly", fg_color=colors["card_bg"], text_color=colors["text"])
    json_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
    
    def select_json_file():
        path = filedialog.askopenfilename(title="Select JSON File", filetypes=[("JSON Files", "*.json")])
        if path:
            json_path_var.set(path)
            print(f"JSON file selected: {path}")
    
    json_browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=select_json_file,
                                    fg_color=colors["card_bg"], hover_color=colors["card_hover"], text_color=colors["text"])
    json_browse_btn.grid(row=2, column=2, padx=5, pady=5)
    
    jbeam_path_var = ctk.StringVar()
    ctk.CTkLabel(input_frame, text="JBEAM File:", text_color=colors["text"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
    jbeam_entry = ctk.CTkEntry(input_frame, textvariable=jbeam_path_var, state="readonly", fg_color=colors["card_bg"], text_color=colors["text"])
    jbeam_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
    
    def select_jbeam_file():
        path = filedialog.askopenfilename(title="Select JBEAM File", filetypes=[("JBEAM Files", "*.jbeam")])
        if path:
            jbeam_path_var.set(path)
            print(f"JBEAM file selected: {path}")
    
    jbeam_browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=select_jbeam_file,
                                     fg_color=colors["card_bg"], hover_color=colors["card_hover"], text_color=colors["text"])
    jbeam_browse_btn.grid(row=3, column=2, padx=5, pady=5)
    
    # Add preview image field (optional)
    image_path_var = ctk.StringVar()
    ctk.CTkLabel(input_frame, text="Preview Image (Optional):", text_color=colors["text"]).grid(row=4, column=0, padx=5, pady=5, sticky="w")
    image_entry = ctk.CTkEntry(input_frame, textvariable=image_path_var, state="readonly", fg_color=colors["card_bg"], text_color=colors["text"])
    image_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
    
    def select_image_file():
        path = filedialog.askopenfilename(
            title="Select Preview Image (JPG only)", 
            filetypes=[("JPEG Images", "*.jpg"), ("JPEG Images", "*.jpeg")]
        )
        if path:
            # Validate it's a JPG file
            if path.lower().endswith(('.jpg', '.jpeg')):
                image_path_var.set(path)
                print(f"Preview image selected: {path}")
            else:
                show_notification("Please select a JPG/JPEG image file", "error")
    
    image_browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=select_image_file,
                                     fg_color=colors["card_bg"], hover_color=colors["card_hover"], text_color=colors["text"])
    image_browse_btn.grid(row=4, column=2, padx=5, pady=5)
    
    input_frame.columnconfigure(1, weight=1)
    
    # Add status label and progress bar (hidden by default)
    dev_status_label = ctk.CTkLabel(developer_tab, text="", text_color=colors["text"], font=ctk.CTkFont(size=12))
    dev_status_label.pack(padx=10, pady=(10,5))
    dev_status_label.pack_forget()
    
    dev_progress_bar = ctk.CTkProgressBar(developer_tab)
    dev_progress_bar.pack(fill="x", padx=10, pady=(0,5))
    dev_progress_bar.pack_forget()

    def add_vehicle():
        carid = carid_var.get().strip()
        carname = carname_var.get().strip()
        json_path = json_path_var.get().strip()
        jbeam_path = jbeam_path_var.get().strip()
        image_path = image_path_var.get().strip()

        print(f"\nAttempting to add vehicle: {carname} (ID: {carid})")

        if not carid or not carname:
            print("ERROR: Car ID or Car Name is empty")
            show_notification("Car ID and Car Name cannot be empty", "error")
            return

        if " " in carid:
            print("ERROR: Car ID contains spaces")
            show_notification("Car ID cannot contain spaces", "error")
            return

        if not json_path:
            print("ERROR: No JSON file selected")
            show_notification("Please select a JSON file", "error")
            return

        # JBEAM is now optional
        if jbeam_path:
            print("JBEAM file will be processed")
        else:
            print("No JBEAM file selected - skipping JBEAM processing")
        
        # Preview image is optional
        if image_path:
            print(f"Preview image will be copied: {image_path}")
        else:
            print("No preview image selected - skipping image copy")

        if carid in [v[0] for v in car_id_list] or carid in added_vehicles:
            print(f"ERROR: Car ID '{carid}' already exists")
            show_notification(f"Car ID '{carid}' already exists", "error")
            return

        # Show progress UI above "Added Vehicles" section
        dev_status_label.configure(text="Preparing to add vehicle...")
        dev_status_label.pack(padx=10, pady=(10,5))
        dev_progress_bar.pack(fill="x", padx=10, pady=(0,10))
        dev_progress_bar.set(0)
        add_button.configure(state="disabled", text="Adding...")

        def update_progress(value, status_text):
            """Update progress bar and status label"""
            dev_progress_bar.set(value)
            dev_status_label.configure(text=status_text)
            developer_tab.update_idletasks()

        try:
            update_progress(0.1, "Saving vehicle information...")
            added_vehicles[carid] = carname
            save_added_vehicles()
            print(f"Vehicle saved to added_vehicles.json")

            update_progress(0.2, "Creating vehicle folders...")
            create_vehicle_folders(carid)
            print(f"Created vehicle folders for {carid}")

            skinname_folder = os.path.join(VEHICLE_FOLDER, carid, "SKINNAME")
            
            # Edit and copy the JSON file (using 'skinname' as placeholder)
            update_progress(0.3, "Processing JSON file...")
            print(f"\n--- Processing JSON file ---")
            edit_material_json(json_path, skinname_folder, carid)
            
            if jbeam_path:
                # Edit and copy the JBEAM file (using 'skinname' as placeholder)
                update_progress(0.6, "Processing JBEAM file...")
                print(f"\n--- Processing JBEAM file ---")
                edit_jbeam_material(jbeam_path, skinname_folder, carid)
                
                # Check if JBEAM was actually saved (with original filename)
                jbeam_filename = os.path.basename(jbeam_path)
                jbeam_output = os.path.join(skinname_folder, jbeam_filename)
                if not os.path.exists(jbeam_output):
                    print(f"\nWARNING: JBEAM file was not created!")
                    print(f"Expected location: {jbeam_output}")
                    raise Exception(
                        "Failed to process JBEAM file.\n\n"
                        "Please make sure the selected JBEAM file is valid."
                    )
            
            # Copy preview image if provided
            if image_path:
                update_progress(0.7, "Copying preview image...")
                print(f"\n--- Copying preview image ---")
                
                # Create image folder structure: imagesforgui/vehicles/{carid}/
                image_folder = os.path.join("imagesforgui", "vehicles", carid)
                os.makedirs(image_folder, exist_ok=True)
                
                # Copy and rename to default.jpg
                import shutil as img_shutil
                dest_path = os.path.join(image_folder, "default.jpg")
                img_shutil.copy2(image_path, dest_path)
                
                print(f"Preview image copied to: {dest_path}")
            
            update_progress(0.8, "Updating vehicle lists...")
            car_id_list.append((carid, carname))
            add_carlist_card(carid, carname, developer_added=True)
            add_vehicle_button(carid, display_name=carname)

            update_progress(0.9, "Cleaning up...")
            carid_var.set("")
            carname_var.set("")
            json_path_var.set("")
            jbeam_path_var.set("")
            image_path_var.set("")
            
            update_progress(1.0, "Vehicle added successfully!")
            print(f"Vehicle '{carname}' added successfully!\n")
            
            # Hide progress UI after a short delay
            app.after(2000, lambda: dev_progress_bar.pack_forget())
            app.after(2000, lambda: dev_status_label.pack_forget())
            
            show_notification(f"✓ Vehicle '{carname}' added successfully!", "success", 5000)
            refresh_developer_list()
            
        except Exception as e:
            print(f"ERROR processing files: {e}")
            dev_status_label.configure(text="Error: Failed to add vehicle")
            show_notification(f"Failed to add vehicle: {str(e)}", "error", 5000)
            delete_vehicle_folders(carid)
            del added_vehicles[carid]
            save_added_vehicles()
            
            # Hide progress UI after error
            app.after(2000, lambda: dev_progress_bar.pack_forget())
            app.after(2000, lambda: dev_status_label.pack_forget())
        finally:
            add_button.configure(state="normal", text="Add Vehicle")

    add_button = ctk.CTkButton(input_frame, text="Add Vehicle", command=add_vehicle,
                               fg_color=colors["accent"], hover_color=colors["accent_hover"], text_color=colors["accent_text"])
    add_button.grid(row=5, column=0, columnspan=3, padx=5, pady=10)
    
    # "Added Vehicles" section header
    ctk.CTkLabel(developer_tab, text="Added Vehicles", font=ctk.CTkFont(size=14, weight="bold"), text_color=colors["text"]).pack(anchor="w", padx=10, pady=(10,5))
    
    # Add status label and progress bar - appears above search
    dev_status_label = ctk.CTkLabel(developer_tab, text="", text_color=colors["text"], font=ctk.CTkFont(size=12))
    dev_status_label.pack_forget()
    
    dev_progress_bar = ctk.CTkProgressBar(developer_tab)
    dev_progress_bar.pack_forget()
    
    # Search box for added vehicles
    dev_search_var = ctk.StringVar()
    dev_search_entry = ctk.CTkEntry(
        developer_tab,
        textvariable=dev_search_var,
        placeholder_text="Search added vehicles...",
        placeholder_text_color="#888888",
        fg_color=colors["card_bg"],
        text_color=colors["text"]
    )
    dev_search_entry.pack(fill="x", padx=10, pady=(0,5))
    
    # List frame for added vehicles
    dev_list_frame = ctk.CTkScrollableFrame(developer_tab, height=300, fg_color=colors["frame_bg"], corner_radius=12)
    dev_list_frame.pack(fill="both", expand=True, padx=10, pady=(0,10))
    
    # Store list items for search filtering
    dev_list_items = []

    def delete_vehicle(carid):
        print(f"\nDeleting vehicle: {carid}")
        if carid in added_vehicles:
            del added_vehicles[carid]
            save_added_vehicles()

            delete_vehicle_folders(carid)
            print(f"Deleted vehicle folders for {carid}")

            # Remove from car_id_list
            for i, item in enumerate(car_id_list):
                if item[0] == carid:
                    car_id_list.pop(i)
                    break

            # Remove from carlist (Car List tab)
            for i, (card, c, n) in enumerate(carlist_items):
                if c == carid:
                    card.destroy()
                    carlist_items.pop(i)
                    break
            
            # Remove from sidebar_vehicle_buttons
            for i, (container, cid, dname, add_frame) in enumerate(sidebar_vehicle_buttons):
                if cid == carid:
                    container.destroy()
                    sidebar_vehicle_buttons.pop(i)
                    break

            print(f"Vehicle '{carid}' deleted successfully\n")
            show_notification(f"✓ Vehicle '{carid}' deleted successfully!", "success", 3000)
            refresh_developer_list()

    def refresh_developer_list():
        global dev_list_items
        dev_list_items = []
        
        for widget in dev_list_frame.winfo_children():
            widget.destroy()
        
        # Get search term
        search_term = dev_search_var.get().lower()
        
        # Populate list with added vehicles
        if not added_vehicles:
            # Show "no vehicles" message
            no_vehicles_label = ctk.CTkLabel(
                dev_list_frame,
                text="No custom vehicles added yet.\nUse the form above to add vehicles.",
                text_color=colors["text_secondary"],
                font=ctk.CTkFont(size=12)
            )
            no_vehicles_label.pack(pady=50)
        else:
            # Sort vehicles alphabetically by name
            sorted_vehicles = sorted(added_vehicles.items(), key=lambda x: x[1].lower())
            
            for carid, carname in sorted_vehicles:
                # Filter by search term
                if search_term and search_term not in carid.lower() and search_term not in carname.lower():
                    continue
                
                # Create item frame
                item_frame = ctk.CTkFrame(
                    dev_list_frame,
                    fg_color=colors["card_bg"],
                    corner_radius=8,
                    border_width=1,
                    border_color=colors["border"]
                )
                item_frame.pack(fill="x", padx=5, pady=3)
                
                # Vehicle info
                info_label = ctk.CTkLabel(
                    item_frame,
                    text=f"{carname}  —  {carid}",
                    text_color=colors["text"],
                    font=ctk.CTkFont(size=12),
                    anchor="w"
                )
                info_label.pack(side="left", fill="x", expand=True, padx=10, pady=8)
                
                # Add hover preview bindings to the item frame
                item_frame.bind("<Enter>", lambda e, c=carid: schedule_hover_preview(c, e.widget))
                item_frame.bind("<Leave>", lambda e: hide_hover_preview())
                
                # Also bind to info label for better coverage
                info_label.bind("<Enter>", lambda e, c=carid: schedule_hover_preview(c, e.widget))
                info_label.bind("<Leave>", lambda e: hide_hover_preview())
                
                # Delete button
                delete_btn = ctk.CTkButton(
                    item_frame,
                    text="Delete",
                    width=80,
                    height=28,
                    fg_color="#B71C1C",  # Red
                    hover_color="#D32F2F",
                    text_color="white",
                    corner_radius=6,
                    command=lambda c=carid: delete_vehicle(c)
                )
                delete_btn.pack(side="right", padx=10, pady=8)
                
                # Force hide preview when hovering over delete button
                delete_btn.bind("<Enter>", lambda e: hide_hover_preview(force=True), add=True)
                
                dev_list_items.append((item_frame, carid, carname))
    
    # Connect search to refresh function
    dev_search_var.trace_add("write", lambda *args: refresh_developer_list())
    
    # Initial population of the list
    refresh_developer_list()
            
        
# ===========================
# POPULATE SIDEBAR WITH VEHICLES (Mods Studio 2 Tree)
# ===========================
print("Populating sidebar with vehicles...")

# ===========================
# POPULATE SIDEBAR WITH EXPANDABLE VEHICLE BUTTONS
# ===========================
def toggle_vehicle_add_button(carid, add_button_frame):
    """Toggle the add button for a vehicle"""
    global expanded_vehicle_carid
    
    # If clicking the same vehicle, collapse it
    if expanded_vehicle_carid == carid:
        add_button_frame.pack_forget()
        expanded_vehicle_carid = None
    else:
        # Collapse any previously expanded vehicle
        if expanded_vehicle_carid is not None:
            for btn_frame, car_id, _, add_btn_frame in sidebar_vehicle_buttons:
                if car_id == expanded_vehicle_carid:
                    add_btn_frame.pack_forget()
                    break
        
        # Expand this vehicle
        add_button_frame.pack(fill="x", padx=5, pady=(0, 5))
        expanded_vehicle_carid = carid

def add_vehicle_to_project_from_sidebar(carid):
    """Add a vehicle to the project from sidebar"""
    global selected_carid, selected_display_name
    
    # Find display name
    display_name = VEHICLE_IDS.get(carid, carid)
    for _, cid, dname, _ in sidebar_vehicle_buttons:
        if cid == carid:
            display_name = dname
            break
    
    selected_carid = carid
    selected_display_name = display_name
    
    # Call the original add car to project function
    add_car_to_project()
    
    # Collapse the add button after adding
    for btn_frame, car_id, _, add_btn_frame in sidebar_vehicle_buttons:
        if car_id == carid:
            add_btn_frame.pack_forget()
            break

        if car_id == carid:
            add_btn_frame.pack_forget()
            break

def add_carlist_card(carid, name, developer_added=False):
    """Add a vehicle card to the Car List tab"""
    insert_position = 0
    for i, (card, cid, cname) in enumerate(carlist_items):
        if cname.lower() > name.lower():
            insert_position = i
            break
        insert_position = i + 1
    
    card_frame = ctk.CTkFrame(
        carlist_scroll,
        corner_radius=12,
        fg_color=colors["card_bg"],
        border_width=1,
        border_color=colors["border"]
    )

    inner_frame = ctk.CTkFrame(
        card_frame,
        corner_radius=12,
        fg_color=colors["card_bg"],
        border_width=0
    )
    inner_frame.pack(fill="x", padx=5, pady=5)

    lbl = ctk.CTkLabel(
        inner_frame,
        text=f"{carid}  —  {name}",
        anchor="w",
        justify="left",
        font=carlist_font,
        text_color=colors["text"]
    )
    lbl.pack(side="left", fill="x", expand=True, padx=(10,5), pady=8)

    widgets_for_hover = [inner_frame, lbl]
    
    # Only add UV Map button for default cars (not user-added)
    if not developer_added:
        uv_btn = ctk.CTkButton(
            inner_frame,
            text="Get UV Map",
            width=100,
            height=28,
            fg_color="#2E7D32",  # Green color to stand out
            hover_color="#1B5E20",  # Darker green on hover
            text_color="white",
            corner_radius=12,
            command=lambda c=carid: get_uv_map(c)
        )
        uv_btn.pack(side="right", padx=(5,10), pady=8)
        widgets_for_hover.append(uv_btn)
        
        # Add explicit bindings to FORCE hide preview when hovering over UV button
        uv_btn.bind("<Enter>", lambda e: hide_hover_preview(force=True), add=True)

    btn = ctk.CTkButton(
        inner_frame,
        text="Copy ID",
        width=90,
        height=28,
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        text_color=colors["accent_text"],
        corner_radius=12,
        command=lambda c=carid: copy_carid(c)
    )
    btn.pack(side="right", padx=10 if developer_added else 5, pady=8)
    
    # Add explicit bindings to FORCE hide preview when hovering over Copy ID button
    btn.bind("<Enter>", lambda e: hide_hover_preview(force=True), add=True)

    # Use robust hover system for complete coverage
    setup_robust_hover(card_frame, carid)

    carlist_items.insert(insert_position, (card_frame, carid, name))
    
    for widget in carlist_scroll.winfo_children():
        widget.pack_forget()
    
    for card, cid, cname in carlist_items:
        card.pack(fill="x", pady=8, padx=8)

def add_vehicle_button(carid, display_name=None):
    """Add vehicle to sidebar (the only visible vehicle list in the UI)"""
    name_to_show = display_name if display_name else carid
    
    # Find insert position (alphabetically)
    insert_position = len(sidebar_vehicle_buttons)
    for i, (container, cid, dname, add_btn_frame) in enumerate(sidebar_vehicle_buttons):
        if dname.lower() > name_to_show.lower():
            insert_position = i
            break
    
    # Create container frame for this vehicle
    container_frame = ctk.CTkFrame(sidebar_scroll, corner_radius=8, fg_color="transparent")
    
    # Create main button
    btn = ctk.CTkButton(
        container_frame,
        text=name_to_show,
        fg_color=colors["card_bg"],
        hover_color=colors["card_hover"],
        height=38,
        corner_radius=8,
        text_color=colors["text"],
        anchor="w",
        font=ctk.CTkFont(size=11)
    )
    btn.pack(fill="x")
    
    # Create add button frame (hidden by default)
    add_button_frame = ctk.CTkFrame(container_frame, fg_color="transparent")
    
    add_btn = ctk.CTkButton(
        add_button_frame,
        text="➕ Add to Project",
        command=lambda c=carid: add_vehicle_to_project_from_sidebar(c),
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        text_color=colors["accent_text"],
        height=32,
        corner_radius=6,
        font=ctk.CTkFont(size=10, weight="bold")
    )
    add_btn.pack(fill="x")
    
    # Click vehicle button to toggle add button
    btn.configure(command=lambda c=carid, frame=add_button_frame: toggle_vehicle_add_button(c, frame))
    
    # Hover preview bindings
    btn.bind("<Enter>", lambda e, c=carid, w=btn: schedule_hover_preview(c, w))
    btn.bind("<Leave>", lambda e: hide_hover_preview())
    
    # Insert at correct position
    sidebar_vehicle_buttons.insert(insert_position, (container_frame, carid, name_to_show, add_button_frame))
    
    # Repack all buttons in order
    for widget in sidebar_scroll.winfo_children():
        if widget in [container for container, _, _, _ in sidebar_vehicle_buttons]:
            widget.pack_forget()
    
    for container, cid, dname, add_frame in sidebar_vehicle_buttons:
        container.pack(fill="x", pady=2, padx=0)

print("Populating sidebar with expandable vehicles...")

# Add all default vehicles to sidebar with expandable add buttons
for carid in sorted(VEHICLE_IDS.keys(), key=lambda c: VEHICLE_IDS[c].lower()):
    display_name = VEHICLE_IDS[carid]
    
    # Container for vehicle button + add button
    container_frame = ctk.CTkFrame(sidebar_scroll, corner_radius=8, fg_color="transparent")
    
    # Main vehicle button
    btn = ctk.CTkButton(
        container_frame,
        text=display_name,
        fg_color=colors["card_bg"],
        hover_color=colors["card_hover"],
        height=38,
        corner_radius=8,
        text_color=colors["text"],
        anchor="w",
        font=ctk.CTkFont(size=11)
    )
    btn.pack(fill="x")
    
    # Add button (hidden by default)
    add_button_frame = ctk.CTkFrame(container_frame, fg_color="transparent")
    
    add_btn = ctk.CTkButton(
        add_button_frame,
        text="➕ Add to Project",
        command=lambda c=carid: add_vehicle_to_project_from_sidebar(c),
        fg_color=colors["accent"],
        hover_color=colors["accent_hover"],
        text_color=colors["accent_text"],
        height=32,
        corner_radius=6,
        font=ctk.CTkFont(size=10, weight="bold")
    )
    add_btn.pack(fill="x")
    
    # Click vehicle button to toggle add button
    btn.configure(command=lambda c=carid, frame=add_button_frame: toggle_vehicle_add_button(c, frame))
    
    # Hover preview
    btn.bind("<Enter>", lambda e, c=carid, w=btn: schedule_hover_preview(c, w))
    btn.bind("<Leave>", lambda e: hide_hover_preview())
    
    # Store: (container, carid, display_name, add_button_frame)
    sidebar_vehicle_buttons.append((container_frame, carid, display_name, add_button_frame))
    container_frame.pack(fill="x", pady=2, padx=0)


print(f"Added {len(sidebar_vehicle_buttons)} expandable vehicles to sidebar")

# Add user-added vehicles
for carid, carname in added_vehicles.items():
    # Add to carlist and vehicle buttons (original functionality)
    add_carlist_card(carid, carname, developer_added=True)
    add_vehicle_button(carid, display_name=carname)
    car_id_list.append((carid, carname))

def on_closing():
    print("\nShutting down BeamSkin Studio...")
    app.destroy()
app.protocol("WM_DELETE_WINDOW", on_closing)

if __name__ == "__main__":
    print(f"\n[DEBUG] ========================================")
    print(f"[DEBUG] BeamSkin Studio Starting...")
    print(f"[DEBUG] Version: {CURRENT_VERSION}")
    print(f"[DEBUG] ========================================\n")
    
    # Show WIP warning on first launch
    print(f"[DEBUG] Checking for first launch warning...")
    show_wip_warning()
    
    # Center the window on screen
    print(f"[DEBUG] Centering window...")
    center_window(app)
    
    # Create a thread so the UI stays responsive while checking for updates
    print(f"[DEBUG] Starting update check thread...")
    threading.Thread(target=check_for_updates, daemon=True).start()
    
    # CRITICAL: Initialize universal scroll handler
    print(f"[DEBUG] Initializing scroll handler...")
    app.after(100, setup_universal_scroll_handler)
    
    print(f"[DEBUG] Starting main event loop...")
    print(f"[DEBUG] ========================================\n")
    app.mainloop()