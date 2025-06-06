# 🧠 UserActivityInsight

**UserActivityInsight** is a powerful Python-based monitoring tool that captures system activity and webcam input to analyze user behavior. It tracks windows, keystrokes, mouse activity, face detection, gaze direction, hand gestures, and generates a comprehensive activity report.

---

## 📌 Features

- ⌨️ Keyboard and 🖱️ mouse event logging  
- 🪟 Active window, browser, and document tracking  
- 👁️ Real-time webcam-based face, gaze, and hand detection  
- 🔋 Battery status & 🎵 music playback estimation  
- 🧠 Auto-generated user activity report  
- 📸 Manual screen snapshot on `S` key press  
- 📄 Modular scripts for each feature  
- 🤖 Integration with **Google Gemini Pro** for report summarization  

---

## 🗂️ Project Structure

```
UserActivityInsight/
│
├── activity_logger.py            # System activity monitoring
├── vision_tracking.py            # Webcam-based user tracking
├── snapshot_listener.py          # On-demand screen capture
├── report_generator.py           # Post-monitoring report generation
├── gemini_generate.py            # Gemini Pro integration script
├── UserActivityInsight_Complete.py  # Unified all-in-one script
│
├── D:/ScreenRecordings/          # Logs, reports & screen recordings
├── D:/Snapshots/                 # Saved screenshots
```

---

## 🔧 Requirements

### 🔁 Environment Variable

For Gemini API integration, set your **Google Gemini API key**:

```bash
# On Windows CMD
set GOOGLE_API_KEY=your_api_key_here

# On Unix/Linux/macOS
export GOOGLE_API_KEY=your_api_key_here
```

### 📦 Python Libraries

Install required libraries:

```bash
pip install pyautogui psutil pygetwindow pynput keyboard opencv-python mediapipe google-generativeai
```

---

## ▶️ How to Run

1. **Run Modular Scripts (Individually):**

```bash
python activity_logger.py
python vision_tracking.py
python snapshot_listener.py
python report_generator.py
```

2. **Run Unified All-In-One Script:**

```bash
python UserActivityInsight_Complete.py
```

The program will:
- Start logging keyboard/mouse activity
- Track webcam-based facial and hand gestures
- Generate a `.txt` report after completion
- Save screen recordings and vision logs

---

## 📤 Output

- `sop_activity_log.txt` – System activity log  
- `vision_activity_log.txt` – Face/gaze/hand tracking log  
- `user_activity_analysis_report.txt` – Final summary report  
- `activity_detected.avi` – Webcam recording  
- Screenshots in `D:/Snapshots/`

---

## 🤖 Gemini Integration

Use `gemini_generate.py` to feed the final report into Google Gemini for an AI-generated summary.

---

## 📍 Use Cases

- Digital productivity tracking  
- Online exam or training supervision  
- Behavioral research  
- Personal time auditing  

---

## 📣 Author

**Abhishek Kumar**  
For feedback or collaboration, feel free to connect!
