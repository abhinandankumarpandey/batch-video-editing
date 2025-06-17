import json
import os

# Default configuration based on requirments_and_rules.txt
DEFAULT_CONFIG = {
    "final": {
        "hwaccel": "cuda", # This might need to be CPU-focused or auto-detected later for broader compatibility
        "resolution": [1080, 1920], # [width, height]
        "fps": 30,
        "_encoding_profiles": {
            "none": {
                "vcodec": "libx264", "preset": "medium", "crf": 21, "tune": "film",
                "extra_args": ["-x264-params keyint=60:min-keyint=60", "-movflags +faststart", "-pix_fmt yuv420p"]
            },
            "qsv": {
                "vcodec": "h264_qsv", "preset": "faster", "vquality": 24,
                "extra_args": ["-look_ahead_depth 4", "-extbrc 1", "-low_power on", "-b_strategy 1", "-adaptive_i 1", "-profile:v high"]
            },
            "cuda": {
                "vcodec": "h264_nvenc", "preset": "p6", "cq": 23, "tune": "hq",
                "extra_args": ["-rc:v vbr", "-b_ref_mode middle", "-spatial_aq 1", "-temporal_aq 1", "-cqm flat"]
            }
        },
        "acodec": "aac", "abr": "160k", "ar": 48000, "threads": os.cpu_count(), "buffer_size": "4000k",
        "_quality_presets": {
            "fast": {"crf": 23, "vquality": 26, "cq": 25},
            "balanced": {"crf": 21, "vquality": 24, "cq": 23},
            "high": {"crf": 18, "vquality": 22, "cq": 21}
        },
        "quality": "balanced", # Default quality preset
        "selected_encoder_profile": "none" # Default encoder profile (CPU-based libx264)
    },
    "assets_base_path": "./assets", # Base path for all assets
    "output_folder": "./output",

    # Feature flags (can be overridden by project config)
    "ENABLE_INTRO": False,
    "ENABLE_OUTRO": False,
    "ENABLE_WATERMARK": True,
    "ENABLE_BGM": True,
    # ... other flags from requirments_and_rules.txt can be added here ...
    "ENABLE_SUBTITLE": True, # For emotion detection later
    "ENABLE_GIFS": False, # Tied to emotion detection
    "ENABLE_STICKERS": False, # Tied to emotion detection

    # Asset paths (relative to assets_base_path, can be overridden)
    "intro_folder": "intros",
    "main_clips_videos_folders": ["videos", "more_randomvideos"],
    "main_clips_images_folder": ["images", "darkimages"],
    "outro_folder": "outros",
    "watermark_path": "branding/logo.png", # Specific file, not folder
    "bgm_folder": "audio", # Folder for BGM files
    "voiceover_folder": "voiceovers",

    # Settings from requirments_and_rules.txt
    "image_percentage": 40,
    "unique_assets": True,
    "video_mode": "full_clip", # "full_clip", "start_random", "split_subclips", "tiny_subclips

    "watermark_params": {
        "position_x": "W-w-10", # FFmpeg expression for top-right
        "position_y": "10",
        "width": "W*0.08" # FFmpeg expression for width (e.g., 8% of main video width)
    },
    "bgm_volume": 0.25,

    # Placeholder for subtitle-related settings for emotion detection (if used)
    "subtitle_folder_to_use_for_sentiment_analysis": "subtitles/full_sentence_subtitle",
    "gif_folder": "gifs",
    "sticker_folder_path": "stickers",
    "emotion_confidence_threshold": 0.5, # From README.md (CONF_THRESH)
    "emotion_min_words_for_meme": 3, # From README.md (MIN_WORDS)
    "emotion_max_display_ms": 2000, # From README.md (MAX_DISPLAY_MS)

    # Anchor positions and size presets from requirments_and_rules.txt (can be used by features like GIFs/Stickers)
    "ANCHOR_POSITIONS": {
        "top-left": ["0+{mx}", "0+{my}"], "top-right": ["W-w-{mx}", "0+{my}"],
        "bottom-left": ["0+{mx}", "H-h-{my}"], "bottom-right": ["W-w-{mx}", "H-h-{my}"],
        "center": ["(W-w)/2", "(H-h)/2"]
    },
    "_size_presets": {
        "small_meme": {"method": "scale", "width": "min(iw\\, W*0.3)", "height": -1},
        "medium_meme": {"method": "scale", "width": "min(iw\\, W*0.4)", "height": -1},
        "large_meme": {"method": "scale", "width": "min(iw\\, W*0.5)", "height": -1}
    }
}

def deep_update(source, overrides):
    """
    Update a nested dictionary or similar mapping.
    Modifies 'source' in place.
    """
    for key, value in overrides.items():
        if isinstance(value, dict) and key in source and isinstance(source[key], dict):
            deep_update(source[key], value)
        else:
            source[key] = value
    return source

