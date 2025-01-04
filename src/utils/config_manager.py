from typing import Dict, Any, Optional
import logging
from pathlib import Path
import json
import yaml
import os
from dataclasses import dataclass
from copy import deepcopy
import sys
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class EnvironmentConfig:
    name: str
    description: str
    settings: Dict

@dataclass
class InstallConfig:
    version: str
    install_date: str
    install_path: Path
    last_update_check: str

class ConfigManager:
    def __init__(self):
        self.config_dir = Path("config")
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.env = os.getenv("TRADING_ENV", "development")
        self.configs: Dict[str, Dict] = {}
        self.env_configs: Dict[str, EnvironmentConfig] = {}
        self.loaded_files = set()
        self.version = "0.2.0"
        self.install_config = self._load_install_config()
        
        # Load configurations
        self._load_base_config()
        self._load_env_config()
        self._validate_config()
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get configuration setting with dot notation support."""
        try:
            value = self.configs.get(self.env, {})
            for part in key.split('.'):
                value = value.get(part, {})
            return value if value != {} else default
            
        except Exception as e:
            logger.error(f"Error getting config setting {key}: {str(e)}")
            return default
            
    def update_setting(self, key: str, value: Any, persist: bool = True) -> bool:
        """Update configuration setting."""
        try:
            config = self.configs.get(self.env, {})
            parts = key.split('.')
            current = config
            
            # Navigate to the correct depth
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
                
            # Update value
            current[parts[-1]] = value
            
            # Persist if requested
            if persist:
                self._save_config()
                
            return True
            
        except Exception as e:
            logger.error(f"Error updating config setting {key}: {str(e)}")
            return False
            
    def add_environment(self, 
                       name: str, 
                       description: str,
                       settings: Dict) -> bool:
        """Add new environment configuration."""
        try:
            env_config = EnvironmentConfig(
                name=name,
                description=description,
                settings=settings
            )
            
            self.env_configs[name] = env_config
            self.configs[name] = settings
            
            # Save environment config
            env_file = self.config_dir / f"{name}.yaml"
            with open(env_file, 'w') as f:
                yaml.dump({
                    'name': name,
                    'description': description,
                    'settings': settings
                }, f)
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding environment {name}: {str(e)}")
            return False
            
    def switch_environment(self, env_name: str) -> bool:
        """Switch to different environment."""
        try:
            if env_name not in self.env_configs:
                logger.error(f"Environment {env_name} not found")
                return False
                
            self.env = env_name
            os.environ["TRADING_ENV"] = env_name
            
            # Reload configurations
            self._load_env_config()
            self._validate_config()
            
            return True
            
        except Exception as e:
            logger.error(f"Error switching environment: {str(e)}")
            return False
            
    def _load_base_config(self):
        """Load base configuration."""
        try:
            base_config = self.config_dir / "base.yaml"
            if base_config.exists():
                with open(base_config) as f:
                    self.configs['base'] = yaml.safe_load(f)
                self.loaded_files.add(base_config)
                
        except Exception as e:
            logger.error(f"Error loading base config: {str(e)}")
            
    def _load_env_config(self):
        """Load environment-specific configuration."""
        try:
            env_config = self.config_dir / f"{self.env}.yaml"
            if env_config.exists():
                with open(env_config) as f:
                    config_data = yaml.safe_load(f)
                    
                self.env_configs[self.env] = EnvironmentConfig(
                    name=config_data['name'],
                    description=config_data['description'],
                    settings=config_data['settings']
                )
                
                # Merge with base config
                base_config = deepcopy(self.configs.get('base', {}))
                self.configs[self.env] = self._merge_configs(
                    base_config,
                    config_data['settings']
                )
                
                self.loaded_files.add(env_config)
                
        except Exception as e:
            logger.error(f"Error loading env config: {str(e)}")
            
    def _merge_configs(self, base: Dict, override: Dict) -> Dict:
        """Deep merge configuration dictionaries."""
        merged = base.copy()
        
        for key, value in override.items():
            if (key in merged and 
                isinstance(merged[key], dict) and 
                isinstance(value, dict)):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
        
    def _validate_config(self) -> bool:
        """Validate configuration settings."""
        try:
            config = self.configs.get(self.env, {})
            
            # Required settings
            required = [
                'api_credentials.exchange',
                'api_credentials.api_key',
                'api_credentials.api_secret',
                'risk_management.max_position_size',
                'risk_management.max_daily_loss'
            ]
            
            for setting in required:
                if not self.get_setting(setting):
                    logger.error(f"Missing required setting: {setting}")
                    return False
                    
            return True
            
        except Exception as e:
            logger.error(f"Error validating config: {str(e)}")
            return False
            
    def _save_config(self):
        """Save current configuration."""
        try:
            env_file = self.config_dir / f"{self.env}.yaml"
            
            config_data = {
                'name': self.env,
                'description': self.env_configs[self.env].description,
                'settings': self.configs[self.env]
            }
            
            with open(env_file, 'w') as f:
                yaml.dump(config_data, f)
                
        except Exception as e:
            logger.error(f"Error saving config: {str(e)}") 

    def _load_install_config(self) -> InstallConfig:
        """Load or create installation configuration."""
        install_file = Path.home() / ".trading-bot" / "install.json"
        install_file.parent.mkdir(parents=True, exist_ok=True)
        
        if install_file.exists():
            try:
                with open(install_file) as f:
                    data = json.load(f)
                return InstallConfig(**data)
            except Exception as e:
                logger.error(f"Error loading install config: {str(e)}")
                
        # Create new install config
        config = InstallConfig(
            version=self.version,
            install_date=datetime.now().isoformat(),
            install_path=Path(sys.executable).parent,
            last_update_check=datetime.now().isoformat()
        )
        
        # Save config
        with open(install_file, 'w') as f:
            json.dump(config.__dict__, f, indent=2, default=str)
            
        return config 