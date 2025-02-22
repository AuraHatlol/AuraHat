import numpy as np
import pyaudio
from scipy.signal import butter, lfilter
import threading

# Global variables for distance and angle
distance = 1.0
angle = 0.0
update_flag = False

# Step 1: Generate a sine wave
def generate_sine_wave(freq, duration, sample_rate=44100):
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    tone = np.sin(freq * t * 2 * np.pi)
    return tone

# Step 2: Adjust volume and frequency based on distance
def adjust_audio(audio_signal, distance):
    """
    Adjust audio properties based on distance.
    :param audio_signal: The input audio signal (numpy array).
    :param distance: Distance factor (larger values = farther away).
    :return: Adjusted audio signal.
    """
    # Volume adjustment
    volume = 1 / (1 + distance)  # Reduce volume as distance increases
    audio_signal = audio_signal * volume

    # High-frequency attenuation
    cutoff_freq = 4000 / (1 + distance)  # Reduce high frequencies as distance increases
    b, a = butter(4, cutoff_freq / (44100 / 2), btype='low')  # Apply low-pass filter
    audio_signal = lfilter(b, a, audio_signal)

    return audio_signal

# Step 3: Create spatial audio effect
def spatial_audio(audio_signal, angle, sample_rate=44100):
    """
    Simulate spatial audio by adjusting the signal for left and right ears.
    :param audio_signal: The input audio signal (numpy array).
    :param angle: Angle of the sound source relative to the listener (in degrees, -180 to 180).
    :param sample_rate: Sample rate of the audio signal.
    :return: Stereo audio signal (left and right channels).
    """
    # Convert angle to radians
    angle_rad = np.radians(angle)
    
    # Calculate delay and volume differences
    max_delay = 0.001  # Maximum delay in seconds (1 ms)
    delay = max_delay * np.sin(angle_rad)  # Delay based on angle
    delay_samples = int(delay * sample_rate)
    
    # Create left and right channels
    left_channel = np.roll(audio_signal, -delay_samples)
    right_channel = np.roll(audio_signal, delay_samples)
    
    # Adjust volume based on angle
    # For sounds behind the listener, reduce volume further
    if abs(angle) > 90:
        rear_attenuation = 0.5  # Reduce volume for sounds behind
    else:
        rear_attenuation = 1.0
    
    left_volume = np.cos((angle_rad - np.pi/2) / 2) * rear_attenuation
    right_volume = np.cos((angle_rad + np.pi/2) / 2) * rear_attenuation
    
    left_channel *= left_volume
    right_channel *= right_volume
    
    # Combine into stereo signal
    stereo_signal = np.column_stack((left_channel, right_channel))
    
    return stereo_signal

# Step 4: Continuously play audio
def play_audio_continuously(sample_rate=44100):
    global distance, angle, update_flag
    
    p = pyaudio.PyAudio()
    stream = p.open(format=pyaudio.paFloat32,
                    channels=2,  # Stereo audio
                    rate=sample_rate,
                    output=True,
                    frames_per_buffer=1024)
    
    # Generate a 440 Hz sine wave
    audio_signal = generate_sine_wave(440, 0.1)  # Short buffer for real-time updates
    
    while True:
        # Adjust audio based on distance
        adjusted_audio = adjust_audio(audio_signal, distance)
        
        # Apply spatial audio effect
        stereo_audio = spatial_audio(adjusted_audio, angle)
        
        # Convert the audio signal to the correct format
        audio_data = stereo_audio.astype(np.float32).tobytes()
        
        # Write the audio data to the stream
        stream.write(audio_data)
        
        # Check if an update is needed
        if update_flag:
            update_flag = False

# Step 5: Handle user input
def user_input_thread():
    global distance, angle, update_flag
    
    while True:
        try:
            new_distance = 1
            new_angle = angle + 0.05
            if angle > 360:
                angle = 0
                new_angle = 0
            print(new_angle)
            # Update global variables
            distance = new_distance
            angle = new_angle
            update_flag = True
        except ValueError:
            print("Invalid input. Please enter numeric values.")

# Main function
def main():
    # Start the audio playback thread
    audio_thread = threading.Thread(target=play_audio_continuously)
    audio_thread.daemon = True  # Daemonize thread to exit when the main program exits
    audio_thread.start()
    
    # Start the user input thread
    input_thread = threading.Thread(target=user_input_thread)
    input_thread.daemon = True
    input_thread.start()
    
    # Keep the main program running
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting...")

# Run the main function
main()