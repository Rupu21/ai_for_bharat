# Simple Snake Game with AI Modes

A simple Snake game with three modes: Manual, AI assistance, and Auto (full AI control). Uses Hugging Face models for AI decision-making.

## Features

- **Manual Mode**: Classic Snake gameplay with arrow key controls (you play)
- **AI Mode**: AI controls the snake using Hugging Face model (AI plays with ML model)
- **Auto Mode**: AI controls the snake using heuristic algorithm (AI plays with simple logic)
- **Configurable**: Customize game settings and AI model via config.json

## Installation

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the game:**
   ```bash
   python run.py
   ```

## Controls

- **1**: Switch to Manual mode (you control with arrow keys)
- **2**: Switch to AI mode (Hugging Face model controls)
- **3**: Switch to Auto mode (heuristic AI controls)
- **Arrow keys**: Move snake (Manual mode only)
- **R**: Restart game
- **ESC**: Quit

## Configuration

Edit `config.json` to customize:

```json
{
  "game": {
    "grid_width": 20,
    "grid_height": 20,
    "cell_size": 30,
    "game_speed": 0.2
  },
  "ai": {
    "model_name": "microsoft/DialoGPT-medium",
    "huggingface_token": "",
    "use_local_cache": true
  }
}
```

## AI Models

The game uses Hugging Face models for AI decision-making. You can:

- Change the model name in config.json
- Add your Hugging Face token for private models
- Models are cached locally for offline use

## Project Structure

```
├── retro_snake_ai/
│   ├── main.py          # Main game file
│   ├── config.py        # Configuration management
│   ├── game/            # Game logic
│   └── ai/              # AI engine
├── config.json          # Game configuration
├── requirements.txt     # Dependencies
└── run.py              # Simple runner
```

## Requirements

- Python 3.8+
- pygame
- transformers
- torch
- hypothesis (for testing)
- pytest (for testing)