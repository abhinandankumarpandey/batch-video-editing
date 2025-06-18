import ffmpeg
import os
import random
import glob
from src.config import ( # This is the new, combined import block
    OUTPUT_FOLDER, VOICEOVER_FOLDER, VOICEOVER_VOLUME, VOICEOVER_START,
    ENABLE_INTRO, MAIN_CLIPS_INTRO_FOLDER, MAIN_CLIPS_VIDEOS_FOLDERS,
    MAIN_CLIPS_IMAGES_FOLDER, UNIQUE_ASSETS, IMAGE_PERCENTAGE, VIDEO_MODE,
    DEFAULT_TRANSITIONS, ENABLE_TRANSITION, ENABLE_OUTRO, OUTRO_FOLDER,
    OUTRO_TRIM, FINAL_RESOLUTION, FINAL_FPS, DEFAULT_DATA, FINAL_CODEC,
    GIF_FOLDER, GIF_ANCHOR_POSITION, GIF_ANCHOR_MARGIN, GIF_SIZE_PRESET,
    FULL_SENTENCE_SUBTITLE_FOLDER,
    STICKER_FOLDER_PATH, STICKER_ANCHOR_POSITION, STICKER_ANCHOR_MARGIN, STICKER_SIZE_PRESET,
    GREENSCREEN_MEMES_FOLDER, GREENSCREEN_CHROMA_COLOR, GREENSCREEN_CHROMA_SIMILARITY,
    GREENSCREEN_CHROMA_BLEND, GREENSCREEN_ANCHOR_POSITION, GREENSCREEN_ANCHOR_MARGIN,
    GREENSCREEN_SIZE_METHOD, GREENSCREEN_SIZE_WIDTH,
    EMOTIONAL_SFX_FOLDER, # Added for emotional SFX
    ADDITIONAL_SFX_FOLDER, ADDITIONAL_SFX_MAX_PER_MINUTE, ADDITIONAL_SFX_VOLUME # Added for additional SFX
)
from src.utils import parse_srt_file, get_text_emotion

def get_asset_files(folder_or_folders, file_types=('.mp4', '*.avi', '*.mov', '*.mkv', '*.png', '*.jpg', '*.jpeg')):
    files = []
    if isinstance(folder_or_folders, str):
        folder_or_folders = [folder_or_folders]
    for folder in folder_or_folders:
        if not os.path.isdir(folder):
            print(f"Warning: Folder not found: {folder}")
            continue
        for file_type in file_types:
            files.extend(glob.glob(os.path.join(folder, file_type)))
    return files

def get_media_duration(media_path):
    try:
        probe = ffmpeg.probe(media_path)
        video_stream = next((s for s in probe['streams'] if s['codec_type'] == 'video'), None)
        if video_stream and 'duration' in video_stream:
            return float(video_stream['duration'])
        audio_stream = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), None)
        if audio_stream and 'duration' in audio_stream:
            return float(audio_stream['duration'])
        return 0
    except ffmpeg.Error as e:
        print(f"Error probing media {media_path}: {e.stderr.decode('utf8', errors='ignore')}")
        return 0
    except Exception as e:
        print(f"An unexpected error probing {media_path}: {e}")
        return 0

def select_voiceover(processed_vo_cache):
    available_voiceovers = get_asset_files(VOICEOVER_FOLDER, file_types=('*.mp3', '*.wav', '*.aac'))
    if not available_voiceovers:
        print(f"No voiceovers in {VOICEOVER_FOLDER}")
        return None, None
    random.shuffle(available_voiceovers)
    for vo_path in available_voiceovers:
        vo_basename = os.path.splitext(os.path.basename(vo_path))[0]
        if vo_basename not in processed_vo_cache:
            duration = get_media_duration(vo_path)
            if duration > 0:
                print(f"Selected voiceover: {vo_path}, Duration: {duration:.2f}s")
                return vo_path, duration
            else:
                print(f"Warning: Voiceover {vo_path} invalid duration. Skipping.")
    print("No new voiceovers to process.")
    return None, None

