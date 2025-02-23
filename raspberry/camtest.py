import cv2
from picamera2 import Picamera2

# Initialize the Pi Camera
picam2 = Picamera2()
picam2.preview_configuration.main.size = (640, 480)  # Set resolution
picam2.preview_configuration.main.format = "RGB888"  # Set format
picam2.preview_configuration.controls.FrameRate = 30  # Set FPS
picam2.configure("preview")
picam2.start()

# OpenCV Loop to Capture and Show Frames
try:
    while True:
        frame = picam2.capture_array()
        cv2.imshow("Raspberry Pi Camera Test", frame)

        # Exit on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\nCamera test stopped by user.")

finally:
    picam2.close()
    cv2.destroyAllWindows()
