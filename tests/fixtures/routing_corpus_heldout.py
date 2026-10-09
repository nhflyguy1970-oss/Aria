"""Held-out routing cases — written and labelled before the Phase 5 router was
scored on them, and never used to tune its rules.

  real      unseen requests from production (conversation archive and
            workstation_activity.jsonl), not in routing_corpus.py
  phrasing  new wordings of supported requests
  nearmiss  look like a rule's trigger but must NOT run that action
  ambiguous / unsupported / multiturn — as in routing_corpus.py

Same format as routing_corpus.CASES.
"""

CLARIFY = "clarify"
_CHATTY = {"chat", CLARIFY, "capabilities"}

CASES = [
    # ---------------------------------------------------------------- real (unseen)
    ("h-real-01", "real", "how do i change the brakes on a 2021 ford ranger xt", {"chat", "web_search", "continuity_recall"}, None),
    ("h-real-02", "real", "are you going to answer my question?", {"chat", "session_continue", "session_repeat"}, None),
    ("h-real-03", "real", "research the melting point of pure copper in depth", {"research_create", "web_search", "learn_about", "research_run"}, None),
    ("h-real-04", "real", "do deep research overnight on bushcraft.", {"research_create", "learn_about", "research_run", "mission_create"}, None),
    ("h-real-05", "real", "show me the fibonacci sequence to n=10", {"chat", "coding_run"}, None),
    ("h-real-06", "real", "can you run an estimate of what the numbers will be in the next powerball drawing?", {"chat"}, None),
    ("h-real-07", "real", "can you use an outside source to look for the answer", {"web_search", "chat", CLARIFY}, None),
    ("h-real-08", "real", "make a meme with top HELLO and bottom WORLD", {"generate_meme"}, None),
    ("h-real-09", "real", "make a meme", {"generate_meme", CLARIFY}, None),
    ("h-real-10", "real", "generate an image of a mayfly on water", {"generate_image"}, None),
    ("h-real-11", "real", "generate a video of a river", {"generate_video"}, None),
    ("h-real-12", "real", "What would happen if I added this to my calendar?", {"chat", CLARIFY}, None),
    ("h-real-13", "real", "say ok", {"chat"}, None),
    ("h-real-14", "real", "Describe this image.", {"describe_image", "analyze_image", CLARIFY}, None),
    ("h-real-15", "real", "Summarize this document.", {"document_summarize", CLARIFY}, None),
    ("h-real-16", "real", "Promote an actionable Journal note into a Planner task for today. Ask me which note if unclear.",
     {"planner_add_task", "journal_open_tasks", CLARIFY, "chat"}, None),
    # ---------------------------------------------------------------- phrasing
    ("h-phr-01", "phrasing", "start a 25 minute countdown", {"planner_set_timer"}, {"duration": "25"}),
    ("h-phr-02", "phrasing", "timer, 90 seconds", {"planner_set_timer"}, {"duration": "90"}),
    ("h-phr-03", "phrasing", "could you set a timer for half an hour", {"planner_set_timer"}, {"duration": "30"}),
    ("h-phr-04", "phrasing", "wake me up at 6:15 am", {"planner_set_alarm"}, {"time": "6:15"}),
    ("h-phr-05", "phrasing", "set my alarm for 7", {"planner_set_alarm"}, {"time": "7"}),
    ("h-phr-06", "phrasing", "put renew boat registration on the to-do list", {"planner_add_task"}, {"text": "boat registration"}),
    ("h-phr-07", "phrasing", "add a task: sharpen the hooks", {"planner_add_task"}, {"text": "sharpen"}),
    ("h-phr-08", "phrasing", "remind me in 20 minutes to check the smoker", {"planner_set_timer", "planner_add_task"}, None),
    ("h-phr-09", "phrasing", "abort mission 9a1b2c3d4e5f", {"mission_cancel"}, {"mission_id": "9a1b2c3d4e5f"}),
    ("h-phr-10", "phrasing", "show me all running missions", {"mission_list"}, None),
    ("h-phr-11", "phrasing", "how's mission 9a1b2c3d4e5f doing", {"mission_status"}, {"mission_id": "9a1b2c3d4e5f"}),
    ("h-phr-12", "phrasing", "switch the porch light on", {"ha_control"}, {"target": "porch light"}),
    ("h-phr-13", "phrasing", "write me a song about a rainy day on the Ausable", {"generate_song", "generate_music"}, None),
    ("h-phr-14", "phrasing", "sketch a brown trout rising to a caddis", {"generate_image"}, None),
    ("h-phr-15", "phrasing", "how busy is the cpu right now", {"runtime_cpu", "runtime_status"}, None),
    ("h-phr-16", "phrasing", "will it be windy on the lake tomorrow", {"weather_forecast"}, None),
    ("h-phr-17", "phrasing", "schedule a call with Dave on my calendar for Monday at 10", {"planner_add_event"}, None),
    ("h-phr-18", "phrasing", "debug the crash in tools/export.py", {"coding_fix", "coding_diagnose"}, None),
    ("h-phr-19", "phrasing", "what's on the planner for today", {"planner_today"}, None),
    ("h-phr-20", "phrasing", "jot down in my journal that the trico spinner fall was at 8am", {"journal_log"}, None),
    # ---------------------------------------------------------------- near misses
    ("h-nm-01", "nearmiss", "how does a kitchen timer work?", {"chat"}, None),
    ("h-nm-02", "nearmiss", "my alarm didn't go off this morning, why might that be?", {"chat", "planner_today"}, None),
    ("h-nm-03", "nearmiss", "what is a to-do list app called that syncs with outlook?", {"chat", "web_search"}, None),
    ("h-nm-04", "nearmiss", "can you draw a conclusion from these numbers: 3, 6, 12, 24?", {"chat"}, None),
    ("h-nm-05", "nearmiss", "I set a timer yesterday and it never rang", {"chat", CLARIFY}, None),
    ("h-nm-06", "nearmiss", "what's a good song about fishing?", {"chat", "web_search"}, None),
    ("h-nm-07", "nearmiss", "explain how home assistant turns lights on and off", {"chat"}, None),
    ("h-nm-08", "nearmiss", "the mission statement for my fly shop needs work", {"chat"}, None),
    ("h-nm-09", "nearmiss", "what does an alarm clock radio cost?", {"chat", "web_search"}, None),
    ("h-nm-10", "nearmiss", "who wrote the song wake me up when september ends", {"chat", "web_search"}, None),
    ("h-nm-11", "nearmiss", "is it worth putting a planner on my desk?", {"chat"}, None),
    ("h-nm-12", "nearmiss", "tell me about the history of the egg timer", {"chat", "web_search"}, None),
    # ---------------------------------------------------------------- ambiguous
    ("h-amb-01", "ambiguous", "cancel it", {CLARIFY}, None),
    ("h-amb-02", "ambiguous", "send that", {CLARIFY}, None),
    ("h-amb-03", "ambiguous", "move it to tomorrow", {CLARIFY}, None),
    ("h-amb-04", "ambiguous", "remove those", {CLARIFY}, None),
    ("h-amb-05", "ambiguous", "set an alarm", {CLARIFY}, None),
    ("h-amb-06", "ambiguous", "start a timer", {CLARIFY}, None),
    # ---------------------------------------------------------------- unsupported
    ("h-uns-01", "unsupported", "reserve a table for two at Tony's at 7", _CHATTY, None),
    ("h-uns-02", "unsupported", "pay my electric bill", _CHATTY, None),
    ("h-uns-03", "unsupported", "post this on facebook", _CHATTY, None),
    ("h-uns-04", "unsupported", "email my boss that I'm sick", _CHATTY, None),
    ("h-uns-05", "unsupported", "start my truck", _CHATTY | {"ha_control"}, None),
    ("h-uns-06", "unsupported", "order more 6X tippet from Orvis", _CHATTY, None),
    # ---------------------------------------------------------------- multi-turn
    ("h-mt-01", "multiturn", ("set a timer for 5 minutes", "make it 8"), {"planner_set_timer", "planner_update_timer", CLARIFY}, {"duration": "8"}),  # Phase 6: updating the existing timer/alarm is the requested behaviour
    ("h-mt-02", "multiturn", ("set an alarm for 6am", "actually make it 6:30"), {"planner_set_alarm", "planner_update_alarm", CLARIFY}, {"time": "6:30"}),  # Phase 6: updating the existing timer/alarm is the requested behaviour
    ("h-mt-03", "multiturn", ("add a task to buy leader material", "one more: wax the line"), {"planner_add_task"}, {"text": "wax the line"}),
    ("h-mt-04", "multiturn", ("is it going to rain tomorrow", "what about saturday?"), {"weather_forecast"}, None),
    ("h-mt-05", "multiturn", ("set a timer for 5 minutes", "what's the capital of Vermont?"), {"chat"}, None),
    ("h-mt-06", "multiturn", ("what's the weather tomorrow", "make it 8"), {"chat", CLARIFY}, None),
]
