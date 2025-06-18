import PySimpleGUI as sg
import os
from src import config # To load default values and potentially update them

# --- Helper function to get folder via browser ---
def browse_folder(default_path=""):
    # In a real scenario, sg.popup_get_folder might be too simple if we need to validate
    # or if the window doesn't stay on top. But it's good for a start.
    folder = sg.popup_get_folder('Select Folder', initial_folder=default_path or os.getcwd(), no_window=True)
    return folder if folder else default_path # Return original if no folder selected

# --- Main GUI Function ---
def run_gui():
    sg.theme('SystemDefaultForReal') # A generally compatible theme

    # --- Column 1: Folder Paths ---
    col1_paths = [
        [sg.Text("Voiceover Folder:", size=(20,1)), sg.InputText(default_text=config.VOICEOVER_FOLDER, key="-VOICEOVER_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_VO_FOLDER-")],
        [sg.Text("Main Videos Folder:", size=(20,1)), sg.InputText(default_text=config.MAIN_CLIPS_VIDEOS_FOLDERS[0] if config.MAIN_CLIPS_VIDEOS_FOLDERS else "", key="-VIDEOS_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_VID_FOLDER-")],
        [sg.Text("Main Images Folder:", size=(20,1)), sg.InputText(default_text=config.MAIN_CLIPS_IMAGES_FOLDER[0] if config.MAIN_CLIPS_IMAGES_FOLDER else "", key="-IMAGES_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_IMG_FOLDER-")],
        [sg.Text("Intro Folder:", size=(20,1)), sg.InputText(default_text=config.MAIN_CLIPS_INTRO_FOLDER, key="-INTRO_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_INTRO_FOLDER-")],
        [sg.Text("Outro Folder:", size=(20,1)), sg.InputText(default_text=config.OUTRO_FOLDER, key="-OUTRO_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_OUTRO_FOLDER-")],
        [sg.Text("Output Folder:", size=(20,1)), sg.InputText(default_text=config.OUTPUT_FOLDER, key="-OUTPUT_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_OUT_FOLDER-")],
        [sg.Text("Subtitle (for emotion):",tooltip="Folder with full sentence SRTs (same name as voiceover)", size=(20,1)), sg.InputText(default_text=config.FULL_SENTENCE_SUBTITLE_FOLDER, key="-FULL_SUB_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_FSUB_FOLDER-")],
        [sg.Text("Subtitle (for display):", tooltip="Folder with 1-4 word SRTs (same name as voiceover)", size=(20,1)), sg.InputText(default_text=config.SUBTITLE_FOLDER, key="-DISP_SUB_FOLDER-", size=(40,1)), sg.Button("Browse", key="-B_DSUB_FOLDER-")],
    ]

    # --- Column 2: Settings & Features ---
    # Feature Toggles
    feature_toggles = [
        [sg.Checkbox("Intro", default=config.ENABLE_INTRO, key="-ENABLE_INTRO-"), sg.Checkbox("Outro", default=config.ENABLE_OUTRO, key="-ENABLE_OUTRO-")],
        [sg.Checkbox("Watermark", default=config.ENABLE_WATERMARK, key="-ENABLE_WATERMARK-"), sg.Checkbox("BGM", default=config.ENABLE_BGM, key="-ENABLE_BGM-")],
        [sg.Checkbox("Subtitles (Display)", default=config.ENABLE_SUBTITLE, key="-ENABLE_SUBTITLE-"), sg.Checkbox("LUT Color Grade", default=config.ENABLE_LUTS, key="-ENABLE_LUTS-")],
        [sg.Checkbox("Aesthetic Frame", default=config.ENABLE_ASTHETIC_FRAME, key="-ENABLE_ASTHETIC_FRAME-"), sg.Checkbox("Cinematic Effect", default=config.ENABLE_CINEMATIC_EFFECT, key="-ENABLE_CINEMATIC_EFFECT-")],
        [sg.Text("Emotion-based Content:")],
        [sg.Checkbox("GIFs", default=config.ENABLE_GIFS, key="-ENABLE_GIFS-"), sg.Checkbox("Stickers", default=config.ENABLE_STICKERS, key="-ENABLE_STICKERS-")],
        [sg.Checkbox("Greenscreen Memes", default=config.ENABLE_GREENSCREEN_OVERLAY, key="-ENABLE_GREENSCREEN_OVERLAY-")],
        [sg.Checkbox("Emotional SFX", default=config.ENABLE_SFX, key="-ENABLE_SFX-"), sg.Checkbox("Additional SFX", default=config.ENABLE_ADDITONAL_SFX, key="-ENABLE_ADDITONAL_SFX-")],
    ]

    # Video Settings
    video_settings = [
        [sg.Text("Resolution:", size=(15,1)), sg.InputText(f"{config.FINAL_RESOLUTION[0]}x{config.FINAL_RESOLUTION[1]}", key="-RESOLUTION-", size=(10,1), tooltip="WidthxHeight, e.g., 1080x1920")],
        [sg.Text("FPS:", size=(15,1)), sg.InputText(str(config.FINAL_FPS), key="-FPS-", size=(5,1))],
        [sg.Text("Codec:", size=(15,1)), sg.Combo(['none', 'qsv', 'cuda'], default_value=config.FINAL_CODEC, key="-CODEC-", size=(10,1))],
        [sg.Text("Quality:", size=(15,1)), sg.Combo(['fast', 'balanced', 'high'], default_value=config.DEFAULT_DATA['final']['quality'], key="-QUALITY-", size=(10,1))],
    ]

    col2_settings = [
        [sg.Frame("Feature Toggles", feature_toggles)],
        [sg.Frame("Video Settings", video_settings)]
    ]

    # --- Layout ---
    layout = [
        [sg.Text("Automatic Batch Video Maker Config", font=("Helvetica", 16))],
        [sg.Column(col1_paths), sg.VSeperator(), sg.Column(col2_settings)],
        [sg.Button("Start Batch Process", key="-START_BATCH-", size=(20,2), button_color=('white', 'green')), sg.Button("Exit", size=(10,2))]
    ]

    window = sg.Window("Video Maker Control Panel", layout, resizable=True)

    # --- Event Loop ---
    while True:
        event, values = window.read()

        if event == sg.WIN_CLOSED or event == "Exit":
            break

        # Folder browsing events
        if event == "-B_VO_FOLDER-": window["-VOICEOVER_FOLDER-"].update(browse_folder(values["-VOICEOVER_FOLDER-"]))
        if event == "-B_VID_FOLDER-": window["-VIDEOS_FOLDER-"].update(browse_folder(values["-VIDEOS_FOLDER-"]))
        if event == "-B_IMG_FOLDER-": window["-IMAGES_FOLDER-"].update(browse_folder(values["-IMAGES_FOLDER-"]))
        if event == "-B_INTRO_FOLDER-": window["-INTRO_FOLDER-"].update(browse_folder(values["-INTRO_FOLDER-"]))
        if event == "-B_OUTRO_FOLDER-": window["-OUTRO_FOLDER-"].update(browse_folder(values["-OUTRO_FOLDER-"]))
        if event == "-B_OUT_FOLDER-": window["-OUTPUT_FOLDER-"].update(browse_folder(values["-OUTPUT_FOLDER-"]))
        if event == "-B_FSUB_FOLDER-": window["-FULL_SUB_FOLDER-"].update(browse_folder(values["-FULL_SUB_FOLDER-"]))
        if event == "-B_DSUB_FOLDER-": window["-DISP_SUB_FOLDER-"].update(browse_folder(values["-DISP_SUB_FOLDER-"]))


        if event == "-START_BATCH-":
            print("--- GUI: Start Batch Process Clicked ---")
            # 1. Collect all values from the GUI
            gui_config_values = values.copy() # Make a copy to work with
            print("Current GUI Values:")
            for key, val in gui_config_values.items():
                print(f"  {key}: {val}")

            # 2. TODO: Update src.config.py or pass these values to the batch processing function.
            #    For a simple approach, one might try to update config module variables directly,
            #    but this has limitations if other modules have already imported specific values from it.
            #    A better way is to collect these into a dictionary and pass it to the core processing logic.

            # Example: Parse resolution string "1080x1920" into [1080, 1920]
            try:
                w_str, h_str = gui_config_values.get("-RESOLUTION-", "1080x1920").split('x')
                resolution = [int(w_str), int(h_str)]
                gui_config_values["_parsed_resolution"] = resolution
            except ValueError:
                sg.popup_error("Invalid resolution format. Use WidthxHeight (e.g., 1080x1920).")
                continue # Don't proceed if validation fails

            try:
                fps = int(gui_config_values.get("-FPS-", "30"))
                gui_config_values["_parsed_fps"] = fps
            except ValueError:
                sg.popup_error("Invalid FPS. Must be an integer.")
                continue

            # 3. TODO: Call the main batch processing function from main.py or video_processing.py
            #    This function would need to be adapted to accept a configuration dictionary.
            #    e.g., from main import process_batch_with_options
            #    process_batch_with_options(gui_config_values)

            sg.popup_auto_close("Batch Processing Started (Placeholder)",
                                "Check console for current GUI values.",
                                auto_close_duration=3, no_titlebar=True)
            print("Placeholder: Actual batch processing would be invoked here with the collected settings.")
            # For now, just print the collected values.
            # In a real app, this might trigger a function in a separate thread to keep GUI responsive.

    window.close()

if __name__ == '__main__':
    print("Starting GUI...")
    # This will try to load the sentiment model if utils.py is imported by config.py or other modules
    # that video_processing (and thus main processing logic) would use.
    # Ensure this is handled gracefully if GUI is meant to be very lightweight on startup.
    run_gui()
    print("GUI Closed.")
