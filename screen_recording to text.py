import cv2
import pytesseract
import os

# Set path to tesseract.exe (Update this path if different)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def extract_text_from_frame(frame):
    # Resize image for better OCR
    frame = cv2.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv2.INTER_LINEAR)

    # Convert to grayscale
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Enhance contrast and apply adaptive threshold
    gray = cv2.adaptiveThreshold(gray, 255,
                                 cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv2.THRESH_BINARY, 11, 2)

    # Invert colors (helps with dark mode)
    inverted = cv2.bitwise_not(gray)

    # OCR to extract text
    text = pytesseract.image_to_string(inverted)
    return text.strip()

def detect_mouse_cursor(frame):
    # Convert to grayscale and threshold to detect white regions
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 250, 255, cv2.THRESH_BINARY)
    white_area = cv2.countNonZero(thresh)

    # Heuristic: if white pixels > threshold, assume cursor is visible
    return white_area > 500

def analyze_video(video_path, output_log='D:/screen_analysis_log.txt'):
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print("Error opening video file.")
        return

    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * 1)  # Analyze 1 frame per second

    frame_id = 0
    analysis_log = []

    print("Analyzing video...")

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % interval == 0:
            timestamp = frame_id / fps

            # Extract text and mouse detection
            text = extract_text_from_frame(frame)
            mouse_present = detect_mouse_cursor(frame)

            log = f"Time {timestamp:.2f}s: "
            if text:
                log += f"[Text Detected]: {text}. "
            if mouse_present:
                log += "[Mouse Cursor Detected]"

            if text or mouse_present:
                analysis_log.append(log)

        frame_id += 1

    cap.release()

    # Write results to file
    with open(output_log, 'w', encoding='utf-8') as f:
        for entry in analysis_log:
            f.write(entry + '\n')

    print(f"✅ Analysis complete. Log saved to: {output_log}")

# === Run Analysis ===
video_input_path = "D:/screen_recording1.avi"  # Replace with your file
analyze_video(video_input_path)
