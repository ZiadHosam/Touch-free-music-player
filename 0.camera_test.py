
import cv2

# Open the default webcam
cap = cv2.VideoCapture(0)

# Check if the camera opened
if not cap.isOpened():
    print("Could not open camera")
    exit()

print("Camera is working!")

while True:

    # Read a frame from the camera
    success, frame = cap.read()

    if not success:
        print("Could not read camera frame")
        break

    # Show the camera
    cv2.imshow("Camera Test", frame)

    # Press Q to close
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release camera
cap.release()
cv2.destroyAllWindows()
