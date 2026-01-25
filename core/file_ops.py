# file_ops.py
# Complete file operations module for BeamNG Skin Studio

import os
import shutil
import tempfile
import zipfile
import getpass
import re

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def sanitize_skin_id(name):
    """
    Convert skin name to valid ID format.
    Example: "My Cool Skin" -> "my_cool_skin"
    """
    return name.lower().replace(" ", "_")

def sanitize_mod_name(name):
    """
    Clean mod name for file system use.
    Removes spaces and strips whitespace.
    """
    return name.strip().replace(" ", "_")

def get_beamng_mods_path():
    """
    Get the default BeamNG.drive mods folder path.
    Returns: C:\\Users\\{username}\\AppData\\Local\\BeamNG\\BeamNG.drive\\current\\mods
    """
    username = getpass.getuser()
    return os.path.join(
        "C:\\Users",
        username,
        "AppData",
        "Local",
        "BeamNG",
        "BeamNG.drive",
        "current",
        "mods"
    )

def zip_folder(source_dir, zip_path):
    """
    Create a ZIP file from a directory.
    
    Args:
        source_dir: Directory to zip
        zip_path: Path where ZIP file should be created
    """
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root_dir, _, files in os.walk(source_dir):
            for file in files:
                full_path = os.path.join(root_dir, file)
                relative_path = os.path.relpath(full_path, source_dir)
                zipf.write(full_path, relative_path)

# =============================================================================
# SINGLE SKIN GENERATION (LEGACY - for backward compatibility)
# =============================================================================

def generate_mod(
    mod_name,
    vehicle_id,
    skin_display_name,
    dds_path,
    output_path=None,
    progress_callback=None,
    author=None
):
    """
    Generate a single-skin mod (legacy function).
    
    Args:
        mod_name: Name of the mod/ZIP file
        vehicle_id: Car ID (e.g., "etk800")
        skin_display_name: Display name for the skin
        dds_path: Path to the DDS texture file
        output_path: Optional custom output directory
        progress_callback: Optional function to call with progress updates (0.0 to 1.0)
        author: Optional author name
    
    Returns:
        Path to the created ZIP file
    """
    print(f"\n{'='*60}")
    print(f"SINGLE SKIN MOD GENERATION")
    print(f"{'='*60}")
    print(f"Mod Name: {mod_name}")
    print(f"Vehicle ID: {vehicle_id}")
    print(f"Skin Name: {skin_display_name}")
    print(f"DDS Path: {dds_path}")
    
    # Sanitize mod name
    mod_name = sanitize_mod_name(mod_name)
    
    # Find template folder
    template_path = os.path.join(os.getcwd(), "vehicles", vehicle_id, "SKINNAME")
    
    print(f"Template path: {template_path}")
    
    if not os.path.exists(template_path):
        raise FileNotFoundError(
            f"No template found for vehicle '{vehicle_id}'.\n"
            f"Expected location: {template_path}\n\n"
            f"Please make sure the vehicle exists in the Developer tab."
        )
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Temp directory: {temp_dir}")
    
    try:
        # Create destination folder structure
        dest_skin_folder = os.path.join(temp_dir, "vehicles", vehicle_id, mod_name)
        
        # Copy template folder (exclude existing .dds files)
        def ignore_dds_files(directory, files):
            return [f for f in files if f.lower().endswith(".dds")]
        
        print(f"Copying template to: {dest_skin_folder}")
        shutil.copytree(template_path, dest_skin_folder, ignore=ignore_dds_files)
        
        if progress_callback:
            progress_callback(0.2)
        
        # Copy DDS file
        dds_filename = os.path.basename(dds_path)
        dds_dest = os.path.join(dest_skin_folder, dds_filename)
        print(f"Copying DDS: {dds_filename}")
        shutil.copy(dds_path, dds_dest)
        
        # Extract skin identifier from DDS filename (last part after underscore)
        dds_last = os.path.splitext(dds_filename)[0].split("_")[-1]
        print(f"DDS identifier: {dds_last}")
        
        if progress_callback:
            progress_callback(0.4)
        
        # Process JBEAM files
        print("Processing JBEAM files...")
        process_jbeam_files(
            dest_skin_folder,
            dds_last,
            skin_display_name,
            author or "Unknown"
        )
        
        if progress_callback:
            progress_callback(0.6)
        
        # Process JSON files
        print("Processing JSON files...")
        process_json_files(
            dest_skin_folder,
            vehicle_id,
            mod_name,
            dds_filename,
            dds_last
        )
        
        if progress_callback:
            progress_callback(0.8)
        
        # Create ZIP file
        mods_path = output_path or get_beamng_mods_path()
        os.makedirs(mods_path, exist_ok=True)
        zip_path = os.path.join(mods_path, f"{mod_name}.zip")
        
        print(f"Creating ZIP: {zip_path}")
        
        if os.path.exists(zip_path):
            raise FileExistsError(
                f"A mod named '{mod_name}.zip' already exists.\n"
                f"Please choose a different name or delete the existing file."
            )
        
        zip_folder(temp_dir, zip_path)
        
        if progress_callback:
            progress_callback(1.0)
        
        print(f"✓ Mod created successfully!")
        print(f"{'='*60}\n")
        
        return zip_path
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# =============================================================================
# MULTI-SKIN GENERATION (NEW - supports multiple cars and skins)
# =============================================================================

