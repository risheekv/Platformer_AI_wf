import os
import json
import re
import requests

# Get the absolute path to the project root directory
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Global scale factor for the game
SCALE_FACTOR = 0.85  # 85% of original size

# ------------ Colors ------------

Colors = {
	"black" :  (0,0,0),
	"white" :  (255,255,255),
	"red" :    (255,0,0),
	"blue" :   (0,0,255),
	"green" :  (0,128,0),
}

# ------------ Sprites ------------

Sprites = {
	"background" : os.path.join(PROJECT_ROOT, "sprites", "Background", "background.png"),
	"ground_1" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_1.png"),
	"ground_2" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_2.png"),
	"ground_3" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_3.png"),
	"ground_4" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_4.png"),
	"ground_5" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_5.png"),
	"ground_6" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_6.png"),
	"ground_7" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_7.png"),
	"ground_8" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_8.png"),
	"ground_9" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_9.png"),
	"ground_10" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_10.png"),
	"ground_11" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "ground_11.png"),
	"grass_1" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Grass", "grass_1.png"),
	"grass_2" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Grass", "grass_2.png"),
	"grass_3" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Grass", "grass_3.png"),
	"grass_4" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Grass", "grass_4.png"),
	"grass_5" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Grass", "grass_5.png"),
	"bush_1" : os.path.join(PROJECT_ROOT, "sprites", "Decor", "Bush", "bush_1.png"),
	"bush_2" : os.path.join(PROJECT_ROOT, "sprites", "Decor", "Bush", "bush_2.png"),
	"tree_1" : os.path.join(PROJECT_ROOT, "sprites", "Decor", "Tree", "tree.png"),
	"tree_2" : os.path.join(PROJECT_ROOT, "sprites", "Decor", "Tree", "tree_dead.png"),
	"rock_1" : os.path.join(PROJECT_ROOT, "sprites", "Decor", "Rock", "rock_1.png"),
	"rock_2" : os.path.join(PROJECT_ROOT, "sprites", "Decor", "Rock", "rock_2.png"),
	"lava" : os.path.join(PROJECT_ROOT, "sprites", "Tile", "Ground", "lava.png"),
	"sign" : os.path.join(PROJECT_ROOT, "sprites", "Items", "sign.png"),
	"bird" : os.path.join(PROJECT_ROOT, "sprites", "Player", "chaser.png"),
}

# ------------ Player Sprites ------------

Player = {
	"idle_1" : os.path.join(PROJECT_ROOT, "sprites", "Player", "idle_1.png"),
	"idle_2" : os.path.join(PROJECT_ROOT, "sprites", "Player", "idle_2.png"),
	"idle_3" : os.path.join(PROJECT_ROOT, "sprites", "Player", "idle_3.png"),
	"idle_4" : os.path.join(PROJECT_ROOT, "sprites", "Player", "idle_4.png"),
	"run_1" : os.path.join(PROJECT_ROOT, "sprites", "Player", "run_1.png"),
	"run_2" : os.path.join(PROJECT_ROOT, "sprites", "Player", "run_2.png"),
	"run_3" : os.path.join(PROJECT_ROOT, "sprites", "Player", "run_3.png"),
	"run_4" : os.path.join(PROJECT_ROOT, "sprites", "Player", "run_4.png"),
	"run_5" : os.path.join(PROJECT_ROOT, "sprites", "Player", "run_5.png"),
	"run_6" : os.path.join(PROJECT_ROOT, "sprites", "Player", "run_6.png"),
	"jump_1" : os.path.join(PROJECT_ROOT, "sprites", "Player", "jump_1.png"),
	"jump_2" : os.path.join(PROJECT_ROOT, "sprites", "Player", "jump_2.png"),
	"fall_1" : os.path.join(PROJECT_ROOT, "sprites", "Player", "fall_1.png"),
	"fall_2" : os.path.join(PROJECT_ROOT, "sprites", "Player", "fall_2.png"),
	"death_1" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_1.png"),
	"death_2" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_2.png"),
	"death_3" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_3.png"),
	"death_4" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_4.png"),
	"death_5" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_5.png"),
	"death_6" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_6.png"),
	"death_7" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_7.png"),
	"death_8" : os.path.join(PROJECT_ROOT, "sprites", "Player", "death_8.png"),
}

# ------------ UI Elements ------------

UI = {
	"play" : os.path.join(PROJECT_ROOT, "sprites", "UI", "play_button.png"),
	"quit" : os.path.join(PROJECT_ROOT, "sprites", "UI", "quit_button.png"),
	"continue" : os.path.join(PROJECT_ROOT, "sprites", "UI", "continue_button.png"),
	"resume" : os.path.join(PROJECT_ROOT, "sprites", "UI", "resume_button.png"),
}

# ------------ Sounds ------------

Sounds = {
	"theme" : os.path.join(PROJECT_ROOT, "sounds", "theme.mp3"),
	"jump" : os.path.join(PROJECT_ROOT, "sounds", "jump.wav"),
	"over" : os.path.join(PROJECT_ROOT, "sounds", "game_over.wav"),
	"complete" : os.path.join(PROJECT_ROOT, "sounds", "game_complete.wav"),
}

def load_api_config():
    api_txt_path = os.path.join(PROJECT_ROOT, 'scripts', 'API.txt')
    with open(api_txt_path, 'r') as f:
        # Remove possible trailing commas and parse as JSON-like
        content = f.read()
        # Fix for non-standard JSON: replace '"services" {' with '{"services": {' and single quotes
        content = content.replace('"services" {', '{"services": {')
        content = content.replace("'", '"')
        # Remove any trailing commas before closing braces
        content = re.sub(r',\s*}', '}', content)
        content = re.sub(r',\s*]', ']', content)
        config = json.loads(content)
    return config

def get_llm_api_config():
    # FAKE CONFIG FOR LOCAL TESTING
    return {
        'endpoint': 'https://example.com/fake-llm-endpoint',
        'api_key': 'FAKE_API_KEY',
        'client_id': 'FAKE_CLIENT_ID',
        'model': 'fake-model',
        'usecase_id': 'fake-usecase-id'
    }

def get_apigee_oauth_config():
    config = load_api_config()
    apigee = config['services']['apigee']
    oauth_url = apigee['oauth-url']
    consumer_key = apigee['consumer']['key']
    consumer_secret = apigee['consumer']['secret']
    return {
        'oauth_url': oauth_url,
        'consumer_key': consumer_key,
        'consumer_secret': consumer_secret
    }

# This function can be used to obtain a bearer token before calling the LLM API
def get_apigee_bearer_token():
    # FAKE TOKEN FOR LOCAL TESTING
    return 'FAKE_BEARER_TOKEN'
