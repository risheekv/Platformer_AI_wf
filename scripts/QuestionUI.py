import pygame
import Config
import os
import sys
import random
import math

# Add Button import
from Button import Button

class QuestionUI:
    def __init__(self, screen):
        self.screen = screen
        self.active = False
        self.current_question = None
        self.selected_option = None
        self.buttons = []
        self.font = pygame.font.SysFont('comicsansms', 24)
        self.title_font = pygame.font.SysFont('comicsansms', 36)
        self.game_paused = False
        self.question_answered = False
        self.correct_answer = None
        self.feedback_alpha = 0
        self.feedback_timer = 0
        self.overlay_alpha = 0
        self.hover_index = -1
        self.animation_time = 0
        self.selection_delay = 0
        self.show_feedback = False
        self.feedback_message = ""
        
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
        
        # Create option buttons
        self.create_buttons()
        
        # Questions list
        self.questions = [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct": 2,
                "explanation": "Paris is the capital city of France."
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "correct": 1,
                "explanation": "Mars is called the Red Planet due to its reddish appearance."
            },
            {
                "question": "What is the largest mammal in the world?",
                "options": ["African Elephant", "Blue Whale", "Giraffe", "Hippopotamus"],
                "correct": 1,
                "explanation": "The Blue Whale is the largest mammal, reaching lengths of up to 100 feet."
            }
        ]
    
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
        button_width = 500
        button_height = 60
        spacing = 25
        
        # Calculate starting position to center the buttons
        start_x = (self.screen.get_width() - button_width) // 2
        start_y = self.screen.get_height() // 2 - 50
        
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
            button = Button(start_x, start_y + (button_height + spacing) * i, button_img, 1)
            self.buttons.append(button)
    
    def show_random_question(self):
        self.active = True
        self.game_paused = True
        self.question_answered = False
        self.current_question = random.choice(self.questions)
        self.correct_answer = self.current_question["correct"]
        self.selected_option = None
        self.feedback_alpha = 0
        self.feedback_timer = 0
        self.overlay_alpha = 0
        self.hover_index = -1
        self.animation_time = 0
        self.selection_delay = 0
        self.show_feedback = False
        self.feedback_message = ""
    
    def handle_events(self, event):
        if not self.active or self.question_answered:
            return None

        # Handle mouse movement for hover effect
        if event.type == pygame.MOUSEMOTION:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.hover_index = i
                    break
            else:
                self.hover_index = -1

        # Handle keyboard navigation
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.hover_index = max(0, self.hover_index - 1)
            elif event.key == pygame.K_DOWN:
                self.hover_index = min(3, self.hover_index + 1)
            elif event.key == pygame.K_RETURN and self.hover_index != -1:
                self.selected_option = self.hover_index
                self.question_answered = True
                self.selection_delay = 60  # 1 second delay at 60 FPS
                # Set feedback message immediately
                if self.hover_index == self.correct_answer:
                    self.feedback_message = "🎉 Correct! " + self.current_question["explanation"]
                else:
                    self.feedback_message = f"❌ Incorrect! The correct answer was: {self.current_question['options'][self.correct_answer]}"
                return self.hover_index == self.correct_answer

        if event.type == pygame.MOUSEBUTTONDOWN:
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
                    self.selected_option = i
                    self.question_answered = True
                    self.selection_delay = 60  # 1 second delay at 60 FPS
                    # Set feedback message immediately
                    if i == self.correct_answer:
                        self.feedback_message = "🎉 Correct! " + self.current_question["explanation"]
                    else:
                        self.feedback_message = f"❌ Incorrect! The correct answer was: {self.current_question['options'][self.correct_answer]}"
                    return i == self.correct_answer
        return None
    
    def is_active(self):
        return self.active
    
    def is_game_paused(self):
        return self.game_paused
    
    def check_answer(self, selected_option):
        if selected_option is None:
            return False
        return selected_option == self.current_question["correct"]
    
    def reset(self):
        self.active = False
        self.game_paused = False
        self.question_answered = False
        self.selected_option = None
        self.current_question = None
        self.correct_answer = None
        self.feedback_alpha = 0
        self.feedback_timer = 0
        self.overlay_alpha = 0
        self.hover_index = -1
        self.animation_time = 0
        self.selection_delay = 0
        self.show_feedback = False
        self.feedback_message = ""
    
    def draw(self):
        if not self.active or self.current_question is None:
            return
            
        # Update animation time
        self.animation_time = (self.animation_time + 0.02) % (2 * math.pi)
        
        # Handle selection delay and feedback timing
        if self.question_answered:
            if self.selection_delay > 0:
                self.selection_delay -= 1
                if self.selection_delay == 0:
                    self.show_feedback = True
                    self.feedback_timer = 60  # Show feedback for 1 second
                    self.feedback_alpha = 0  # Reset feedback alpha for fade in
            elif self.show_feedback and self.feedback_timer > 0:
                self.feedback_timer -= 1
                if self.feedback_timer == 0:
                    # Only reset and unpause when feedback is complete
                    self.reset()
                    self.set_game_paused(False)
        
        # Smoothly fade in the overlay
        if self.overlay_alpha < 200:
            self.overlay_alpha = min(200, self.overlay_alpha + 40)
        self.overlay.set_alpha(self.overlay_alpha)
        self.screen.blit(self.overlay, (0, 0))
        
        # Draw question box with animated gradient
        question_box_width = 800
        question_box_height = 100
        question_box_x = (self.screen.get_width() - question_box_width) // 2
        question_box_y = self.screen.get_height() // 4 - 50
        
        # Create animated gradient for question box
        question_gradient = self.create_gradient_surface(
            question_box_width, question_box_height,
            self.colors['gradient_start'],
            self.colors['gradient_end'],
            math.sin(self.animation_time) * 45
        )
        self.screen.blit(question_gradient, (question_box_x, question_box_y))
        pygame.draw.rect(self.screen, self.colors['border'], 
                        (question_box_x, question_box_y, question_box_width, question_box_height), 2)
        
        # Draw question
        question_alpha = min(255, self.overlay_alpha * 2)
        question_text = self.title_font.render(self.current_question["question"], True, self.colors['text'])
        question_text.set_alpha(question_alpha)
        question_rect = question_text.get_rect(center=(self.screen.get_width() // 2, 
                                                     question_box_y + question_box_height // 2))
        self.screen.blit(question_text, question_rect)
        
        # Draw options with hover effects
        for i, option in enumerate(self.current_question["options"]):
            # Create button with animated gradient
            button_width = 500
            button_height = 60
            button_x = (self.screen.get_width() - button_width) // 2
            button_y = self.screen.get_height() // 2 - 50 + i * (button_height + 25)
            
            # Determine button gradient colors based on state
            if self.question_answered and self.show_feedback:
                if i == self.correct_answer:
                    # Always show correct answer in green
                    start_color = self.colors['correct_gradient_start']
                    end_color = self.colors['correct_gradient_end']
                elif i == self.selected_option:
                    # Show selected wrong answer in red
                    start_color = self.colors['wrong_gradient_start']
                    end_color = self.colors['wrong_gradient_end']
                else:
                    # Other options remain neutral
                    start_color = self.colors['option_gradient_start']
                    end_color = self.colors['option_gradient_end']
            elif i == self.hover_index:
                start_color = self.colors['hover_gradient_start']
                end_color = self.colors['hover_gradient_end']
            else:
                start_color = self.colors['option_gradient_start']
                end_color = self.colors['option_gradient_end']
            
            # Create and draw button gradient
            button_gradient = self.create_gradient_surface(
                button_width, button_height,
                start_color, end_color,
                math.sin(self.animation_time) * 45
            )
            self.screen.blit(button_gradient, (button_x, button_y))
            
            # Draw button border
            if self.question_answered and self.show_feedback:
                if i == self.correct_answer:
                    border_color = self.colors['correct']
                elif i == self.selected_option:
                    border_color = self.colors['wrong']
                else:
                    border_color = self.colors['border']
            else:
                border_color = (255, 255, 255) if i == self.hover_index else self.colors['border']
            
            pygame.draw.rect(self.screen, border_color, 
                           (button_x, button_y, button_width, button_height), 2)
            
            # Draw option text
            option_text = self.font.render(option, True, self.colors['text'])
            option_text.set_alpha(question_alpha)
            option_rect = option_text.get_rect(center=(self.screen.get_width() // 2, 
                                                     button_y + button_height // 2))
            self.screen.blit(option_text, option_rect)
        
        # Show feedback if question is answered and delay is complete
        if self.question_answered and self.show_feedback and self.feedback_timer > 0:
            # Calculate feedback alpha (fade in/out)
            if self.feedback_timer > 30:
                self.feedback_alpha = min(255, self.feedback_alpha + 17)
            else:
                self.feedback_alpha = max(0, self.feedback_alpha - 17)
            
            # Create feedback box with increased height for better text spacing
            feedback_box_width = 700
            feedback_box_height = 120
            feedback_box_x = (self.screen.get_width() - feedback_box_width) // 2
            feedback_box_y = self.screen.get_height() * 3 // 4 + 50  # Moved down to avoid overlap
            
            # Draw feedback background with gradient
            feedback_gradient = self.create_gradient_surface(
                feedback_box_width, feedback_box_height,
                self.colors['correct_gradient_start'] if self.selected_option == self.correct_answer 
                else self.colors['wrong_gradient_start'],
                self.colors['correct_gradient_end'] if self.selected_option == self.correct_answer 
                else self.colors['wrong_gradient_end'],
                math.sin(self.animation_time) * 45
            )
            feedback_gradient.set_alpha(self.feedback_alpha)
            self.screen.blit(feedback_gradient, (feedback_box_x, feedback_box_y))
            
            # Draw feedback border
            border_color = self.colors['correct'] if self.selected_option == self.correct_answer else self.colors['wrong']
            pygame.draw.rect(self.screen, border_color, 
                           (feedback_box_x, feedback_box_y, feedback_box_width, feedback_box_height), 2)
            
            # Split feedback message into two lines if needed
            if len(self.feedback_message) > 40:  # If message is long, split it
                parts = self.feedback_message.split("! ", 1)  # Split at first "! "
                if len(parts) > 1:
                    line1 = parts[0] + "!"
                    line2 = parts[1]
                else:
                    line1 = self.feedback_message[:40]
                    line2 = self.feedback_message[40:]
            else:
                line1 = self.feedback_message
                line2 = ""
            
            # Draw first line of feedback text
            feedback_text1 = self.font.render(line1, True, border_color)
            feedback_text1.set_alpha(self.feedback_alpha)
            feedback_rect1 = feedback_text1.get_rect(center=(self.screen.get_width() // 2, 
                                                           feedback_box_y + feedback_box_height // 3))
            self.screen.blit(feedback_text1, feedback_rect1)
            
            # Draw second line if it exists
            if line2:
                feedback_text2 = self.font.render(line2, True, border_color)
                feedback_text2.set_alpha(self.feedback_alpha)
                feedback_rect2 = feedback_text2.get_rect(center=(self.screen.get_width() // 2, 
                                                               feedback_box_y + feedback_box_height * 2 // 3))
                self.screen.blit(feedback_text2, feedback_rect2)

    def set_game_paused(self, paused):
        self.game_paused = paused 