def get_main_clips_data(voiceover_duration_target):
    main_clips = []
    current_total_duration = 0
    selected_asset_paths = set()

    if ENABLE_INTRO:
        intro_files = get_asset_files(MAIN_CLIPS_INTRO_FOLDER, file_types=('*.mp4', '*.mov'))
        if intro_files:
            intro_path = random.choice(intro_files)
            if UNIQUE_ASSETS: selected_asset_paths.add(intro_path)
            intro_dur = get_media_duration(intro_path)
            if intro_dur > 0:
                main_clips.append({"path": intro_path, "type": "video", "duration": intro_dur, "trim": {"start": 0, "end": intro_dur}, "transitions": DEFAULT_TRANSITIONS if ENABLE_TRANSITION else None})
                current_total_duration += intro_dur
                print(f"Added intro: {os.path.basename(intro_path)}, duration: {intro_dur:.2f}s")

    video_pool = get_asset_files(MAIN_CLIPS_VIDEOS_FOLDERS, file_types=('*.mp4', '*.mov', '*.mkv'))
    image_pool = get_asset_files(MAIN_CLIPS_IMAGES_FOLDER, file_types=('*.png', '*.jpg', '*.jpeg'))
    if UNIQUE_ASSETS:
        video_pool = [f for f in video_pool if f not in selected_asset_paths]
        image_pool = [f for f in image_pool if f not in selected_asset_paths]
    random.shuffle(video_pool)
    random.shuffle(image_pool)
    IMAGE_FIXED_DURATION = 5.0

    while current_total_duration < voiceover_duration_target:
        is_image_next = (random.randint(1, 100) <= IMAGE_PERCENTAGE and image_pool) or not video_pool
        chosen_asset_path = None; asset_type = None; asset_duration_to_use = 0; trim_spec = None

        if is_image_next and image_pool:
            chosen_asset_path = image_pool.pop(0) if UNIQUE_ASSETS else random.choice(image_pool)
            if UNIQUE_ASSETS: selected_asset_paths.add(chosen_asset_path)
            asset_type = "image"; asset_duration_to_use = IMAGE_FIXED_DURATION
        elif video_pool:
            chosen_asset_path = video_pool.pop(0) if UNIQUE_ASSETS else random.choice(video_pool)
            if UNIQUE_ASSETS: selected_asset_paths.add(chosen_asset_path)
            asset_type = "video"
            native_video_dur = get_media_duration(chosen_asset_path)
            if native_video_dur <= 0: continue
            remaining_needed = voiceover_duration_target - current_total_duration
            if VIDEO_MODE == "full_clip":
                asset_duration_to_use = min(native_video_dur, remaining_needed)
                trim_spec = {"start": 0, "end": asset_duration_to_use}
            else:
                asset_duration_to_use = min(native_video_dur, remaining_needed)
                trim_spec = {"start": 0, "end": asset_duration_to_use}
        else: break

        if chosen_asset_path and asset_duration_to_use > 0:
            main_clips.append({"path": chosen_asset_path, "type": asset_type, "duration": asset_duration_to_use, "trim": trim_spec, "transitions": DEFAULT_TRANSITIONS if ENABLE_TRANSITION else None})
            current_total_duration += asset_duration_to_use
        if UNIQUE_ASSETS and not image_pool and not video_pool: break

    if main_clips and current_total_duration > voiceover_duration_target:
        overage = current_total_duration - voiceover_duration_target
        last_clip = main_clips[-1]
        if last_clip["duration"] > overage + 0.1:
            last_clip["duration"] -= overage
            if last_clip["type"] == "video" and last_clip["trim"]: last_clip["trim"]["end"] -= overage

    print(f"Prepared {len(main_clips)} main clips. Total duration: {current_total_duration:.2f}s")
    return main_clips

def add_outro_data():
    if not ENABLE_OUTRO: return None
    outro_files = get_asset_files(OUTRO_FOLDER, file_types=('*.mp4', '*.mov'))
    if not outro_files: return None
    outro_path = random.choice(outro_files)
    outro_native_dur = get_media_duration(outro_path)
    if outro_native_dur <= 0: return None
    start = OUTRO_TRIM.get("start", 0); end = min(OUTRO_TRIM.get("end", outro_native_dur), outro_native_dur)
    actual_dur = end - start
    if actual_dur <= 0: return None
    print(f"Prepared outro: {os.path.basename(outro_path)}, duration: {actual_dur:.2f}s")
    return {"path": outro_path, "type": "video", "duration": actual_dur, "trim": {"start": start, "end": end}, "transitions": {"in": "fade", "out": None} if ENABLE_TRANSITION else None}

