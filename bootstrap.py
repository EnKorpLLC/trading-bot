import urllib.request
import subprocess
import sys
import os
from pathlib import Path

def main():
    try:
        print("Downloading installer...")
        installer_url = f"https://github.com/EnKorpLLC/trading-bot/releases/latest/download/installer.exe"
        installer_path = Path(os.environ['TEMP']) / "trading_bot_installer.exe"
        
        urllib.request.urlretrieve(installer_url, installer_path)
        subprocess.run([str(installer_path)])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 