import argparse
import os
import glob
import importlib # To potentially reload config if modified by GUI
from concurrent.futures import ThreadPoolExecutor, as_completed

# Attempt to import global config first
try:
    from src import config as global_config
except ImportError:
    # This might happen if src is not in PYTHONPATH when run directly
    # For now, assume it works as part of a package or with PYTHONPATH set
    import config as global_config # Fallback for local testing if file is in same dir

# Import all necessary video processing functions
# This list will be long. Ensure all functions that create the final video are here.
from src.video_processing import (
    get_media_duration,
    get_main_clips_data,
    add_outro_data,
    combine_video_elements,
    apply_asthetic_frame,
    apply_watermark,
    add_background_music,
    apply_cinematic_effect,
    apply_subtitles_and_lut,
    add_gifs_based_on_subtitles,
    add_stickers_based_on_subtitles,
    add_greenscreen_memes_based_on_subtitles,
    add_sfx_according_to_emotion,
    add_additional_sfx
    # select_voiceover is not needed here as we iterate through files.
)
# Import GUI function if we want to be able to launch it from main
from src.gui import run_gui


def get_output_filename(voiceover_path):
    """Generates an output filename based on the voiceover filename."""
    base_name = os.path.splitext(os.path.basename(voiceover_path))[0]
    return os.path.join(global_config.OUTPUT_FOLDER, f"{base_name}.mp4")


