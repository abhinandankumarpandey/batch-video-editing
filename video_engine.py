import ffmpeg
import os

# Default config for FPS is not directly available here without importing config_loader
# Define a fallback or expect it from output_params
DEFAULT_FALLBACK_FPS = 30

def get_video_info(file_path):
    """Gets video information using ffmpeg.probe."""
    try:
        return ffmpeg.probe(file_path)
    except ffmpeg.Error as e:
        print(f"Error probing video {file_path}: {e.stderr.decode('utf8')}")
        return None

def combine_videos_and_watermark(video_files_and_image_specs, output_path, watermark_path=None, watermark_params=None, output_params=None, bgm_path=None, bgm_volume=0.25):
    """
    Combines multiple video files and images (as video segments) into one,
    optionally adds a watermark, and optionally mixes in background music.

    Args:
        video_files_and_image_specs (list): List of either:
            - strings (paths to video files)
            - dicts {'path': 'path/to/image.png', 'type': 'image', 'duration': 3.0}
        output_path (str): Path for the output video file.
        watermark_path (str, optional): Path to the watermark image.
        watermark_params (dict, optional): Parameters for watermark.
        output_params (dict, optional): Parameters for output video encoding.
        bgm_path (str, optional): Path to the background music audio file.
        bgm_volume (float, optional): Volume for the background music (0.0 to 1.0+).
    """
    if not video_files_and_image_specs:
        raise ValueError("No video files or image specifications provided.")

    input_video_streams = []
    input_audio_streams = [] # To hold audio from videos

    # Default output parameters if not provided
    final_output_params = {
        'vcodec': 'libx264', 'acodec': 'aac', 'pix_fmt': 'yuv420p',
        'threads': os.cpu_count() or 1 # Ensure at least 1 thread
    }
    if output_params:
        final_output_params.update(output_params)

    output_width, output_height = None, None
    if 'resolution' in final_output_params:
        res = final_output_params.get('resolution')
        if isinstance(res, str):
            output_width, output_height = map(int, res.split('x'))
        elif isinstance(res, (list, tuple)):
            output_width, output_height = res

    output_fps_val = final_output_params.get('fps', DEFAULT_FALLBACK_FPS)


    for item in video_files_and_image_specs:
        video_path = None
        item_duration = 0 # Will hold probed duration or spec duration for videos

        if isinstance(item, str): # Simple video file path string
            video_path = item
            # We'll try to probe duration later
        elif isinstance(item, dict) and item.get('type') == 'video': # Video spec as dict
            video_path = item.get('path')
            # Use spec's duration as fallback if probe fails or for initial silent audio length
            item_duration = item.get('duration', 0)
        elif isinstance(item, dict) and item.get('type') == 'image': # Image spec as dict
            img_path = item.get('path')
            img_duration = item.get('duration', 3.0)
            if not img_path or not os.path.exists(img_path):
                print(f"Warning: Image file not found or path is null: {img_path}. Skipping.")
                continue

            img_node = ffmpeg.input(img_path, loop=1, framerate=output_fps_val, t=img_duration)

            processed_img_video = img_node.video
            if output_width and output_height:
                scaled_img_video = ffmpeg.filter(img_node.video, 'scale', output_width, output_height, force_original_aspect_ratio='decrease')
                processed_img_video = ffmpeg.filter(scaled_img_video, 'pad', output_width, output_height, '-1', '-1', 'black')

            processed_img_video = ffmpeg.filter(processed_img_video, 'setsar', '1') # Ensure SAR is 1 for image-videos
            input_video_streams.append(processed_img_video)
            # Images always get silent audio for their duration
            silent_audio = ffmpeg.input(f'anullsrc=channel_layout=stereo:sample_rate=44100', format='lavfi', t=img_duration).audio
            input_audio_streams.append(silent_audio)
            continue # Processed image, move to next item in the loop
        else: # Invalid item type
            print(f"Warning: Invalid item in video_files_and_image_specs: {item}. Skipping.")
            continue

        # Common logic for video files (whether from string or dict)
        if video_path and os.path.exists(video_path):
            video_input_node = ffmpeg.input(video_path)


            processed_video_stream = video_input_node.video
            if output_width and output_height:
                # Scale and pad to fit output resolution, similar to images
                scaled_vid = ffmpeg.filter(processed_video_stream, 'scale', output_width, output_height, force_original_aspect_ratio='decrease')
                processed_video_stream = ffmpeg.filter(scaled_vid, 'pad', output_width, output_height, '-1', '-1', 'black')

            # Apply setsar=1 to actual video inputs too for consistency before concat
            processed_video_stream = ffmpeg.filter(processed_video_stream, 'setsar', '1')
            input_video_streams.append(processed_video_stream)

            probed_duration = 0.0
            has_audio_stream = False
            try:
                probe_data = ffmpeg.probe(video_path)
                probed_duration = float(probe_data.get('format', {}).get('duration', '0'))
                if any(s.get('codec_type') == 'audio' for s in probe_data.get('streams', [])):
                    has_audio_stream = True
            except ffmpeg.Error as e:
                 print(f"Warning: Probe failed for video {video_path} ({e.stderr.decode('utf8')}). Will use spec duration if available, or default for silent audio.")

            # Determine effective duration for audio track (prefer probe, then spec, then default for videos)
            effective_duration_for_audio = probed_duration if probed_duration > 0 else item_duration
            if effective_duration_for_audio <= 0: # If still no duration from probe or spec
                print(f"Warning: Video {video_path} has no determinable duration. Defaulting associated audio to 1s.")
                effective_duration_for_audio = 1.0 # Default to 1s if all else fails

            if has_audio_stream:
                input_audio_streams.append(video_input_node.audio)
            else:
                # Video has no audio stream or probe failed to confirm, add silent audio for its effective duration
                print(f"Video {video_path} has no audio stream or probe failed; adding silent audio for {effective_duration_for_audio}s.")
                silent_audio = ffmpeg.input(f'anullsrc=channel_layout=stereo:sample_rate=44100', format='lavfi', t=effective_duration_for_audio).audio
                input_audio_streams.append(silent_audio)
        elif video_path: # video_path was specified but file not found
            print(f"Warning: Video file not found: {video_path}. Skipping.")
            # No need to continue here, as the outer loop will continue
        # else: (item was invalid type, already handled by the first 'else' in the loop and continued)

    if not input_video_streams:
        raise ValueError("No valid video or image inputs to process after filtering.")

    if len(input_video_streams) != len(input_audio_streams):
        print(f"Critical Warning: Mismatch in video ({len(input_video_streams)}) and audio ({len(input_audio_streams)}) streams. This will likely cause concat to fail. Review stream generation logic.")
        # This is a fatal issue for ffmpeg.concat if streams aren't 1:1 video to audio.
        # Forcing a stop or trying to pad audio streams to match video streams count here is complex.
        # The logic above for silent audio generation for images and videos without audio MUST ensure counts match.
        # If this warning appears, there's a bug in that logic.
        raise ValueError("Video and audio stream counts for concatenation do not match.")

    # If v=1, a=0, concat itself should return the single video stream directly.
    joined_video_node = ffmpeg.concat(*input_video_streams, v=1, a=0)
    # Similarly for audio, if present.
    joined_audio_node = ffmpeg.concat(*input_audio_streams, v=0, a=1) if input_audio_streams else None

    # Resolution and FPS scaling (if not already done for images, or to ensure uniformity)
    # Note: If images were already scaled&padded, this scale might be redundant for them but ensures uniformity for videos.
    current_video_stream = joined_video_node
    # Removing post-concat scale and pad for now, as images are pre-scaled/padded
    # and videos will be handled by the final output node's scaling if dimensions differ.
    # if output_width and output_height:
    #      # Ensure final output resolution after concat, especially if videos had different ARs
    #     # current_video_stream = ffmpeg.filter(current_video_stream, 'setsar', '1') # Normalize SAR - Removing this line as it causes issues
    #     current_video_stream = ffmpeg.filter(current_video_stream, 'scale', output_width, output_height, eval='frame', force_original_aspect_ratio='decrease')
    #     current_video_stream = ffmpeg.filter(current_video_stream, 'pad', output_width, output_height, '-1', '-1', 'black')

    # Rely on output node to handle FPS based on final_output_params['fps']
    # if 'fps' in final_output_params: # Applying FPS to the concatenated stream is usually safe
    #     current_video_stream = ffmpeg.filter(current_video_stream, 'fps', fps=final_output_params['fps'], round='near')

    streams_for_final_output = []
    final_video_processing_stage = current_video_stream

    if watermark_path and os.path.exists(watermark_path):
        watermark_input_node = ffmpeg.input(watermark_path)
        wm_params = watermark_params or {}
        # wm_width_expr = wm_params.get('width', 'w*0.1') # This was an error, 'w' is not defined here for scale
        # wm_height_expr = wm_params.get('height', '-1')

        scaled_watermark_video = watermark_input_node.video
        # Robust watermark scaling: Scale watermark relative to output video width if known
        # Example: Scale watermark to be 10% of output video width, keep aspect ratio.
        # The 'scale' filter refers to its own input dimensions with W/H, not the main video.
        # Overlay is where you can reference main video width (main_w or W) and watermark input width (overlay_w or w).
        # Simpler: Scale watermark to an absolute size or fraction of ITS OWN size first.
        # For scaling relative to main video, it's more complex.
        # Let's use a fixed_width from params or default, then overlay.
        # Or, if output_width is known, scale it based on a fraction of that.
        if wm_params.get('width_is_fraction_of_video', False) and output_width:
            fraction = float(wm_params.get('width', '0.1')) # e.g. 0.1 for 10%
            target_wm_width = int(output_width * fraction)
            scaled_watermark_video = ffmpeg.filter(scaled_watermark_video, 'scale', target_wm_width, -1)
        elif wm_params.get('fixed_width'):
            scaled_watermark_video = ffmpeg.filter(scaled_watermark_video, 'scale', wm_params.get('fixed_width'), -1)
        else: # Default: scale to 10% of its own width (no, this is not useful) -> let's use 100px width
            scaled_watermark_video = ffmpeg.filter(scaled_watermark_video, 'scale', '100', -1)


        pos_x = wm_params.get('position_x', 'W-w-10') # W is main video, w is watermark
        pos_y = wm_params.get('position_y', '10')
        final_video_processing_stage = ffmpeg.overlay(final_video_processing_stage, scaled_watermark_video, x=pos_x, y=pos_y)

    streams_for_final_output.append(final_video_processing_stage)

    main_audio_final_stage = joined_audio_node

    if bgm_path and os.path.exists(bgm_path) and main_audio_final_stage:
        bgm_input_node = ffmpeg.input(bgm_path, stream_loop=-1)
        mixed_audio = ffmpeg.filter([main_audio_final_stage, bgm_input_node.audio], 'amix', inputs=2, duration='first', dropout_transition=0, weights=f"1 {bgm_volume}")
        streams_for_final_output.append(mixed_audio)
    elif main_audio_final_stage:
        streams_for_final_output.append(main_audio_final_stage)
    else:
        if 'acodec' in final_output_params :
             print("Warning: Audio codec specified but no audio streams (main or BGM) to output. Output might lack audio or fail if acodec is forced.")
             del final_output_params['acodec']
             if 'audio_bitrate' in final_output_params: del final_output_params['audio_bitrate']
             if 'ar' in final_output_params: del final_output_params['ar']
        pass

    if len(streams_for_final_output) == 1 and hasattr(streams_for_final_output[0], 'type') and streams_for_final_output[0].type == 'video':
        if 'acodec' in final_output_params: del final_output_params['acodec']
        if 'audio_bitrate' in final_output_params: del final_output_params['audio_bitrate']
        if 'ar' in final_output_params: del final_output_params['ar']

    # Ensure 'fps' from config is translated to 'r' for ffmpeg-python output
    if 'fps' in final_output_params:
        final_output_params['r'] = final_output_params.pop('fps')

    # Ensure 'resolution' from config is translated to 's' (size) for ffmpeg-python output
    if 'resolution' in final_output_params:
        res_val = final_output_params.pop('resolution')
        if isinstance(res_val, (list, tuple)) and len(res_val) == 2:
            final_output_params['s'] = f"{res_val[0]}x{res_val[1]}"
        elif isinstance(res_val, str): # Allow "WxH" string format as well
            final_output_params['s'] = res_val


    try:
        final_node = ffmpeg.output(*streams_for_final_output, output_path, **final_output_params)
        # For debugging: print("FFmpeg Command:", " ".join(final_node.compile()))
        final_node.run(overwrite_output=True, capture_stdout=True, capture_stderr=True)
        print(f"Video successfully created: {output_path}")
    except ffmpeg.Error as e:
        print(f"Error during ffmpeg processing for {output_path}:")
        cmd_str = "ffmpeg " + " ".join(e.cmd) if hasattr(e, 'cmd') and e.cmd else "Unknown command"
        print("FFmpeg command:", cmd_str)
        print("FFmpeg stdout:", e.stdout.decode('utf8') if hasattr(e, 'stdout') and e.stdout else "N/A")
        print("FFmpeg stderr:", e.stderr.decode('utf8') if hasattr(e, 'stderr') and e.stderr else "N/A")
        raise
    except Exception as ex:
        print(f"An unexpected error occurred in video_engine: {ex}")
        raise

