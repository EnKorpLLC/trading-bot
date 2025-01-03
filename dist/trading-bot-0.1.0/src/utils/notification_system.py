from PyQt6.QtWidgets import QMessageBox, QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QTimer
import logging
from enum import Enum
from typing import Optional, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationLevel(Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    TRADE = "TRADE"

class NotificationSystem:
    def __init__(self, parent=None):
        self.parent = parent
        self.notifications = []
        self.callbacks = {}
        
        # Initialize system tray
        self.tray_icon = QSystemTrayIcon(parent)
        self.tray_icon.setIcon(QIcon("assets/icon.png"))  # TODO: Add icon
        
        # Create tray menu
        self.tray_menu = QMenu()
        self.tray_menu.addAction("Show App", self._show_app)
        self.tray_menu.addAction("Clear Notifications", self.clear_notifications)
        self.tray_icon.setContextMenu(self.tray_menu)
        
        self.tray_icon.show()
        
    def notify(self, 
               message: str, 
               level: NotificationLevel = NotificationLevel.INFO,
               callback: Optional[Callable] = None):
        """Show a notification."""
        # Log the notification
        logger.log(
            logging.ERROR if level == NotificationLevel.ERROR else logging.INFO,
            message
        )
        
        # Store notification
        notification = {
            'message': message,
            'level': level,
            'timestamp': datetime.now(),
            'callback': callback
        }
        self.notifications.append(notification)
        
        # Show system tray notification
        self.tray_icon.showMessage(
            f"Trading Bot - {level.value}",
            message,
            QSystemTrayIcon.MessageIcon.Information,
            3000  # Display for 3 seconds
        )
        
        # Show dialog for errors
        if level == NotificationLevel.ERROR:
            self._show_error_dialog(message)
            
        # Execute callback if provided
        if callback:
            callback()
            
    def notify_trade(self, trade_details: dict):
        """Show trade-specific notification."""
        message = (
            f"New Trade: {trade_details['symbol']}\n"
            f"Type: {trade_details['side']}\n"
            f"Price: ${trade_details['entry_price']:.2f}"
        )
        self.notify(message, NotificationLevel.TRADE)
        
    def _show_error_dialog(self, message: str):
        """Show error dialog."""
        if self.parent:
            QMessageBox.critical(self.parent, "Error", message)
            
    def _show_app(self):
        """Show main application window."""
        if self.parent:
            self.parent.show()
            self.parent.activateWindow()
            
    def clear_notifications(self):
        """Clear all notifications."""
        self.notifications.clear()
        
    def register_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific events."""
        self.callbacks[event_type] = callback
        
    def get_recent_notifications(self, count: int = 10):
        """Get recent notifications."""
        return self.notifications[-count:] 