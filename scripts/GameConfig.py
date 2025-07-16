# GameConfig.py

# General scaling
SCALE_FACTOR = 0.85

# Screen and tile sizes
SCREEN_WIDTH = int(1000 * SCALE_FACTOR)
SCREEN_HEIGHT = int(900 * SCALE_FACTOR)
TILE_SIZE = int(50 * SCALE_FACTOR)

# Level/gameplay timing
LEVEL_TIME_SECONDS = 60  # seconds per level
time_per_level = LEVEL_TIME_SECONDS
POINTS_THRESHOLD = 20    # points needed to progress

# Points for each level of hardness
POINTS = {
    "level_1": 3,
    "level_2": 5,
    "level_3": 8,
    "level_3_ai": 6,
    "fallback_ai": 3,
    "fallback": 5,
}

# Question timing
QUESTION_TIMER_SECONDS = 15  # seconds per question

# Chaser variables
CHASER_BASE_SPEED = 0.6 * SCALE_FACTOR
CHASER_DELAY_MS = 40000  # 20 seconds before chaser appears 

# Option to enable/disable the Ask AI button
SHOW_AI_BUTTON = True
# Option to enable/disable the Hint button
SHOW_HINT_BUTTON = True

# Per-level configuration for Ask AI and Hint button visibility
SHOW_AI_BUTTON_LEVELS = {
    'level_1': True,
    'level_2': False,
    'level_3': True,
}
SHOW_HINT_BUTTON_LEVELS = {
    'level_1': False,
    'level_2': True,
    'level_3': True,
}