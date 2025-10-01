@echo off
set "PYTHON_EXE=C:\Python313\python.exe"
set "GAME_PATH=%%LOCALAPPDATA%%\StalCal\client\main.py"
set "WORKING_DIR=%%LOCALAPPDATA%%\StalCal\client"
set "ICON_LOCATION_WITH_INDEX=%%LOCALAPPDATA%%\StalCal\client\assets\icon.ico,0"

:: 🌟 НОВОЕ ИМЯ ЯРЛЫКА!
set "SHORTCUT_NAME=StalCal Game.lnk" 

echo.
echo --- Создание ярлыка %SHORTCUT_NAME% ---

powershell -Command "$Desktop = [System.Environment]::GetFolderPath('Desktop'); " ^
           "$ShortcutPath = Join-Path $Desktop '%SHORTCUT_NAME%'; " ^
           "$s=(New-Object -COM WScript.Shell).CreateShortcut($ShortcutPath); " ^
           "$s.TargetPath='%PYTHON_EXE%'; " ^
           "$s.Arguments='%GAME_PATH%'; " ^
           "$s.WorkingDirectory='%WORKING_DIR%'; " ^
           "$s.IconLocation='%ICON_LOCATION_WITH_INDEX%';" ^
           "$s.Save()"
...