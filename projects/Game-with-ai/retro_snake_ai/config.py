"""
Simple configuration management for the Snake game.
"""

import json
from pathlib import Path


class Config:
    """Simple configuration class."""
    
    def __init__(self):
        # Default values
        self.grid_width = 20
        self.grid_height = 20
        self.cell_size = 30
        self.game_speed = 0.2
        self.ai_model_name = "microsoft/DialoGPT-medium"
        self.huggingface_token = ""
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from config.json if it exists."""
        try:
            with open('config.json', 'r') as f:
                config_data = json.load(f)
                
            game_config = config_data.get('game', {})
            ai_config = config_data.get('ai', {})
            
            self.grid_width = game_config.get('grid_width', self.grid_width)
            self.grid_height = game_config.get('grid_height', self.grid_height)
            self.cell_size = game_config.get('cell_size', self.cell_size)
            self.game_speed = game_config.get('game_speed', self.game_speed)
            
            self.ai_model_name = ai_config.get('model_name', self.ai_model_name)
            self.huggingface_token = ai_config.get('huggingface_token', self.huggingface_token)
            
        except FileNotFoundError:
            print("Config file not found, using defaults")
            self.create_default_config()
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
    
    def create_default_config(self):
        """Create a default config.json file."""
        default_config = {
            "game": {
                "grid_width": self.grid_width,
                "grid_height": self.grid_height,
                "cell_size": self.cell_size,
                "game_speed": self.game_speed
            },
            "ai": {
                "model_name": self.ai_model_name,
                "huggingface_token": self.huggingface_token,
                "use_local_cache": True
            }
        }
        
        try:
            with open('config.json', 'w') as f:
                json.dump(default_config, f, indent=2)
            print("Created default config.json file")
        except Exception as e:
            print(f"Could not create config file: {e}")


# Global config instance
config = Config()