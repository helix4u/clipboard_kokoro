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
import time

# Configuration for Kokoro-FastAPI TTS endpoint
API_URL = "http://localhost:8880/v1/audio/speech"
VOICE = "af_sky+af+af_nicole"   # Change to your preferred voice
RESPONSE_FORMAT = "mp3"         # Audio format for output

# Global variables for managing audio playback and shutdown
selected_device = None          # Currently chosen output device index (None = default)
playback_thread = None          # Thread handle for audio playback
exit_event = threading.Event()  # Signals the main loop and threads to exit

# Playback control variables
is_playing = False              # Whether audio is currently playing
is_paused = False               # Whether audio is currently paused
current_audio = None            # Current audio segment being played
playback_lock = threading.Lock() # Lock for thread-safe playback control

def list_audio_devices():
    """
    List all available audio output devices.
    Returns a dictionary mapping device IDs to device info.
    """
    print("\nAvailable Audio Devices:")
    devices = sd.query_devices()
    output_devices = {idx: device for idx, device in enumerate(devices) if device['max_output_channels'] > 0}
    for idx, device in output_devices.items():
        print(f"{idx}: {device['name']}")
    return output_devices

def get_valid_device_id(device_id):
    """
    Check if the given device ID is valid (present and enabled) at the moment.
    Returns device_id if valid, otherwise None (falls back to default device).
    """
    try:
        devices = sd.query_devices()
        output_devices = [idx for idx, device in enumerate(devices) if device['max_output_channels'] > 0]
        if device_id in output_devices:
            return device_id
        else:
            print(f"Selected device {device_id} not available. Using default.")
            return None
    except Exception as e:
        print(f"Device validation error: {e}")
        return None

def play_audio(audio, device_id=None):
    """
    Play audio using the specified output device with pause/resume support.
    If device is unavailable, fallback to default. Handles device errors gracefully.
    """
    global is_playing, is_paused, current_audio
    
    try:
        with playback_lock:
            current_audio = audio
            is_playing = True
            is_paused = False
        
        # Convert pydub audio to numpy float32 array, normalizing from int16
        audio_array = np.array(audio.get_array_of_samples(), dtype=np.float32) / (2**15)
        audio_format = audio.frame_rate
        audio_channels = audio.channels

        # Validate device at playback time to handle hotplug/removal
        valid_device_id = get_valid_device_id(device_id)

        # Try playing audio with pause/resume support, catch and recover from device errors
        try:
            with sd.OutputStream(
                samplerate=audio_format,
                device=valid_device_id,
                channels=audio_channels,
                dtype="float32",
                blocksize=2048
            ) as stream:
                # Play audio in chunks to support pause/resume
                chunk_size = 2048
                for i in range(0, len(audio_array), chunk_size):
                    # Check for pause/resume/stop conditions
                    with playback_lock:
                        if not is_playing:  # Stop requested
                            break
                        if is_paused and is_playing:  # Paused
                            # Release the lock and wait for resume
                            pass
                    
                    # If paused, wait in a loop until resumed or stopped
                    while True:
                        with playback_lock:
                            if not is_playing:  # Stop requested
                                break
                            if not is_paused:  # Resume requested
                                break
                        # Small sleep to avoid busy waiting
                        time.sleep(0.01)
                    
                    if not is_playing:  # Stop was requested during pause
                        break
                        
                    chunk = audio_array[i:i+chunk_size]
                    if len(chunk) > 0:
                        stream.write(chunk)
                        
        except Exception as device_exc:
            # Device error fallback: try system default
            if valid_device_id is not None:
                print(f"Playback failed on device {valid_device_id}: {device_exc}. Falling back to default output device.")
                try:
                    with sd.OutputStream(
                        samplerate=audio_format,
                        device=None,
                        channels=audio_channels,
                        dtype="float32",
                        blocksize=2048
                    ) as stream:
                        # Play audio in chunks to support pause/resume
                        chunk_size = 2048
                        for i in range(0, len(audio_array), chunk_size):
                            # Check for pause/resume/stop conditions
                            with playback_lock:
                                if not is_playing:  # Stop requested
                                    break
                                if is_paused and is_playing:  # Paused
                                    # Release the lock and wait for resume
                                    pass
                            
                            # If paused, wait in a loop until resumed or stopped
                            while True:
                                with playback_lock:
                                    if not is_playing:  # Stop requested
                                        break
                                    if not is_paused:  # Resume requested
                                        break
                                # Small sleep to avoid busy waiting
                                time.sleep(0.01)
                            
                            if not is_playing:  # Stop was requested during pause
                                break
                                
                            chunk = audio_array[i:i+chunk_size]
                            if len(chunk) > 0:
                                stream.write(chunk)
                except Exception as fallback_exc:
                    print(f"Playback failed on default device as well: {fallback_exc}")
            else:
                print(f"Playback failed on default device: {device_exc}")
        
        # Reset playback state when done
        with playback_lock:
            is_playing = False
            is_paused = False
            current_audio = None

    except Exception as e:
        print(f"Error preparing or playing audio: {e}")
        with playback_lock:
            is_playing = False
            is_paused = False
            current_audio = None

