@echo off
echo Setting up Trading Bot Frontend...

:: Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Node.js is not installed. Downloading and installing Node.js...
    :: Download Node.js installer
    powershell -Command "& {Invoke-WebRequest -Uri 'https://nodejs.org/dist/v18.19.0/node-v18.19.0-x64.msi' -OutFile 'nodejs_installer.msi'}"
    
    :: Install Node.js
    msiexec /i nodejs_installer.msi /qn
    
    :: Clean up installer
    del nodejs_installer.msi
    
    :: Add Node.js to PATH
    set PATH=%PATH%;C:\Program Files\nodejs\
    echo Node.js has been installed.
) else (
    echo Node.js is already installed.
)

:: Navigate to frontend directory
cd frontend

:: Install dependencies
echo Installing frontend dependencies...
call npm install

:: Start the development server
echo Starting development server...
start cmd /k "npm start"

echo Frontend setup complete! The development server should start automatically.
echo If the browser doesn't open automatically, visit http://localhost:3000
pause 