def process_single_video(voiceover_path, current_config_dict, is_basic_mode=False):
    """
    Main pipeline for processing a single voiceover file into a video.
    - voiceover_path: Path to the voiceover audio file.
    - current_config_dict: A dictionary holding all config values (like those from src.config).
                           This allows for easier modification by GUI/CLI for a specific run
                           without directly altering the imported config module's state globally.
    - is_basic_mode: Boolean, if True, skips most optional effects.
    """
    print(f"Processing: {voiceover_path}")
    vo_filename_base = os.path.splitext(os.path.basename(voiceover_path))[0]
    output_video_path = get_output_filename(voiceover_path)

    # 0. Get Voiceover Duration
    vo_duration = get_media_duration(voiceover_path)
    if vo_duration <= 0:
        print(f"Error: Voiceover {voiceover_path} has invalid duration. Skipping.")
        return None, "VO duration error"

    # --- Initialize main video and audio streams ---
    # This is a conceptual representation. The actual ffmpeg streams are built progressively.
    # We start with information, then build ffmpeg objects.

    # 1. Get Main Clips (intro is handled within get_main_clips_data if enabled in config)
    # Pass relevant config values that get_main_clips_data might need.
    # For simplicity, assuming get_main_clips_data internally uses global_config or is adapted.
    # A better way: Pass a config snapshot.
    # For now, functions in video_processing.py directly use imported config.
    # This will be an issue if we want GUI to override config for a run.
    # Solution: Modify video_processing functions to accept a config dict.
    # For this step, I'll assume they use the global config, and --basic mode
    # will modify this global config (though not ideal).

    main_clips_list = get_main_clips_data(vo_duration) # Uses global_config settings
    if not main_clips_list:
        print(f"Error: Could not generate main clips for {voiceover_path}. Skipping.")
        return None, "Main clips error"

    # 2. Get Outro data (if enabled in config)
    outro_clip_data = add_outro_data() # Uses global_config

    # Assemble all primary clips for initial combination
    all_primary_clips = []
    all_primary_clips.extend(main_clips_list)
    if outro_clip_data: # and current_config_dict['ENABLE_OUTRO'] (already handled by add_outro_data)
        all_primary_clips.append(outro_clip_data)

    if not all_primary_clips:
        print(f"No primary clips to assemble for {voiceover_path}. Skipping.")
        return None, "No primary clips"

    # 3. Combine clips into a base video with the main voiceover
    # This function should return the initial video stream and audio stream (just voiceover)
    # For simplicity, let's assume combine_video_elements now primarily sets up the video track
    # and the main voiceover is the primary audio track.
    # The function definition of combine_video_elements needs to align with this.
    # It takes `main_voiceover_path` and returns a path to a temporary combined video.
    # This might need to be refactored to work with streams for overlays.

    # --- This is a major point of refactoring need for stream-based processing ---
    # For now, let's imagine combine_video_elements produces an initial ffmpeg.Stream object
    # or we build it here. The current combine_video_elements writes to a file.
    # This needs to be changed to return a stream that can be further processed.
    # This is a BIG assumption for this step, plan may need update for this refactor.

    # Conceptual stream building (FFMPEG OBJECTS):
    # Create initial video stream from combined clips
    # This is a placeholder for the actual stream creation logic
    # For now, we'll call combine_video_elements which writes a file, then read it back. This is inefficient.
    # TODO: Refactor combine_video_elements and subsequent functions to pass ffmpeg.Stream objects.

    temp_combined_path = os.path.join(global_config.OUTPUT_FOLDER, f"{vo_filename_base}_temp_combined.mp4")

    # This is where the main audio stream (voiceover) is first introduced.
    # The function `combine_video_elements` from video_processing.py already handles this.
    # It takes all_clips_data, output_filename, and main_voiceover_path.
    # It applies FINAL_RESOLUTION, FINAL_FPS, VOICEOVER_VOLUME, VOICEOVER_START from config.

    # To make it work with overlays, combine_video_elements should ideally return an ffmpeg Node/Stream object
    # representing the combined video and audio, not write to a file.
    # This is a significant change to the existing `combine_video_elements`.
    # For this planning step, I will assume this refactor is done or will be handled.
    # Let's denote the output of this stage as `base_video_stream` and `main_audio_stream`.

    # --- SIMPLIFIED APPROACH FOR THIS STEP (assuming combine_video_elements is a final step for now) ---
    # The current plan implies a sequential application of filters.
    # This means each function takes a stream and returns a stream.
    # `combine_video_elements` is currently the last step in video_processing.py's example.
    # This needs to be re-thought for a pipelined approach.

    # --- REVISED PIPELINE APPROACH (Conceptual) ---
    # 1. Video elements (intro, main, outro) are prepared as data.
    # 2. A base video stream is constructed using these elements (scaled, padded, fps set).
    # 3. Voiceover is prepared as the initial main audio stream.
    # 4. Overlays and effects are applied to the base video stream.
    # 5. Audio effects (SFX, BGM) are mixed into the main audio stream.
    # 6. Finally, the processed video and audio streams are muxed.

    # For this subtask, let's focus on the loop and calling structure,
    # assuming the video_processing functions can be chained.
    # We'll create a list of operations and then apply them.

    # --- Stage 1: Prepare video and audio inputs for ffmpeg.output ---
    # This is highly conceptual as ffmpeg-python builds a graph.

    # Let's assume the final video stream is 'current_video_stream'
    # and final audio is 'current_audio_stream'.

    # Initialize: Video is built from clips_data_list. Audio starts with voiceover.
    # This part needs a function like `prepare_base_video_stream_from_clips(all_primary_clips)`
    # and `prepare_voiceover_stream(voiceover_path)`.
    # These are not yet defined. This highlights a gap in `video_processing.py`.

    # For now, let the call to `combine_video_elements` be the "black box" that does everything
    # up to the point of needing overlays. This is not ideal for the filter pipeline.

    # To proceed with the current structure of video_processing.py, we would have to
    # make combine_video_elements the *very last* step.
    # OR, refactor all overlay functions to take file paths and produce new file paths,
    # which is very inefficient (multiple transcodes).

    # The best approach is to make all video_processing functions work with ffmpeg.Stream objects.
    # This is a MAJOR REFACTOR of video_processing.py.

    # --- Let's assume this refactor is done for the sake of this main.py logic ---
    # Placeholder: create a base video stream from all_primary_clips
    # This would involve ffmpeg.concat for video segments.
    # And scaling/padding each to FINAL_RESOLUTION and setting FINAL_FPS.
    # This is complex and should be encapsulated in video_processing.py.

    # For now, to make progress, this function will be simplified and represent a call to a
    # master processing function in video_processing.py that internally handles the pipeline.

    print(f"Calling master video processing for {voiceover_path} (conceptual)...")
    # This master function would take all necessary inputs and config.
    # success = process_video_pipeline(
    # voiceover_path=voiceover_path,
    # all_primary_clips_data=all_primary_clips,
    # output_path=output_video_path,
    # current_config_dict=current_config_dict, # or use global_config
    # is_basic_mode=is_basic_mode
    # )
    # For now, we'll just simulate success.
    # The actual calls to apply_watermark, add_gifs etc. would be inside process_video_pipeline.

    # --- Simplified main processing flow for THIS SUBTASK (will need refinement) ---
    # This assumes video_processing functions are adapted to take current_config_dict
    # or that we modify global_config temporarily (undesirable but simpler for now).

    # Create a list of video segments from all_primary_clips
    # This is where the video stream generation begins.
    # This part is missing from video_processing.py as a standalone stream generator.
    # For now, this step cannot be fully implemented without that refactor.

    # Let's assume `video_stream` and `audio_stream` are ffmpeg stream objects after initial setup.
    # This is a BIG assumption. The current `combine_video_elements` writes a file.
    # To truly chain effects, `combine_video_elements` needs to be broken down or return streams.

    # --- For the purpose of this step, let's define the *intended* pipeline structure ---
    # This structure assumes all processing functions in video_processing.py are refactored
    # to accept an input stream and return an output stream.

    # STAGE 1: Prepare initial video and audio streams (NEEDS NEW FUNCTIONS IN video_processing.py)
    # video_stream = create_concatenated_video_stream(all_primary_clips, current_config_dict)
    # audio_stream = create_voiceover_audio_stream(voiceover_path, current_config_dict)

    # If the above are not available, this function cannot be completed as a true pipeline.
    # We will have to rely on a more monolithic call or a sequence of file operations.

    # Given the current state, this function will be more of a high-level orchestrator
    # that calls a (yet to be fully defined/refactored) pipeline in video_processing.py.

    # For now, let's just print what would happen.
    print(f"  [Pipeline Start] for {vo_filename_base}")

    # These would be the ffmpeg stream objects
    # current_video_stream = ... initial video from clips ...
    # current_audio_stream = ... initial audio from voiceover ...

    # Example of applying effects (conceptual if streams are not ready)
    # if not is_basic_mode and current_config_dict.get('ENABLE_LUTS'):
    # current_video_stream = apply_subtitles_and_lut(current_video_stream, subtitle_for_display_path, lut_path)
    # if not is_basic_mode and current_config_dict.get('ENABLE_WATERMARK'):
    # current_video_stream = apply_watermark(current_video_stream, ...)
    # ... and so on for all visual effects ...

    # if not is_basic_mode and current_config_dict.get('ENABLE_GIFS'):
    # current_video_stream = add_gifs_based_on_subtitles(current_video_stream, vo_filename_base)
    # ... stickers, greenscreen ...

    # Audio pipeline
    # if not is_basic_mode and current_config_dict.get('ENABLE_SFX'): # Emotional SFX
    # current_audio_stream = add_sfx_according_to_emotion(current_audio_stream, vo_filename_base)
    # if not is_basic_mode and current_config_dict.get('ENABLE_ADDITONAL_SFX'):
    # total_duration = get_media_duration(output_video_path) # Problem: need duration before final output
    # current_audio_stream = add_additional_sfx(current_audio_stream, vo_duration) # Use VO duration as proxy
    # if not is_basic_mode and current_config_dict.get('ENABLE_BGM'):
    # current_audio_stream = add_background_music(None, current_audio_stream, ...) # Video stream not needed if duration from audio

    # Final muxing
    # ffmpeg.output(current_video_stream, current_audio_stream, output_video_path, ...).run()

    # Due to the major refactoring needed in video_processing.py for stream-based pipelining,
    # this function will remain largely conceptual for now.
    # The primary goal of this step is the batch looping and CLI integration.

    print(f"  [Conceptual] Video pipeline would run here for {vo_filename_base}.")
    print(f"  [Conceptual] Output would be: {output_video_path}")
    # Simulate success for now for batch processing structure.
    if os.path.exists(output_video_path): # If a previous test run created it
         print(f"Warning: Dummy output file {output_video_path} already exists. Will be overwritten if real processing runs.")
    # To simulate a successful run for testing the loop:
    try:
        with open(output_video_path, 'w') as f: # Create a dummy file
            f.write(f"Processed: {voiceover_path}")
        print(f"Dummy output file created: {output_video_path}")
        return output_video_path, "Success (simulated)"
    except IOError as e:
        print(f"Error creating dummy output file {output_video_path}: {e}")
        return None, "Dummy file creation error"


