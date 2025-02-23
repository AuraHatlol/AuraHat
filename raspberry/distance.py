import RPi.GPIO as GPIO
import time
import threading

class UltrasonicSensor:
    def __init__(self, trigger_pin, echo_pin):
        """
        Initializes the ultrasonic sensor with the specified GPIO pins.
        :param trigger_pin: GPIO pin connected to the sensor's trigger.
        :param echo_pin: GPIO pin connected to the sensor's echo.
        """
        self.TRIG = trigger_pin
        self.ECHO = echo_pin
        self.distance = 10000.0
        self.running = False
        self.thread = None
        
        # Setup GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.TRIG, GPIO.OUT)
        GPIO.setup(self.ECHO, GPIO.IN)

    def measure_distance(self):
        """
        Measures the distance using the ultrasonic sensor.
        """
        # Ensure trigger is low
        GPIO.output(self.TRIG, False)
        time.sleep(0.1)

        # Send a 10µs pulse to trigger
        GPIO.output(self.TRIG, True)
        time.sleep(0.00001)  # 10 microseconds
        GPIO.output(self.TRIG, False)

        # Wait for echo response
        pulse_start = time.time()
        while GPIO.input(self.ECHO) == 0:
            pulse_start = time.time()
        
        pulse_end = time.time()
        while GPIO.input(self.ECHO) == 1:
            pulse_end = time.time()

        # Calculate time difference
        pulse_duration = pulse_end - pulse_start

        # Convert to distance (Speed of sound = 34300 cm/s)
        self.distance = round(pulse_duration * 17150, 2)  # Convert to cm
        if self.distance > 400:
            self.distance = 10000.0

    def _run(self):
        """
        Continuously measures distance in a separate thread.
        """
        while self.running:
            self.measure_distance()
            time.sleep(0.2)  # Delay between readings

    def start(self):
        """
        Starts the distance measurement in a separate thread.
        """
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run)
            self.thread.daemon = True
            self.thread.start()
            print("Ultrasonic sensor thread started.")

    def stop(self):
        """
        Stops the distance measurement thread.
        """
        self.running = False
        if self.thread:
            self.thread.join()
        print("Ultrasonic sensor thread stopped.")

    def cleanup(self):
        """
        Cleans up the GPIO pins.
        """
        GPIO.cleanup()

# Example usage
if __name__ == "__main__":
    try:
        sensor = UltrasonicSensor(trigger_pin=23, echo_pin=24)
        sensor.start()
        
        while True:
            print(f"Distance: {sensor.distance} cm")
            time.sleep(0.2)  # Main thread delay

    except KeyboardInterrupt:
        print("Measurement stopped by user")
        sensor.stop()
        sensor.cleanup()
