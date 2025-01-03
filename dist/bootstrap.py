import sys
import urllib.request
import subprocess

def main():
    # URL of the installer
    installer_url = "https://github.com/yourusername/trading-bot/releases/latest/download/installer.py"
    
    try:
        # Download installer
        print("Downloading installer...")
        urllib.request.urlretrieve(installer_url, "installer.py")
        
        # Run installer
        subprocess.run([sys.executable, "installer.py"])
        
    except Exception as e:
        print(f"Error: {str(e)}")
        input("Press Enter to exit...")

if __name__ == "__main__":
    main() 