"""Fly Tying product boundaries."""

TERMINOLOGY = {
    "product": "Fly Tying",
    "pipeline": "shared_flytying_pipeline",
}

BOUNDARIES = {
    "philosophy": (
        "Fly Tying owns the tying workflow: pattern library, recipes, materials inventory, "
        "search, sessions, seasonal hatch guidance, Fly Tying RAG, videos, barcodes, and "
        "suggestions. Vision, Voice, Gallery, Planner, Calendar, Documents, Mission Control, "
        "and Models integrate with Fly Tying — they are not owned by it."
    ),
    "owns": [
        "pattern_library",
        "recipes",
        "materials_inventory",
        "pattern_search",
        "pattern_comparison",
        "pattern_queue",
        "tying_sessions",
        "seasonal_hatch_guidance",
        "flytying_rag",
        "videos",
        "barcode_management",
        "materials_suggestions",
        "flytying_profiles",
        "flytying_history",
    ],
    "does_not_own": [
        "vision",
        "voice",
        "gallery",
        "planner",
        "calendar",
        "documents",
        "mission_control",
        "models",
        "separate_flytying_llm",
        "always_on_bench_camera",
        "social_feed",
        "marketplace",
        "auto_purchasing",
        "gis_fishing_maps",
        "emotion_analysis",
        "silent_memory_ingestion",
    ],
}
