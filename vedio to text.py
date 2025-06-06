import cv2
import mediapipe as mp
import datetime
import os

# Initialize mediapipe
mp_face = mp.solutions.face_mesh
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Setup webcam and output paths
cap = cv2.VideoCapture(0)
fourcc = cv2.VideoWriter_fourcc(*'XVID')
video_path = 'D:/activity_detected.avi'
log_path = 'D:/activity_log.txt'
out = cv2.VideoWriter(video_path, fourcc, 10.0, (640, 480))

# Prepare MediaPipe models
face_mesh = mp_face.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5)
hands = mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Open log file
log_file = open(log_path, "w")

start_time = datetime.datetime.now()
duration = 30  # seconds

print("Silent recording started...")

while (datetime.datetime.now() - start_time).seconds < duration:
    ret, frame = cap.read()
    if not ret:
        break

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    face_results = face_mesh.process(frame_rgb)
    hand_results = hands.process(frame_rgb)

    activity_text = []

    # Face detection
    if face_results.multi_face_landmarks:
        activity_text.append("Face detected")

        for face_landmarks in face_results.multi_face_landmarks:
            # Eye detection
            left_eye = face_landmarks.landmark[159]
            right_eye = face_landmarks.landmark[386]

            if left_eye.y < face_landmarks.landmark[145].y and right_eye.y < face_landmarks.landmark[374].y:
                activity_text.append("Eyes open")
            else:
                activity_text.append("Eyes possibly closed")

            # Gaze direction estimation
            nose_tip = face_landmarks.landmark[1]
            if nose_tip.x < 0.4:
                activity_text.append("Looking right")
            elif nose_tip.x > 0.6:
                activity_text.append("Looking left")
            else:
                activity_text.append("Looking at screen")

            mp_drawing.draw_landmarks(frame, face_landmarks, mp_face.FACEMESH_CONTOURS)
    else:
        activity_text.append("No face detected")

    # Hand detection
    if hand_results.multi_hand_landmarks:
        activity_text.append(f"{len(hand_results.multi_hand_landmarks)} hand(s) detected")
        for hand_landmarks in hand_results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
    else:
        activity_text.append("No hands detected")

    # Log activity to file with timestamp
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"{timestamp} - {', '.join(activity_text)}\n")

    # Save frame to video file
    out.write(frame)

    # DO NOT SHOW THE WINDOW
    # Commented out to make it invisible:
    # cv2.imshow("Activity Detection", frame)
    # if cv2.waitKey(1) & 0xFF == ord('q'):
    #     break

# Cleanup
cap.release()
out.release()
cv2.destroyAllWindows()
face_mesh.close()
hands.close()
log_file.close()

print(f"Silent recording finished. Video saved to: {video_path}")
print(f"Activity log saved to: {log_path}")