def combine_video_elements(all_clips_data, output_filename, main_voiceover_path=None):
    if not all_clips_data: return None
    video_segments = []; audio_segments_from_clips = []

    for clip in all_clips_data:
        input_node = ffmpeg.input(clip['path'])
        v_seg = input_node.video; a_seg = input_node.audio if 'audio' in input_node.streams else None
        if clip['type'] == 'video':
            if clip.get('trim'):
                v_seg = v_seg.trim(start=clip['trim']['start'], end=clip['trim']['end']).setpts('PTS-STARTPTS')
                if a_seg: a_seg = a_seg.filter('atrim', start=clip['trim']['start'], end=clip['trim']['end']).filter('asetpts', 'PTS-STARTPTS')
        elif clip['type'] == 'image':
            v_seg = v_seg.loop(loop=-1, time=clip['duration']).trim(duration=clip['duration']).setpts('PTS-STARTPTS')
            a_seg = ffmpeg.input(f"anullsrc=channel_layout=stereo:sample_rate=48000", format='lavfi', t=clip['duration']).audio

        v_seg = v_seg.filter('scale', FINAL_RESOLUTION[0], FINAL_RESOLUTION[1], force_original_aspect_ratio='decrease').filter('pad', FINAL_RESOLUTION[0], FINAL_RESOLUTION[1], '(ow-iw)/2', '(oh-ih)/2', 'black').filter('fps', FINAL_FPS, round='up')
        video_segments.append(v_seg)
        audio_segments_from_clips.append(a_seg if a_seg else ffmpeg.input(f"anullsrc=channel_layout=stereo:sample_rate=48000", format='lavfi', t=clip['duration']).audio)

    if not video_segments: return None
    concatenated_video = ffmpeg.concat(*video_segments, v=1, a=0).node

    final_audio_stream = None
    if main_voiceover_path:
        vo_input = ffmpeg.input(main_voiceover_path)
        processed_vo = vo_input.audio.filter('volume', VOICEOVER_VOLUME)
        if VOICEOVER_START > 0:
            silence = ffmpeg.input(f"anullsrc=channel_layout=stereo:sample_rate=48000", format='lavfi', t=VOICEOVER_START).audio
            processed_vo = ffmpeg.concat(silence, processed_vo, v=0, a=1).node
        final_audio_stream = processed_vo
    elif audio_segments_from_clips:
        final_audio_stream = ffmpeg.concat(*audio_segments_from_clips, v=0, a=1).node
    else:
        total_duration_est = sum(c.get('duration', 0) for c in all_clips_data)
        if total_duration_est > 0:
            final_audio_stream = ffmpeg.input(f"anullsrc=channel_layout=stereo:sample_rate=48000", format='lavfi', t=total_duration_est).audio

    output_params = {}
    profile_name = FINAL_CODEC if FINAL_CODEC in DEFAULT_DATA['final']['_encoding_profiles'] else 'none'
    profile = DEFAULT_DATA['final']['_encoding_profiles'][profile_name]
    output_params['vcodec'] = profile['vcodec']
    output_params['acodec'] = DEFAULT_DATA['final']['acodec']
    output_params['audio_bitrate'] = DEFAULT_DATA['final']['abr']
    for key in ['preset', 'crf', 'cq']:
        if key in profile: output_params[key] = profile[key]
    if 'vquality' in profile: output_params['global_quality'] = profile['vquality']
    extra_args = profile.get('extra_args', [])

    full_output_path = os.path.join(OUTPUT_FOLDER, output_filename)
    try:
        stream_spec = [concatenated_video]
        if final_audio_stream: stream_spec.append(final_audio_stream)
        (ffmpeg.output(*stream_spec, full_output_path, **output_params)
         .overwrite_output().run(capture_stdout=True, capture_stderr=True))
        print(f"Successfully created video: {full_output_path}")
        return full_output_path
    except ffmpeg.Error as e:
        print(f"FFmpeg Error for {full_output_path}: {e.stderr.decode('utf8', errors='ignore')}")
        return None
    except Exception as e:
        print(f"General error for {full_output_path}: {e}")
        return None

# --- Basic Overlay and Effect Functions ---
def apply_asthetic_frame(video_stream, frame_path, position, margin, size_config):
    if not (frame_path and os.path.exists(frame_path)):
        print(f"Warning: Aesthetic frame path not found or not specified: {frame_path}")
        return video_stream
    frame_input = ffmpeg.input(frame_path)
    frame_video = frame_input.video
    if size_config.get('method') == 'stretch' and size_config.get('width') == 'W' and size_config.get('height') == 'H':
        frame_video = frame_video.filter('scale', width=FINAL_RESOLUTION[0], height=FINAL_RESOLUTION[1])
    else:
        print(f"Warning: Unsupported frame size config: {size_config}. Defaulting to stretch.")
        frame_video = frame_video.filter('scale', width=FINAL_RESOLUTION[0], height=FINAL_RESOLUTION[1])
    print(f"Applying aesthetic frame: {os.path.basename(frame_path)}")
    return ffmpeg.overlay(video_stream, frame_video, x='0', y='0', eof_action='repeat')

