"""Search product boundaries — one engine; products own corpora."""

TERMINOLOGY = {
    "product": "Search",
    "architecture_term": "Federated Retrieval",
    "pipeline": "shared_search_pipeline",
    "engine": "Search Engine",
    "home": "Search Home",
}

BOUNDARIES = {
    "philosophy": (
        "Search is Aria's unified find surface: one pipeline for intent, corpus selection, "
        "parallel retrieval, ranking, result contract, presentation, history, and diagnostics. "
        "Products own their data and indexes. Search retrieves and presents — never duplicates ownership. "
        "Sidebar filters navigation; Ctrl+K is commands + quick search; Search Home browses everything; "
        "Chat answers and synthesizes; Voice speaks search; product views stay scoped."
    ),
    "owns": [
        "search_home",
        "federated_search",
        "search_sessions",
        "ranking",
        "result_presentation",
        "search_history",
        "saved_searches",
        "search_diagnostics",
        "search_health",
        "search_apis",
        "search_result_contract",
        "intent_classification",
        "parallel_retrieval",
        "open_in_context",
    ],
    "does_not_own": [
        "documents_corpus",
        "memory_store",
        "knowledge_graph",
        "projects_data",
        "gallery_library",
        "smart_home",
        "voice_runtime",
        "vision_runtime",
        "browser_agent",
        "coding_workspace",
        "planner_tasks",
        "calendar_schedule",
        "automation_runtime",
        "chat_synthesis",
        "web_search_backend",
        "elastic_solr_cluster",
        "second_search_engine",
    ],
}

MENTAL_MODEL = {
    "sidebar": "Filter navigation (views, settings, tools) — not content search",
    "palette": "Ctrl+K — commands + quick federated search",
    "search_home": "Browse everything — facets, previews, history, saved searches",
    "chat": "Answer + synthesis (including web)",
    "voice": "Spoken search via the same engine",
    "products": "Scoped in-product search; products own data",
}

FACETS = (
    "everything",
    "documents",
    "memory",
    "projects",
    "journal",
    "code",
    "graph",
    "connections",
    "audio",
    "web",
    "planner",
    "calendar",
    "gallery",
    "home_assistant",
    "flytying",
    "automation",
    "learned",
)
