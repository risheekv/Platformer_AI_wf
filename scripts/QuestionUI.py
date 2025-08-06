import pygame
import Config
import os
import sys
import random
import math
import pandas as pd
import threading
from llm_client import LLMClient
from dotenv import load_dotenv
load_dotenv('scripts/secrets.env')

# Add Button import
from Button import Button

# Import scale factor from config
import GameConfig

class QuestionUI:
    def __init__(self, screen, sheet_name=None):
        self.screen = screen  # This will now always be game_surface
        self.active = False
        self.current_question = None
        self.selected_option = None
        self.buttons = []
        self.font = pygame.font.SysFont('comicsansms', int(20 * GameConfig.SCALE_FACTOR))
        self.title_font = pygame.font.SysFont('comicsansms', int(28 * GameConfig.SCALE_FACTOR))
        self.game_paused = False
        self.question_answered = False
        self.correct_answer = None
        self.feedback_alpha = 0
        self.feedback_timer = 0
        self.overlay_alpha = 0
        self.question_box_alpha = 0
        self.question_box_scale = 0.92
        self.hover_index = -1
        self.animation_time = 0
        self.show_feedback = False
        self.feedback_message = ""
        self.current_level = ""  # Track current question level
        
        # Track asked questions
        self.asked_questions = set()
        self.available_questions = []
        
        # Enhanced color scheme
        self.colors = {
            'background': (0, 0, 0),
            'overlay': (0, 0, 0),
            'text': (255, 255, 255),
            'button': (45, 45, 45),
            'button_hover': (60, 60, 60),
            'correct': (46, 204, 113),  # Green
            'wrong': (231, 76, 60),     # Red
            'border': (100, 100, 100),
            'gradient_start': (41, 128, 185),  # Blue
            'gradient_end': (142, 68, 173),    # Purple
            'option_gradient_start': (52, 152, 219),  # Light Blue
            'option_gradient_end': (155, 89, 182),    # Light Purple
            'hover_gradient_start': (41, 128, 185),   # Dark Blue
            'hover_gradient_end': (142, 68, 173),     # Dark Purple
            'correct_gradient_start': (39, 174, 96),  # Light Green
            'correct_gradient_end': (46, 204, 113),   # Green
            'wrong_gradient_start': (192, 57, 43),    # Dark Red
            'wrong_gradient_end': (231, 76, 60)       # Light Red
        }
        
        # Create a semi-transparent overlay
        self.overlay = pygame.Surface((screen.get_width(), screen.get_height()))
        self.overlay.fill(self.colors['overlay'])
        
        # Create Ask AI button
        self.ask_ai_button = self.create_ask_ai_button()
        self.hint_button = self.create_hint_button()
        self.showing_hint_popup = False
        self.hint_clicked = False
        
        # Create option buttons
        self.create_buttons()
        
        # Questions list
        self.questions = self.load_questions_from_excel('scripts/questions.xlsx', sheet_name)
        
        # Initialize available questions
        self.reset_available_questions()
        
        self.llm_client = LLMClient()
        self.ai_answer = None
        self.ai_loading = False
        self.ai_error = None
        self.showing_ai_popup = False
        self.back_button = self.create_back_button()
        self.ask_ai_clicked = False
        self.option_rects = []  # Store dynamic option rects for click/hover
        self.show_ask_ai = False  # Only show Ask AI button for last 2 platforms
        self.question_timer = 0
        self.question_timer_max = GameConfig.QUESTION_TIMER_SECONDS
        self.question_timer_active = False
    
    def create_gradient_surface(self, width, height, start_color, end_color, angle=0):
        surface = pygame.Surface((width, height))
        for y in range(height):
            # Calculate gradient color
            ratio = y / height
            r = int(start_color[0] * (1 - ratio) + end_color[0] * ratio)
            g = int(start_color[1] * (1 - ratio) + end_color[1] * ratio)
            b = int(start_color[2] * (1 - ratio) + end_color[2] * ratio)
            pygame.draw.line(surface, (r, g, b), (0, y), (width, y))
        return surface
    
    def create_buttons(self):
        self.buttons = []
        
        # Button dimensions and spacing
        button_width = int(500 * GameConfig.SCALE_FACTOR)
        button_height = int(60 * GameConfig.SCALE_FACTOR)
        spacing = int(25 * GameConfig.SCALE_FACTOR)
        
        # Calculate starting position to center the buttons
        start_x = (self.screen.get_width() - button_width) // 2
        start_y = self.screen.get_height() // 2 - int(50 * GameConfig.SCALE_FACTOR)
        
        # Create buttons for each option
        for i in range(4):
            # Create button with gradient background
            button_img = pygame.Surface((button_width, button_height))
            gradient = self.create_gradient_surface(button_width, button_height,
                                                  self.colors['option_gradient_start'],
                                                  self.colors['option_gradient_end'])
            button_img.blit(gradient, (0, 0))
            # Add border
            pygame.draw.rect(button_img, self.colors['border'], button_img.get_rect(), 2)
            button = Button(start_x, start_y + (button_height + spacing) * i, button_img)
            self.buttons.append(button)
    
    def reset_available_questions(self):
        """Reset the available questions pool"""
        self.available_questions = list(range(len(self.questions)))
        random.shuffle(self.available_questions)

    def show_random_question(self, show_ask_ai=False, level_key=None):
        """Show a random question that hasn't been asked recently. show_ask_ai: only show Ask AI button if True. level_key: level string for per-level config."""
        self.active = True
        self.game_paused = True
        self.question_answered = False
        # Only use per-level config for Ask AI button
        if level_key is not None:
            self.show_ask_ai = show_ask_ai and GameConfig.SHOW_AI_BUTTON_LEVELS.get(level_key, False)
        else:
            self.show_ask_ai = False
        
        # If we've used all questions, reset the pool
        if not self.available_questions:
            self.reset_available_questions()
        
        # Get a random question from available questions
        question_index = self.available_questions.pop()
        self.current_question = self.questions[question_index]
        self.correct_answer = self.current_question["correct"]
        self.selected_option = None
        self.show_feedback = False
        self.feedback_message = ""
        
        # Add to asked questions
        self.asked_questions.add(question_index)
        
        self.overlay_alpha = 0
        self.question_box_alpha = 0
        self.question_box_scale = 0.92
        self.question_timer = self.question_timer_max * 60  # 60 FPS
        self.question_timer_active = True
    
    def handle_events(self, event, offset=(0, 0)):
        # Adjust event.pos for offset if it's a mouse event
        adj_event = event
        if hasattr(event, 'pos'):
            adj_pos = (event.pos[0] - offset[0], event.pos[1] - offset[1])
            # Create a new event with adjusted pos (pygame.event.Event is immutable, so create a new one)
            adj_event = pygame.event.Event(event.type, {**event.__dict__, 'pos': adj_pos})
        # If Ask AI modal is open, only handle Back button
        if self.showing_ai_popup and GameConfig.SHOW_AI_BUTTON:
            if adj_event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.rect.collidepoint(adj_event.pos):
                    self.showing_ai_popup = False
                    self.ai_answer = None
                    self.ai_loading = False
                    self.ai_error = None
                    return None
            return None
        if self.showing_hint_popup:
            if adj_event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.rect.collidepoint(adj_event.pos):
                    self.showing_hint_popup = False
                    self.hint_clicked = False
                    return None
            return None
        if not self.active or self.question_answered:
            return None

        # Handle mouse movement for hover effect
        if adj_event.type == pygame.MOUSEMOTION:
            self.hover_index = -1
            if hasattr(self, 'option_rects') and self.option_rects:
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(adj_event.pos):
                        self.hover_index = i
                        break

        # Handle mouse clicks
        if adj_event.type == pygame.MOUSEBUTTONDOWN:
            # Determine level for per-level config
            level_str = str(self.current_level).strip().lower()
            if level_str.startswith('level'):
                level_key = level_str.replace(' ', '_')
            else:
                level_key = f'level_{level_str}' if level_str else 'level_1'
            # Check if Hint button is available and clicked
            if (
                GameConfig.SHOW_HINT_BUTTON
                and GameConfig.SHOW_HINT_BUTTON_LEVELS.get(level_key, True)
                and self.current_question and self.current_question.get('explanation', '').strip()
            ):
                if self.hint_button.rect.collidepoint(adj_event.pos):
                    self.showing_hint_popup = True
                    self.hint_clicked = True
                    return None

            # Check if Ask AI button is available and clicked
            if (
                self.show_ask_ai
                and self.ask_ai_button.rect.collidepoint(adj_event.pos)
                and not self.ai_loading
            ):
                self.ai_loading = True
                self.ai_answer = None
                self.ai_error = None
                self.showing_ai_popup = True
                print("Ask AI button clicked, querying LLM...")
                def fetch_ai_answer():
                    try:
                        q = self.current_question["question"] + "\n\nAnswer in short about 2-3 lines."
                        answer = self.llm_client.ask(q)
                        if answer:
                            self.ai_answer = answer
                            self.ai_error = None
                        else:
                            self.ai_answer = None
                            self.ai_error = "AI could not answer the question."
                    except Exception as e:
                        self.ai_answer = None
                        self.ai_error = f"Error: {e}"
                    self.ai_loading = False
                threading.Thread(target=fetch_ai_answer, daemon=True).start()
                return None

            # Handle option button clicks
            if hasattr(self, 'option_rects') and self.option_rects:
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(adj_event.pos):
                        self.selected_option = i
                        self.question_answered = True
                        self.show_feedback = True
                        self.feedback_timer = 60  # 1 second delay at 60 FPS
                        self.feedback_alpha = 0
                        # Set feedback message immediately
                        if i == self.correct_answer:
                            self.feedback_message = "🎉 Correct! " + self.current_question["explanation"]
                            return (True, self.ask_ai_clicked)
                        else:
                            self.feedback_message = f"❌ Incorrect! The correct answer was: {self.current_question['options'][self.correct_answer]}"
                            return (False, self.ask_ai_clicked)

        # Handle keyboard navigation
        if adj_event.type == pygame.KEYDOWN:
            if adj_event.key == pygame.K_UP:
                self.hover_index = max(0, self.hover_index - 1)
            elif adj_event.key == pygame.K_DOWN:
                self.hover_index = min(3, self.hover_index + 1)
            elif adj_event.key == pygame.K_RETURN and self.hover_index != -1:
                self.selected_option = self.hover_index
                self.question_answered = True
                self.show_feedback = True
                self.feedback_timer = 60  # 1 second delay at 60 FPS
                self.feedback_alpha = 0
                # Set feedback message immediately
                if self.hover_index == self.correct_answer:
                    self.feedback_message = "🎉 Correct! " + self.current_question["explanation"]
                    return (True, self.ask_ai_clicked)
                else:
                    self.feedback_message = f"❌ Incorrect! The correct answer was: {self.current_question['options'][self.correct_answer]}"
                    return (False, self.ask_ai_clicked)

        return None
    
    def is_active(self):
        return self.active
    
    def is_game_paused(self):
        return self.game_paused
    
    def check_answer(self, selected_option):
        if self.current_question and not self.question_answered:
            self.selected_option = selected_option
            self.question_answered = True
            self.show_feedback = True
            self.feedback_timer = 60  # 1 second delay at 60 FPS
            if selected_option == self.current_question['correct']:
                self.feedback_message = "🎉 Correct! " + self.current_question["explanation"]
                return (True, self.ask_ai_clicked)
            else:
                self.feedback_message = f"❌ Incorrect! The correct answer was: {self.current_question['options'][self.correct_answer]}"
                return (False, self.ask_ai_clicked)
        return (False, self.ask_ai_clicked)
    
    def reset(self):
        # First unpause the game
        self.set_game_paused(False)
        # Then reset all other states
        self.active = False
        self.question_answered = False
        self.selected_option = None
        self.current_question = None
        self.correct_answer = None
        self.show_feedback = False
        self.feedback_message = ""
        self.feedback_alpha = 0
        self.feedback_timer = 0
        self.overlay_alpha = 0
        self.question_box_alpha = 0
        self.question_box_scale = 0.92
        self.hover_index = -1
        self.ask_ai_clicked = False
        self.current_level = ""  # Reset current level
        self.option_rects = []  # Reset option rects each frame
    
    def wrap_text(self, text, font, max_width):
        """Wrap text to fit within max_width"""
        words = text.split(' ')
        lines = []
        current_line = []
        
        for word in words:
            # Test if adding this word exceeds the width
            test_line = ' '.join(current_line + [word])
            test_width = font.size(test_line)[0]
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
            
        return lines

    def create_ask_ai_button(self):
        # Create a surface for the button
        button_width = int(120 * GameConfig.SCALE_FACTOR)
        button_height = int(40 * GameConfig.SCALE_FACTOR)
        button_surface = pygame.Surface((button_width, button_height))
        
        # Create gradient background
        gradient = self.create_gradient_surface(
            button_width, button_height,
            self.colors['gradient_start'],
            self.colors['gradient_end']
        )
        button_surface.blit(gradient, (0, 0))
        
        # Add border
        pygame.draw.rect(button_surface, self.colors['border'], button_surface.get_rect(), 2)
        
        # Add text
        text = self.font.render("Ask AI", True, self.colors['text'])
        text_rect = text.get_rect(center=(button_width//2, button_height//2))
        button_surface.blit(text, text_rect)
        
        # Create button and position it in top right corner
        button = Button(0, 0, button_surface)  # Initial position, will be updated in draw
        return button

    def create_hint_button(self):
        button_width = int(120 * GameConfig.SCALE_FACTOR)
        button_height = int(40 * GameConfig.SCALE_FACTOR)
        button_surface = pygame.Surface((button_width, button_height))
        gradient = self.create_gradient_surface(
            button_width, button_height,
            self.colors['gradient_start'],
            self.colors['gradient_end']
        )
        button_surface.blit(gradient, (0, 0))
        pygame.draw.rect(button_surface, self.colors['border'], button_surface.get_rect(), 2)
        text = self.font.render("Hint", True, self.colors['text'])
        text_rect = text.get_rect(center=(button_width//2, button_height//2))
        button_surface.blit(text, text_rect)
        button = Button(0, 0, button_surface)
        return button

    def create_back_button(self):
        button_width = int(100 * GameConfig.SCALE_FACTOR)
        button_height = int(40 * GameConfig.SCALE_FACTOR)
        button_surface = pygame.Surface((button_width, button_height))
        gradient = self.create_gradient_surface(
            button_width, button_height,
            self.colors['gradient_start'],
            self.colors['gradient_end']
        )
        button_surface.blit(gradient, (0, 0))
        pygame.draw.rect(button_surface, self.colors['border'], button_surface.get_rect(), 2)
        text = self.font.render("Back", True, self.colors['text'])
        text_rect = text.get_rect(center=(button_width//2, button_height//2))
        button_surface.blit(text, text_rect)
        button = Button(0, 0, button_surface)
        return button

    def load_ai_image(self):
        if self.current_question and self.current_question.get('image_path'):
            image_path = self.current_question['image_path']
            print(f"Attempting to load image from: {image_path}")
            if not os.path.exists(image_path):
                print(f"Error: Image file does not exist at {image_path}")
                return
            try:
                img = pygame.image.load(image_path)
                # Scale image to fit screen while maintaining aspect ratio
                screen_width = self.screen.get_width()
                screen_height = self.screen.get_height()
                img_width = img.get_width()
                img_height = img.get_height()
                scale = min(screen_width / img_width, screen_height / img_height) * 0.8
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                img = pygame.transform.scale(img, (new_width, new_height))
                # self.ai_image = img # This line was removed as per the edit hint
                # self.ai_image_rect = img.get_rect(center=(screen_width // 2, screen_height // 2)) # This line was removed as per the edit hint
                print(f"Successfully loaded image: {image_path}, size: {img.get_width()}x{img.get_height()}")
            except Exception as e:
                print(f"Error loading image: {self.current_question['image_path']}")
                print(f"Exception: {str(e)}")

    def update(self):
        # Call this once per frame from the main game loop
        if self.active and self.question_timer_active and not self.question_answered:
            if self.question_timer > 0:
                self.question_timer -= 1
            else:
                # Time's up, mark as wrong
                self.question_answered = True
                self.show_feedback = True
                self.selected_option = None
                self.feedback_message = f"⏰ Time's up! The correct answer was: {self.current_question['options'][self.correct_answer]}"
                self.feedback_timer = 60  # 1 second delay at 60 FPS
                self.feedback_alpha = 0
                self.question_timer_active = False

    def draw(self):
        if not self.active or self.current_question is None:
            return
            
        # Update animation time
        self.animation_time = (self.animation_time + 0.02) % (2 * math.pi)
        
        # Handle feedback timing
        if self.question_answered and self.show_feedback:
            if self.feedback_timer > 0:
                self.feedback_timer -= 1
                # Fade in during first half, fade out during second half
                if self.feedback_timer > 30:
                    self.feedback_alpha = min(255, self.feedback_alpha + 5)  # even slower fade
                else:
                    self.feedback_alpha = max(0, self.feedback_alpha - 5)
            else:
                self.reset()  # This will handle both unpausing and resetting
                return
        
        # Smoothly fade in the overlay (even slower)
        if self.overlay_alpha < 200:
            self.overlay_alpha = min(200, self.overlay_alpha + 4)
        self.overlay.set_alpha(self.overlay_alpha)
        self.screen.blit(self.overlay, (0, 0))
        
        # Smoothly fade and scale in the question box
        if self.overlay_alpha >= 180 and self.question_box_alpha < 255:
            self.question_box_alpha = min(255, self.question_box_alpha + 7)
            self.question_box_scale = min(1.0, self.question_box_scale + 0.01)
        elif self.overlay_alpha < 180:
            self.question_box_alpha = 0
            self.question_box_scale = 0.92
        
        # Draw Hint button if hint is available
        # Determine level for per-level config
        level_str = str(self.current_level).strip().lower()
        if level_str.startswith('level'):
            level_key = level_str.replace(' ', '_')
        else:
            level_key = f'level_{level_str}' if level_str else 'level_1'
        # Per-level and global config for Hint button
        hint_available = (
            GameConfig.SHOW_HINT_BUTTON
            and GameConfig.SHOW_HINT_BUTTON_LEVELS.get(level_key, True)
            and self.current_question.get('explanation', '').strip() != ''
        )
        ai_button_x = self.screen.get_width() - self.ask_ai_button.rect.width - int(20 * GameConfig.SCALE_FACTOR)
        ai_button_y = int(20 * GameConfig.SCALE_FACTOR)
        if hint_available:
            self.hint_button.rect.topleft = (
                ai_button_x - self.hint_button.rect.width - int(12 * GameConfig.SCALE_FACTOR),
                ai_button_y
            )
            self.hint_button.draw(self.screen)
        # Draw Ask AI button if enabled (global and per-level)
        ai_available = (
            self.show_ask_ai
        )
        if ai_available:
            self.ask_ai_button.rect.topleft = (ai_button_x, ai_button_y)
            self.ask_ai_button.draw(self.screen)
        
        # Draw question box with scale and shadow
        question_lines = self.wrap_text(self.current_question["question"], self.title_font, int(700 * GameConfig.SCALE_FACTOR))
        question_height = len(question_lines) * self.title_font.get_height() + int(40 * GameConfig.SCALE_FACTOR)
        question_box_width = int(700 * GameConfig.SCALE_FACTOR)
        question_box_x = (self.screen.get_width() - question_box_width) // 2
        question_box_y = self.screen.get_height() // 4 - question_height // 2

        # Scale for animation
        scale = self.question_box_scale
        scaled_width = int(question_box_width * scale)
        scaled_height = int(question_height * scale)
        scaled_x = question_box_x + (question_box_width - scaled_width) // 2
        scaled_y = question_box_y + (question_height - scaled_height) // 2

        # Draw drop shadow
        shadow_offset = int(18 * GameConfig.SCALE_FACTOR)
        shadow_surf = pygame.Surface((scaled_width, scaled_height), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, int(self.question_box_alpha * 0.25)))
        self.screen.blit(shadow_surf, (scaled_x + shadow_offset, scaled_y + shadow_offset))

        # Create animated gradient for question box
        question_gradient = self.create_gradient_surface(
            scaled_width, scaled_height,
            self.colors['gradient_start'],
            self.colors['gradient_end'],
            math.sin(self.animation_time) * 45
        )
        question_gradient.set_alpha(self.question_box_alpha)
        self.screen.blit(question_gradient, (scaled_x, scaled_y))

        # Calculate question alpha for text
        question_alpha = max(60, min(self.question_box_alpha, 255))

        # Draw wrapped question text
        for i, line in enumerate(question_lines):
            line_surface = self.title_font.render(line, True, self.colors['text'])
            line_surface.set_alpha(question_alpha)
            line_rect = line_surface.get_rect(center=(self.screen.get_width() // 2,
                                                    scaled_y + int(20 * GameConfig.SCALE_FACTOR * scale) + i * int(self.title_font.get_height() * scale)))
            self.screen.blit(line_surface, line_rect)
        
        # Draw options with color feedback
        button_width = int(600 * GameConfig.SCALE_FACTOR * scale)
        button_height = int(50 * GameConfig.SCALE_FACTOR * scale)
        spacing = int(20 * GameConfig.SCALE_FACTOR * scale)
        
        self.option_rects = []  # Reset option rects each frame
        for i, option in enumerate(self.current_question["options"]):
            # Wrap option text
            option_lines = self.wrap_text(option, self.font, button_width - int(40 * GameConfig.SCALE_FACTOR * scale))
            option_height = len(option_lines) * int(self.font.get_height() * scale) + int(20 * GameConfig.SCALE_FACTOR * scale)
            button_height = max(int(50 * GameConfig.SCALE_FACTOR * scale), option_height)
            
            # Calculate button position
            button_x = (self.screen.get_width() - button_width) // 2
            button_y = self.screen.get_height() // 2 - int(50 * GameConfig.SCALE_FACTOR * scale) + i * (button_height + spacing)
            
            # Determine button colors based on selection state
            if self.question_answered and self.show_feedback:
                if i == self.correct_answer:
                    start_color = self.colors['correct_gradient_start']
                    end_color = self.colors['correct_gradient_end']
                    border_color = self.colors['correct']
                elif i == self.selected_option:
                    start_color = self.colors['wrong_gradient_start']
                    end_color = self.colors['wrong_gradient_end']
                    border_color = self.colors['wrong']
                else:
                    start_color = self.colors['option_gradient_start']
                    end_color = self.colors['option_gradient_end']
                    border_color = self.colors['border']
            elif i == self.hover_index:
                start_color = self.colors['hover_gradient_start']
                end_color = self.colors['hover_gradient_end']
                border_color = (255, 255, 255)
            else:
                start_color = self.colors['option_gradient_start']
                end_color = self.colors['option_gradient_end']
                border_color = self.colors['border']
            
            # Create and draw button gradient
            button_gradient = self.create_gradient_surface(
                button_width, button_height,
                start_color, end_color,
                math.sin(self.animation_time) * 45
            )
            button_gradient.set_alpha(self.question_box_alpha)
            self.screen.blit(button_gradient, (button_x, button_y))
            # Store the actual rect for this option
            self.option_rects.append(pygame.Rect(button_x, button_y, button_width, button_height))

            # Center-align wrapped option text vertically and horizontally
            total_text_height = len(option_lines) * int(self.font.get_height() * scale)
            text_start_y = button_y + (button_height - total_text_height) // 2
            # Ensure option text is always visible (minimum alpha 60)
            option_alpha = max(60, min(self.question_box_alpha, 255))
            for j, line in enumerate(option_lines):
                line_surface = self.font.render(line, True, self.colors['text'])
                line_surface.set_alpha(option_alpha)
                line_rect = line_surface.get_rect(center=(self.screen.get_width() // 2,
                                                        text_start_y + j * int(self.font.get_height() * scale) + int(self.font.get_height() * scale) // 2))
                self.screen.blit(line_surface, line_rect)

        # Draw feedback message
        if self.question_answered and self.show_feedback and self.feedback_timer > 0:
            feedback_lines = self.wrap_text(self.feedback_message, self.font, int(600 * GameConfig.SCALE_FACTOR))
            feedback_height = len(feedback_lines) * self.font.get_height() + int(40 * GameConfig.SCALE_FACTOR)
            feedback_y = self.screen.get_height() // 2 + int(200 * GameConfig.SCALE_FACTOR)
            
            # Create feedback surface with alpha
            feedback_surface = pygame.Surface((int(600 * GameConfig.SCALE_FACTOR), feedback_height), pygame.SRCALPHA)
            feedback_surface.fill((0, 0, 0, int(self.feedback_alpha * 0.8)))
            
            # Draw feedback text
            for i, line in enumerate(feedback_lines):
                text = self.font.render(line, True, self.colors['text'])
                text.set_alpha(int(self.feedback_alpha))
                text_rect = text.get_rect(center=(int(300 * GameConfig.SCALE_FACTOR), int(20 * GameConfig.SCALE_FACTOR) + i * self.font.get_height()))
                feedback_surface.blit(text, text_rect)
            
            # Draw feedback box
            feedback_x = (self.screen.get_width() - int(600 * GameConfig.SCALE_FACTOR)) // 2
            self.screen.blit(feedback_surface, (feedback_x, feedback_y))

        # Draw question timer if active
        if self.active and self.question_timer_active and not self.question_answered:
            timer_font = pygame.font.SysFont('comicsansms', int(32 * GameConfig.SCALE_FACTOR))
            seconds_left = max(0, int(self.question_timer // 60))
            timer_text = timer_font.render(f"Time Left: {seconds_left}s", True, (255, 100, 100))
            timer_rect = timer_text.get_rect(center=(self.screen.get_width() // 2, scaled_y - int(40 * GameConfig.SCALE_FACTOR)))
            self.screen.blit(timer_text, timer_rect)

        # If Ask AI modal is open, draw modal overlay with two boxes and Back button
        if self.showing_ai_popup:
            # Dim the background
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            # Modal dimensions (much taller)
            modal_width = int(950 * GameConfig.SCALE_FACTOR)
            modal_height = int(720 * GameConfig.SCALE_FACTOR)
            modal_x = (self.screen.get_width() - modal_width) // 2
            modal_y = (self.screen.get_height() - modal_height) // 2
            # Modal background with rounded corners and drop shadow
            shadow = pygame.Surface((modal_width + 24, modal_height + 24), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=24)
            self.screen.blit(shadow, (modal_x - 12, modal_y - 12))
            modal_bg = self.create_gradient_surface(modal_width, modal_height, self.colors['gradient_start'], self.colors['gradient_end'])
            modal_bg_rounded = pygame.Surface((modal_width, modal_height), pygame.SRCALPHA)
            modal_bg_rounded.blit(modal_bg, (0, 0))
            pygame.draw.rect(modal_bg_rounded, (0, 0, 0, 0), (0, 0, modal_width, modal_height), border_radius=18)
            self.screen.blit(modal_bg_rounded, (modal_x, modal_y))
            pygame.draw.rect(self.screen, self.colors['border'], (modal_x, modal_y, modal_width, modal_height), 4, border_radius=18)
            # Question box
            q_box_height = int(modal_height * 0.22)
            q_box_y = modal_y + int(36 * GameConfig.SCALE_FACTOR)
            q_box = pygame.Rect(modal_x + int(44 * GameConfig.SCALE_FACTOR), q_box_y, modal_width - int(88 * GameConfig.SCALE_FACTOR), q_box_height)
            q_gradient = self.create_gradient_surface(q_box.width, q_box.height, self.colors['option_gradient_start'], self.colors['option_gradient_end'])
            q_box_surf = pygame.Surface((q_box.width, q_box.height), pygame.SRCALPHA)
            q_box_surf.blit(q_gradient, (0, 0))
            pygame.draw.rect(q_box_surf, self.colors['border'], q_box_surf.get_rect(), 2, border_radius=12)
            self.screen.blit(q_box_surf, (q_box.x, q_box.y))
            q_lines = self.wrap_text(self.current_question["question"], self.title_font, q_box.width - 40)
            for i, line in enumerate(q_lines):
                line_surface = self.title_font.render(line, True, self.colors['text'])
                line_rect = line_surface.get_rect(midtop=(q_box.centerx, q_box.y + 24 + i * self.title_font.get_height()))
                self.screen.blit(line_surface, line_rect)
            # AI response box (much taller)
            a_box_height = int(modal_height * 0.47)
            a_box_y = q_box_y + q_box_height + int(40 * GameConfig.SCALE_FACTOR)
            a_box = pygame.Rect(modal_x + int(44 * GameConfig.SCALE_FACTOR), a_box_y, modal_width - int(88 * GameConfig.SCALE_FACTOR), a_box_height)
            a_gradient = self.create_gradient_surface(a_box.width, a_box.height, self.colors['hover_gradient_start'], self.colors['hover_gradient_end'])
            a_box_surf = pygame.Surface((a_box.width, a_box.height), pygame.SRCALPHA)
            a_box_surf.blit(a_gradient, (0, 0))
            pygame.draw.rect(a_box_surf, self.colors['border'], a_box_surf.get_rect(), 2, border_radius=12)
            self.screen.blit(a_box_surf, (a_box.x, a_box.y))
            if self.ai_loading:
                a_lines = ["AI is thinking..."]
            elif self.ai_error:
                a_lines = [self.ai_error]
            elif self.ai_answer:
                a_lines = self.wrap_text(self.ai_answer, self.font, a_box.width - 40)
            else:
                a_lines = [""]
            for i, line in enumerate(a_lines):
                line_surface = self.font.render(line, True, self.colors['text'])
                line_rect = line_surface.get_rect(midtop=(a_box.centerx, a_box.y + 24 + i * self.font.get_height()))
                self.screen.blit(line_surface, line_rect)
            # Back button well below the answer box, with clear gap
            back_btn_y = a_box.y + a_box.height + int(36 * GameConfig.SCALE_FACTOR)
            self.back_button.rect.topleft = (modal_x + modal_width//2 - self.back_button.rect.width//2, back_btn_y)
            self.back_button.draw(self.screen)
            return

        # Draw Hint modal popup if showing
        if self.showing_hint_popup:
            overlay = pygame.Surface((self.screen.get_width(), self.screen.get_height()), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))
            # Modal dimensions
            modal_width = int(700 * GameConfig.SCALE_FACTOR)
            modal_height = int(300 * GameConfig.SCALE_FACTOR)
            modal_x = (self.screen.get_width() - modal_width) // 2
            modal_y = (self.screen.get_height() - modal_height) // 2
            # Modal background
            shadow = pygame.Surface((modal_width + 24, modal_height + 24), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 80), shadow.get_rect(), border_radius=24)
            self.screen.blit(shadow, (modal_x - 12, modal_y - 12))
            modal_bg = self.create_gradient_surface(modal_width, modal_height, self.colors['gradient_start'], self.colors['gradient_end'])
            modal_bg_rounded = pygame.Surface((modal_width, modal_height), pygame.SRCALPHA)
            modal_bg_rounded.blit(modal_bg, (0, 0))
            pygame.draw.rect(modal_bg_rounded, (0, 0, 0, 0), (0, 0, modal_width, modal_height), border_radius=18)
            self.screen.blit(modal_bg_rounded, (modal_x, modal_y))
            pygame.draw.rect(self.screen, self.colors['border'], (modal_x, modal_y, modal_width, modal_height), 4, border_radius=18)
            # Hint text
            hint_text = self.current_question.get('explanation', '').strip()
            hint_lines = self.wrap_text(hint_text, self.font, modal_width - 60)
            for i, line in enumerate(hint_lines):
                line_surface = self.font.render(line, True, self.colors['text'])
                line_rect = line_surface.get_rect(center=(self.screen.get_width() // 2, modal_y + 60 + i * self.font.get_height()))
                self.screen.blit(line_surface, line_rect)
            # Back button
            back_btn_y = modal_y + modal_height - self.back_button.rect.height - int(24 * GameConfig.SCALE_FACTOR)
            self.back_button.rect.topleft = (modal_x + modal_width//2 - self.back_button.rect.width//2, back_btn_y)
            self.back_button.draw(self.screen)
            return

    def set_game_paused(self, paused):
        self.game_paused = paused 

    def load_questions_from_excel(self, filename, sheet_name=None):
        if not os.path.exists(filename):
            print(f"Excel file {filename} not found. No questions loaded.")
            return []
        df = pd.read_excel(filename, sheet_name=sheet_name)
        questions = []
        for _, row in df.iterrows():
            # Parse correct answer index (e.g., 'Option 1' -> 0)
            correct_str = str(row.get('Correct Answer', '')).strip().lower()
            correct_idx = None
            for i in range(1, 5):
                if correct_str == f'option {i}':
                    correct_idx = i - 1
                    break
            if correct_idx is None:
                print(f"Warning: Could not parse correct answer for question: {row.get('Question', '')}")
                continue
            questions.append({
                "question": str(row.get('Question', '')),
                "options": [
                    str(row.get('Answer 1', '')),
                    str(row.get('Answer 2', '')),
                    str(row.get('Answer 3', '')),
                    str(row.get('Answer 4', ''))
                ],
                "correct": correct_idx,
                "explanation": str(row.get('Hint', '')),
                "complexity": str(row.get('Complexity', '')) if 'Complexity' in row else '',
                # Optionally add: "domain": row.get('Domain', '')
            })
        return questions

    def show_random_question_by_complexity(self, complexity, show_ask_ai=False):
        """Show a random question of the given complexity. If none, fallback to any question."""
        self.active = True
        self.game_paused = True
        self.question_answered = False
        # Only use per-level config for Ask AI button
        level_str = str(complexity).strip().lower()
        if level_str.startswith('level'):
            level_key = level_str.replace(' ', '_')
        else:
            level_key = f'level_{level_str}' if level_str else 'level_1'
        self.show_ask_ai = show_ask_ai and GameConfig.SHOW_AI_BUTTON_LEVELS.get(level_key, False)
        self.current_level = complexity  # Store the current level

        # Filter available questions by complexity and not already asked
        available = [i for i, q in enumerate(self.questions)
                     if q.get('complexity', '').strip().lower() == complexity.strip().lower() and i not in self.asked_questions]
        if not available:
            # Fallback: any not-asked question
            available = [i for i in range(len(self.questions)) if i not in self.asked_questions]
        if not available:
            # Fallback: reset all
            self.asked_questions = set()
            available = [i for i in range(len(self.questions))]
        question_index = random.choice(available)
        self.current_question = self.questions[question_index]
        self.correct_answer = self.current_question["correct"]
        self.selected_option = None
        self.show_feedback = False
        self.feedback_message = ""
        self.asked_questions.add(question_index)
        self.overlay_alpha = 0
        self.question_box_alpha = 0
        self.question_box_scale = 0.92
        self.question_timer = self.question_timer_max * 60  # 60 FPS
        self.question_timer_active = True 