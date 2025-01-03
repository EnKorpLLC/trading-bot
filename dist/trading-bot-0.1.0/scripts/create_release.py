import os
import shutil
from pathlib import Path
import datetime

def create_release():
    # Get version from setup.py
    with open("setup.py", "r") as f:
        for line in f:
            if "version=" in line:
                version = line.split('"')[1]
                break
                
    # Create release directory
    release_name = f"trading-bot-{version}"
    release_dir = Path("dist") / release_name
    release_dir.mkdir(parents=True, exist_ok=True)
    
    # Directories to include
    dirs_to_copy = [
        "src",
        "config",
        "scripts",
        "docs",
        "tests"
    ]
    
    # Files to include
    files_to_copy = [
        "README.md",
        "requirements.txt",
        "setup.py",
        "setup.cfg",
        "pyproject.toml",
        "LICENSE"
    ]
    
    # Copy directories
    for dir_name in dirs_to_copy:
        if os.path.exists(dir_name):
            shutil.copytree(dir_name, release_dir / dir_name)
            
    # Copy files
    for file_name in files_to_copy:
        if os.path.exists(file_name):
            shutil.copy2(file_name, release_dir)
            
    # Create standalone installer
    installer_files = [
        "installer.py",
        "bootstrap.py"
    ]
    
    for file_name in installer_files:
        if os.path.exists(file_name):
            shutil.copy2(file_name, release_dir.parent / file_name)
            
    # Create small bootstrap executable (Windows)
    if os.name == 'nt':
        try:
            import PyInstaller.__main__
            
            PyInstaller.__main__.run([
                'bootstrap.py',
                '--onefile',
                '--noconsole',
                '--name=TradingBot-Installer',
                f'--distpath={release_dir.parent}'
            ])
        except ImportError:
            print("PyInstaller not found. Skipping executable creation.")
            
    # Create archive
    shutil.make_archive(str(release_dir), 'zip', release_dir.parent, release_name)
    
    print(f"Release archive created: {release_dir}.zip")
    print(f"Installer created: {release_dir.parent}/TradingBot-Installer.exe")

if __name__ == "__main__":
    create_release() 