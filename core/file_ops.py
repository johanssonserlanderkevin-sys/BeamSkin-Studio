"""File operations for JBEAM/JSON editing"""
import os
import json
import re
import copy
import shutil
from tkinter import messagebox

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
        print(f"[DEBUG] Deleted preview image folder: {image_folder}")


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
        print(f"[DEBUG] \n--- Starting JSON Edit Process ---")
        print(f"[DEBUG] Reading JSON file: {json_path}")
        print(f"[DEBUG] Target Car ID: {carid}")
        print(f"[DEBUG] Using placeholder: 'skinname' (will be replaced by generator)")
        
        # Read the raw file content
        with open(json_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean the JSON content
        print("[DEBUG] Cleaning JSON (removing comments and fixing trailing commas)...")
        
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
            print(f"[DEBUG] ERROR: Could not parse JSON even after cleaning - {e}")
            print("[DEBUG] Attempting to save cleaned version for manual inspection...")
            cleaned_path = json_path + ".cleaned"
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[DEBUG] Cleaned JSON saved to: {cleaned_path}")
            raise
        
        print(f"[DEBUG] Original JSON contains {len(data)} entries")
        
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
            print("[DEBUG] WARNING: No skin entries found in JSON")
            return
        
        # Use the first skin suffix found
        target_suffix = list(skin_suffixes)[0]
        print(f"[DEBUG] Target skin suffix: {target_suffix}")
        
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
                    
                    print(f"[DEBUG] Processing: {key} → {new_key}")
                    
                    # Deep copy the value to avoid modifying original
                    new_value = copy.deepcopy(value)
                    
                    # Update name and mapTo fields
                    if "name" in new_value:
                        new_value["name"] = new_key
                        print(f"[DEBUG]   Updated name: {new_key}")
                    
                    if "mapTo" in new_value:
                        new_value["mapTo"] = new_key
                        print(f"[DEBUG]   Updated mapTo: {new_key}")
                    
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
                                print(f"[DEBUG]   Updated baseColorMap in Stage 2:")
                                print(f"[DEBUG]     Old: {old_path}")
                                print(f"[DEBUG]     New: {new_path}")
                    
                    filtered_data[new_key] = new_value
        
        print(f"[DEBUG] \nFiltered JSON contains {len(filtered_data)} entries")
        
        # Write the edited JSON back to the folder
        json_filename = os.path.basename(json_path)
        output_path = os.path.join(skinname_folder, json_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4)
        
        print(f"[DEBUG] Edited JSON saved to: {output_path}")
        print(f"[DEBUG] --- JSON Edit Complete ---\n")
        
    except json.JSONDecodeError as e:
        print(f"[DEBUG] ERROR: Invalid JSON format - {e}")
        raise Exception(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        print(f"[DEBUG] ERROR during JSON editing: {e}")
        raise
        
    except json.JSONDecodeError as e:
        print(f"[DEBUG] ERROR: Invalid JSON format - {e}")
        raise Exception(f"Invalid JSON format: {str(e)}")
    except Exception as e:
        print(f"[DEBUG] ERROR during JSON editing: {e}")
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
        print(f"[DEBUG] \n--- Starting JBEAM Edit Process ---")
        print(f"[DEBUG] Reading JBEAM file: {jbeam_path}")
        print(f"[DEBUG] Target Car ID: {carid}")
        print(f"[DEBUG] Using placeholders: 'Author Name' and 'Skin Name' (will be replaced by generator)")
        
        # Read the raw file content
        with open(jbeam_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Clean the JBEAM content (remove comments)
        print("[DEBUG] Cleaning JBEAM (removing comments)...")
        
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
            print(f"[DEBUG] ERROR: Could not parse JBEAM even after cleaning - {e}")
            print("[DEBUG] Attempting to save cleaned version for manual inspection...")
            cleaned_path = jbeam_path + ".cleaned"
            with open(cleaned_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[DEBUG] Cleaned JBEAM saved to: {cleaned_path}")
            raise
        
        print(f"[DEBUG] Original JBEAM contains {len(data)} entries")
        
        # STEP 1: Find all skin entries (keys containing "_skin_")
        skin_entries = []
        for key in data.keys():
            if "_skin_" in key:
                skin_entries.append((key, data[key]))
        
        if not skin_entries:
            print("[DEBUG] WARNING: No skin entries found in JBEAM")
            return
        
        print(f"[DEBUG] Found {len(skin_entries)} skin entries")
        
        # STEP 2: Keep only the FIRST skin entry
        first_skin_key, first_skin_value = skin_entries[0]
        print(f"[DEBUG] \n✓ Canonical skin identified: {first_skin_key}")
        
        if len(skin_entries) > 1:
            removed_skins = [key for key, _ in skin_entries[1:]]
            print(f"[DEBUG] ✗ Removing {len(removed_skins)} other skin(s): {', '.join(removed_skins)}")
        
        # STEP 3: Create the new skin entry
        new_key = f"{carid}_skin_skinname"
        new_value = copy.deepcopy(first_skin_value)
        
        print(f"[DEBUG] \n✓ Renaming: {first_skin_key} → {new_key}")
        
        # STEP 4: Update authors and name fields to placeholders
        if "information" in new_value and isinstance(new_value["information"], dict):
            if "authors" in new_value["information"]:
                old_author = new_value["information"]["authors"]
                new_value["information"]["authors"] = "Author Name"
                print(f"[DEBUG]   ✓ Updated authors: '{old_author}' → 'Author Name' (placeholder)")
            
            if "name" in new_value["information"]:
                old_name = new_value["information"]["name"]
                new_value["information"]["name"] = "Skin Name"
                print(f"[DEBUG]   ✓ Updated name: '{old_name}' → 'Skin Name' (placeholder)")
            
            # Preserve value field
            if "value" in new_value["information"]:
                print(f"[DEBUG]   ✓ Preserved value: {new_value['information']['value']}")
        
        # STEP 5: Update globalSkin to "skinname"
        if "globalSkin" in new_value:
            old_global_skin = new_value["globalSkin"]
            new_value["globalSkin"] = "skinname"
            print(f"[DEBUG]   ✓ Updated globalSkin: '{old_global_skin}' → 'skinname'")
        
        # STEP 6: Preserve all other fields (slotType, etc.)
        if "slotType" in new_value:
            print(f"[DEBUG]   ✓ Preserved slotType: '{new_value['slotType']}'")
        
        # Create the filtered data with only the new skin entry
        filtered_data = {new_key: new_value}
        
        print(f"[DEBUG] \n--- Summary ---")
        print(f"[DEBUG] Original skins: {len(skin_entries)}")
        print(f"[DEBUG] Final skins: 1")
        print(f"[DEBUG] Removed: {len(skin_entries) - 1}")
        
        # Write the edited JBEAM back to the folder, keeping original filename
        jbeam_filename = os.path.basename(jbeam_path)
        output_path = os.path.join(skinname_folder, jbeam_filename)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=4)
        
        print(f"[DEBUG] Edited JBEAM saved to: {output_path}")
        print(f"[DEBUG] --- JBEAM Edit Complete ---\n")
        
    except json.JSONDecodeError as e:
        print(f"[DEBUG] ERROR: Invalid JBEAM format - {e}")
        raise Exception(f"Invalid JBEAM format: {str(e)}")
    except Exception as e:
        print(f"[DEBUG] ERROR during JBEAM editing: {e}")
        raise


