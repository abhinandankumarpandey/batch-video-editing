# User Guide

Welcome to the Automatic Batch Video Maker! This guide explains how to use the tool to configure your assets and generate videos.

## Overview
The Automatic Batch Video Maker is a Python-based tool designed to automate the creation of short videos. It combines various elements like video clips, images, voiceovers, intros, outros, background music, subtitles, and dynamic overlays (GIFs, stickers, green screen memes, SFX) based on subtitle sentiment. The tool is configurable and can be run via a command-line interface.

## Asset Folder Structure
For the tool to correctly find and use your media, you need to organize your assets in a specific way within the main `assets` directory. Below is the recommended structure and purpose of each subfolder:

*   `assets/`
    *   `audio/`: Store background music files (e.g., `trending_song.mp3`).
    *   `branding/`: For watermarks or logos (e.g., `logo.png`).
    *   `color/`: For LUT (Look-Up Table) files (e.g., `teal_and_orange.cube`).
    *   `effects/`: For cinematic video overlays (e.g., `rain_overlay.mov`).
    *   `frames/`: For aesthetic border frames (e.g., `meme_border.png`).
    *   `full_sentence_subtitle/`: **Crucial for emotion analysis.** Store `.srt` subtitle files here. Each file should correspond by name to a voiceover file and contain the full sentences spoken in the voiceover, accurately timed. (e.g., if voiceover is `my_talk.mp3`, subtitle should be `my_talk.srt`).
    *   `gifs/`: For animated GIFs used in emotion-based overlays.
        *   `gifs/joy/`: GIFs for 'joy' emotion.
        *   `gifs/sadness/`: GIFs for 'sadness' emotion.
        *   `(other emotion subfolders as per EMOTION_ID2LABEL in src/utils.py)`: Create subfolders for each emotion you want to use (e.g., anger, surprise, etc.).
    *   `images/`: Primary folder for still images to be used in video sequences.
    *   `darkimages/`: Secondary folder for images, perhaps with a different theme.
    *   `intros/`: Video clips to be used as intros.
    *   `memes/`: For green screen video memes, also organized by emotion.
        *   `memes/joy/`: Green screen videos for 'joy'.
        *   `(other emotion subfolders)`
    *   `more_randomvideos/`: Secondary folder for general video clips.
    *   `one_to_four_word_subtitle/`: Store `.srt` subtitle files that are formatted for display (e.g., shorter, larger text). These are what will be rendered onto the video if `ENABLE_SUBTITLE` is true. File names should match voiceover names.
    *   `outros/`: Video clips for outros.
    *   `sfx_emotional/`: For sound effects linked to emotions.
        *   `sfx_emotional/joy/`: SFX for 'joy'.
        *   `(other emotion subfolders)`
    *   `additional_sfx/`: For general sound effects to be added randomly (not based on emotion).
    *   `stickers/`: For PNG stickers used in emotion-based overlays.
        *   `stickers/joy/`: Stickers for 'joy'.
        *   `(other emotion subfolders)`
    *   `videos/`: Primary folder for general video clips.
    *   `voiceovers/`: Your main audio voiceover files (e.g., `.mp3`, `.wav`). The tool processes these one by one.

## Configuration (`src/config.py`)
Many aspects of the video generation can be controlled by editing the `src/config.py` file before running the tool. Key options include:

*   **Feature Flags (`ENABLE_...`):**
    *   `ENABLE_INTRO`, `ENABLE_OUTRO`, `ENABLE_WATERMARK`, `ENABLE_BGM`, `ENABLE_SUBTITLE`, etc. Set to `True` to enable a feature, `False` to disable.
    *   `ENABLE_GIFS`, `ENABLE_STICKERS`, `ENABLE_GREENSCREEN_OVERLAY`, `ENABLE_SFX` (for emotional SFX), `ENABLE_ADDITONAL_SFX`.
*   **Paths:**
    *   `OUTPUT_FOLDER`: Where generated videos will be saved.
    *   Paths to all asset folders (e.g., `VOICEOVER_FOLDER`, `MAIN_CLIPS_VIDEOS_FOLDERS`, `GIF_FOLDER`).
*   **Video Properties:**
    *   `FINAL_RESOLUTION`: Output video resolution (e.g., `[1080, 1920]` for 1080p vertical).
    *   `FINAL_FPS`: Output video frames per second (e.g., `30`).
    *   `FINAL_CODEC`: Hardware acceleration. Options:
        *   `'qsv'`: Intel Quick Sync Video (requires compatible Intel hardware and FFmpeg build).
        *   `'cuda'`: NVIDIA NVENC (requires compatible NVIDIA GPU and FFmpeg build).
        *   `'none'`: CPU-based encoding (libx264, slower but most compatible).
    *   `DEFAULT_DATA['final']['quality']`: Can be `'fast'`, `'balanced'`, `'high'` to adjust encoding quality/speed.