def save_audio_file(audio_content, filename="output.mp3"):
    """
    Save binary audio content to a file inside ./saved_audio/
    """
    os.makedirs("saved_audio", exist_ok=True)
    filepath = os.path.join("saved_audio", filename)
    try:
        with open(filepath, "wb") as f:
            f.write(audio_content)
        print(f"Audio saved to {filepath}")
        return filepath
    except Exception as e:
        print(f"Failed to save audio file: {e}")
        return None

def read_clipboard_aloud():
    """
    Reads text from the clipboard, converts it to speech using TTS API,
    plays it on the chosen output device, and saves the audio file.
    If audio is already playing, pauses/resumes it instead.
    """
    global playback_thread, is_playing, is_paused
    
    try:
        if exit_event.is_set():
            return

        # Check if audio is currently playing
        with playback_lock:
            if is_playing:
                if is_paused:
                    # Resume playback
                    is_paused = False
                    print("Resuming playback...")
                else:
                    # Pause playback
                    is_paused = True
                    print("Pausing playback...")
                return

        clipboard_content = pyperclip.paste()
        if not clipboard_content or not clipboard_content.strip():
            print("Clipboard is empty.")
            return

        # Clean up clipboard content (optional: adjust for your needs)
        clipboard_content = clipboard_content.replace("*", "").replace("#", "")
        print(f"Reading aloud: {clipboard_content}")

        # Make TTS API request
        response = requests.post(
            API_URL,
            json={
                "input": clipboard_content,
                "voice": VOICE,
                "response_format": RESPONSE_FORMAT,
                "speed": 1.75,
            },
        )

        if response.status_code != 200:
            try:
                print(f"Error: {response.json().get('message', 'Unknown error')}")
            except Exception:
                print(f"API Error: Status {response.status_code}")
            return

        # Load and re-export MP3 to sanitize headers/metadata
        audio = AudioSegment.from_file(io.BytesIO(response.content), format="mp3")
        os.makedirs("saved_audio", exist_ok=True)
        fixed_audio_path = os.path.join("saved_audio", "clipboard_output_fixed.mp3")
        audio.export(fixed_audio_path, format="mp3", bitrate="160k")
        print(f"Audio saved to {fixed_audio_path}")

        # Spawn playback in a background thread
        def playback():
            play_audio(audio, device_id=selected_device)

        playback_thread = threading.Thread(target=playback, daemon=True)
        playback_thread.start()

    except Exception as e:
        print(f"An error occurred in read_clipboard_aloud: {e}")

def stop_playback():
    """
    Stop current audio playback.
    """
    global is_playing, is_paused
    
    with playback_lock:
        if is_playing:
            is_playing = False
            is_paused = False
            print("Stopping playback...")
        else:
            print("No audio is currently playing.")

def close_program():
    """
    Gracefully exit the program, terminating any active playback threads.
    """
    global playback_thread
    print("Exiting the program...")
    exit_event.set()  # Notify main loop and playback threads to stop

    if playback_thread and playback_thread.is_alive():
        playback_thread.join(timeout=1)  # Wait for thread to exit

    os._exit(0)  # Force exit, guarantees hotkeys and threads are killed

def main():
    """
    Main entry point. Handles device selection, hotkey binding, and main event loop.
    """
    global selected_device

    print("Ctrl+Shift+Space to read the clipboard aloud (or pause/resume if playing).")
    print("Escape to stop current playback.")
    print("Shift+Esc to close the program.")

    # Device selection prompt
    try:
        use_default_device = input("Do you want to use the default audio device? (y/n): ").strip().lower()
    except Exception:
        use_default_device = "y"  # If stdin fails (rare, but possible)

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
        except Exception:
            print("Invalid input. Default audio device will be used.")
            selected_device = None

    # Hotkey bindings
    keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
    keyboard.add_hotkey("esc", stop_playback)
    keyboard.add_hotkey("shift+esc", close_program)

    # Main program loop. Stays alive until exit_event is set.
    try:
        while not exit_event.is_set():
            # Wait for any registered hotkey to be pressed
            keyboard.wait()  # This will wait for any registered hotkey
    except KeyboardInterrupt:
        close_program()
    except Exception as main_exc:
        print(f"Main loop error: {main_exc}")
        close_program()

if __name__ == "__main__":
    main()
