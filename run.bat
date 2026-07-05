@echo off
title Command & Conquer - Tiberian Dawn Clone
echo ========================================
echo    Command & Conquer: Tiberian Dawn
echo         Python + Pygame Clone
echo ========================================
echo.
echo  OPERATION CONTROLS:
echo    Left Click      - Select unit or building
echo    Drag Left Click - Select multiple units
echo    Right Click     - Move / Attack enemy
echo    WASD / Arrows   - Scroll the map
echo    Mouse at edge   - Auto-scroll
echo    F1 / H          - Toggle help overlay
echo    R               - Restart (after game over)
echo    ESC             - Quit game
echo.
echo  SIDEBAR:
echo    Click Construction Yard -^> building buttons appear
echo    Click Barracks/War Factory -^> unit training buttons
echo.
echo  ECONOMY:
echo    Harvester auto-collects Tiberium
echo    Returns to Refinery for credits
echo.
echo ========================================
"C:\Users\Admin\AppData\Local\Programs\Python\Python312\python.exe" "%~dp0game.py"
pause
