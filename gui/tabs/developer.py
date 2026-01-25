"""
Developer Tab - COMPLETE IMPLEMENTATION
Add and manage custom vehicles
Migrated from app_backup.py lines 3670-4010
"""
import customtkinter as ctk
from tkinter import filedialog, messagebox
from typing import Callable, Optional
import os

from gui.state import state


class DeveloperTab(ctk.CTkFrame):
    """Complete developer tab for custom vehicle management"""
    
    def __init__(self, parent: ctk.CTk, notification_callback: Callable[[str, str, int], None] = None):
        super().__init__(parent, fg_color=state.colors["app_bg"])
        
        # Callback for notifications
        self.show_notification = notification_callback or self._fallback_notification
        
        # Variables for adding vehicles
        self.carid_var = ctk.StringVar()
        self.carname_var = ctk.StringVar()
        self.json_path_var = ctk.StringVar()
        self.jbeam_path_var = ctk.StringVar()
        self.image_path_var = ctk.StringVar()
        
        # UI references
        self.dev_status_label: Optional[ctk.CTkLabel] = None
        self.dev_progress_bar: Optional[ctk.CTkProgressBar] = None
        self.dev_list_scroll: Optional[ctk.CTkScrollableFrame] = None
        self.dev_search_var = ctk.StringVar()
        
        self._setup_ui()
        self.refresh_developer_list()
    
    def _fallback_notification(self, message: str, type: str = "info", duration: int = 3000):
        """Fallback notification"""
        print(f"[{type.upper()}] {message}")
    
    def _setup_ui(self):
        """Set up the developer tab UI"""
        # Title
        ctk.CTkLabel(
            self,
            text="Add New Vehicle",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=state.colors["text"]
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Input frame
        input_frame = ctk.CTkFrame(self, fg_color=state.colors["frame_bg"], corner_radius=12)
        input_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Car ID input
        ctk.CTkLabel(input_frame, text="Car ID:", text_color=state.colors["text"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        carid_entry = ctk.CTkEntry(input_frame, textvariable=self.carid_var, fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        carid_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Car Name input
        ctk.CTkLabel(input_frame, text="Car Name:", text_color=state.colors["text"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        carname_entry = ctk.CTkEntry(input_frame, textvariable=self.carname_var, fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        carname_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        
        # JSON File input
        ctk.CTkLabel(input_frame, text="JSON File:", text_color=state.colors["text"]).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        json_entry = ctk.CTkEntry(input_frame, textvariable=self.json_path_var, state="readonly", fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        json_entry.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        json_browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=self.select_json_file,
                                        fg_color=state.colors["card_bg"], hover_color=state.colors["card_hover"], text_color=state.colors["text"])
        json_browse_btn.grid(row=2, column=2, padx=5, pady=5)
        
        # JBEAM File input
        ctk.CTkLabel(input_frame, text="JBEAM File:", text_color=state.colors["text"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        jbeam_entry = ctk.CTkEntry(input_frame, textvariable=self.jbeam_path_var, state="readonly", fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        jbeam_entry.grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        jbeam_browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=self.select_jbeam_file,
                                         fg_color=state.colors["card_bg"], hover_color=state.colors["card_hover"], text_color=state.colors["text"])
        jbeam_browse_btn.grid(row=3, column=2, padx=5, pady=5)
        
        # Preview Image input (optional)
        ctk.CTkLabel(input_frame, text="Preview Image (Optional):", text_color=state.colors["text"]).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        image_entry = ctk.CTkEntry(input_frame, textvariable=self.image_path_var, state="readonly", fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        image_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")
        image_browse_btn = ctk.CTkButton(input_frame, text="Browse", width=80, command=self.select_image_file,
                                         fg_color=state.colors["card_bg"], hover_color=state.colors["card_hover"], text_color=state.colors["text"])
        image_browse_btn.grid(row=4, column=2, padx=5, pady=5)
        
        input_frame.columnconfigure(1, weight=1)
        
        # Status and progress
        self.dev_status_label = ctk.CTkLabel(self, text="", text_color=state.colors["text"], font=ctk.CTkFont(size=12))
        self.dev_status_label.pack(padx=10, pady=(10, 5))
        self.dev_status_label.pack_forget()
        
        self.dev_progress_bar = ctk.CTkProgressBar(self)
        self.dev_progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.dev_progress_bar.pack_forget()
        
        # Add Vehicle button
        add_btn = ctk.CTkButton(
            self,
            text="➕ Add Vehicle",
            command=self.add_vehicle,
            fg_color=state.colors["accent"],
            hover_color=state.colors["accent_hover"],
            text_color=state.colors["accent_text"],
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40
        )
        add_btn.pack(fill="x", padx=10, pady=(5, 15))
        
        # Added Vehicles section
        ctk.CTkLabel(
            self,
            text="Added Vehicles",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=state.colors["text"]
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        # Search
        dev_search_entry = ctk.CTkEntry(
            self,
            textvariable=self.dev_search_var,
            placeholder_text="🔍 Search added vehicles...",
            placeholder_text_color="#888888",
            fg_color=state.colors["card_bg"],
            text_color=state.colors["text"],
            height=35
        )
        dev_search_entry.pack(fill="x", padx=10, pady=(0, 10))
        dev_search_entry.bind("<KeyRelease>", lambda e: self.refresh_developer_list())
        
        # List of added vehicles
        self.dev_list_scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=state.colors["frame_bg"],
            corner_radius=12
        )
        self.dev_list_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def select_json_file(self):
        """Select JSON file"""
        path = filedialog.askopenfilename(title="Select JSON File", filetypes=[("JSON Files", "*.json")])
        if path:
            self.json_path_var.set(path)
            print(f"[DEBUG] JSON file selected: {path}")
    
    def select_jbeam_file(self):
        """Select JBEAM file"""
        path = filedialog.askopenfilename(title="Select JBEAM File", filetypes=[("JBEAM Files", "*.jbeam")])
        if path:
            self.jbeam_path_var.set(path)
            print(f"[DEBUG] JBEAM file selected: {path}")
    
    def select_image_file(self):
        """Select preview image"""
        path = filedialog.askopenfilename(
            title="Select Preview Image (JPG only)",
            filetypes=[("JPEG Images", "*.jpg"), ("JPEG Images", "*.jpeg")]
        )
        if path:
            if path.lower().endswith(('.jpg', '.jpeg')):
                self.image_path_var.set(path)
                print(f"[DEBUG] Preview image selected: {path}")
            else:
                self.show_notification("Please select a JPG/JPEG image file", "error")
    
    def add_vehicle(self):
        """Add a custom vehicle to the system"""
        carid = self.carid_var.get().strip()
        carname = self.carname_var.get().strip()
        json_path = self.json_path_var.get().strip()
        jbeam_path = self.jbeam_path_var.get().strip()
        image_path = self.image_path_var.get().strip()
        
        # Validation
        if not carid:
            self.show_notification("Please enter a Car ID", "error")
            return
        if not carname:
            self.show_notification("Please enter a Car Name", "error")
            return
        if not json_path:
            self.show_notification("Please select a JSON file", "error")
            return
        if not jbeam_path:
            self.show_notification("Please select a JBEAM file", "error")
            return
        
        # Check if already exists
        if carid in state.added_vehicles:
            self.show_notification(f"Vehicle '{carid}' already exists", "error")
            return
        
        print(f"[DEBUG] Adding custom vehicle: {carid} - {carname}")
        
        # Show progress
        self.dev_status_label.configure(text="Processing files...")
        self.dev_status_label.pack(padx=10, pady=(10, 5))
        self.dev_progress_bar.pack(fill="x", padx=10, pady=(0, 5))
        self.dev_progress_bar.set(0.3)
        
        try:
            # Import the developer functions
            from core.developer import process_vehicle_files
            
            # Process the files
            success = process_vehicle_files(
                carid=carid,
                carname=carname,
                json_path=json_path,
                jbeam_path=jbeam_path,
                image_path=image_path if image_path else None
            )
            
            if success:
                # Add to state
                state.added_vehicles[carid] = carname
                
                # Save to settings
                from core.settings import save_settings
                save_settings()
                
                # Success
                self.dev_status_label.configure(text="Vehicle added successfully!")
                self.dev_progress_bar.set(1.0)
                
                # Clear inputs
                self.carid_var.set("")
                self.carname_var.set("")
                self.json_path_var.set("")
                self.jbeam_path_var.set("")
                self.image_path_var.set("")
                
                self.show_notification(f"✓ Added vehicle '{carname}'", "success", 3000)
                self.refresh_developer_list()
            else:
                self.dev_status_label.configure(text="Error: Processing failed")
                self.show_notification("Failed to process vehicle files", "error")
        
        except ImportError:
            self.dev_status_label.configure(text="Error: Developer module not found")
            self.show_notification("Developer module not available", "error")
            print("[ERROR] core.developer module not found")
        except Exception as e:
            self.dev_status_label.configure(text=f"Error: {str(e)}")
            self.show_notification(f"Error: {str(e)}", "error")
            print(f"[ERROR] Failed to add vehicle: {e}")
        finally:
            # Hide progress after delay
            self.after(2000, lambda: self.dev_progress_bar.pack_forget())
            self.after(2000, lambda: self.dev_status_label.pack_forget())
    
    def delete_vehicle(self, carid: str):
        """Delete a custom vehicle"""
        response = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete '{carid}'?\n\nThis will remove the vehicle from all menus."
        )
        
        if response:
            if carid in state.added_vehicles:
                carname = state.added_vehicles[carid]
                del state.added_vehicles[carid]
                
                # Save settings
                from core.settings import save_settings
                save_settings()
                
                # TODO: Also delete from vehicle templates directory if needed
                
                self.show_notification(f"Deleted '{carname}'", "info", 2000)
                self.refresh_developer_list()
            else:
                self.show_notification(f"Vehicle '{carid}' not found", "error")
    
    def refresh_developer_list(self):
        """Refresh the list of added vehicles"""
        # Clear existing
        for widget in self.dev_list_scroll.winfo_children():
            widget.destroy()
        
        # Get search query
        search_query = self.dev_search_var.get().lower().strip()
        
        # Filter vehicles
        filtered_vehicles = []
        for carid, carname in state.added_vehicles.items():
            if not search_query or search_query in carid.lower() or search_query in carname.lower():
                filtered_vehicles.append((carid, carname))
        
        # Empty state
        if not state.added_vehicles:
            empty_frame = ctk.CTkFrame(self.dev_list_scroll, fg_color="transparent")
            empty_frame.pack(expand=True, pady=40)
            
            ctk.CTkLabel(
                empty_frame,
                text="🛠️",
                font=ctk.CTkFont(size=48)
            ).pack()
            
            ctk.CTkLabel(
                empty_frame,
                text="No custom vehicles added yet",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=state.colors["text"]
            ).pack(pady=(10, 5))
            
            ctk.CTkLabel(
                empty_frame,
                text="Use the form above to add custom vehicles",
                font=ctk.CTkFont(size=11),
                text_color=state.colors["text_secondary"]
            ).pack()
            return
        
        # No results
        if not filtered_vehicles:
            no_results = ctk.CTkFrame(self.dev_list_scroll, fg_color="transparent")
            no_results.pack(expand=True, pady=40)
            
            ctk.CTkLabel(
                no_results,
                text="🔍",
                font=ctk.CTkFont(size=48)
            ).pack()
            
            ctk.CTkLabel(
                no_results,
                text="No vehicles found",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color=state.colors["text"]
            ).pack(pady=(10, 5))
            return
        
        # Show vehicles
        for carid, carname in sorted(filtered_vehicles, key=lambda x: x[1].lower()):
            vehicle_card = ctk.CTkFrame(
                self.dev_list_scroll,
                fg_color=state.colors["card_bg"],
                corner_radius=10,
                border_width=1,
                border_color=state.colors["border"]
            )
            vehicle_card.pack(fill="x", pady=3, padx=5)
            
            # Content
            content_frame = ctk.CTkFrame(vehicle_card, fg_color="transparent")
            content_frame.pack(fill="x", padx=10, pady=8)
            
            # Left side (info)
            info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)
            
            ctk.CTkLabel(
                info_frame,
                text=carname,
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=state.colors["text"],
                anchor="w"
            ).pack(anchor="w")
            
            ctk.CTkLabel(
                info_frame,
                text=f"ID: {carid}",
                font=ctk.CTkFont(size=10),
                text_color=state.colors["text_secondary"],
                anchor="w"
            ).pack(anchor="w")
            
            # Right side (delete button)
            delete_btn = ctk.CTkButton(
                content_frame,
                text="🗑️ Delete",
                width=80,
                height=28,
                fg_color=state.colors["error"],
                hover_color=state.colors["error_hover"],
                text_color="white",
                font=ctk.CTkFont(size=11, weight="bold"),
                corner_radius=6,
                command=lambda c=carid: self.delete_vehicle(c)
            )
            delete_btn.pack(side="right")