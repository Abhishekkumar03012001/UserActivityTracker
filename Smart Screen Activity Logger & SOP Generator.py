import cv2
import numpy as np
import pyautogui
import os
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from datetime import datetime
from pynput import keyboard, mouse
import pygetwindow as gw
import pytesseract
from PIL import Image
import threading
import time

# === CONFIGURATION ===
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
SCREEN_SIZE = pyautogui.size()
VIDEO_PATH = "D:/screen_recording1.avi"
OUTPUT_TEXT = "D:/video_to_text_sop.txt"
LOG_PATH = "D:/user_activity_log.txt"
SNAPSHOT_FOLDER = "D:/button_snapshots"
FRAME_INTERVAL = 30
FPS = 20.0

os.makedirs(SNAPSHOT_FOLDER, exist_ok=True)

# === GLOBALS ===
recording = True
stop_all = threading.Event()
typed_text_buffer = ""
last_window = None
step_counter = 1
step_lock = threading.Lock()

# === BLIP LOADING ===
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# === LOGGING UTIL ===
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

# === UTILITIES ===
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
    region = (max(0, x - radius), max(0, y - radius), min(screenshot.width, x + radius), min(screenshot.height, y + radius))
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

# === USER ACTIVITY MONITORING THREAD ===
def user_activity_monitor():
    def on_click(x, y, button, pressed):
        if pressed:
            window_title = get_active_window_title()
            detected_text = get_text_near_click(x, y)
            write_log_step(window_title, clicked=detected_text)

    def on_press(key):
        global typed_text_buffer, last_window, recording
        try:
            if key == keyboard.Key.f10:
                take_full_screenshot()
                return
            elif key == keyboard.Key.f9:
                recording = False
                stop_all.set()
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

    mouse_listener = mouse.Listener(on_click=on_click)
    keyboard_listener = keyboard.Listener(on_press=on_press)
    mouse_listener.start()
    keyboard_listener.start()
    while not stop_all.is_set():
        time.sleep(0.5)
    mouse_listener.stop()
    keyboard_listener.stop()

# === SCREEN RECORDER THREAD ===
def screen_record():
    global recording
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    out = cv2.VideoWriter(VIDEO_PATH, fourcc, FPS, SCREEN_SIZE)
    while recording:
        img = pyautogui.screenshot()
        frame = np.array(img)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        out.write(frame)
    out.release()

# === VIDEO TO TEXT AFTER RECORDING ===
def describe_frame(frame):
    inputs = processor(frame, return_tensors="pt").to(device)
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

def video_to_text(video_path, output_path, frame_interval):
    cap = cv2.VideoCapture(video_path)
    frame_count = 0
    step_number = 1
    log = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % frame_interval == 0:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            try:
                caption = describe_frame(frame_rgb)
                timestamp = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                log.append(f"Step {step_number} @ {timestamp}: {caption}")
                print(f"[BLIP] {log[-1]}")
                step_number += 1
            except Exception as e:
                print(f"[BLIP ERROR] Frame captioning failed: {e}")
        frame_count += 1
    cap.release()
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(log))
    print(f"[BLIP SAVED] Captions written to {output_path}")

# === MAIN LAUNCH ===
def main():
    print("[INFO] Press F9 to stop recording and monitoring")
    write_log_step("System", screenshot_note="=== Monitoring + Recording Started ===")

    t1 = threading.Thread(target=user_activity_monitor, daemon=True)
    t2 = threading.Thread(target=screen_record, daemon=True)

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    print("[INFO] Processing video for BLIP captions...")
    video_to_text(VIDEO_PATH, OUTPUT_TEXT, FRAME_INTERVAL)

if __name__ == "__main__":
    main()