def apply_watermark(video_stream, wm_path, position_key, margin_eval, size_w_eval, when_eval):
    if not (wm_path and os.path.exists(wm_path)):
        print(f"Warning: Watermark path not found or not specified: {wm_path}")
        return video_stream
    watermark_input = ffmpeg.input(wm_path)
    watermark_video = watermark_input.video.filter('scale', width=size_w_eval, height='-1')
    pos_template = DEFAULT_DATA['ANCHOR_POSITIONS'].get(position_key)
    if not pos_template:
        print(f"Warning: Watermark position key '{position_key}' not found. Defaulting to top-left.")
        pos_template = DEFAULT_DATA['ANCHOR_POSITIONS']['top-left']
    overlay_x = pos_template[0].format(mx=margin_eval['x'])
    overlay_y = pos_template[1].format(my=margin_eval['y'])
    print(f"Applying watermark: {os.path.basename(wm_path)} at {position_key} ({overlay_x}, {overlay_y})")
    enable_str = f"between(t,{when_eval['start']},{when_eval['end']})"
    return ffmpeg.overlay(video_stream, watermark_video, x=overlay_x, y=overlay_y, enable=enable_str, eof_action='repeat')

def add_background_music(video_stream, audio_stream_existing, bgm_path, loop, volume, start_time, end_time):
    if not (bgm_path and os.path.exists(bgm_path)):
        print(f"Warning: BGM path not found or not specified: {bgm_path}")
        return audio_stream_existing
    bgm_input = ffmpeg.input(bgm_path)
    bgm_audio = bgm_input.audio.filter('volume', volume)
    if audio_stream_existing is None:
        print(f"No existing audio, using BGM: {os.path.basename(bgm_path)}")
        return bgm_audio
    print(f"Adding BGM: {os.path.basename(bgm_path)}")
    mixed_audio = ffmpeg.filter([audio_stream_existing, bgm_audio], 'amix', inputs=2, duration='longest', dropout_transition=0)
    return mixed_audio

def apply_cinematic_effect(video_stream, effect_path, when_eval, size_eval, anchor_eval, opacity_val):
    if not (effect_path and os.path.exists(effect_path)):
        print(f"Warning: Cinematic effect path not found or not specified: {effect_path}")
        return video_stream
    effect_input = ffmpeg.input(effect_path, stream_loop=-1)
    effect_video = effect_input.video
    if size_eval.get('method') == 'stretch' and size_eval.get('width') == 'W' and size_eval.get('height') == 'H':
        effect_video = effect_video.filter('scale', width=FINAL_RESOLUTION[0], height=FINAL_RESOLUTION[1])
    if opacity_val < 1.0:
        print(f"Note: Opacity ({opacity_val}) for cinematic effect is noted, but direct application is complex and may depend on asset format.")
    overlay_x = '0'
    overlay_y = '0'
    if anchor_eval.get('position') == 'center' and not (size_eval.get('width') == 'W' and size_eval.get('height') == 'H'):
        overlay_x = '(main_w-overlay_w)/2'
        overlay_y = '(main_h-overlay_h)/2'
    print(f"Applying cinematic effect: {os.path.basename(effect_path)}")
    enable_str = f"between(t,{when_eval['start']},{when_eval['end']})"
    return ffmpeg.overlay(video_stream, effect_video, x=overlay_x, y=overlay_y, enable=enable_str, shortest=False, eof_action='pass')

# --- Subtitle and LUT Application ---
def apply_subtitles_and_lut(video_stream, subtitle_file_path, lut_file_path):
    processed_stream = video_stream
    if subtitle_file_path and os.path.exists(subtitle_file_path):
        print(f"Applying subtitles from: {os.path.basename(subtitle_file_path)}")
        processed_stream = processed_stream.filter('subtitles', filename=subtitle_file_path)
    elif subtitle_file_path:
        print(f"Warning: Subtitle file not found: {subtitle_file_path}")
    if lut_file_path and os.path.exists(lut_file_path):
        print(f"Applying LUT: {os.path.basename(lut_file_path)}")
        processed_stream = processed_stream.filter('lut3d', file=lut_file_path, interp='trilinear')
    elif lut_file_path:
        print(f"Warning: LUT file not found: {lut_file_path}")
    return processed_stream

