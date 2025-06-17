import os
import random
import glob
import json # For the main block test config
from video_engine import get_video_info

# Supported media file extensions
VIDEO_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp']
AUDIO_EXTENSIONS = ['.mp3', '.wav', '.aac', '.m4a']

def _scan_folder_for_files(folder_path, extensions):
    """Scans a folder for files with given extensions."""
    found_files = []
    if not os.path.isdir(folder_path):
        # print(f"Warning: Folder not found or not a directory: {folder_path}") # Less verbose
        return found_files
    for ext in extensions:
        found_files.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
    return found_files

def _get_file_basename(file_path):
    """Returns the basename of a file without its extension."""
    return os.path.splitext(os.path.basename(file_path))[0]

def select_voiceover(config):
    """
    Selects a random voiceover from the configured folder.
    Skips voiceovers if a video with the same name already exists in the output folder.
    Returns the path to the selected voiceover file, or None if none can be selected.
    """
    voiceover_folder = config.get("voiceover_folder")
    output_folder = config.get("output_folder")

    if not voiceover_folder or not os.path.isdir(voiceover_folder):
        # print(f"Error: Voiceover folder not found or not specified: {voiceover_folder}")
        return None

    available_voiceovers = _scan_folder_for_files(voiceover_folder, AUDIO_EXTENSIONS)
    if not available_voiceovers:
        # print(f"No voiceovers found in {voiceover_folder}")
        return None

    random.shuffle(available_voiceovers)

    for vo_path in available_voiceovers:
        vo_basename = _get_file_basename(vo_path)
        potential_output_video = os.path.join(output_folder, f"{vo_basename}.mp4")
        # Added configurable skip for existing output
        if os.path.exists(potential_output_video) and config.get("skip_existing_output", True):
            # print(f"Skipping voiceover {vo_path}, output video {potential_output_video} already exists.")
            continue

        # print(f"Selected voiceover: {vo_path}")
        return vo_path

    # print("No suitable voiceover found (all might be processed or folder empty).")
    return None

def get_media_duration_seconds(file_path):
    """
    Gets the duration of a media file in seconds.
    Returns 0.0 for images or if duration can't be determined.
    """
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext in IMAGE_EXTENSIONS:
        return 0.0

    try:
        info = get_video_info(file_path)
        if info and 'format' in info and 'duration' in info['format']:
            return float(info['format']['duration'])
    except Exception as e:
        # print(f"Could not get duration for {file_path}: {e}")
        pass # Keep it less verbose
    return 0.0


def get_main_clips_data(config, target_duration_seconds=None):
    """
    Selects main video and image clips based on the configuration.
    """
    video_folders = config.get("main_clips_videos_folders", [])
    image_folders = config.get("main_clips_images_folder", [])
    image_percentage_target = config.get("image_percentage", 0) / 100.0
    unique_assets = config.get("unique_assets", True)
    default_image_display_duration = config.get("default_image_display_duration", 3.0)

    all_video_files = []
    for folder in video_folders:
        if os.path.isdir(folder): # Check if folder exists before scanning
            all_video_files.extend(_scan_folder_for_files(folder, VIDEO_EXTENSIONS))
        # else: print(f"Warning: Video folder not found: {folder}") # Already handled by _scan_folder

    all_image_files = []
    for folder in image_folders:
        if os.path.isdir(folder): # Check if folder exists
            all_image_files.extend(_scan_folder_for_files(folder, IMAGE_EXTENSIONS))
        # else: print(f"Warning: Image folder not found: {folder}")

    if not all_video_files and not all_image_files:
        # print("Warning: No video or image files found in specified main_clips folders.")
        return []

    random.shuffle(all_video_files)
    random.shuffle(all_image_files)

    selected_clips = []
    used_assets = set()
    num_clips_target = config.get("num_main_clips_target", 15)

    num_images_to_select = int(num_clips_target * image_percentage_target)
    # num_videos_to_select = num_clips_target - num_images_to_select # This is dynamic

    # Select images
    for img_path in all_image_files:
        if sum(1 for c in selected_clips if c['type'] == 'image') >= num_images_to_select:
            break
        if unique_assets and img_path in used_assets:
            continue
        selected_clips.append({'path': img_path, 'type': 'image', 'duration': default_image_display_duration})
        if unique_assets:
            used_assets.add(img_path)

    # Select videos (fill up to num_clips_target)
    num_videos_to_select = num_clips_target - len(selected_clips)
    for vid_path in all_video_files:
        if sum(1 for c in selected_clips if c['type'] == 'video') >= num_videos_to_select:
             break # Met video quota
        if len(selected_clips) >= num_clips_target: # Also check overall target
            break
        if unique_assets and vid_path in used_assets:
            continue

        duration = get_media_duration_seconds(vid_path)
        if duration > 0:
            selected_clips.append({'path': vid_path, 'type': 'video', 'duration': duration})
            if unique_assets:
                used_assets.add(vid_path)

    # If still under target, try to add more of whatever is available (first videos, then images)
    if len(selected_clips) < num_clips_target:
        for vid_path in all_video_files:
            if len(selected_clips) >= num_clips_target: break
            if unique_assets and vid_path in used_assets: continue
            duration = get_media_duration_seconds(vid_path)
            if duration > 0:
                selected_clips.append({'path': vid_path, 'type': 'video', 'duration': duration})
                if unique_assets: used_assets.add(vid_path)

        for img_path in all_image_files:
            if len(selected_clips) >= num_clips_target: break
            if unique_assets and img_path in used_assets: continue
            selected_clips.append({'path': img_path, 'type': 'image', 'duration': default_image_display_duration})
            if unique_assets: used_assets.add(img_path)

    random.shuffle(selected_clips)
    # print(f"Selected {len(selected_clips)} main clips ({sum(1 for c in selected_clips if c['type'] == 'image')} images, {sum(1 for c in selected_clips if c['type'] == 'video')} videos).")
    return selected_clips