def load_config(project_config_path):
    """
    Loads a project-specific JSON configuration file and merges it with the default config.
    Also resolves asset paths to be absolute or relative to a defined base.
    """
    if not os.path.exists(project_config_path):
        raise FileNotFoundError(f"Project configuration file not found: {project_config_path}")

    with open(project_config_path, 'r') as f:
        project_specific_config = json.load(f)

    # Start with a copy of the default config
    config = DEFAULT_CONFIG.copy()

    # Deep update with project-specific settings
    config = deep_update(config, project_specific_config)

    # Resolve paths: Make asset paths relative to 'assets_base_path' if not absolute
    # This makes project configs cleaner as they don't need to repeat the full base path.
    base_path = config.get("assets_base_path", "./assets") # Default if not in config

    # Helper to resolve path
    def resolve_path(p):
        if isinstance(p, str) and not os.path.isabs(p):
            return os.path.join(base_path, p)
        return p

    # Helper to resolve paths in a list
    def resolve_paths_in_list(path_list):
        if isinstance(path_list, list):
            return [resolve_path(p) for p in path_list]
        return resolve_path(path_list) # If it's a single string path by mistake

    path_keys_folders = [
        "intro_folder", "outro_folder", "bgm_folder", "voiceover_folder",
        "subtitle_folder_to_use_for_sentiment_analysis", "gif_folder", "sticker_folder_path"
    ]
    path_keys_files = ["watermark_path"]
    path_keys_list_folders = ["main_clips_videos_folders", "main_clips_images_folder"]

    for key in path_keys_folders:
        if key in config:
            config[key] = resolve_path(config[key])

    for key in path_keys_files:
        if key in config:
            config[key] = resolve_path(config[key]) # Also resolve single file paths

    for key in path_keys_list_folders:
        if key in config:
            config[key] = resolve_paths_in_list(config[key])

    if not os.path.exists(config["output_folder"]):
        os.makedirs(config["output_folder"], exist_ok=True)
        print(f"Created output directory: {config['output_folder']}")

    # Apply quality preset to encoding profile
    # This allows 'quality' to be a simple string like 'fast', 'balanced', 'high'
    # which then sets CRF/CQ values in the chosen encoder profile.
    quality_setting = config["final"].get("quality", "balanced")
    encoder_profile_name = config["final"].get("selected_encoder_profile", "none")

    if encoder_profile_name in config["final"]["_encoding_profiles"] and \
       quality_setting in config["final"]["_quality_presets"]:

        quality_values = config["final"]["_quality_presets"][quality_setting]
        profile_to_update = config["final"]["_encoding_profiles"][encoder_profile_name]

        if "crf" in profile_to_update and "crf" in quality_values: # For libx264
            profile_to_update["crf"] = quality_values["crf"]
        if "cq" in profile_to_update and "cq" in quality_values: # For nvenc
            profile_to_update["cq"] = quality_values["cq"]
        if "vquality" in profile_to_update and "vquality" in quality_values: # For QSV
            profile_to_update["vquality"] = quality_values["vquality"]

    # TODO: Add more comprehensive validation here (e.g., check if critical paths exist)

    return config

if __name__ == '__main__':
    # Example Usage:
    # Create a dummy project config file for testing
    dummy_project_config = {
        "project_name": "Test Video 001",
        "ENABLE_INTRO": True,
        "ENABLE_WATERMARK": True,
        "voiceover_to_use": "assets/voiceovers/sample_vo.mp3", # Example of a project specific override
        "final": {
            "resolution": [1280, 720], # Override resolution
            "quality": "fast",
            "selected_encoder_profile": "none" # Explicitly CPU for this test
        }
    }
    dummy_config_path = "configs/dummy_test_project.json"
    if not os.path.exists("configs"):
        os.makedirs("configs")
    with open(dummy_config_path, 'w') as f:
        json.dump(dummy_project_config, f, indent=2)

    print(f"Created dummy project config: {dummy_config_path}")

    # Create dummy assets path for the example to work
    if not os.path.exists("assets/voiceovers"): os.makedirs("assets/voiceovers")
    if not os.path.exists("assets/branding"): os.makedirs("assets/branding")
    # Create a dummy voiceover and watermark if they don't exist for path resolution testing
    if not os.path.exists("assets/voiceovers/sample_vo.mp3"): open("assets/voiceovers/sample_vo.mp3", 'a').close()
    if not os.path.exists("assets/branding/logo.png"): open("assets/branding/logo.png", 'a').close()


    try:
        loaded_settings = load_config(dummy_config_path)
        print("\nLoaded configuration:")
        # Using json.dumps for pretty printing the dict
        print(json.dumps(loaded_settings, indent=2, default=str)) # default=str for Path objects if any

        # Check if quality preset was applied
        print(f"\nEffective CRF for 'none' profile after 'fast' quality setting: {loaded_settings['final']['_encoding_profiles']['none'].get('crf')}")
        # Check path resolution
        print(f"Resolved watermark path: {loaded_settings['watermark_path']}")

    except FileNotFoundError as e:
        print(f"Error loading config: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    # Clean up dummy file
    # os.remove(dummy_config_path) # Keep it for now for easy re-testing
    print(f"\nconfig_loader.py loaded. Contains default config and loading function.")
    print(f"Test by creating a JSON file in 'configs/' and running 'python config_loader.py'")
