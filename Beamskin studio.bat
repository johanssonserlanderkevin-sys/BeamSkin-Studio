@echo off
:: BeamSkin Studio - Silent Quick Launcher
:: No checks, no console windows, just shows loading GUI and launches

if exist "launchers-scripts\quick_launcher.py" (
    start "" pythonw "launchers-scripts\quick_launcher.py"
    exit
) else (
    echo Error: quick_launcher.py not found in launchers-scripts folder!
    echo Please make sure the launchers-scripts folder exists with quick_launcher.py inside.
    pause
)