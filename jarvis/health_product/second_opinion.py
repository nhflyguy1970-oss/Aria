"""Optional multi-model second opinion — never votes on a diagnosis."""

from __future__ import annotations

import json
import os
import re
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.consult import preview_consultation
from jarvis.health_product.terminology import DISCLAIMER

_BOUNDARY = (
    "Second opinions compare consultant wording only. They do not vote on a diagnosis, "
    "do not imply medical certainty, and do not replace a physician."
)

_TRUSTED_SOURCES = (
    "Prefer educational framing aligned with major public-health agencies, government health "
    "organizations, large academic medical centers, and established professional medical organizations "
    "(e.g. NIH, CDC, WHO, Mayo Clinic, Cleveland Clinic, AHA, ADA). "
    "Clearly separate: (1) user Health data, (2) AI interpretation, (3) educational information, "
    "(4) external references. Do not invent citations."
)


def configured_models() -> list[str]:
    raw = os.getenv("JARVIS_HEALTH_SECOND_OPINION_MODELS") or ""
    models = [m.strip() for m in raw.split(",") if m.strip()]
    if len(models) >= 2:
        return models[:4]
    local = os.getenv("JARVIS_HEALTH_LOCAL_MODEL") or ""
    cloud = os.getenv("JARVIS_HEALTH_CONSULT_MODEL") or os.getenv("JARVIS_CLOUD_MODEL") or ""
    out = []
    if local:
        out.append(local)
    if cloud and cloud not in out:
        out.append(cloud)
    return out[:4]


def preview_second_opinion(question: str, *, level: str = "sanitized") -> dict[str, Any]:
    models = configured_models()
    preview = preview_consultation(question or "Second opinion on my recent Health trends.", level=level, include_docs=level == "full")
    preview["intent"] = "second_opinion_preview"
    preview["second_opinion"] = True
    preview["models"] = models
    shared = preview.get("shared") or {}
    info_sent = {
        "privacy_level": shared.get("privacy_level") or level,
        "leaves_device": bool(preview.get("leaves_device")),
        "keys": sorted(shared.keys()) if isinstance(shared, dict) else [],
        "note": "Nothing leaves this computer until you explicitly approve send.",
    }
    preview["information_sent_preview"] = info_sent
    preview["trusted_sources_note"] = _TRUSTED_SOURCES
    extra = [
        "",
        "**Second opinion**",
        _BOUNDARY,
        f"Models that would be asked after approval: {', '.join(models) if models else 'none configured — set JARVIS_HEALTH_SECOND_OPINION_MODELS or local+cloud models.'}",
        "",
        "**Information that would be shared** (preview only)",
        f"• Privacy level: {info_sent['privacy_level']}",
        f"• Leaves device after approval: {'yes' if info_sent['leaves_device'] else 'no (local only)'}",
        f"• Payload sections: {', '.join(info_sent['keys']) or '—'}",
        "",
        "**Trusted sources preference**",
        _TRUSTED_SOURCES,
        "",
        "Reply **send consultation** to run, or **cancel consultation**.",
    ]
    preview["message"] = (preview.get("message") or "") + "\n".join(extra)
    rec = store.get_by_id("consultations", preview["consultation_id"])
    if rec:
        store.update_consultation(preview["consultation_id"], {"question": f"[second-opinion] {question}"})
    return preview


def run_second_opinion(consultation_id: str) -> dict[str, Any]:
    rec = store.get_by_id("consultations", consultation_id)
    if not rec:
        return {"ok": False, "message": "Second-opinion preview not found.", "disclaimer": DISCLAIMER}
    try:
        shared = json.loads(rec.get("shared_json") or "{}")
    except Exception:
        shared = {}
    question = re.sub(r"^\[second-opinion\]\s*", "", rec.get("question") or "")
    models = configured_models()
    if len(models) < 2:
        text = "A second opinion needs at least two configured models (JARVIS_HEALTH_SECOND_OPINION_MODELS). Nothing was compared."
        store.update_consultation(consultation_id, {"response": text, "approved": 1, "status": "complete"})
        return {"ok": True, "intent": "second_opinion", "message": text + "\n\n_" + DISCLAIMER + "_", "disclaimer": DISCLAIMER}
    from jarvis.inference.gateway import chat_with_usage

    system = (
        "You are an optional health-information consultant. You are NOT a physician. "
        "Do not diagnose. Do not prescribe. Do not tell the user to stop prescription medications. "
        "List observations, uncertainties, and questions for a clinician. Be explicit about what you cannot know. "
        + _TRUSTED_SOURCES
        + " Structure your reply with short sections labeled: User-data observations, AI interpretation, "
        "Educational information, External references (only if you truly know them), Questions for a physician."
    )
    answers = []
    for model in models:
        try:
            text, usage = chat_with_usage(
                model,
                [
                    {"role": "system", "content": system},
                    {"role": "user", "content": f"Second opinion request: {question}\n\nHealth excerpt:\n{json.dumps(shared)[:14000]}"},
                ],
                role="general",
            )
            answers.append({"model": usage.get("execution_model") or model, "provider": usage.get("execution_provider") or "unknown", "text": text})
        except Exception as exc:
            answers.append({"model": model, "provider": "error", "text": f"(unavailable: {exc})"})
    comparison = _compare(answers)
    combined = _format(question, answers, comparison, shared)
    store.update_consultation(
        consultation_id,
        {
            "response": combined,
            "approved": 1,
            "stored": 1,
            "status": "complete",
            "provider": "multi",
            "model": ",".join(a["model"] for a in answers),
        },
    )
    store.add_note("AI second opinion", combined[:4000])
    return {
        "ok": True,
        "intent": "second_opinion",
        "consultation_id": consultation_id,
        "answers": answers,
        "comparison": comparison,
        "information_sent": {
            "privacy_level": shared.get("privacy_level"),
            "keys": sorted(shared.keys()) if isinstance(shared, dict) else [],
        },
        "message": combined,
        "disclaimer": DISCLAIMER,
        "open_view": "health",
    }


