@echo off
:: BeamSkin Studio - Full Installer/Launcher
:: Checks Python, installs dependencies, then launches

if exist "launchers-scripts\launcher.py" (
    start "" pythonw "launchers-scripts\launcher.py"
    exit
) else (
    echo Error: launcher.py not found in launchers-scripts folder!
    echo Please make sure the launchers-scripts folder exists with launcher.py inside.
    pause
)