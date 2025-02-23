import RPi.GPIO as GPIO
import time

# Define GPIO pins
TRIG = 23  # Trigger pin
ECHO = 24  # Echo pin

# Setup GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

def measure_distance():
    # Ensure trigger is low
    GPIO.output(TRIG, False)
    time.sleep(0.1)

    # Send a 10µs pulse to trigger
    GPIO.output(TRIG, True)
    time.sleep(0.00001)  # 10 microseconds
    GPIO.output(TRIG, False)

    # Wait for echo response
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
    
    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()

    # Calculate time difference
    pulse_duration = pulse_end - pulse_start

    # Convert to distance (Speed of sound = 34300 cm/s)
    distance = pulse_duration * 17150  # Convert to cm
    distance = round(distance, 2)  # Round to two decimal places

    return distance

try:
    while True:
        dist = measure_distance()
        print(f"Distance: {dist} cm")
        time.sleep(1)  # Delay between readings

except KeyboardInterrupt:
    print("Measurement stopped by user")
    GPIO.cleanup()  # Cleanup GPIO on exit
