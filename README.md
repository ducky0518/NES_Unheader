# NES ROM Header Remover Tool

## Overview

This application provides a user-friendly graphical interface (GUI) to remove the 16-byte iNES header from Nintendo Entertainment System (NES) ROM files. It can process individual `.nes` files as well as `.nes` files contained within `.zip` archives. The resulting unheadered ROMs are saved to a user-specified output directory.

This tool is built using Python and the CustomTkinter library for its interface.

## Features

* **Graphical User Interface:** Easy-to-use interface for selecting directories and managing the conversion process.
* **Header Removal:** Correctly identifies and removes the standard 16-byte iNES header.
* **Batch Processing:** Select an input directory, and the tool will scan for all compatible ROMs.
* **ZIP Archive Support:** Automatically finds and processes `.nes` files within `.zip` archives in the input directory.
* **Selective Listing:** Scans and lists only ROMs confirmed to have an iNES header.
* **Alphabetical Sorting:** Displays the list of ROMs to be processed in alphabetical order.
* **Progress Display:** Shows the status of the current operation and overall progress for conversions.
* **Interruptible Operations:** "Stop Scanning" and "Stop Conversion" buttons allow you to halt lengthy processes gracefully.
* **Standalone Executable:** Released as a single `.exe` file for Windows (see Releases).

## Using the Application

There are two ways to use this application:

### 1. Using the Standalone Executable (for Windows - see Releases)

If a pre-built `NES_Unheader_Tool.exe` (or similar name) is provided:

1.  Download the executable file.
2.  Double-click the `.exe` file to run the application. No installation is required.
3.  **Select Input Directory:** Click the "Browse" button next to "Input ROMs Directory" to choose the folder containing your headered NES ROMs (can be `.nes` files or `.zip` archives containing `.nes` files).
4.  **Select Output Directory:** Click the "Browse" button next to "Output Directory" to choose where the unheadered ROMs will be saved.
5.  **Scan for ROMs:** Once both paths are selected, click the "Scan for Headered ROMs" button. The application will scan the input directory and list all headered ROMs found.
    * You can click "Stop Scanning" if the process takes too long. ROMs found up to that point will be listed.
6.  **Convert ROMs:** After scanning is complete and ROMs are listed, click the "Convert Selected ROMs" button. The application will process each ROM, remove its header, and save it to your output directory.
    * You can click "Stop Conversion" to halt the process. A summary of work done up to that point will be provided.
7.  A confirmation message will appear when the conversion process is finished or stopped.

### 2. Running from Source Code

This section describes how to run the application directly using Python, without using a pre-built `.exe` file.

**Prerequisites:**

* Python 3.7 or newer (Python can be downloaded from [python.org](https://www.python.org/downloads/)).
* CustomTkinter library.

**Steps:**

1.  **Download/Clone Source Code:** Obtain the Python script file (e.g., `nes_unheader.py`) and any associated files.
2.  **Install Dependencies:** Open a terminal or command prompt and install CustomTkinter:
    ```bash
    pip install customtkinter
    ```
3.  **Run the Script:** Navigate to the directory where you saved the Python script using the terminal/command prompt. Then, run the script using:
    ```bash
    python nes_unheader.py
    ```
4.  **Using the Application Window:** Once the script is running, the application window will appear.
    * Click the "Browse" button next to "Input ROMs Directory" to choose the folder containing your headered NES ROMs.
    * Click the "Browse" button next to "Output Directory" to select where the unheadered ROMs will be saved.
    * When both paths are set, click the "Scan for Headered ROMs" button. You can use the "Stop Scanning" button if needed.
    * After the scan is complete and ROMs are listed, click the "Convert Selected ROMs" button. You can use the "Stop Conversion" button if needed.
    * A message will indicate when the process is complete or stopped.

## Troubleshooting

* **Antivirus False Positives:** Occasionally, antivirus software might flag executables created by PyInstaller as suspicious. This is usually a false positive. If this occurs, you may need to add an exception for the file in your antivirus settings.
* **Application Fails to Start (from .exe):** If the packaged `.exe` doesn't start or crashes immediately, try building it without the `--windowed` option first (`pyinstaller --onefile your_script_name.py`). Run this version from a command prompt; it may display error messages that can help diagnose the issue (e.g., missing files or unhandled exceptions).

## Disclaimer

* This tool modifies ROM files by removing their headers. Always back up your original ROM files before processing them.
* Use this software at your own risk. The author is not responsible for any damage or loss of data.

---