def select_bgm(config):
    """Selects a random BGM from the configured folder."""
    bgm_folder = config.get("bgm_folder")
    if not bgm_folder or not os.path.isdir(bgm_folder):
        # print(f"Warning: BGM folder not found or not specified: {bgm_folder}")
        return None

    available_bgm = _scan_folder_for_files(bgm_folder, AUDIO_EXTENSIONS)
    if not available_bgm:
        # print(f"No BGM files found in {bgm_folder}")
        return None

    selected_bgm_path = random.choice(available_bgm)
    # print(f"Selected BGM: {selected_bgm_path}")
    return selected_bgm_path

if __name__ == '__main__':
    # print("asset_manager.py loaded.") # Keep __main__ minimal for imports by other modules
    pass # Main functionality tested via batch_processor or dedicated test scripts.
    # The original more extensive __main__ for asset_manager.py:
    # if not os.path.exists("configs"): os.makedirs("configs", exist_ok=True)
    # if not os.path.exists("assets/voiceovers"): os.makedirs("assets/voiceovers", exist_ok=True)
    # if not os.path.exists("assets/videos"): os.makedirs("assets/videos", exist_ok=True)
    # if not os.path.exists("assets/images"): os.makedirs("assets/images", exist_ok=True)
    # if not os.path.exists("assets/audio"): os.makedirs("assets/audio", exist_ok=True)
    # if not os.path.exists("output"): os.makedirs("output", exist_ok=True)

    # dummy_vo_files = ["assets/voiceovers/vo1.mp3", "assets/voiceovers/vo2.wav"]
    # dummy_vid_files = ["assets/videos/vid1.mp4", "assets/videos/vid2.mov"]
    # dummy_img_files = ["assets/images/img1.jpg", "assets/images/img2.png"]
    # dummy_bgm_files = ["assets/audio/bgm1.mp3", "assets/audio/bgm2.wav"]
    # for f_path in dummy_vo_files + dummy_vid_files + dummy_img_files + dummy_bgm_files:
    #     if not os.path.exists(f_path): open(f_path, 'a').close()
    # if not os.path.exists("output/vo1.mp4"): open("output/vo1.mp4", 'a').close()

    # dummy_project_config_path = "configs/asset_manager_test_project.json"
    # test_config_data = {
    #     "project_name": "Asset Manager Test",
    #     "voiceover_folder": "assets/voiceovers", "output_folder": "output",
    #     "main_clips_videos_folders": ["assets/videos"],
    #     "main_clips_images_folder": ["assets/images"],
    #     "image_percentage": 30, "unique_assets": True,
    #     "num_main_clips_target": 5, "default_image_display_duration": 2.5,
    #     "bgm_folder": "assets/audio",
    #     "final": {"resolution": [100,100], "fps":10}
    # }
    # with open(dummy_project_config_path, 'w') as f:
    #     json.dump(test_config_data, f, indent=2)

    # original_get_video_info_func = get_video_info
    # def mock_get_video_info_for_asset_test(file_path_arg):
    #     if file_path_arg.endswith(tuple(VIDEO_EXTENSIONS + AUDIO_EXTENSIONS)):
    #         return {'format': {'duration': str(random.uniform(5.0, 15.0))}}
    #     return None
    # get_video_info = mock_get_video_info_for_asset_test

    # print("\n--- Testing select_voiceover ---")
    # selected_vo = select_voiceover(test_config_data)
    # print(f"Test selected_voiceover: {selected_vo if selected_vo else 'None'}")

    # print("\n--- Testing get_main_clips_data ---")
    # main_clips = get_main_clips_data(test_config_data)
    # print(f"Test get_main_clips_data selected {len(main_clips)} clips.")

    # print("\n--- Testing select_bgm ---")
    # selected_music = select_bgm(test_config_data)
    # print(f"Test selected_bgm: {selected_music if selected_music else 'None'}")

    # get_video_info = original_get_video_info_func
    # print("\nAsset manager module test run complete.")
