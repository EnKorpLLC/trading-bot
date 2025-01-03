from typing import Dict
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import QApplication
from dataclasses import dataclass

@dataclass
class Theme:
    name: str
    description: str
    colors: Dict[str, str]
    styles: Dict[str, str]

class ThemeManager:
    def __init__(self):
        self.themes = {
            'light': Theme(
                name='Light',
                description='Light theme for day trading',
                colors={
                    'background': '#FFFFFF',
                    'foreground': '#000000',
                    'primary': '#007AFF',
                    'secondary': '#5856D6',
                    'success': '#34C759',
                    'warning': '#FF9500',
                    'error': '#FF3B30'
                },
                styles={
                    'font-family': 'Segoe UI',
                    'font-size': '12px',
                    'border-radius': '4px'
                }
            ),
            'dark': Theme(
                name='Dark',
                description='Dark theme for night trading',
                colors={
                    'background': '#000000',
                    'foreground': '#FFFFFF',
                    'primary': '#0A84FF',
                    'secondary': '#5E5CE6',
                    'success': '#30D158',
                    'warning': '#FF9F0A',
                    'error': '#FF453A'
                },
                styles={
                    'font-family': 'Segoe UI',
                    'font-size': '12px',
                    'border-radius': '4px'
                }
            )
        }
        
    def apply_theme(self, theme_name: str):
        """Apply theme to application."""
        if theme_name not in self.themes:
            raise ValueError(f"Theme {theme_name} not found")
            
        theme = self.themes[theme_name]
        app = QApplication.instance()
        
        # Create palette
        palette = QPalette()
        
        # Set colors
        palette.setColor(QPalette.ColorRole.Window, 
                        QColor(theme.colors['background']))
        palette.setColor(QPalette.ColorRole.WindowText,
                        QColor(theme.colors['foreground']))
        palette.setColor(QPalette.ColorRole.Base,
                        QColor(theme.colors['background']))
        palette.setColor(QPalette.ColorRole.AlternateBase,
                        QColor(theme.colors['secondary']))
        palette.setColor(QPalette.ColorRole.ToolTipBase,
                        QColor(theme.colors['background']))
        palette.setColor(QPalette.ColorRole.ToolTipText,
                        QColor(theme.colors['foreground']))
        palette.setColor(QPalette.ColorRole.Text,
                        QColor(theme.colors['foreground']))
        palette.setColor(QPalette.ColorRole.Button,
                        QColor(theme.colors['primary']))
        palette.setColor(QPalette.ColorRole.ButtonText,
                        QColor(theme.colors['background']))
        palette.setColor(QPalette.ColorRole.Link,
                        QColor(theme.colors['primary']))
        palette.setColor(QPalette.ColorRole.Highlight,
                        QColor(theme.colors['primary']))
        palette.setColor(QPalette.ColorRole.HighlightedText,
                        QColor(theme.colors['background']))
        
        # Apply palette
        app.setPalette(palette)
        
        # Apply stylesheet
        app.setStyleSheet(self._generate_stylesheet(theme))
        
    def _generate_stylesheet(self, theme: Theme) -> str:
        """Generate Qt stylesheet from theme."""
        return f"""
            QWidget {{
                background-color: {theme.colors['background']};
                color: {theme.colors['foreground']};
                font-family: {theme.styles['font-family']};
                font-size: {theme.styles['font-size']};
            }}
            
            QPushButton {{
                background-color: {theme.colors['primary']};
                color: {theme.colors['background']};
                border: none;
                padding: 5px 15px;
                border-radius: {theme.styles['border-radius']};
            }}
            
            QPushButton:hover {{
                background-color: {theme.colors['secondary']};
            }}
            
            QLineEdit {{
                padding: 5px;
                border: 1px solid {theme.colors['secondary']};
                border-radius: {theme.styles['border-radius']};
            }}
            
            QTableWidget {{
                gridline-color: {theme.colors['secondary']};
                border: none;
            }}
            
            QHeaderView::section {{
                background-color: {theme.colors['secondary']};
                color: {theme.colors['background']};
                padding: 5px;
            }}
        """ 