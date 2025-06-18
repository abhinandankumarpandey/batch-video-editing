import json

DEFAULT_DATA = {
    "ANCHOR_POSITIONS": {
        "top-left": ["0+{mx}", "0+{my}"],
        "top-right": ["W-w-{mx}", "0+{my}"],
        "bottom-left": ["0+{mx}", "H-h-{my}"],
        "bottom-right": ["W-w-{mx}", "H-h-{my}"],
        "center": ["(W-w)/2", "(H-h)/2"]
    },
    "_size_presets": {
        "small_meme": {
            "method": "scale",
            "width": "min(iw\\, W*0.3)",
            "height": -1
        },
        "medium_meme": {
            "method": "scale",
            "width": "min(iw\\, W*0.4)",
            "height": -1
        },
        "large_meme": {
            "method": "scale",
            "width": "min(iw\\, W*0.5)",
            "height": -1
        }
    },
    "final": {
        "hwaccel": "cuda",
        "resolution": [1080, 1920],
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
        "acodec": "aac", "abr": "160k", "ar": 48000,
        "threads": 8, "buffer_size": "4000k",
        "_quality_presets": {
            "fast": {"crf": 23, "vquality": 26, "cq": 25},
            "balanced": {"crf": 21, "vquality": 24, "cq": 23},
            "high": {"crf": 18, "vquality": 22, "cq": 21}
        },
        "quality": "balanced"
    }
}

ENABLE_HOOK = False
ENABLE_INTRO = False
ENABLE_TRANSITION = True
ENABLE_SFX = False
ENABLE_ADDITONAL_SFX = False
ENABLE_LUTS = False
ENABLE_SUBTITLE = True
ENABLE_GREENSCREEN_OVERLAY = False
ENABLE_STICKERS = False
ENABLE_GIFS = False
ENABLE_WATERMARK = True
ENABLE_BGM = True
ENABLE_CINEMATIC_EFFECT = False
ENABLE_ASTHETIC_FRAME = False
ENABLE_OUTRO = True

OUTPUT_FOLDER = "./output"
VOICEOVER_FOLDER = "./assets/voiceovers"
MAIN_CLIPS_INTRO_FOLDER = "./assets/intros"
MAIN_CLIPS_VIDEOS_FOLDERS = ["./assets/videos", "./assets/more_randomvideos"]
MAIN_CLIPS_IMAGES_FOLDER = ["./assets/images", "./assets/darkimages"]
OUTRO_FOLDER = "./assets/outros"
ASTHETIC_FRAME_PATH = "./assets/frames/meme_border.png"
WATERMARK_PATH = "./assets/branding/logo.png"
BGM_PATH = "./assets/audio/trending_song.mp3"
CINEMATIC_EFFECT_PATH = "./assets/effects/rain_overlay.mov"
SUBTITLE_FOLDER = "./assets/one_to_four_word_subtitle"
FULL_SENTENCE_SUBTITLE_FOLDER = "./assets/full_sentence_subtitle"
LUT_FILE = "./assets/color/teal_and_orange.cube"
GIF_FOLDER = "./assets/gifs"
STICKER_FOLDER_PATH = "./assets/stickers"
GREENSCREEN_MEMES_FOLDER = "./assets/memes"
ADDITIONAL_SFX_FOLDER = "./assets/additional_sfx"
EMOTIONAL_SFX_FOLDER = "./assets/sfx_emotional" # Folder for emotion-tagged SFX

FINAL_FPS = 30
FINAL_RESOLUTION = [1080, 1920]
FINAL_CODEC = "qsv"

VOICEOVER_VOLUME = 1.1
VOICEOVER_START = 0

UNIQUE_ASSETS = True
IMAGE_PERCENTAGE = 40
VIDEO_MODE = "full_clip"
DEFAULT_TRANSITIONS = {"in": None, "out": "fade"}
OUTRO_TRIM = {"start": 0, "end": 10}
ASTHETIC_FRAME_POSITION = "center"
ASTHETIC_FRAME_MARGIN = {"x": 0, "y": 0}
ASTHETIC_FRAME_SIZE = {"method": "stretch", "width": "W", "height": "H"}
WATERMARK_POSITION = "top-left"
WATERMARK_MARGIN = {"x": "W*0.02", "y": "H*0.02"}
WATERMARK_SIZE_WIDTH = "W*0.08"
WATERMARK_WHEN = {"start": 0, "end": 99999}
BGM_LOOP = True
BGM_VOLUME = 0.25
BGM_START = 0
BGM_END = 99999
CINEMATIC_EFFECT_WHEN = {"start": 0, "end": 9999}
CINEMATIC_EFFECT_SIZE = {"method": "stretch", "width": "W", "height": "H"}
CINEMATIC_EFFECT_ANCHOR = {"position": "center", "margin": {"x":0, "y":0}}
CINEMATIC_EFFECT_OPACITY = 0.4
GIF_LOOP_MODE = "shortest"
GIF_LOOP_COUNT = 1
GIF_ANCHOR_POSITION = "bottom-left"
GIF_ANCHOR_MARGIN = {"x": "W*0.03", "y": "H*0.03"}
GIF_SIZE_PRESET = "_size_presets.small_meme"
STICKER_ANCHOR_POSITION = "top-left"
STICKER_ANCHOR_MARGIN = {"x": "W*0.04", "y": "H*0.04"}
STICKER_SIZE_PRESET = "_size_presets.small_meme"
GREENSCREEN_CHROMA_COLOR = "0x00ff00"
GREENSCREEN_CHROMA_SIMILARITY = 0.35
GREENSCREEN_CHROMA_BLEND = 0.15
GREENSCREEN_ANCHOR_POSITION = "top-right"
GREENSCREEN_ANCHOR_MARGIN = {"x": "W*0.04", "y": "H*0.04"}
GREENSCREEN_SIZE_METHOD = "scale"
GREENSCREEN_SIZE_WIDTH = "min(iw\\, W*0.35)"
GREENSCREEN_VOLUME = 0.4
ADDITIONAL_SFX_MAX_PER_MINUTE = 3
ADDITIONAL_SFX_VOLUME = 0.8

def load_config(config_file_path=None):
    config = {key: value for key, value in globals().items() if key.isupper()}
    if config_file_path:
        try:
            with open(config_file_path, 'r') as f:
                user_config = json.load(f)
            config.update(user_config)
        except FileNotFoundError:
            print(f"Warning: Config file {config_file_path} not found. Using defaults.")
        except json.JSONDecodeError:
            print(f"Warning: Error decoding {config_file_path}. Using defaults.")
    return config
