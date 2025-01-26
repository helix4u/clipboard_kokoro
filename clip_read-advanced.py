import pyperclip
import requests
import keyboard
from pydub import AudioSegment
import io
import threading
import os
import sys
import sounddevice as sd
import numpy as np

# Kokoro-FastAPI Configuration
API_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_sky+af+af_nicole"  # Replace with your desired voice
RESPONSE_FORMAT = "mp3"  # Audio format

# Global variables for playback management
selected_device = None
playback_thread = None
exit_event = threading.Event()  # Used to signal threads to exit


def list_audio_devices():
    """List all audio output devices."""
    print("\nAvailable Audio Devices:")
    devices = sd.query_devices()
    output_devices = {idx: device for idx, device in enumerate(devices) if device['max_output_channels'] > 0}
    for idx, device in output_devices.items():
        print(f"{idx}: {device['name']}")
    return output_devices


def play_audio(audio, device_id=None):
    """Play audio using the selected device."""
    try:
        # Convert audio to NumPy array
        audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32) / (2**15)
        audio_format = audio.frame_rate
        audio_channels = audio.channels

        # Configure the sounddevice stream
        with sd.OutputStream(
            samplerate=audio_format,
            device=device_id,
            channels=audio_channels,
            dtype="float32",
            blocksize=2048
        ) as stream:
            # Write audio data to the stream
            stream.write(audio_array)

    except Exception as e:
        print(f"Error playing audio on device {device_id}: {e}")


def save_audio_file(audio_content, filename="output.mp3"):
    """Save audio content to a file."""
    os.makedirs("saved_audio", exist_ok=True)  # Create a folder for audio files
    filepath = os.path.join("saved_audio", filename)
    with open(filepath, "wb") as f:
        f.write(audio_content)
    print(f"Audio saved to {filepath}")
    return filepath


def read_clipboard_aloud():
    global playback_thread
    try:
        if exit_event.is_set():
            return

        clipboard_content = pyperclip.paste()
        if not clipboard_content.strip():
            print("Clipboard is empty.")
            return
        clipboard_content = clipboard_content.replace("*", "").replace("#", "")

        print(f"Reading aloud: {clipboard_content}")

        response = requests.post(
            API_URL,
            json={
                "input": clipboard_content,
                "voice": VOICE,
                "response_format": RESPONSE_FORMAT,
                "speed": 1.3,
            },
        )
        if response.status_code != 200:
            print(f"Error: {response.json().get('message', 'Unknown error')}")
            return

        audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        save_audio_file(response.content, filename="clipboard_output.mp3")

        def playback():
            play_audio(audio, device_id=selected_device)

        playback_thread = threading.Thread(target=playback, daemon=True)
        playback_thread.start()

    except Exception as e:
        print(f"An error occurred: {e}")


def close_program():
    """Close the program safely."""
    global playback_thread
    print("Exiting the program...")
    exit_event.set()  # Signal all threads to exit

    if playback_thread and playback_thread.is_alive():
        playback_thread.join(timeout=1)

    os._exit(0)  # Forcefully terminate the program


def main():
    global selected_device
    print("Ctrl+Shift+Space to read the clipboard aloud.")
    print("Shift+Esc to close the program.")

    # Ask user whether to select a specific device
    use_default_device = input("Do you want to use the default audio device? (y/n): ").strip().lower()
    if use_default_device == "n":
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

    keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
    keyboard.add_hotkey("shift+esc", close_program)

    try:
        while not exit_event.is_set():
            pass  # Keep the program running
    except KeyboardInterrupt:
        close_program()


if __name__ == "__main__":
    main()
