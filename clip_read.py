import pyperclip
import requests
import keyboard
from pydub import AudioSegment
from pydub.playback import play
import io

# Kokoro-FastAPI Configuration
API_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_sky+af_bella"  # Replace with your desired voice
RESPONSE_FORMAT = "mp3"  # Audio format

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
        
        # Play the generated audio
        audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        play(audio)
        
    except Exception as e:
        print(f"An error occurred: {e}")

def main():
    print("ctrl+shift+space to read the clipboard aloud.")
    keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
    keyboard.wait("esc")  # Wait for the user to press ESC to exit

if __name__ == "__main__":
    main()
