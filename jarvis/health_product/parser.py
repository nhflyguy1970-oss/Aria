"""Natural-language health updates — no forms required."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

_NUM = r"(\d+(?:\.\d+)?)"


def parse_health_utterance(message: str) -> dict[str, Any]:
    """Return structured mutations inferred from Jeff-speak."""
    text = (message or "").strip()
    lower = text.lower()
    out: dict[str, Any] = {
        "vitals": [],
        "checkin": {},
        "medications": [],
        "supplements": [],
        "symptoms": [],
        "labs": [],
        "conditions": [],
        "allergies": [],
        "notes": [],
        "missed_doses": [],
        "taken_doses": [],
        "recovery": [],
        "vaccinations": [],
        "doctor_questions": [],
        "activities": [],
        "workouts": [],
        "journal": [],
        "goals": [],
        "family_history": [],
        "preventive": [],
        "nutrition": [],
        "query": None,
        "level": None,
        "intent": None,
    }

    if re.search(r"^(yes|yep|yeah|confirm|please add(?: it)?|add it|do it|go ahead)\b", lower) and len(lower) < 80:
        out["intent"] = "confirm"
        return out
    if re.search(r"^(no|nope|cancel|don'?t|do not|never mind)\b", lower) and len(lower) < 80:
        out["intent"] = "reject"
        return out
    if m := re.search(r"\b(?:remind me to ask(?: my)? doctor(?: about)?|question for(?: my)? doctor[:\s]+)\s*(.+)$", lower):
        out["intent"] = "doctor_question"
        out["query"] = m.group(1).strip(" .")
        return out
    if re.search(r"\b(health timeline|show(?: me)?(?: my)? health (?:history|timeline)|timeline of my health|lifetime health)\b", lower):
        out["intent"] = "timeline"
        m = re.search(
            r"\b(meds|medications|labs?|vitals?|sleep|supplements?|symptoms?|documents?|visits?|doctors?|"
            r"consult|exercise|workouts?|journal|goals?|milestones?|recovery)\b",
            lower,
        )
        out["query"] = m.group(1) if m else ""
        return out
    if re.search(r"\b(wellness coach|lifestyle (ideas|suggestions|recommendations)|health coach)\b", lower):
        out["intent"] = "coach"
        return out
    if re.search(r"\b(second opinion|get a second opinion|multi-?model (consult|opinion))\b", lower):
        out["intent"] = "second_opinion"
        out["level"] = "full" if re.search(r"\b(full|complete)\b", lower) else "sanitized"
        out["query"] = text
        return out
    if re.search(
        r"\b("
        r"how(?:'?s| is) my health|"
        r"how have i been doing|"
        r"how am i doing(?: healthwise)?|"
        r"health dashboard|"
        r"what changed(?: this month)?|"
        r"have i improved|"
        r"what should i pay attention to"
        r")\b",
        lower,
    ):
        out["intent"] = "dashboard"
        return out
    if re.search(r"\b(wellness scorecard|health scorecard|habit scorecard)\b", lower):
        out["intent"] = "scorecard"
        return out
    if re.search(r"\b(health milestones?|show(?: me)?(?: my)? milestones?)\b", lower):
        out["intent"] = "milestones"
        return out
    if re.search(r"\b(medication adherence|adherence|did i (?:take|miss)(?: my)? (?:meds|medications)|meds? (?:taken|due) today)\b", lower):
        out["intent"] = "adherence"
        return out
    if re.search(r"\b(what runs in my family|family medical history|show(?: me)?(?: my)? family history)\b", lower):
        out["intent"] = "family_history"
        return out
    if m := re.search(r"\bdoes\s+(.+?)\s+run in my family\b", lower):
        out["intent"] = "family_history"
        out["query"] = m.group(1).strip(" .")
        return out
    if re.search(r"\bam i due for\b", lower):
        out["intent"] = "preventive"
        out["query"] = "due"
        return out
    if m := re.search(
        r"\bwhen was my last (colonoscopy|eye exam|mammogram|pap test|pap smear|psa|dental cleaning|physical exam|physical|hearing test|skin exam|bone density)\b",
        lower,
    ):
        out["intent"] = "preventive"
        out["query"] = m.group(1).strip()
        return out
    if re.search(r"\b(do you see any patterns|health patterns|why do i keep getting)\b", lower):
        out["intent"] = "insights"
        if "headache" in lower:
            out["query"] = "headache"
        return out
    if re.search(r"\b(prepare me for|prep for my appointment)\b", lower):
        out["intent"] = "visit_prep"
        return out
    if re.search(r"\b(nutrition habits|what did i eat|eating habits|food habits)\b", lower):
        out["intent"] = "nutrition"
        return out
    if re.search(r"\b(backup(?: my)? health|create health backup|encrypted health backup)\b", lower):
        out["intent"] = "backup"
        return out
    if re.search(r"\b(restore(?: my)? health|restore health backup)\b", lower):
        out["intent"] = "restore"
        return out
    if re.search(r"\b(backup integrity|verify backups?|health backup integrity)\b", lower):
        out["intent"] = "integrity"
        return out
    if re.search(r"\b(when was my last (?:doctor|physician) (?:visit|appointment)|last (?:doctor|physician) visit)\b", lower):
        out["intent"] = "last_visit"
        return out
    if re.search(r"\b(health trends?|am i improving|needs attention)\b", lower):
        out["intent"] = "trends"
        return out
    if re.search(r"\b(medication (safety|interactions?)|interact with my (meds|medications|supplements)|grapefruit)\b", lower):
        out["intent"] = "safety"
        return out
    if re.search(r"\b(have i exercised enough|activity (log|summary|history)|workout (history|summary|streak)|last workout|personal best)\b", lower):
        out["intent"] = "activity" if "exercis" in lower or "activity" in lower else "workouts"
        return out
    if re.search(r"\b(did i lose weight|how'?s my (weight|blood pressure|sleep|sugar)|how am i sleeping)\b", lower):
        out["intent"] = "graph"
        if "pressure" in lower:
            out["query"] = "blood_pressure"
        elif "sleep" in lower:
            out["query"] = "sleep"
        elif "sugar" in lower:
            out["query"] = "blood_sugar"
        else:
            out["query"] = "weight"
        return out
    if re.search(r"\bwhat should i ask my doctor\b", lower):
        out["intent"] = "doctor_visit"
        return out
    if re.search(r"\b(cancel consultation|don'?t send|do not send)\b", lower):
        out["intent"] = "consult_cancel"
        return out
    if re.search(r"\b(send consultation|confirm consultation|approve consultation)\b", lower):
        out["intent"] = "consult_send"
        return out
    if re.search(
        r"\b("
        r"consult(?: with)?(?: a)?(?: cloud)? ai|"
        r"review my (?:last )?(?:six months|6 months|labs?|lab trends|blood pressure|medications?)|"
        r"analyze my (?:lab|health|bp|blood pressure|medication)"
        r")\b",
        lower,
    ):
        out["intent"] = "consult"
        out["level"] = "full" if re.search(r"\b(full|complete|send (?:my )?(?:labs?|documents?|reports?))\b", lower) else "sanitized"
        out["query"] = text
        return out
    if re.search(r"\b(export(?: my)? health|download(?: my)? health record)\b", lower):
        out["intent"] = "export"
        return out
    if re.search(r"\b(health reminders?|medication reminders?)\b", lower):
        out["intent"] = "reminders"
        return out
    if re.search(r"\b(prepare for (my )?doctor|doctor (visit|appointment)|appointment summary)\b", lower):
        out["intent"] = "doctor_visit"
        return out
    if re.search(r"\b(emergency (summary|card|info)|wallet card)\b", lower):
        out["intent"] = "emergency"
        return out
    if re.search(r"\b(what (meds|medications) am i (on|taking)|what medications am i take|current medications?)\b", lower):
        out["intent"] = "medications"
        return out
    if re.search(r"\b(what supplements|supplements? (do i|am i))\b", lower):
        out["intent"] = "supplements"
        return out
    if re.search(r"\b(show|graph|how (is|has)|trend).{0,40}\b(weight|blood pressure|pressure|sugar|sleep|mood|pain|energy|heart rate|a1c|cholesterol)\b", lower) or re.search(
        r"\b(weight|blood pressure|sugar|sleep) (log|history|graph|trend)\b", lower
    ):
        out["intent"] = "graph"
        m = re.search(
            r"\b(weight|blood pressure|pressure|sugar|glucose|sleep|mood|pain|energy|stress|heart rate|pulse|a1c|cholesterol|hdl|ldl|triglycerides|vitamin d)\b",
            lower,
        )
        out["query"] = (m.group(1) if m else "weight").replace("pressure", "blood_pressure").replace("blood pressure", "blood_pressure")
        if out["query"] == "blood_pressure":
            pass
        elif "pressure" in (m.group(1) if m else ""):
            out["query"] = "blood_pressure"
        return out
    if re.search(r"\b(last|latest|recent).{0,20}\b(lab|cholesterol|a1c|psa|vitamin d|glucose)\b", lower) or re.search(
        r"\b(lab results?|cholesterol results?)\b", lower
    ):
        out["intent"] = "labs"
        return out
    if re.search(r"\b(daily health|health (today|check-?in)|how (am i|did i) (do|feel) today)\b", lower):
        out["intent"] = "today"
        return out
    if re.search(r"\b(search|find).{0,20}\b(health|medication|lab|allerg)\b", lower) or re.search(
        r"\bhealth search\b", lower
    ):
        out["intent"] = "search"
        out["query"] = text
        return out

    # Vitals / check-in captures
    if m := re.search(rf"\b(?:blood )?sugar(?: was| is|:)?\s*{_NUM}\b", lower):
        out["vitals"].append({"kind": "blood_sugar", "value": float(m.group(1)), "units": "mg/dL"})
        out["checkin"]["blood_sugar"] = float(m.group(1))
    if m := re.search(rf"\b(?:glucose(?: was| is|:)?)\s*{_NUM}\b", lower):
        out["vitals"].append({"kind": "blood_sugar", "value": float(m.group(1)), "units": "mg/dL"})
        out["checkin"]["blood_sugar"] = float(m.group(1))
    if m := re.search(rf"\b(?:blood )?pressure(?: was| is|:)?\s*{_NUM}\s*(?:/|over)\s*{_NUM}\b", lower):
        out["vitals"].append(
            {"kind": "blood_pressure", "value": float(m.group(1)), "value2": float(m.group(2)), "units": "mmHg"}
        )
        out["checkin"]["bp_systolic"] = float(m.group(1))
        out["checkin"]["bp_diastolic"] = float(m.group(2))
    if m := re.search(rf"\b(?:i )?(?:weighed|weight(?: was| is|:)?)\s*{_NUM}\b", lower):
        out["vitals"].append({"kind": "weight", "value": float(m.group(1)), "units": "lb"})
        out["checkin"]["weight"] = float(m.group(1))
    if m := re.search(rf"\bslept\s*{_NUM}\s*(?:hours?|hrs?)\b", lower):
        out["vitals"].append({"kind": "sleep_hours", "value": float(m.group(1)), "units": "hr"})
        out["checkin"]["sleep_hours"] = float(m.group(1))
    if m := re.search(rf"\b(?:heart rate|pulse)(?: was| is|:)?\s*{_NUM}\b", lower):
        out["vitals"].append({"kind": "heart_rate", "value": float(m.group(1)), "units": "bpm"})
        out["checkin"]["heart_rate"] = float(m.group(1))
    if m := re.search(rf"\b(?:temp(?:erature)?)(?: was| is|:)?\s*{_NUM}\b", lower):
        out["vitals"].append({"kind": "temperature", "value": float(m.group(1)), "units": "F"})
        out["checkin"]["temperature"] = float(m.group(1))
    if m := re.search(rf"\b(?:o2|oxygen|pulse ox(?:imeter)?)(?: was| is|:)?\s*{_NUM}\b", lower):
        out["vitals"].append({"kind": "spo2", "value": float(m.group(1)), "units": "%"})
        out["checkin"]["spo2"] = float(m.group(1))
    if m := re.search(rf"\b(?:overall(?: health)?|feeling)\s*(?:is|was|:)?\s*{_NUM}\b", lower):
        out["checkin"]["overall"] = float(m.group(1))
    if m := re.search(rf"\benergy\s*(?:is|was|:)?\s*{_NUM}\b", lower):
        out["checkin"]["energy"] = float(m.group(1))
        out["vitals"].append({"kind": "energy", "value": float(m.group(1))})
    if m := re.search(rf"\bmood\s*(?:is|was|:)?\s*{_NUM}\b", lower):
        out["checkin"]["mood"] = float(m.group(1))
        out["vitals"].append({"kind": "mood", "value": float(m.group(1))})
    if m := re.search(rf"\bstress\s*(?:is|was|:)?\s*{_NUM}\b", lower):
        out["checkin"]["stress"] = float(m.group(1))
        out["vitals"].append({"kind": "stress", "value": float(m.group(1))})
    if m := re.search(rf"\bpain\s*(?:is|was|:)?\s*{_NUM}\b", lower):
        out["checkin"]["pain"] = float(m.group(1))
        out["vitals"].append({"kind": "pain", "value": float(m.group(1))})

    if m := re.search(rf"\b(?:a1c|hba1c)\s*(?:was|is|:)?\s*{_NUM}\b", lower):
        out["labs"].append({"name": "A1C", "value": float(m.group(1)), "units": "%"})
    if m := re.search(rf"\bcholesterol\s*(?:was|is|:)?\s*{_NUM}\b", lower):
        out["labs"].append({"name": "Cholesterol", "value": float(m.group(1)), "units": "mg/dL"})
    if m := re.search(rf"\bhdl\s*(?:was|is|:)?\s*{_NUM}\b", lower):
        out["labs"].append({"name": "HDL", "value": float(m.group(1)), "units": "mg/dL"})
    if m := re.search(rf"\bldl\s*(?:was|is|:)?\s*{_NUM}\b", lower):
        out["labs"].append({"name": "LDL", "value": float(m.group(1)), "units": "mg/dL"})
    if m := re.search(rf"\btriglycerides?\s*(?:was|is|:)?\s*{_NUM}\b", lower):
        out["labs"].append({"name": "Triglycerides", "value": float(m.group(1)), "units": "mg/dL"})
    if m := re.search(rf"\bvitamin d\s*(?:was|is|:)?\s*{_NUM}\b", lower):
        out["labs"].append({"name": "Vitamin D", "value": float(m.group(1)), "units": "ng/mL"})

    # Meds / supplements lifecycle
    if m := re.search(
        r"\b(?:i )?(?:started|start)(?: taking)?\s+(.+?)(?:\s+for\s+(.+))?(?:[.!?]|$)",
        lower,
    ):
        name = m.group(1).strip(" .")
        purpose = (m.group(2) or "").strip(" .")
        if _looks_like_supplement(name):
            out["supplements"].append({"name": name.title(), "status": "current", "purpose": purpose, "action": "start"})
        elif not _is_noise_start(name):
            out["medications"].append({"name": _clean_med_name(name), "status": "current", "purpose": purpose, "action": "start"})
    if m := re.search(r"\b(?:i )?(?:stopped|stop(?:ped)?|discontinued)(?: taking)?\s+(.+?)(?:[.!?]|$)", lower):
        name = m.group(1).strip(" .")
        if _looks_like_supplement(name):
            out["supplements"].append({"name": name.title(), "status": "stopped", "action": "stop"})
        else:
            out["medications"].append({"name": _clean_med_name(name), "status": "stopped", "action": "stop"})
    if m := re.search(
        r"\b(?:doctor|physician).{0,40}\b(increased|decreased|raised|lowered|changed)\s+(?:my\s+)?(.+?)(?:[.!?]|$)",
        lower,
    ):
        out["medications"].append(
            {
                "name": _clean_med_name(m.group(2)),
                "status": "current",
                "action": "change",
                "notes": text,
            }
        )
    if m := re.search(r"\b(?:paused|on hold with)\s+(.+?)(?:[.!?]|$)", lower):
        out["medications"].append({"name": _clean_med_name(m.group(1)), "status": "paused", "action": "pause"})

    from jarvis.health_product.nutrition import looks_like_food, parse_nutrition_utterance

    _food_guard = looks_like_food(text)
    _nutrition_entries = parse_nutrition_utterance(text)
    if _nutrition_entries:
        out["nutrition"] = _nutrition_entries
        out["intent"] = out["intent"] or "log"

    _REL = r"(?:father|mother|sister|brother|grandmother|grandfather|grandma|grandpa|aunt|uncle|cousin|son|daughter|sibling)"
    if m := re.search(rf"\bmy\s+({_REL})\s+(?:had|has)\s+(.+?)(?:[.!?]|$)", lower):
        rel = m.group(1).replace("grandma", "grandmother").replace("grandpa", "grandfather")
        out["family_history"].append({"relation": rel, "condition": m.group(2).strip(" .")})
        out["intent"] = out["intent"] or "log"
    if m := re.search(r"\b(.+?)\s+runs in my family\b", lower):
        out["family_history"].append({"relation": "other", "condition": m.group(1).strip(" .")})
        out["intent"] = out["intent"] or "log"
    _PREV = r"(colonoscopy|eye exam|mammogram|pap test|pap smear|psa|dental cleaning|dental|physical exam|physical|hearing test|skin exam|bone density)"
    if m := re.search(rf"\b(?:i )?had\s+(?:a|an|my)?\s*({_PREV})\b", lower):
        slug = m.group(1).strip()
        slug_map = {
            "pap smear": "pap",
            "dental": "dental",
            "physical": "physical",
            "physical exam": "physical",
        }
        out["preventive"].append(
            {
                "slug": slug_map.get(slug, slug.replace(" ", "_")),
                "name": slug.title(),
                "last_done": date.today().isoformat(),
                "action": "complete",
            }
        )
        out["intent"] = out["intent"] or "log"

    if not _food_guard:
        if m := re.search(r"\bmissed(?: my)?\s+(.+?)(?:\s+dose)?(?:[.!?]|$)", lower):
            name = m.group(1).strip(" .")
            kind = "supplement" if _looks_like_supplement(name) else "medication"
            out["missed_doses"].append({"name": _clean_med_name(name), "kind": kind, "notes": text})
        if m := re.search(r"\b(?:took|taken|i took)(?: my)?\s+(.+?)(?:\s+dose)?(?:[.!?]|$)", lower):
            name = m.group(1).strip(" .")
            if not re.search(r"\b(walk|shower|nap|photo|break)\b", name):
                kind = "supplement" if _looks_like_supplement(name) else "medication"
                out["taken_doses"].append({"name": _clean_med_name(name), "kind": kind, "notes": text})
    if m := re.search(
        r"\b(?:recovering from|recovery from|physical therapy for|pt for|injury(?: to)?|surgery(?: for)?|illness)\s+(.+?)(?:[.!?]|$)",
        lower,
    ):
        kind = "recovery"
        if "surgery" in lower:
            kind = "surgery"
        elif "injury" in lower:
            kind = "injury"
        elif "illness" in lower:
            kind = "illness"
        elif "physical therapy" in lower or "pt for" in lower:
            kind = "physical_therapy"
        out["recovery"].append({"title": m.group(1).strip(" .")[:120], "kind": kind, "notes": text})
        out["intent"] = out["intent"] or "log"

    # Symptoms
    if m := re.search(r"\bmy\s+(.+?)\s+(?:has )?hurt(?:ing)?(?:\s+for\s+(.+?))?(?:[.!?]|$)", lower):
        out["symptoms"].append({"name": m.group(1).strip(), "duration": (m.group(2) or "").strip(), "notes": text})
    if m := re.search(r"\b(?:i (?:have|had|ve got)|experiencing)\s+(.+?)(?:[.!?]|$)", lower) and re.search(
        r"\b(pain|ache|hurt|nausea|dizzy|headache|cough|fever|swelling)\b", lower
    ):
        out["symptoms"].append({"name": m.group(1).strip(), "notes": text})

    if m := re.search(
        rf"\b(?:i )?(?:walked|ran|cycled|biked|swam|hiked|stretched|fished)\b(?: for)?\s*{_NUM}\s*(?:min|minutes|hours|hrs)?",
        lower,
    ):
        kind_map = {"walked": "walking", "ran": "running", "cycled": "cycling", "biked": "cycling", "swam": "swimming", "hiked": "hiking", "stretched": "stretching", "fished": "fishing"}
        verb = re.search(r"\b(walked|ran|cycled|biked|swam|hiked|stretched|fished)\b", lower)
        kind = kind_map.get(verb.group(1) if verb else "walked", "walking")
        mins = float(m.group(1))
        if re.search(r"\b(hour|hrs)\b", lower) and mins <= 12:
            mins *= 60
        out["activities"].append({"kind": kind, "duration_min": mins, "title": kind.replace("_", " ").title(), "notes": text})
    if m := re.search(r"\b(?:i )?(?:did|finished|completed)\s+(?:an?\s+)?(upper body|lower body|full body|push|pull|legs|core|resistance band|cardio|mobility|rehab(?:ilitation)?)\s+workout\b", lower):
        tmpl = m.group(1).replace(" ", "_").replace("rehabilitation", "rehabilitation").replace("rehab", "rehabilitation")
        out["workouts"].append({"title": m.group(1).title() + " workout", "template": tmpl, "notes": text})
    if re.search(r"\b(i felt|i had a headache|i slept terribly|i felt fantastic|i felt dizzy|my knee hurt)\b", lower):
        out["journal"].append({"body": text})
        if re.search(r"\b(dizzy|headache|hurt|terrible)\b", lower) and not out["symptoms"]:
            out["symptoms"].append({"name": text[:80], "notes": text})
    if m := re.search(r"\b(?:set|add)(?: a)? goal(?: to)?\s+(.+)$", lower):
        out["goals"].append({"title": m.group(1).strip(" ."), "kind": "custom"})
        out["intent"] = out["intent"] or "goal_add"

    if (
        out["vitals"]
        or out["checkin"]
        or out["medications"]
        or out["supplements"]
        or out["symptoms"]
        or out["labs"]
        or out["activities"]
        or out["workouts"]
        or out["journal"]
        or out["goals"]
        or out["taken_doses"]
        or out["missed_doses"]
        or out["recovery"]
        or out["family_history"]
        or out["preventive"]
        or out["nutrition"]
    ):
        out["intent"] = out["intent"] or "log"
    elif re.search(r"\b(health|medication|blood pressure|sugar|supplement|allerg)\b", lower):
        out["intent"] = out["intent"] or "search"
        out["query"] = text
    return out


def _looks_like_supplement(name: str) -> bool:
    n = name.lower()
    return bool(
        re.search(
            r"\b(vitamin|magne|fish oil|omega|creatine|protein|multivitamin|coq10|co-q10|zinc|iron|biotin|probiotic|melatonin|turmeric|collagen)\b",
            n,
        )
    )


def _is_noise_start(name: str) -> bool:
    n = (name or "").strip().lower()
    return len(n) > 80 or "http" in n or n in {"taking", "my"}


def _clean_med_name(name: str) -> str:
    name = re.sub(r"^(taking|my)\s+", "", name.strip(), flags=re.I)
    name = re.sub(r"\s+(today|this morning|again)$", "", name, flags=re.I)
    return name.strip(" .").title()
