"""
How To Tab
"""
import customtkinter as ctk
from typing import Dict, Tuple, List
from gui.state import state


class HowToTab(ctk.CTkFrame):
    """Complete How-To documentation tab with all chapters"""
    
    def __init__(self, parent: ctk.CTk):
        super().__init__(parent, fg_color=state.colors["app_bg"])
        
        # UI references
        self.howto_text: ctk.CTkTextbox = None
        self.chapter_buttons: List[Tuple[ctk.CTkButton, str]] = []
        
        # Chapter data (all 10 chapters from app_backup.py)
        self.chapters = {
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

Project Overview:

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
5. The vehicle appears in the Vehicles in project

You can add the same vehicle multiple times if you want
different sets of skins organized separately.

Adding Skins to Vehicles:

1. Click on a vehicle card in the Vehicles in project
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
1. Review your project in the Vehicles in project
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
        
        self._setup_ui()
        self.load_all_chapters()  # Load all chapters by default
    
    def _setup_ui(self):
        """Set up the How-To tab UI"""
        # Main frame
        howto_main_frame = ctk.CTkFrame(self, fg_color="transparent")
        howto_main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Chapter navigation frame
        chapter_nav_frame = ctk.CTkFrame(
            howto_main_frame,
            fg_color=state.colors["frame_bg"],
            corner_radius=12
        )
        chapter_nav_frame.pack(fill="x", pady=(0, 10))
        
        # Two rows for chapter buttons
        row1_frame = ctk.CTkFrame(chapter_nav_frame, fg_color="transparent")
        row1_frame.pack(fill="x", padx=5, pady=(10, 5))
        
        row2_frame = ctk.CTkFrame(chapter_nav_frame, fg_color="transparent")
        row2_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        # Text box for displaying chapters
        self.howto_text = ctk.CTkTextbox(
            howto_main_frame,
            width=580,
            height=900,
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=state.colors["frame_bg"],
            text_color=state.colors["text"]
        )
        self.howto_text.pack(fill="both", expand=True)
        
        # View All button
        view_all_btn = ctk.CTkButton(
            row1_frame,
            text="📖 View All Chapters",
            command=self.load_all_chapters,
            width=150,
            height=35,
            fg_color=state.colors["card_bg"],
            hover_color=state.colors["card_hover"],
            text_color=state.colors["text"],
            font=ctk.CTkFont(size=12, weight="bold"),
            corner_radius=8
        )
        view_all_btn.pack(side="left", padx=5)
        
        # Sort chapters by number
        sorted_chapters = sorted(self.chapters.keys(), key=lambda x: int(x.split()[1]))
        
        # First 5 chapters in row 1
        for chapter_key in sorted_chapters[:5]:
            chapter_title, _ = self.chapters[chapter_key]
            
            btn = ctk.CTkButton(
                row1_frame,
                text=chapter_title,
                command=lambda k=chapter_key: self.load_chapter(k),
                width=150,
                height=35,
                fg_color=state.colors["card_bg"],
                hover_color=state.colors["card_hover"],
                text_color=state.colors["text"],
                font=ctk.CTkFont(size=13, weight="bold"),
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.chapter_buttons.append((btn, chapter_key))
        
        # Chapters 6-10 in row 2
        for chapter_key in sorted_chapters[5:]:
            chapter_title, _ = self.chapters[chapter_key]
            
            btn = ctk.CTkButton(
                row2_frame,
                text=chapter_title,
                command=lambda k=chapter_key: self.load_chapter(k),
                width=150,
                height=35,
                fg_color=state.colors["card_bg"],
                hover_color=state.colors["card_hover"],
                text_color=state.colors["text"],
                font=ctk.CTkFont(size=13, weight="bold"),
                corner_radius=8
            )
            btn.pack(side="left", padx=5)
            self.chapter_buttons.append((btn, chapter_key))
    
    def load_chapter(self, chapter_key: str):
        """Load a specific chapter into the text box"""
        chapter_title, chapter_content = self.chapters[chapter_key]
        
        # Update text box
        self.howto_text.configure(state="normal")
        self.howto_text.delete("0.0", "end")
        self.howto_text.insert("0.0", chapter_content)
        self.howto_text.configure(state="disabled")
        
        # Update button colors
        for btn, key in self.chapter_buttons:
            if key == chapter_key:
                btn.configure(fg_color=state.colors["accent"], text_color=state.colors["accent_text"])
            else:
                btn.configure(fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        
        print(f"[DEBUG] Loaded: {chapter_key} - {chapter_title}")
    
    def load_all_chapters(self):
        """Load all chapters into the text box"""
        self.howto_text.configure(state="normal")
        self.howto_text.delete("0.0", "end")
        
        # Introduction
        self.howto_text.insert("0.0", """How to Use Guide

This guide will walk you through the basics of creating a skin and using the modding tool to package it correctly.
Follow each chapter carefully to ensure your skin works in-game.

Use the chapter buttons above to jump to specific sections, or scroll through all chapters below.

""")
        
        # Add all chapters
        for chapter_key in sorted(self.chapters.keys(), key=lambda x: int(x.split()[1])):
            chapter_title, chapter_content = self.chapters[chapter_key]
            self.howto_text.insert("end", chapter_content)
            self.howto_text.insert("end", "\n")
        
        self.howto_text.configure(state="disabled")
        
        # Reset all button colors
        for btn, key in self.chapter_buttons:
            btn.configure(fg_color=state.colors["card_bg"], text_color=state.colors["text"])
        
        print("[DEBUG] Loaded all chapters")