# Holistic Tracking -> (lab code) for Hand and Body Skeleton Tracking (prob will use bec reqs)+ needs whole skeleton 4 accuracy

import cv2
import mediapipe as mp

# MediaPipe Holistic
mp_holistic = mp.solutions.holistic
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Initialize Holistic
holistic = mp_holistic.Holistic(
    static_image_mode=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
    model_complexity=2
)

# Open laptop camera
cap = cv2.VideoCapture(0)

while cap.isOpened():

    success, frame = cap.read()

    if not success:
        break

    # Flip camera
    f_frame = cv2.flip(frame, 1)

    # Convert BGR to RGB
    frame_rgb = cv2.cvtColor(
        f_frame, cv2.COLOR_BGR2RGB
    )

    # Process frame
    results = holistic.process(frame_rgb)

    # Copy frame
    annotated_image = f_frame.copy()

    # Draw left hand
    mp_drawing.draw_landmarks(
        annotated_image,
        results.left_hand_landmarks,
        mp_holistic.HAND_CONNECTIONS
    )

    # Draw right hand
    mp_drawing.draw_landmarks(
        annotated_image,
        results.right_hand_landmarks,
        mp_holistic.HAND_CONNECTIONS
    )

    # Draw body skeleton
    mp_drawing.draw_landmarks(
        annotated_image,
        results.pose_landmarks,
        mp_holistic.POSE_CONNECTIONS,
        landmark_drawing_spec=
        mp_drawing_styles.get_default_pose_landmarks_style()
    )

    # Display camera
    cv2.imshow("Hand Tracking", annotated_image)

    # Press Q to exit
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
holistic.close()
cv2.destroyAllWindows()