# --- Emotion-Based Dynamic Content Functions ---
def get_video_processing_asset_files(folder_or_folders, file_types=('.gif', '*.png', '*.mp4')):
    """Gets all files of specified types from a folder or list of folders."""
    files = []
    if isinstance(folder_or_folders, str):
        folder_or_folders = [folder_or_folders]
    for folder in folder_or_folders:
        if not os.path.isdir(folder):
            print(f"Warning: Asset folder not found: {folder}")
            continue
        for file_type in file_types:
            files.extend(glob.glob(os.path.join(folder, file_type)))
    return files

def add_gifs_based_on_subtitles(video_stream_input, voiceover_basename_for_srt_match):
    """
    Analyzes subtitles for emotion and overlays relevant GIFs using a complex filter graph.
    - video_stream_input: The main ffmpeg.Stream for the video (e.g., output of previous step).
    - voiceover_basename_for_srt_match: Base name of VO file to find matching .srt.
    Returns a new video stream with GIFs overlaid, or original if issues.
    """
    srt_file_path = os.path.join(FULL_SENTENCE_SUBTITLE_FOLDER, f"{voiceover_basename_for_srt_match}.srt")

    if not os.path.exists(srt_file_path):
        print(f"SRT file {srt_file_path} not found for GIF analysis. Skipping GIF overlays.")
        return video_stream_input

    subtitles = parse_srt_file(srt_file_path)
    if not subtitles:
        print(f"No subtitles parsed from {srt_file_path}. Skipping GIF overlays.")
        return video_stream_input

    print(f"Analyzing {len(subtitles)} subtitle entries from {srt_file_path} for GIF opportunities...")

    gif_data_to_overlay = []

    for sub_entry in subtitles:
        text = sub_entry['text']
        emotion, logits = get_text_emotion(text)

        if emotion != 'neutral':
            gif_emotion_folder = os.path.join(GIF_FOLDER, emotion)
            if os.path.isdir(gif_emotion_folder):
                possible_gifs = get_video_processing_asset_files(gif_emotion_folder, file_types=('*.gif',))
                if possible_gifs:
                    selected_gif_path = random.choice(possible_gifs)
                    gif_data_to_overlay.append({
                        'path': selected_gif_path,
                        'start_time': sub_entry['start'],
                        'end_time': sub_entry['end'],
                        'emotion': emotion
                    })
                    print(f"  Found GIF for emotion '{emotion}': {os.path.basename(selected_gif_path)} for sub: '{text[:30]}...'")

    if not gif_data_to_overlay:
        print("No suitable GIFs found or emotions detected for overlay.")
        return video_stream_input

    all_ffmpeg_inputs = [video_stream_input]
    for i, gif_info in enumerate(gif_data_to_overlay):
        all_ffmpeg_inputs.append(ffmpeg.input(gif_info['path'], ignore_loop=0))

    filter_chain_str = ""
    last_video_label = "[0:v]"

    for i, gif_info in enumerate(gif_data_to_overlay):
        gif_input_label = f"[{i+1}:v]"
        size_preset_ref = GIF_SIZE_PRESET.split('.')[-1] if '.' in GIF_SIZE_PRESET else GIF_SIZE_PRESET
        size_preset_data = DEFAULT_DATA['_size_presets'].get(size_preset_ref)

        if not size_preset_data:
            print(f"Warning: GIF size preset '{GIF_SIZE_PRESET}' (ref: '{size_preset_ref}') not found. Using default scaling.")
            gif_width_eval = "iw*0.3"
            gif_height_eval = "-1"
        else:
            gif_width_eval = size_preset_data['width'].replace('W', str(FINAL_RESOLUTION[0])).replace('iw', 'iw')
            gif_height_eval = str(size_preset_data['height'])

        pos_template = DEFAULT_DATA['ANCHOR_POSITIONS'].get(GIF_ANCHOR_POSITION)
        if not pos_template:
            print(f"Warning: GIF anchor position '{GIF_ANCHOR_POSITION}' not found. Defaulting to bottom-left.")
            pos_template = DEFAULT_DATA['ANCHOR_POSITIONS']['bottom-left']

        x_pos_str = pos_template[0].replace("{mx}", GIF_ANCHOR_MARGIN['x'])
        y_pos_str = pos_template[1].replace("{my}", GIF_ANCHOR_MARGIN['y'])

        enable_str = f"between(t,{gif_info['start_time']},{gif_info['end_time']})"
        current_overlay_label = f"[v_gif_out_{i}]"
        scaled_gif_label = f"[scaled_gif_{i}]"

        filter_chain_str += f"{gif_input_label}scale=width={gif_width_eval}:height={gif_height_eval}{scaled_gif_label};"
        filter_chain_str += f"{last_video_label}{scaled_gif_label}overlay=x='{x_pos_str}':y='{y_pos_str}':shortest=0:enable='{enable_str}'{current_overlay_label};"

        last_video_label = current_overlay_label

    if not filter_chain_str:
        return video_stream_input

    final_filter_chain = filter_chain_str.rstrip(';')

    print(f"Applying {len(gif_data_to_overlay)} GIFs using filter_complex.")
    try:
        processed_video_stream = ffmpeg.filter_complex(all_ffmpeg_inputs, final_filter_chain, **{'map': last_video_label})
        return processed_video_stream
    except ffmpeg.Error as e:
        print(f"Error applying GIF overlays with filter_complex: {e.stderr.decode('utf8', errors='ignore')}")
        return video_stream_input
    except Exception as e_gen:
        print(f"General error in add_gifs_based_on_subtitles: {e_gen}")
        return video_stream_input

