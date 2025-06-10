import pygame
import Config
from Config import SCALE_FACTOR
from Button import Button
import openai
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

class ChatbotUI:
    def __init__(self, screen, api_key=None):
        self.screen = screen
        self.active = False
        self.current_question = None
        self.answer = ""
        self.search_text = ""
        self.search_active = False
        
        # Calculate dynamic font sizes based on screen size
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        self.font_size = int(min(screen_width, screen_height) * 0.02)  # 2% of screen size
        self.title_font_size = int(self.font_size * 1.4)  # 40% larger than regular font
        
        self.font = pygame.font.SysFont('comicsansms', self.font_size)
        self.title_font = pygame.font.SysFont('comicsansms', self.title_font_size)
        
        # Colors
        self.colors = {
            'background': (0, 0, 0),
            'overlay': (0, 0, 0),
            'text': (255, 255, 255),
            'button': (45, 45, 45),
            'button_hover': (60, 60, 60),
            'border': (100, 100, 100),
            'search_bg': (30, 30, 30, 180),  # More transparent background
            'search_text': (200, 200, 200),
            'search_cursor': (255, 255, 255),
            'gradient_start': (41, 128, 185),
            'gradient_end': (142, 68, 173)
        }
        
        # Create a semi-transparent overlay
        self.overlay = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))  # More transparent overlay
        
        # Calculate dynamic UI dimensions
        padding = int(screen_width * 0.05)  # 5% padding
        search_height = int(screen_height * 0.08)
        answer_height = int(screen_height * 0.6)  # 60% of screen height
        button_width = int(screen_width * 0.15)  # 15% of screen width
        button_height = int(screen_height * 0.06)  # 6% of screen height
        
        # Search bar properties
        self.search_rect = pygame.Rect(
            padding,
            int(screen_height * 0.2),  # 20% from top
            screen_width - (2 * padding),
            search_height
        )
        
        # Answer display area
        self.answer_rect = pygame.Rect(
            padding,
            self.search_rect.bottom + padding,
            screen_width - (2 * padding),
            answer_height
        )
        
        # Create buttons
        self.create_chatbot_button(button_width, button_height)
        self.create_back_button(button_width, button_height)
        
        # Cursor properties
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_position = 0
        
        # OpenAI configuration
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Please set the OPENAI_API_KEY environment variable in .env file.")
        
        try:
            self.client = openai.OpenAI(api_key=self.api_key)
            # Test the API key with a simple request and timeout
            self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "test"}],
                max_tokens=5,
                timeout=10  # 10 second timeout for initialization
            )
        except openai.AuthenticationError:
            raise ValueError("Invalid OpenAI API key. Please check your API key and try again.")
        except openai.APITimeoutError:
            raise ValueError("API connection timed out during initialization. Please check your internet connection.")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # Minimum seconds between requests
        self.is_processing = False  # Flag to prevent multiple simultaneous requests
        
        # Scroll properties for answer
        self.scroll_offset = 0
        self.max_scroll = 0
        self.line_height = int(self.font_size * 1.5)  # 1.5 times font size for line spacing

    def create_back_button(self, width, height):
        # Create button surface
        button_img = pygame.Surface((width, height))
        button_img.fill(self.colors['button'])
        pygame.draw.rect(button_img, self.colors['border'], button_img.get_rect(), 2)
        
        # Create text
        text = self.font.render("Back", True, self.colors['text'])
        text_rect = text.get_rect(center=(width//2, height//2))
        button_img.blit(text, text_rect)
        
        # Create button
        self.back_button = Button(
            int(self.screen.get_width() * 0.05),  # 5% from left
            int(self.screen.get_height() * 0.05),  # 5% from top
            button_img
        )

    def get_answer(self):
        if self.is_processing:
            return
            
        try:
            # Check rate limiting
            current_time = time.time()  # Use time.time() for more accurate timing
            if current_time - self.last_request_time < self.min_request_interval:
                self.answer = "Please wait a moment before asking another question."
                return
            
            self.is_processing = True
            self.answer = "Processing your question..."  # Show loading state
            
            # Make the API call
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful AI assistant that provides clear and concise answers."},
                    {"role": "user", "content": self.search_text}
                ],
                max_tokens=100,
                temperature=0.7,
                timeout=30  # 30 second timeout for requests
            )
            
            # Update rate limiting
            self.last_request_time = time.time()
            
            # Extract the answer
            self.answer = response.choices[0].message.content.strip()
            
        except openai.AuthenticationError:
            self.answer = "Error: Invalid API key. Please check your OpenAI API key configuration."
        except openai.RateLimitError:
            self.answer = "Error: Rate limit exceeded. Please try again in a few moments."
        except openai.APIError as e:
            self.answer = f"Error: API error occurred. Please try again. ({str(e)})"
        except openai.APITimeoutError:
            self.answer = "Error: Request timed out. Please check your internet connection and try again."
        except openai.APIConnectionError:
            self.answer = "Error: Could not connect to OpenAI. Please check your internet connection."
        except Exception as e:
            self.answer = f"Error: An unexpected error occurred. ({str(e)})"
        finally:
            self.is_processing = False

    def create_chatbot_button(self, width, height):
        # Create button surface
        button_img = pygame.Surface((width, height))
        button_img.fill(self.colors['button'])
        pygame.draw.rect(button_img, self.colors['border'], button_img.get_rect(), 2)
        
        # Create text
        text = self.font.render("Ask AI", True, self.colors['text'])
        text_rect = text.get_rect(center=(width//2, height//2))
        button_img.blit(text, text_rect)
        
        # Create button
        self.chatbot_button = Button(
            self.screen.get_width() - width - int(self.screen.get_width() * 0.05),
            int(self.screen.get_height() * 0.05),
            button_img
        )
        
        # Store button position
        self.button_pos = (self.screen.get_width() - width - int(self.screen.get_width() * 0.05),
                          int(self.screen.get_height() * 0.05))

    def is_active(self):
        return self.active

    def show(self, question):
        self.active = True
        self.current_question = question
        self.search_text = question  # Pre-fill with current question
        self.answer = ""
        self.search_active = True
        self.cursor_position = len(question)  # Set cursor to end of question

    def hide(self):
        self.active = False
        self.search_active = False
        self.search_text = ""
        self.answer = ""

    def handle_events(self, event):
        if not self.active:
            return None

        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if back button was clicked
            if self.back_button.rect.collidepoint(event.pos):
                self.hide()
                return None
                
            # Check if search bar was clicked
            if self.search_rect.collidepoint(event.pos):
                self.search_active = True
            else:
                self.search_active = False
                
            # Handle mouse wheel for scrolling
            if event.button == 4:  # Scroll up
                self.scroll_offset = max(0, self.scroll_offset - 1)
            elif event.button == 5:  # Scroll down
                self.scroll_offset = min(self.max_scroll, self.scroll_offset + 1)

        if event.type == pygame.KEYDOWN and self.search_active:
            if event.key == pygame.K_RETURN:
                # Send question to API
                self.get_answer()
            elif event.key == pygame.K_BACKSPACE:
                if self.cursor_position > 0:
                    self.search_text = self.search_text[:self.cursor_position-1] + self.search_text[self.cursor_position:]
                    self.cursor_position = max(0, self.cursor_position - 1)
            elif event.key == pygame.K_LEFT:
                self.cursor_position = max(0, self.cursor_position - 1)
            elif event.key == pygame.K_RIGHT:
                self.cursor_position = min(len(self.search_text), self.cursor_position + 1)
            elif event.key == pygame.K_ESCAPE:
                self.hide()
            else:
                # Add character at cursor position
                self.search_text = self.search_text[:self.cursor_position] + event.unicode + self.search_text[self.cursor_position:]
                self.cursor_position += 1

        return None

    def draw(self):
        if not self.active:
            return

        # Draw overlay
        self.screen.blit(self.overlay, (0, 0))

        # Draw search bar with transparency
        search_surface = pygame.Surface((self.search_rect.width, self.search_rect.height), pygame.SRCALPHA)
        search_surface.fill(self.colors['search_bg'])
        self.screen.blit(search_surface, self.search_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.search_rect, 2)
        
        # Draw search text
        text_surface = self.font.render(self.search_text, True, self.colors['search_text'])
        self.screen.blit(text_surface, (self.search_rect.x + 10, self.search_rect.y + 10))
        
        # Draw cursor if search is active
        if self.search_active and self.cursor_visible:
            cursor_x = self.search_rect.x + 10 + self.font.size(self.search_text[:self.cursor_position])[0]
            pygame.draw.line(
                self.screen,
                self.colors['search_cursor'],
                (cursor_x, self.search_rect.y + 10),
                (cursor_x, self.search_rect.y + self.search_rect.height - 10),
                2
            )
        
        # Draw answer area with transparency
        answer_surface = pygame.Surface((self.answer_rect.width, self.answer_rect.height), pygame.SRCALPHA)
        answer_surface.fill(self.colors['search_bg'])
        self.screen.blit(answer_surface, self.answer_rect)
        pygame.draw.rect(self.screen, self.colors['border'], self.answer_rect, 2)
        
        if self.answer:
            # Wrap and draw answer text
            words = self.answer.split()
            lines = []
            current_line = []
            max_width = self.answer_rect.width - 20  # 10px padding on each side
            
            for word in words:
                # Handle very long words by breaking them
                if self.font.size(word)[0] > max_width:
                    # Break long word into characters
                    chars = list(word)
                    current_word = ""
                    for char in chars:
                        test_word = current_word + char
                        if self.font.size(test_word)[0] < max_width:
                            current_word = test_word
                        else:
                            if current_word:
                                current_line.append(current_word)
                                lines.append(' '.join(current_line))
                                current_line = []
                            current_word = char
                    if current_word:
                        current_line.append(current_word)
                else:
                    test_line = ' '.join(current_line + [word])
                    if self.font.size(test_line)[0] < max_width:
                        current_line.append(word)
                    else:
                        lines.append(' '.join(current_line))
                        current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate maximum scroll
            total_height = len(lines) * self.line_height
            visible_height = self.answer_rect.height
            self.max_scroll = max(0, (total_height - visible_height) // self.line_height)
            
            # Draw visible lines
            visible_lines = lines[self.scroll_offset:self.scroll_offset + (visible_height // self.line_height) + 1]
            for i, line in enumerate(visible_lines):
                text = self.font.render(line, True, self.colors['text'])
                self.screen.blit(text, (
                    self.answer_rect.x + 10,
                    self.answer_rect.y + 10 + (i * self.line_height)
                ))
            
            # Draw scroll indicator if needed
            if self.max_scroll > 0:
                indicator_height = (visible_height / total_height) * visible_height
                indicator_y = self.answer_rect.y + (self.scroll_offset / self.max_scroll) * (visible_height - indicator_height)
                pygame.draw.rect(self.screen, self.colors['border'], (
                    self.answer_rect.right - 5,
                    indicator_y,
                    5,
                    indicator_height
                ))
        
        # Draw back button
        self.back_button.draw(self.screen)

    def update(self):
        # Update cursor blink
        self.cursor_timer += 1
        if self.cursor_timer >= 30:  # Blink every 30 frames
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0

    def draw_button(self):
        # Only draw button if not active
        if not self.active:
            return self.chatbot_button.draw(self.screen)
        return False 