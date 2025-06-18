from pynput import mouse, keyboard
import pygetwindow as gw
import pyautogui
import pytesseract
from datetime import datetime
import threading
import os
import time
from PIL import Image

# ----------- Configuration ------------
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
LOG_PATH = "D:/user_activity_log.txt"
SNAPSHOT_FOLDER = "D:/button_snapshots"
os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)

# ----------- Global Variables ------------
typed_text_buffer = ""
last_window = None
step_counter = 1
step_lock = threading.Lock()
stop_flag = threading.Event()

# ----------- Utility Functions ------------
def write_log_step(website, clicked=None, typed=None, screenshot_note=None):
    global step_counter
    with step_lock:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"\nStep {step_counter} @ {timestamp}\nWebsite Active: {website}"
        if clicked:
            log_entry += f"\nClicked on Button/Link: {clicked}"
        if typed:
            log_entry += f"\nUser Typed: {typed}"
        if screenshot_note:
            log_entry += f"\nScreenshot: {screenshot_note}"
        log_entry += "\n"

        step_counter += 1
        print(log_entry.strip())
        with open(LOG_PATH, "a", encoding='utf-8') as f:
            f.write(log_entry)

def get_active_window_title():
    try:
        win = gw.getActiveWindow()
        return win.title if win else "Unknown Window"
    except:
        return "Unknown Window"

def preprocess_image(img):
    img = img.resize((img.width * 2, img.height * 2))
    img = img.convert('L')
    img = img.point(lambda x: 0 if x < 150 else 255, '1')
    return img

def get_text_near_click(x, y, radius=200):
    screenshot = pyautogui.screenshot()
    region = (
        max(0, x - radius),
        max(0, y - radius),
        min(screenshot.width, x + radius),
        min(screenshot.height, y + radius)
    )
    cropped = screenshot.crop(region)
    cropped = preprocess_image(cropped)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    img_path = os.path.join(SNAPSHOT_FOLDER, f"snap_{timestamp}.png")
    cropped.save(img_path)

    text = pytesseract.image_to_string(cropped).strip()
    return text if text else "No readable text"

def take_full_screenshot():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(SNAPSHOT_FOLDER, f"F10_screenshot_{timestamp}.png")
    pyautogui.screenshot(filepath)
    print(f"Screenshot saved: {filepath}")
    write_log_step(get_active_window_title(), screenshot_note=f"Saved at {filepath}")

# ----------- Event Handlers ------------
def on_click(x, y, button, pressed):
    if pressed:
        window_title = get_active_window_title()
        detected_text = get_text_near_click(x, y)
        if detected_text != "No readable text":
            write_log_step(window_title, clicked=detected_text)
        else:
            write_log_step(window_title, clicked="(no text detected near click)")

def on_press(key):
    global typed_text_buffer, last_window
    try:
        if key == keyboard.Key.f10:
            take_full_screenshot()
            return
        elif key == keyboard.Key.f9:
            stop_flag.set()
            write_log_step(get_active_window_title(), screenshot_note="Monitoring stopped by user via F9")
            return

        active_win = get_active_window_title()
        if last_window != active_win:
            typed_text_buffer = ""
            last_window = active_win

        if hasattr(key, 'char') and key.char is not None:
            typed_text_buffer += key.char
        elif key == keyboard.Key.space:
            typed_text_buffer += ' '
        elif key == keyboard.Key.enter:
            if typed_text_buffer.strip():
                write_log_step(active_win, typed=typed_text_buffer.strip())
            typed_text_buffer = ""
        elif key == keyboard.Key.backspace:
            typed_text_buffer = typed_text_buffer[:-1]
    except Exception as e:
        write_log_step("Unknown Window", screenshot_note=f"[ERROR] Keyboard capture failed: {e}")

# ----------- Start Listeners ------------
def start_listeners():
    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener.start()
    keyboard_listener.start()

    while not stop_flag.is_set():
        time.sleep(0.5)

    mouse_listener.stop()
    keyboard_listener.stop()

# ----------- Main Execution ------------
threading.Thread(target=start_listeners, daemon=True).start()
write_log_step("System", screenshot_note="=== Structured User Activity Monitoring Started ===")

try:
    while not stop_flag.is_set():
        time.sleep(1)
except KeyboardInterrupt:
    write_log_step("System", screenshot_note="Monitoring stopped by keyboard interrupt.")