def add_stickers_based_on_subtitles(video_stream_input, voiceover_basename_for_srt_match):
    """
    Analyzes subtitles for emotion and overlays relevant stickers (PNGs).
    - video_stream_input: The main ffmpeg.Stream for the video.
    - voiceover_basename_for_srt_match: Base name of VO file to find matching .srt.
    Returns a new video stream with stickers overlaid, or original if issues.
    """
    # Configs are now expected to be imported at the top of the module.
    srt_file_path = os.path.join(FULL_SENTENCE_SUBTITLE_FOLDER, f"{voiceover_basename_for_srt_match}.srt")

    if not os.path.exists(srt_file_path):
        print(f"SRT file {srt_file_path} not found for Sticker analysis. Skipping sticker overlays.")
        return video_stream_input

    subtitles = parse_srt_file(srt_file_path)
    if not subtitles:
        print(f"No subtitles parsed from {srt_file_path}. Skipping sticker overlays.")
        return video_stream_input

    print(f"Analyzing {len(subtitles)} subtitle entries from {srt_file_path} for Sticker opportunities...")

    sticker_data_to_overlay = []

    for sub_entry in subtitles:
        text = sub_entry['text']
        emotion, _ = get_text_emotion(text)

        if emotion != 'neutral':
            sticker_emotion_folder = os.path.join(STICKER_FOLDER_PATH, emotion)
            if os.path.isdir(sticker_emotion_folder):
                possible_stickers = get_video_processing_asset_files(sticker_emotion_folder, file_types=('*.png',))
                if possible_stickers:
                    selected_sticker_path = random.choice(possible_stickers)
                    sticker_data_to_overlay.append({
                        'path': selected_sticker_path,
                        'start_time': sub_entry['start'],
                        'end_time': sub_entry['end'],
                        'emotion': emotion
                    })
                    print(f"  Found Sticker for emotion '{emotion}': {os.path.basename(selected_sticker_path)} for sub: '{text[:30]}...'")

    if not sticker_data_to_overlay:
        print("No suitable stickers found or emotions detected for overlay.")
        return video_stream_input

    all_ffmpeg_inputs = [video_stream_input]
    for sticker_info in sticker_data_to_overlay:
        all_ffmpeg_inputs.append(ffmpeg.input(sticker_info['path']))

    filter_chain_str = ""
    last_video_label = "[0:v]"

    for i, sticker_info in enumerate(sticker_data_to_overlay):
        sticker_input_label = f"[{i+1}:v]"

        size_preset_ref = STICKER_SIZE_PRESET.split('.')[-1] if '.' in STICKER_SIZE_PRESET else STICKER_SIZE_PRESET
        size_preset_data = DEFAULT_DATA['_size_presets'].get(size_preset_ref)
        if not size_preset_data:
            print(f"Warning: Sticker size preset '{STICKER_SIZE_PRESET}' (ref: '{size_preset_ref}') not found. Using default.")
            sticker_width_eval = "iw*0.2"
            sticker_height_eval = "-1"
        else:
            sticker_width_eval = size_preset_data['width'].replace('W', str(FINAL_RESOLUTION[0])).replace('iw', 'iw')
            sticker_height_eval = str(size_preset_data['height'])

        pos_template = DEFAULT_DATA['ANCHOR_POSITIONS'].get(STICKER_ANCHOR_POSITION)
        if not pos_template:
            print(f"Warning: Sticker anchor '{STICKER_ANCHOR_POSITION}' not found. Defaulting to top-left.")
            pos_template = DEFAULT_DATA['ANCHOR_POSITIONS']['top-left']

        x_pos_str = pos_template[0].replace("{mx}", STICKER_ANCHOR_MARGIN['x'])
        y_pos_str = pos_template[1].replace("{my}", STICKER_ANCHOR_MARGIN['y'])

        enable_str = f"between(t,{sticker_info['start_time']},{sticker_info['end_time']})"
        current_overlay_label = f"[v_sticker_out_{i}]"
        scaled_sticker_label = f"[scaled_sticker_{i}]"

        filter_chain_str += f"{sticker_input_label}scale=width={sticker_width_eval}:height={sticker_height_eval}{scaled_sticker_label};"
        filter_chain_str += f"{last_video_label}{scaled_sticker_label}overlay=x='{x_pos_str}':y='{y_pos_str}':enable='{enable_str}'{current_overlay_label};"

        last_video_label = current_overlay_label

    if not filter_chain_str:
        return video_stream_input

    final_filter_chain = filter_chain_str.rstrip(';')

    print(f"Applying {len(sticker_data_to_overlay)} stickers using filter_complex.")
    try:
        processed_video_stream = ffmpeg.filter_complex(all_ffmpeg_inputs, final_filter_chain, **{'map': last_video_label})
        return processed_video_stream

    except ffmpeg.Error as e:
        print(f"Error applying Sticker overlays with filter_complex: {e.stderr.decode('utf8', errors='ignore')}")
        return video_stream_input
    except Exception as e_gen:
        print(f"General error in add_stickers_based_on_subtitles: {e_gen}")
        return video_stream_input

