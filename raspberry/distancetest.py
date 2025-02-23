import RPi.GPIO as GPIO
import time

TRIG = 23
ECHO = 24

GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

GPIO.output(TRIG, False)
print("Waiting for sensor to settle...")
time.sleep(2)

print("Sending test pulse...")
GPIO.output(TRIG, True)
time.sleep(0.00001)
GPIO.output(TRIG, False)

# Check if Echo responds
start_time = time.time()
timeout = start_time + 2  # 2-second timeout

while GPIO.input(ECHO) == 0:
    if time.time() > timeout:
        print("ECHO pin never went HIGH. Check wiring.")
        GPIO.cleanup()
        exit()

print("ECHO detected. Sensor is responding.")
GPIO.cleanup()
