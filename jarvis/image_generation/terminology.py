"""Image Generation product boundaries."""

TERMINOLOGY = {
    "product": "Image Generation",
    "engine": "Image Engine",
    "pipeline": "shared_comfyui_pipeline",
}

BOUNDARIES = {
    "philosophy": (
        "Image Generation creates stills via one shared ComfyUI pipeline. "
        "Gallery browses and organizes; Chat converses; Mission Control monitors health."
    ),
    "owns": [
        "prompt_to_image",
        "comfyui_execution",
        "prompt_enhancement",
        "diffusion_workflows",
        "generation_presets",
        "gpu_cpu_execution",
        "generation_parameters",
        "shared_generation_pipeline",
    ],
    "does_not_own": [
        "gallery_library",
        "chat_conversation",
        "video_studio",
        "meme_studio",
        "documents",
        "memory",
        "mission_control",
        "second_diffusion_backend",
        "cloud_generation",
        "silent_prompt_rewrite",
    ],
}
