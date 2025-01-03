from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout
from PyQt6.QtWidgets import QLineEdit, QCheckBox, QSpinBox, QPushButton, QSlider
from PyQt6.QtCore import Qt

class NotificationSettingsTab(QWidget):
    def __init__(self, config_manager):
        super().__init__()
        self.config = config_manager
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Device notifications
        device_group = QGroupBox("Device Notifications")
        device_layout = QFormLayout()
        
        self.device_enabled = QCheckBox()
        self.notification_duration = QSpinBox()
        self.notification_duration.setRange(1, 30)
        
        device_layout.addRow("Enable:", self.device_enabled)
        device_layout.addRow("Duration (seconds):", self.notification_duration)
        device_group.setLayout(device_layout)
        
        # Email notifications
        email_group = QGroupBox("Email Notifications")
        email_layout = QFormLayout()
        
        self.email_enabled = QCheckBox()
        self.smtp_server = QLineEdit()
        self.smtp_port = QSpinBox()
        self.smtp_port.setRange(1, 65535)
        self.smtp_username = QLineEdit()
        self.smtp_password = QLineEdit()
        self.smtp_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.email_from = QLineEdit()
        self.email_to = QLineEdit()
        
        email_layout.addRow("Enable:", self.email_enabled)
        email_layout.addRow("SMTP Server:", self.smtp_server)
        email_layout.addRow("SMTP Port:", self.smtp_port)
        email_layout.addRow("Username:", self.smtp_username)
        email_layout.addRow("Password:", self.smtp_password)
        email_layout.addRow("From Email:", self.email_from)
        email_layout.addRow("To Email:", self.email_to)
        email_group.setLayout(email_layout)
        
        # SMS notifications
        sms_group = QGroupBox("SMS Notifications")
        sms_layout = QFormLayout()
        
        self.sms_enabled = QCheckBox()
        self.twilio_sid = QLineEdit()
        self.twilio_token = QLineEdit()
        self.twilio_token.setEchoMode(QLineEdit.EchoMode.Password)
        self.twilio_from = QLineEdit()
        self.sms_to = QLineEdit()
        
        sms_layout.addRow("Enable:", self.sms_enabled)
        sms_layout.addRow("Twilio Account SID:", self.twilio_sid)
        sms_layout.addRow("Twilio Auth Token:", self.twilio_token)
        sms_layout.addRow("From Number:", self.twilio_from)
        sms_layout.addRow("To Number:", self.sms_to)
        sms_group.setLayout(sms_layout)
        
        # Sound notifications
        sound_group = QGroupBox("Sound Notifications")
        sound_layout = QFormLayout()
        
        self.sounds_enabled = QCheckBox()
        self.sound_volume = QSlider(Qt.Orientation.Horizontal)
        self.sound_volume.setRange(0, 100)
        self.sound_volume.setValue(50)
        
        # Test sound buttons
        test_loss_sound = QPushButton("Test Loss Limit Sound")
        test_profit_sound = QPushButton("Test Profit Target Sound")
        
        test_loss_sound.clicked.connect(
            lambda: self.notification_manager.sound_manager.play_sound('loss_limit')
        )
        test_profit_sound.clicked.connect(
            lambda: self.notification_manager.sound_manager.play_sound('profit_target')
        )
        
        sound_layout.addRow("Enable Sounds:", self.sounds_enabled)
        sound_layout.addRow("Volume:", self.sound_volume)
        sound_layout.addRow(test_loss_sound)
        sound_layout.addRow(test_profit_sound)
        
        sound_group.setLayout(sound_layout)
        # Add all groups to layout
        layout.addWidget(device_group)
        layout.addWidget(email_group)
        layout.addWidget(sms_group)
        
        # Test buttons
        test_layout = QHBoxLayout()
        test_device = QPushButton("Test Device")
        test_email = QPushButton("Test Email")
        test_sms = QPushButton("Test SMS")
        
        test_device.clicked.connect(self._test_device_notification)
        test_email.clicked.connect(self._test_email_notification)
        test_sms.clicked.connect(self._test_sms_notification)
        
        test_layout.addWidget(test_device)
        test_layout.addWidget(test_email)
        test_layout.addWidget(test_sms)
        
        layout.addLayout(test_layout)
        self.setLayout(layout)
        
        # Load current settings
        self._load_settings()
        
    def _load_settings(self):
        """Load current notification settings."""
        settings = self.config.get_setting('notifications', {})
        
        # Device settings
        self.device_enabled.setChecked(settings.get('device_enabled', True))
        self.notification_duration.setValue(settings.get('device_notification_duration', 5))
        
        # Email settings
        self.email_enabled.setChecked(settings.get('email_enabled', False))
        self.smtp_server.setText(settings.get('smtp_server', ''))
        self.smtp_port.setValue(settings.get('smtp_port', 587))
        self.smtp_username.setText(settings.get('smtp_username', ''))
        self.smtp_password.setText(settings.get('smtp_password', ''))
        self.email_from.setText(settings.get('email_from', ''))
        self.email_to.setText(settings.get('email_to', ''))
        
        # SMS settings
        self.sms_enabled.setChecked(settings.get('sms_enabled', False))
        self.twilio_sid.setText(settings.get('twilio_account_sid', ''))
        self.twilio_token.setText(settings.get('twilio_auth_token', ''))
        self.twilio_from.setText(settings.get('twilio_from_number', ''))
        self.sms_to.setText(settings.get('sms_to_number', '')) 
        self.sms_to.setText(settings.get('sms_to_number', '')) 