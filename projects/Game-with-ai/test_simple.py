"""
Simple tests for the Snake game.
"""

import pytest
from retro_snake_ai.main import Snake, Food, Direction, Config


def test_snake_initialization():
    """Test that snake initializes correctly."""
    snake = Snake(20, 20)
    assert len(snake.segments) == 1
    assert snake.direction == Direction.RIGHT
    assert not snake.grow_next


def test_snake_movement():
    """Test basic snake movement."""
    snake = Snake(20, 20)
    initial_pos = snake.segments[0]
    snake.move()
    new_pos = snake.segments[0]
    
    # Snake should move right by default
    assert new_pos[0] == initial_pos[0] + 1
    assert new_pos[1] == initial_pos[1]


def test_snake_direction_change():
    """Test snake direction changes."""
    snake = Snake(20, 20)
    snake.change_direction(Direction.UP)
    assert snake.direction == Direction.UP
    
    # Should not allow reversing into self
    snake.change_direction(Direction.DOWN)
    assert snake.direction == Direction.UP  # Should remain UP


def test_snake_growth():
    """Test snake growth mechanism."""
    snake = Snake(20, 20)
    initial_length = len(snake.segments)
    
    snake.grow()
    snake.move()
    
    assert len(snake.segments) == initial_length + 1


def test_food_initialization():
    """Test food initialization."""
    food = Food(20, 20)
    x, y = food.position
    assert 0 <= x < 20
    assert 0 <= y < 20


def test_food_consumption():
    """Test food consumption detection."""
    food = Food(20, 20)
    food.position = (5, 5)
    
    assert food.is_eaten((5, 5))
    assert not food.is_eaten((4, 5))


def test_config_loading():
    """Test configuration loading."""
    config = Config()
    assert config.grid_width > 0
    assert config.grid_height > 0
    assert config.cell_size > 0
    assert config.game_speed > 0


if __name__ == "__main__":
    pytest.main([__file__])