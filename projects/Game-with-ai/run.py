#!/usr/bin/env python3
"""
Simple runner for the Snake game.
"""

import sys
import os

# Add the project directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from retro_snake_ai.main import main

if __name__ == "__main__":
    main()