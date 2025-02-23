import cv2
import numpy as np
import picamera
import picamera.array

# Initialize the Pi Camera
camera = picamera.PiCamera()
camera.resolution = (640, 480)  # Set resolution
camera.framerate = 30  # Set FPS

# OpenCV Loop to Capture and Show Frames
try:
    with picamera.array.PiRGBArray(camera) as output:
        for frame in camera.capture_continuous(output, format="bgr", use_video_port=True):
            image = frame.array  # Convert frame to a NumPy array
            
            cv2.imshow("Raspberry Pi Camera Test", image)  # Show frame

            # Clear the stream for the next frame
            output.truncate(0)

            # Exit on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

except KeyboardInterrupt:
    print("\nCamera test stopped by user.")

finally:
    camera.close()
    cv2.destroyAllWindows()
