# Hand Tracking ->only the hands are detected (better 4 our proj)
from datetime import datetime, time
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

model_path = "models/hand_landmarker.task"

# Initialize MediaPipe Hands
# mp_hands = mp.solutions.hands
mp_hands = vision.HandLandmarker
# mp_drawing = mp.solutions.drawing_utils
mp_drawing = vision.drawing_utils
# hands = vision.(
#     static_image_mode=False,
#     num_hands=1,
#     model_complexity=1,
#     min_detection_confidence=0.5,
#     min_tracking_confidence=0.5
# )
def results(result: vision.HandLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    for hand_landmarks in result.hand_landmarks:
            # Draw hand skeleton
            mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                mp.tasks.vision.HandLandmarksConnections.HAND_CONNECTIONS
            )

            # Draw landmark numbers
            height, width, _ = frame.shape

            for i, landmark in enumerate(hand_landmarks):

                x = int(landmark.x * width)
                y = int(landmark.y * height)

                cv2.putText(
                    frame,
                    str(i),
                    (x + 5, y - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.4,
                    (0, 255, 255),
                    1
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

# Open webcam
cap = cv2.VideoCapture(0)

# Request a higher camera resolution
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

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
    cv2.imshow("MediaPipe Hands", frame)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord('q'):
        landmarker.close()
        break

cap.release()
cv2.destroyAllWindows()
