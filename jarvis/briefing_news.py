"""Headlines for morning briefing — Google News RSS + web search fallback."""

from __future__ import annotations

import logging
import os
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Any

log = logging.getLogger("jarvis")

_USER_AGENT = "Mozilla/5.0 (compatible; Jarvis/3.2; +local morning briefing)"
_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_CACHE_TTL_SEC = 15 * 60

_MATCH_STOPWORDS = frozenset(
    {
        "about",
        "briefing",
        "detail",
        "details",
        "expand",
        "explain",
        "from",
        "headline",
        "more",
        "morning",
        "news",
        "story",
        "that",
        "this",
        "tell",
        "what",
        "with",
        "your",
    }
)

_JUNK_HEADLINE_RE = re.compile(
    r"|".join(
        (
            r"\bwikipedia\b",
            r"\bfacebook\b",
            r"\bhome page\s*\|",
            r"\| wikipedia\b",
            r"^\s*news\s*-\s*",
            r"\boutdoors\s*$",
            r"\blogin\b",
            r"\bpinterest\b",
        )
    ),
    re.I,
)

_TITLE_DATE_RE = re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b")

# Connecticut River corridor Charlestown → Lebanon (~10 mi), both NH and VT banks.
_DEFAULT_CORRIDOR_TOWNS = (
    "Walpole NH",
    "North Walpole NH",
    "Alstead NH",
    "Langdon NH",
    "Acworth NH",
    "Unity NH",
    "Claremont NH",
    "Cornish NH",
    "Plainfield NH",
    "Lebanon NH",
    "Hanover NH",
    "Newport NH",
    "Bellows Falls VT",
    "Springfield VT",
    "Ascutney VT",
    "Weathersfield VT",
    "Windsor VT",
    "Hartland VT",
    "Hartford VT",
    "Norwich VT",
    "Thetford VT",
    "Fairlee VT",
)
_DEFAULT_REGIONAL_LABEL = "Connecticut River Valley (Charlestown–Lebanon, NH & VT)"


def news_enabled() -> bool:
    return os.getenv("JARVIS_BRIEFING_NEWS", "1") != "0"


def news_available() -> bool:
    from jarvis.profiles import web_search_disabled

    return news_enabled() and not web_search_disabled()


def _national_limit() -> int:
    try:
        return max(1, min(8, int(os.getenv("JARVIS_NEWS_NATIONAL_LIMIT", "5"))))
    except ValueError:
        return 5


def _local_limit() -> int:
    try:
        return max(1, min(6, int(os.getenv("JARVIS_NEWS_LOCAL_LIMIT", "4"))))
    except ValueError:
        return 4


def _local_max_age_days() -> int:
    try:
        return max(1, min(7, int(os.getenv("JARVIS_NEWS_LOCAL_MAX_DAYS", "3"))))
    except ValueError:
        return 3


def profile_location(memory_store) -> str | None:
    if memory_store is None:
        return None
    for entry in memory_store.list_entries(namespace="profile"):
        content = (entry.get("content") or "").strip()
        m = re.match(r"User is based in (.+?)\.?$", content, re.I)
        if m:
            place = m.group(1).strip()
            return place or None
    return None


def _resolve_primary_place(*, memory_store=None, weather: dict | None = None) -> str:
    """Primary town for local news (Charlestown by default in this corridor)."""
    for key in ("JARVIS_NEWS_LOCAL_PRIMARY", "JARVIS_NEWS_LOCAL"):
        override = os.getenv(key, "").strip()
        if override:
            return override

    if weather and weather.get("location"):
        return str(weather["location"]).strip()

    profile_loc = profile_location(memory_store)
    if profile_loc:
        return profile_loc

    weather_loc = os.getenv("JARVIS_WEATHER_LOCATION", "").strip()
    if weather_loc:
        return weather_loc

    weather_city = os.getenv("JARVIS_WEATHER_CITY", "").strip()
    if weather_city:
        return weather_city

    try:
        from jarvis.journal_weather import _resolve_location

        loc = _resolve_location()
        if loc:
            return loc[2]
    except Exception:
        pass

    return "Charlestown, NH"


