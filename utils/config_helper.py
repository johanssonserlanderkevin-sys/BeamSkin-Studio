# config_helper.py
# Helper functions for managing car config types

import os

def load_config_types(config_file=None):

    print(f"[DEBUG] load_config_types called")
    """
    Load config types from carconfigs.txt file in vehicles folder.
    Returns a list of config types.
    
    Args:
        config_file: Optional custom path to the config types file
    
    Returns:
        List of config type strings
    """
    config_types = ["Factory", "Custom", "Police"]  # Default values
    
    # Default location: vehicles/carconfigs.txt
    if config_file is None:
        config_file = os.path.join("vehicles", "carconfigs.txt")
    
    try:
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                loaded_types = [line.strip() for line in f if line.strip()]
                if loaded_types:
                    config_types = loaded_types
                    print(f"[DEBUG] Loaded {len(config_types)} config types from {config_file}")
                else:
                    print(f"[DEBUG] Config file empty, using defaults")
        else:
            print(f"[DEBUG] Config file not found at {config_file}, using default config types")
            os.makedirs("vehicles", exist_ok=True)
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write("Factory\nCustom\nPolice\n")
            print(f"[DEBUG] Created default {config_file}")
    except Exception as e:
        print(f"[DEBUG] Error loading config types: {e}, using defaults")
    
    return config_types


def get_beamng_vehicles_path():


    print(f"[DEBUG] get_beamng_vehicles_path called")
    """
    Get the path to BeamNG.drive vehicles folder.
    Returns: C:\\Users\\{username}\\AppData\\Local\\BeamNG\\BeamNG.drive\\current\\vehicles
    """
    import getpass
    username = getpass.getuser()
    return os.path.join(
        "C:\\Users",
        username,
        "AppData",
        "Local",
        "BeamNG",
        "BeamNG.drive",
        "current",
        "vehicles"
    )
