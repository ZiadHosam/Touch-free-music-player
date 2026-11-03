
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
import time
from datetime import datetime
import json
import os

from dollarpy import Recognizer, Template, Point

# Initialize MediaPipe Hands
model_path = "models/hand_landmarker.task"

# Initialize MediaPipe Hands
mp_hands = vision.HandLandmarker
mp_drawing = vision.drawing_utils

def results(result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    for hand_landmarks in result.hand_landmarks:
            # Draw hand skeleton
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
            )

            # Get index fingertip (landmark 8)
            fingertip = hand_landmarks[8]

            # Collect coordinates during recording
            if recording:

                points.append(
                    Point(
                        fingertip.x,
                        fingertip.y,
                        1
                    )
                )


           

                

                            

hands = vision.HandLandmarkerOptions(
    base_options=mp.tasks.BaseOptions(model_asset_path=model_path),
    running_mode=vision.RunningMode.LIVE_STREAM,
    num_hands=1,
    # model_complexity=1,
    min_hand_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    result_callback= results
)


# Store gesture templates in json file
TEMPLATE_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "gesture_templates.json"
)


def save_templates(templates):

    data = []

    for template in templates:

        points_data = []

        for p in template:
            points_data.append({
                "x": p.x,
                "y": p.y,
                "stroke_id": p.stroke_id
            })

        data.append({
            "name": template.name,
            "points": points_data
        })

    with open(TEMPLATE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)

    print("Templates saved successfully!")


def load_templates():

    if not os.path.exists(TEMPLATE_FILE):
        print("No saved templates found. Record your gestures.")
        return []

    try:
        with open(TEMPLATE_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        loaded_templates = []

        for item in data:

            points = []

            for p in item["points"]:
                points.append(
                    Point(p["x"], p["y"], p["stroke_id"])
                )

            loaded_templates.append(
                Template(item["name"], points)
            )

        print("Loaded", len(loaded_templates), "templates!")

        return loaded_templates

    except (json.JSONDecodeError, KeyError, OSError, TypeError, ValueError) as error:
        print("Could not load templates:", error)
        return []
templates = load_templates()

# Recording variables
recording = False
recording_label = ""
points = []
start_time = 0

# Record each gesture for 1.5 seconds
RECORD_DURATION = 1.5

# Open webcam
cap = cv2.VideoCapture(0)

print("GESTURE CONTROLS")
print("L = Record Swipe Left")
print("R = Record Swipe Right")
print("T = Test a gesture")
print("Q = Quit")

while cap.isOpened():

    success, frame = cap.read()

    if not success:
        break

    frame = cv2.flip(frame, 1)

 # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(
        frame, cv2.COLOR_BGR2RGB
    )
    frame_rgb = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)
    timestamp_ms = int(datetime.now().microsecond)
    # Process hand detection
    # results = hands.process(frame_rgb)
    
    with mp_hands.create_from_options(hands) as landmarker:
        landmarker.detect_async(frame_rgb,timestamp_ms)

    # Display recording status
    if recording:
        cv2.putText(
            frame,
            "Recording: " + recording_label,
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

        # Check if recording finished
        if time.time() - start_time >= RECORD_DURATION:

            recording = False

            if len(points) >= 10:

                if recording_label == "TEST":

                    if len(templates) > 0:

                        recognizer = Recognizer(templates)
                        result = recognizer.recognize(points)

                        print("Gesture:", result[0])
                        print("Similarity Score:", result[1])

                    else:
                        print("Record templates first!")

                else:

                    template = Template(
                        recording_label,
                        points.copy()
                    )

                    templates.append(template)
                    save_templates(templates)
                    print(
                        recording_label,
                        "template saved!",
                        "Points:",
                        len(points)
                    )

            else:
                print("Not enough points detected. Try again.")

            points = []

    cv2.putText(
        frame,
        "L: Left | R: Right | U: Up | D: Down | C: Circle | T: Test | Q: Quit",
        (20, frame.shape[0] - 20),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (255, 255, 255),
        2
    )

    cv2.imshow("Gesture Recognition", frame)

    key = cv2.waitKey(1) & 0xFF

    # Start recording Swipe Left
    if key == ord('l') and not recording:

        recording = True
        recording_label = "Swipe Left"
        points = []
        start_time = time.time()

        print("Perform Swipe Left now!")

    # Start recording Swipe Right
    elif key == ord('r') and not recording:

        recording = True
        recording_label = "Swipe Right"
        points = []
        start_time = time.time()

        print("Perform Swipe Right now!")
    # Record Swipe Up
    elif key == ord('u') and not recording:

        recording = True
        recording_label = "Swipe Up"
        points = []
        start_time = time.time()

        print("Perform Swipe Up now!")

    # Record Swipe Down
    elif key == ord('d') and not recording:

        recording = True
        recording_label = "Swipe Down"
        points = []
        start_time = time.time()

        print("Perform Swipe Down now!")

    # Record Circle
    elif key == ord('c') and not recording:

        recording = True
        recording_label = "Circle"
        points = []
        start_time = time.time()

        print("Perform Circle now!")
    # Test a new gesture
    elif key == ord('t') and not recording:

        if len(templates) == 0:
            print("Record gesture templates first!")

        else:
            recording = True
            recording_label = "TEST"
            points = []
            start_time = time.time()

            print("Perform a gesture to recognize!")

    elif key == ord('q'):
        landmarker.close()
        break

cap.release()
cv2.destroyAllWindows()


# if recording_label == "TEST":

#     dx = points[-1].x - points[0].x
#     dy = points[-1].y - points[0].y

#     # Check for horizontal movement
#     if abs(dx) > 0.15 and abs(dx) > abs(dy):

#         if dx < 0:
#             print("Gesture: Swipe Left")
#         else:
#             print("Gesture: Swipe Right")

#     # Use DollarPy for the other gestures
#     elif len(templates) > 0:

#         recognizer = Recognizer(templates)
#         result = recognizer.recognize(points)

#         print("Gesture:", result[0])
#         print("Similarity Score:", result[1])

#     else:
#         print("Record other gesture templates first!")