*   **Content Control:**
    *   `IMAGE_PERCENTAGE`: Percentage of main content that should be images (vs. videos).
    *   `VIDEO_MODE`: How video clips are used (e.g., `'full_clip'`, `'start_random'`).
    *   Volume levels for voiceover, BGM, SFX.
    *   Settings for watermarks, frames, cinematic effects (position, size, opacity).
    *   Parameters for GIFs, stickers, green screen memes (anchor positions, margins, sizes).

## Running the Tool (Command-Line Interface - CLI)
Navigate to the project's root directory in your terminal (ensure your virtual environment is activated). The main script is `src/main.py`.

*   **Process all available voiceovers in the `VOICEOVER_FOLDER`:**
    \`\`\`bash
    python src/main.py --batch
    \`\`\`
    *(Note: The `--batch` functionality in `main.py` is yet to be fully implemented in the provided plan)*

*   **Process a limited number of videos with a specific number of worker threads:**
    \`\`\`bash
    python src/main.py --batch --max-videos 5 --max-workers 2
    \`\`\`
    *   `--max-videos N`: Limits processing to the first N new voiceovers found.
    *   `--max-workers N`: (For future parallel processing) Specifies how many videos to process concurrently.

*   **Basic processing mode (clips + voiceover, minimal extra features):**
    \`\`\`bash
    python src/main.py --batch --basic
    \`\`\`
    *   `--basic`: This flag will disable most overlays and effects, focusing on core video assembly. (Requires implementation in `main.py` to toggle relevant `ENABLE_` flags from `config.py` based on this).

*(CLI argument parsing and handling in `src/main.py` will be developed in a later step of the plan.)*

## GUI Usage
(A lightweight Graphical User Interface is planned. This section will be updated with instructions once the GUI is implemented. It will allow setting folder paths, common configurations, and starting the batch process without using the command line directly.)

## Feature Details
(This section will briefly list each feature from `config.py` like `ENABLE_INTRO`, `ENABLE_GIFS`, etc., and what they do, as a quick reference).

*   **Intro/Outro:** Adds pre-defined video clips at the beginning/end.
*   **Main Clips:** Assembles a sequence of videos and images.
*   **Voiceover:** The primary audio track for the video.
*   **Subtitles (Display):** Renders text from `one_to_four_word_subtitle` onto the video.
*   **Subtitles (Emotion Analysis):** Uses text from `full_sentence_subtitle` to drive dynamic content.
*   **Background Music (BGM):** Adds a continuous audio track.
*   **Watermark:** Overlays a branding logo.
*   **Aesthetic Frame:** Adds a static border frame.
*   **Cinematic Effect:** Overlays a video effect (e.g., rain).
*   **LUT Color Grading:** Applies a Look-Up Table for color correction/styling.
*   **Emotion-Based GIFs/Stickers/Memes/SFX:** Dynamically adds visual or audio elements based on the emotion detected in the voiceover script (via `full_sentence_subtitle`).
*   **Additional SFX:** Randomly adds sound effects not tied to emotion.

## Troubleshooting

*   **`ffmpeg not found` or `No such file or directory: 'ffmpeg'`:**
    *   FFmpeg is not installed correctly or not added to your system's PATH. Please re-check Step 3 of the Installation Guide. Ensure you can run `ffmpeg -version` in a new terminal window.
*   **Hugging Face Model Download Issues (`OSError: Can't load tokenizer for 'nayeems94/text-emotion-classifier'`):**
    *   Ensure you have an active internet connection the first time you run a feature using sentiment analysis.
    *   There might be temporary issues with the Hugging Face Hub or network restrictions. Try again later.
    *   If behind a proxy, you might need to configure environment variables (`HTTP_PROXY`, `HTTPS_PROXY`).
*   **Asset Not Found Warnings (e.g., "GIF folder not found for emotion 'joy'"):**
    *   Double-check your `assets` folder structure. Ensure subfolders for emotions (e.g., `assets/gifs/joy`, `assets/stickers/sadness`) exist and contain media if you expect content for those emotions.
    *   Verify paths in `src/config.py` are correct.
*   **Low Quality Output / Slow Processing:**
    *   If not using hardware acceleration (`FINAL_CODEC = 'none'`), processing can be slow. Ensure FFmpeg is compiled with support for QSV or NVENC if you have compatible hardware and set `FINAL_CODEC` accordingly.
    *   Adjust `DEFAULT_DATA['final']['quality']` in `src/config.py` (e.g., to `'fast'` for quicker, lower quality previews).
*   **"Permission Denied" errors:**
    *   Ensure you have write permissions for the `OUTPUT_FOLDER` and read permissions for all asset folders.
