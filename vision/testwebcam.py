import cv2

# Open video stream
cap = cv2.VideoCapture(0)  # Use 0 for webcam or provide a file path for video

if not cap.isOpened():
    print("Error: Could not open video stream or file.")
    exit()

while True:
    ret, frame = cap.read()
    if not ret:
        print("Error: Failed to capture frame.")
        break

    # Add object detection or processing here

    # Display the frame
    cv2.imshow("YOLOv8 Largest Object Detection", frame)

    # Exit on 'q' key press
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release resources
cap.release()
cv2.destroyAllWindows()
