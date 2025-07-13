# GameConfig.py

# General scaling
SCALE_FACTOR = 0.85

# Screen and tile sizes
SCREEN_WIDTH = int(1000 * SCALE_FACTOR)
SCREEN_HEIGHT = int(900 * SCALE_FACTOR)
TILE_SIZE = int(50 * SCALE_FACTOR)

# Level/gameplay timing
LEVEL_TIME_SECONDS = 30  # seconds per level
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
CHASER_DELAY_MS = 20000  # 20 seconds before chaser appears 