def resolve_local_news_scope(
    *,
    memory_store=None,
    weather: dict | None = None,
) -> dict[str, Any]:
    """Primary town + Connecticut River corridor towns for regional coverage."""
    primary = _resolve_primary_place(memory_store=memory_store, weather=weather)

    regional_towns_str = os.getenv("JARVIS_NEWS_REGIONAL_TOWNS", "").strip()
    if regional_towns_str:
        towns = [t.strip() for t in regional_towns_str.split("|") if t.strip()]
    else:
        primary_short = primary.split(",")[0].strip().lower()
        towns = [
            town
            for town in _DEFAULT_CORRIDOR_TOWNS
            if primary_short not in town.lower()
        ]

    label = os.getenv("JARVIS_NEWS_REGIONAL_LABEL", _DEFAULT_REGIONAL_LABEL).strip()
    if not label:
        label = _DEFAULT_REGIONAL_LABEL

    return {"primary": primary, "towns": towns, "label": label}


def resolve_local_place(*, memory_store=None, weather: dict | None = None) -> str | None:
    """Best-effort local news area from env, profile, or weather."""
    scope = resolve_local_news_scope(memory_store=memory_store, weather=weather)
    return scope.get("primary")


def _fetch_bytes(url: str, *, timeout: float = 10) -> bytes | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as exc:
        log.debug("News fetch failed for %s: %s", url, exc)
        return None


def _parse_rss_pub_date(text: str) -> datetime | None:
    if not text or not text.strip():
        return None
    try:
        dt = parsedate_to_datetime(text.strip())
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (TypeError, ValueError, OverflowError):
        return None


def _is_recent(published: datetime | None, max_age_days: int) -> bool:
    if published is None:
        return False
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    return published.astimezone(timezone.utc) >= cutoff


def _parse_title_embedded_date(title: str) -> datetime | None:
    m = _TITLE_DATE_RE.search(title or "")
    if not m:
        return None
    month, day, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if year < 100:
        year += 2000
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _is_quality_headline(item: dict[str, str], *, max_age_days: int | None = None) -> bool:
    """Drop directory pages, social posts, and visibly stale story titles."""
    title = (item.get("title") or "").strip()
    url = (item.get("url") or "").strip().lower()
    if not title or len(title) < 12:
        return False
    blob = f"{title} {url}"
    if _JUNK_HEADLINE_RE.search(blob):
        return False

    if max_age_days is not None:
        published = item.get("published")
        pub_dt = None
        if published:
            try:
                pub_dt = datetime.fromisoformat(published)
                if pub_dt.tzinfo is None:
                    pub_dt = pub_dt.replace(tzinfo=timezone.utc)
            except ValueError:
                pub_dt = None
        title_dt = _parse_title_embedded_date(title)
        check_dt = title_dt or pub_dt
        if check_dt is not None and not _is_recent(check_dt, max_age_days):
            return False
        # Web-search hits often lack dates — reject if the title embeds an old date.
        if title_dt is not None and not _is_recent(title_dt, max_age_days):
            return False

    return True


def _filter_quality_headlines(
    items: list[dict[str, str]],
    *,
    max_age_days: int | None = None,
) -> list[dict[str, str]]:
    return [item for item in items if _is_quality_headline(item, max_age_days=max_age_days)]


def _headline_key(item: dict[str, str]) -> str:
    return re.sub(r"\W+", " ", item.get("title", "").lower()).strip()


