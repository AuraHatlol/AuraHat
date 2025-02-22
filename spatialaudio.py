import numpy as np
import pyaudio
from scipy.signal import butter, lfilter
import threading

class SpatialAudio:
    def __init__(self, sample_rate=44100):
        """
        Initializes the spatial audio class.
        :param sample_rate: Sample rate of the audio (default is 44100 Hz).
        """
        self.sample_rate = sample_rate
        self.distance = 100.0
        self.angle = 0.0
        self.update_flag = False
        self.stream = None
        self.p = None
        self.audio_thread = None
        self.running = False

    def generate_sine_wave(self, freq, duration):
        """
        Generates a sine wave audio signal.
        :param freq: Frequency of the sine wave (in Hz).
        :param duration: Duration of the audio signal (in seconds).
        :return: The generated audio signal (numpy array).
        """
        t = np.linspace(0, duration, int(self.sample_rate * duration), False)
        tone = np.sin(freq * t * 2 * np.pi)
        return tone

    def adjust_audio(self, audio_signal, distance):
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
        b, a = butter(4, cutoff_freq / (self.sample_rate / 2), btype='low')  # Apply low-pass filter
        audio_signal = lfilter(b, a, audio_signal)

        return audio_signal

    def spatial_audio(self, audio_signal, angle):
        """
        Simulate spatial audio by adjusting the signal for left and right ears.
        :param audio_signal: The input audio signal (numpy array).
        :param angle: Angle of the sound source relative to the listener (in degrees, -180 to 180).
        :return: Stereo audio signal (left and right channels).
        """
        # Convert angle to radians
        angle_rad = np.radians(angle)
        
        # Calculate delay and volume differences
        max_delay = 0.001  # Maximum delay in seconds (1 ms)
        delay = max_delay * np.sin(angle_rad)  # Delay based on angle
        delay_samples = int(delay * self.sample_rate)
        
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

    def play_audio_continuously(self):
        """
        Continuously plays the audio with spatial effects based on distance and angle.
        Runs in a separate thread.
        """
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paFloat32,
                                  channels=2,  # Stereo audio
                                  rate=self.sample_rate,
                                  output=True,
                                  frames_per_buffer=1024)
        
        # Generate a 440 Hz sine wave
        audio_signal = self.generate_sine_wave(440, 0.1)  # Short buffer for real-time updates
        
        while self.running:
            # Adjust audio based on distance
            adjusted_audio = self.adjust_audio(audio_signal, self.distance)
            
            # Apply spatial audio effect
            stereo_audio = self.spatial_audio(adjusted_audio, self.angle)
            
            # Convert the audio signal to the correct format
            audio_data = stereo_audio.astype(np.float32).tobytes()
            
            # Write the audio data to the stream
            self.stream.write(audio_data)
            
            # Check if an update is needed
            if self.update_flag:
                self.update_flag = False

    def start(self):
        """
        Starts the audio playback in a separate thread.
        """
        if not self.running:
            self.running = True
            self.audio_thread = threading.Thread(target=self.play_audio_continuously)
            self.audio_thread.daemon = True
            self.audio_thread.start()
            print("Audio playback started.")
        else:
            print("Audio playback is already running.")

    def stop(self):
        """
        Stops the audio playback and terminates the thread.
        """
        self.running = False
        if self.audio_thread is not None:
            self.audio_thread.join()
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
        if self.p is not None:
            self.p.terminate()
        print("Audio playback stopped.")

    def update_audio_params(self, new_distance, new_angle):
        """
        Update the global distance and angle parameters.
        :param new_distance: New distance value (0 = closest, higher values = farther).
        :param new_angle: New angle value (-180 to 180 degrees, 0 = front).
        """
        self.distance = new_distance
        self.angle = new_angle


        self.update_flag = True

# Example usage
if __name__ == "__main__":
    spatial_audio = SpatialAudio()
    
    # Start the audio playback
    spatial_audio.start()
    
    # Update audio parameters
    spatial_audio.update_audio_params(2.0, 95)  # Update distance and angle after some time
    
    # Stop the audio playback after some time
    import time
    time.sleep(10)  # Let it play for 10 seconds
    spatial_audio.stop()
