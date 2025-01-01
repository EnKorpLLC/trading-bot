from typing import Dict, Optional
import logging
from datetime import datetime
import json
from pathlib import Path
import requests
from packaging import version

logger = logging.getLogger(__name__)

class UpdateMonitor:
    def __init__(self, error_tracker):
        self.error_tracker = error_tracker
        self.update_check_url = "https://api.trade-locker.com/updates/check"
        self.error_report_url = "https://api.trade-locker.com/errors/report"
        self.current_version = "1.0.0"
        
    def check_for_updates(self) -> Optional[Dict]:
        """Check for available updates."""
        try:
            response = requests.get(
                self.update_check_url,
                params={'current_version': self.current_version}
            )
            
            if response.status_code == 200:
                update_info = response.json()
                if version.parse(update_info['latest_version']) > version.parse(self.current_version):
                    return update_info
            return None
            
        except Exception as e:
            logger.error(f"Error checking for updates: {str(e)}")
            return None
            
    def report_errors(self) -> bool:
        """Report accumulated errors to server."""
        try:
            error_summary = self.error_tracker.get_error_summary()
            
            # Get today's error log
            date_str = datetime.now().strftime('%Y%m%d')
            error_file = Path(f"logs/errors/errors_{date_str}.json")
            
            if error_file.exists():
                with open(error_file) as f:
                    error_details = json.load(f)
            else:
                error_details = []
                
            # Prepare report
            report = {
                'version': self.current_version,
                'timestamp': datetime.now().isoformat(),
                'summary': error_summary,
                'details': error_details
            }
            
            # Send report
            response = requests.post(
                self.error_report_url,
                json=report
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Error reporting errors: {str(e)}")
            return False 