def _compare(answers: list[dict[str, Any]]) -> dict[str, Any]:
    blobs = [re.findall(r"[a-z]{4,}", (a.get("text") or "").lower()) for a in answers]
    sets = [set(b) for b in blobs]
    if len(sets) < 2:
        return {
            "agreement": [],
            "disagreement": [],
            "uncertainty": ["Not enough model responses to compare."],
            "physician_questions": [],
            "confidence": "low",
            "confidence_note": "Fewer than two usable model responses.",
        }
    shared = set.intersection(*sets) if sets else set()
    stop = {
        "about", "these", "those", "their", "there", "would", "could", "should", "physician", "doctor",
        "health", "which", "with", "that", "this", "from", "have", "been", "your", "user", "data",
        "information", "educational", "section", "interpretation", "external", "references",
    }
    agreement = sorted(w for w in shared if w not in stop)[:12]
    disagreement = []
    # Unique emphases per model (words in one set but not the intersection)
    for i, s in enumerate(sets):
        uniq = sorted(w for w in (s - shared) if w not in stop and len(w) > 5)[:6]
        if uniq:
            disagreement.append({"model": answers[i].get("model"), "unique_terms": uniq})
    # Explicit contradiction cues across answers
    contradiction_lines = []
    for a in answers:
        for line in (a.get("text") or "").splitlines():
            if re.search(r"\b(disagree|however|unlike|in contrast|on the other hand|contradict)\b", line, re.I):
                contradiction_lines.append(f"{a.get('model')}: {line.strip()[:180]}")
    uncertainty = []
    for a in answers:
        for line in (a.get("text") or "").splitlines():
            if re.search(r"\b(uncertain|not sure|unclear|cannot|can't|unknown|possible|might|may be)\b", line, re.I):
                uncertainty.append(f"{a.get('model')}: {line.strip()[:180]}")
    questions = []
    for a in answers:
        for line in (a.get("text") or "").splitlines():
            if "?" in line:
                questions.append(line.strip()[:200])
    # Confidence is about agreement of wording — never medical certainty
    overlap_ratio = len(agreement) / max(1, min(len(s) for s in sets))
    if contradiction_lines or overlap_ratio < 0.05:
        confidence = "low"
        conf_note = "Models diverge or flag contrasts — read each response separately. Not medical certainty."
    elif overlap_ratio >= 0.15 and len(uncertainty) <= 2:
        confidence = "moderate"
        conf_note = "Some wording overlap across models. Still educational only — not a diagnosis."
    else:
        confidence = "limited"
        conf_note = "Partial overlap with notable uncertainty. Discuss with a physician."
    return {
        "agreement": agreement,
        "disagreement": disagreement,
        "contradiction_cues": contradiction_lines[:6],
        "uncertainty": uncertainty[:8] or ["Models did not clearly flag uncertainty — still treat all of this as non-diagnostic."],
        "physician_questions": list(dict.fromkeys(questions))[:8],
        "confidence": confidence,
        "confidence_note": conf_note,
    }


def _format(question: str, answers: list[dict[str, Any]], comparison: dict[str, Any], shared: dict[str, Any]) -> str:
    lines = [
        "**AI second opinion** (consultant comparison only)",
        "",
        _BOUNDARY,
        "",
        f"Question: {question}",
        "",
        "**Information sent** (after your explicit approval)",
        f"• Privacy level: {shared.get('privacy_level') or '—'}",
        f"• Sections: {', '.join(sorted(shared.keys())) if shared else '—'}",
        "",
        "**Comparison confidence** (wording agreement — not medical certainty)",
        f"• Level: {comparison.get('confidence')} — {comparison.get('confidence_note')}",
        "",
        "**Areas where models agree** (lexical overlap, not a diagnosis vote)",
    ]
    if comparison.get("agreement"):
        lines.append("• " + ", ".join(comparison["agreement"]))
    else:
        lines.append("• Little lexical overlap — read each response separately.")
    lines += ["", "**Areas where models disagree or emphasize differently**"]
    if comparison.get("contradiction_cues"):
        lines.extend(f"• {c}" for c in comparison["contradiction_cues"])
    for d in comparison.get("disagreement") or []:
        lines.append(f"• {d.get('model')}: unique terms — {', '.join(d.get('unique_terms') or [])}")
    if not comparison.get("contradiction_cues") and not comparison.get("disagreement"):
        lines.append("• No strong disagreement cues detected in wording.")
    lines += ["", "**Areas of uncertainty**"]
    lines.extend(f"• {u}" for u in comparison.get("uncertainty") or [])
    lines += ["", "**Questions worth discussing with a physician**"]
    qs = comparison.get("physician_questions") or []
    if qs:
        lines.extend(f"• {q}" for q in qs)
    else:
        lines.append("• Which of these observations, if any, should change follow-up or testing?")
    lines += ["", "**Trusted sources preference**", _TRUSTED_SOURCES]
    for a in answers:
        lines += ["", f"**{a.get('provider')} / {a.get('model')}**", a.get("text") or ""]
    lines += ["", "_" + DISCLAIMER + "_"]
    return "\n".join(lines)
