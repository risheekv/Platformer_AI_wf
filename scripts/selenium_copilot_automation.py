import subprocess
import time
import pyautogui
import pyperclip
import platform
import sys
import os
import pygetwindow as gw

# CONFIGURATION
DEFAULT_PROMPT = "Tell me about the different types of equipment financing."
VSCODE_PATH = "/Applications/Visual Studio Code.app"  # macOS default, change for Windows
VSCODE_EXE = r"C:\\Users\\<YourUsername>\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"  # Windows path example
CHATBOX_POS = (1113, 877)  # Coordinates for Copilot Chat input box
ANSWERBOX_POS = (1321, 420)  # Coordinates for Copilot answer box
GAME_WINDOW_TITLE = "Mazer"  # The title of your pygame window
VSCODE_WINDOW_TITLE = "Visual Studio Code"
GAME_PROCESS_NAME = "Python"  # Updated for macOS AppleScript focus

# Get output file path from argument or default to scripts/copilot_output.txt
if len(sys.argv) > 2:
    OUTPUT_FILE = sys.argv[2]
else:
    OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "copilot_output.txt")

print(f"Writing Copilot output to: {OUTPUT_FILE}")

# Step 1: Open VS Code as a desktop application
def open_vscode():
    try:
        if platform.system() == 'Darwin':
            subprocess.Popen(["open", "-a", VSCODE_PATH])
            time.sleep(2)
            # Use AppleScript to make VS Code full screen
            script = f'''osascript -e 'tell application "System Events" to tell process "Visual Studio Code" to set value of attribute "AXFullScreen" of window 1 to true' '''
            os.system(script)
        elif platform.system() == 'Windows':
            subprocess.Popen([VSCODE_EXE])
            time.sleep(2)
            import pygetwindow as gw
            win = gw.getWindowsWithTitle("Visual Studio Code")
            if win:
                win[0].activate()
                win[0].maximize()
                time.sleep(1)
        else:
            subprocess.call(['wmctrl', '-a', GAME_WINDOW_TITLE])
        print("VS Code launched.")
    except Exception as e:
        print(f"Failed to open VS Code: {e}")

def focus_vscode():
    time.sleep(5)  # Wait for VS Code to launch
    pyautogui.hotkey('alt', 'tab')
    time.sleep(1)

def open_copilot_chat():
    if platform.system() == 'Darwin':
        pyautogui.hotkey('command', 'shift', 'p')
    else:
        pyautogui.hotkey('ctrl', 'shift', 'p')
    time.sleep(1)
    pyperclip.copy('Copilot: Chat')
    pyautogui.hotkey('ctrl', 'v') if platform.system() != 'Darwin' else pyautogui.hotkey('command', 'v')
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(2)

def enter_prompt(prompt):
    pyautogui.click(CHATBOX_POS[0], CHATBOX_POS[1])
    time.sleep(0.5)
    pyperclip.copy(prompt)
    pyautogui.hotkey('ctrl', 'v') if platform.system() != 'Darwin' else pyautogui.hotkey('command', 'v')
    pyautogui.press('enter')
    print("Prompt entered.")
    time.sleep(7)

def copy_copilot_output():
    pyautogui.rightClick(ANSWERBOX_POS[0], ANSWERBOX_POS[1])
    time.sleep(0.5)
    pyautogui.press('enter')
    time.sleep(1)
    output = pyperclip.paste()
    return output

def focus_game_window():
    try:
        if platform.system() == 'Darwin':
            # Try AppleScript with correct process name
            script = f'''osascript -e 'tell application "System Events" to set frontmost of process "{GAME_PROCESS_NAME}" to true' '''
            result = os.system(script)
            if result != 0:
                print("AppleScript failed or not permitted, using click fallback.")
                # Click the center of the game window (1000x900 -> 500, 450)
                pyautogui.click(500, 450)
                time.sleep(0.5)
                # Try alt+tab a few times as a last resort
                for _ in range(3):
                    pyautogui.hotkey('alt', 'tab')
                    time.sleep(0.3)
        elif platform.system() == 'Windows':
            import pygetwindow as gw
            win = gw.getWindowsWithTitle(GAME_WINDOW_TITLE)
            if win:
                win[0].activate()
        else:
            subprocess.call(['wmctrl', '-a', GAME_WINDOW_TITLE])
    except Exception as e:
        print(f"Could not focus game window: {e}")

def main():
    prompt = ' '.join(sys.argv[1:]) if len(sys.argv) > 1 else DEFAULT_PROMPT
    open_vscode()
    focus_vscode()
    open_copilot_chat()
    enter_prompt(prompt)
    output = copy_copilot_output()
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(output)
    print(f"Copilot output saved to {OUTPUT_FILE}")
    focus_game_window()

if __name__ == "__main__":
    main() 