def generate_multi_skin_mod(
    project_data,
    output_path=None,
    progress_callback=None
):
    """
    Generate a mod with multiple cars and multiple skins per car.
    
    Args:
        project_data: Dictionary containing:
            {
                "mod_name": "MyModPack",
                "author": "Author Name",
                "cars": {
                    "car_instance_id": {
                        "base_carid": "etk800",
                        "skins": [
                            {"name": "Red Racing", "dds_path": "/path/to/skin.dds"},
                            {"name": "Blue Sport", "dds_path": "/path/to/skin2.dds"}
                        ]
                    },
                    "car_instance_id_2": {...}
                }
            }
        output_path: Optional custom output directory
        progress_callback: Optional function to call with progress updates (0.0 to 1.0)
    
    Returns:
        Path to the created ZIP file
    """
    print(f"\n{'='*60}")
    print(f"MULTI-SKIN MOD GENERATION")
    print(f"{'='*60}")
    
    # Extract project data
    mod_name = sanitize_mod_name(project_data["mod_name"])
    author = project_data.get("author", "Unknown")
    cars = project_data["cars"]
    
    # Calculate totals
    total_cars = len(cars)
    total_skins = sum(len(car_info['skins']) for car_info in cars.values())
    
    print(f"Mod Name: {mod_name}")
    print(f"Author: {author}")
    print(f"Total Cars: {total_cars}")
    print(f"Total Skins: {total_skins}")
    
    # Create temporary directory
    temp_dir = tempfile.mkdtemp()
    print(f"Temp directory: {temp_dir}")
    
    try:
        processed_skins = 0
        
        # Process each car
        for car_instance_id, car_info in cars.items():
            base_carid = car_info.get("base_carid", car_instance_id)
            skins = car_info["skins"]
            
            print(f"\n--- Processing {base_carid} ({len(skins)} skins) ---")
            
            # Find template folder
            template_path = os.path.join(os.getcwd(), "vehicles", base_carid, "SKINNAME")
            
            if not os.path.exists(template_path):
                raise FileNotFoundError(
                    f"No template found for vehicle '{base_carid}'.\n"
                    f"Expected location: {template_path}\n\n"
                    f"Please make sure the vehicle exists in the Developer tab."
                )
            
            # Process each skin for this car
            for skin_idx, skin in enumerate(skins):
                skin_name = sanitize_skin_id(skin["name"])
                dds_path = skin["dds_path"]
                
                print(f"  [{skin_idx + 1}/{len(skins)}] Processing: {skin['name']} -> {skin_name}")
                
                # Create destination folder
                dest_skin_folder = os.path.join(
                    temp_dir,
                    "vehicles",
                    base_carid,
                    skin_name
                )
                
                # Copy template folder (exclude existing .dds files)
                def ignore_dds_files(directory, files):
                    return [f for f in files if f.lower().endswith(".dds")]
                
                shutil.copytree(template_path, dest_skin_folder, ignore=ignore_dds_files)
                
                # Copy DDS file
                dds_filename = os.path.basename(dds_path)
                dds_dest = os.path.join(dest_skin_folder, dds_filename)
                shutil.copy(dds_path, dds_dest)
                
                # Extract skin identifier from DDS filename
                dds_last = os.path.splitext(dds_filename)[0].split("_")[-1]
                
                # Process JBEAM files
                process_jbeam_files(
                    dest_skin_folder,
                    dds_last,
                    skin["name"],  # Use original display name
                    author
                )
                
                # Process JSON files
                process_json_files(
                    dest_skin_folder,
                    base_carid,
                    skin_name,
                    dds_filename,
                    dds_last
                )
                
                # Update progress
                processed_skins += 1
                if progress_callback:
                    # Progress: 10% to 85% for skin processing
                    progress = 0.1 + (processed_skins / total_skins) * 0.75
                    progress_callback(progress)
        
        # Create ZIP file
        print(f"\nCreating final ZIP file...")
        
        if progress_callback:
            progress_callback(0.9)
        
        mods_path = output_path or get_beamng_mods_path()
        os.makedirs(mods_path, exist_ok=True)
        zip_path = os.path.join(mods_path, f"{mod_name}.zip")
        
        print(f"ZIP path: {zip_path}")
        
        if os.path.exists(zip_path):
            raise FileExistsError(
                f"A mod named '{mod_name}.zip' already exists.\n"
                f"Please choose a different name or delete the existing file."
            )
        
        zip_folder(temp_dir, zip_path)
        
        if progress_callback:
            progress_callback(1.0)
        
        print(f"\n✓ Multi-skin mod created successfully!")
        print(f"  Cars: {total_cars}")
        print(f"  Skins: {total_skins}")
        print(f"  Location: {zip_path}")
        print(f"{'='*60}\n")
        
        return zip_path
        
    finally:
        # Clean up temporary directory
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

