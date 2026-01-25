"""
Generator Tab - COMPLETE IMPLEMENTATION
Fully migrated from app.py with all project management functionality
Lines migrated: 848-2188 from app_backup.py
FIXED: Project loading now updates sidebar ZIP name and author fields
FIXED: Add Skin button now works properly (line 429 was broken)
"""
from typing import Dict, List, Optional, Any, Callable
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image
import threading
import json
import os

from gui.state import state

# Import file operations
try:
    from core.file_ops import generate_multi_skin_mod
except ImportError:
    print("[WARNING] generate_multi_skin_mod not found, using fallback")
    def generate_multi_skin_mod(*args, **kwargs):
        messagebox.showerror("Error", "generate_multi_skin_mod function not available")


class GeneratorTab(ctk.CTkFrame):
    """Complete generator tab - fully functional project creation and mod generation"""
    
    def __init__(self, parent: ctk.CTk, notification_callback: Callable[[str, str, int], None] = None):
        super().__init__(parent, fg_color=state.colors["app_bg"])
        
        # Callback for notifications (passed from main window)
        self.show_notification = notification_callback or self._fallback_notification
        
        # Get references we need from state/sidebar
        self.mod_name_entry_sidebar = None  # Will be set by main window
        self.author_entry_sidebar = None    # Will be set by main window
        
        # UI Element references
        self.generator_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.project_overview_frame: Optional[ctk.CTkFrame] = None
        self.project_search_entry: Optional[ctk.CTkEntry] = None
        self.current_car_label: Optional[ctk.CTkLabel] = None
        self.dds_preview_label: Optional[ctk.CTkLabel] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.export_status_label: Optional[ctk.CTkLabel] = None
        self.skin_name_entry: Optional[ctk.CTkEntry] = None  # Store reference to skin name entry
        
        # Variables
        self.skin_name_var = ctk.StringVar()
        self.dds_path_var = ctk.StringVar()
        self.project_search_var = ctk.StringVar()
        
        # Project data structure (matches old app.py format exactly)
        self.project_data = {
            "mod_name": "",
            "author": "",
            "cars": {}  # {car_id: {"base_carid": str, "skins": [], "temp_skin_name": "", "temp_dds_path": ""}}
        }
        
        # Selected car for adding skins
        self.selected_car_for_skin: Optional[str] = None
        
        # Car ID list (for lookups)
        self.car_id_list = self._build_car_id_list()
        
        # Setup UI
        self._setup_ui()
        self._bind_search()
        self.refresh_project_display()
    
    def set_sidebar_references(self, mod_name_entry, author_entry):
        """Called by main window to provide sidebar entry references"""
        self.mod_name_entry_sidebar = mod_name_entry
        self.author_entry_sidebar = author_entry
    
    def _fallback_notification(self, message: str, type: str = "info", duration: int = 3000):
        """Fallback notification if none provided"""
        print(f"[{type.upper()}] {message}")
    
    def _build_car_id_list(self) -> List:
        """Build the car ID list from VEHICLE_IDS"""
        car_list = []
        
        # Add all vehicles from VEHICLE_IDS
        for carid, carname in state.vehicle_ids.items():
            car_list.append((carid, carname))
        
        # Add developer-added vehicles
        for carid, carname in state.added_vehicles.items():
            car_list.append((carid, carname))
        
        return sorted(car_list, key=lambda x: x[1].lower())
    
    def get_real_value(self, entry: ctk.CTkEntry, placeholder: str) -> str:
        """Get real value from entry (not placeholder)"""
        if entry is None:
            return ""
        value = entry.get()
        return "" if value == placeholder else value
    
    # ==================== UI SETUP ====================
    
    def _setup_ui(self):
        """Set up the complete generator tab UI"""
        # Main container (NOT scrollable - only the vehicles section scrolls)
        self.generator_scroll = ctk.CTkFrame(self, fg_color="transparent")
        self.generator_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        # ===== PROJECT OVERVIEW SECTION =====
        section_header = ctk.CTkFrame(self.generator_scroll, fg_color="transparent", height=60)
        section_header.pack(fill="x", padx=20, pady=(15, 10))
        section_header.pack_propagate(False)
        
        ctk.CTkLabel(
            section_header,
            text="Project Overview",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=state.colors["text"]
        ).pack(side="left", anchor="w")
        
        # Project controls
        project_controls = ctk.CTkFrame(section_header, fg_color="transparent")
        project_controls.pack(side="right")
        
        self._create_button(project_controls, "💾 Save Project", self.save_project, "primary", 130, 32).pack(side="left", padx=3)
        self._create_button(project_controls, "📁 Load Project", self.load_project, "primary", 130, 32).pack(side="left", padx=3)
        self._create_button(project_controls, "Clear", self.clear_project, "danger", 100, 32).pack(side="left", padx=3)
        
        # Vehicles in project label
        ctk.CTkLabel(
            self.generator_scroll,
            text="Vehicles in project",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=state.colors["text"]
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Project search
        project_search_frame = ctk.CTkFrame(self.generator_scroll, fg_color="transparent")
        project_search_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        self.project_search_entry = ctk.CTkEntry(
            project_search_frame,
            textvariable=self.project_search_var,
            height=32,
            corner_radius=8,
            fg_color=state.colors["card_bg"],
            border_color=state.colors["border"],
            text_color="#888888"
        )
        self.project_search_entry.pack(fill="x")
        self._setup_placeholder(self.project_search_entry, "🔍 Search cars...")
        
        # Project overview container (scrollable, fixed height for 2 rows of cars)
        # Each car card is roughly 80-100px tall, so 2 rows = ~200px
        project_overview_container = ctk.CTkScrollableFrame(
            self.generator_scroll,
            height=200,
            corner_radius=12,
            fg_color=state.colors["frame_bg"]
        )
        project_overview_container.pack(fill="x", padx=10, pady=(0, 10))
        
        self.project_overview_frame = ctk.CTkFrame(project_overview_container, fg_color="transparent")
        self.project_overview_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Current car label (shows which car is selected for adding skins)
        self.current_car_label = ctk.CTkLabel(
            self.generator_scroll,
            text="",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=state.colors["accent"]
        )
        
        # ===== ADD SKINS SECTION =====
        ctk.CTkLabel(
            self.generator_scroll,
            text="Add Skins to Selected Car",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=state.colors["text"]
        ).pack(anchor="w", padx=20, pady=(20, 10))
        
        # Skin card
        skin_card = self._create_card(self.generator_scroll)
        skin_card.pack(fill="x", padx=20, pady=(0, 15))
        
        # Skin name
        ctk.CTkLabel(
            skin_card,
            text="Skin Name",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=state.colors["text"]
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.skin_name_entry = ctk.CTkEntry(
            skin_card,
            textvariable=self.skin_name_var,
            height=36,
            fg_color=state.colors["frame_bg"],
            border_color=state.colors["border"],
            text_color=state.colors["text"]
        )
        self.skin_name_entry.pack(fill="x", padx=15, pady=(0, 10))
        self._setup_placeholder(self.skin_name_entry, "Enter skin name...")
        
        # DDS file
        ctk.CTkLabel(
            skin_card,
            text="DDS Texture",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=state.colors["text"]
        ).pack(anchor="w", padx=15, pady=(5, 5))
        
        dds_frame = ctk.CTkFrame(skin_card, fg_color="transparent")
        dds_frame.pack(fill="x", padx=15, pady=(0, 10))
        
        dds_entry = ctk.CTkEntry(
            dds_frame,
            textvariable=self.dds_path_var,
            state="readonly",
            height=36,
            fg_color=state.colors["frame_bg"],
            border_color=state.colors["border"],
            text_color=state.colors["text"]
        )
        dds_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self._setup_placeholder(dds_entry, "No file selected...")
        
        dds_browse = ctk.CTkButton(
            dds_frame,
            text="📁 Browse",
            command=self.browse_dds,
            width=100,
            height=36,
            fg_color=state.colors["card_bg"],
            hover_color=state.colors["card_hover"],
            text_color=state.colors["text"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8
        )
        dds_browse.pack(side="right")
        
        # DDS preview
        self.dds_preview_label = ctk.CTkLabel(
            skin_card,
            text="",
            image=None,
            width=600,
            height=300
        )
        self.dds_preview_label.pack(padx=15, pady=(0, 10))
        
        # Add skin button
        add_skin_btn = ctk.CTkButton(
            skin_card,
            text="➕ Add Skin",
            command=self.add_skin_to_selected_car,
            height=40,
            fg_color=state.colors["accent"],
            hover_color=state.colors["accent_hover"],
            text_color=state.colors["accent_text"],
            font=ctk.CTkFont(size=13, weight="bold"),
            corner_radius=8
        )
        add_skin_btn.pack(fill="x", padx=15, pady=(5, 15))
        
        # Export status label
        self.export_status_label = ctk.CTkLabel(
            self.generator_scroll,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=state.colors["text_secondary"]
        )
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            self.generator_scroll,
            height=8,
            corner_radius=4,
            fg_color=state.colors["frame_bg"],
            progress_color=state.colors["accent"]
        )
    
    def _create_card(self, parent) -> ctk.CTkFrame:
        """Create a card container"""
        return ctk.CTkFrame(
            parent,
            fg_color=state.colors["card_bg"],
            corner_radius=12,
            border_width=1,
            border_color=state.colors["border"]
        )
    
    def _create_button(self, parent, text: str, command, style: str = "primary", width: int = 120, height: int = 36) -> ctk.CTkButton:
        """Create a styled button"""
        if style == "primary":
            fg_color = state.colors["accent"]
            hover_color = state.colors["accent_hover"]
            text_color = state.colors["accent_text"]
        elif style == "danger":
            fg_color = state.colors["error"]
            hover_color = state.colors["error_hover"]
            text_color = "white"
        else:
            fg_color = state.colors["card_bg"]
            hover_color = state.colors["card_hover"]
            text_color = state.colors["text"]
        
        return ctk.CTkButton(
            parent,
            text=text,
            command=command,
            width=width,
            height=height,
            fg_color=fg_color,
            hover_color=hover_color,
            text_color=text_color,
            corner_radius=8,
            font=ctk.CTkFont(size=12, weight="bold")
        )
    
    def _setup_placeholder(self, entry: ctk.CTkEntry, placeholder: str):
        """Setup placeholder text for an entry"""
        entry._placeholder = placeholder
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(text_color="#888888")
        
        def on_focus_in(event):
            if entry.get() == placeholder:
                entry.delete(0, "end")
                entry.configure(text_color=state.colors["text"])
        
        def on_focus_out(event):
            if not entry.get():
                entry.insert(0, placeholder)
                entry.configure(text_color="#888888")
        
        entry.bind("<FocusIn>", on_focus_in)
        entry.bind("<FocusOut>", on_focus_out)
    
    def _bind_search(self):
        """Bind search functionality"""
        self.project_search_var.trace_add("write", lambda *args: self.refresh_project_display())
    
    # ==================== PROJECT MANAGEMENT ====================
    
    def add_car_to_project(self, carid: str, display_name: str):
        """Add a car to the project
        
        Args:
            carid: Vehicle ID (e.g., "etk800")
            display_name: Display name (e.g., "ETK 800 Series")
        """
        print(f"[DEBUG] Adding car to project: {display_name} ({carid})")
        
        # Check if this car is already in the project (prevent duplicates)
        if carid in self.project_data["cars"]:
            self.show_notification(f"{display_name} is already in the project", "warning")
            # Select the existing car instead
            self.selected_car_for_skin = carid
            self.refresh_project_display()
            return
        
        # Check if any instance of this car exists
        for car_id in self.project_data["cars"].keys():
            if car_id.startswith(f"{carid}_"):
                self.show_notification(f"{display_name} is already in the project", "warning")
                # Select the first instance
                self.selected_car_for_skin = carid if carid in self.project_data["cars"] else car_id
                self.refresh_project_display()
                return
        
        # First instance of this car - add it
        self.project_data["cars"][carid] = {
            "base_carid": carid,
            "skins": [],
            "temp_skin_name": "",
            "temp_dds_path": ""
        }
        
        # Select this car
        self.selected_car_for_skin = carid
        self.show_notification(f"Added {display_name} to project", "success")
        
        print(f"[DEBUG] Selected car for skins: {self.selected_car_for_skin}")
        
        # Refresh display
        self.refresh_project_display()
    
    def remove_car_from_project(self, car_instance_id: str):
        """Remove a car instance from the project"""
        if car_instance_id in self.project_data["cars"]:
            base_carid = self.project_data["cars"][car_instance_id].get("base_carid", car_instance_id)
            del self.project_data["cars"][car_instance_id]
            
            # If this was the selected car, clear selection
            if self.selected_car_for_skin == car_instance_id:
                self.selected_car_for_skin = None
            
            car_name = state.vehicle_ids.get(base_carid, base_carid)
            self.show_notification(f"Removed {car_name}", "info")
            
            # Refresh display
            self.refresh_project_display()
    
    def select_car_for_skin(self, car_instance_id: str):
        """Select a car to add skins to"""
        if car_instance_id in self.project_data["cars"]:
            self.selected_car_for_skin = car_instance_id
            print(f"[DEBUG] Selected car for adding skins: {car_instance_id}")
            self.refresh_project_display()
    
    def add_skin_to_selected_car(self):
        """Add a skin to the currently selected car"""
        # Check if car is selected
        if not self.selected_car_for_skin:
            self.show_notification("Please select a car first", "warning")
            return
        
        # Get skin name - FIXED: Simply use the StringVar instead of complex widget traversal
        skin_name = self.skin_name_var.get().strip()
        
        # Get DDS path
        dds_path = self.dds_path_var.get().strip()
        
        # Validation
        if not skin_name or skin_name == "Enter skin name...":
            self.show_notification("Please enter a skin name", "warning")
            return
        
        if not dds_path or dds_path == "No file selected...":
            self.show_notification("Please select a DDS file", "warning")
            return
        
        if not os.path.exists(dds_path):
            self.show_notification("DDS file does not exist", "error")
            return
        
        # Add skin to selected car
        skin_data = {
            "name": skin_name,
            "dds_path": dds_path
        }
        
        self.project_data["cars"][self.selected_car_for_skin]["skins"].append(skin_data)
        
        # Clear inputs and preview
        self.skin_name_var.set("")
        self.dds_path_var.set("")
        
        # IMPORTANT: Clear the preview image completely
        self.dds_preview_label.configure(image=None, text="")
        # Remove the stored image reference to free memory
        if hasattr(self.dds_preview_label, 'image'):
            delattr(self.dds_preview_label, 'image')
        
        # Reset placeholder for skin name entry
        if self.skin_name_entry:
            self.skin_name_entry.delete(0, "end")
            self.skin_name_entry.insert(0, "Enter skin name...")
            self.skin_name_entry.configure(text_color="#888888")
        
        self.show_notification(f"Added skin '{skin_name}'", "success")
        self.refresh_project_display()
    
    def remove_skin_from_car(self, car_instance_id: str, skin_index: int):
        """Remove a skin from a car"""
        if car_instance_id in self.project_data["cars"]:
            skins = self.project_data["cars"][car_instance_id]["skins"]
            if 0 <= skin_index < len(skins):
                skin_name = skins[skin_index]["name"]
                del skins[skin_index]
                self.show_notification(f"Removed skin '{skin_name}'", "info")
                self.refresh_project_display()
    
    def browse_dds(self):
        """Browse for DDS file"""
        filename = filedialog.askopenfilename(
            title="Select DDS Texture",
            filetypes=[("DDS files", "*.dds"), ("All files", "*.*")]
        )
        
        if filename:
            self.dds_path_var.set(filename)
            
            # Try to load preview
            try:
                img = Image.open(filename)
                img.thumbnail((400, 400), Image.Resampling.LANCZOS)
                photo = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
                self.dds_preview_label.configure(image=photo, text="")
                self.dds_preview_label.image = photo
            except Exception as e:
                print(f"[DEBUG] Could not load DDS preview: {e}")
                self.dds_preview_label.configure(image=None, text="Preview unavailable")
    
    def save_project(self):
        """Save current project to file"""
        if not self.project_data["cars"]:
            self.show_notification("No cars in project to save", "warning")
            return
        
        # Get mod name from sidebar
        mod_name = ""
        if self.mod_name_entry_sidebar:
            mod_name = self.get_real_value(self.mod_name_entry_sidebar, "Enter mod name...").strip()
        
        # Get author from sidebar
        author = ""
        if self.author_entry_sidebar:
            author = self.get_real_value(self.author_entry_sidebar, "Your name...").strip()
        
        # Update project data
        self.project_data["mod_name"] = mod_name
        self.project_data["author"] = author if author else "Unknown"
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Project",
            defaultextension=".bsproject",
            filetypes=[("BeamSkin Project", "*.bsproject"), ("All files", "*.*")],
            initialfile=f"{mod_name}.bsproject" if mod_name else "project.bsproject"
        )
        
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(self.project_data, f, indent=2)
                print(f"[DEBUG] Project saved to: {filename}")
                self.show_notification("Project saved successfully", "success")
            except Exception as e:
                print(f"[DEBUG] Error saving project: {e}")
                self.show_notification(f"Error saving project: {str(e)}", "error")
    
    def load_project(self):
        """Load project from file"""
        filename = filedialog.askopenfilename(
            title="Load Project",
            filetypes=[("BeamSkin Project", "*.bsproject"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r') as f:
                    loaded_data = json.load(f)
                
                # Validate structure
                if "cars" not in loaded_data:
                    self.show_notification("Invalid project file", "error")
                    return
                
                # Clear current project
                self.project_data = loaded_data
                self.selected_car_for_skin = None
                
                # Update sidebar fields
                if "mod_name" in loaded_data and self.mod_name_entry_sidebar:
                    self.mod_name_entry_sidebar.delete(0, "end")
                    self.mod_name_entry_sidebar.insert(0, loaded_data["mod_name"])
                    self.mod_name_entry_sidebar.configure(text_color=state.colors["text"])
                
                if "author" in loaded_data and self.author_entry_sidebar:
                    self.author_entry_sidebar.delete(0, "end")
                    self.author_entry_sidebar.insert(0, loaded_data["author"])
                    self.author_entry_sidebar.configure(text_color=state.colors["text"])
                
                print(f"[DEBUG] Project loaded from: {filename}")
                self.show_notification(f"Loaded project with {len(loaded_data['cars'])} cars", "success")
                
                # Refresh display
                self.refresh_project_display()
                
            except Exception as e:
                print(f"[DEBUG] Error loading project: {e}")
                self.show_notification(f"Error loading project: {str(e)}", "error")
    
    def clear_project(self):
        """Clear the current project"""
        if not self.project_data["cars"]:
            self.show_notification("Project is already empty", "info")
            return
        
        # Import custom dialog
        from gui.components.dialogs import show_confirmation_dialog
        
        # Show custom confirmation dialog
        confirmed = show_confirmation_dialog(
            self.winfo_toplevel(),
            "Clear Project",
            "Are you sure you want to clear the project?\nAll unsaved changes will be lost."
        )
        
        if confirmed:
            self.project_data["cars"] = {}
            self.selected_car_for_skin = None
            self.show_notification("Project cleared", "info")
            self.refresh_project_display()
    
    # ==================== UI REFRESH ====================
    
    def refresh_project_display(self):
        """Refresh the project overview display with 2-column grid layout"""
        print(f"[DEBUG] ========== REFRESH PROJECT DISPLAY ==========")
        print(f"[DEBUG] Cars in project: {len(self.project_data['cars'])}")
        
        # Clear existing widgets
        for widget in self.project_overview_frame.winfo_children():
            widget.destroy()
        
        if not self.project_data["cars"]:
            # Show empty state
            empty_label = ctk.CTkLabel(
                self.project_overview_frame,
                text="No cars in project. Add cars from the sidebar →",
                font=ctk.CTkFont(size=13),
                text_color=state.colors["text_secondary"]
            )
            empty_label.pack(pady=40)
            self.update_current_car_label()
            print(f"[DEBUG] ========== REFRESH COMPLETE (EMPTY) ==========\n")
            return
        
        # Get search query
        search_query = self.project_search_var.get().lower().strip()
        if search_query == "🔍 search cars...":
            search_query = ""
        
        # Filter cars
        filtered_cars = {}
        for car_instance_id, car_info in self.project_data["cars"].items():
            base_carid = car_info.get("base_carid", car_instance_id)
            
            # Get car name
            car_name = state.vehicle_ids.get(base_carid, base_carid)
            for cid, cname in self.car_id_list:
                if cid == base_carid:
                    car_name = cname
                    break
            
            # Check if matches search
            if not search_query or search_query in car_name.lower() or search_query in base_carid.lower():
                filtered_cars[car_instance_id] = car_info
        
        print(f"[DEBUG] Filtered cars: {len(filtered_cars)} (search: '{search_query}')")
        
        if not filtered_cars:
            # Show no results
            no_results_label = ctk.CTkLabel(
                self.project_overview_frame,
                text=f"No cars match '{search_query}'",
                font=ctk.CTkFont(size=13),
                text_color=state.colors["text_secondary"]
            )
            no_results_label.pack(pady=40)
            self.update_current_car_label()
            print(f"[DEBUG] ========== REFRESH COMPLETE (NO RESULTS) ==========\n")
            return
        
        # Create car cards in a 2-column grid
        current_row = None
        for idx, (car_instance_id, car_info) in enumerate(filtered_cars.items()):
            base_carid = car_info.get("base_carid", car_instance_id)
            
            # Get car name
            car_name = state.vehicle_ids.get(base_carid, base_carid)
            for cid, cname in self.car_id_list:
                if cid == base_carid:
                    car_name = cname
                    break
            
            print(f"[DEBUG]   - {car_instance_id}: {car_name} ({len(car_info['skins'])} skins)")
            
            # Create new row every 2 cards
            if idx % 2 == 0:
                current_row = ctk.CTkFrame(self.project_overview_frame, fg_color="transparent")
                current_row.pack(fill="x", pady=4, padx=4)
            
            # Determine if this is selected
            is_selected = (car_instance_id == self.selected_car_for_skin)
            
            # Car card
            car_card = ctk.CTkFrame(
                current_row,
                fg_color=state.colors["accent"] if is_selected else state.colors["card_bg"],
                corner_radius=10,
                border_width=2,
                border_color=state.colors["accent"] if is_selected else state.colors["border"]
            )
            car_card.pack(side="left", fill="both", expand=True, padx=4)
            
            # Make card clickable to select for adding skins
            def select_handler(cid=car_instance_id):
                self.select_car_for_skin(cid)
            
            car_card.bind("<Button-1>", lambda e, cid=car_instance_id: select_handler(cid))
            
            # Header row
            header_row = ctk.CTkFrame(car_card, fg_color="transparent")
            header_row.pack(fill="x", padx=10, pady=(10, 5))
            
            # Car name
            display_text = f"{car_name}"
            if "_" in car_instance_id and car_instance_id != base_carid:
                instance_num = car_instance_id.split("_")[-1]
                display_text = f"{car_name} (Instance #{instance_num})"
            
            car_label = ctk.CTkLabel(
                header_row,
                text=display_text,
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=state.colors["accent_text"] if is_selected else state.colors["text"],
                anchor="w"
            )
            car_label.pack(side="left", fill="x", expand=True)
            car_label.bind("<Button-1>", lambda e, cid=car_instance_id: select_handler(cid))
            
            # Remove button
            remove_btn = ctk.CTkButton(
                header_row,
                text="✕",
                width=28,
                height=28,
                fg_color=state.colors["error"],
                hover_color=state.colors["error_hover"],
                text_color="white",
                font=ctk.CTkFont(size=13, weight="bold"),
                corner_radius=6,
                command=lambda c=car_instance_id: self.remove_car_from_project(c)
            )
            remove_btn.pack(side="right")
            
            # Skin count
            skin_count_label = ctk.CTkLabel(
                car_card,
                text=f"🎨 {len(car_info['skins'])} skins",
                font=ctk.CTkFont(size=12),
                text_color=state.colors["accent_text"] if is_selected else state.colors["text_secondary"],
                anchor="w"
            )
            skin_count_label.pack(anchor="w", padx=10, pady=(0, 5))
            skin_count_label.bind("<Button-1>", lambda e, cid=car_instance_id: select_handler(cid))
            
            # Show skins if any
            if car_info["skins"]:
                # Skins container with subtle background
                skins_container = ctk.CTkFrame(
                    car_card,
                    fg_color=state.colors["app_bg"],
                    corner_radius=8
                )
                skins_container.pack(fill="x", padx=8, pady=(5, 10))
                skins_container.bind("<Button-1>", lambda e, cid=car_instance_id: select_handler(cid))
                
                # Skins header
                skins_header = ctk.CTkLabel(
                    skins_container,
                    text="Skins:",
                    font=ctk.CTkFont(size=11, weight="bold"),
                    text_color=state.colors["text_secondary"],
                    anchor="w"
                )
                skins_header.pack(anchor="w", padx=8, pady=(6, 4))
                
                for skin_idx, skin in enumerate(car_info["skins"]):
                    # All rows use app_bg for consistency
                    row_color = state.colors["app_bg"]
                    
                    skin_row = ctk.CTkFrame(
                        skins_container,
                        fg_color=row_color,
                        corner_radius=6,
                        height=36
                    )
                    skin_row.pack(fill="x", padx=4, pady=2)
                    skin_row.pack_propagate(False)  # Maintain height
                    
                    # Icon
                    icon_label = ctk.CTkLabel(
                        skin_row,
                        text="🎨",
                        font=ctk.CTkFont(size=14)
                    )
                    icon_label.pack(side="left", padx=(8, 6))
                    
                    # Skin name with number
                    skin_label = ctk.CTkLabel(
                        skin_row,
                        text=f"{skin_idx + 1}. {skin['name']}",
                        text_color=state.colors["text"],
                        anchor="w",
                        font=ctk.CTkFont(size=13, weight="bold")
                    )
                    skin_label.pack(side="left", fill="x", expand=True, padx=(0, 8))
                    
                    # Remove button
                    remove_skin_btn = ctk.CTkButton(
                        skin_row,
                        text="✕",
                        width=28,
                        height=28,
                        fg_color=state.colors["error"],
                        hover_color=state.colors["error_hover"],
                        text_color="white",
                        font=ctk.CTkFont(size=13, weight="bold"),
                        corner_radius=6,
                        command=lambda c=car_instance_id, i=skin_idx: self.remove_skin_from_car(c, i)
                    )
                    remove_skin_btn.pack(side="right", padx=6)
        
        self.update_current_car_label()
        print(f"[DEBUG] ========== REFRESH COMPLETE (SUCCESS - {len(filtered_cars)} cars displayed) ==========\n")
    
    def update_current_car_label(self):
        """Update the label showing which car is selected"""
        if self.selected_car_for_skin and self.selected_car_for_skin in self.project_data["cars"]:
            base_carid = self.project_data["cars"][self.selected_car_for_skin].get("base_carid", self.selected_car_for_skin)
            
            car_name = state.vehicle_ids.get(base_carid, base_carid)
            for cid, cname in self.car_id_list:
                if cid == base_carid:
                    car_name = cname
                    break
            
            display_text = f"{car_name} ({base_carid})"
            if "_" in self.selected_car_for_skin and self.selected_car_for_skin != base_carid:
                instance_num = self.selected_car_for_skin.split("_")[-1]
                display_text = f"{car_name} - Instance #{instance_num} ({base_carid})"
            
            self.current_car_label.configure(text=f"Adding Skins to: {display_text}")
            self.current_car_label.pack(anchor="w", padx=10, pady=(10, 0))
        else:
            self.current_car_label.pack_forget()
    
    def generate_mod(self, generate_button_topbar, output_mode_var, custom_output_var):
        """Generate the mod with all cars and skins
        
        This should be called by the topbar generate button.
        Pass in the button reference and output mode variables.
        """
        print("[DEBUG] \n" + "="*50)
        print("[DEBUG] MULTI-SKIN MOD GENERATION INITIATED")
        print("[DEBUG] ="*50)
        
        # Get mod name and author from sidebar entries
        mod_name = ""
        author_name = ""
        if self.mod_name_entry_sidebar:
            mod_name = self.get_real_value(self.mod_name_entry_sidebar, "Enter mod name...").strip()
        if self.author_entry_sidebar:
            author_name = self.get_real_value(self.author_entry_sidebar, "Your name...").strip()
        
        # Validation
        if not mod_name:
            self.show_notification("Please enter a ZIP name", "error")
            return
        
        if not self.project_data["cars"]:
            self.show_notification("Please add at least one car to the project", "error")
            return
        
        # Check all cars have skins
        cars_without_skins = []
        for carid, car_info in self.project_data["cars"].items():
            if not car_info["skins"]:
                cars_without_skins.append(carid)
        
        if cars_without_skins:
            self.show_notification(f"Please add skins to: {', '.join(cars_without_skins)}", "error", 4000)
            return
        
        # Get output path if custom
        output_path = custom_output_var.get() if output_mode_var.get() == "custom" else None
        
        # Update project data
        self.project_data["mod_name"] = mod_name
        self.project_data["author"] = author_name if author_name else "Unknown"
        
        print(f"[DEBUG] Mod Name: {mod_name}")
        print(f"[DEBUG] Author: {self.project_data['author']}")
        print(f"[DEBUG] Cars: {len(self.project_data['cars'])}")
        total_skins = sum(len(car_info['skins']) for car_info in self.project_data['cars'].values())
        print(f"[DEBUG] Total Skins: {total_skins}")
        
        # Show progress UI
        self.export_status_label.configure(text="Preparing to export...")
        self.export_status_label.pack(padx=20, pady=(10, 5))
        self.progress_bar.pack(fill="x", padx=20, pady=(0, 5))
        self.progress_bar.set(0)
        generate_button_topbar.configure(state="disabled")
        
        def update_status(message):
            """Update the status label text"""
            self.export_status_label.configure(text=message)
        
        def update_progress(value):
            """Update progress bar"""
            if self.progress_bar.winfo_ismapped():
                self.progress_bar.set(value)
        
        def thread_fn():
            try:
                print("[DEBUG] \nStarting mod generation thread...")
                update_status("Processing skins...")
                
                def progress_with_status(value):
                    update_progress(value)
                    if value < 0.3:
                        update_status("Copying template files...")
                    elif value < 0.7:
                        update_status(f"Processing {total_skins} skins...")
                    else:
                        update_status("Creating ZIP archive...")
                
                # Call the file_ops function
                if generate_multi_skin_mod:
                    generate_multi_skin_mod(
                        self.project_data,
                        output_path=output_path,
                        progress_callback=progress_with_status
                    )
                    
                    update_status("Export completed successfully!")
                    print("[DEBUG] Mod generation completed successfully!")
                    print("[DEBUG] ="*50 + "\n")
                    self.show_notification(f"✓ Mod '{mod_name}' created with {total_skins} skins!", "success", 5000)
                    
                    # Show info about keeping project
                    self.after(2000, lambda: self.show_notification("Project kept. Click 'Clear Project' to start new one.", "info", 4000))
                else:
                    update_status("Error: Generation function not available")
                    self.show_notification("Error: generate_multi_skin_mod function not found", "error", 5000)
                
            except FileExistsError as e:
                update_status("Error: File already exists")
                print(f"[DEBUG] ERROR: File already exists - {e}")
                self.show_notification(f"File already exists: {str(e)}", "error", 5000)
            except Exception as e:
                update_status("Error: Export failed")
                print(f"[DEBUG] ERROR: {e}")
                import traceback
                traceback.print_exc()
                self.show_notification(f"Error: {str(e)}", "error", 5000)
            finally:
                self.progress_bar.set(0)
                generate_button_topbar.configure(state="normal")
                self.after(2000, lambda: self.progress_bar.pack_forget())
                self.after(2000, lambda: self.export_status_label.pack_forget())
        
        # Start generation in background thread
        threading.Thread(target=thread_fn, daemon=True).start()