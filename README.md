# py-os Simulator

An accessible operating system simulator for blind and visually impaired users.

## Features
- **Cross-platform Speech Engine**: Uses NVDA on Windows when available, macOS `say` on Mac, and Speech Dispatcher, eSpeak, or `pyttsx3` on Linux depending on what is installed.
- **High Contrast GUI**: Built with `wxPython`, optimized for screen readers and low-vision users.
- **Virtual File System**: A safe, sandboxed environment (`/vfs` folder) to practice file management.
- **VoiceOver-friendly navigation on macOS**: Focus changes avoid excessive duplicate announcements so VoiceOver can read controls naturally.
- **Platform Diagnostics app**: Reports available speech backends, host shells, file-open helpers, and optional dependencies on the current machine.
- **Keyboard Shortcuts**:
  - `Ctrl + T`: Speak current time.
  - `Ctrl + W`: Speak current location (path).
  - `Enter`: Execute command.

## Commands
- `help`: List available commands.
- `list`: Speak items in the current directory.
- `open <name>`: Open a folder or read a text file.
- `create <name>`: Create a new text file.
- `delete <name>`: Delete a file or empty folder.
- `time`: Speak the current time.
- `where`: Speak current directory.
- `exit`: Close the simulator.
- `shell <type>`: Open a host shell such as `zsh`, `bash`, `sh`, `cmd`, or `powershell`, depending on your platform.

## macOS Notes

- On macOS, py-os uses the built-in `say` command for spoken feedback.
- The desktop reduces automatic focus chatter on macOS so VoiceOver can announce buttons and controls more clearly.
- File Explorer uses the native `open` command to launch files with their default Mac app.
- By default, app data is stored in the repo-local `.py-os-data/` folder. Set `PY_OS_DATA_DIR` if you want it elsewhere.

## Support Matrix

- Windows: Best with `wxPython`, optional NVDA Controller DLL, and optional `sounddevice` plus `soundfile` for recording.
- macOS: Best with `wxPython`; speech works with built-in `say`, and recording works when `sounddevice` plus `soundfile` are installed.
- Linux: Best with `wxPython`; speech can use `spd-say`, `espeak-ng`, `espeak`, or `pyttsx3`, depending on what is installed.

Open the `Platform Diagnostics` app after launch to see the exact support level on the current machine.

## NVDA Integration (Optional)
To enable direct NVDA support:
1. Download `nvdaControllerClient64.dll` (for 64-bit Python) or `nvdaControllerClient32.dll` (for 32-bit Python) from the [NVDA GitHub Repository](https://github.com/nvaccess/nvda/tree/master/extras/controllerClient).
2. Place the DLL in the same folder as `desktop.py`.

## Installation Guide for Windows

To install py-os and set everything up automatically:

1.  **Run the Installer:**
    Double-click `setup.bat` in the project root. This will:
    -   Check for Python.
    -   Create a virtual environment (`venv`).
    -   Install all required dependencies.
    -   Create a `launch.bat` file.
    -   Create a **Desktop Shortcut** named "py-os Simulator".

2.  **Launch the Application:**
    You can now start the simulator by double-clicking the shortcut on your Desktop or by running `launch.bat`.

---

## Installation Guide for GitHub (Manual)

1.  **Clone the repository:**
    First, clone the proj
    ```bash
    git clone https://github.com/wasilewsk/py-os
    cd py-os 
    ```

2.  **Set up a virtual environment (Recommended):**
    Using a virtual environment is highly recommended to manage project dependencies without conflicts.
    ```bash
    # Create a virtual environment (e.g., named 'venv')
    python -m venv venv
    
    # Activate the virtual environment:
    # On Windows:
    .\venv\Scripts\activate
    # On macOS/Linux:
    # source venv/bin/activate
    ```

3.  **Install FFmpeg (Optional but recommended):**
    The system can use FFmpeg tools such as `ffplay` for audio playback fallbacks.
    ```bash
    # Windows
    winget install ffmpeg

    # macOS
    brew install ffmpeg

    # Linux (Debian/Ubuntu example)
    sudo apt install ffmpeg
    ```

4.  **Install dependencies:**
    Install all required Python packages using the `requirements.txt` file.
    ```bash
    pip install -r requirements.txt
    ```

4.  **NVDA Controller Client DLL (for direct NVDA integration):**
    If you intend to use the direct NVDA integration feature, follow these steps:
    a. Download the appropriate DLL file: `nvdaControllerClient64.dll` (for 64-bit Python) or `nvdaControllerClient32.dll` (for 32-bit Python) from the [NVDA GitHub Repository extras page](https://github.com/nvaccess/nvda/tree/master/extras/controllerClient).
    b. Copy the downloaded DLL file into the main project directory (the same folder where `desktop.py` is located).

5.  **Run the application:**
    Execute the main application script to launch the simulator.
    ```bash
    python desktop.py
    ```

---
