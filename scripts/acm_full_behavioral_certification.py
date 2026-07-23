#!/usr/bin/env python3
"""Full ACM behavioral certification — live Aria conversational gate.

Permanent project requirement: the COMPLETE ACM must pass this suite before
any ACM-related commit or push.

Usage:
  python scripts/acm_full_behavioral_certification.py
  python scripts/acm_full_behavioral_certification.py --base http://127.0.0.1:8765

Exit 0 only when every capability check passes.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af]")
SCORE_LEAK = re.compile(
    r"(~\d+%\)|goal\s*\(~|pattern\s*\(~|user\s*\(~|when\s*\(~)",
    re.I,
)
IMPL_LEAK = re.compile(
    r"\b(organ|classification|CognitiveIntent|reasoning_path|Memory Authority|"
    r"activation|COMPETING_RECOLLECTIONS)\b",
    re.I,
)
HOST_FB = re.compile(
    r"still learning about you|I don't have personal memory|"
    r"as an AI language model|No matching memories",
    re.I,
)
WEB_ESCAPE = re.compile(r"\b(web_search|reference_search)\b", re.I)

MEM = ["memory_about_user"]
CONV = ["conversation_language"]


def wait_ready(base: str, timeout: float = 90.0) -> bool:
    live = f"{base.rstrip('/')}/api/live"
    t0 = time.time()
    while time.time() - t0 < timeout:
        r = subprocess.run(
            ["curl", "-sS", "-m", "2", live], capture_output=True, text=True
        )
        if r.returncode == 0 and '"ready":true' in (r.stdout or ""):
            return True
        time.sleep(1)
    return False


def chat(base: str, msg: str, timeout: int = 120, retries: int = 3) -> dict:
    url = f"{base.rstrip('/')}/api/chat"
    for _ in range(retries):
        if not wait_ready(base, 30):
            time.sleep(1)
            continue
        r = subprocess.run(
            [
                "curl",
                "-sS",
                "-m",
                str(timeout),
                "-X",
                "POST",
                url,
                "-F",
                f"message={msg}",
                "-F",
                "stream=false",
            ],
            capture_output=True,
            text=True,
        )
        if r.returncode:
            time.sleep(1)
            continue
        try:
            return json.loads(r.stdout)
        except json.JSONDecodeError:
            time.sleep(1)
    return {"ok": False, "message": "unreachable", "action": None}


def run_suite(base: str) -> list[dict]:
    results: list[dict] = []

    def check(
        cap: str,
        msg: str,
        *,
        must_contain: tuple[str, ...] = (),
        any_of: tuple[str, ...] | None = None,
        must_not: tuple[str, ...] = (),
        action_in: list[str] | None = None,
        english: bool = True,
        no_score: bool = True,
        no_leak: bool = True,
        no_host: bool = True,
        no_web: bool = True,
        source_in: list[str] | None = None,
    ) -> dict:
        d = chat(base, msg)
        reply = d.get("message") or ""
        action = d.get("action")
        status = d.get("cognitive_status")
        source = d.get("source")
        ok = True
        reasons: list[str] = []
        low = reply.lower()
        for s in must_contain:
            if s.lower() not in low:
                ok = False
                reasons.append(f"missing:{s!r}")
        if any_of is not None and not any(s.lower() in low for s in any_of):
            ok = False
            reasons.append(f"none of {any_of}")
        for s in must_not:
            if s.lower() in low:
                ok = False
                reasons.append(f"forbidden:{s!r}")
        if action_in is not None and action not in action_in:
            ok = False
            reasons.append(f"action={action!r}")
        if source_in is not None and source not in source_in:
            ok = False
            reasons.append(f"source={source!r}")
        if english and CJK.search(reply):
            ok = False
            reasons.append("non-English")
        if no_score and SCORE_LEAK.search(reply):
            ok = False
            reasons.append(f"score:{SCORE_LEAK.search(reply).group(0)}")
        if no_leak and IMPL_LEAK.search(reply):
            ok = False
            reasons.append(f"leak:{IMPL_LEAK.search(reply).group(0)}")
        if no_host and HOST_FB.search(reply):
            ok = False
            reasons.append("host-fallback")
        if no_web and action and WEB_ESCAPE.search(str(action)):
            ok = False
            reasons.append(f"web-escape:{action}")
        mark = "PASS" if ok else "FAIL"
        snippet = reply.replace("\n", " ")[:180]
        row = {
            "mark": mark,
            "cap": cap,
            "msg": msg,
            "action": action,
            "status": status,
            "source": source,
            "reply": snippet,
            "reasons": reasons,
        }
        results.append(row)
        print(
            f"[{mark}] {cap}: {msg[:58]!r} -> a={action} src={source} "
            f"st={status} :: {snippet}",
            flush=True,
        )
        if reasons:
            print("   !!", "; ".join(reasons), flush=True)
        return d

    print("=== FULL ACM BEHAVIORAL CERTIFICATION ===", flush=True)

    # --- Identity ---
    check("Identity", "What is my name?", must_contain=("Jeff",), action_in=MEM, source_in=["acm"])
    check("Identity", "Who am I?", must_contain=("Jeff",), action_in=MEM)

    # --- Episodic ---
    check(
        "Episodic-teach",
        "Yesterday I upgraded my GPU.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Episodic-recall",
        "What did I do yesterday?",
        must_contain=("GPU",),
        action_in=MEM,
    )

    # --- Semantic autobiographical ---
    for t in (
        "My laptop runs Zorin.",
        "I'm working on Aria.",
        "I'm building BlackFly.",
        "My desktop has an RTX 3060.",
    ):
        check("Semantic-teach", t, any_of=("remember", "Okay"), action_in=MEM)
    check(
        "Semantic-recall",
        "What operating system does my laptop use?",
        must_contain=("Zorin",),
        action_in=MEM,
    )
    check(
        "Semantic-recall",
        "What projects am I working on?",
        any_of=("Aria", "BlackFly"),
        action_in=MEM,
    )
    check(
        "Semantic-prod",
        "What did I install?",
        must_contain=("SSD",),
        action_in=MEM,
    )

    # --- Preference ---
    check(
        "Pref-teach",
        "I prefer local AI models.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Pref-teach",
        "My favorite programming language is Python.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Pref-recall",
        "What is my favorite programming language?",
        must_contain=("Python",),
        action_in=MEM,
    )
    check(
        "Pref-recall",
        "Do I prefer local AI models or cloud models?",
        must_contain=("local",),
        action_in=MEM,
    )
    # Preference update
    check(
        "Pref-update",
        "My favorite programming language is Rust.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Pref-update-recall",
        "What is my favorite programming language?",
        must_contain=("Rust",),
        action_in=MEM,
        must_not=("Python",),
    )

    # --- Relational / cross-memory ---
    for t in (
        "I upgraded my desktop to train larger AI models.",
        "My goal is to build the best local AI assistant possible.",
        "I'm building Aria to achieve that goal.",
        "Aria uses ACM.",
        "I prefer local AI because I value privacy.",
        "For systems programming I prefer Rust.",
        "BlackFly is part of my AI ecosystem.",
    ):
        check("Relational-teach", t, any_of=("remember", "Okay"), action_in=MEM)
    check(
        "Relational",
        "Why did I upgrade my desktop?",
        any_of=("train", "AI models"),
        action_in=MEM,
    )
    check(
        "Relational",
        "How are Aria and ACM related?",
        any_of=("ACM", "uses"),
        action_in=MEM,
    )
    check(
        "Relational",
        "What language do I prefer for systems programming?",
        must_contain=("Rust",),
        action_in=MEM,
    )
    check(
        "Relational",
        "Why do I prefer local AI?",
        any_of=("privacy", "local"),
        action_in=MEM,
    )
    check(
        "Relational",
        "How does BlackFly fit into my projects?",
        any_of=("BlackFly", "ecosystem"),
        action_in=MEM,
    )
    check(
        "Cross-memory",
        "How does Aria relate to my goal?",
        any_of=("Aria", "goal", "assistant"),
        action_in=MEM,
    )
    check(
        "Relational-prod",
        "Tell me about visiting my brother.",
        must_contain=("brother",),
        action_in=MEM,
    )

    # --- Memory evolution / historical ---
    check(
        "Evolution-teach",
        "My laptop runs Fedora.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Evolution",
        "What operating systems has my laptop used?",
        any_of=("Zorin", "Fedora"),
        action_in=MEM,
    )
    check(
        "Historical",
        "Have my AI preferences changed?",
        english=True,
        action_in=MEM,
        no_host=True,
    )

    # --- Teaching recognition / habit / pattern learning ---
    PRED_TEACH = (
        "It has rained every day this week.",
        "Every time I drink coffee after 8 PM, I have trouble sleeping.",
        "Whenever I skip breakfast, I get hungry before lunch.",
        "Every Saturday I usually go fishing.",
        "I usually get more work done in the morning.",
        "Every weekend for the last year I have gone hiking.",
        "Coffee causes insomnia.",
        "Sometimes coffee helps me sleep.",
    )
    for t in PRED_TEACH:
        check("Habit-teach", t, any_of=("remember", "Okay"), action_in=MEM)

    # Re-anchor Saturday → fishing so prior Habit-update runs cannot poison Prediction.
    check(
        "Pred-anchor-teach",
        "Every Saturday I usually go fishing.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )

    # --- Prediction ---
    check(
        "Prediction",
        "What is likely to happen tomorrow?",
        must_contain=("rain",),
        action_in=MEM,
        must_not=("coffee",),
        source_in=["acm"],
    )
    check(
        "Prediction",
        "What am I likely to do next Saturday?",
        must_contain=("fishing",),
        action_in=MEM,
        must_not=("hiking",),
    )
    check(
        "Prediction",
        "When am I likely to be most productive?",
        any_of=("work", "morning", "productive"),
        action_in=MEM,
    )
    check(
        "Prediction",
        "If I skip breakfast, what is likely to happen?",
        must_contain=("hungry",),
        action_in=MEM,
        must_not=("rain",),
    )
    check(
        "Prediction",
        "Will it rain tomorrow?",
        must_contain=("rain",),
        action_in=MEM,
    )
    # Prediction update — reinforce fishing
    check(
        "Pred-update-teach",
        "Every Saturday I usually go fishing.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Pred-update",
        "What am I likely to do next Saturday?",
        must_contain=("fishing",),
        action_in=MEM,
    )

    # --- Recommendation ---
    check(
        "Recommendation",
        "When SHOULD I work?",
        must_contain=("recommend",),
        action_in=MEM,
        must_not=("likely from memory",),
    )
    check(
        "Recommendation",
        "Which of my computers should I use for training AI?",
        any_of=("desktop", "train"),
        action_in=MEM,
    )

    # --- Confidence / certainty ---
    check(
        "Confidence",
        "How confident are you that I'll go hiking this weekend?",
        must_contain=("confidence",),
        action_in=MEM,
    )
    check(
        "Certainty",
        "Will I definitely go fishing next Saturday?",
        any_of=("fishing", "certain", "definite", "likely"),
        action_in=MEM,
    )

    # --- Explainability ---
    check(
        "Explain",
        "Why do you think that is likely?",
        action_in=MEM,
        any_of=("taught", "previously", "fishing", "hiking", "because"),
    )
    check(
        "Explain",
        "How did you make that prediction?",
        action_in=MEM,
        english=True,
    )

    # --- Conflict resolution + evidence filter ---
    check(
        "Conflict",
        "If I drink coffee after 8 PM, what is likely to happen?",
        must_contain=("conflict",),
        action_in=MEM,
        must_not=("rain",),
    )

    # --- Unknown / failure ---
    check(
        "Unknown",
        "What am I likely to do on my birthday next year?",
        must_contain=("don't currently know",),
        action_in=MEM,
    )
    check(
        "Unknown",
        "What will happen in the stock market tomorrow?",
        must_contain=("don't currently know",),
        action_in=MEM,
    )
    check(
        "Unknown",
        "Why did I buy my phone?",
        any_of=("don't currently know", "don't know", "not sure", "no"),
        action_in=MEM,
        english=True,
    )

    # --- Conversation management ---
    check(
        "ConvLang",
        "What language have we been speaking in during this conversation?",
        must_contain=("English",),
        action_in=CONV,
        must_not=("Python", "Rust"),
    )

    # --- Language stability ---
    check(
        "LangStab",
        "Will it rain tomorrow?",
        must_contain=("rain",),
        action_in=MEM,
        english=True,
    )
    check(
        "LangStab",
        "When SHOULD I work?",
        must_contain=("recommend",),
        action_in=MEM,
        english=True,
    )

    # --- Memory Authority / reconstruction / context ---
    check(
        "MemAuth",
        "What did I install?",
        must_contain=("SSD",),
        action_in=MEM,
        source_in=["acm"],
    )
    check(
        "MemAuth",
        "What is likely to happen tomorrow?",
        must_contain=("rain",),
        action_in=MEM,
        source_in=["acm"],
    )
    check(
        "Reconstruction",
        "Summarize what you know about my AI setup.",
        any_of=("local", "Aria", "ACM", "BlackFly"),
        action_in=MEM,
        english=True,
    )
    check(
        "Context",
        "What have I caught?",
        any_of=("trout", "three"),
        action_in=MEM,
    )

    # --- NLU variations (same intent, alternate phrasing) ---
    check(
        "NLU",
        "What's my name?",
        must_contain=("Jeff",),
        action_in=MEM,
    )
    check(
        "NLU",
        "What fish did I catch?",
        any_of=("trout", "three"),
        action_in=MEM,
    )
    check(
        "NLU",
        "What did I catch?",
        any_of=("trout", "three"),
        action_in=MEM,
    )
    check(
        "NLU",
        "If I drink coffee late at night, what is likely to happen?",
        any_of=("conflict", "sleep", "insomni", "trouble"),
        action_in=MEM,
        must_not=("rain",),
    )
    check(
        "NLU",
        "Am I likely to go fishing next Saturday?",
        must_contain=("fishing",),
        action_in=MEM,
    )
    check(
        "NLU",
        "What programming language do I prefer for systems programming?",
        must_contain=("Rust",),
        action_in=MEM,
    )

    # --- Habit / recommendation updates ---
    # Use Sunday (not Saturday) so this update cannot poison the Saturday→fishing
    # prediction gate used earlier in this suite and on the next certification run.
    check(
        "Habit-update-teach",
        "Every Sunday I usually go hiking.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Habit-update",
        "What am I likely to do next Sunday?",
        any_of=("hiking", "Sunday", "sunday"),
        action_in=MEM,
        english=True,
    )
    check(
        "Rec-update-teach",
        "I usually get more work done in the evening.",
        any_of=("remember", "Okay"),
        action_in=MEM,
    )
    check(
        "Rec-update",
        "When SHOULD I work?",
        must_contain=("recommend",),
        action_in=MEM,
        any_of=("morning", "evening"),
    )

    # --- Provenance / evidence explainability ---
    check(
        "Provenance",
        "How did you know why I upgraded my desktop?",
        any_of=("taught", "upgraded", "train", "previously", "because"),
        action_in=MEM,
        english=True,
        must_not=("RAM",),
    )

    # --- Agent identity (non-ACM chat OK) ---
    check(
        "Identity-agent",
        "Who are you?",
        any_of=("ARIA", "Aria", "assistant"),
        english=True,
        no_host=False,
    )

    # --- Version compatibility (pin readable via live identity still works) ---
    check(
        "Version-compat",
        "What is my name?",
        must_contain=("Jeff",),
        action_in=MEM,
        source_in=["acm"],
    )

    return results


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--base", default="http://127.0.0.1:8765")
    ap.add_argument(
        "--report",
        default="/tmp/acm_full_behavioral_certification.json",
    )
    args = ap.parse_args()
    if not wait_ready(args.base, 90):
        print("FAIL: Aria not ready", file=sys.stderr)
        return 2
    results = run_suite(args.base)
    fails = [r for r in results if r["mark"] == "FAIL"]
    Path(args.report).write_text(json.dumps(results, indent=2))
    print("\n=== SUMMARY ===", flush=True)
    print(
        f"total={len(results)} pass={len(results) - len(fails)} fail={len(fails)}",
        flush=True,
    )
    for r in fails:
        print("FAIL", r["cap"], r["msg"][:70], r["reasons"], flush=True)

    pred_caps = {
        "Habit-teach",
        "Prediction",
        "Pred-update-teach",
        "Pred-update",
        "Recommendation",
        "Confidence",
        "Certainty",
        "Explain",
        "Conflict",
        "Unknown",
    }
    bad_routes = [
        r
        for r in results
        if r["cap"] in pred_caps and r["action"] != "memory_about_user"
    ]
    cjk = sum(1 for r in results if CJK.search(r["reply"] or ""))
    host = sum(1 for r in results if "host-fallback" in r.get("reasons", []))
    print("pred_family_bad_routes", len(bad_routes), flush=True)
    print("cjk_hits", cjk, flush=True)
    print("host_fallback_hits", host, flush=True)
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
