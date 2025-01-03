import os
import sys
import urllib.request
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk
from pathlib import Path
import threading

# Only import Windows-specific modules if on Windows
if os.name == 'nt':  # Windows
    import winshell  # type: ignore
    from win32com.client import Dispatch  # type: ignore
else:
    winshell = None
    Dispatch = None

class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Trading Bot Installer")
        self.root.geometry("400x300")
        self.root.iconbitmap("assets/icon.ico")  # We'll need to create this
        
        # Center window
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width/2) - (400/2)
        y = (screen_height/2) - (300/2)
        self.root.geometry(f'400x300+{int(x)}+{int(y)}')
        
        # Create main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add title
        self.title_label = ttk.Label(
            self.main_frame, 
            text="Trading Bot Installer",
            font=("Helvetica", 16)
        )
        self.title_label.grid(row=0, column=0, pady=20)
        
        # Add progress bar
        self.progress = ttk.Progressbar(
            self.main_frame, 
            length=300,
            mode='determinate'
        )
        self.progress.grid(row=1, column=0, pady=20)
        
        # Add status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Ready to install"
        )
        self.status_label.grid(row=2, column=0, pady=10)
        
        # Add install button
        self.install_button = ttk.Button(
            self.main_frame,
            text="Install",
            command=self.start_installation
        )
        self.install_button.grid(row=3, column=0, pady=20)
        
    def start_installation(self):
        """Start the installation process in a separate thread."""
        self.install_button.state(['disabled'])
        thread = threading.Thread(target=self.install)
        thread.start()
        
    def install(self):
        """Perform the installation."""
        try:
            self.update_status("Creating directories...")
            install_dir = Path(os.path.expanduser("~/Trading Bot"))
            install_dir.mkdir(parents=True, exist_ok=True)
            
            self.update_status("Downloading files...")
            self.progress['value'] = 20
            
            # Download and extract main package
            package_url = f"https://github.com/YOUR_USERNAME/YOUR_REPO/releases/latest/download/latest.zip"
            package_path = install_dir / "package.zip"
            urllib.request.urlretrieve(package_url, package_path)
            
            self.update_status("Extracting files...")
            self.progress['value'] = 40
            
            with zipfile.ZipFile(package_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)
            package_path.unlink()  # Remove zip file
            
            self.update_status("Installing Python...")
            self.progress['value'] = 60
            
            # Install Python if not present
            if not self._check_python():
                self._install_python()
            
            self.update_status("Installing dependencies...")
            self.progress['value'] = 80
            
            # Install dependencies
            subprocess.run([
                sys.executable, 
                "-m", "pip", 
                "install", 
                "-r", 
                str(install_dir / "requirements.txt")
            ])
            
            self.update_status("Creating shortcuts...")
            self.progress['value'] = 90
            
            # Create desktop shortcut
            self._create_shortcut(install_dir)
            
            self.update_status("Installation complete!")
            self.progress['value'] = 100
            
            self.install_button.state(['!disabled'])
            self.install_button.configure(text="Finish", command=self.root.destroy)
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.install_button.state(['!disabled'])
    
    def update_status(self, message: str):
        """Update the status label."""
        self.status_label['text'] = message
        self.root.update()
    
    def _check_python(self) -> bool:
        """Check if Python is installed."""
        try:
            subprocess.run([sys.executable, "--version"], check=True)
            return True
        except:
            return False
    
    def _install_python(self):
        """Download and install Python."""
        python_url = "https://www.python.org/ftp/python/3.9.7/python-3.9.7-amd64.exe"
        installer_path = Path(os.environ['TEMP']) / "python_installer.exe"
        
        urllib.request.urlretrieve(python_url, installer_path)
        subprocess.run([str(installer_path), "/quiet", "PrependPath=1"])
    
    def _create_shortcut(self, install_dir: Path):
        """Create desktop shortcut."""
        if os.name != 'nt':  # Not Windows
            self.update_status("Shortcut creation skipped (non-Windows system)")
            return

        desktop = Path(winshell.desktop())
        shortcut_path = desktop / "Trading Bot.lnk"
        
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(str(shortcut_path))
        shortcut.Targetpath = str(install_dir / "trading_bot.exe")
        shortcut.WorkingDirectory = str(install_dir)
        shortcut.IconLocation = str(install_dir / "assets/icon.ico")
        shortcut.save()

def main():
    installer = InstallerGUI()
    installer.root.mainloop()

if __name__ == "__main__":
    main() 