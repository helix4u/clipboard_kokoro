# Clipboard-to-Speech Tool

This script utilizes the Kokoro-FastAPI to read the clipboard content aloud with a customizable voice or a combination of voices. It listens for a hotkey press (`Ctrl+Shift+Space`) to trigger the text-to-speech process.

## Features
- Reads the current clipboard content aloud.
- Supports combined voices (e.g., `af_sky+af_bella`).
- Configurable hotkey (`Ctrl+Shift+Space` by default).
- Supports multiple audio formats (`mp3` by default).

## How It Works
1. **Clipboard Access**: The script uses `pyperclip` to read text from the clipboard.
2. **Text-to-Speech**: The clipboard content is sent to Kokoro-FastAPI for speech generation.
3. **Audio Playback**: The generated audio is played immediately using `pydub`.

## Requirements
Install the required Python libraries:
```bash
pip install pyperclip requests keyboard pydub
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
2. Copy any text to your clipboard.
3. Press `Ctrl+Shift+Space` to hear the clipboard content read aloud.
4. Press `ESC` to exit the program.

## Configuration
### Kokoro-FastAPI Settings
Update the following parameters in the script to customize behavior:
- **`API_URL`**: URL of the Kokoro-FastAPI server (default: `http://localhost:8880/v1/audio/speech`).
- **`VOICE`**: Set to a single voice or combine multiple voices with a `+` (e.g., `af_sky+af_bella`).
- **`RESPONSE_FORMAT`**: Choose the desired audio format (e.g., `mp3`, `wav`).

### Hotkey
The default hotkey to trigger the tool is `Ctrl+Shift+Space`. You can modify it in the following line:
```python
keyboard.add_hotkey("ctrl+shift+space", read_clipboard_aloud)
```

## Example
For a combined voice configuration:
```python
VOICE = "af_sky+af_bella"  # Combines two voices
```

To run the script, copy some text to the clipboard, press `Ctrl+Shift+Space`, and enjoy the audio playback.

## Notes
- If the clipboard is empty or contains non-text content, the script will notify you and do nothing.
- Ensure Kokoro-FastAPI is running and accessible before running the script.

## Exit
Press `ESC` to terminate the program.
