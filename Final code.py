
# === Monitoring & Logging Code ===
import os
import time
import pyautogui
import psutil
import pygetwindow as gw
from pynput import keyboard as pynput_keyboard, mouse
import keyboard
import cv2
import mediapipe as mp
from datetime import datetime, timedelta
from threading import Thread
from collections import defaultdict, Counter
# Paths
snapshot_dir = 'D:/Snapshots'
recording_dir = 'D:/ScreenRecordings'
os.makedirs(snapshot_dir, exist_ok=True)
os.makedirs(recording_dir, exist_ok=True)

log_file_path = os.path.join(recording_dir, "sop_activity_log.txt")
vision_log_path = os.path.join(recording_dir, "vision_activity_log.txt")
report_output_path = os.path.join(recording_dir, "user_activity_analysis_report.txt")
video_path = os.path.join(recording_dir, "activity_detected.avi")

# Flags & Logs
recording = True
key_log, click_log, activity_log = [], [], []

# Mediapipe
mp_face, mp_hands, mp_drawing = mp.solutions.face_mesh, mp.solutions.hands, mp.solutions.drawing_utils
face_mesh = mp_face.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
out = cv2.VideoWriter(video_path, fourcc, 10.0, (640, 480))
vision_log_file = open(vision_log_path, "w")

def on_click(x, y, button, pressed):
    if pressed:
        click_log.append(f"Mouse clicked at ({x}, {y}) with {button}")

def on_press(key):
    try:
        key_log.append(f"Key pressed: {key.char}")
    except:
        key_log.append(f"Special key pressed: {key}")

def detect_running_browsers(process_list):
    browsers = ['chrome', 'firefox', 'msedge', 'brave', 'opera', 'iexplore']
    return list(set([p for p in process_list if any(browser in p.lower() for browser in browsers)]))

def detect_open_documents(process_list):
    doc_types = {
        'Word': ['winword'], 'Excel': ['excel'], 'PowerPoint': ['powerpnt'],
        'PDF Reader': ['acrord32', 'foxit', 'pdf'], 'Notepad': ['notepad'],
        'VSCode': ['code'], 'Notepad++': ['notepad++']
    }
    open_docs = []
    for name, keywords in doc_types.items():
        if any(any(k in proc.lower() for k in keywords) for proc in process_list):
            open_docs.append(name)
    return open_docs

def monitor_thread():
    while recording:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        try:
            active_window = gw.getActiveWindow().title
        except:
            active_window = "Unknown"

        processes = [p.info['name'] for p in psutil.process_iter(['name']) if p.info['name']]
        unique_processes = list(set(processes))
        running_browsers = detect_running_browsers(unique_processes)
        open_documents = detect_open_documents(unique_processes)

        battery = psutil.sensors_battery()
        battery_status = f"{battery.percent}% {'Plugged In' if battery.power_plugged else 'On Battery'}" if battery else "Battery Info Unavailable"
        music_status = "Possibly Playing" if any("spotify" in p.lower() or "chrome" in p.lower() for p in unique_processes) else "Not Detected"

        log_entry = f"\n[{timestamp}]\nActive Window: {active_window}\nMouse Clicks: {click_log.copy()}\nKeys Pressed: {key_log.copy()}\n"
        log_entry += f"Running Browsers: {', '.join(running_browsers) if running_browsers else 'None'}\n"
        log_entry += f"Open Documents: {', '.join(open_documents) if open_documents else 'None'}\n"
        log_entry += f"Top Background Apps: {', '.join(unique_processes[:5])}\nMusic Status: {music_status}\nBattery: {battery_status}\n"
        log_entry += "-" * 60

        activity_log.append(log_entry)
        click_log.clear()
        key_log.clear()
        time.sleep(1)

def snapshot_listener():
    while recording:
        if keyboard.is_pressed('s'):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = os.path.join(snapshot_dir, f"screen_{timestamp}.png")
            pyautogui.screenshot().save(filename)
            print(f"✅ Snapshot saved: {filename}")
            time.sleep(0.5)
        elif keyboard.is_pressed('q'):
            break
        time.sleep(0.1)

def vision_capture():
    while recording:
        ret, frame = cap.read()
        if not ret:
            break

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_results = face_mesh.process(frame_rgb)
        hand_results = hands.process(frame_rgb)
        activity_text = []

        if face_results.multi_face_landmarks:
            activity_text.append("Face detected")
            for face_landmarks in face_results.multi_face_landmarks:
                mp_drawing.draw_landmarks(frame, face_landmarks, mp_face.FACEMESH_CONTOURS)
        else:
            activity_text.append("No face detected")

        if hand_results.multi_hand_landmarks:
            activity_text.append(f"{len(hand_results.multi_hand_landmarks)} hand(s) detected")
            for hand_landmarks in hand_results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
        else:
            activity_text.append("No hands detected")

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        vision_log_file.write(f"{timestamp} - {', '.join(activity_text)}\n")
        out.write(frame)

# Start Listeners
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener = pynput_keyboard.Listener(on_press=on_press)
mouse_listener.start()
keyboard_listener.start()

threads = [
    Thread(target=monitor_thread),
    Thread(target=snapshot_listener),
    Thread(target=vision_capture)
]

for t in threads: t.start()
print("🟢 Recording started. Press Ctrl+C to stop...")

try:
    while any(t.is_alive() for t in threads):
        time.sleep(1)
except KeyboardInterrupt:
    print("\n🛑 Stopping...")
    recording = False
    for t in threads: t.join()
finally:
    cap.release()
    out.release()
    vision_log_file.close()
    face_mesh.close()
    hands.close()
    cv2.destroyAllWindows()
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("Activity Log Summary\n" + "="*50 + "\n" + '\n'.join(activity_log))

    print(f"📄 Logs saved to: {log_file_path}")
    print(f"📽️ Video saved to: {video_path}")
    print(f"📑 Vision log saved to: {vision_log_path}")

# === AUTO-TRIGGER GEMINI BASED ON FINAL REPORT ===
# Required: pip install google-genai

import os
from google import genai
from google.genai import types

def generate_with_gemini(prompt):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("API key not found. Set the 'GOOGLE_API_KEY' environment variable.")
    client = genai.Client(api_key=api_key)
    model = "gemini-1.5-pro-latest"

    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    config = types.GenerateContentConfig(response_mime_type="text/plain")

    print("\n🔍 Gemini Response:\n")
    try:
        for chunk in client.models.generate_content_stream(model=model, contents=contents, config=config):
            print(chunk.text, end="")
    except Exception as e:
        print(f"\n❌ Error: {e}")

# Prompt user after report is ready
print("\n🤖 Do you want to analyze the report with Gemini AI? (y/n)")
if input().lower().strip() == "y":
    with open(report_output_path, "r", encoding="utf-8") as f:
        report_text = f.read()
    print("\n📨 Sending report to Gemini...")
    generate_with_gemini(report_text)
