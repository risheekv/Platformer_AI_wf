import pyautogui
import time

print("Move your mouse to the Copilot chatbox... You have 5 seconds.")
time.sleep(5)

position = pyautogui.position()
print(f"Mouse is at: {position}") 