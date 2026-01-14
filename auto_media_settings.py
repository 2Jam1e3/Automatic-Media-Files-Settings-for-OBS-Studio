<<<<<<< HEAD
import obspython as obs

# ---------------- CONFIGURATION ----------------

GRAPHICS_SCENES = ["Graphics - 1", "Graphics - 2", "Graphics - 3"]
GRAPHICS_SCENES_NO_RESTART = ["Graphics - 3"]
MEDIA_SCENES = ["AC / VC / Clips with Audio"]
MEDIA_SOURCE_ID = "ffmpeg_source"
PARENT_SCENE = "Graphics - Out"

OBS_MONITORING_MONITOR_AND_OUTPUT = 2
OBS_SPEAKER_LAYOUT_MONO = 0

# ---------------- HELPER FUNCTIONS ----------------

def apply_fit_to_screen(scene_item):
    """Safely sets Bounding Box to Fit to Screen"""
    ovi = obs.obs_video_info()
    obs.obs_get_video_info(ovi)

    size = obs.vec2()
    size.x = float(ovi.base_width)
    size.y = float(ovi.base_height)

    obs.obs_sceneitem_set_bounds_type(scene_item, 2)
    obs.obs_sceneitem_set_bounds(scene_item, size)
    obs.obs_sceneitem_set_bounds_alignment(scene_item, 0)

    pos = obs.vec2()
    pos.x = 0.0
    pos.y = 0.0
    obs.obs_sceneitem_set_pos(scene_item, pos)


def process_source_safely(source_name):
    """Apply media settings based on scene usage"""
    source = obs.obs_get_source_by_name(source_name)
    if not source:
        return

    if obs.obs_source_get_id(source) != MEDIA_SOURCE_ID:
        obs.obs_source_release(source)
        return

    applied_graphics_settings = False
    applied_media_settings = False

    # ---------------- GRAPHICS SCENES ----------------
    for scene_name in GRAPHICS_SCENES:
        scene_source = obs.obs_get_source_by_name(scene_name)
        if scene_source:
            scene = obs.obs_scene_from_source(scene_source)
            if scene:
                scene_item = obs.obs_scene_find_source(scene, source_name)
                if scene_item:
                    if not applied_graphics_settings:
                        settings = obs.obs_source_get_settings(source)

                        obs.obs_data_set_bool(settings, "looping", True)
                        obs.obs_data_set_bool(settings, "hw_decode", True)
                        obs.obs_data_set_bool(settings, "close_when_inactive", True)

                        obs.obs_source_update(source, settings)
                        obs.obs_data_release(settings)

                        obs.obs_source_set_muted(source, True)
                        applied_graphics_settings = True

                    apply_fit_to_screen(scene_item)

            obs.obs_source_release(scene_source)

    # ---------------- AC / VC / CLIPS WITH AUDIO ----------------
    for scene_name in MEDIA_SCENES:
        scene_source = obs.obs_get_source_by_name(scene_name)
        if scene_source:
            scene = obs.obs_scene_from_source(scene_source)
            if scene:
                scene_item = obs.obs_scene_find_source(scene, source_name)
                if scene_item:
                    if not applied_media_settings:
                        settings = obs.obs_source_get_settings(source)

                        obs.obs_data_set_bool(settings, "looping", False)
                        obs.obs_data_set_bool(settings, "hw_decode", True)
                        obs.obs_data_set_bool(settings, "close_when_inactive", True)

                        obs.obs_source_update(source, settings)
                        obs.obs_data_release(settings)

                        obs.obs_source_set_monitoring_type(
                            source,
                            OBS_MONITORING_MONITOR_AND_OUTPUT
                        )
                        
                        obs.obs_source_set_flags(
                            source,
                            obs.obs_source_get_flags(source) | obs.OBS_SOURCE_FLAG_FORCE_MONO
                        )
                        
                        obs.obs_source_set_volume(source, 0.31622776601683794)
                        applied_media_settings = True

                    apply_fit_to_screen(scene_item)

            obs.obs_source_release(scene_source)

    obs.obs_source_release(source)


def is_source_in_no_restart_scene(source_name):
    """Check if the source exists in any scene that should disable restart_on_activate"""
    for scene_name in GRAPHICS_SCENES_NO_RESTART:
        scene_source = obs.obs_get_source_by_name(scene_name)
        if scene_source:
            scene = obs.obs_scene_from_source(scene_source)
            if scene:
                scene_item = obs.obs_scene_find_source(scene, source_name)
                if scene_item:
                    obs.obs_source_release(scene_source)
                    return True
            obs.obs_source_release(scene_source)
    return False


def is_nested_scene_active_in_parent():
    """Check if Graphics - 3 is currently visible through Graphics - Out in Program"""
    program_scene_source = obs.obs_frontend_get_current_scene()
    if not program_scene_source:
        return False
    
    program_scene_name = obs.obs_source_get_name(program_scene_source)
    
    # Only proceed if Graphics - Out is in Program
    if program_scene_name != PARENT_SCENE:
        obs.obs_source_release(program_scene_source)
        return False
    
    # Now check if Graphics - 3 is visible in Graphics - Out
    scene = obs.obs_scene_from_source(program_scene_source)
    obs.obs_source_release(program_scene_source)
    
    if not scene:
        return False
    
    # Look for Graphics - 3 as a nested scene source
    for nested_scene_name in GRAPHICS_SCENES_NO_RESTART:
        nested_source = obs.obs_get_source_by_name(nested_scene_name)
        if nested_source:
            scene_item = obs.obs_scene_find_source(scene, nested_scene_name)
            if scene_item and obs.obs_sceneitem_visible(scene_item):
                obs.obs_source_release(nested_source)
                return True
            obs.obs_source_release(nested_source)
    
    return False


