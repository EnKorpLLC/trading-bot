from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor
from enum import Enum
import json
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class Theme(Enum):
    LIGHT = "light"
    DARK = "dark"

class ThemeManager:
    def __init__(self):
        self.current_theme = Theme.LIGHT
        self.config_file = Path("config/theme.json")
        self.load_theme_preference()
        
    def load_theme_preference(self):
        """Load saved theme preference."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    self.current_theme = Theme(config.get('theme', 'light'))
        except Exception as e:
            logger.error(f"Error loading theme preference: {e}")
            
    def save_theme_preference(self):
        """Save current theme preference."""
        try:
            self.config_file.parent.mkdir(exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump({'theme': self.current_theme.value}, f)
        except Exception as e:
            logger.error(f"Error saving theme preference: {e}")
            
    def apply_theme(self, app: QApplication):
        """Apply the current theme to the application."""
        if self.current_theme == Theme.DARK:
            self._apply_dark_theme(app)
        else:
            self._apply_light_theme(app)
            
    def toggle_theme(self, app: QApplication):
        """Toggle between light and dark themes."""
        self.current_theme = Theme.DARK if self.current_theme == Theme.LIGHT else Theme.LIGHT
        self.apply_theme(app)
        self.save_theme_preference()
        
    def _apply_dark_theme(self, app: QApplication):
        """Apply dark theme to the application."""
        palette = QPalette()
        palette.setColor(QPalette.ColorRole.Window, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Base, QColor(42, 42, 42))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(66, 66, 66))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Text, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Button, QColor(53, 53, 53))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(255, 255, 255))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(255, 255, 255))
        
        app.setPalette(palette)
        
    def _apply_light_theme(self, app: QApplication):
        """Apply light theme to the application."""
        app.setPalette(app.style().standardPalette()) 