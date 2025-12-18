"""
Simple Snake Game with AI modes.
"""

import pygame
import json
import sys
import time
import logging
from enum import Enum
from typing import List, Tuple
from datetime import datetime
import torch

import re

# ---------------- LOGGING ---------------- #

def setup_logging():
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler('snake_game.log'),
            logging.StreamHandler(sys.stdout)
        ]
    )

setup_logging()
logger = logging.getLogger(__name__)

# ---------------- ENUMS ---------------- #

class Direction(Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


class GameMode(Enum):
    MANUAL = "MANUAL"
    AI = "AI"
    AUTO = "AUTO"

# ---------------- CONFIG ---------------- #

class Config:
    def __init__(self):
        logger.info("Initializing game configuration")
        self.grid_width = 20
        self.grid_height = 20
        self.cell_size = 30
        self.game_speed = 0.2
        self.ai_model_name = "mistralai/Mistral-7B"
        self.huggingface_token = ""
        self.load_config()

    def load_config(self):
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
            logger.info(f"Configuration loaded - AI Model: {self.ai_model_name}")

        except FileNotFoundError:
            logger.warning("Config file not found, using defaults")

# ---------------- SNAKE ---------------- #

class Snake:
    def __init__(self, grid_width: int, grid_height: int):
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.segments = [(grid_width // 2, grid_height // 2)]
        self.direction = Direction.RIGHT
        self.grow_next = False

    def move(self):
        x, y = self.segments[0]
        if self.direction == Direction.UP:
            new = (x, y - 1)
        elif self.direction == Direction.DOWN:
            new = (x, y + 1)
        elif self.direction == Direction.LEFT:
            new = (x - 1, y)
        else:
            new = (x + 1, y)

        self.segments.insert(0, new)
        if not self.grow_next:
            self.segments.pop()
        else:
            self.grow_next = False

    def change_direction(self, new_dir: Direction):
        opposite = {
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
            Direction.LEFT: Direction.RIGHT,
            Direction.RIGHT: Direction.LEFT
        }
        if new_dir != opposite[self.direction]:
            self.direction = new_dir

    def grow(self):
        self.grow_next = True

    def check_collision(self):
        x, y = self.segments[0]
        if x < 0 or y < 0 or x >= self.grid_width or y >= self.grid_height:
            return True
        if (x, y) in self.segments[1:]:
            return True
        return False

# ---------------- FOOD ---------------- #

class Food:
    def __init__(self, w: int, h: int):
        self.grid_width = w
        self.grid_height = h
        self.spawn()

    def spawn(self):
        import random
        self.position = (
            random.randint(0, self.grid_width - 1),
            random.randint(0, self.grid_height - 1)
        )

    def is_eaten(self, head: Tuple[int, int]):
        return self.position == head

# ---------------- AI ENGINE (UPDATED) ---------------- #

class AIEngine:
    def __init__(self, config: Config):
        logger.info("Initializing AI Engine")
        self.config = config
        self.model = None
        self.tokenizer = None
        self.use_hf_model = False
        self.load_model()

    def load_model(self):
        try:
            from transformers import AutoTokenizer, AutoModelForCausalLM , AutoModelForSeq2SeqLM

            self.tokenizer = AutoTokenizer.from_pretrained(self.config.ai_model_name, use_auth_token = self.config.huggingface_token)
            model_name_lower = self.config.ai_model_name.lower()

            # ✅ Select correct model type automatically
            if "t5" in model_name_lower:
                logger.info("Detected T5 / Flan-T5 model (Seq2Seq)")
                self.model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.config.ai_model_name
                )
            else:
                logger.info("Detected GPT-style model (Causal LM)")
                self.model = AutoModelForCausalLM.from_pretrained(
                    self.config.ai_model_name,
                    use_auth_token = self.config.huggingface_token,
                    # torch_dtype=torch.float16,
                    # device_map="auto"
                )
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

            self.use_hf_model = True
            logger.info(f"Successfully loaded Hugging Face model: {self.config.ai_model_name}")

        except Exception as e:
            logger.warning(f"Failed to load HF model: {e}")
            self.use_hf_model = False

    def predict_move(self, snake: Snake, food: Food) -> Direction:
        if self.use_hf_model:
            return self._predict_with_hf_model(snake, food)
        return self._predict_with_heuristic(snake, food)

    # 🔥 IMPROVED PROMPT + PARSING 🔥
    def _predict_with_hf_model(self, snake: Snake, food: Food) -> Direction:
        try:
            import torch

            hx, hy = snake.segments[0]
            fx, fy = food.position

            prompt = (
                f"Snake head is at ({hx},{hy}). "
                f"Food is at ({fx},{fy}). "
                f"Snake body segments: {snake.segments[1:5]}. "
                "Choose the next best for the snake to avoid collison. \n"
                "Valid moves are: UP, DOWN, LEFT, RIGHT. "
            )




            inputs = self.tokenizer.encode(prompt, return_tensors="pt")


            # with torch.no_grad():
            #     outputs = self.model.generate(
            #         inputs,
            #         max_length=inputs.shape[1] + 3,
            #         do_sample=False,
            #         pad_token_id=self.tokenizer.pad_token_id
            #     )

            outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + 3,  # current
                    do_sample=False,
                    pad_token_id=self.tokenizer.pad_token_id
                )
            response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)


            # 🔒 Normalize model output
            response = response.upper()
            response = re.sub(r"[^A-Z]", "", response)
            logger.info(f"Response from AI - {response}")
            # ✅ Strict validation
            # Check if any valid direction is present in the cleaned response
            double_check = 0
            for valid_dir in ["UP", "DOWN", "LEFT", "RIGHT"]:
                if valid_dir in response:
                    direction = Direction[valid_dir]
                    # Make sure the move is safe
                    if self._is_safe_move(snake, direction):
                        double_check+=1
                        
            if double_check == 1:
                return direction
            logger.warning(f"HF Model returned invalid or empty response -{response}-, falling back to heuristic")
            return self._predict_with_heuristic(snake, food)

        except Exception as e:
            logger.error(f"HF prediction error: {e}")
            return self._predict_with_heuristic(snake, food)

    def _predict_with_heuristic(self, snake: Snake, food: Food) -> Direction:
        hx, hy = snake.segments[0]
        fx, fy = food.position

        best_move = snake.direction
        best_dist = float("inf")

        for d in Direction:
            nx, ny = {
                Direction.UP: (hx, hy - 1),
                Direction.DOWN: (hx, hy + 1),
                Direction.LEFT: (hx - 1, hy),
                Direction.RIGHT: (hx + 1, hy)
            }[d]

            if nx < 0 or ny < 0 or nx >= snake.grid_width or ny >= snake.grid_height:
                continue
            if (nx, ny) in snake.segments:
                continue

            dist = abs(nx - fx) + abs(ny - fy)
            if dist < best_dist:
                best_dist = dist
                best_move = d
        logger.info(f"Return from Heuristic - {best_move}")
        return best_move

    def _is_safe_move(self, snake: Snake, d: Direction) -> bool:
        hx, hy = snake.segments[0]
        nx, ny = {
            Direction.UP: (hx, hy - 1),
            Direction.DOWN: (hx, hy + 1),
            Direction.LEFT: (hx - 1, hy),
            Direction.RIGHT: (hx + 1, hy)
        }[d]

        # check out-of-bounds
        if not (0 <= nx < snake.grid_width and 0 <= ny < snake.grid_height):
            return False

        # simulate snake move
        new_segments = [(nx, ny)] + snake.segments[:-1]  # tail moves forward
        if len(new_segments) != len(set(new_segments)):
            return False

        return True


    def get_confidence(self):
        return 0.9 if self.use_hf_model else 0.7