# =============================================================================
# FILE PROCESSING FUNCTIONS
# =============================================================================

def process_jbeam_files(folder_path, dds_identifier, skin_display_name, author):
    """
    Process all JBEAM files in the folder.
    Updates skin references, author, and display name.
    
    Args:
        folder_path: Path to the skin folder
        dds_identifier: The skin identifier from DDS filename (e.g., "skinname")
        skin_display_name: Display name for the skin
        author: Author name
    """
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if not file.endswith(".jbeam"):
                continue
            
            file_path = os.path.join(root_dir, file)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Update author - use \g<1> and \g<2> to avoid group reference issues
            content = re.sub(
                r'("authors"\s*:\s*")[^"]*(")',
                rf'\g<1>{author}\g<2>',
                content
            )
            
            # Update skin display name - use \g<1> and \g<2>
            content = re.sub(
                r'("name"\s*:\s*")[^"]*(")',
                rf'\g<1>{skin_display_name}\g<2>',
                content
            )
            
            # Update first skin reference (e.g., "prefix_skinname": -> "prefix_newskin":)
            # Using a function to avoid group reference issues
            def replace_first_skin_key(match):
                return f'"{match.group(1)}{dds_identifier}":'
            
            content = re.sub(
                r'"([^"]*_)[^"]+":',
                replace_first_skin_key,
                content,
                count=1
            )
            
            # Update globalSkin - use \g<1> and \g<2>
            content = re.sub(
                r'("globalSkin"\s*:\s*")[^"]*(")',
                rf'\g<1>{dds_identifier}\g<2>',
                content
            )
            
            # Update _extra.skin references using functions
            def replace_extra_skin(match):
                return f'"{match.group(1)}{dds_identifier}"'
            
            content = re.sub(
                r'"([^"]*_extra\.skin\.)[^"]+"',
                replace_extra_skin,
                content
            )
            
            def replace_extra_skin_name(match):
                return f'{match.group(1)}{dds_identifier}"'
            
            content = re.sub(
                r'("name"\s*:\s*"[^"]*_extra\.skin\.)[^"]+"',
                replace_extra_skin_name,
                content
            )
            content = re.sub(
                r'("mapTo"\s*:\s*"[^"]*_extra\.skin\.)[^"]+"',
                replace_extra_skin_name,
                content
            )
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

def process_json_files(folder_path, vehicle_id, skin_folder_name, dds_filename, dds_identifier):
    """
    Process all JSON files in the folder.
    Updates skin references and texture paths.
    
    Args:
        folder_path: Path to the skin folder
        vehicle_id: Car ID (e.g., "etk800")
        skin_folder_name: Name of the skin folder
        dds_filename: Full DDS filename (e.g., "etk800_skin_red.dds")
        dds_identifier: The skin identifier from DDS filename (e.g., "red")
    """
    for root_dir, _, files in os.walk(folder_path):
        for file in files:
            if not file.endswith(".json"):
                continue
            
            file_path = os.path.join(root_dir, file)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Update generic .skin. references using functions to avoid group reference issues
            def replace_skin_ref(match):
                return f'"{match.group(1)}{dds_identifier}"'
            
            content = re.sub(
                r'"([^"]+\.skin\.)[^"]+"',
                replace_skin_ref,
                content,
                count=1
            )
            
            def replace_skin_name(match):
                return f'{match.group(1)}{dds_identifier}"'
            
            content = re.sub(
                r'("name"\s*:\s*"[^"]+\.skin\.)[^"]+"',
                replace_skin_name,
                content,
                count=1
            )
            content = re.sub(
                r'("mapTo"\s*:\s*"[^"]+\.skin\.)[^"]+"',
                replace_skin_name,
                content,
                count=1
            )
            
            # Update _extra.skin references (all occurrences)
            def replace_extra_skin_all(match):
                return f'"{match.group(1)}{dds_identifier}"'
            
            content = re.sub(
                r'"([^"]*_extra\.skin\.)[^"]+"',
                replace_extra_skin_all,
                content
            )
            
            def replace_extra_skin_name_all(match):
                return f'{match.group(1)}{dds_identifier}"'
            
            content = re.sub(
                r'("name"\s*:\s*"[^"]*_extra\.skin\.)[^"]+"',
                replace_extra_skin_name_all,
                content
            )
            content = re.sub(
                r'("mapTo"\s*:\s*"[^"]*_extra\.skin\.)[^"]+"',
                replace_extra_skin_name_all,
                content
            )
            
            # Update baseColorMap path - construct the replacement string safely
            baseColorMap_replacement = f'"baseColorMap": "vehicles/{vehicle_id}/{skin_folder_name}/{dds_filename}"'
            content = re.sub(
                r'"baseColorMap"\s*:\s*"[^"]+\.dds"',
                baseColorMap_replacement,
                content
            )
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)