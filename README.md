# Qobuz Overlay

A lightweight, "always-on-top" desktop overlay for the Qobuz music player on Windows. It displays the currently playing track, artist, and album art in a sleek, minimal, draggable, and resizable window.

## Features

-   **Now Playing Info:** Displays the current track and artist by reading the Qobuz window title.
-   **Album Art:** Fetches and displays high-quality album art from the iTunes API.
-   **Always-on-Top:** Stays visible over your other applications for easy viewing.
-   **Minimalist UI:** A clean, frameless window that can be moved and resized.
-   **Interactive:** A close button appears on hover for easy termination.
-   **Auto-Detection:** Automatically shows "Qobuz Idle" when the application isn't playing or is closed.

## Requirements

This application is designed for **Windows only** due to its use of the Windows API for process and window detection.

You will need Python 3.x installed. The project depends on the following Python libraries:

-   `PyQt6`: For the graphical user interface.
-   `qasync`: To run an asyncio event loop within a PyQt6 application.
-   `psutil`: To find the Qobuz process and its ID.
-   `requests`: To fetch album art from the web API.

You can install all dependencies using the provided `requirements.txt` file.

## Installation & Usage

1.  Clone the repository or download the source code.

2.  Install the required dependencies from the project's root directory:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python main.py
    ```

## Building a Standalone Executable (.EXE)

You can compile the script into a single, standalone executable file (`.exe`) using `PyInstaller`.

1.  First, ensure PyInstaller is installed:
    ```bash
    pip install pyinstaller
    ```
2.  From the project's root directory, run the following build command:
    ```bash
    python -m PyInstaller --noconsole --onefile --name "QobuzOverlay" main.py
    ```
    -   `--noconsole`: Prevents a command prompt window from opening when the `.exe` is run.
    -   `--onefile`: Bundles everything into a single executable file.
    -   `--name "QobuzOverlay"`: Sets the name of the final executable.

3.  The final `QobuzOverlay.exe` will be located in a new `dist` folder.