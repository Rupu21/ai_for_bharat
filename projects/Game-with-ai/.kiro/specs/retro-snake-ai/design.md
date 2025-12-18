# Design Document

## Overview

A simple Snake game implemented in Python using Pygame for graphics and Hugging Face transformers for AI. The system has three modes: Manual (player control), AI (AI suggestions with player control), and Auto (full AI control). The architecture separates game logic, rendering, and AI components for maintainability.

## Architecture

Simple layered architecture:

```
┌─────────────────────────────────────────┐
│            Game Interface               │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │   Pygame    │  │  Mode Selector  │   │
│  │   Window    │  │                 │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            Game Engine                  │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │    Snake    │  │     Food        │   │
│  │   Logic     │  │   Manager       │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
┌─────────────────────────────────────────┐
│            AI Engine                    │
│  ┌─────────────┐  ┌─────────────────┐   │
│  │ Hugging Face│  │  Move Predictor │   │
│  │   Model     │  │                 │   │
│  └─────────────┘  └─────────────────┘   │
└─────────────────────────────────────────┘
```

## Components and Interfaces

### Core Game Components

**Game**
- Main game class that manages the game loop and state
- Handles mode switching (Manual, AI, Auto)
- Interface: `run()`, `update()`, `handle_input()`, `switch_mode()`

**Snake**
- Manages snake position, movement, and growth
- Handles collision detection
- Interface: `move(direction)`, `grow()`, `check_collision()`, `get_segments()`

**Food**
- Handles food placement and consumption
- Interface: `spawn()`, `get_position()`, `is_eaten(snake_head)`

### AI Components

**AIEngine**
- Loads and manages Hugging Face model
- Provides move predictions based on game state
- Interface: `load_model()`, `predict_move(game_state)`, `get_confidence()`

### Configuration

**Config**
- Manages game settings and AI model configuration
- Loads from config file with fallback to defaults
- Interface: `load()`, `get(key)`, `save()`

## Data Models

### Game State Structure
```python
@dataclass
class GameState:
    snake_segments: List[Tuple[int, int]]
    snake_direction: str  # 'UP', 'DOWN', 'LEFT', 'RIGHT'
    food_position: Tuple[int, int]
    score: int
    game_over: bool
    mode: str  # 'MANUAL', 'AI', 'AUTO'
```

### Configuration Structure
```python
@dataclass
class Config:
    grid_width: int = 20
    grid_height: int = 20
    cell_size: int = 30
    game_speed: float = 0.2
    ai_model_name: str = "microsoft/DialoGPT-medium"
    huggingface_token: str = ""  # Optional for private models
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Core Game Mechanics Properties

**Property 1: Direction change consistency**
*For any* valid arrow key input during gameplay, the snake should change to the corresponding direction and continue moving in that direction until another input is received
**Validates: Requirements 1.2**

**Property 2: Food consumption growth**
*For any* snake position and food location, when the snake head reaches the food position, the snake length should increase by exactly one segment and new food should appear at an empty grid location
**Validates: Requirements 1.3**

**Property 3: Collision detection reliability**
*For any* game state where the snake head position equals a wall boundary or any snake body segment position, the game should transition to game over state
**Validates: Requirements 1.4**

**Property 4: Automatic movement timing**
*For any* game state during active gameplay, the snake position should update at regular intervals matching the configured move interval without requiring user input
**Validates: Requirements 1.5**

### Game Mode Properties

**Property 5: Manual mode isolation**
*For any* game state when manual mode is active, snake movement should respond only to player input without AI interference
**Validates: Requirements 2.2**

**Property 6: AI mode suggestion display**
*For any* game state when AI mode is active, AI suggestions should be displayed while still allowing player control to override AI recommendations
**Validates: Requirements 2.3**

**Property 7: Auto mode AI control**
*For any* game state when auto mode is active, snake movement should be controlled entirely by AI decisions without player input affecting movement
**Validates: Requirements 2.4**

**Property 8: Mode switching capability**
*For any* point during gameplay, the system should allow switching between Manual, AI, and Auto modes without losing game state
**Validates: Requirements 2.5**

### AI Engine Properties

**Property 9: Hugging Face model usage**
*For any* AI prediction request when AI mode is active, the system should use the configured Hugging Face model for move prediction
**Validates: Requirements 3.1**

**Property 10: Game state analysis**
*For any* game state, AI move decisions should be based on analysis of the current snake position, food location, and collision risks
**Validates: Requirements 3.3**

**Property 11: Confidence score provision**
*For any* AI move recommendation, the system should provide a confidence score indicating the AI's certainty about the suggested move
**Validates: Requirements 3.4**

### Configuration Properties

**Property 12: Model configuration**
*For any* valid Hugging Face model name in the configuration, the system should attempt to load and use that model for AI predictions
**Validates: Requirements 4.3**

**Property 13: Game parameter configuration**
*For any* valid game speed and grid size values in the configuration, the system should apply those settings to gameplay
**Validates: Requirements 4.4**

**Property 14: Invalid configuration handling**
*For any* invalid configuration values, the system should use safe default values and provide appropriate warnings to the user
**Validates: Requirements 4.5**

## Error Handling

### Game Logic Errors
- **Invalid Move Detection**: Prevents snake from reversing into itself or moving outside grid boundaries
- **Food Placement Failures**: Handles cases where no empty cells exist for food placement

### AI Engine Errors
- **Model Loading Failures**: Falls back to manual-only mode if Hugging Face models cannot be loaded
- **Prediction Failures**: Uses safe default moves if AI inference fails
- **Network Errors**: Handles model download failures gracefully

### Configuration Errors
- **Missing Config File**: Creates default configuration file if none exists
- **Invalid Values**: Uses safe defaults for invalid configuration parameters
- **Model Access Errors**: Provides clear error messages for authentication or model access issues

## Testing Strategy

### Unit Testing Approach
Unit tests verify specific functionality:
- Game initialization with correct starting conditions
- Mode switching between Manual, AI, and Auto
- Configuration loading and validation
- AI model loading and fallback behavior

### Property-Based Testing Approach
Property-based tests verify universal properties using **Hypothesis** for Python:
- Each property-based test runs a minimum of 100 iterations with randomly generated inputs
- Tests generate random game states, snake positions, and user inputs to verify correctness properties
- Each property-based test is tagged with comments referencing the specific correctness property from this design document
- Test tags use the format: **Feature: retro-snake-ai, Property {number}: {property_text}**

### Test Coverage Requirements
- All correctness properties must be implemented as property-based tests
- Critical game mechanics require both unit and property-based test coverage
- AI components require tests with mocked models for deterministic behavior
- Configuration handling requires tests for valid and invalid inputs