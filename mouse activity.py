import cv2
import time
import threading
from pynput import mouse
from datetime import datetime
import mss
import numpy as np

log_file = "D:/SOP_log.txt"
video_file = "D:/screen_record.avi"

# ---------------------- Mouse Activity Logger ----------------------

mouse_log = []

def on_click(x, y, button, pressed):
    if pressed:
        action = f"{datetime.now()} - Mouse clicked at ({x}, {y}) with {button}"
        print(action)
        mouse_log.append(action)

def on_scroll(x, y, dx, dy):
    action = f"{datetime.now()} - Scrolled at ({x}, {y}) by ({dx}, {dy})"
    print(action)
    mouse_log.append(action)

def on_move(x, y):
    action = f"{datetime.now()} - Mouse moved to ({x}, {y})"
    print(action)
    mouse_log.append(action)

def start_mouse_listener():
    with mouse.Listener(on_click=on_click, on_scroll=on_scroll, on_move=on_move) as listener:
        listener.join()

# ---------------------- Screen Recorder ----------------------

def record_screen(duration=30, fps=10):
    with mss.mss() as sct:
        monitor = sct.monitors[1]  # Full screen
        width, height = monitor["width"], monitor["height"]

        fourcc = cv2.VideoWriter_fourcc(*"XVID")
        out = cv2.VideoWriter(video_file, fourcc, fps, (width, height))

        start_time = time.time()
        while time.time() - start_time < duration:
            img = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            out.write(frame)
            time.sleep(1 / fps)

        out.release()

# ---------------------- Save Mouse Logs ----------------------

def save_logs():
    with open(log_file, "w") as f:
        f.write("Mouse Activity Log:\n\n")
        for log in mouse_log:
            f.write(log + "\n")

# ---------------------- Analyze Screen Recording (Basic) ----------------------

def analyze_screen_video():
    cap = cv2.VideoCapture(video_file)
    prev_frame = None
    event_logs = []
    i = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        i += 1
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if prev_frame is None:
            prev_frame = gray
            continue

        delta_frame = cv2.absdiff(prev_frame, gray)
        thresh = cv2.threshold(delta_frame, 25, 255, cv2.THRESH_BINARY)[1]
        non_zero_count = np.count_nonzero(thresh)

        if non_zero_count > 50000:
            timestamp = i / 10  # Assuming 10 fps
            event_logs.append(f"{timestamp:.2f}s - Significant activity (mouse movement or click)")

        prev_frame = gray

    cap.release()

    with open("D:/screen_analysis.txt", "w") as f:
        f.write("Screen Recording Analysis:\n\n")
        for log in event_logs:
            f.write(log + "\n")

# ---------------------- Main Runner ----------------------

if __name__ == "__main__":
    print("Recording started. Press Ctrl+C to stop early.")

    mouse_thread = threading.Thread(target=start_mouse_listener)
    mouse_thread.daemon = True
    mouse_thread.start()

    # Record screen for 30 seconds
    record_screen(duration=30)

    # Save logs after screen record ends
    save_logs()
    analyze_screen_video()

    print("Activity tracking complete. Logs and analysis saved.")
