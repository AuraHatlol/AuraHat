import threading
import time
from raspberry.detector import ObjectDetector  # Import the object detector class
from spatialaudio import SpatialAudio  # Import the spatial audio class
from raspberry.distance import UltrasonicSensor  # Import the distance sensor class

class AuraHat:
    def __init__(self):
        self.objectdetector = ObjectDetector(fov=60)  # Object detection instance
        self.spatialaudio = SpatialAudio()  # Spatial audio instance
        self.distance_sensor = UltrasonicSensor(trigger_pin=23, echo_pin=24)  # Distance sensor instance
        self.running = False  # Flag to indicate if the system is running
        self.audio_thread = None  # The thread for running spatial audio updates

    def update_spatial_audio(self):
        """
        Continuously update the spatial audio based on object detection.
        Runs in a separate thread to update the audio parameters in real-time.
        """
        while self.running:
            newdistance = min(self.distance_sensor.distance / 10, self.objectdetector.distance)
            newangle = self.objectdetector.angle * 1.5
            print(newdistance, newangle)
            self.spatialaudio.update_audio_params(newdistance, newangle)  # Update the spatial audio parameters
                
            # Delay before the next update
            time.sleep(0.1)  # Adjust the sleep duration to control the update frequency

    def start(self):
        """
        Starts the object detection and spatial audio update in a separate thread.
        Initializes the necessary hardware (LEDs, sensors, speakers).
        """
        if not self.running:
            self.running = True

            self.objectdetector.start()
            self.spatialaudio.start()
            self.distance_sensor.start()
            
            self.audio_thread = threading.Thread(target=self.update_spatial_audio)
            self.audio_thread.daemon = True  # Daemonize the thread to ensure it ends when the program exits
            self.audio_thread.start()

            print("AuraHat system started.")

    def stop(self):
        """
        Stops the object detection and spatial audio updates.
        Cleans up resources.
        """
        self.running = False

        # Stop the audio thread and spatial audio playback
        if self.audio_thread is not None:
            self.audio_thread.join()
        if self.distance_thread is not None:
            self.distance_thread.join()

        self.objectdetector.stop()
        self.spatialaudio.stop()
        self.distancesensor.stop()

        print("AuraHat system stopped.")

# Example usage
if __name__ == "__main__":
    aurahat = AuraHat()
    
    # Start the system (detection and spatial audio update in a thread)
    aurahat.start()



    # Run for a while (e.g., 30 seconds) before stopping
    time.sleep(90)  # Adjust the duration as needed
    aurahat.stop()
