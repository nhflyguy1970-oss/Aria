"""ARIA workload benchmark — correctness first, then cost.

The older execution benchmark ranks models on latency and throughput over a
handful of toy prompts. This one asks whether a model does ARIA's actual jobs
correctly, and only then how fast and how heavy it is:

  reasoning    exact-answer arithmetic, logic, dates and instruction following
  routing      choose ARIA's action for an utterance (JSON, and native tools)
  coding       write functions that must pass hidden unit tests
  memory       answer from retrieved conversation records — and say "no record"
               when the record is absent instead of inventing one
  evidence     judge a claim from snippets: supported / contradicted /
               insufficient (unrelated text must not count as support)
  vision       read colour, count and text from generated images

Every task is scored deterministically by code; no model grades another.
Scorers live here so they can be unit-tested; the runner is
``scripts/benchmark_local_models.py``.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class Task:
    id: str
    category: str
    prompt: str
    score: Callable[[str], bool]
    system: str = ""
    max_tokens: int = 256
    images: list[str] = field(default_factory=list)  # file paths, filled at run time
    tools: list[dict] | None = None
    score_tool: Callable[[list[dict]], bool] | None = None


# ------------------------------------------------------------------ helpers


def _strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text or "", flags=re.S).strip()


def _final_line(text: str) -> str:
    lines = [ln.strip() for ln in _strip_thinking(text).splitlines() if ln.strip()]
    return lines[-1] if lines else ""


def _number_is(expected: float) -> Callable[[str], bool]:
    def check(text: str) -> bool:
        nums = re.findall(r"-?\d+(?:\.\d+)?", _strip_thinking(text).replace(",", ""))
        return bool(nums) and abs(float(nums[-1]) - expected) < 1e-6

    return check


def _word_is(expected: str) -> Callable[[str], bool]:
    def check(text: str) -> bool:
        words = re.findall(r"[A-Za-z]+", _strip_thinking(text))
        return bool(words) and words[-1].lower() == expected.lower()

    return check


def _exactly(expected: str) -> Callable[[str], bool]:
    return lambda text: _strip_thinking(text).strip().strip(".").strip() == expected


def _json_obj(text: str) -> dict | None:
    body = _strip_thinking(text)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", body, re.S)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start, end = body.find("{"), body.rfind("}")
        candidate = body[start : end + 1] if start != -1 and end > start else ""
    try:
        value = json.loads(candidate)
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def _contains_all(*words: str) -> Callable[[str], bool]:
    return lambda text: all(w.lower() in _strip_thinking(text).lower() for w in words)


_NO_RECORD = re.compile(
    r"\b(?:no (?:record|information|mention|data)|not (?:in|mentioned|recorded|stated)|"
    r"(?:do not|don't|doesn't|does not) (?:have|know|contain|mention|say)|"
    r"isn't (?:mentioned|recorded)|unknown|can(?:not|'t) (?:tell|determine|find))\b",
    re.I,
)


def _says_no_record(forbidden: tuple[str, ...] = ()) -> Callable[[str], bool]:
    def check(text: str) -> bool:
        body = _strip_thinking(text)
        return bool(_NO_RECORD.search(body)) and not any(f.lower() in body.lower() for f in forbidden)

    return check


def _label_is(expected: str) -> Callable[[str], bool]:
    labels = ("SUPPORTED", "CONTRADICTED", "INSUFFICIENT")

    def check(text: str) -> bool:
        found = [lab for lab in labels if lab in _strip_thinking(text).upper()]
        return found == [expected]

    return check


# ------------------------------------------------------------------ reasoning


def _two_sentences(text: str) -> bool:
    body = _strip_thinking(text)
    if re.search(r"^\s*[-*\d]", body, re.M):
        return False
    return len([s for s in re.split(r"(?<=[.!?])\s+", body.strip()) if s.strip()]) == 2


def _three_primes_over_50(text: str) -> bool:
    nums = [int(n) for n in re.findall(r"\d+", _strip_thinking(text))]
    if len(nums) != 3 or len(set(nums)) != 3:
        return False
    return all(n > 50 and all(n % d for d in range(2, int(n**0.5) + 1)) for n in nums)


def _caddis_json(text: str) -> bool:
    obj = _json_obj(text)
    return bool(obj) and isinstance(obj.get("name"), str) and obj.get("count") == 3


ONLY = " Answer with only the final answer."
REASONING = [
    Task("r1", "reasoning", "I start with 3 flies, tie 7 on Monday and 9 on Tuesday, then lose 5 on "
         "Wednesday. How many flies do I have?" + ONLY, _number_is(14)),
    Task("r2", "reasoning", "A GPU has 12 GiB. The display uses 0.7 GiB, model weights need 8.4 GiB "
         "and the context cache needs 1.6 GiB. How many GiB remain free?" + ONLY, _number_is(1.3)),
    Task("r3", "reasoning", "Alice is older than Bob. Bob is older than Carol. Who is the youngest? "
         "Answer with one word.", _word_is("Carol")),
    Task("r4", "reasoning", "What is 17 multiplied by 23?" + ONLY, _number_is(391)),
    Task("r5", "reasoning", "Today is Thursday. What day of the week is it 10 days from today? "
         "Answer with one word.", _word_is("Sunday")),
    Task("r6", "reasoning", "A 150-mile trip: I drive 45 mph for 2 hours, then 60 mph for the rest. "
         "How many minutes does the rest take?" + ONLY, _number_is(60)),
    Task("r7", "reasoning", "Reply with exactly the word ACK and nothing else.", _exactly("ACK")),
    Task("r8", "reasoning", "Write exactly two sentences about brook trout. No lists, no headings.",
         _two_sentences),
    Task("r9", "reasoning", "List three prime numbers greater than 50, separated by commas, and "
         "nothing else.", _three_primes_over_50),
    Task("r10", "reasoning", 'Return only a JSON object with a string key "name" and an integer key '
         '"count" describing 3 caddis flies.', _caddis_json),
]


# ------------------------------------------------------------------ routing

ROUTING_ACTIONS = {
    "weather_forecast": "weather or forecast questions",
    "continuity_recall": "questions about earlier conversations, decisions or where we left off",
    "remember": "the user asks ARIA to store a fact about them",
    "mission_create": "start a long-running background job",
    "coding_task": "write, fix or change code in a project",
    "web_search": "look up current information on the internet",
    "planner_add_task": "add an item to the to-do list",
    "image_generate": "create a picture",
    "chat": "anything else; general conversation and knowledge",
}
ROUTING_SYSTEM = (
    "You route requests for an assistant named ARIA. Choose exactly one action:\n"
    + "\n".join(f"- {name}: {desc}" for name, desc in ROUTING_ACTIONS.items())
    + '\nRespond with only JSON: {"action": "<name>"}'
)
ROUTING_CASES = [
    ("Will it rain at the river tomorrow morning?", "weather_forecast"),
    ("Where did we leave off on the fishing app?", "continuity_recall"),
    ("Remember that my waders are size 11.", "remember"),
    ("Run a background job that re-indexes all my documents overnight.", "mission_create"),
    ("Fix the off-by-one bug in scraper.py.", "coding_task"),
    ("What is the latest stable Linux kernel release right now?", "web_search"),
    ("Add 'buy 5X tippet' to my to-do list.", "planner_add_task"),
    ("Draw a picture of an Adams dry fly on a wooden table.", "image_generate"),
    ("Explain why trout rise to emerging mayflies.", "chat"),
    ("What did we decide about the storage engine last week?", "continuity_recall"),
]


def _routing_score(expected: str) -> Callable[[str], bool]:
    def check(text: str) -> bool:
        obj = _json_obj(text)
        return bool(obj) and obj.get("action") == expected

    return check


ROUTE_TOOL = [
    {
        "type": "function",
        "function": {
            "name": "route",
            "description": "Choose ARIA's action for the user's request.",
            "parameters": {
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": list(ROUTING_ACTIONS)},
                },
                "required": ["action"],
            },
        },
    }
]


def _tool_score(expected: str) -> Callable[[list[dict]], bool]:
    def check(calls: list[dict]) -> bool:
        return bool(calls) and calls[0].get("name") == "route" and (
            (calls[0].get("arguments") or {}).get("action") == expected
        )

    return check


ROUTING = [
    Task(f"j{i}", "routing", text, _routing_score(action), system=ROUTING_SYSTEM, max_tokens=64)
    for i, (text, action) in enumerate(ROUTING_CASES, 1)
]
TOOL_ROUTING = [
    Task(
        f"t{i}",
        "tool_routing",
        f"Route this request: {text}",
        lambda _t: False,
        system="Call the route tool for every request.",
        max_tokens=128,
        tools=ROUTE_TOOL,
        score_tool=_tool_score(action),
    )
    for i, (text, action) in enumerate(ROUTING_CASES, 1)
]


# ------------------------------------------------------------------ memory

MEMORY_CONTEXT = """Conversation history (HITS) — retrieved from ARIA's archived conversations.
Decisions the user made:
- Tue Oct 06 18:02 user: Let's go with SQLite for the fishing log app since it stays local.
Rejected or dropped options:
- Tue Oct 06 18:04 user: No, let's not build the web dashboard; keep it a desktop app.
Corrections (these override what they correct):
- Tue Oct 06 18:07 user: Actually, log catches by lake, not by river.
Unfinished work:
- Tue Oct 06 18:10 user: Next we need to design the catch entry form.
"""
def _lake_not_river(text: str) -> bool:
    """The correction (lake) must win; mentioning river only as the replaced value is fine."""
    body = _strip_thinking(text).lower()
    cleaned = re.sub(r"(?:not|instead of|rather than|no longer)\s+(?:by\s+)?(?:the\s+)?river", "", body)
    return "lake" in body and "river" not in cleaned


MEMORY_SYSTEM = (
    "Answer using only the conversation history provided. If the history does not "
    "contain the answer, say there is no record of it. Do not guess."
)
MEMORY = [
    Task("m1", "memory", f"{MEMORY_CONTEXT}\nWhich database did we choose for the fishing log app?",
         _contains_all("sqlite"), system=MEMORY_SYSTEM),
    Task("m2", "memory", f"{MEMORY_CONTEXT}\nAre we building a web dashboard? Answer yes or no, then why.",
         lambda t: _strip_thinking(t).lower().lstrip("*# ").startswith("no"), system=MEMORY_SYSTEM),
    Task("m3", "memory", f"{MEMORY_CONTEXT}\nDo we log catches by river or by lake?",
         _lake_not_river, system=MEMORY_SYSTEM),
    Task("m4", "memory", f"{MEMORY_CONTEXT}\nWhat is the next thing we still need to do?",
         _contains_all("entry form"), system=MEMORY_SYSTEM),
    Task("m5", "memory", f"{MEMORY_CONTEXT}\nWhat price did we decide to charge for the app?",
         _says_no_record(("$",)), system=MEMORY_SYSTEM),
    Task("m6", "memory", f"{MEMORY_CONTEXT}\nWhich programming language did we pick for the app?",
         _says_no_record(("python", "rust", "javascript", "kotlin", "swift")), system=MEMORY_SYSTEM),
]


# ------------------------------------------------------------------ evidence

EVIDENCE_SYSTEM = (
    "Judge the claim using only the snippets. Reply with exactly one label: SUPPORTED if "
    "the snippets directly state the claim, CONTRADICTED if they state the opposite, or "
    "INSUFFICIENT if they do not address it."
)


def _evidence(claim: str, snippets: list[str]) -> str:
    body = "\n".join(f"[{i}] {s}" for i, s in enumerate(snippets, 1))
    return f"Claim: {claim}\nSnippets:\n{body}\nLabel:"


EVIDENCE = [
    Task("e1", "evidence", _evidence("The moon is made of cheese.",
         ["Garden soil holds water.", "Loam drains better than clay."]),
         _label_is("INSUFFICIENT"), system=EVIDENCE_SYSTEM, max_tokens=32),
    Task("e2", "evidence", _evidence("Brook trout need cold water.",
         ["Brook trout require cold, clean, well-oxygenated water.",
          "Brook trout populations decline when streams warm above 20C."]),
         _label_is("SUPPORTED"), system=EVIDENCE_SYSTEM, max_tokens=32),
    Task("e3", "evidence", _evidence("Ubuntu LTS releases come out every year.",
         ["Ubuntu LTS releases are published every two years, in April."]),
         _label_is("CONTRADICTED"), system=EVIDENCE_SYSTEM, max_tokens=32),
    Task("e4", "evidence", _evidence("The RTX 3060 has 12 GB of VRAM.",
         ["The application server restarts cleanly.", "Use nvidia-smi to view processes."]),
         _label_is("INSUFFICIENT"), system=EVIDENCE_SYSTEM, max_tokens=32),
    Task("e5", "evidence", _evidence("Caddisflies build protective cases.",
         ["Many caddisfly larvae build portable cases from sand and plant material."]),
         _label_is("SUPPORTED"), system=EVIDENCE_SYSTEM, max_tokens=32),
    Task("e6", "evidence", _evidence("Python lists are immutable.",
         ["Lists in Python are mutable; tuples are immutable."]),
         _label_is("CONTRADICTED"), system=EVIDENCE_SYSTEM, max_tokens=32),
]


# ------------------------------------------------------------------ coding

CODING_SYSTEM = "Write Python. Reply with one ```python code block and nothing else."
CODING_SPECS = [
    ("c1", "Write `is_palindrome(s: str) -> bool` that ignores case and non-alphanumeric characters.",
     "assert is_palindrome('A man, a plan, a canal: Panama')\nassert not is_palindrome('trout')\n"
     "assert is_palindrome('')"),
    ("c2", "Write `to_minutes(hhmm: str) -> int` converting '07:45' style times to minutes after "
     "midnight. Raise ValueError for invalid input like '25:00' or '7:5x'.",
     "assert to_minutes('07:45') == 465\nassert to_minutes('00:00') == 0\n"
     "for bad in ('25:00', '7:5x', '12:60'):\n"
     "    try:\n        to_minutes(bad)\n        raise SystemExit(1)\n    except ValueError:\n        pass"),
    ("c3", "Write `merge(intervals: list[tuple[int, int]]) -> list[tuple[int, int]]` that merges "
     "overlapping or touching intervals and returns them sorted.",
     "assert merge([(5,7),(1,3),(2,4)]) == [(1,4),(5,7)]\nassert merge([(1,2),(2,3)]) == [(1,3)]\n"
     "assert merge([]) == []"),
    ("c4", "Write `top_words(text: str, k: int) -> list[str]` returning the k most frequent "
     "lowercase words (letters only), ties broken alphabetically.",
     "assert top_words('b a b c a b', 2) == ['b', 'a']\nassert top_words('x y', 5) == ['x', 'y']"),
    ("c5", "Write `flatten(items)` that flattens arbitrarily nested lists into one flat list.",
     "assert flatten([1,[2,[3,[4]]],5]) == [1,2,3,4,5]\nassert flatten([]) == []"),
    ("c6", "This function should return the average of a list but crashes on an empty list and "
     "uses integer division. Fix it so an empty list returns 0.0:\n\n```python\ndef average(xs):\n"
     "    return sum(xs) // len(xs)\n```",
     "assert average([1,2]) == 1.5\nassert average([]) == 0.0"),
]


def extract_code(text: str) -> str:
    body = _strip_thinking(text)
    blocks = re.findall(r"```(?:python|py)?\s*\n(.*?)```", body, re.S)
    return max(blocks, key=len) if blocks else body


def run_hidden_tests(code: str, tests: str, *, timeout: float = 10.0) -> bool:
    """Run model code + hidden asserts in a throwaway directory, isolated interpreter."""
    with tempfile.TemporaryDirectory(prefix="aria-bench-") as tmp:
        stub = Path(tmp) / "pytest_stub.py"
        stub.write_text("")
        script = Path(tmp) / "candidate.py"
        script.write_text(code + "\n\n" + tests + "\n")
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-S", str(script)],
                cwd=tmp,
                capture_output=True,
                timeout=timeout,
                env={"PATH": "/usr/bin:/bin", "PYTHONPATH": tmp},
            )
        except subprocess.TimeoutExpired:
            return False
        return proc.returncode == 0


def _coding_score(tests: str) -> Callable[[str], bool]:
    return lambda text: run_hidden_tests(extract_code(text), tests)


CODING = [
    Task(cid, "coding", prompt, _coding_score(tests), system=CODING_SYSTEM, max_tokens=700)
    for cid, prompt, tests in CODING_SPECS
]


# ------------------------------------------------------------------ vision


def make_vision_images(directory: Path) -> dict[str, str]:
    """Deterministic test images: colour, count and text."""
    from PIL import Image, ImageDraw, ImageFont

    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, str] = {}

    img = Image.new("RGB", (320, 240), "white")
    ImageDraw.Draw(img).ellipse((100, 60, 220, 180), fill=(220, 20, 20))
    paths["red_circle"] = str(directory / "red_circle.png")
    img.save(paths["red_circle"])

    img = Image.new("RGB", (360, 240), "white")
    draw = ImageDraw.Draw(img)
    for x in (30, 140, 250):
        draw.rectangle((x, 80, x + 80, 160), fill=(20, 60, 220))
    paths["three_squares"] = str(directory / "three_squares.png")
    img.save(paths["three_squares"])

    img = Image.new("RGB", (420, 160), "white")
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans-Bold.ttf", 56)
    except OSError:
        font = ImageFont.load_default()
    draw.text((30, 45), "TROUT 42", fill="black", font=font)
    paths["text"] = str(directory / "text.png")
    img.save(paths["text"])

    img = Image.new("RGB", (320, 240), "white")
    ImageDraw.Draw(img).polygon([(160, 40), (60, 200), (260, 200)], fill=(20, 170, 40))
    paths["green_triangle"] = str(directory / "green_triangle.png")
    img.save(paths["green_triangle"])
    return paths


VISION = [
    Task("v1", "vision", "What colour is the shape in this image? Answer with one word.",
         _word_is("red"), images=["red_circle"], max_tokens=32),
    Task("v2", "vision", "How many squares are in this image? Answer with only the number.",
         _number_is(3), images=["three_squares"], max_tokens=32),
    Task("v3", "vision", "What text is written in this image? Reply with the text only.",
         _contains_all("trout", "42"), images=["text"], max_tokens=32),
    Task("v4", "vision", "What shape is in this image? Answer with one word.",
         _word_is("triangle"), images=["green_triangle"], max_tokens=32),
]

SUITES: dict[str, list[Task]] = {
    "reasoning": REASONING,
    "routing": ROUTING,
    "tool_routing": TOOL_ROUTING,
    "memory": MEMORY,
    "evidence": EVIDENCE,
    "coding": CODING,
    "vision": VISION,
}


def summarise(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-model, per-category accuracy and latency from raw task results."""
    out: dict[str, Any] = {}
    for r in results:
        m = out.setdefault(r["model"], {"categories": {}})
        cat = m["categories"].setdefault(
            r["category"], {"passed": 0, "total": 0, "errors": 0, "wall_ms": []}
        )
        cat["total"] += 1
        cat["passed"] += 1 if r.get("passed") else 0
        cat["errors"] += 1 if r.get("error") else 0
        if r.get("wall_ms") is not None:
            cat["wall_ms"].append(r["wall_ms"])
    for m in out.values():
        for cat in m["categories"].values():
            walls = sorted(cat.pop("wall_ms"))
            cat["accuracy"] = round(cat["passed"] / cat["total"], 3) if cat["total"] else None
            cat["p50_ms"] = walls[len(walls) // 2] if walls else None
            cat["p95_ms"] = walls[min(len(walls) - 1, int(len(walls) * 0.95))] if walls else None
    return out
