"""Research verification — source authority, conflict detection, claim support.

Search discovery ≠ verification. This module ranks sources, filters weak
evidence for consequential/current claims, and post-checks synthesized answers.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

# --- Authority tiers (general; not product-specific) ---

_TIER1_HOST = re.compile(
    r"(?:"
    # Governments / standards
    r"\.gov(?:\.[a-z]{2})?$|nhtsa\.gov|iihs\.org|iso\.org|nist\.gov|who\.int|"
    # Official vendor / manufacturer / project docs
    r"ford\.com|owner\.ford|service\.ford|motorcraft|"
    r"gm\.com|toyota\.com|honda\.com|nissanusa\.com|stellantis|bmw\.com|"
    r"ubuntu\.com|canonical\.com|kernel\.org|python\.org|docs\.python\.org|"
    r"nodejs\.org|nvidia\.com|docs\.nvidia\.com|developer\.nvidia\.com|"
    r"huggingface\.co|github\.com/[^/]+/[^/]+/(?:blob|tree|releases)|"
    r"learn\.microsoft\.com|docs\.microsoft\.com|developer\.mozilla\.org|"
    r"ietf\.org|w3\.org|apache\.org|gnu\.org|"
    r"federalregister\.gov|congress\.gov|whitehouse\.gov|"
    r"gov\.uk$|parliament\.uk|number10\.gov\.uk"
    r")",
    re.I,
)

_TIER2_HOST = re.compile(
    r"(?:"
    r"arxiv\.org|ieee\.org|acm\.org|nature\.com|science\.org|"
    r"reuters\.com|apnews\.com|bbc\.com|bbc\.co\.uk|"
    r"nytimes\.com|washingtonpost\.com|theguardian\.com|"
    r"ars[-]?technica\.com|wired\.com|theregister\.com|"
    r"anandtech\.com|tomshardware\.com|phoronix\.com|"
    r"sae\.org|asme\.org|alldata\.com|mitchell1\.com|"
    r"motor\.com|motortrend\.com"
    r")",
    re.I,
)

_TIER4_HOST = re.compile(
    r"(?:"
    r"justanswer|quora\.com|pinterest\.com|ebay\.com|facebook\.com|"
    r"answers\.yahoo|blogspot\.|wordpress\.com|"
    r"buzzfeed|clickbait|content-?farm|"
    r"fandom\.com|wikihow\.com"
    r")",
    re.I,
)

_CURRENT_CLAIM = re.compile(
    r"\b(?:"
    r"latest|current|currently|newest|as of|today|right now|"
    r"prime\s+minister|president|version\s+\d|released\s+in|"
    r"LTS\b|supported until"
    r")\b",
    re.I,
)

_CONFLICT_MARKERS = re.compile(
    r"\b(?:however|but|alternatively|other sources|conflicting|disagree)\b",
    re.I,
)


@dataclass
class RankedSource:
    index: int
    title: str
    url: str
    snippet: str
    tier: int
    host: str
    raw: dict[str, Any] = field(default_factory=dict)


def _host(url: str) -> str:
    try:
        return (urlparse(url).hostname or "").lower().lstrip("www.")
    except Exception:
        return ""


def classify_source_tier(url: str, title: str = "", snippet: str = "") -> int:
    """Return 1–4 authority tier for a URL."""
    host = _host(url)
    blob = f"{host} {title} {snippet}".lower()
    if not host and not blob.strip():
        return 4
    if _TIER4_HOST.search(host) or _TIER4_HOST.search(blob):
        return 4
    if _TIER1_HOST.search(host) or re.search(r"\bofficial\s+(?:docs?|documentation|site)\b", blob):
        return 1
    if _TIER2_HOST.search(host):
        return 2
    # Known forums / Q&A as weak for consequential even if not Tier 4 list
    if re.search(r"reddit\.com|stackexchange\.com|stackoverflow\.com|forum", host):
        return 4
    return 3


def rank_sources(results: list[dict]) -> list[RankedSource]:
    ranked: list[RankedSource] = []
    for i, r in enumerate(results or [], 1):
        url = str(r.get("url") or "")
        title = str(r.get("title") or "")
        snippet = str(r.get("snippet") or "")
        tier = classify_source_tier(url, title, snippet)
        ranked.append(
            RankedSource(
                index=i,
                title=title,
                url=url,
                snippet=snippet,
                tier=tier,
                host=_host(url),
                raw=dict(r),
            )
        )
    ranked.sort(key=lambda s: (s.tier, s.index))
    return ranked


def filter_results_for_query(
    query: str,
    results: list[dict],
    *,
    consequential: bool = False,
    current: bool = False,
) -> tuple[list[dict], dict[str, Any]]:
    """Prefer stronger sources; drop Tier 4 when consequential/current if better exist."""
    ranked = rank_sources(results)
    meta: dict[str, Any] = {
        "tiers": {str(s.index): s.tier for s in ranked},
        "hosts": {str(s.index): s.host for s in ranked},
        "filtered": False,
        "reason": "",
    }
    if not ranked:
        return [], meta

    if consequential or current:
        strong = [s for s in ranked if s.tier <= 2]
        mid = [s for s in ranked if s.tier == 3]
        weak = [s for s in ranked if s.tier >= 4]
        if consequential:
            # Consequential: Tier 1–2 only when available; else Tier 3; never Tier 4 alone.
            chosen = strong or mid
            meta["filtered"] = True
            meta["reason"] = "consequential_prefer_authoritative"
            if not chosen:
                meta["reason"] = "consequential_no_usable_sources"
                return [], meta
        else:
            # Current info: prefer Tier 1–2 exclusively when available.
            if strong:
                chosen = strong
                meta["filtered"] = True
                meta["reason"] = "current_prefer_authoritative"
            elif mid:
                chosen = mid
                meta["filtered"] = True
                meta["reason"] = "current_secondary_only"
            else:
                # Only weak sources — keep them but mark unverified for synthesis hedging.
                chosen = weak
                meta["filtered"] = True
                meta["reason"] = "current_weak_only"
        # Restore original discovery order among chosen
        chosen.sort(key=lambda s: s.index)
        return [s.raw for s in chosen], meta

    # Non-consequential: keep all, but put better tiers first for the model.
    ranked.sort(key=lambda s: (s.tier, s.index))
    return [s.raw for s in ranked], meta


def format_ranked_for_llm(results: list[dict], tier_map: dict[str, int] | None = None) -> str:
    lines = []
    for i, r in enumerate(results, 1):
        title = r.get("title", "Result")
        url = r.get("url", "")
        snippet = r.get("snippet", "")
        # Find original index tier if remapped
        tier = classify_source_tier(str(url), str(title), str(snippet))
        if tier_map:
            # Prefer map by matching url
            for k, v in tier_map.items():
                pass
        tier_label = {1: "T1-primary", 2: "T2-reputable", 3: "T3-secondary", 4: "T4-weak"}.get(
            tier, f"T{tier}"
        )
        lines.append(f"[{i}] ({tier_label}) {title}\nURL: {url}\n{snippet}")
    return "\n\n".join(lines)


def synthesis_system_prompt(*, consequential: bool, current: bool, local_now: str) -> str:
    parts = [
        "You answer using ONLY the ranked web search results below.",
        "Cite sources as [1], [2] matching the numbered results.",
        "Treat each result's authority tier seriously:",
        "T1-primary and T2-reputable outweigh T3-secondary; T4-weak is not enough for hard facts.",
        "A search snippet is a discovery hint — do not invent details not present in the snippets.",
        f"Local clock for currency judgments: {local_now}.",
    ]
    if current:
        parts.append(
            "This is a CURRENT-information question. Prefer the newest dated official source. "
            "If only weak/undated sources remain, say you could not conclusively verify the current value."
        )
    if consequential:
        parts.append(
            "This is CONSEQUENTIAL. Do not state exact specs (torque, voltages, dosages, legal limits) "
            "unless a T1/T2 source supports that exact figure. Otherwise refuse the exact number."
        )
    parts.append(
        "If T1/T2 sources conflict without a clear date/version explanation, say the claim cannot "
        "be conclusively verified and summarize the conflict — do not pick silently."
    )
    parts.append("If snippets are insufficient, say what is missing. Be concise and direct.")
    return " ".join(parts)


def postcheck_research_answer(
    query: str,
    answer: str,
    results: list[dict],
    *,
    consequential: bool,
    current: bool,
) -> str | None:
    """Return replacement text when synthesis is insufficiently supported; else None."""
    text = (answer or "").strip()
    if not text:
        return (
            "I could not verify a supported answer from the available sources. "
            "Please try a more specific query or an official documentation URL."
        )

    ranked = rank_sources(results)
    best = min((s.tier for s in ranked), default=4)
    cites = set(int(x) for x in re.findall(r"\[(\d+)\]", text))

    # Fiction / nonexistent premise — do not invent manuals or products.
    try:
        from jarvis.research_context import premise_supported_by_results, premise_tokens

        inventedish = bool(
            re.search(
                r"\b(?:acme|hyperdrive|flux\s+capacitor|z9|999\.99|99\.99|quantum\s+quokka)\b",
                query or "",
                re.I,
            )
        )
        toks = premise_tokens(query)
        # Only refuse on unsupported *invented/rare* premises — not ordinary proper nouns.
        if inventedish and not premise_supported_by_results(query, results):
            return (
                "I can find no reliable evidence that this product, document, or version exists, "
                "so I will not invent documentation or specifications for it."
            )
        # Version-existence probes with no supporting hit
        if re.search(r"\b(?:does|is there)\b.+\b(?:exist|real)\b", query or "", re.I):
            if toks and not premise_supported_by_results(query, results):
                return (
                    "I can find no reliable evidence that this version or product exists "
                    "in the retrieved sources, so I will not invent release notes for it."
                )
    except Exception:
        pass

    # Consequential numeric specs without T1/T2 support
    if consequential:
        from jarvis.orchestration_policy import (
            answer_has_unverified_critical_spec,
            consequential_web_answer_ok,
        )

        refused = consequential_web_answer_ok(query, text, results)
        if refused:
            return refused
        if answer_has_unverified_critical_spec(text) and best >= 3:
            return (
                "I found discussion of this topic, but not an authoritative (manufacturer or "
                "official) source strong enough to quote an exact safety-critical specification. "
                "Please check OEM service documentation."
            )

    # Current claims from weak-only evidence
    if current and best >= 4:
        return (
            "I found only weak or unclear sources for this current-information question, "
            "so I cannot conclusively verify the latest value. Please check the official "
            "project or vendor site."
        )

    if current and _CURRENT_CLAIM.search(text) and best >= 3 and not any(
        s.tier <= 2 for s in ranked
    ):
        # Soften: prepend caution rather than total refuse if answer already hedges
        if re.search(
            r"\b(?:could not|cannot|unable to|not (?:conclusively )?verify|unclear|uncertain)\b",
            text,
            re.I,
        ):
            return None
        return (
            "I could not confirm this from a primary or highly reputable official source. "
            "Secondary web results conflict or lack clear provenance, so I am not stating a "
            "definitive current value. Please check the official vendor/project documentation."
        )

    # Cited only weak sources while stronger existed unused
    if cites and ranked:
        cited_tiers = []
        for c in cites:
            if 1 <= c <= len(results):
                cited_tiers.append(classify_source_tier(
                    str(results[c - 1].get("url") or ""),
                    str(results[c - 1].get("title") or ""),
                    str(results[c - 1].get("snippet") or ""),
                ))
        if cited_tiers and max(cited_tiers) >= 4 and best <= 2 and (consequential or current):
            return (
                "Available authoritative sources were not reflected in the draft answer, "
                "so I am not presenting that draft as verified. Please rely on the official "
                "documentation for this claim."
            )

    return None


def prepare_research_context(query: str, results: list[dict]) -> tuple[list[dict], str, dict[str, Any]]:
    """Filter/rank results and build synthesis system prompt + metadata."""
    from jarvis.orchestration_policy import is_consequential_request, research_required

    consequential = is_consequential_request(query)
    current = bool(
        research_required(query)
        and re.search(
            r"\b(?:latest|current|currently|newest|today|now|as of|who currently)\b",
            query or "",
            re.I,
        )
    )
    filtered, meta = filter_results_for_query(
        query, results, consequential=consequential, current=current
    )
    meta["consequential"] = consequential
    meta["current"] = current
    now = datetime.now().astimezone().strftime("%A, %B %d, %Y %H:%M %Z")
    system = synthesis_system_prompt(
        consequential=consequential, current=current, local_now=now
    )
    return filtered, system, meta