def main_cli():
    parser = argparse.ArgumentParser(description="Automatic Batch Video Maker CLI")
    parser.add_argument('--gui', action='store_true', help="Launch the GUI configuration panel.")
    parser.add_argument('--batch', action='store_true', help="Enable batch processing.")
    parser.add_argument('--voiceover', type=str, default=None, help="Path to a single voiceover file.")
    parser.add_argument('--max-videos', type=int, default=None, help="Max videos for batch.")
    parser.add_argument('--max-workers', type=int, default=1, help="Max concurrent workers.")
    parser.add_argument('--basic', action='store_true', help="Basic processing mode.")
    parser.add_argument('--output-dir', type=str, default=None, help="Override output directory from config.")

    args = parser.parse_args()

    # Update global config if output-dir is specified via CLI
    if args.output_dir:
        if os.path.isdir(args.output_dir):
            global_config.OUTPUT_FOLDER = args.output_dir
            print(f"Output folder overridden by CLI: {global_config.OUTPUT_FOLDER}")
        else:
            print(f"Warning: CLI specified output directory {args.output_dir} does not exist. Using config default.")

    # Ensure output folder exists
    if not os.path.exists(global_config.OUTPUT_FOLDER):
        try:
            os.makedirs(global_config.OUTPUT_FOLDER)
            print(f"Created output directory: {global_config.OUTPUT_FOLDER}")
        except OSError as e:
            print(f"Error: Could not create output directory {global_config.OUTPUT_FOLDER}: {e}")
            return

    if args.gui:
        print("Launching GUI...")
        run_gui() # from src.gui
        return

    # Make a copy of the current config state to pass to processing functions if needed
    # This is a shallow copy. Deep copy if functions modify nested dicts in config.
    current_run_config = {k: getattr(global_config, k) for k in dir(global_config) if not k.startswith('__')}

    is_basic = args.basic
    if is_basic:
        print("Basic mode enabled via CLI. Some features will be disabled.")
        # Modify current_run_config for basic mode (conceptual)
        # e.g., current_run_config['ENABLE_GIFS'] = False ... etc.
        # This is better than modifying global_config directly if it's passed around.
        # For now, process_single_video will check global_config or passed flags.

    if args.voiceover:
        if not os.path.exists(args.voiceover):
            print(f"Error: Specified voiceover file not found: {args.voiceover}")
            return
        print(f"Processing single voiceover: {args.voiceover}")
        # For single processing, max_workers is 1
        process_single_video(args.voiceover, current_run_config, is_basic_mode=is_basic)
    elif args.batch:
        print("Starting batch processing...")
        voiceover_files = glob.glob(os.path.join(global_config.VOICEOVER_FOLDER, '*.mp3')) + \
                          glob.glob(os.path.join(global_config.VOICEOVER_FOLDER, '*.wav')) + \
                          glob.glob(os.path.join(global_config.VOICEOVER_FOLDER, '*.aac'))

        if not voiceover_files:
            print(f"No voiceover files found in {global_config.VOICEOVER_FOLDER}")
            return

        new_voiceovers_to_process = []
        for vo_file in voiceover_files:
            if not os.path.exists(get_output_filename(vo_file)):
                new_voiceovers_to_process.append(vo_file)

        if not new_voiceovers_to_process:
            print("No new voiceovers to process. All seem to have existing output files.")
            return

        if args.max_videos is not None:
            new_voiceovers_to_process = new_voiceovers_to_process[:args.max_videos]

        print(f"Found {len(new_voiceovers_to_process)} new voiceover(s) to process.")

        if args.max_workers > 1 and len(new_voiceovers_to_process) > 1 :
            print(f"Using ThreadPoolExecutor with max_workers={args.max_workers}")
            with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
                futures = {executor.submit(process_single_video, vo_file, current_run_config, is_basic): vo_file for vo_file in new_voiceovers_to_process}
                for future in as_completed(futures):
                    vo_file = futures[future]
                    try:
                        result_path, status_msg = future.result()
                        if result_path:
                            print(f"Successfully processed (threaded): {os.path.basename(vo_file)} -> {result_path} ({status_msg})")
                        else:
                            print(f"Failed to process (threaded): {os.path.basename(vo_file)} - {status_msg}")
                    except Exception as exc:
                        print(f"Exception processing (threaded) {os.path.basename(vo_file)}: {exc}")
        else:
            print("Processing sequentially (max_workers=1 or single video).")
            for vo_file in new_voiceovers_to_process:
                result_path, status_msg = process_single_video(vo_file, current_run_config, is_basic)
                if result_path:
                    print(f"Successfully processed: {os.path.basename(vo_file)} -> {result_path} ({status_msg})")
                else:
                    print(f"Failed to process: {os.path.basename(vo_file)} - {status_msg}")
    else:
        print("No specific voiceover file provided and --batch flag not set.")
        parser.print_help()

if __name__ == '__main__':
    main_cli()
