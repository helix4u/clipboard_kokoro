# Clipboard-to-Speech Tool

This script utilizes the Kokoro-FastAPI to read the clipboard content aloud with a customizable voice or a combination of voices. It listens for a hotkey press (`Ctrl+Shift+Space`) to trigger the text-to-speech process.

## Features
- Reads the current clipboard content aloud.
- **Pause/Resume**: Press the hotkey again while playing to pause, press again to resume.
- **Stop Playback**: Press `Escape` to completely stop current playback.
- Supports combined voices (e.g., `af_sky+af_bella`).
- Configurable hotkey (`Ctrl+Shift+Space` by default).
- Supports multiple audio formats (`mp3` by default).
- Audio device selection on startup.

## How It Works
1. **Clipboard Access**: The script uses `pyperclip` to read text from the clipboard.
2. **Text-to-Speech**: The clipboard content is sent to Kokoro-FastAPI for speech generation.
3. **Audio Playback**: The generated audio is played immediately using `sounddevice` with pause/resume support.
4. **Playback Control**: Audio is played in chunks, allowing for responsive pause/resume/stop functionality.

## Requirements
Install the required Python libraries:
```bash
pip install pyperclip requests keyboard pydub sounddevice numpy
```
Your mileage may vary depending on OS, package updates etc. If you have missing modules after install, you can pip install them normally. This is a very basic script that doesn't require much beyond https://github.com/remsky/Kokoro-FastAPI.

Ensure that:
- The Kokoro-FastAPI service is running locally or is accessible at the configured `API_URL`.
- Your desired voice packs are installed and available in Kokoro-FastAPI.

## Usage
1. Run the script:
   ```bash
   python clip_read.py
   ```
2. Choose your audio output device (default or select from list).
3. Copy any text to your clipboard.
4. Press `Ctrl+Shift+Space` to hear the clipboard content read aloud.
5. **Control playback**:
   - Press `Ctrl+Shift+Space` again to **pause** playback
   - Press `Ctrl+Shift+Space` again to **resume** from where you paused
   - Press `Escape` to **stop** playback completely
6. Press `Shift+Esc` to exit the program.

## Configuration
### Kokoro-FastAPI Settings
Update the following parameters in the script to customize behavior:
- **`API_URL`**: URL of the Kokoro-FastAPI server (default: `http://localhost:8880/v1/audio/speech`).
- **`VOICE`**: Set to a single voice or combine multiple voices with a `+` (e.g., `af_sky+af_bella`).
- **`RESPONSE_FORMAT`**: Choose the desired audio format (e.g., `mp3`, `wav`).

### Hotkeys
The default hotkeys are:
- `Ctrl+Shift+Space`: Read clipboard / Pause / Resume playback
- `Escape`: Stop current playback
- `Shift+Esc`: Exit program

You can modify them in the following lines:
```python
keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
keyboard.add_hotkey("esc", stop_playback)
keyboard.add_hotkey("shift+esc", close_program)
```

## Example
For a combined voice configuration:
```python
VOICE = "af_sky+af_bella"  # Combines two voices
```

To run the script, copy some text to the clipboard, press `Ctrl+Shift+Space`, and enjoy the audio playback with full pause/resume control.

## Notes
- If the clipboard is empty or contains non-text content, the script will notify you and do nothing.
- Ensure Kokoro-FastAPI is running and accessible before running the script.
- The script automatically saves generated audio files to the `saved_audio/` directory.
- Audio device selection is available on startup for better compatibility.

## Playback Controls
- **Toggle Playback**: `Ctrl+Shift+Space` acts as a smart toggle - starts playback if nothing is playing, pauses if playing, resumes if paused.
- **Stop Playback**: `Escape` completely stops current playback (cannot resume from this point).
- **Exit Program**: `Shift+Esc` terminates the program and all playback.

## Support

If the tool is helpful, consider supporting it on [Ko-fi](https://ko-fi.com/gille).
