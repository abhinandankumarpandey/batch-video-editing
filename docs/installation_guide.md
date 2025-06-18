# Installation Guide

This guide will walk you through setting up the Automatic Batch Video Maker project on your system.

## Prerequisites

*   **Python:** Version 3.8 to 3.11 is recommended. You can download Python from [python.org](https://www.python.org/downloads/).
*   **FFmpeg:** This is a crucial system-level dependency for video and audio processing. The `ffmpeg-python` library is a Python wrapper around the FFmpeg executable, but you need to install FFmpeg itself separately.
*   **Git:** For cloning the repository (recommended). You can download Git from [git-scm.com](https://git-scm.com/downloads). Alternatively, you can download the project as a ZIP file from the repository page.
*   **Internet Connection:** Required for downloading Python dependencies and the Hugging Face sentiment analysis model on first run.

## Setup Instructions

### 1. Clone the Repository (Recommended)
If you have Git installed, clone the project repository to your local machine:
\`\`\`bash
git clone <repository_url> # Replace <repository_url> with the actual URL of your Git repo
cd <project_folder_name>   # Replace <project_folder_name> with the name of the cloned directory
\`\`\`
If you downloaded a ZIP file, extract it to your desired location and navigate into the project folder using your terminal or command prompt.

### 2. Create and Activate a Virtual Environment
It's highly recommended to use a virtual environment to manage project dependencies and avoid conflicts with other Python projects.

*   **Navigate to your project directory in the terminal.**
*   **Create a virtual environment (e.g., named `.venv`):**
    \`\`\`bash
    python -m venv .venv
    \`\`\`
    (On some systems, you might need to use `python3` instead of `python`)

*   **Activate the virtual environment:**
    *   **Windows (Command Prompt/PowerShell):**
        \`\`\`bash
        .\venv\Scripts\activate
        \`\`\`
    *   **macOS/Linux (Bash/Zsh):**
        \`\`\`bash
        source .venv/bin/activate
        \`\`\`
    Your terminal prompt should change to indicate that the virtual environment is active (e.g., `(.venv) your-prompt$`).

### 3. Install FFmpeg
FFmpeg must be installed on your system and accessible via the system's PATH.

*   **Windows:**
    1.  Download a static build from an official source:
        *   [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (recommended, provides full builds)
        *   [BtbN's builds](https://github.com/BtbN/FFmpeg-Builds/releases)
    2.  Extract the downloaded ZIP file to a permanent location on your computer (e.g., `C:\FFmpeg`).
    3.  Add the `bin` directory from your FFmpeg installation (e.g., `C:\FFmpeg\bin`) to your system's PATH environment variable.
        *   Search for "environment variables" in the Windows search bar.
        *   Click "Edit the system environment variables".
        *   In the System Properties window, click the "Environment Variables..." button.
        *   Under "System variables", find the variable named `Path` and select it. Click "Edit...".
        *   Click "New" and add the path to your FFmpeg `bin` directory.
        *   Click OK on all windows to save the changes.
    4.  Verify the installation by opening a **new** command prompt or PowerShell window and typing:
        \`\`\`bash
        ffmpeg -version
        \`\`\`
        You should see FFmpeg version information.

*   **macOS:**
    *   The easiest way is to use [Homebrew](https://brew.sh/):
        \`\`\`bash
        brew install ffmpeg
        \`\`\`
    *   Verify installation:
        \`\`\`bash
        ffmpeg -version
        \`\`\`

*   **Linux (Debian/Ubuntu-based):**
    \`\`\`bash
    sudo apt update
    sudo apt install ffmpeg
    \`\`\`
    *   **Linux (Fedora/RHEL-based):**
        You might need to enable the RPM Fusion repository first.
        \`\`\`bash
        sudo dnf install https://download1.rpmfusion.org/free/fedora/rpmfusion-free-release-$(rpm -E %fedora).noarch.rpm https://download1.rpmfusion.org/nonfree/fedora/rpmfusion-nonfree-release-$(rpm -E %fedora).noarch.rpm
        sudo dnf install ffmpeg
        \`\`\`
    *   Verify installation:
        \`\`\`bash
        ffmpeg -version
        \`\`\`

### 4. Install Python Dependencies
With your virtual environment activated, install the required Python packages using the `requirements.txt` file:
\`\`\`bash
pip install -r requirements.txt
\`\`\`
This will install `ffmpeg-python`, `transformers`, `torch`, `PySimpleGUI` (or other chosen GUI library), and any other necessary packages.

### 5. Hugging Face Model Download
The first time you run a feature that uses sentiment analysis (e.g., adding emotion-based GIFs, stickers, SFX), the `transformers` library will automatically download the pre-trained model (`nayeems94/text-emotion-classifier`) from the Hugging Face Hub. This requires an active internet connection. The model will be cached locally for future use.

## Setup Complete!
You should now have all the necessary components installed to run the Automatic Batch Video Maker.

## Next Steps
Once installation is complete, please refer to the [User Guide](user_guide.md) for instructions on how to configure and run the application.
