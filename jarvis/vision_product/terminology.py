"""Vision product boundaries."""

TERMINOLOGY = {
    "product": "Vision",
    "pipeline": "shared_vision_pipeline",
}

BOUNDARIES = {
    "philosophy": (
        "Vision owns understanding of visual inputs: OCR, describe, compare, region, "
        "PDF/video frames, webcam analysis, imports. Image Generation creates pixels; "
        "Gallery stores them; Presence handles presence/gestures; Coding applies code."
    ),
    "owns": [
        "image_understanding",
        "ocr",
        "structured_ocr",
        "image_comparison",
        "region_analysis",
        "pdf_page_analysis",
        "video_frame_analysis",
        "webcam_capture_for_analysis",
        "visual_reasoning",
        "vision_profiles",
        "vision_history",
        "vision_import_pipeline",
        "vision_routing",
    ],
    "does_not_own": [
        "image_generation",
        "gallery_library",
        "presence_gestures",
        "browser_navigation",
        "coding_apply",
        "audio_studio",
        "documents_store",
        "memory_store",
        "mission_control",
        "always_on_ambient_camera",
        "emotion_detection",
        "auto_apply_coding",
        "silent_memory_ingest",
    ],
}
