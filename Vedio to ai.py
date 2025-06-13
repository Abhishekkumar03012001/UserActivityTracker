import cv2
import os
import torch
from transformers import BlipProcessor, BlipForConditionalGeneration
from datetime import datetime

# === CONFIGURATION ===
VIDEO_PATH = "D:/screen_recording1.avi"
OUTPUT_TEXT = "D:/video_to_text_sop.txt"
FRAME_INTERVAL = 30  # Capture 1 frame every 30 frames (~1 sec if video is 30 FPS)

# === LOAD HUGGINGFACE MODEL ===
device = "cuda" if torch.cuda.is_available() else "cpu"
processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base").to(device)

# === UTILITY: Describe Frame using BLIP ===
def describe_frame(frame):
    inputs = processor(frame, return_tensors="pt").to(device)
    out = model.generate(**inputs)
    caption = processor.decode(out[0], skip_special_tokens=True)
    return caption

# === MAIN FUNCTION ===
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
                print(f"[INFO] {log[-1]}")
                step_number += 1
            except Exception as e:
                print(f"[ERROR] Failed to caption frame: {e}")

        frame_count += 1

    cap.release()

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(log))
    print(f"\n[SAVED] Actions written to {output_path}")

# === RUN ===
video_to_text(VIDEO_PATH, OUTPUT_TEXT, FRAME_INTERVAL)
