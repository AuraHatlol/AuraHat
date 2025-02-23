import cv2
import torch
from ultralytics import YOLO
import numpy as np
import threading
from collections import deque

class ObjectDetector:
    def __init__(self, model_path='yolov8n.pt', device=None, fov=90, image_width=2048, image_height=840):
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

        # Define the classes to detect (person, chair, dining table)
        self.target_classes = {0: "person", 56: "chair", 60: "dining table"}

        # Confidence threshold for detection
        self.confidence_threshold = 0.5  # Only consider detections with confidence > 0.5

        # Temporal consistency check
        self.detection_history = deque(maxlen=10)  # Store last 10 frames of detections
        self.consistency_threshold = 5  # Object must be detected in at least 5 of the last 10 frames

    def detect_largest_object(self):
        """
        Detects the largest object in the current video frame and returns its midpoint and class.
        Only detects people, chairs, and tables.
        """
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to grab frame")
            return None, None, None

        # Run YOLO detection
        results = self.model(frame)

        largest_area = 0
        largest_box = None
        largest_class = None
        largest_confidence = 0.0

        for result in results:
            boxes = result.boxes

            if boxes is not None and hasattr(boxes, 'xyxy'):
                box_coords = boxes.xyxy.cpu().numpy()
                class_ids = boxes.cls.cpu().numpy().astype(int)
                confidences = boxes.conf.cpu().numpy()  # Confidence scores
                names = self.model.names  # COCO class names

                for i, box in enumerate(box_coords):
                    class_id = class_ids[i]
                    confidence = confidences[i]

                    if class_id in self.target_classes and confidence > self.confidence_threshold:
                        x1, y1, x2, y2 = map(int, box)
                        area = (x2 - x1) * (y2 - y1)

                        if area > largest_area:
                            largest_area = area
                            largest_box = (x1, y1, x2, y2)
                            largest_class = self.target_classes[class_id]
                            largest_confidence = confidence

        if largest_box:
            x1, y1, x2, y2 = largest_box
            midpoint_x = (x1 + x2) // 2
            midpoint_y = (y1 + y2) // 2

            # Calculate object size as a percentage of the frame area
            frame_area = self.image_width * self.image_height
            object_size_percentage = (largest_area / frame_area) * 100

            # Update angle and distance
            self.angle, self.distance = self.convert_point_to_polar(midpoint_x, midpoint_y, object_size_percentage)

            # Add detection to history
            self.detection_history.append((largest_class, midpoint_x, midpoint_y, object_size_percentage, largest_confidence))

            # Check temporal consistency
            if self.is_consistent_detection():
                return largest_class, (midpoint_x, midpoint_y), frame, object_size_percentage
        else:
            self.detection_history.append(None)  # No detection in this frame
            self.angle, self.distance = 0.0, 100.0  # Default values if no object is detected

        return None, None, frame, None

    def is_consistent_detection(self):
        """
        Checks if the object has been detected consistently over the last few frames.
        :return: True if the object is consistently detected, False otherwise.
        """
        if len(self.detection_history) < self.consistency_threshold:
            return False

        # Count how many times the object was detected in the last N frames
        detection_count = sum(1 for detection in self.detection_history if detection is not None)
        return detection_count >= self.consistency_threshold

    def convert_point_to_polar(self, x, y, object_size_percentage):
        """
        Converts points on image to polar coordinates for spatial audio, with the center of the image as forward.
        fov = 90 degrees. Returns a tuple of (angle, distance), where distance is based on object size percentage.
        :param x: x-coordinate of the object center (in pixels).
        :param y: y-coordinate of the object center (in pixels).
        :param object_size_percentage: Percentage of the frame area occupied by the object.
        :return: A tuple (angle, distance)
        """
        # Step 1: Calculate angle based on x-coordinate
        angle = -((x - self.image_width / 2) / (self.image_width / 2)) * (self.fov / 2)

        # Step 2: Calculate distance based on object size percentage
        # Smaller objects are farther away, larger objects are closer
        distance = max(0.1, 100 / object_size_percentage)  # Ensure distance is at least 0.1

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
            largest_class, midpoint, frame, object_size_percentage = self.detect_largest_object()

            if midpoint:
                x, y = midpoint
                angle, distance = self.convert_point_to_polar(x, y, object_size_percentage)

                # Visual feedback on frame
                cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
                cv2.putText(frame, f"{largest_class} A: {round(angle, 1)}, D: {round(distance, 3)}, Size: {round(object_size_percentage, 2)}%", 
                            (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

                print(f"Largest Detected: {largest_class}, Midpoint: {angle}")
                print(f"Angle: {angle:.2f}, Distance: {distance:.2f}, Size: {object_size_percentage:.2f}%")

            #cv2.imshow("YOLOv8 Largest Object Detection", frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to quit
                break

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
    time.sleep(10)  # Run detection for 10 seconds
    detector.stop()