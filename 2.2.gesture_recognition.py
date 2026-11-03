
import cv2
import mediapipe as mp
import time
import json
import os
import math

from dollarpy import Recognizer, Template, Point
from websockets.sync.client import connect


# Initialize MediaPipe Hands
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)


# Store gesture templates in JSON file
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


# Load saved templates
templates = load_templates()


# Map DollarPy gestures to website actions
GESTURE_ACTIONS = {
    "Swipe Left": "prev",
    "Swipe Right": "next",
    "Swipe Up": "volup",
    "Swipe Down": "voldown",
    "Circle": "play"
}


# Connect to WebSocket server
try:

    websocket = connect("ws://localhost:8765")
    print("Connected to WebSocket server!")

except OSError as error:

    print("Could not connect to WebSocket server.")
    print("Start websocket_server.py first.")
    print(error)

    hands.close()
    raise SystemExit


# Send recognized gesture to website
def send_gesture(action, score):

    message = {
        "type": "gesture",
        "id": action,
        "score": score
    }

    try:
        websocket.send(json.dumps(message))
        print("Sent to web app:", action)

    except Exception as error:
        print("Could not send gesture:", error)


# Manual recording variables
recording = False
recording_label = ""
points = []
start_time = 0

RECORD_DURATION = 1.5


# Automatic recognition variables
auto_recording = False
auto_points = []

previous_tip = None

last_movement_time = 0
last_auto_sample_time = 0

AUTO_IDLE_TIME = 0.45
AUTO_SAMPLE_INTERVAL = 0.03

MOVEMENT_THRESHOLD = 0.005
MIN_GESTURE_RANGE = 0.05


# Open webcam
cap = cv2.VideoCapture(0)

print("\nGESTURE CONTROLS")
print("L = Record Swipe Left")
print("R = Record Swipe Right")
print("U = Record Swipe Up")
print("D = Record Swipe Down")
print("C = Record Circle")
print("T = Manual test")
print("Q = Quit")

print("\nAutomatic recognition is enabled!")
print("Perform a gesture after recording your templates.")


try:

    while cap.isOpened():

        success, frame = cap.read()

        if not success:
            break

        frame = cv2.flip(frame, 1)

        # Convert to RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Detect hand
        results = hands.process(rgb)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                # Draw hand landmarks
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS
                )

                # Get index fingertip
                fingertip = hand_landmarks.landmark[8]

                current_point = Point(
                    fingertip.x,
                    fingertip.y,
                    1
                )

                # Manual template recording
                if recording:

                    points.append(current_point)

                # Automatic gesture detection
                else:

                    current_time = time.time()

                    if previous_tip is not None:

                        movement = math.hypot(
                            current_point.x - previous_tip.x,
                            current_point.y - previous_tip.y
                        )

                        if movement > MOVEMENT_THRESHOLD:

                            if not auto_recording:

                                auto_recording = True

                                auto_points = [
                                    Point(
                                        previous_tip.x,
                                        previous_tip.y,
                                        1
                                    )
                                ]

                                print("Movement detected...")

                            last_movement_time = current_time

                    # Collect points while gesture is active
                    if auto_recording:

                        if current_time - last_auto_sample_time >= AUTO_SAMPLE_INTERVAL:

                            auto_points.append(current_point)
                            last_auto_sample_time = current_time

                previous_tip = current_point

        else:

            previous_tip = None

        # Display manual recording status
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

            # Check if manual recording finished
            if time.time() - start_time >= RECORD_DURATION:

                recording = False

                if len(points) >= 10:

                    if recording_label == "TEST":

                        if len(templates) > 0:

                            recognizer = Recognizer(templates)
                            result = recognizer.recognize(points)

                            gesture_name = result[0]
                            score = float(result[1])

                            print("Gesture:", gesture_name)
                            print("Similarity Score:", score)

                            action = GESTURE_ACTIONS.get(gesture_name)

                            if action:
                                send_gesture(action, score)

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

        # Finish automatic gesture when hand movement stops
        if auto_recording and not recording:

            if time.time() - last_movement_time >= AUTO_IDLE_TIME:

                auto_recording = False

                if len(auto_points) >= 10 and len(templates) > 0:

                    xs = [p.x for p in auto_points]
                    ys = [p.y for p in auto_points]

                    gesture_range = max(
                        max(xs) - min(xs),
                        max(ys) - min(ys)
                    )

                    # Ignore very small movements
                    if gesture_range >= MIN_GESTURE_RANGE:

                        recognizer = Recognizer(templates)
                        result = recognizer.recognize(auto_points)

                        gesture_name = result[0]
                        score = float(result[1])

                        print("\nAutomatic Gesture:", gesture_name)
                        print("Similarity Score:", score)

                        action = GESTURE_ACTIONS.get(gesture_name)

                        if action:
                            send_gesture(action, score)

                    else:
                        print("Small movement ignored.")

                elif len(templates) == 0:
                    print("Record gesture templates first!")

                auto_points = []
                previous_tip = None

        # Display automatic recognition status
        cv2.putText(
            frame,
            "Automatic Recognition: ON",
            (20, 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 255),
            2
        )

        # Display controls
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

        # Clear automatic movement before manual recording/testing
        if key in [
            ord('l'), ord('r'), ord('u'),
            ord('d'), ord('c'), ord('t')
        ] and not recording:

            auto_recording = False
            auto_points = []
            previous_tip = None

        # Record Swipe Left
        if key == ord('l') and not recording:

            recording = True
            recording_label = "Swipe Left"
            points = []
            start_time = time.time()

            print("Perform Swipe Left now!")

        # Record Swipe Right
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

        # Manual test (optional)
        elif key == ord('t') and not recording:

            if len(templates) == 0:

                print("Record gesture templates first!")

            else:

                recording = True
                recording_label = "TEST"
                points = []
                start_time = time.time()

                print("Perform a gesture!")

        # Quit
        elif key == ord('q'):
            break


finally:

    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    websocket.close()

    print("WebSocket disconnected.")
    print("Program closed.")
