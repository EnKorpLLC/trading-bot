import os
import sys
import shutil
from PyInstaller.__main__ import run

def create_installer():
    # Clean previous builds
    for dir_name in ['build', 'dist']:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    # PyInstaller configuration
    installer_args = [
        'src/main.py',  # Main script
        '--name=TradingBot',
        '--windowed',  # GUI mode
        '--onedir',    # Create a directory containing the executable
        '--icon=resources/icon.ico',  # Application icon
        '--add-data=resources;resources',  # Include resources
        '--hidden-import=sklearn.tree',
        '--hidden-import=sklearn.ensemble',
        '--hidden-import=sklearn.preprocessing',
        '--hidden-import=ta',
        '--hidden-import=deap',
        '--noconsole',
        '--clean',
    ]
    
    # Add data files
    data_dirs = ['models', 'config', 'strategies']
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            installer_args.append(f'--add-data={data_dir};{data_dir}')
    
    # Run PyInstaller
    run(installer_args)
    
    # Create the installer directory if it doesn't exist
    installer_dir = 'installer'
    os.makedirs(installer_dir, exist_ok=True)
    
    # Copy the distribution to the installer directory
    dist_dir = os.path.join('dist', 'TradingBot')
    if os.path.exists(dist_dir):
        target_dir = os.path.join(installer_dir, 'TradingBot')
        if os.path.exists(target_dir):
            shutil.rmtree(target_dir)
        shutil.copytree(dist_dir, target_dir)
        
        # Create a simple batch file to run the application
        with open(os.path.join(installer_dir, 'Install.bat'), 'w') as f:
            f.write('@echo off\n')
            f.write('echo Installing TradingBot...\n')
            f.write('xcopy /E /I /Y TradingBot "%LOCALAPPDATA%\\TradingBot"\n')
            f.write('echo Creating desktop shortcut...\n')
            f.write('@echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs\n')
            f.write('@echo sLinkFile = oWS.ExpandEnvironmentStrings("%USERPROFILE%\\Desktop\\TradingBot.lnk") >> CreateShortcut.vbs\n')
            f.write('@echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs\n')
            f.write('@echo oLink.TargetPath = oWS.ExpandEnvironmentStrings("%LOCALAPPDATA%\\TradingBot\\TradingBot.exe") >> CreateShortcut.vbs\n')
            f.write('@echo oLink.Save >> CreateShortcut.vbs\n')
            f.write('cscript CreateShortcut.vbs\n')
            f.write('del CreateShortcut.vbs\n')
            f.write('echo Installation complete!\n')
            f.write('pause\n')
        
        print("Installer created successfully!")
        print(f"Installer location: {os.path.abspath(installer_dir)}")
    else:
        print("Error: Build failed!")

if __name__ == '__main__':
    create_installer() 