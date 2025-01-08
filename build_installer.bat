@echo off
echo Building TradingBot Installer...

echo Step 1: Creating application icon...
python create_icon.py

echo Step 2: Building PyInstaller package...
python create_installer.py

echo Step 3: Building NSIS installer...
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi

echo Build complete!
echo The installer is available as TradingBot-Setup.exe
pause 