# ---------------- GAME (UNCHANGED) ---------------- #

class Game:
    def __init__(self):
        logger.info("Initializing Snake Game")
        self.config = Config()
        self.snake = Snake(self.config.grid_width, self.config.grid_height)
        self.food = Food(self.config.grid_width, self.config.grid_height)
        self.ai_engine = AIEngine(self.config)
        self.score = 0
        self.game_over = False
        self.mode = GameMode.MANUAL
        
        logger.info(f"Game initialized in {self.mode.value} mode")
        
        # Pygame setup
        pygame.init()
        self.window_width = self.config.grid_width * self.config.cell_size
        self.window_height = self.config.grid_height * self.config.cell_size + 100  # Extra space for UI
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Snake Game - AI Modes")
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        logger.info(f"Pygame initialized with window size {self.window_width}x{self.window_height}")
        
        # Colors
        self.colors = {
            'black': (0, 0, 0),
            'white': (255, 255, 255),
            'green': (0, 255, 0),
            'red': (255, 0, 0),
            'blue': (0, 0, 255),
            'yellow': (255, 255, 0)
        }
    
    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                
                elif event.key == pygame.K_r:
                    logger.info("Game restart requested")
                    self.restart()
                
                elif event.key == pygame.K_1:
                    old_mode = self.mode
                    self.mode = GameMode.MANUAL
                    logger.info(f"Game mode changed from {old_mode.value} to {self.mode.value}")
                
                elif event.key == pygame.K_2:
                    old_mode = self.mode
                    self.mode = GameMode.AI
                    logger.info(f"Game mode changed from {old_mode.value} to {self.mode.value}")
                
                elif event.key == pygame.K_3:
                    old_mode = self.mode
                    self.mode = GameMode.AUTO
                    logger.info(f"Game mode changed from {old_mode.value} to {self.mode.value}")
                
                # Manual controls (work in Manual mode only)
                elif self.mode == GameMode.MANUAL:
                    if event.key == pygame.K_UP:
                        self.snake.change_direction(Direction.UP)
                    elif event.key == pygame.K_DOWN:
                        self.snake.change_direction(Direction.DOWN)
                    elif event.key == pygame.K_LEFT:
                        self.snake.change_direction(Direction.LEFT)
                    elif event.key == pygame.K_RIGHT:
                        self.snake.change_direction(Direction.RIGHT)
        
        return True
    
    def update(self):
        if self.game_over:
            return
        
        # AI control in AI and AUTO modes
        if self.mode == GameMode.AI or self.mode == GameMode.AUTO:
            ai_direction = self.ai_engine.predict_move(self.snake, self.food)
            self.snake.change_direction(ai_direction)
        
        # Move snake
        self.snake.move()
        
        # Check collision
        if self.snake.check_collision():
            self.game_over = True
            logger.info(f"Game over! Final score: {self.score}, Snake length: {len(self.snake.segments)}")
            return
        
        # Check food consumption
        if self.food.is_eaten(self.snake.segments[0]):
            self.snake.grow()
            old_score = self.score
            self.score += 10
            logger.info(f"Food consumed! Score: {old_score} -> {self.score}, Snake length: {len(self.snake.segments)}")
            self.food.spawn()
            
            # Make sure food doesn't spawn on snake
            respawn_attempts = 0
            while self.food.position in self.snake.segments and respawn_attempts < 100:
                self.food.spawn()
                respawn_attempts += 1
            
            if respawn_attempts >= 100:
                logger.warning("Could not find empty space for food after 100 attempts")
    
    def render(self):
        self.screen.fill(self.colors['black'])
        
        # Draw grid
        for x in range(self.config.grid_width):
            for y in range(self.config.grid_height):
                rect = pygame.Rect(
                    x * self.config.cell_size,
                    y * self.config.cell_size,
                    self.config.cell_size,
                    self.config.cell_size
                )
                pygame.draw.rect(self.screen, self.colors['white'], rect, 1)
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake.segments):
            rect = pygame.Rect(
                x * self.config.cell_size,
                y * self.config.cell_size,
                self.config.cell_size,
                self.config.cell_size
            )
            color = self.colors['green'] if i == 0 else self.colors['blue']
            pygame.draw.rect(self.screen, color, rect)
        
        # Draw food
        food_x, food_y = self.food.position
        food_rect = pygame.Rect(
            food_x * self.config.cell_size,
            food_y * self.config.cell_size,
            self.config.cell_size,
            self.config.cell_size
        )
        pygame.draw.rect(self.screen, self.colors['red'], food_rect)
        
        # Draw AI indicator in AI modes
        if (self.mode == GameMode.AI or self.mode == GameMode.AUTO) and not self.game_over:
            head_x, head_y = self.snake.segments[0]
            
            # Draw a glowing effect around the snake head to show AI control
            glow_rect = pygame.Rect(
                head_x * self.config.cell_size - 2,
                head_y * self.config.cell_size - 2,
                self.config.cell_size + 4,
                self.config.cell_size + 4
            )
            pygame.draw.rect(self.screen, self.colors['yellow'], glow_rect, 3)
        
        # Draw UI
        ui_y = self.config.grid_height * self.config.cell_size + 10
        
        score_text = self.font.render(f"Score: {self.score}", True, self.colors['white'])
        self.screen.blit(score_text, (10, ui_y))
        
        mode_text = self.font.render(f"Mode: {self.mode.value}", True, self.colors['white'])
        self.screen.blit(mode_text, (200, ui_y))
        
        if self.mode == GameMode.AI or self.mode == GameMode.AUTO:
            confidence = self.ai_engine.get_confidence()
            ai_type = "HF Model" if self.ai_engine.use_hf_model else "Heuristic"
            conf_text = self.small_font.render(f"AI: {ai_type} (Conf: {confidence:.1f})", True, self.colors['yellow'])
            self.screen.blit(conf_text, (400, ui_y))
        
        # Controls
        controls_y = ui_y + 40
        controls = [
            "Controls: Arrow keys (Manual only), 1=Manual, 2=AI, 3=Auto, R=Restart, ESC=Quit"
        ]
        
        for i, control in enumerate(controls):
            control_text = self.small_font.render(control, True, self.colors['white'])
            self.screen.blit(control_text, (10, controls_y + i * 20))
        
        if self.game_over:
            game_over_text = self.font.render("GAME OVER - Press R to restart", True, self.colors['red'])
            text_rect = game_over_text.get_rect(center=(self.window_width // 2, self.window_height // 2))
            self.screen.blit(game_over_text, text_rect)
        
        pygame.display.flip()
    
    def restart(self):
        logger.info("Restarting game")
        self.snake = Snake(self.config.grid_width, self.config.grid_height)
        self.food = Food(self.config.grid_width, self.config.grid_height)
        self.score = 0
        self.game_over = False
        logger.info(f"Game restarted in {self.mode.value} mode")
    
    def run(self):
        logger.info("Starting game loop")
        clock = pygame.time.Clock()
        last_move_time = time.time()
        
        logger.info("Snake Game with AI Modes")
        logger.info("Controls:")
        logger.info("  1 = Manual mode (you control with arrow keys)")
        logger.info("  2 = AI mode (AI controls using Hugging Face model)")
        logger.info("  3 = Auto mode (AI controls with heuristic)")
        logger.info("  Arrow keys = Move (Manual mode only)")
        logger.info("  R = Restart")
        logger.info("  ESC = Quit")
        
        running = True
        frame_count = 0
        while running:
            running = self.handle_input()
            
            # Update game at specified speed
            current_time = time.time()
            if current_time - last_move_time >= self.config.game_speed:
                self.update()
                last_move_time = current_time
            
            self.render()
            clock.tick(60)  # 60 FPS for smooth rendering
            
            frame_count += 1
            if frame_count % 3600 == 0:  # Log every minute at 60 FPS
                logger.debug(f"Game running - Frame: {frame_count}, Score: {self.score}, Mode: {self.mode.value}")
        
        logger.info("Game loop ended")
        pygame.quit()


def main():
    logger.info("=== Snake Game Starting ===")
    try:
        game = Game()
        game.run()
        logger.info("=== Snake Game Ended Successfully ===")
    except KeyboardInterrupt:
        logger.info("Game interrupted by user")
    except Exception as e:
        logger.error(f"Error running game: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()