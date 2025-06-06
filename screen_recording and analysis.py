import os
import time
import psutil
import pygetwindow as gw
from pynput import keyboard, mouse
from datetime import datetime
from threading import Thread

# Output folder
output_dir = r"D:\ScreenRecordings"
os.makedirs(output_dir, exist_ok=True)

log_file_path = os.path.join(output_dir, "sop_activity_log.txt")

# Global stores
key_log = []
click_log = []
activity_log = []

recording = True

# Mouse click detection
def on_click(x, y, button, pressed):
    if pressed:
        log = f"Mouse clicked at ({x}, {y}) with {button}"
        click_log.append(log)

# Keyboard key detection
def on_press(key):
    try:
        key_log.append(f"Key pressed: {key.char}")
    except AttributeError:
        key_log.append(f"Special key pressed: {key}")

# Helper functions
def detect_running_browsers(process_list):
    browsers = ['chrome', 'firefox', 'msedge', 'brave', 'opera', 'iexplore']
    running = [p for p in process_list if any(browser in p.lower() for browser in browsers)]
    return list(set(running))

def detect_open_documents(process_list):
    doc_types = {
        'Word': ['winword'],
        'Excel': ['excel'],
        'PowerPoint': ['powerpnt'],
        'PDF Reader': ['acrord32', 'foxit', 'pdf'],
        'Notepad': ['notepad'],
        'VSCode': ['code'],
        'Notepad++': ['notepad++']
    }

    open_docs = []
    for name, keywords in doc_types.items():
        for proc in process_list:
            if any(k in proc.lower() for k in keywords):
                open_docs.append(name)
                break

    return open_docs

# Monitor thread
def monitor_thread():
    while recording:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Active window
        try:
            active_window = gw.getActiveWindow().title
        except:
            active_window = "Unknown"

        # Background apps
        processes = [p.info['name'] for p in psutil.process_iter(['name']) if p.info['name']]
        unique_processes = list(set(processes))

        # Detect browsers and documents
        running_browsers = detect_running_browsers(unique_processes)
        open_documents = detect_open_documents(unique_processes)

        # Battery info
        battery = psutil.sensors_battery()
        battery_status = f"{battery.percent}% {'Plugged In' if battery.power_plugged else 'On Battery'}" if battery else "Battery Info Unavailable"

        # Media status
        music_status = "Not Detected"
        if any("spotify" in p.lower() or "chrome" in p.lower() for p in unique_processes):
            music_status = "Possibly Playing"

        # Log
        log_entry = f"\n[{timestamp}]\n"
        log_entry += f"Active Window: {active_window}\n"
        log_entry += f"Mouse Clicks: {click_log.copy()}\n"
        log_entry += f"Keys Pressed: {key_log.copy()}\n"
        log_entry += f"Running Browsers: {', '.join(running_browsers) if running_browsers else 'None'}\n"
        log_entry += f"Open Documents: {', '.join(open_documents) if open_documents else 'None'}\n"
        log_entry += f"Top Background Apps: {', '.join(unique_processes[:5])}\n"
        log_entry += f"Music Status: {music_status}\n"
        log_entry += f"Battery: {battery_status}\n"
        log_entry += "-" * 60

        activity_log.append(log_entry)
        click_log.clear()
        key_log.clear()
        time.sleep(1)

# Start listeners
mouse_listener = mouse.Listener(on_click=on_click)
keyboard_listener = keyboard.Listener(on_press=on_press)
mouse_listener.start()
keyboard_listener.start()

# Start recording thread
thread = Thread(target=monitor_thread)
thread.start()

print("Recording started. Press Ctrl+C to stop...")

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\nRecording stopped.")
    recording = False
    thread.join()

    # Save log
    with open(log_file_path, "w", encoding="utf-8") as f:
        f.write("Activity Log Summary\n")
        f.write("=" * 50 + "\n")
        for entry in activity_log:
            f.write(entry + "\n")

    print(f"\nActivity log saved to: {log_file_path}")
