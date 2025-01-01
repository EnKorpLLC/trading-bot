import os
import sys
import urllib.request
import zipfile
import subprocess
import tkinter as tk
from tkinter import ttk
import threading

class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Trading Bot Installer")
        self.root.geometry("400x300")
        
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
            font=('Helvetica', 16, 'bold')
        )
        self.title_label.grid(row=0, column=0, pady=20)
        
        # Add progress bar
        self.progress = ttk.Progressbar(
            self.main_frame,
            orient="horizontal",
            length=300,
            mode="determinate"
        )
        self.progress.grid(row=1, column=0, pady=20)
        
        # Add status label
        self.status_label = ttk.Label(
            self.main_frame,
            text="Ready to install",
            wraplength=300
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
        self.install_button.state(['disabled'])
        thread = threading.Thread(target=self.install)
        thread.start()
        
    def update_status(self, message, progress=None):
        self.status_label['text'] = message
        if progress is not None:
            self.progress['value'] = progress
        self.root.update()
        
    def install(self):
        try:
            # Update status
            self.update_status("Checking Python installation...", 0)
            
            # Check Python version
            if sys.version_info < (3, 9):
                raise RuntimeError("Python 3.9 or higher is required")
            
            # Download latest release
            self.update_status("Downloading Trading Bot...", 20)
            release_url = "https://github.com/yourusername/trading-bot/releases/latest/download/trading-bot.zip"
            download_path = os.path.join(os.path.expanduser("~"), "Downloads", "trading-bot.zip")
            urllib.request.urlretrieve(release_url, download_path)
            
            # Create installation directory
            self.update_status("Creating installation directory...", 40)
            install_dir = os.path.join(os.path.expanduser("~"), "TradingBot")
            os.makedirs(install_dir, exist_ok=True)
            
            # Extract files
            self.update_status("Extracting files...", 60)
            with zipfile.ZipFile(download_path, 'r') as zip_ref:
                zip_ref.extractall(install_dir)
            
            # Install dependencies
            self.update_status("Installing dependencies...", 80)
            if sys.platform == 'win32':
                subprocess.run([
                    'cmd', '/c', 
                    os.path.join(install_dir, 'scripts', 'install.bat')
                ], cwd=install_dir)
            else:
                subprocess.run([
                    'bash',
                    os.path.join(install_dir, 'scripts', 'install.sh')
                ], cwd=install_dir)
            
            # Create desktop shortcut
            self.update_status("Creating desktop shortcut...", 90)
            self.create_shortcut(install_dir)
            
            # Cleanup
            os.remove(download_path)
            
            # Installation complete
            self.update_status("Installation complete!\nYou can now run Trading Bot from your desktop.", 100)
            self.install_button['text'] = "Finish"
            self.install_button['command'] = self.root.destroy
            self.install_button.state(['!disabled'])
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}")
            self.install_button['text'] = "Retry"
            self.install_button.state(['!disabled'])
            
    def create_shortcut(self, install_dir):
        if sys.platform == 'win32':
            # Windows shortcut
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "Trading Bot.lnk")
            
            import winshell
            from win32com.client import Dispatch
            
            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(shortcut_path)
            shortcut.Targetpath = os.path.join(install_dir, "venv", "Scripts", "trading-bot.exe")
            shortcut.WorkingDirectory = install_dir
            shortcut.save()
        else:
            # Linux/macOS desktop entry
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop, "Trading Bot.desktop")
            
            with open(shortcut_path, 'w') as f:
                f.write(f"""[Desktop Entry]
Name=Trading Bot
Exec={install_dir}/venv/bin/trading-bot
Type=Application
Terminal=false
""")
            os.chmod(shortcut_path, 0o755)

def main():
    installer = InstallerGUI()
    installer.root.mainloop()

if __name__ == "__main__":
    main() 