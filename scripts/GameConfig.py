# GameConfig.py

# General scaling
SCALE_FACTOR = 1.10

# Jump physics scaling - mathematical function derived from empirical data
# Data points: (0.85, 1.0) and (1.10, 0.08)
# Function: root_value = -3.68 * SCALE_FACTOR + 4.128
ORIGINAL_SCALE = 0.85  # The scale where jump was perfectly tuned
ROOT_VALUE = -3.68 * SCALE_FACTOR + 4.128  # Linear function through data points
JUMP_SCALE_FACTOR = (SCALE_FACTOR / ORIGINAL_SCALE) ** ROOT_VALUE  # Dynamic scaling

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

# ------------ Configurable Domain Settings ------------

# Domain configuration with switches (up to 10 domains)
# Each domain has: name, sheet_name, enabled status
DOMAIN_CONFIG = {
    "domain_1": {
        "name": "Equipment Finance",
        "sheet_name": "Equipment Finance",
        "enabled": True,
        "color_start": (41, 128, 185),   # Blue
        "color_end": (142, 68, 173)      # Purple
    },
    "domain_2": {
        "name": "Lending",
        "sheet_name": "Lending", 
        "enabled": True,
        "color_start": (46, 204, 113),   # Green
        "color_end": (39, 174, 96)       # Dark Green
    },
    "domain_3": {
        "name": "Trade Finance",
        "sheet_name": "Trade Finance",
        "enabled": True,
        "color_start": (231, 76, 60),    # Red
        "color_end": (192, 57, 43)       # Dark Red
    },
    "domain_4": {
        "name": "Leasing",
        "sheet_name": "Leasing",
        "enabled": True,
        "color_start": (155, 89, 182),   # Purple
        "color_end": (142, 68, 173)      # Dark Purple
    },
    "domain_5": {
        "name": "Asset Management",
        "sheet_name": "Asset Management",
        "enabled": False,  # Disabled by default
        "color_start": (241, 196, 15),   # Yellow
        "color_end": (243, 156, 18)      # Orange
    },
    "domain_6": {
        "name": "Risk Management",
        "sheet_name": "Risk Management", 
        "enabled": False,  # Disabled by default
        "color_start": (52, 73, 94),     # Dark Blue
        "color_end": (44, 62, 80)        # Darker Blue
    },
    "domain_7": {
        "name": "Investment Banking",
        "sheet_name": "Investment Banking",
        "enabled": False,  # Disabled by default
        "color_start": (26, 188, 156),   # Teal
        "color_end": (22, 160, 133)      # Dark Teal
    },
    "domain_8": {
        "name": "Corporate Finance",
        "sheet_name": "Corporate Finance",
        "enabled": True,  # Disabled by default
        "color_start": (230, 126, 34),   # Orange
        "color_end": (211, 84, 0)        # Dark Orange
    },
    "domain_9": {
        "name": "Retail Banking",
        "sheet_name": "Retail Banking",
        "enabled": False,  # Disabled by default
        "color_start": (149, 165, 166),  # Gray
        "color_end": (127, 140, 141)     # Dark Gray
    },
    "domain_10": {
        "name": "Digital Banking",
        "sheet_name": "Digital Banking",
        "enabled": False,  # Disabled by default
        "color_start": (52, 152, 219),   # Light Blue
        "color_end": (41, 128, 185)      # Blue
    }
}

# Function to get enabled domains for the UI
def get_enabled_domains():
    """Returns a dictionary of enabled domains for the domain selection screen"""
    enabled_domains = {}
    for domain_key, domain_config in DOMAIN_CONFIG.items():
        if domain_config["enabled"]:
            enabled_domains[domain_config["name"]] = domain_config["sheet_name"]
    return enabled_domains

# Function to get domain colors
def get_domain_colors(domain_name):
    """Returns the color scheme for a specific domain"""
    for domain_config in DOMAIN_CONFIG.values():
        if domain_config["name"] == domain_name:
            return (domain_config["color_start"], domain_config["color_end"])
    # Default colors if domain not found
    return ((41, 128, 185), (142, 68, 173))

# Function to enable/disable a domain
def set_domain_enabled(domain_name, enabled):
    """Enable or disable a specific domain"""
    for domain_config in DOMAIN_CONFIG.values():
        if domain_config["name"] == domain_name:
            domain_config["enabled"] = enabled
            break

# Function to get all domain names (enabled and disabled)
def get_all_domain_names():
    """Returns list of all domain names"""
    return [config["name"] for config in DOMAIN_CONFIG.values()]

# Function to check if a domain is enabled
def is_domain_enabled(domain_name):
    """Check if a specific domain is enabled"""
    for domain_config in DOMAIN_CONFIG.values():
        if domain_config["name"] == domain_name:
            return domain_config["enabled"]
    return False