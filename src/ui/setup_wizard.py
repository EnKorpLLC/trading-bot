from PyQt6.QtWidgets import (
    QWizard, QWizardPage, QLabel, QLineEdit, 
    QVBoxLayout, QTextEdit, QPushButton, QMessageBox
)
from PyQt6.QtCore import Qt
import webbrowser
import logging

logger = logging.getLogger(__name__)

class APISetupWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Trading Bot Setup Wizard")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        
        # Add pages
        self.addPage(IntroPage())
        self.addPage(APIKeyInstructionsPage())
        self.addPage(APIKeyInputPage())
        
        self.setMinimumWidth(600)
        
        # Add a Skip button
        self.setButtonText(QWizard.WizardButton.CancelButton, "Skip for Now")
        self.setOption(QWizard.WizardOption.NoCancelButton, False)
        
    def get_credentials(self):
        """Return the API credentials entered by user or None if skipped."""
        if self.result() == QWizard.DialogCode.Rejected:
            return None
            
        return {
            'api_key': self.field('api_key'),
            'api_secret': self.field('api_secret')
        }

class IntroPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Welcome to Trading Bot")
        
        layout = QVBoxLayout()
        intro_text = QLabel(
            "This wizard will help you set up your trading bot by guiding you "
            "through the process of obtaining and configuring your API credentials.\n\n"
            "Before proceeding, please ensure you have:\n"
            "• A Trade Locker account\n"
            "• Access to your Trade Locker dashboard\n\n"
            "You can skip this setup and configure your API credentials later.\n\n"
            "Click Next to begin the setup process, or Skip for Now to explore the application."
        )
        intro_text.setWordWrap(True)
        layout.addWidget(intro_text)
        self.setLayout(layout)

class APIKeyInstructionsPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Getting Your API Keys")
        
        layout = QVBoxLayout()
        
        instructions = QLabel(
            "Follow these steps to get your API keys:\n\n"
            "1. Log in to your Trade Locker account\n"
            "2. Go to Settings > API Keys\n"
            "3. Click 'Create New API Key'\n"
            "4. Set the following permissions:\n"
            "   • View account information\n"
            "   • Trade\n"
            "5. Copy both the API Key and Secret Key\n\n"
            "Click the button below to open Trade Locker in your browser:"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)
        
        open_browser_btn = QPushButton("Open Trade Locker")
        open_browser_btn.clicked.connect(
            lambda: webbrowser.open("https://trade-locker.com/dashboard")
        )
        layout.addWidget(open_browser_btn)
        
        layout.addStretch()
        self.setLayout(layout)

class APIKeyInputPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Enter Your API Credentials")
        
        layout = QVBoxLayout()
        
        # API Key input
        layout.addWidget(QLabel("API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter your API key")
        layout.addWidget(self.api_key_input)
        
        # API Secret input
        layout.addWidget(QLabel("API Secret:"))
        self.api_secret_input = QTextEdit()
        self.api_secret_input.setPlaceholderText("Enter your API secret (including BEGIN and END lines)")
        self.api_secret_input.setMinimumHeight(100)
        layout.addWidget(self.api_secret_input)
        
        # Register fields
        self.registerField('api_key*', self.api_key_input)
        self.registerField('api_secret*', self.api_secret_input, 'plainText')
        
        layout.addStretch()
        self.setLayout(layout) 