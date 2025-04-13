import os
import json
from typing import Dict, Any, List, Optional

class Config:
    """Configuration handler for the Telegram monitor"""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize with optional config path"""
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config.json"
        )
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            with open(self.config_path, "r") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Return default config if file doesn't exist or is invalid
            return {
                "host": "0.0.0.0",
                "port": 8000,
                "bots": {}
            }
    
    def save_config(self) -> None:
        """Save current configuration to file"""
        with open(self.config_path, "w") as f:
            json.dump(self.config, f, indent=2)
    
    def get_bot_config(self, name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific bot"""
        return self.config.get("bots", {}).get(name)
    
    def set_bot_config(self, name: str, config: Dict[str, Any]) -> None:
        """Set configuration for a specific bot"""
        if "bots" not in self.config:
            self.config["bots"] = {}
        
        self.config["bots"][name] = config
        self.save_config()
    
    def get_api_settings(self) -> Dict[str, Any]:
        """Get API server settings"""
        return {
            "host": self.config.get("host", "0.0.0.0"),
            "port": self.config.get("port", 8000)
        }
    
    def set_api_settings(self, host: str, port: int) -> None:
        """Set API server settings"""
        self.config["host"] = host
        self.config["port"] = port
        self.save_config()
