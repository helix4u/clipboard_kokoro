import pyperclip
import requests
import keyboard
from pydub import AudioSegment
from pydub.playback import play  # Properly import the play function
import io
import sounddevice as sd
import numpy as np
import threading
import os
import sys

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


def play_on_device(audio, device_id):
    """Play audio on a specific device using sounddevice."""
    audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32) / (2**15)
    audio_format = audio.frame_rate
    audio_channels = audio.channels

    device_info = sd.query_devices(device_id)
    device_sample_rate = int(device_info["default_samplerate"])

    if audio_format != device_sample_rate:
        print(f"Resampling audio from {audio_format} Hz to {device_sample_rate} Hz")
        audio_array = resample_audio(audio_array, audio_format, device_sample_rate)
        audio_format = device_sample_rate

    with sd.OutputStream(
        samplerate=audio_format,
        device=device_id,
        channels=audio_channels,
        dtype="float32",
        blocksize=2048,
    ) as stream:
        for chunk in np.array_split(audio_array, len(audio_array) // 2048):
            if exit_event.is_set():  # Stop playback if exit event is triggered
                break
            stream.write(chunk)


def resample_audio(audio_array, input_rate, output_rate):
    """Resample audio to match the output device's sample rate."""
    from scipy.signal import resample

    num_samples = int(len(audio_array) * (output_rate / input_rate))
    return resample(audio_array, num_samples)


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
            if selected_device is not None:
                play_on_device(audio, selected_device)
            else:
                play(audio)

        playback_thread = threading.Thread(target=playback, daemon=True)
        playback_thread.start()

    except Exception as e:
        print(f"An error occurred: {e}")


def close_program():
    """Close the program safely."""
    global playback_thread
    print("Exiting the program...")
    exit_event.set()  # Signal all threads to exit

    # Ensure playback thread is terminated
    if playback_thread and playback_thread.is_alive():
        playback_thread.join(timeout=1)

    # If playback thread hangs, forcefully terminate the process
    os._exit(0)


def main():
    global selected_device
    print("ctrl+shift+space to read the clipboard aloud.")
    print("Shift+Esc to close the program.")

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