def add_greenscreen_memes_based_on_subtitles(video_stream_input, voiceover_basename_for_srt_match):
    """
    Analyzes subtitles for emotion and overlays relevant chroma-keyed green screen memes.
    - video_stream_input: The main ffmpeg.Stream for the video.
    - voiceover_basename_for_srt_match: Base name of VO file to find matching .srt.
    Returns a new video stream with memes overlaid, or original if issues.
    Note: Audio from memes is NOT currently mixed in this version.
    """
    # Configs like GREENSCREEN_MEMES_FOLDER are now expected to be imported at the top of the module.
    # get_video_processing_asset_files is defined above.
    # parse_srt_file, get_text_emotion from src.utils.

    srt_file_path = os.path.join(FULL_SENTENCE_SUBTITLE_FOLDER, f"{voiceover_basename_for_srt_match}.srt")

    if not os.path.exists(srt_file_path):
        print(f"SRT file {srt_file_path} not found for Greenscreen analysis. Skipping overlays.")
        return video_stream_input

    subtitles = parse_srt_file(srt_file_path)
    if not subtitles:
        print(f"No subtitles parsed from {srt_file_path}. Skipping greenscreen overlays.")
        return video_stream_input

    print(f"Analyzing {len(subtitles)} subtitle entries from {srt_file_path} for Greenscreen opportunities...")

    meme_data_to_overlay = []

    for sub_entry in subtitles:
        text = sub_entry['text']
        emotion, _ = get_text_emotion(text)

        if emotion != 'neutral': # Add more filters if needed
            meme_emotion_folder = os.path.join(GREENSCREEN_MEMES_FOLDER, emotion)
            if os.path.isdir(meme_emotion_folder):
                possible_memes = get_video_processing_asset_files(meme_emotion_folder, file_types=('*.mp4', '*.mov', '*.avi')) # Video files
                if possible_memes:
                    selected_meme_path = random.choice(possible_memes)
                    meme_data_to_overlay.append({
                        'path': selected_meme_path,
                        'start_time': sub_entry['start'],
                        'end_time': sub_entry['end'],
                        'emotion': emotion
                    })
                    print(f"  Found Greenscreen Meme for emotion '{emotion}': {os.path.basename(selected_meme_path)} for sub: '{text[:30]}...'")

    if not meme_data_to_overlay:
        print("No suitable greenscreen memes found or emotions detected for overlay.")
        return video_stream_input

    all_ffmpeg_inputs = [video_stream_input] # [0:v]
    for meme_info in meme_data_to_overlay:
        all_ffmpeg_inputs.append(ffmpeg.input(meme_info['path']))

    filter_chain_str = ""
    last_video_label = "[0:v]"

    for i, meme_info in enumerate(meme_data_to_overlay):
        meme_input_label = f"[{i+1}:v]"

        if GREENSCREEN_SIZE_METHOD == 'scale':
            meme_width_eval = GREENSCREEN_SIZE_WIDTH.replace('W', str(FINAL_RESOLUTION[0])).replace('iw', 'iw')
            meme_height_eval = "-1"
        else:
            print(f"Warning: Greenscreen size method '{GREENSCREEN_SIZE_METHOD}' not supported. Defaulting.")
            meme_width_eval = "iw*0.35"
            meme_height_eval = "-1"

        pos_template = DEFAULT_DATA['ANCHOR_POSITIONS'].get(GREENSCREEN_ANCHOR_POSITION)
        if not pos_template:
            print(f"Warning: Greenscreen anchor '{GREENSCREEN_ANCHOR_POSITION}' not found. Defaulting.")
            pos_template = DEFAULT_DATA['ANCHOR_POSITIONS']['top-right']

        x_pos_str = pos_template[0].replace("{mx}", GREENSCREEN_ANCHOR_MARGIN['x'])
        y_pos_str = pos_template[1].replace("{my}", GREENSCREEN_ANCHOR_MARGIN['y'])

        enable_str = f"between(t,{meme_info['start_time']},{meme_info['end_time']})"

        processed_meme_label = f"[chroma_meme_{i}]"
        scaled_meme_label = f"[scaled_meme_{i}]"
        current_overlay_label = f"[v_meme_out_{i}]"

        filter_chain_str += (
            f"{meme_input_label}"
            f"chromakey=color={GREENSCREEN_CHROMA_COLOR}:similarity={GREENSCREEN_CHROMA_SIMILARITY}:blend={GREENSCREEN_CHROMA_BLEND}"
            f"{processed_meme_label};"
        )
        filter_chain_str += (
            f"{processed_meme_label}scale=width={meme_width_eval}:height={meme_height_eval}"
            f"{scaled_meme_label};"
        )
        filter_chain_str += (
            f"{last_video_label}{scaled_meme_label}"
            f"overlay=x='{x_pos_str}':y='{y_pos_str}':shortest=0:enable='{enable_str}'"
            f"{current_overlay_label};"
        )

        last_video_label = current_overlay_label

    if not filter_chain_str:
        return video_stream_input

    final_filter_chain = filter_chain_str.rstrip(';')

    print(f"Applying {len(meme_data_to_overlay)} greenscreen memes using filter_complex.")
    try:
        processed_video_stream = ffmpeg.filter_complex(all_ffmpeg_inputs, final_filter_chain, **{'map': last_video_label})
        return processed_video_stream

    except ffmpeg.Error as e:
        print(f"Error applying Greenscreen Meme overlays with filter_complex: {e.stderr.decode('utf8', errors='ignore')}")
        return video_stream_input
    except Exception as e_gen:
        print(f"General error in add_greenscreen_memes_based_on_subtitles: {e_gen}")
        return video_stream_input

