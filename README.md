# Batch Video Editor CLI

A command-line tool for automating batch video editing tasks. This tool allows you to define video projects using JSON configuration files and generate videos by combining your media assets, applying watermarks, background music, and more.

## Features

*   **Batch Processing:** Process multiple video projects by providing a directory of configuration files.
*   **Configurable Projects:** Each video is defined by a JSON configuration file.
*   **Asset Management:**
    *   Automatic selection of voiceovers (skips already processed ones).
    *   Selection of video and image clips for the main timeline based on percentages and uniqueness.
    *   Selection of intros, outros, and background music from specified folders.
*   **Video Compilation:**
    *   Concatenation of video clips.
    *   Conversion of images into video segments (slideshow functionality).
    *   Overlaying intros and outros.
*   **Audio Features:**
    *   Mixing of background music (BGM) with adjustable volume. Loops BGM if shorter than video.
    *   (Note: Voiceover audio is expected to be part of the primary video clips or the first segment's audio.)
*   **Branding:**
    *   Optional watermarking with configurable position and size.
*   **Output Control:**
    *   Customizable output resolution, FPS, video codec, audio codec, and quality settings (CRF/CQ).
    *   Support for CPU-based encoding (libx264) and profiles for QSV (Intel Quick Sync) and CUDA (NVIDIA NVENC) if FFmpeg is compiled with support.

## Directory Structure

Organize your project and assets as follows:

```
your_project_root/
├── batch_processor.py       # Main script to run
├── video_engine.py          # Core video processing logic
├── asset_manager.py         # Asset selection logic
├── config_loader.py         # Configuration loading logic
├── requirements.txt         # Python dependencies
├── README.md                # This file
├── configs/                 # Your project JSON configuration files
│   └── project1.json
│   └── project2.json
├── assets/                  # All your media assets
│   ├── voiceovers/          # Audio files for voiceovers
│   ├── intros/              # Video files for intros
│   ├── videos/              # Main video clips
│   ├── images/              # Main image files
│   ├── outros/              # Video files for outros
│   ├── branding/            # Watermark images (e.g., logo.png)
│   ├── audio/               # Background music files
│   ├── effects/             # (For future cinematic effects)
│   ├── subtitles/           # (For future subtitle features)
│   │   ├── one_to_four_word_subtitle/
│   │   └── full_sentence_subtitle/
│   ├── luts/                # (For future LUT/color grading)
│   ├── gifs/                # (For future GIF overlays)
│   ├── stickers/            # (For future sticker overlays)
│   ├── greenscreen/         # (For future green screen overlays)
│   └── sfx/                 # (For future sound effects)
└── output/                  # Generated videos will be saved here
```

## Installation

### 1. Python
Ensure you have Python 3.8 or newer installed.

### 2. FFmpeg
This tool relies heavily on FFmpeg for video processing. You must have FFmpeg installed and accessible in your system's PATH.

*   **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt update
    sudo apt install ffmpeg
    ```
*   **macOS (using Homebrew):**
    ```bash
    brew install ffmpeg
    ```
*   **Windows:**
    Download FFmpeg builds from [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/) (select a "release" build). Extract the archive, and add the `bin` directory (which contains `ffmpeg.exe`, `ffprobe.exe`) to your system's PATH environment variable.

Verify installation by typing `ffmpeg -version` and `ffprobe -version` in your terminal.

### 3. Python Dependencies
Navigate to the project's root directory and install the required Python packages:

```bash
pip install -r requirements.txt
```
This will install `ffmpeg-python` and any other necessary libraries.

## Configuration

Each video project is defined by a JSON file placed in the `configs/` directory. This file specifies paths to assets, enables features, and sets output parameters.

The system uses a default configuration (see `config_loader.py:DEFAULT_CONFIG`). Your project JSON only needs to override the settings you want to change.

### Example Project JSON (`configs/my_awesome_video.json`):

```json
{
  "project_name": "My Awesome Video Episode 1",
  "assets_base_path": "./assets", // Or an absolute path to your assets folder

  // Feature Flags
  "ENABLE_INTRO": true,
  "ENABLE_OUTRO": true,
  "ENABLE_WATERMARK": true,
  "ENABLE_BGM": true,

  // Asset Locations (relative to assets_base_path or absolute)
  "intro_folder": "intros/cool_intros",
  "main_clips_videos_folders": ["videos/set1", "videos/set2"],
  "main_clips_images_folder": ["images/landscapes"],
  "outro_folder": "outros",
  "watermark_path": "branding/my_logo.png",
  "bgm_folder": "audio/epic_music",
  "voiceover_folder": "voiceovers/episode1_vo", // Used to pick a voiceover and name the output

  // Asset Selection
  "image_percentage": 30, // Target 30% of main clips (by count) to be images
  "unique_assets": true,    // Ensure each video/image in main clips is used only once
  "num_main_clips_target": 20, // Aim for about 20 main clips (videos + images)
  "default_image_display_duration": 4.0, // Display each image for 4 seconds

  // Watermark Customization
  "watermark_params": {
    "position_x": "W-w-20", // FFmpeg expression for position (20px from right edge)
    "position_y": "H-h-20", // FFmpeg expression for position (20px from bottom edge)
    "width": "W*0.15"       // Watermark width is 15% of the main video width
  },

  // BGM Customization
  "bgm_volume": 0.15, // Lower BGM volume (1.0 is original)

  // Output Settings
  "final": {
    "resolution": [1920, 1080], // Width x Height
    "fps": 30,
    "selected_encoder_profile": "none", // 'none' (libx264), 'qsv', or 'cuda'
    "quality": "balanced", // 'fast', 'balanced', or 'high' - adjusts CRF/CQ of selected profile
    // For advanced users, you can override specific profile settings here:
    // "_encoding_profiles": {
    //   "none": { "crf": 18 } // Example: Override CRF for libx264
    // }
    "output_folder": "./output" // Where to save the final video
  }
}
```

### Key Configuration Options:

*   `project_name`: (Optional) A descriptive name for your project.
*   `assets_base_path`: Base directory where your asset subfolders (like `videos`, `images`) are located.
*   `ENABLE_...` flags: Booleans (`true`/`false`) to turn features on/off.
*   `..._folder` / `..._path`: Paths to your media assets. These can be absolute or relative to `assets_base_path`.
*   `image_percentage`: Target percentage of main timeline clips that should be images (by count).
*   `num_main_clips_target`: Desired total number of clips (videos + images) in the main section.
*   `default_image_display_duration`: How long each image should appear in the slideshow.
*   `watermark_params`: Controls watermark size and position using FFmpeg expressions.
    *   `W`, `H`: Main video width/height.
    *   `w`, `h`: Watermark image width/height.
*   `bgm_volume`: Volume for the background music (e.g., 0.5 for 50% volume).
*   `final`: Contains output video settings.
    *   `resolution`: `[width, height]`.
    *   `fps`: Frames per second.
    *   `selected_encoder_profile`: Choose `"none"` for CPU-based x264 encoding (most compatible), `"qsv"` for Intel QuickSync, or `"cuda"` for Nvidia NVENC. Ensure your FFmpeg supports these and hardware is available.
    *   `quality`: A preset (`"fast"`, `"balanced"`, `"high"`) that adjusts encoding parameters (like CRF for x264) for the selected profile.

## Usage

Run the script from your project's root directory:

1.  **To process a single project configuration file:**
    ```bash
    python batch_processor.py configs/my_project.json
    ```

2.  **To process all `.json` configuration files in a directory:**
    ```bash
    python batch_processor.py configs/
    ```

The generated videos will be saved in the `output/` directory (or the `output_folder` specified in your config), named after the selected voiceover file.

## Future Enhancements (TODO)

*   Advanced audio mixing (e.g., voiceover ducking for BGM).
*   More sophisticated video transitions.
*   Direct subtitle overlay and emotion-based GIF/sticker overlays.
*   Support for LUTs and other visual effects.
*   Improved error handling and reporting.
*   Parallel processing for multiple projects using threading/multiprocessing.

---
This project provides a foundation for automated video creation. Feel free to extend and adapt it to your needs!
