from typing import Optional
import logging
from pathlib import Path
from PyQt6.QtMultimedia import QSoundEffect
from PyQt6.QtCore import QUrl

logger = logging.getLogger(__name__)

class SoundManager:
    def __init__(self):
        self.sounds_dir = Path("resources/sounds")
        self.sounds = {}
        self._load_sounds()
        
    def _load_sounds(self):
        """Load sound effects."""
        sound_files = {
            'loss_limit': "loss_limit_alert.wav",
            'profit_target': "profit_target.wav",
            'trade_entry': "trade_entry.wav",
            'trade_exit': "trade_exit.wav",
            'warning': "warning.wav",
            'error': "error.wav"
        }
        
        try:
            for sound_name, filename in sound_files.items():
                sound_path = self.sounds_dir / filename
                if sound_path.exists():
                    sound = QSoundEffect()
                    sound.setSource(QUrl.fromLocalFile(str(sound_path)))
                    sound.setVolume(1.0)
                    self.sounds[sound_name] = sound
                else:
                    logger.warning(f"Sound file not found: {sound_path}")
                    
        except Exception as e:
            logger.error(f"Error loading sounds: {str(e)}")
            
    def play_sound(self, sound_name: str):
        """Play a specific sound effect."""
        try:
            if sound := self.sounds.get(sound_name):
                sound.play()
            else:
                logger.warning(f"Sound not found: {sound_name}")
                
        except Exception as e:
            logger.error(f"Error playing sound {sound_name}: {str(e)}") 