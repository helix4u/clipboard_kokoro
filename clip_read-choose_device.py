import pyperclip
import requests
import keyboard
from pydub import AudioSegment
from pydub.playback import play
import io
import sounddevice as sd
import numpy as np

# Kokoro-FastAPI Configuration
API_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_sky+af_bella"  # Replace with your desired voice
RESPONSE_FORMAT = "mp3"  # Audio format

# Global variable for the selected audio device
selected_device = None

def list_audio_devices():
    """List all audio output devices."""
    print("\nAvailable Audio Devices:")
    devices = sd.query_devices()
    output_devices = {idx: device for idx, device in enumerate(devices) if device['max_output_channels'] > 0}
    for idx, device in output_devices.items():
        print(f"{idx}: {device['name']}")
    return output_devices

def play_on_device(audio, device_id):
    """Play audio on a specific device."""
    # Convert audio to a NumPy array and normalize it to range [-1.0, 1.0]
    audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32) / (2 ** 15)
    
    # Set audio playback settings
    audio_format = audio.frame_rate
    audio_channels = audio.channels

    # Configure the sounddevice stream to use the specified device
    with sd.OutputStream(
        samplerate=audio_format,
        device=device_id,
        channels=audio_channels,
        dtype='float32'
    ) as stream:
        stream.write(audio_array)

def read_clipboard_aloud():
    try:
        # Get clipboard content
        clipboard_content = pyperclip.paste()
        if not clipboard_content.strip():
            print("Clipboard is empty.")
            return
        
        print(f"Reading aloud: {clipboard_content}")
        
        # Send text to Kokoro API for speech generation
        response = requests.post(
            API_URL,
            json={
                "input": clipboard_content,
                "voice": VOICE,
                "response_format": RESPONSE_FORMAT
            }
        )
        if response.status_code != 200:
            print(f"Error: {response.json().get('message', 'Unknown error')}")
            return
        
        # Load audio for playback
        audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        
        # Play audio on the selected device or default
        if selected_device is not None:
            play_on_device(audio, selected_device)
        else:
            play(audio)
        
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    global selected_device
    print("ctrl+shift+space to read the clipboard aloud.")
    
    # Ask user whether to use the default or a specified device
    use_default_device = input("Do you want to use the default audio device? (y/n): ").strip().lower()
    if use_default_device == 'n':
        available_devices = list_audio_devices()
        try:
            device_id = int(input("\nEnter the ID of the audio device to use: ").strip())
            if device_id in available_devices:
                selected_device = device_id
                print(f"Audio device set to: {available_devices[device_id]['name']}")
            else:
                print("Invalid device ID. Default audio device will be used.")
                selected_device = None
        except ValueError:
            print("Invalid input. Default audio device will be used.")
            selected_device = None
    
    # Add hotkey for reading clipboard aloud
    keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
    keyboard.wait("Shift+esc")  # Wait for the user to press ESC to exit

if __name__ == "__main__":
    main()
