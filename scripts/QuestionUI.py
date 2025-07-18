import pygame
import Config
import os
import sys
import random
import math

# Add Button import
from Button import Button

# Import scale factor from config
from Config import SCALE_FACTOR

class QuestionUI:
    def __init__(self, screen):
        self.screen = screen
        self.active = False
        self.current_question = None
        self.selected_option = None
        self.buttons = []
        self.font = pygame.font.SysFont('comicsansms', int(20 * SCALE_FACTOR))
        self.title_font = pygame.font.SysFont('comicsansms', int(28 * SCALE_FACTOR))
        self.game_paused = False
        self.question_answered = False
        self.correct_answer = None
        self.feedback_alpha = 0
        self.feedback_timer = 0
        self.overlay_alpha = 0
        self.hover_index = -1
        self.animation_time = 0
        self.show_feedback = False
        self.feedback_message = ""
        
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
        
        # Create option buttons
        self.create_buttons()
        
        # Questions list
        self.questions = [
            {
                "question": "Why might a large company lease machinery instead of buying it outright?",
                "options": ["To increase taxes", "To own it faster", "To reduce upfront costs and save cash", "To avoid training employees"],
                "correct": 2,
                "explanation": "Leasing machinery helps companies reduce upfront costs and conserve cash flow.",
                "image_path": "sprites/questions/lease_machinery.png"
            },
            {
                "question": "What is one major benefit of leasing equipment instead of buying it?",
                "options": ["You can return it after each use", "Lower maintenance fees", "No need for insurance", "Use now, pay over time"],
                "correct": 3,
                "explanation": "Leasing allows companies to use equipment immediately while spreading the cost over time.",
                "image_path": "sprites/questions/leasing_benefit.png"
            },
            {
                "question": "Leasing equipment is often preferred by businesses because:",
                "options": ["It comes with free upgrades", "It requires no legal contracts", "It frees up money for other investments", "It removes the need for employees"],
                "correct": 2,
                "explanation": "Leasing frees up capital that can be used for other business investments.",
                "image_path": "sprites/questions/leasing_preference.png"
            },
            {
                "question": "What does a company usually offer as security when taking a loan backed by assets?",
                "options": ["Its future ideas", "Inventory or unpaid customer invoices", "Social media followers", "Office snacks"],
                "correct": 1,
                "explanation": "Companies typically use inventory or accounts receivable as security for asset-backed loans.",
                "image_path": "sprites/questions/asset_security.png"
            },
            {
                "question": "Why would a business use a loan backed by its assets?",
                "options": ["To buy shares in other companies", "To get quick access to money without selling ownership", "To shut down operations", "To pay employee bonuses only"],
                "correct": 1,
                "explanation": "Asset-backed loans provide quick access to capital without giving up company ownership.",
                "image_path": "sprites/questions/asset_loan.png"
            },
            {
                "question": "What kind of assets can help a company get a business loan?",
                "options": ["Office pets", "Furniture only", "Equipment, inventory, or customer payments due", "Company name"],
                "correct": 2,
                "explanation": "Tangible assets like equipment, inventory, and accounts receivable can be used as collateral.",
                "image_path": "sprites/questions/business_assets.png"
            },
            {
                "question": "Why would a company choose a loan secured by assets instead of a regular loan?",
                "options": ["Easier to qualify if the company owns valuable stuff", "It always comes with free gadgets", "It doesn't need to be repaid", "It avoids any paperwork"],
                "correct": 0,
                "explanation": "Asset-secured loans are often easier to qualify for if the company has valuable assets.",
                "image_path": "sprites/questions/asset_secured_loan.png"
            },
            
        ]
        
        # Initialize available questions
        self.reset_available_questions()
        
        self.showing_ai_image = False
        self.ai_image = None
        self.ai_image_rect = None
        self.back_button = self.create_back_button()
        self.ask_ai_clicked = False
    
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
        button_width = int(500 * SCALE_FACTOR)
        button_height = int(60 * SCALE_FACTOR)
        spacing = int(25 * SCALE_FACTOR)
        
        # Calculate starting position to center the buttons
        start_x = (self.screen.get_width() - button_width) // 2
        start_y = self.screen.get_height() // 2 - int(50 * SCALE_FACTOR)
        
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

    def show_random_question(self):
        """Show a random question that hasn't been asked recently"""
        self.active = True
        self.game_paused = True
        self.question_answered = False
        
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
    
    def handle_events(self, event):
        if self.showing_ai_image:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.back_button.rect.collidepoint(event.pos):
                    self.showing_ai_image = False
                    print("Back button clicked, returning to question view.")
                    return None
            return None
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

        # Handle mouse clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if Ask AI button was clicked
            if self.ask_ai_button.rect.collidepoint(event.pos) and not self.ask_ai_clicked:
                self.showing_ai_image = True
                self.load_ai_image()
                self.ask_ai_clicked = True
                print("Ask AI button clicked, showing image view.")
                return None

            # Handle option button clicks
            for i, button in enumerate(self.buttons):
                if button.rect.collidepoint(event.pos):
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
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.hover_index = max(0, self.hover_index - 1)
            elif event.key == pygame.K_DOWN:
                self.hover_index = min(3, self.hover_index + 1)
            elif event.key == pygame.K_RETURN and self.hover_index != -1:
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
        self.hover_index = -1
        self.ask_ai_clicked = False
    
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
        button_width = int(120 * SCALE_FACTOR)
        button_height = int(40 * SCALE_FACTOR)
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

    def create_back_button(self):
        button_width = int(100 * SCALE_FACTOR)
        button_height = int(40 * SCALE_FACTOR)
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
                self.ai_image = img
                self.ai_image_rect = img.get_rect(center=(screen_width // 2, screen_height // 2))
                print(f"Successfully loaded image: {image_path}, size: {img.get_width()}x{img.get_height()}")
            except Exception as e:
                print(f"Error loading image: {self.current_question['image_path']}")
                print(f"Exception: {str(e)}")

    def draw(self):
        if self.showing_ai_image:
            # Draw overlay
            if self.overlay_alpha < 200:
                self.overlay_alpha = min(200, self.overlay_alpha + 40)
            self.overlay.set_alpha(self.overlay_alpha)
            self.screen.blit(self.overlay, (0, 0))
            # Determine image size and position
            if self.ai_image and self.ai_image_rect:
                img_w, img_h = self.ai_image_rect.width, self.ai_image_rect.height
            else:
                img_w, img_h = max(int(self.screen.get_width() * 0.7), int(500 * SCALE_FACTOR)), max(int(self.screen.get_height() * 0.7), int(375 * SCALE_FACTOR))
            img_x = (self.screen.get_width() - img_w) // 2
            img_y = (self.screen.get_height() - img_h) // 2
            rect = pygame.Rect(img_x, img_y, img_w, img_h)
            pygame.draw.rect(self.screen, self.colors['border'], rect, 6)
            if self.ai_image:
                self.screen.blit(self.ai_image, (img_x, img_y))
            else:
                # Draw placeholder if image missing
                placeholder = self.font.render("No Image Available", True, (200, 50, 50))
                ph_rect = placeholder.get_rect(center=(self.screen.get_width()//2, self.screen.get_height()//2))
                self.screen.blit(placeholder, ph_rect)
            # Draw Back button below image
            self.back_button.rect.topleft = (img_x + img_w//2 - self.back_button.rect.width//2, img_y + img_h + int(30 * SCALE_FACTOR))
            self.back_button.draw(self.screen)
            return
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
                    self.feedback_alpha = min(255, self.feedback_alpha + 17)
                else:
                    self.feedback_alpha = max(0, self.feedback_alpha - 17)
            else:
                # Reset everything when feedback is complete
                self.reset()  # This will handle both unpausing and resetting
                return
        
        # Smoothly fade in the overlay
        if self.overlay_alpha < 200:
            self.overlay_alpha = min(200, self.overlay_alpha + 40)
        self.overlay.set_alpha(self.overlay_alpha)
        self.screen.blit(self.overlay, (0, 0))
        
        # Position Ask AI button in top right corner of game window
        self.ask_ai_button.rect.topleft = (
            self.screen.get_width() - self.ask_ai_button.rect.width - int(20 * SCALE_FACTOR),
            int(20 * SCALE_FACTOR)
        )
        self.ask_ai_button.draw(self.screen)
        
        # Draw question box
        question_lines = self.wrap_text(self.current_question["question"], self.title_font, int(700 * SCALE_FACTOR))
        question_height = len(question_lines) * self.title_font.get_height() + int(40 * SCALE_FACTOR)
        
        question_box_width = int(700 * SCALE_FACTOR)
        question_box_x = (self.screen.get_width() - question_box_width) // 2
        question_box_y = self.screen.get_height() // 4 - question_height // 2
        
        # Create animated gradient for question box
        question_gradient = self.create_gradient_surface(
            question_box_width, question_height,
            self.colors['gradient_start'],
            self.colors['gradient_end'],
            math.sin(self.animation_time) * 45
        )
        self.screen.blit(question_gradient, (question_box_x, question_box_y))
        pygame.draw.rect(self.screen, self.colors['border'], 
                        (question_box_x, question_box_y, question_box_width, question_height), 2)
        
        # Draw wrapped question text
        question_alpha = min(255, self.overlay_alpha * 2)
        for i, line in enumerate(question_lines):
            line_surface = self.title_font.render(line, True, self.colors['text'])
            line_surface.set_alpha(question_alpha)
            line_rect = line_surface.get_rect(center=(self.screen.get_width() // 2,
                                                    question_box_y + int(20 * SCALE_FACTOR) + i * self.title_font.get_height()))
            self.screen.blit(line_surface, line_rect)
        
        # Draw options with color feedback
        button_width = int(600 * SCALE_FACTOR)
        button_height = int(50 * SCALE_FACTOR)
        spacing = int(20 * SCALE_FACTOR)
        
        for i, option in enumerate(self.current_question["options"]):
            # Wrap option text
            option_lines = self.wrap_text(option, self.font, button_width - int(40 * SCALE_FACTOR))
            option_height = len(option_lines) * self.font.get_height() + int(20 * SCALE_FACTOR)
            button_height = max(int(50 * SCALE_FACTOR), option_height)
            
            # Calculate button position
            button_x = (self.screen.get_width() - button_width) // 2
            button_y = self.screen.get_height() // 2 - int(50 * SCALE_FACTOR) + i * (button_height + spacing)
            
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
            self.screen.blit(button_gradient, (button_x, button_y))
            pygame.draw.rect(self.screen, border_color, 
                           (button_x, button_y, button_width, button_height), 2)
            
            # Draw wrapped option text
            for j, line in enumerate(option_lines):
                line_surface = self.font.render(line, True, self.colors['text'])
                line_surface.set_alpha(question_alpha)
                line_rect = line_surface.get_rect(center=(self.screen.get_width() // 2,
                                                        button_y + int(10 * SCALE_FACTOR) + j * self.font.get_height()))
                self.screen.blit(line_surface, line_rect)
        
        # Draw feedback message
        if self.question_answered and self.show_feedback and self.feedback_timer > 0:
            feedback_lines = self.wrap_text(self.feedback_message, self.font, int(600 * SCALE_FACTOR))
            feedback_height = len(feedback_lines) * self.font.get_height() + int(40 * SCALE_FACTOR)
            feedback_y = self.screen.get_height() // 2 + int(200 * SCALE_FACTOR)
            
            # Create feedback surface with alpha
            feedback_surface = pygame.Surface((int(600 * SCALE_FACTOR), feedback_height), pygame.SRCALPHA)
            feedback_surface.fill((0, 0, 0, int(self.feedback_alpha * 0.8)))
            
            # Draw feedback text
            for i, line in enumerate(feedback_lines):
                text = self.font.render(line, True, self.colors['text'])
                text.set_alpha(int(self.feedback_alpha))
                text_rect = text.get_rect(center=(int(300 * SCALE_FACTOR), int(20 * SCALE_FACTOR) + i * self.font.get_height()))
                feedback_surface.blit(text, text_rect)
            
            # Draw feedback box
            feedback_x = (self.screen.get_width() - int(600 * SCALE_FACTOR)) // 2
            self.screen.blit(feedback_surface, (feedback_x, feedback_y))

    def set_game_paused(self, paused):
        self.game_paused = paused 