def get_parent_scene_of_source(source_name):
    """Returns the direct parent scene name containing this source, or None"""
    for scene_name in GRAPHICS_SCENES_NO_RESTART:
        scene_source = obs.obs_get_source_by_name(scene_name)
        if scene_source:
            scene = obs.obs_scene_from_source(scene_source)
            if scene:
                scene_item = obs.obs_scene_find_source(scene, source_name)
                if scene_item:
                    obs.obs_source_release(scene_source)
                    return scene_name
            obs.obs_source_release(scene_source)
    return None


# ---------------- OBS SIGNAL CALLBACKS ----------------

def on_source_create(calldata):
    source = obs.calldata_source(calldata, "source")
    if source:
        source_name = obs.obs_source_get_name(source)

        def delayed():
            process_source_safely(source_name)
            obs.remove_current_callback()

        obs.timer_add(delayed, 500)


def on_source_activate(calldata):
    """Called when a source becomes active in the Program output"""
    source = obs.calldata_source(calldata, "source")
    if not source:
        return
    
    if obs.obs_source_get_id(source) != MEDIA_SOURCE_ID:
        return
    
    source_name = obs.obs_source_get_name(source)
    parent_scene = get_parent_scene_of_source(source_name)
    
    # Only process if this source is in a no-restart scene (Graphics - 3)
    if not parent_scene or parent_scene not in GRAPHICS_SCENES_NO_RESTART:
        return
    
    # Check if the activation is happening because Graphics - Out is in Program
    # AND Graphics - 3 is visible within it
    if is_nested_scene_active_in_parent():
        settings = obs.obs_source_get_settings(source)
        obs.obs_data_set_bool(settings, "restart_on_activate", False)
        obs.obs_source_update(source, settings)
        obs.obs_data_release(settings)


def on_frontend_event(event):
    """Track scene changes to re-enable restart_on_activate when leaving Graphics - Out"""
    if event == obs.OBS_FRONTEND_EVENT_SCENE_CHANGED:
        program_scene_source = obs.obs_frontend_get_current_scene()
        if not program_scene_source:
            return
        
        program_scene_name = obs.obs_source_get_name(program_scene_source)
        obs.obs_source_release(program_scene_source)
        
        # If we've switched away from Graphics - Out, re-enable restart_on_activate
        # for all sources in Graphics - 3
        if program_scene_name != PARENT_SCENE:
            for scene_name in GRAPHICS_SCENES_NO_RESTART:
                scene_source = obs.obs_get_source_by_name(scene_name)
                if scene_source:
                    scene = obs.obs_scene_from_source(scene_source)
                    if scene:
                        # Iterate all items in Graphics - 3
                        def reset_restart(scene, scene_item, param):
                            source = obs.obs_sceneitem_get_source(scene_item)
                            if source and obs.obs_source_get_id(source) == MEDIA_SOURCE_ID:
                                settings = obs.obs_source_get_settings(source)
                                # Re-enable restart_on_activate (set to default/true)
                                obs.obs_data_set_bool(settings, "restart_on_activate", True)
                                obs.obs_source_update(source, settings)
                                obs.obs_data_release(settings)
                            return True
                        
                        obs.obs_scene_enum_items(scene, reset_restart, None)
                    obs.obs_source_release(scene_source)


# ---------------- SCRIPT EXPORTS ----------------

def script_description():
    return (
        "Media Source Manager (FIXED)\n\n"
        "Graphics Scenes (Graphics - 1, Graphics - 2):\n"
        "- Loop enabled\n"
        "- Muted\n"
        "- Restart on Activate: DEFAULT\n"
        "- Fit to screen\n"
        "- HW decode enabled\n"
        "- Close when inactive\n\n"
        "Graphics Scene (Graphics - 3):\n"
        "- Loop enabled\n"
        "- Muted\n"
        "- Restart on Activate: DISABLED only when:\n"
        "  1. Graphics - Out is in Program\n"
        "  2. Graphics - 3 is visible in Graphics - Out\n"
        "  3. The media source activates\n"
        "- Re-enabled when switching away from Graphics - Out\n"
        "- Fit to screen\n"
        "- HW decode enabled\n"
        "- Close when inactive\n\n"
        "AC / VC / Clips with Audio:\n"
        "- Audio Monitoring: Monitor & Output\n"
        "- Audio Output: MONO\n"
        "- Volume: -10.0 dB\n"
        "- Normal playback\n"
        "- Fit to screen\n"
        "- HW decode enabled\n"
        "- Close when inactive"
    )


def script_load(settings):
    sh = obs.obs_get_signal_handler()
    obs.signal_handler_connect(sh, "source_create", on_source_create)
    obs.signal_handler_connect(sh, "source_activate", on_source_activate)
    obs.obs_frontend_add_event_callback(on_frontend_event)


def script_unload():
    sh = obs.obs_get_signal_handler()
    obs.signal_handler_disconnect(sh, "source_create", on_source_create)
    obs.signal_handler_disconnect(sh, "source_activate", on_source_activate)
    obs.obs_frontend_remove_event_callback(on_frontend_event)
=======
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
>>>>>>> ce6aeaaac108931b34532f4677be5159b8cb1de8
