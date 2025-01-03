from typing import List, Dict, Optional
import logging
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import requests
from pathlib import Path
import json
from PyQt6.QtWidgets import QSystemTrayIcon
from PyQt6.QtGui import QIcon
from twilio.rest import Client
from ..utils.config_manager import ConfigManager
from .sound_manager import SoundManager

logger = logging.getLogger(__name__)

class NotificationManager:
    def __init__(self):
        self.config = ConfigManager()
        self.notification_settings = self._load_notification_settings()
        
        # Initialize notification channels
        self.system_tray = self._setup_system_tray()
        self.email_client = self._setup_email_client()
        self.sms_client = self._setup_sms_client()
        
        # Notification history
        self.history_file = Path("data/notification_history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.notification_history = self._load_history()
        
        self.sound_manager = SoundManager()
        
    def send_notification(self, 
                         title: str, 
                         message: str, 
                         priority: str = "normal",
                         channels: List[str] = None,
                         sound: str = None) -> bool:
        """Send notification through specified channels."""
        if channels is None:
            channels = self.notification_settings['default_channels']
            
        success = True
        timestamp = datetime.now()
        
        try:
            # Send through each channel
            for channel in channels:
                if channel == "device" and self.notification_settings['device_enabled']:
                    success &= self._send_device_notification(title, message, priority)
                    
                if channel == "email" and self.notification_settings['email_enabled']:
                    success &= self._send_email_notification(title, message, priority)
                    
                if channel == "sms" and self.notification_settings['sms_enabled']:
                    success &= self._send_sms_notification(message, priority)
                    
            # Record notification
            self._record_notification({
                'timestamp': timestamp.isoformat(),
                'title': title,
                'message': message,
                'priority': priority,
                'channels': channels,
                'success': success
            })
            
            # Play sound if specified
            if sound and self.notification_settings['sounds_enabled']:
                self.sound_manager.play_sound(sound)
                
            return success
            
        except Exception as e:
            logger.error(f"Error sending notification: {str(e)}")
            return False
            
    def _send_device_notification(self, title: str, message: str, priority: str) -> bool:
        """Send device notification using system tray."""
        try:
            if self.system_tray and self.system_tray.isSystemTrayAvailable():
                icon = QSystemTrayIcon.Icon.Information
                if priority == "high":
                    icon = QSystemTrayIcon.Icon.Warning
                    
                self.system_tray.showMessage(
                    title,
                    message,
                    icon,
                    self.notification_settings['device_notification_duration'] * 1000
                )
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error sending device notification: {str(e)}")
            return False
            
    def _send_email_notification(self, title: str, message: str, priority: str) -> bool:
        """Send email notification."""
        try:
            if not self.email_client:
                return False
                
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.notification_settings['email_from']
            msg['To'] = self.notification_settings['email_to']
            msg['Subject'] = f"[{priority.upper()}] {title}"
            
            # Add body
            body = f"""
            {message}
            
            ---
            Sent by Trade Locker Bot
            Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            """
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            self.email_client.send_message(msg)
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return False
            
    def _send_sms_notification(self, message: str, priority: str) -> bool:
        """Send SMS notification using Twilio."""
        try:
            if not self.sms_client:
                return False
                
            # Prepare message
            if priority == "high":
                message = "🚨 " + message
                
            # Send SMS
            self.sms_client.messages.create(
                body=message,
                from_=self.notification_settings['twilio_from_number'],
                to=self.notification_settings['sms_to_number']
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            return False
            
    def _setup_system_tray(self) -> Optional[QSystemTrayIcon]:
        """Setup system tray icon."""
        try:
            tray = QSystemTrayIcon()
            tray.setIcon(QIcon("icons/app_icon.png"))
            tray.setVisible(True)
            return tray
        except Exception as e:
            logger.error(f"Error setting up system tray: {str(e)}")
            return None
            
    def _setup_email_client(self) -> Optional[smtplib.SMTP]:
        """Setup email client."""
        try:
            if not self.notification_settings['email_enabled']:
                return None
                
            client = smtplib.SMTP(
                self.notification_settings['smtp_server'],
                self.notification_settings['smtp_port']
            )
            client.starttls()
            client.login(
                self.notification_settings['smtp_username'],
                self.notification_settings['smtp_password']
            )
            return client
            
        except Exception as e:
            logger.error(f"Error setting up email client: {str(e)}")
            return None
            
    def _setup_sms_client(self) -> Optional[Client]:
        """Setup Twilio SMS client."""
        try:
            if not self.notification_settings['sms_enabled']:
                return None
                
            return Client(
                self.notification_settings['twilio_account_sid'],
                self.notification_settings['twilio_auth_token']
            )
            
        except Exception as e:
            logger.error(f"Error setting up SMS client: {str(e)}")
            return None
            
    def _load_notification_settings(self) -> Dict:
        """Load notification settings from config."""
        default_settings = {
            'device_enabled': True,
            'email_enabled': False,
            'sms_enabled': False,
            'default_channels': ['device'],
            'device_notification_duration': 5,  # seconds
            'smtp_server': '',
            'smtp_port': 587,
            'smtp_username': '',
            'smtp_password': '',
            'email_from': '',
            'email_to': '',
            'twilio_account_sid': '',
            'twilio_auth_token': '',
            'twilio_from_number': '',
            'sms_to_number': ''
        }
        
        settings = self.config.get_setting('notifications', default_settings)
        return {**default_settings, **settings}
        
    def _load_history(self) -> List[Dict]:
        """Load notification history from file."""
        try:
            if self.history_file.exists():
                with open(self.history_file) as f:
                    return json.load(f)
            return []
        except Exception as e:
            logger.error(f"Error loading notification history: {str(e)}")
            return []
            
    def _record_notification(self, notification: Dict):
        """Record notification in history."""
        try:
            self.notification_history.append(notification)
            
            # Trim history if too long
            max_history = self.notification_settings.get('max_history', 1000)
            if len(self.notification_history) > max_history:
                self.notification_history = self.notification_history[-max_history:]
                
            # Save to file
            with open(self.history_file, 'w') as f:
                json.dump(self.notification_history, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error recording notification: {str(e)}") 