# Original if __name__ == '__main__' block
if __name__ == '__main__':
    print("--- Running video_processing_test ---")
    for folder in [VOICEOVER_FOLDER, MAIN_CLIPS_INTRO_FOLDER, MAIN_CLIPS_VIDEOS_FOLDERS[0], MAIN_CLIPS_IMAGES_FOLDER[0], OUTRO_FOLDER, OUTPUT_FOLDER]:
        os.makedirs(folder, exist_ok=True)
    print("Dummy assets folders checked/created. Ensure test files exist within them.")

    ENABLE_INTRO = True; ENABLE_OUTRO = True; UNIQUE_ASSETS = False

    selected_vo, vo_dur = select_voiceover(set())
    if not (selected_vo and vo_dur):
        print("Test FAILED: select_voiceover"); exit()
    print(f"VO: {selected_vo} ({vo_dur}s)")

    main_clips = get_main_clips_data(vo_dur)
    if not main_clips: print("Test FAILED: get_main_clips_data"); exit()
    print(f"Main clips: {len(main_clips)}")

    outro_data = add_outro_data()

    final_assembly = main_clips + ([outro_data] if outro_data else [])
    if not final_assembly: print("Test FAILED: final_assembly empty"); exit()
    print(f"Total clips: {len(final_assembly)}")

    output_fname = f"test_output_{random.randint(1000,9999)}.mp4"
    result_path = combine_video_elements(final_assembly, output_fname, selected_vo)

    if result_path and os.path.exists(result_path):
        print(f"SUCCESS: Video at {result_path}, Duration: {get_media_duration(result_path):.2f}s")
    else:
        print(f"FAILURE: Video not created.")
    print("--- video_processing_test finished ---")

[end of src/video_processing.py]
