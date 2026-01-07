import obspython as obs

# --- Configuration ---
SCENE_NAMES = ["Graphics - 1", "Graphics - 2", "Graphics - 3"]
MEDIA_SOURCE_ID = "ffmpeg_source"

def apply_fit_to_screen(scene_item):
    """Safely sets Bounding Box to Fit to Screen"""
    ovi = obs.obs_video_info()
    obs.obs_get_video_info(ovi)
    
    size = obs.vec2()
    size.x = float(ovi.base_width)
    size.y = float(ovi.base_height)
    
    # OBS_BOUNDS_SCALE_INNER (2) fits while keeping aspect ratio
    obs.obs_sceneitem_set_bounds_type(scene_item, 2) 
    obs.obs_sceneitem_set_bounds(scene_item, size)
    obs.obs_sceneitem_set_bounds_alignment(scene_item, 0) # Center
    
    pos = obs.vec2()
    pos.x = 0.0
    pos.y = 0.0
    obs.obs_sceneitem_set_pos(scene_item, pos)

def process_source_safely(source_name):
    """Finds the source and fits it ONLY if it still exists in the scene"""
    source = obs.obs_get_source_by_name(source_name)
    if not source:
        return

    # Check ID to ensure it's a media source
    if obs.obs_source_get_id(source) != MEDIA_SOURCE_ID:
        obs.obs_source_release(source)
        return

    # Apply Settings (Loop, HW Decode, etc.)
    settings = obs.obs_source_get_settings(source)
    obs.obs_data_set_bool(settings, "looping", True)
    obs.obs_data_set_bool(settings, "hw_decode", True)
    obs.obs_data_set_bool(settings, "close_when_inactive", True)
    obs.obs_source_update(source, settings)
    obs.obs_source_set_muted(source, True)
    obs.obs_data_release(settings)

    # Locate the item in scenes and fit it
    for scene_name in SCENE_NAMES:
        scene_source = obs.obs_get_source_by_name(scene_name)
        if scene_source:
            scene = obs.obs_scene_from_source(scene_source)
            # This is the line that crashed; we check scene validity now
            if scene:
                scene_item = obs.obs_scene_find_source(scene, source_name)
                if scene_item:
                    apply_fit_to_screen(scene_item)
            obs.obs_source_release(scene_source)
    
    obs.obs_source_release(source)

# --- Signal Callbacks ---

def on_source_create(calldata):
    source = obs.calldata_source(calldata, "source")
    if source:
        source_name = obs.obs_source_get_name(source)
        # Use a single-shot timer to let OBS finish internal scene-tree setup
        # We pass the NAME, not the object pointer, to stay thread-safe
        obs.timer_add(lambda: (process_source_safely(source_name), obs.remove_current_callback()), 500)

# --- OBS Script Exports ---

def script_description():
    return "FINAL FIX: Uses Name-lookup to avoid pointer crashes in Graphics scenes."

def script_load(settings):
    sh = obs.obs_get_signal_handler()
    obs.signal_handler_connect(sh, "source_create", on_source_create)

def script_unload():
    sh = obs.obs_get_signal_handler()
    obs.signal_handler_disconnect(sh, "source_create", on_source_create)