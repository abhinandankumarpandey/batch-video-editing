# Automatic Batch Video Maker

## Overview

The Automatic Batch Video Maker is a Python-based tool designed to automate the creation of short-form videos. It intelligently combines various media elements including:

*   Video clips and images
*   Voiceovers
*   Intros and outros
*   Background music
*   Subtitles (both for display and for sentiment analysis)
*   Dynamic, emotion-driven overlays:
    *   Animated GIFs
    *   Stickers (PNG)
    *   Green screen video memes
    *   Sound effects (SFX)
*   General SFX, watermarks, aesthetic frames, and cinematic effects.

The tool leverages FFmpeg for powerful video processing and Hugging Face Transformers for sentiment analysis to make content more engaging. It is configurable through a Python configuration file and will support command-line operations for batch processing. A lightweight GUI is also planned for easier management.

## Features
*   Automated assembly of video sequences from diverse asset types.
*   Sentiment analysis of subtitle text to trigger contextually relevant dynamic content (GIFs, stickers, memes, SFX).
*   Support for various overlays: watermarks, aesthetic frames, video effects.
*   Background music and multiple SFX layers.
*   LUT-based color grading.
*   Configurable output resolution, FPS, and encoding quality.
*   Planned support for hardware acceleration (Intel QSV, NVIDIA NVENC) via FFmpeg.
*   Command-line interface for batch processing.
*   (Planned) Lightweight GUI for easy configuration and operation.

## Getting Started

For detailed instructions on how to set up and use this project, please refer to the following guides:

*   **[Installation Guide](docs/installation_guide.md)**: Covers prerequisites, environment setup, FFmpeg installation, and Python dependencies.
*   **[User Guide](docs/user_guide.md)**: Explains how to structure your assets, configure the tool, run it, and troubleshoot common issues.

## Project Structure (Brief)

*   `src/`: Contains the main Python source code.
    *   `main.py`: Entry point for the application (CLI, batch processing).
    *   `video_processing.py`: Core FFmpeg logic for video assembly and effects.
    *   `utils.py`: Helper functions (e.g., sentiment analysis, SRT parsing).
    *   `config.py`: Global configurations, feature flags, paths.
    *   `gui.py`: (Planned) Code for the GUI.
*   `assets/`: Default root directory for all your media input files (see User Guide for detailed structure).
*   `docs/`: Contains detailed documentation.
*   `output/`: Default directory where generated videos are saved.
*   `requirements.txt`: Lists Python dependencies.

## Contributing
(Placeholder for contribution guidelines if this were an open project)

## License
(Placeholder for license information - e.g., MIT License)

---

This project aims to streamline video creation by automating repetitive editing tasks and intelligently adding dynamic elements.
