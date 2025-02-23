import cv2
import torch
from ultralytics import YOLO
import numpy as np
import threading
from picamera2 import Picamera2

class ObjectDetector:
    def __init__(self, model_path='yolov8n.pt', device=None, fov=90, image_width=640, image_height=480):
        print("Initializing YOLO Model...")
        
        self.device = device if device else ("cuda" if torch.cuda.is_available() else "cpu")
        if self.device == "cuda":
            torch.cuda.set_device(0)
        
        print(f"Using device: {self.device}")
        
        self.model = YOLO(model_path).to(self.device)
    
        
        # Initialize Picamera2
        self.picam2 = Picamera2()
        self.picam2.preview_configuration.main.size = (image_width, image_height)
        self.picam2.preview_configuration.main.format = "RGB888"
        self.picam2.preview_configuration.controls.FrameRate = 30
        self.picam2.configure("preview")
        self.picam2.start()
        
        self.fov = fov
        self.image_width = image_width
        self.image_height = image_height
        
        self.angle = 0.0
        self.distance = 100.0
        
        self.thread = None
        self.running = False
    
    def detect_largest_object(self):
        frame = self.picam2.capture_array()
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)  # Convert to OpenCV format
        
        results = self.model(frame)
        
        largest_area = 25000
        largest_box = None
        largest_class = None
        
        valid_classes = {"person", "chair", "dining table"}
        
        for result in results:
            boxes = result.boxes
            if boxes is not None and hasattr(boxes, 'xyxy'):
                box_coords = boxes.xyxy.cpu().numpy()
                class_ids = boxes.cls.cpu().numpy().astype(int)
                confidences = boxes.conf.cpu().numpy()
                names = self.model.names
                
                for i, box in enumerate(box_coords):
                    x1, y1, x2, y2 = map(int, box)
                    area = (x2 - x1) * (y2 - y1)
                    class_name = names.get(class_ids[i], "Unknown")
                    confidence = confidences[i]
                    
                    if confidence > 0.8 and area > largest_area:
                        largest_area = area
                        largest_box = (x1, y1, x2, y2)
                        largest_class = class_name
        
        if largest_box:
            x1, y1, x2, y2 = largest_box
            midpoint_x = (x1 + x2) // 2
            midpoint_y = (y1 + y2) // 2
            
            self.angle, self.distance = self.convert_point_to_polar(midpoint_x, midpoint_y, largest_area)
            return largest_class, (midpoint_x, midpoint_y), frame, largest_area
        else:
            self.angle, self.distance = 0.0, 100.0
        
        return None, None, frame, None
    
    def convert_point_to_polar(self, x, y, area):
        angle = -((x - self.image_width / 2) / (self.image_width / 2)) * (self.fov / 2)
        distance = min(10, 300000 / area)  
        return angle, distance
    
    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_detection)
            self.thread.daemon = True
            self.thread.start()
            print("Detection thread started.")
        else:
            print("Detection thread is already running.")
    
    def _run_detection(self):
        while self.running:
            largest_class, midpoint, frame, largest_area = self.detect_largest_object()
            
            if midpoint:
                x, y = midpoint
                angle, distance = self.convert_point_to_polar(x, y, largest_area)
                
                # cv2.circle(frame, (x, y), 5, (0, 0, 255), -1)
                # cv2.putText(frame, f"{largest_class} A: {round(angle, 1)}, D: {round(distance, 3)}, A: {largest_area}", 
                #             (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                print(f"Largest Detected: {largest_class}, Midpoint: {angle}")
                print(f"Angle: {angle:.2f}, Distance: {distance:.2f}")
            
            #cv2.imshow("YOLOv8 Largest Object Detection", frame)
            cv2.waitKey(1)
    
    def stop(self):
        self.running = False
        if self.thread is not None:
            self.thread.join()
        self.picam2.stop()
        cv2.destroyAllWindows()
        print("Video feed stopped and detection thread terminated.")

if __name__ == "__main__":
    import time
    detector = ObjectDetector()
    detector.start()
    time.sleep(10)
    detector.stop()