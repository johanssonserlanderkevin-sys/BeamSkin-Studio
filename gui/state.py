"""
State Manager - Centralized state management for the application
Eliminates global variables by providing a singleton state manager
"""
from typing import Dict, List, Tuple, Optional, Any
import customtkinter as ctk
from core.settings import colors, current_theme, app_settings, THEMES, added_vehicles, EDITABLE_COLOR_KEYS, COLOR_LABELS
from core.updater import CURRENT_VERSION

try:
    from core.config import VEHICLE_IDS
except ImportError:
    print("[WARNING] core/config.py not found, using empty VEHICLE_IDS")
    VEHICLE_IDS = {}


class StateManager:
    """Singleton class to manage application state"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StateManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # Theme and colors
        self.colors = colors
        self.current_theme = current_theme
        self.app_settings = app_settings
        self.themes = THEMES
        self.editable_color_keys = EDITABLE_COLOR_KEYS
        self.color_labels = COLOR_LABELS
        
        # Vehicle data
        self.vehicle_ids = VEHICLE_IDS
        self.added_vehicles = added_vehicles
        
        # Version
        self.current_version = CURRENT_VERSION
        
        # Project data (using plain values, not StringVar - those need a Tk root window)
        self.project_data: Dict[str, Any] = {
            'mod_name': "My Mod",
            'author_name': "",
            'mod_description': "",
            'mod_version': "1.0",
            'added_cars': []
        }
        
        # UI state
        self.selected_carid: Optional[str] = None
        self.selected_display_name: Optional[str] = None
        self.expanded_vehicle_carid: Optional[str] = None
        
        # Lists for UI components (to be populated by UI classes)
        self.sidebar_vehicle_buttons: List[Tuple[ctk.CTkFrame, str, str, ctk.CTkFrame]] = []
        self.carlist_items: List[Tuple[ctk.CTkFrame, str, str]] = []
        self.car_id_list: List[Tuple[str, str]] = []
        
        # Car card frames (for project tab)
        self.car_card_frames: List[ctk.CTkFrame] = []
        
        # Material settings state
        self.material_settings: Dict[str, Dict[str, Any]] = {}
        
        # Debug mode
        self.debug_mode: bool = False
        
        # Icon references (for output icons)
        self.output_icons: Dict[str, Any] = {}
        
    def get_vehicle_name(self, carid: str) -> str:
        """Get the display name for a vehicle ID"""
        return self.vehicle_ids.get(carid, carid)
    
    def is_vehicle_in_project(self, carid: str) -> bool:
        """Check if a vehicle is already in the project"""
        return any(car['id'] == carid for car in self.project_data['added_cars'])
    
    def add_vehicle_to_project(self, carid: str, display_name: str) -> None:
        """Add a vehicle to the project"""
        if not self.is_vehicle_in_project(carid):
            self.project_data['added_cars'].append({
                'id': carid,
                'name': display_name,
                'settings': {}
            })
    
    def remove_vehicle_from_project(self, carid: str) -> None:
        """Remove a vehicle from the project"""
        self.project_data['added_cars'] = [
            car for car in self.project_data['added_cars'] 
            if car['id'] != carid
        ]
    
    def get_project_vehicle_count(self) -> int:
        """Get the number of vehicles in the current project"""
        return len(self.project_data['added_cars'])
    
    def clear_project(self) -> None:
        """Clear all vehicles from the project"""
        self.project_data['added_cars'] = []
    
    def update_color(self, key: str, value: str) -> None:
        """Update a theme color"""
        self.colors[key] = value
    
    def reset_theme_colors(self) -> None:
        """Reset theme colors to defaults"""
        from core.settings import reset_theme_colors
        reset_theme_colors()


# Create singleton instance
state = StateManager()