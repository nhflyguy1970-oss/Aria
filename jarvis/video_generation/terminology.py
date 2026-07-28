"""Video Generation product boundaries."""

TERMINOLOGY = {
    "product": "Video Generation",
    "studio": "Video Studio",
    "pipeline": "shared_motion_pipeline",
}

BOUNDARIES = {
    "philosophy": (
        "Video Generation creates motion via one shared AnimateDiff / Ken Burns pipeline. "
        "Video Studio is the primary create surface; Gallery owns stills; Mission Control owns health."
    ),
    "owns": [
        "text_to_video",
        "image_to_motion",
        "animatediff",
        "ken_burns",
        "video_presets",
        "motion_planning",
        "prompt_enhancement",
        "shared_video_pipeline",
        "storyboard_creation",
    ],
    "does_not_own": [
        "gallery_stills",
        "image_generation_engine",
        "chat_conversation",
        "mission_control",
        "documents",
        "memory",
        "timeline_editor",
        "cloud_video_backend",
        "silent_prompt_rewrite",
        "second_generation_stack",
    ],
}
