"""ARIA routing benchmark corpus.

Categories:
  real       requests recorded in production (data/logs/workstation_activity.jsonl,
             Aug–Sep 2026), labelled by hand
  confirmed  the three misroutes confirmed in Phase 4, and close variants
  everyday   realistic requests across ARIA's domains
  ambiguous  genuinely underspecified — a clarifying question is the right answer
  unsupported  things ARIA cannot do — must not become an unrelated action
  multiturn  follow-ups that depend on the previous turn

Each case: (id, category, text, acceptable actions, expected args or None).
"clarify" in the acceptable set means a clarification is a correct outcome.
Args are checked as case-insensitive substrings of the routed params' values.
Multi-turn cases are tuples of turns; only the last turn is scored.
"""

CLARIFY = "clarify"

CASES = [
    # ---------------------------------------------------------------- real
    ("real-01", "real", "what can you do", {"capabilities"}, None),
    ("real-02", "real", "cancel mission 3f18c26524ce", {"mission_cancel"}, {"mission_id": "3f18c26524ce"}),
    ("real-03", "real", "Good morning", {"greeting", "morning_briefing"}, None),
    ("real-04", "real", "Generate a song:", {"generate_song", "generate_music", CLARIFY}, None),
    ("real-05", "real", "Help me reprioritize my planner tasks for today", {"planner_plan", "planner_today", "planner_list_tasks"}, None),
    ("real-06", "real", "What should I focus on in Planner today?", {"planner_today", "planner_plan", "what_should_i_work_on_next", "today_recommendations"}, None),
    ("real-07", "real", "Add a planner task:", {"planner_add_task", CLARIFY}, None),
    ("real-08", "real", "do deep research on tenkara rod action and learn about it", {"learn_about", "research_create", "research_run", "knowledge_research_run"}, None),
    ("real-09", "real", "learn about hackle feather quality for dry flies", {"learn_about", "research_create"}, None),
    ("real-10", "real", "generate an image of a brook trout in a mountain stream", {"generate_image"}, None),
    ("real-11", "real", "make a meme with top text WHEN THE TEST PASSES and bottom text FIRST TRY", {"generate_meme"}, None),
    ("real-12", "real", "make a meme about fly fishing", {"generate_meme"}, None),
    ("real-13", "real", "upscale the image 2x", {"upscale_image", CLARIFY}, None),
    ("real-14", "real", "edit the image to add falling snow", {"edit_image", CLARIFY}, None),
    ("real-15", "real", "inpaint the top left corner with a fly rod", {"inpaint_image", CLARIFY}, None),
    ("real-16", "real", "generate a video of a trout swimming in a stream", {"generate_video"}, None),
    ("real-17", "real", "What is a meme?", {"chat"}, None),
    ("real-18", "real", "Can you explain image upscaling?", {"chat"}, None),
    ("real-19", "real", "What is inpainting?", {"chat"}, None),
    ("real-20", "real", "How does video generation work?", {"chat"}, None),
    ("real-21", "real", "How do you create a PDF?", {"chat"}, None),
    ("real-22", "real", "Can you export CSV files?", {"chat", "capabilities"}, None),
    ("real-23", "real", "How does calendar integration work?", {"chat", "capabilities"}, None),
    ("real-24", "real", "Why would someone export to CSV?", {"chat"}, None),
    ("real-25", "real", "Investigate the stale active-request lifecycle and report any relevant logs",
     {"coding_diagnose", "aria_self_diagnose", "coding_agent", "observe_log", "coding_chat", "coding_task"}, None),
    ("real-26", "real", "Say hello in one short sentence.", {"chat", "greeting"}, None),
    ("real-27", "real", "What is 2 plus 2? Answer with just the number.", {"chat"}, None),
    ("real-28", "real", "What is 3 plus 3? Just the number.", {"chat"}, None),
    ("real-29", "real", "stop", {"session_interrupt"}, None),
    ("real-30", "real", "What do you know about me?", {"memory_about_user"}, None),
    ("real-31", "real", "Remember that I prefer concise answers.", {"remember"}, {"text": "concise"}),
    ("real-32", "real", "research in exhaustive depth the complete global history of hydraulic excavators",
     {"research_create", "web_search", "research_run", "learn_about"}, None),
    ("real-33", "real", "what is my GPU?", {"runtime_gpu"}, None),
    ("real-34", "real", "search the web for the boiling point of nitrogen", {"web_search"}, None),
    ("real-35", "real", "Who wrote Hamlet?", {"chat"}, None),
    ("real-36", "real", "Reply with only the number 10.", {"chat"}, None),
    # ---------------------------------------------------------------- confirmed misroutes
    ("conf-01", "confirmed", "Wake me at 5:30", {"planner_set_alarm"}, {"time": "5:30"}),
    ("conf-02", "confirmed", "Wake me at 5:30 tomorrow for the morning hatch.", {"planner_set_alarm"}, {"time": "5:30"}),
    ("conf-03", "confirmed", "Add order more hackle to my to-do list", {"planner_add_task"}, {"text": "hackle"}),
    ("conf-04", "confirmed", "Put 'order more hackle' on my to-do list.", {"planner_add_task"}, {"text": "hackle"}),
    ("conf-05", "confirmed", "12-minute timer", {"planner_set_timer"}, {"duration": "12"}),
    ("conf-06", "confirmed", "Give me a 12 minute timer for the epoxy.", {"planner_set_timer"}, {"duration": "12"}),
    # ---------------------------------------------------------------- everyday
    ("day-01", "everyday", "Is it going to rain at the river tomorrow?", {"weather_forecast"}, None),
    ("day-02", "everyday", "what's the weather like this weekend", {"weather_forecast"}, None),
    ("day-03", "everyday", "set a timer for 20 minutes", {"planner_set_timer"}, {"duration": "20"}),
    ("day-04", "everyday", "remind me in 45 minutes to flip the steaks", {"planner_set_timer", "planner_add_task", "planner_set_alarm"}, None),
    ("day-05", "everyday", "set an alarm for 6am", {"planner_set_alarm"}, {"time": "6"}),
    ("day-06", "everyday", "add buy 5X tippet to my tasks", {"planner_add_task"}, {"text": "tippet"}),
    ("day-07", "everyday", "what's on my plate today", {"planner_today", "daily_status", "what_am_i_working_on"}, None),
    ("day-08", "everyday", "show my open tasks", {"planner_list_tasks", "planner_today", "journal_open_tasks"}, None),
    ("day-09", "everyday", "put the dentist on my calendar Thursday at 3pm", {"planner_add_event"}, None),
    ("day-10", "everyday", "Where did we leave off?", {"continuity_recall"}, None),
    ("day-11", "everyday", "What did we decide about the fishing log app?", {"continuity_recall"}, None),
    ("day-12", "everyday", "forget that my car is red", {"memory_forget"}, None),
    ("day-13", "everyday", "draw a mayfly dun on the water at sunset", {"generate_image"}, None),
    ("day-14", "everyday", "make a song about catching my first brook trout", {"generate_song", "generate_music"}, None),
    ("day-15", "everyday", "list my missions", {"mission_list"}, None),
    ("day-16", "everyday", "what's the status of mission 3f18c26524ce", {"mission_status"}, {"mission_id": "3f18c26524ce"}),
    ("day-17", "everyday", "show git status", {"git_status"}, None),
    ("day-18", "everyday", "fix the off-by-one bug in scraper.py", {"coding_fix", "coding_agent", "coding_task"}, None),
    ("day-19", "everyday", "how much RAM is free right now", {"runtime_ram", "runtime_status"}, None),
    ("day-20", "everyday", "turn off the living room lights", {"ha_control"}, None),
    ("day-21", "everyday", "how do I tie a parachute adams", {"chat"}, None),
    ("day-22", "everyday", "log in my journal that the hatch was incredible today", {"journal_log"}, None),
    ("day-23", "everyday", "search my documents for the waders warranty", {"document_search", "document_ask_library"}, None),
    ("day-24", "everyday", "brief me", {"morning_briefing", "daily_status"}, None),
    ("day-25", "everyday", "what's my CPU load", {"runtime_cpu", "runtime_status"}, None),
    ("day-26", "everyday", "write a python script that renames my photos by date", {"coding_create"}, None),
    ("day-27", "everyday", "explain the difference between a nymph and an emerger", {"chat"}, None),
    ("day-28", "everyday", "transcribe this recording", {"transcribe", "record_transcribe", CLARIFY}, None),
    ("day-29", "everyday", "what models do you have installed", {"model_inventory", "runtime_models", "models_info"}, None),
    ("day-30", "everyday", "pause mission 3f18c26524ce", {"mission_pause"}, {"mission_id": "3f18c26524ce"}),
    ("day-31", "everyday", "what was I working on", {"what_am_i_working_on", "continuity_recall", "project_resume"}, None),
    ("day-32", "everyday", "play some music", {"play_audio", CLARIFY}, None),
    ("day-33", "everyday", "what's the capital of Montana", {"chat"}, None),
    ("day-34", "everyday", "summarize the latest news", {"briefing_news_detail", "web_search", "morning_briefing"}, None),
    ("day-35", "everyday", "set a 3 minute timer for my tea", {"planner_set_timer"}, {"duration": "3"}),
    ("day-36", "everyday", "can you add a task to call the fly shop tomorrow", {"planner_add_task"}, {"text": "fly shop"}),
    ("day-37", "everyday", "alarm for 4:45 am", {"planner_set_alarm"}, {"time": "4:45"}),
    ("day-38", "everyday", "what's the forecast for Saturday", {"weather_forecast"}, None),
    # ---------------------------------------------------------------- ambiguous
    ("amb-01", "ambiguous", "can you fix it?", {CLARIFY}, None),
    ("amb-02", "ambiguous", "do the thing", {CLARIFY, "chat"}, None),
    ("amb-03", "ambiguous", "turn it off", {CLARIFY}, None),
    ("amb-04", "ambiguous", "delete it", {CLARIFY}, None),
    ("amb-05", "ambiguous", "set it for tomorrow", {CLARIFY}, None),
    ("amb-06", "ambiguous", "run it again", {CLARIFY, "session_repeat"}, None),
    # ---------------------------------------------------------------- unsupported
    ("uns-01", "unsupported", "book me a flight to Denver next Friday", {"chat", CLARIFY, "capabilities"}, None),
    ("uns-02", "unsupported", "order a large pepperoni pizza", {"chat", CLARIFY, "capabilities"}, None),
    ("uns-03", "unsupported", "transfer $500 to my savings account", {"chat", CLARIFY, "capabilities"}, None),
    ("uns-04", "unsupported", "text my brother that I'm running late", {"chat", CLARIFY, "capabilities"}, None),
    ("uns-05", "unsupported", "buy new waders on amazon", {"chat", CLARIFY, "capabilities"}, None),
    ("uns-06", "unsupported", "call my mom", {"chat", CLARIFY, "capabilities"}, None),
    ("uns-07", "unsupported", "renew my fishing license", {"chat", CLARIFY, "capabilities", "web_search"}, None),
    ("uns-08", "unsupported", "unlock the front door", {"chat", CLARIFY, "capabilities", "ha_control"}, None),
    # ---------------------------------------------------------------- multi-turn (last turn scored)
    ("mt-01", "multiturn", ("set a timer for 10 minutes", "actually make it 15"), {"planner_set_timer", "planner_update_timer", CLARIFY}, None),  # Phase 6: updating the existing timer/alarm is the requested behaviour
    ("mt-02", "multiturn", ("generate an image of a brook trout", "now make it snowy"), {"edit_image", "generate_image", CLARIFY}, None),
    ("mt-03", "multiturn", ("What do you know about me?", "Show me the evidence."), {"memory_about_user", "correction_recall", "evidence_provenance"}, None),
    ("mt-04", "multiturn", ("add a task to order hackle", "and another one to clean my reels"), {"planner_add_task"}, {"text": "reels"}),
    ("mt-05", "multiturn", ("what's the weather tomorrow", "and on Sunday?"), {"weather_forecast"}, None),
    ("mt-06", "multiturn", ("list my missions", "cancel the first one"), {"mission_cancel", CLARIFY}, None),
]
