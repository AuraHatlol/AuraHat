import cv2
import torch
from ultralytics import YOLO
import numpy as np
import threading

class ObjectDetector:
    def __init__(self, model_path='yolov8n.pt', device=None, fov=90, image_width=640, image_height=480):
        """
        Initializes the YOLOv8 object detector.
        :param model_path: Path to the YOLO model file (default is 'yolov8n.pt' for COCO detection).
        :param device: The device to run the model on ('cpu' or 'cuda'). If None, it selects automatically.
        :param fov: Field of view in degrees (default 90 degrees).
        :param image_width: Width of the video frame/image.
        :param image_height: Height of the video frame/image.
        """
        print("Initializing YOLO Model...")

        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cuda":
            torch.cuda.set_device(0)

        print(f"Using device: {self.device}")

        # Load the YOLO model
        self.model = YOLO(model_path).to(self.device)

        # OpenCV video capture
        self.cap = cv2.VideoCapture(0)

        # Initialize field of view and image size
        self.fov = fov
        self.image_width = image_width
        self.image_height = image_height

        self.angle = 0.0
        self.distance = 100.0

        # Thread-related attributes
        self.thread = None
        self.running = False

        self.angle = 0.0
        self.distance = 1.0

    def detect_largest_object(self):
        """
        Detects the largest object in the current video frame and returns its midpoint and class.
        """
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            return None, None, None

        # Run YOLO detection
        results = self.model(frame)

        largest_area = 25000
        largest_box = None
        largest_class = None

        for result in results:
            boxes = result.boxes

            if boxes is not None and hasattr(boxes, 'xyxy'):
                box_coords = boxes.xyxy.cpu().numpy()
                class_ids = boxes.cls.cpu().numpy().astype(int)
                names = self.model.names  # COCO class names

                for i, box in enumerate(box_coords):
                    x1, y1, x2, y2 = map(int, box)
                    area = (x2 - x1) * (y2 - y1)

                    if area > largest_area:
                        largest_area = area
                        largest_box = (x1, y1, x2, y2)
                        largest_class = names.get(class_ids[i], "Unknown")

        if largest_box:
            x1, y1, x2, y2 = largest_box
            midpoint_x = (x1 + x2) // 2
            midpoint_y = (y1 + y2) // 2

            # Update angle, distance
            self.angle, self.distance = self.convert_point_to_polar(midpoint_x, midpoint_y, largest_area)

            return largest_class, (midpoint_x, midpoint_y), frame, largest_area
        else:
            self.angle, self.distance = 0.0, 100.0  # Default values if no object is detected


        return None, None, frame, None

    def convert_point_to_polar(self, x, y, area):
        """
        Converts points on image to polar coordinates for spatial audio, with the center of the image as forward.
        fov = 90 degrees. Returns a tuple of (angle, distance), along with a loudness factor from 0 to 1 with 0 being loudest.
        :param x: x-coordinate of the object center (in pixels).
        :param y: y-coordinate of the object center (in pixels).
        :param area: Area of the bounding box (used to estimate distance).
        :return: A tuple (angle, distance, )
        """
        # Step 1: Calculate angle based on x-coordinate
        angle = -((x - self.image_width / 2) / (self.image_width / 2)) * (self.fov / 2)


        # Step 2: Calculate distance based on area of the bounding box
        distance = min(10, 300000 / area)  # Avoid division by zero, with minimum distance 0.1

        # Return the polar coordinates
        return angle, distance

    def start(self):
        """
        Starts the video feed and displays the detected largest object in a separate thread.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_detection)
            self.thread.daemon = True
            self.thread.start()
            print("Detection thread started.")
        else:
            print("Detection thread is already running.")


    def _run_detection(self):
        """
        The actual detection loop that runs in the background thread.
        """
        while self.running and self.cap.isOpened():
            largest_class, midpoint, frame, largest_area = self.detect_largest_object()

            if midpoint:
                x, y = midpoint
                angle, distance = self.convert_point_to_polar(x, y, largest_area)

                # Visual feedback on frame
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"{largest_class} A: {round(angle, 1)}, D: {round(distance, 3)}, A: {largest_area}", 
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                print(f"Largest Detected: {largest_class}, Midpoint: {angle}")
                print(f"Angle: {angle:.2f}, Distance: {distance:.2f}")

            cv2.imshow("YOLOv8 Largest Object Detection", frame)

            cv2.waitKey(1)

    def stop(self):
        """
        Stops the video feed and the detection thread.
        """
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.cap.release()
        cv2.destroyAllWindows()
        print("Video feed stopped and detection thread terminated.")

# Example usage
if __name__ == "__main__":
    import time
    detector = ObjectDetector()
    detector.start()
    time.sleep(10)
    detector.stop()
