"""Second held-out routing set (Phase 6) — labelled before either router was
scored on it; not used to tune rules. Same format as routing_corpus.CASES."""

CLARIFY = "clarify"
_CHATTY = {"chat", CLARIFY, "capabilities"}

CASES = [
    # ---------------------------------------------------------------- phrasing
    ("h2-phr-01", "phrasing", "set a two minute timer for the tea", {"planner_set_timer"}, {"duration": "2"}),
    ("h2-phr-02", "phrasing", "45 second timer", {"planner_set_timer"}, {"duration": "45"}),
    ("h2-phr-03", "phrasing", "wake me up at 5 tomorrow", {"planner_set_alarm"}, {"time": "5"}),
    ("h2-phr-04", "phrasing", "alarm at 7:15pm", {"planner_set_alarm"}, {"time": "7:15"}),
    ("h2-phr-05", "phrasing", "add re-spool the 5wt to my tasks", {"planner_add_task"}, {"text": "re-spool"}),
    ("h2-phr-06", "phrasing", "put buy floatant on the to-do list", {"planner_add_task"}, {"text": "floatant"}),
    ("h2-phr-07", "phrasing", "schedule a guide trip on my calendar for Saturday at 6am", {"planner_add_event"}, None),
    ("h2-phr-08", "phrasing", "kill mission 0123456789ab", {"mission_cancel"}, {"mission_id": "0123456789ab"}),
    ("h2-phr-09", "phrasing", "research the history of the woolly bugger in depth", {"research_create", "web_search", "learn_about"}, None),
    ("h2-phr-10", "phrasing", "start some deep research into tenkara line weights", {"research_create"}, None),
    ("h2-phr-11", "phrasing", "draw a steelhead leaping a waterfall", {"generate_image"}, None),
    ("h2-phr-12", "phrasing", "compose a song about the evening caddis hatch", {"generate_song", "generate_music"}, None),
    ("h2-phr-13", "phrasing", "turn the shop lights off", {"ha_control"}, None),
    ("h2-phr-14", "phrasing", "how much ram is being used", {"runtime_ram", "runtime_status"}, None),
    ("h2-phr-15", "phrasing", "search my docs for the reel warranty", {"document_search", "document_ask_library"}, None),
    # ---------------------------------------------------------------- unsupported
    ("h2-uns-01", "unsupported", "remote start the truck", _CHATTY, None),
    ("h2-uns-02", "unsupported", "reserve a campsite at Baxter for the weekend", _CHATTY, None),
    ("h2-uns-03", "unsupported", "venmo Dave $40 for the flies", _CHATTY, None),
    ("h2-uns-04", "unsupported", "call my brother", _CHATTY, None),
    ("h2-uns-05", "unsupported", "buy a new net from cabelas.com", _CHATTY, None),
    ("h2-uns-06", "unsupported", "tweet that the hatch is on", _CHATTY | {"web_search"}, None),
    # ---------------------------------------------------------------- needs an artifact
    ("h2-art-01", "artifact", "describe this photo", {CLARIFY, "describe_image"}, None),
    ("h2-art-02", "artifact", "what's in this picture?", {CLARIFY, "describe_image"}, None),
    ("h2-art-03", "artifact", "summarize this pdf", {CLARIFY, "document_summarize"}, None),
    ("h2-art-04", "artifact", "give me a summary of the report", {CLARIFY, "document_summarize", "chat"}, None),
    # ---------------------------------------------------------------- near misses
    ("h2-nm-01", "nearmiss", "what is a good alarm clock app?", {"chat", "web_search"}, None),
    ("h2-nm-02", "nearmiss", "who invented the kitchen timer?", {"chat", "web_search"}, None),
    ("h2-nm-03", "nearmiss", "why do trucks need diesel exhaust fluid?", {"chat", "web_search"}, None),
    ("h2-nm-04", "nearmiss", "explain how planners help with ADHD", {"chat"}, None),
    ("h2-nm-05", "nearmiss", "what's a to do list", {"chat"}, None),
    ("h2-nm-06", "nearmiss", "is research on fly fishing ethics published anywhere?", {"chat", "web_search"}, None),
    ("h2-nm-07", "nearmiss", "the image of the river in my head is vivid", {"chat"}, None),
    ("h2-nm-08", "nearmiss", "text summarization is a hard problem", {"chat"}, None),
    ("h2-nm-09", "nearmiss", "calling all fly tiers: what's your favourite dubbing?", {"chat"}, None),
    ("h2-nm-10", "nearmiss", "I ordered waders from Orvis last week", {"chat"}, None),
    # ---------------------------------------------------------------- ambiguous
    ("h2-amb-01", "ambiguous", "cancel that", {CLARIFY, "session_interrupt"}, None),
    ("h2-amb-02", "ambiguous", "stop it", {CLARIFY, "session_interrupt"}, None),
    ("h2-amb-03", "ambiguous", "delete that", {CLARIFY}, None),
    ("h2-amb-04", "ambiguous", "update it", {CLARIFY}, None),
    ("h2-amb-05", "ambiguous", "share it", {CLARIFY}, None),
    # ---------------------------------------------------------------- multi-turn
    ("h2-mt-01", "multiturn", ("set a timer for 8 minutes", "make it 12"), {"planner_update_timer", "planner_set_timer", CLARIFY}, {"duration": "12"}),
    ("h2-mt-02", "multiturn", ("set an alarm for 5:45am", "change it to 6"), {"planner_update_alarm", "planner_set_alarm", CLARIFY}, {"time": "6"}),
    ("h2-mt-03", "multiturn", ("what's the forecast for tomorrow", "what about Friday?"), {"weather_forecast"}, None),
    ("h2-mt-04", "multiturn", ("add a task to tie six caddis", "also add another one: clean the vise"), {"planner_add_task"}, {"text": "clean the vise"}),
    ("h2-mt-05", "multiturn", ("set a timer for 8 minutes", "how long do brook trout live?"), {"chat", "web_search"}, None),
    # ---------------------------------------------------------------- coding continuity
    ("h2-code-01", "coding", "What were we doing with the Fly Tying Reference?", {"coding_project_activity", "continuity_recall"}, None),
    ("h2-code-02", "coding", "which agent worked on BlackFly today?", {"coding_agent_changes", "coding_agent_runs"}, None),
    ("h2-code-03", "coding", "what did codex actually change?", {"coding_agent_changes"}, None),
    ("h2-code-04", "coding", "what's waiting for my approval?", {"coding_approvals_pending", CLARIFY}, None),
    ("h2-code-05", "coding", "ask claude to review the scraper retry logic", {"coding_agent_plan"}, None),
    ("h2-code-06", "coding", "have antigravity explain the barcode module", {"coding_agent_plan"}, None),
    ("h2-code-07", "coding", "what did claude test?", {"coding_agent_tests"}, None),
    ("h2-code-08", "coding", "resume the interrupted coding task", {"coding_agent_resume"}, None),
    ("h2-code-09", "coding", "roll back the promotion", {"coding_promotion_rollback"}, None),
    ("h2-code-10", "coding", "the codex docs are confusing", {"chat"}, None),
    ("h2-code-11", "coding", "I like how BlackFly handles retries", {"chat"}, None),
    # ---------------------------------------------------------------- real-ish
    ("h2-real-01", "real", "Good morning", {"greeting", "morning_briefing"}, None),
    ("h2-real-02", "real", "What do you know about me?", {"memory_about_user"}, None),
    ("h2-real-03", "real", "Where did we leave off?", {"continuity_recall"}, None),
    ("h2-real-04", "real", "show git status", {"git_status"}, None),
]