if __name__ == '__main__':
    print("video_engine.py loaded. Contains core video processing functions.")
    print("This version includes image sequence handling and BGM mixing.")

    if not os.path.exists("output"): os.makedirs("output")
    if not os.path.exists("assets/images"): os.makedirs("assets/images")
    if not os.path.exists("assets/videos"): os.makedirs("assets/videos")
    if not os.path.exists("assets/audio"): os.makedirs("assets/audio")
    if not os.path.exists("assets/branding"): os.makedirs("assets/branding")

    dummy_video_path = "assets/videos/dummy_clip1.mp4"
    if not os.path.exists(dummy_video_path):
        try:
            ffmpeg.input('color=c=blue:s=128x72:d=1:r=25', format='lavfi', ).output(dummy_video_path, vcodec='libx264', acodec='aac').run(overwrite_output=True, capture_stderr=True) # Added acodec
            print(f"Created dummy video: {dummy_video_path}")
        except Exception as e:
            print(f"Could not create dummy video {dummy_video_path} (ffmpeg needed): {getattr(e, 'stderr', e)}")

    dummy_image_path = "assets/images/dummy_img1.png"
    if not os.path.exists(dummy_image_path) and os.path.exists(dummy_video_path):
         try:
            ffmpeg.input(dummy_video_path, ss=0.5).output(dummy_image_path, vframes=1).run(overwrite_output=True, capture_stderr=True)
            print(f"Created dummy image: {dummy_image_path}")
         except Exception as e:
            print(f"Could not create dummy image {dummy_image_path} (ffmpeg needed): {getattr(e, 'stderr', e)}")

    dummy_bgm_path = "assets/audio/dummy_bgm.mp3"
    if not os.path.exists(dummy_bgm_path):
        try:
            ffmpeg.input('anullsrc=channel_layout=stereo:sample_rate=44100', format='lavfi', t=5).output(dummy_bgm_path, acodec='mp3').run(overwrite_output=True, capture_stderr=True) # Added acodec
            print(f"Created dummy BGM: {dummy_bgm_path}")
        except Exception as e:
            print(f"Could not create dummy BGM {dummy_bgm_path} (ffmpeg needed): {getattr(e, 'stderr', e)}")

    dummy_watermark_path = "assets/branding/dummy_logo.png"
    if not os.path.exists(dummy_watermark_path) and os.path.exists(dummy_image_path):
        try:
            import shutil
            shutil.copy(dummy_image_path, dummy_watermark_path)
            print(f"Created dummy watermark: {dummy_watermark_path}")
        except Exception as e:
            print(f"Could not create dummy watermark: {e}")


    if os.path.exists(dummy_video_path) and os.path.exists(dummy_image_path):
        print("\n--- Attempting a test run of combine_videos_and_watermark ---")
        test_specs = [
            dummy_video_path,
            {'path': dummy_image_path, 'type': 'image', 'duration': 2.0},
            dummy_video_path
        ]
        test_output_path = "output/test_video_with_image_and_bgm.mp4"
        test_output_params = {'resolution': '128x72', 'fps': 25, 'vcodec': 'libx264', 'acodec': 'aac', 'audio_bitrate': '128k'}
        test_wm_params = {'position_x': '10', 'position_y': '10', 'fixed_width': '30'} # Test fixed_width

        try:
            combine_videos_and_watermark(
                video_files_and_image_specs=test_specs,
                output_path=test_output_path,
                watermark_path=dummy_watermark_path if os.path.exists(dummy_watermark_path) else None,
                watermark_params=test_wm_params,
                output_params=test_output_params,
                bgm_path=dummy_bgm_path if os.path.exists(dummy_bgm_path) else None,
                bgm_volume=0.15
            )
            print(f"Test run completed. Check: {test_output_path}")
            probe = get_video_info(test_output_path)
            if probe:
                 print(f"Output video duration: {probe.get('format',{}).get('duration')} seconds.")
                 # Expected duration: 1s video + 2s image + 1s video = 4s
                 # BGM is 5s but should be trimmed to video duration by amix duration='first'
            else:
                print("Probe of output video failed.")

        except Exception as e:
            print(f"Test run failed: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("Skipping direct test in video_engine.py __main__ because dummy assets could not be created (ffmpeg likely required).")
