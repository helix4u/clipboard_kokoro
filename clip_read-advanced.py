import pyperclip
import requests
import keyboard
from pydub import AudioSegment
import pyaudio
import io
import os
import sys

# Kokoro-FastAPI Configuration
API_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_sky+af+af_nicole"  # Replace with your desired voice
RESPONSE_FORMAT = "mp3"  # Audio format

# Global variable for selected audio output device
selected_device = None


def list_audio_devices():
    """List all available audio output devices."""
    p = pyaudio.PyAudio()
    print("\nAvailable Audio Devices:")
    for i in range(p.get_device_count()):
        info = p.get_device_info_by_index(i)
        if info["maxOutputChannels"] > 0:
            print(f"{i}: {info['name']}")
    p.terminate()


def play_audio(audio, device_id=None):
    """Play audio using pyaudio on a specified output device."""
    p = pyaudio.PyAudio()
    stream = None

    try:
        # Configure audio stream
        stream = p.open(
            format=pyaudio.paInt16,
            channels=audio.channels,
            rate=audio.frame_rate,
            output=True,
            output_device_index=device_id,
        )

        # Write audio data to stream
        stream.write(audio.raw_data)

    finally:
        if stream:
            stream.stop_stream()
            stream.close()
        p.terminate()


def save_audio_file(audio_content, filename="output.mp3"):
    """Save audio content to a file."""
    os.makedirs("saved_audio", exist_ok=True)  # Create a folder for audio files
    filepath = os.path.join("saved_audio", filename)
    with open(filepath, "wb") as f:
        f.write(audio_content)
    print(f"Audio saved to {filepath}")
    return filepath


def read_clipboard_aloud():
    global selected_device
    try:
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
                "response_format": RESPONSE_FORMAT,
                "speed": 1.3,
            },
        )
        if response.status_code != 200:
            print(f"Error: {response.json().get('message', 'Unknown error')}")
            return

        # Load audio and save locally
        audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        save_audio_file(response.content, filename="clipboard_output.mp3")

        # Play audio using the selected device
        play_audio(audio, device_id=selected_device)

    except Exception as e:
        print(f"An error occurred: {e}")


def close_program():
    """Close the program."""
    print("Exiting the program...")
    sys.exit(0)  # Exit immediately


def main():
    global selected_device
    print("ctrl+shift+space to read the clipboard aloud.")
    print("Shift+Esc to close the program.")

    # Ask if the user wants to select an output device
    use_default_device = input("Do you want to use the default audio device? (y/n): ").strip().lower()
    if use_default_device == "n":
        list_audio_devices()
        try:
            selected_device = int(input("\nEnter the ID of the audio device to use: ").strip())
            print(f"Selected audio device: {selected_device}")
        except ValueError:
            print("Invalid input. Using the default audio device.")
            selected_device = None

    # Register hotkeys
    keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
    keyboard.add_hotkey("shift+esc", close_program)

    try:
        keyboard.wait("shift+esc")  # Wait until the user exits
    except KeyboardInterrupt:
        close_program()


if __name__ == "__main__":
    main()
