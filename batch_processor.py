import argparse
import os
import json
import time
import random
import ffmpeg # Added for __main__ block's dummy asset creation
from config_loader import load_config, DEFAULT_CONFIG

from asset_manager import (select_voiceover, get_main_clips_data,
                           get_media_duration_seconds, _scan_folder_for_files,
                           select_bgm,
                           AUDIO_EXTENSIONS, VIDEO_EXTENSIONS, _get_file_basename)
from video_engine import combine_videos_and_watermark, get_video_info


def process_project(project_config_path):
    print(f"\nProcessing project: {project_config_path}")
    try:
        config = load_config(project_config_path)
        project_name = config.get("project_name", _get_file_basename(project_config_path))
        print(f"Successfully loaded configuration for: {project_name}")
    except FileNotFoundError:
        print(f"Error: Config file not found {project_config_path}")
        return
    except Exception as e:
        print(f"Error loading configuration {project_config_path}: {e}")
        import traceback
        traceback.print_exc()
        return

    selected_vo_path = select_voiceover(config)
    if not selected_vo_path:
        print(f"No suitable voiceover found for {project_name}, or project already processed. Skipping project.")
        return

    vo_duration = get_media_duration_seconds(selected_vo_path)
    if vo_duration <= 0:
        print(f"Warning: Voiceover {selected_vo_path} has zero or invalid duration. Processing may be unpredictable.")

    # The selected_vo_path is primarily for output naming and to ensure it's processed.
    # Actual audio from selected_vo_path is NOT automatically the main audio track unless it's part of a video.
    # The video_engine's combine_videos_and_watermark function takes audio from the video segments.
    # If selected_vo_path is an audio-only file, it should be explicitly handled:
    # e.g. by making it the first item in timeline_segments_for_engine IF video_engine can handle audio-only inputs as primary audio,
    # or by a dedicated parameter in video_engine.
    # For now, let's assume that if a voiceover is critical, it's part of one of the main video clips,
    # or it will be handled by a more advanced audio mixing strategy later.
    # The current video_engine primarily concatenates audio from video sources and then optionally adds BGM.

    main_clips_list = get_main_clips_data(config, target_duration_seconds=vo_duration)
    if not main_clips_list:
        print(f"No main clips selected for {project_name}. Skipping project.")
        return

    timeline_segments_for_engine = []

    if config.get("ENABLE_INTRO", False):
        intro_folder = config.get("intro_folder")
        if intro_folder and os.path.isdir(intro_folder):
            intro_files = _scan_folder_for_files(intro_folder, VIDEO_EXTENSIONS)
            if intro_files:
                chosen_intro = random.choice(intro_files)
                timeline_segments_for_engine.append(chosen_intro)
                print(f"Added intro: {chosen_intro}")
            else:
                print(f"Warning: ENABLE_INTRO is true, but no intro files found in {intro_folder}")
        else:
            print(f"Warning: ENABLE_INTRO is true, but intro_folder '{intro_folder}' is not valid or not found.")


    # Add Main Clips (both videos and images are now handled by video_engine via the list of dicts/paths)
    timeline_segments_for_engine.extend(main_clips_list)

    if config.get("ENABLE_OUTRO", False):
        outro_folder = config.get("outro_folder")
        if outro_folder and os.path.isdir(outro_folder):
            outro_files = _scan_folder_for_files(outro_folder, VIDEO_EXTENSIONS)
            if outro_files:
                chosen_outro = random.choice(outro_files)
                timeline_segments_for_engine.append(chosen_outro)
                print(f"Added outro: {chosen_outro}")
            else:
                print(f"Warning: ENABLE_OUTRO is true, but no outro files found in {outro_folder}")
        else:
             print(f"Warning: ENABLE_OUTRO is true, but outro_folder '{outro_folder}' is not valid or not found.")

    if not timeline_segments_for_engine:
        print(f"No video/image segments (intro, main, outro) to process for {project_name}. Skipping.")
        return

    output_basename = _get_file_basename(selected_vo_path)
    output_video_path = os.path.join(config["output_folder"], f"{output_basename}.mp4")

    watermark_file_path = None
    if config.get("ENABLE_WATERMARK", True): # Defaulting to True based on typical use
        watermark_file_path = config.get("watermark_path")
        if watermark_file_path and not os.path.exists(watermark_file_path):
            print(f"Warning: ENABLE_WATERMARK is true, but watermark file not found: {watermark_file_path}")
            watermark_file_path = None
        elif not watermark_file_path:
            print(f"Warning: ENABLE_WATERMARK is true, but no watermark_path specified in config.")


    bgm_file_path = None
    bgm_vol = config.get("bgm_volume", 0.25) # Default BGM volume from config or hardcoded
    if config.get("ENABLE_BGM", False): # Defaulting to False unless specified
        bgm_file_path = select_bgm(config)
        if bgm_file_path and not os.path.exists(bgm_file_path):
            print(f"Warning: BGM file selected '{bgm_file_path}' but not found. No BGM will be added.")
            bgm_file_path = None
        elif not bgm_file_path:
            print(f"ENABLE_BGM is true, but no BGM file could be selected from {config.get('bgm_folder')}.")


    final_config_params = config.get("final", {})
    # Ensure DEFAULT_CONFIG is used for fallbacks if keys are missing in project's final_config
    default_final_config = DEFAULT_CONFIG.get('final', {})

    selected_profile_name = final_config_params.get("selected_encoder_profile", default_final_config.get("selected_encoder_profile", "none"))

    # Start with a base from DEFAULT_CONFIG's profile, then overlay project's specific profile, then specific final params
    base_profile_params = default_final_config.get("_encoding_profiles", {}).get(selected_profile_name, {})
    project_profile_params = final_config_params.get("_encoding_profiles", {}).get(selected_profile_name, {})

    output_render_params = {
        'resolution': final_config_params.get('resolution', default_final_config.get('resolution')),
        'fps': final_config_params.get('fps', default_final_config.get('fps')),
        'vcodec': project_profile_params.get('vcodec', base_profile_params.get('vcodec', 'libx264')),
        'acodec': final_config_params.get('acodec', default_final_config.get('acodec', 'aac')),
        'audio_bitrate': final_config_params.get('abr', default_final_config.get('abr')) # Ensure 'abr' from config becomes 'audio_bitrate'
    }
    # Remove None values so they don't override ffmpeg-python defaults if not specified
    output_render_params = {k:v for k,v in output_render_params.items() if v is not None}


    # Apply encoding profile parameters (crf, preset, etc.)
    # Order of precedence: project_specific_final_config > project_profile > default_profile
    profile_keys = ['crf', 'preset', 'tune', 'cq', 'vquality'] # Removed 'extra_args' for special handling
    for key in profile_keys:
        if key in final_config_params: # Direct override in final config
             output_render_params[key] = final_config_params[key]
        elif key in project_profile_params: # From project's chosen profile
            output_render_params[key] = project_profile_params[key]
        elif key in base_profile_params: # From default config's chosen profile
            output_render_params[key] = base_profile_params[key]

    # Handle extra_args from the profile carefully (project or default)
    # Project profile extra_args take precedence over default profile extra_args
    project_extra_args = project_profile_params.get('extra_args', [])
    default_extra_args = base_profile_params.get('extra_args', [])
    # Simple merge: project args override default if both exist (though list extend is more common)
    # For this specific structure, let's assume project_extra_args is complete if provided.
    effective_extra_args = project_extra_args if project_extra_args else default_extra_args

    for arg in effective_extra_args:
        if arg.startswith("-x264-params"):
            # Ensure there's a space before splitting, otherwise value might be lost
            if " " in arg:
                output_render_params['x264-params'] = arg.split(" ", 1)[1]  # Use hyphenated key
            else: # Handle cases like "-x264-params" without a value, if that's ever valid (unlikely)
                output_render_params['x264-params'] = ""
        elif arg.startswith("-movflags"):
            if " " in arg:
                output_render_params['movflags'] = arg.split(" ", 1)[1]
            else:
                output_render_params['movflags'] = "" # e.g. if it was just "-movflags"
        elif arg.startswith("-pix_fmt"):
            # This is usually handled by the main 'pix_fmt' key, but if present in extra_args
            if " " in arg:
                output_render_params['pix_fmt'] = arg.split(" ", 1)[1]
        # Add more specific handlers if other extra_args are common
        else:
            parts = arg.split(" ", 1)
            if len(parts) == 2 and parts[0].startswith("-"):
                # ffmpeg-python often uses the option name without '-' as kwarg
                # This is a general guess and might not work for all ffmpeg options.
                # Example: -tune film -> tune='film' (already handled by profile_keys)
                # Example: -profile:v high -> profile_v='high' (needs manual mapping)
                # For safety, only add known/tested ones or provide a more robust parser.
                # For now, this is a placeholder for expansion.
                print(f"Warning: Unhandled extra_arg '{arg}' may not be correctly applied.")
            elif parts[0].startswith("-"): # Flag without value
                 # output_render_params[parts[0][1:]] = True # Or some other indicator
                 print(f"Warning: Unhandled valueless extra_arg '{arg}' may not be correctly applied.")


    print(f"Timeline segments for engine: {timeline_segments_for_engine}")
    print(f"Output video: {output_video_path}")
    print(f"Watermark: {watermark_file_path if watermark_file_path else 'No'}")
    print(f"BGM: {bgm_file_path if bgm_file_path else 'No'}, Volume: {bgm_vol if bgm_file_path else 'N/A'}")
    print(f"Output parameters: {output_render_params}")

    try:
        start_time = time.time()
        combine_videos_and_watermark(
            video_files_and_image_specs=timeline_segments_for_engine,
            output_path=output_video_path,
            watermark_path=watermark_file_path,
            watermark_params=config.get("watermark_params"), # Pass full watermark_params dict
            output_params=output_render_params,
            bgm_path=bgm_file_path,
            bgm_volume=bgm_vol
        )
        end_time = time.time()
        print(f"Project {project_name} processed successfully in {end_time - start_time:.2f} seconds.")
    except Exception as e:
        print(f"Error during processing {project_name}: {e}")
        import traceback
        traceback.print_exc()


