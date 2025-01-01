import sys
import os
from pathlib import Path
import requests
import json
import logging
import platform
from packaging import version
import hashlib
from typing import Optional, Dict
import subprocess

logger = logging.getLogger(__name__)

class InstallationManager:
    def __init__(self):
        self.app_data_dir = self._get_app_data_dir()
        self.current_version = "1.0.0"  # Load from version file
        self.update_url = "https://api.trade-locker.com/updates"
        self.platform = self._get_platform()
        
    def _get_platform(self) -> str:
        """Determine current platform and architecture."""
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        elif system == "android":
            return "android"
        elif system == "ios":
            return "ios"
        return "unknown"
        
    def _get_app_data_dir(self) -> Path:
        """Get appropriate application data directory."""
        if sys.platform == "win32":
            base_dir = os.environ.get("LOCALAPPDATA")
            return Path(base_dir) / "TradeLocker"
        elif sys.platform == "darwin":
            return Path.home() / "Library" / "Application Support" / "TradeLocker"
        else:  # Linux and others
            return Path.home() / ".tradelocker"
            
    def check_for_updates(self) -> Optional[Dict]:
        """Check for available updates."""
        try:
            response = requests.get(
                f"{self.update_url}/check",
                params={
                    "current_version": self.current_version,
                    "platform": self.platform
                }
            )
            
            if response.status_code == 200:
                update_info = response.json()
                if version.parse(update_info['latest_version']) > version.parse(self.current_version):
                    return update_info
            return None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            return None
            
    def download_update(self, update_info: Dict) -> bool:
        """Download and verify update package."""
        try:
            # Create downloads directory
            download_dir = self.app_data_dir / "downloads"
            download_dir.mkdir(parents=True, exist_ok=True)
            
            # Download update package
            response = requests.get(update_info['download_url'], stream=True)
            package_path = download_dir / f"update_{update_info['latest_version']}.zip"
            
            with open(package_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            # Verify package
            if not self._verify_package(package_path, update_info['checksum']):
                logger.error("Update package verification failed")
                return False
                
            return True
            
        except Exception as e:
            logger.error(f"Error downloading update: {str(e)}")
            return False
            
    def install_update(self, update_info: Dict) -> bool:
        """Install downloaded update."""
        try:
            package_path = self.app_data_dir / "downloads" / f"update_{update_info['latest_version']}.zip"
            
            # Backup current installation
            self._backup_current_installation()
            
            # Install update
            if self.platform in ["windows", "linux", "macos"]:
                return self._install_desktop_update(package_path)
            else:
                return self._install_mobile_update(package_path)
                
        except Exception as e:
            logger.error(f"Error installing update: {str(e)}")
            self._restore_backup()
            return False
            
    def _verify_package(self, package_path: Path, expected_checksum: str) -> bool:
        """Verify update package integrity."""
        sha256_hash = hashlib.sha256()
        
        with open(package_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
                
        return sha256_hash.hexdigest() == expected_checksum 