def _parse_google_news_rss(
    payload: bytes,
    *,
    limit: int,
    max_age_days: int | None = None,
) -> list[dict[str, str]]:
    if not payload:
        return []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return []

    items = root.findall(".//item")
    scan_limit = limit * 4 if max_age_days is not None else limit
    hits: list[dict[str, str]] = []
    for item in items[:scan_limit]:
        title = unescape(item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        source_el = item.find("source")
        source = unescape(source_el.text or "").strip() if source_el is not None else ""
        if not source and " - " in title:
            head, pub = title.rsplit(" - ", 1)
            if pub and len(pub) < 80:
                title, source = head.strip(), pub.strip()
        elif source and title.endswith(f" - {source}"):
            title = title[: -len(f" - {source}")].strip()
        if not title:
            continue

        pub_date_text = (item.findtext("pubDate") or "").strip()
        published = _parse_rss_pub_date(pub_date_text)
        if max_age_days is not None and not _is_recent(published, max_age_days):
            continue

        entry: dict[str, str] = {"title": title, "url": link, "source": source}
        if published is not None:
            entry["published"] = published.isoformat()
        hits.append(entry)
        if len(hits) >= limit:
            break
    return hits


def _google_news_rss(*, query: str | None = None) -> str:
    params = {"hl": "en-US", "gl": "US", "ceid": "US:en"}
    if query:
        return f"https://news.google.com/rss/search?{urllib.parse.urlencode({**params, 'q': query})}"
    return f"https://news.google.com/rss?{urllib.parse.urlencode(params)}"


def _parse_city_state(place: str) -> tuple[str, str]:
    place = (place or "").strip()
    if "," in place:
        city, state = place.split(",", 1)
        return city.strip(), state.strip()
    return place, ""


_STATE_NAMES: dict[str, str] = {
    "NH": "New Hampshire",
    "VT": "Vermont",
    "MA": "Massachusetts",
    "ME": "Maine",
    "RI": "Rhode Island",
}


def _state_terms(state: str) -> list[str]:
    abbr = state.strip().upper()
    if not abbr:
        return []
    full = _STATE_NAMES.get(abbr, "")
    terms = [abbr]
    if full and full.lower() not in {t.lower() for t in terms}:
        terms.append(full)
    return terms


# Headlines that say "Charlestown" but mean another town (Boston neighborhood, RI, MA, etc.)
_WRONG_CHARLESTOWN_RE = re.compile(
    r"|".join(
        (
            r"\bcharlestown\s*,?\s*(ri|ma|wv|in)\b",
            r"\b(rhode island|massachusetts|west virginia)\b",
            r"\bboston\b",
            r"\bbeacon hill\b",
            r"\bcharlestown\s+neighborhood\b",
        )
    ),
    re.I,
)

_NH_LOCAL_SIGNAL_RE = re.compile(
    r"|".join(
        (
            r"\bnew hampshire\b",
            r"\bnh\b",
            r"\bsullivan county\b",
            r"\bconnecticut river\b",
            r"\bupper valley\b",
            r"\bcharlestown\s*,?\s*nh\b",
            r"\bcharlestown\s+nh\b",
            r"\bclaremont\b",
            r"\blebanon\b",
            r"\bcornish\b",
            r"\bwalpole\b",
            r"\bvalley news\b",
            r"\beagle times\b",
        )
    ),
    re.I,
)


def _headline_text_blob(item: dict[str, str]) -> str:
    return f"{item.get('title', '')} {item.get('source', '')}"


def _is_relevant_local_headline(item: dict[str, str], scope: dict[str, Any]) -> bool:
    """Drop local hits that clearly refer to a different homonym town."""
    primary = str(scope.get("primary") or "")
    city, state = _parse_city_state(primary)
    if not city:
        return True

    blob = _headline_text_blob(item)
    city_re = re.compile(rf"\b{re.escape(city)}\b", re.I)
    if not city_re.search(blob):
        return True

    # Charlestown is a common place name — require NH/Upper Valley context when state is NH.
    if city.lower() == "charlestown" and state.upper() == "NH":
        if _WRONG_CHARLESTOWN_RE.search(blob):
            return False
        if not _NH_LOCAL_SIGNAL_RE.search(blob):
            return False

    return True


def _filter_local_headlines(items: list[dict[str, str]], scope: dict[str, Any]) -> list[dict[str, str]]:
    return [item for item in items if _is_relevant_local_headline(item, scope)]


def _build_primary_query(primary: str, *, max_age_days: int) -> str:
    city, state = _parse_city_state(primary)
    if state:
        terms: list[str] = [f'"{primary}"', f'"{city} {state.upper()}"']
        for st in _state_terms(state):
            terms.append(f'"{city}, {st}"')
        if city.lower() == "charlestown" and state.upper() == "NH":
            terms.extend(['"Sullivan County NH"', '"Connecticut River" "Charlestown NH"'])
        # Never search bare "Charlestown" — it pulls Boston, RI, MA, etc.
        q = " OR ".join(dict.fromkeys(terms))
        return f"({q}) when:{max_age_days}d"
    return f'"{primary}" when:{max_age_days}d'


def _build_regional_query(towns: list[str], *, max_age_days: int) -> str:
    if not towns:
        return f"Upper Valley Connecticut River when:{max_age_days}d"
    quoted = " OR ".join(f'"{town}"' if " " in town else town for town in towns)
    return f"({quoted}) Connecticut River when:{max_age_days}d"


def _merge_local_headlines(
    primary: list[dict[str, str]],
    regional: list[dict[str, str]],
    *,
    limit: int,
) -> list[dict[str, str]]:
    """Charlestown / primary headlines first, then corridor towns."""
    seen: set[str] = set()
    merged: list[dict[str, str]] = []

    for item in primary:
        key = _headline_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= limit:
            return merged

    for item in regional:
        key = _headline_key(item)
        if not key or key in seen:
            continue
        seen.add(key)
        merged.append(item)
        if len(merged) >= limit:
            break

    return merged


def _search_fallback(query: str, *, limit: int) -> list[dict[str, str]]:
    from jarvis import web_search

    hits = web_search.search(query, limit=limit)
    out: list[dict[str, str]] = []
    for hit in hits:
        title = (hit.get("title") or "").strip()
        if not title:
            continue
        out.append({
            "title": title,
            "url": (hit.get("url") or "").strip(),
            "source": "",
        })
    return out


def _dedupe_headlines(*groups: list[dict[str, str]]) -> tuple[list[dict[str, str]], ...]:
    seen: set[str] = set()
    result: list[list[dict[str, str]]] = []
    for group in groups:
        kept: list[dict[str, str]] = []
        for item in group:
            key = _headline_key(item)
            if not key or key in seen:
                continue
            seen.add(key)
            kept.append(item)
        result.append(kept)
    return tuple(result)


def _fetch_local_headlines(
    scope: dict[str, Any],
    *,
    limit: int,
    max_age_days: int,
) -> list[dict[str, str]]:
    primary = str(scope["primary"])
    towns = list(scope.get("towns") or [])
    overfetch = max(limit, limit * 2)

    primary_query = _build_primary_query(primary, max_age_days=max_age_days)
    primary_hits = _filter_quality_headlines(
        _filter_local_headlines(
            _parse_google_news_rss(
                _fetch_bytes(_google_news_rss(query=primary_query)) or b"",
                limit=overfetch,
                max_age_days=max_age_days,
            ),
            scope,
        ),
        max_age_days=max_age_days,
    )

    regional_query = _build_regional_query(towns, max_age_days=max_age_days)
    regional_hits = _filter_quality_headlines(
        _filter_local_headlines(
            _parse_google_news_rss(
                _fetch_bytes(_google_news_rss(query=regional_query)) or b"",
                limit=overfetch,
                max_age_days=max_age_days,
            ),
            scope,
        ),
        max_age_days=max_age_days,
    )

    local = _merge_local_headlines(primary_hits, regional_hits, limit=limit)
    local = _filter_quality_headlines(_filter_local_headlines(local, scope), max_age_days=max_age_days)

    if not local:
        year = datetime.now(timezone.utc).year
        fallback_query = (
            f'"{primary}" {" OR ".join(f'"{t}"' if " " in t else t for t in towns[:4])} '
            f'"Connecticut River" news {year} last {max_age_days} days'
        )
        local = _filter_quality_headlines(
            _filter_local_headlines(
                _search_fallback(fallback_query, limit=limit * 2),
                scope,
            ),
            max_age_days=max_age_days,
        )[:limit]

    return local


def fetch_briefing_news(
    *,
    memory_store=None,
    weather: dict | None = None,
    national_limit: int | None = None,
    local_limit: int | None = None,
    force_refresh: bool = False,
) -> dict[str, Any]:
    """Fetch national + local headline lists for the briefing."""
    nat_lim = national_limit if national_limit is not None else _national_limit()
    loc_lim = local_limit if local_limit is not None else _local_limit()
    max_age_days = _local_max_age_days()
    scope = resolve_local_news_scope(memory_store=memory_store, weather=weather)
    local_place = scope["label"]
    local_primary = scope["primary"]

    if not news_available():
        return {
            "enabled": False,
            "national": [],
            "local": [],
            "local_place": local_place,
            "local_primary": local_primary,
            "skipped": "offline profile or JARVIS_BRIEFING_NEWS=0",
        }

    cache_key = f"{local_primary}|{local_place}|{nat_lim}|{loc_lim}|{max_age_days}"
    if not force_refresh:
        cached = _CACHE.get(cache_key)
        if cached and (time.time() - cached[0]) < _CACHE_TTL_SEC:
            return dict(cached[1])

    national = _filter_quality_headlines(
        _parse_google_news_rss(
            _fetch_bytes(_google_news_rss()) or b"",
            limit=nat_lim * 2,
            max_age_days=max_age_days,
        ),
        max_age_days=max_age_days,
    )[:nat_lim]
    if not national:
        year = datetime.now(timezone.utc).year
        national = _filter_quality_headlines(
            _search_fallback(f"United States top news headlines {year}", limit=nat_lim * 2),
            max_age_days=max_age_days,
        )[:nat_lim]

    local: list[dict[str, str]] = []
    if local_primary:
        local = _fetch_local_headlines(scope, limit=loc_lim, max_age_days=max_age_days)

    national, local = _dedupe_headlines(national, local)

    bundle = {
        "enabled": True,
        "national": national,
        "local": local,
        "local_place": local_place,
        "local_primary": local_primary,
        "skipped": None,
    }
    _CACHE[cache_key] = (time.time(), bundle)
    return dict(bundle)


def _format_headline(item: dict[str, str], *, index: int | None = None) -> str:
    title = item.get("title", "Headline")
    url = item.get("url", "")
    source = item.get("source", "")
    prefix = f"{index}. " if index is not None else "- "
    suffix = f" — _{source}_" if source else ""
    if url:
        return f"{prefix}[{title}]({url}){suffix}"
    return f"{prefix}**{title}**{suffix}"


def format_news_markdown(news: dict[str, Any]) -> list[str]:
    """Markdown lines for briefing; empty if nothing to show."""
    if not news.get("enabled"):
        return []

    lines: list[str] = []
    national = news.get("national") or []
    local = news.get("local") or []
    local_place = news.get("local_place")
    local_primary = news.get("local_primary")

    if national:
        lines.extend(["", "**National headlines**"])
        lines.extend(_format_headline(item, index=i) for i, item in enumerate(national, 1))

    if local:
        if local_place and local_primary:
            label = f"**Local headlines ({local_place} · {local_primary} first)**"
        elif local_place:
            label = f"**Local headlines ({local_place})**"
        else:
            label = "**Local headlines**"
        lines.extend(["", label])
        lines.extend(_format_headline(item, index=i) for i, item in enumerate(local, 1))
        lines.extend([
            "",
            "_To expand a story in chat: **tell me more about local headline 2** "
            "or **headline 3** (national # / local # as shown)._",
        ])

    if not lines and news.get("skipped"):
        return []

    if not lines:
        lines.extend(["", "_Headlines unavailable right now — try again later._"])

    return lines


def headlines_from_bundle(news: dict[str, Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in news.get("national") or []:
        out.append({**item, "category": "national"})
    for item in news.get("local") or []:
        out.append({**item, "category": "local"})
    return out


def persist_briefing_headlines(news: dict[str, Any]) -> list[dict[str, str]]:
    """Save today's briefing headlines for chat follow-ups."""
    headlines = headlines_from_bundle(news)
    if not headlines:
        return []
    from datetime import date

    from jarvis.config import _load_chat_settings, _write_chat_settings

    data = _load_chat_settings()
    data.setdefault("morning_briefing", {})["headlines"] = headlines
    data["morning_briefing"]["headlines_day"] = date.today().isoformat()
    _write_chat_settings(data)
    return headlines


def load_recent_headlines() -> list[dict[str, str]]:
    from datetime import date

    from jarvis.config import _load_chat_settings

    state = _load_chat_settings().get("morning_briefing") or {}
    if state.get("headlines_day") != date.today().isoformat():
        return []
    return list(state.get("headlines") or [])


def _meaningful_words(text: str) -> set[str]:
    return {
        w
        for w in re.findall(r"[a-z]{4,}", (text or "").lower())
        if w not in _MATCH_STOPWORDS
    }


def _headlines_for_category(headlines: list[dict[str, str]], category: str) -> list[dict[str, str]]:
    return [h for h in headlines if (h.get("category") or "") == category]


def match_headline(query: str, headlines: list[dict[str, str]]) -> dict[str, str] | None:
    """Best-effort match from user text to a briefing headline."""
    if not query or not headlines:
        return None

    q = query.lower().strip()

    title_hint = query.strip()
    if title_hint:
        for item in headlines:
            if (item.get("title") or "").strip() == title_hint:
                return item

    cat_match = re.search(
        r"\b(national|local)\s+(?:headline|story|article|item|news)?\s*#?\s*(\d+)\b",
        q,
    )
    if cat_match:
        category = cat_match.group(1)
        idx = int(cat_match.group(2)) - 1
        pool = _headlines_for_category(headlines, category)
        if 0 <= idx < len(pool):
            return pool[idx]

    index_match = re.search(r"\b(?:headline|story|article|item|news)\s*#?\s*(\d+)\b", q)
    if index_match:
        idx = int(index_match.group(1)) - 1
        if re.search(r"\blocal\b", q):
            pool = _headlines_for_category(headlines, "local")
            if 0 <= idx < len(pool):
                return pool[idx]
        if re.search(r"\bnational\b", q):
            pool = _headlines_for_category(headlines, "national")
            if 0 <= idx < len(pool):
                return pool[idx]
        if 0 <= idx < len(headlines):
            return headlines[idx]

    for item in headlines:
        title = (item.get("title") or "").strip()
        if title and title.lower() in q:
            return item

    query_words = _meaningful_words(q)
    if not query_words:
        return None

    best: dict[str, str] | None = None
    best_score = 0
    for item in headlines:
        title = (item.get("title") or "").strip()
        if not title:
            continue
        title_words = _meaningful_words(title)
        overlap = len(title_words & query_words)
        if overlap > best_score:
            best_score = overlap
            best = item

    if best_score >= 2:
        return best
    return None


_DETAIL_PATTERNS = (
    r"\b(tell me more|more (?:about|on)|expand on|go deeper on)\b",
    r"\b(explain (?:the |that )?(?:story|article|headline|news))\b",
    r"\b(what(?:'s| is) (?:the )?(?:story|news) (?:about|on))\b",
    r"\b(that|this) (?:story|headline|article|news item)\b",
    r"\babout (?:that|the) (?:story|headline|news)\b",
    r"\bheadline\s*#?\s*\d+\b",
    r"\b(briefing|morning) (?:news|headline|story)\b",
)


def looks_like_headline_followup(message: str, *, last_module: str = "") -> bool:
    lower = (message or "").lower().strip()
    if not lower:
        return False
    if any(re.search(p, lower) for p in _DETAIL_PATTERNS):
        return True
    if last_module == "briefing" and re.search(r"\b(news|headline|story|article)\b", lower):
        return True
    return False


def briefing_news_intent(message: str, session) -> dict[str, Any] | None:
    """Router helper: expand a morning-briefing headline."""
    headlines = list(getattr(session, "last_briefing_headlines", None) or []) or load_recent_headlines()
    if not headlines:
        return None

    last_module = getattr(session, "last_module", "") or ""
    wants_detail = looks_like_headline_followup(message, last_module=last_module)
    matched = match_headline(message, headlines)
    if not matched and not wants_detail:
        return None

    return {
        "action": "briefing_news_detail",
        "params": {
            "query": message,
            "title": (matched.get("title", "") if matched else ""),
        },
        "thinking": "briefing news detail",
    }


def _detail_synthesis_messages(
    headline: dict[str, str],
    user_query: str,
    results: list[dict],
) -> tuple[list[dict], str]:
    from jarvis import web_search

    title = headline.get("title", "Headline")
    source = headline.get("source", "")
    category = headline.get("category", "")
    context = web_search.format_results_for_llm(results)
    system = (
        "You are expanding on a headline from the user's morning briefing. "
        "Give a clear news summary with the key facts: who, what, when, where, and why it matters. "
        "Write in complete sentences. Do NOT tell the user to visit a website or read elsewhere — "
        "deliver the story here. Use ONLY the search snippets below. "
        "Cite sources as [1], [2]. If snippets are thin, say what is known and what is still unclear."
    )
    user = (
        f"Briefing headline ({category or 'news'}): {title}"
        + (f" — {source}" if source else "")
        + f"\nUser question: {user_query or f'Tell me more about: {title}'}"
        + f"\n\nSearch results:\n{context}"
    )
    sources = "\n".join(
        f"[{i}] {r.get('title', '')} — {r.get('url', '')}"
        for i, r in enumerate(results, 1)
        if r.get("url")
    )
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ], sources


def expand_headline_detail(
    headline: dict[str, str],
    *,
    user_query: str = "",
    search_limit: int = 6,
) -> str:
    """Research and summarize a briefing headline for chat."""
    from jarvis import web_search
    from jarvis.profiles import web_search_disabled

    if web_search_disabled():
        return (
            "Web search is disabled in your current profile, so I can't pull more on that story right now. "
            "Switch to an online profile in the sidebar, or open the headline link from your briefing."
        )

    title = (headline.get("title") or "").strip()
    if not title:
        return "I couldn't identify which briefing story you mean."

    query = user_query.strip() or f"Tell me more about: {title}"
    year = datetime.now(timezone.utc).year
    search_terms = f"{title} {year}"
    if headline.get("source"):
        search_terms += f" {headline['source']}"
    results = web_search.search(search_terms, limit=search_limit)
    if not results:
        results = web_search.search(f"{title} news {year}", limit=search_limit)
    if not results:
        return f"I couldn't find more coverage on **{title}** right now. Try again in a few minutes."

    return "".join(expand_headline_detail_stream(headline, user_query=query, results=results)).strip()


def expand_headline_detail_stream(
    headline: dict[str, str],
    *,
    user_query: str = "",
    results: list[dict] | None = None,
):
    """Stream a detailed briefing headline summary."""
    from jarvis import llm, web_search

    title = (headline.get("title") or "").strip()
    query = user_query.strip() or f"Tell me more about: {title}"
    hits = results if results is not None else web_search.search(title, limit=6)
    if not hits:
        yield f"I couldn't find more coverage on **{title}** right now."
        return

    msgs, sources = _detail_synthesis_messages(headline, query, hits)
    body: list[str] = []
    try:
        for chunk in llm.ask_stream(llm.general_model(), msgs):
            body.append(chunk)
            yield chunk
        if sources and "".join(body).strip():
            yield f"\n\n**Sources**\n{sources}"
    except Exception as exc:
        log.warning("Briefing headline synthesis failed: %s", exc)
        if not body:
            yield web_search.synthesize_answer(query, hits)