def main():
    parser = argparse.ArgumentParser(description="Batch Video Processor")
    parser.add_argument("input_path",
                        help="Path to a single project JSON config file or a directory containing multiple .json config files.")
    args = parser.parse_args()

    if not os.path.exists(args.input_path):
        print(f"Error: Input path does not exist: {args.input_path}")
        return

    project_files_to_process = []
    if os.path.isdir(args.input_path):
        print(f"Scanning directory for project JSON files: {args.input_path}")
        for filename in os.listdir(args.input_path):
            if filename.lower().endswith(".json"):
                project_files_to_process.append(os.path.join(args.input_path, filename))
        if not project_files_to_process:
            print(f"No .json configuration files found in directory: {args.input_path}")
            return
        print(f"Found {len(project_files_to_process)} project configuration(s).")
    elif os.path.isfile(args.input_path) and args.input_path.lower().endswith(".json"):
        project_files_to_process.append(args.input_path)
    else:
        print("Error: Input path must be a .json file or a directory containing .json files.")
        return

    for project_config_file in project_files_to_process:
        process_project(project_config_file)
        print("-" * 50)

    print("\nBatch processing finished.")

if __name__ == "__main__":
    # This ensures that main() is called when the script is executed directly.
    # The main() function itself handles command line arguments via argparse.
    main()
