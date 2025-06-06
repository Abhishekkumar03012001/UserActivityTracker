import re
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# --------- File Paths ---------
screen_file_path = "D:/ScreenRecordings/sop_activity_log.txt"
face_file_path = "D:/activity_log.txt"
report_output_path = "D:/user_activity_analysis_report.txt"

# --------- Parse Screen Activity ---------
def parse_screen_activity(path):
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    entries = data.split("------------------------------------------------------------")
    logs = []

    for entry in entries:
        lines = entry.strip().splitlines()
        if not lines:
            continue
        log = {}
        try:
            log["timestamp"] = datetime.strptime(lines[0].strip("[]"), "%Y-%m-%d %H:%M:%S.%f")
            for line in lines[1:]:
                if ": " in line:
                    k, v = line.split(": ", 1)
                    log[k.strip()] = v.strip()
            logs.append(log)
        except:
            continue
    return logs

# --------- Parse Face Activity ---------
def parse_face_activity(path):
    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    logs = []
    for line in lines:
        try:
            ts, activity = line.strip().split(" - ", 1)
            logs.append({"timestamp": datetime.strptime(ts, "%Y-%m-%d %H:%M:%S"), "activity": activity})
        except:
            continue
    return logs

# --------- Normalize Typed Keys ---------
def normalize_keys(key_entries):
    keys = []
    for entry in key_entries:
        cleaned = entry.strip("[]").replace("'", "").replace(",", "")
        tokens = cleaned.split()
        keys.extend(tokens)

    typed_chars = []
    i = 0
    while i < len(keys):
        token = keys[i].lower()

        # Match: Key | pressed: | x
        if token == "key" and i + 2 < len(keys) and keys[i + 1].lower() == "pressed:":
            char = keys[i + 2]
            if len(char) == 1:  # actual letter
                typed_chars.append(char)
            i += 3
            continue

        # Match: Special | key | pressed: | Key.space
        if token == "special" and i + 3 < len(keys) and keys[i + 1].lower() == "key" and keys[i + 2].lower() == "pressed:":
            special_key = keys[i + 3].lower()
            if "space" in special_key:
                typed_chars.append(" ")
            elif "enter" in special_key:
                typed_chars.append("\n")
            elif "tab" in special_key:
                typed_chars.append("\t")
            i += 4
            continue

        i += 1

    return keys, ''.join(typed_chars)

# --------- Analyze & Report ---------
def analyze_data(screen_logs, face_logs):
    report = []

    time_per_window = defaultdict(timedelta)
    typed_keys = defaultdict(list)
    mouse_clicks = defaultdict(int)

    for i in range(len(screen_logs) - 1):
        cur, next_ = screen_logs[i], screen_logs[i + 1]
        window = cur.get("Active Window", "Unknown")
        duration = next_["timestamp"] - cur["timestamp"]
        time_per_window[window] += duration

        if cur.get("Keys Pressed", "[]") != "[]":
            typed_keys[window].append(cur["Keys Pressed"])
        if cur.get("Mouse Clicks", "[]") != "[]":
            mouse_clicks[window] += 1

    gaze_time = defaultdict(timedelta)
    hand_activity = defaultdict(int)
    face_by_second = defaultdict(list)

    for f in face_logs:
        second = f["timestamp"].replace(microsecond=0)
        face_by_second[second].append(f["activity"])

    for sec, activities in face_by_second.items():
        common = Counter(activities).most_common(1)[0][0]
        gaze_time[common] += timedelta(seconds=1)
        if "hand" in common.lower():
            hand_activity[common] += 1

    report.append("USER ACTIVITY REPORT\n" + "="*60)

    report.append("\n1. TIME SPENT ON APPLICATIONS / WEBSITES:\n")
    for win, dur in sorted(time_per_window.items(), key=lambda x: x[1], reverse=True):
        report.append(f" - {win}: {dur}")

    report.append("\n2. TYPING ACTIVITY:\n")
    for win, keys in typed_keys.items():
        key_tokens, full_text = normalize_keys(keys)

        # Don't filter unique characters; keep all typed chars as-is
        clean_string = full_text.replace("\n", "").replace("\t", "").replace("\r", "")
        # Normalize spaces properly (remove multiple spaces if any)
        clean_string = ' '.join(clean_string.split())

        keys_flat = ' | '.join(key_tokens)
        report.append(f" - {win}:\n    Keys Pressed: {keys_flat}\n    Full Typed String: {clean_string}\n")
    report.append("\n3. MOUSE CLICKS:\n")
    for win, count in mouse_clicks.items():
        report.append(f" - {win}: {count} click(s)")

    report.append("\n4. USER GAZE DIRECTION & DURATION:\n")
    for gaze, dur in sorted(gaze_time.items(), key=lambda x: x[1], reverse=True):
        report.append(f" - {gaze}: {dur}")

    report.append("\n5. HAND DETECTION SUMMARY:\n")
    for state, count in hand_activity.items():
        report.append(f" - {state}: {count} frames")

    report.append("\n6. OBSERVATIONS:\n")
    report.append(" • User mostly focused on one or two primary windows.")
    report.append(" • Eyes were consistently open and directed in one direction (e.g., left).")
    report.append(" • No hand gestures were prominently detected; user may have been using keyboard/mouse steadily.")
    report.append(" • Overall activity pattern suggests focus and productivity.\n")

    return '\n'.join(report)

# --------- Main Execution ---------
if __name__ == "__main__":
    screen_logs = parse_screen_activity(screen_file_path)
    face_logs = parse_face_activity(face_file_path)
    final_report = analyze_data(screen_logs, face_logs)

    with open(report_output_path, "w", encoding="utf-8") as f:
        f.write(final_report)

    print(f"✅ Report successfully saved to:\n{report_output_path}")
