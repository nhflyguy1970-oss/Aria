"""Local daily weather for bullet journal — Open-Meteo (no API key)."""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, timedelta
from typing import Any

# WMO weather interpretation codes (subset)
WMO_ICONS: dict[int, str] = {
    0: "☀️",
    1: "🌤️",
    2: "⛅",
    3: "☁️",
    45: "🌫️",
    48: "🌫️",
    51: "🌦️",
    53: "🌦️",
    55: "🌧️",
    61: "🌧️",
    63: "🌧️",
    65: "🌧️",
    71: "🌨️",
    73: "🌨️",
    75: "❄️",
    80: "🌦️",
    81: "🌧️",
    82: "⛈️",
    95: "⛈️",
    96: "⛈️",
    99: "⛈️",
}

WMO_LABELS: dict[int, str] = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}

_GEO_CACHE: dict[str, tuple[float, float, str]] = {}


def _http_json(url: str, timeout: float = 12.0) -> dict[str, Any] | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Jarvis/1.0 (local journal weather)"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None


def _units() -> str:
    u = os.getenv("JARVIS_WEATHER_UNITS", "fahrenheit").strip().lower()
    return "celsius" if u in ("c", "celsius", "metric") else "fahrenheit"


def _resolve_location() -> tuple[float, float, str] | None:
    lat = os.getenv("JARVIS_WEATHER_LAT", "").strip()
    lon = os.getenv("JARVIS_WEATHER_LON", "").strip()
    label = os.getenv("JARVIS_WEATHER_LOCATION", "").strip()
    if lat and lon:
        try:
            return float(lat), float(lon), label or f"{lat}, {lon}"
        except ValueError:
            pass

    city = os.getenv("JARVIS_WEATHER_CITY", "").strip()
    if city:
        if city in _GEO_CACHE:
            la, lo, name = _GEO_CACHE[city]
            return la, lo, name
        q = urllib.parse.quote(city)
        data = _http_json(
            f"https://geocoding-api.open-meteo.com/v1/search?name={q}&count=1&language=en&format=json"
        )
        results = (data or {}).get("results") or []
        if results:
            r = results[0]
            la, lo = float(r["latitude"]), float(r["longitude"])
            parts = [r.get("name"), r.get("admin1"), r.get("country_code")]
            name = ", ".join(p for p in parts if p)
            _GEO_CACHE[city] = (la, lo, name)
            return la, lo, name

    if os.getenv("JARVIS_WEATHER_IP_LOOKUP", "1").lower() not in ("0", "false", "no"):
        data = _http_json("http://ip-api.com/json/?fields=status,lat,lon,city,regionName,countryCode")
        if data and data.get("status") == "success":
            la, lo = float(data["lat"]), float(data["lon"])
            parts = [data.get("city"), data.get("regionName"), data.get("countryCode")]
            name = ", ".join(p for p in parts if p) or "Local"
            return la, lo, name
    return None


def parse_weather_day(message: str, *, reference: date | None = None) -> str:
    """Map natural language to an ISO date (today, tomorrow, or YYYY-MM-DD)."""
    ref = reference or date.today()
    lower = message.lower()
    if re.search(r"\btomorrow\b", lower):
        return (ref + timedelta(days=1)).isoformat()
    if re.search(r"\byesterday\b", lower):
        return (ref - timedelta(days=1)).isoformat()
    if re.search(r"\btoday\b", lower):
        return ref.isoformat()
    if m := re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", message):
        return m.group(1)
    return ref.isoformat()


def weather_day_label(day: str, *, reference: date | None = None) -> str:
    ref = reference or date.today()
    d = date.fromisoformat(day)
    if d == ref:
        return "Today"
    if d == ref + timedelta(days=1):
        return "Tomorrow"
    if d == ref - timedelta(days=1):
        return "Yesterday"
    return d.strftime("%A, %B %d")


def weather_forecast_text(day: str | None = None, *, message: str = "") -> str:
    """User-facing forecast line for chat or journal."""
    target = day or (parse_weather_day(message) if message else date.today().isoformat())
    w = weather_for_day(target)
    if not w:
        loc = os.getenv("JARVIS_WEATHER_LOCATION", "").strip() or "your area"
        return (
            f"I couldn't load a forecast for **{weather_day_label(target)}** near {loc}. "
            "Check `JARVIS_WEATHER_LAT` / `JARVIS_WEATHER_LON` in `data/jarvis.env`."
        )
    label = weather_day_label(w["date"])
    line = format_weather_line(w)
    body = line.split(": ", 1)[-1] if ": " in line else line
    loc = w.get("location", "")
    head = f"**{label}**"
    if loc:
        head += f" in {loc}"
    return f"{head} — {body}"


def weather_for_day(day: str | None = None) -> dict[str, Any] | None:
    """Fetch high/low temp and conditions for a calendar day (ISO date)."""
    d = day or date.today().isoformat()
    loc = _resolve_location()
    if not loc:
        return None
    lat, lon, place = loc
    unit = _units()
    params = urllib.parse.urlencode({
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,weathercode",
        "timezone": "auto",
        "start_date": d,
        "end_date": d,
        "temperature_unit": unit,
    })
    data = _http_json(f"https://api.open-meteo.com/v1/forecast?{params}")
    if not data:
        return None
    daily = data.get("daily") or {}
    times = daily.get("time") or []
    if d not in times:
        return None
    idx = times.index(d)
    try:
        high = float(daily["temperature_2m_max"][idx])
        low = float(daily["temperature_2m_min"][idx])
        code = int(daily["weathercode"][idx])
    except (KeyError, IndexError, TypeError, ValueError):
        return None

    sym = "°F" if unit == "fahrenheit" else "°C"
    condition = WMO_LABELS.get(code, f"Code {code}")
    icon = WMO_ICONS.get(code, "🌡️")
    hi, lo = round(high), round(low)
    return {
        "date": d,
        "location": place,
        "high": round(high, 1),
        "low": round(low, 1),
        "unit": sym,
        "code": code,
        "icon": icon,
        "condition": condition,
        "summary": f"{condition} · H {hi}{sym} / L {lo}{sym}",
        "source": "open-meteo",
    }


def weather_icon(code: int | None) -> str:
    if code is None:
        return "🌡️"
    return WMO_ICONS.get(int(code), "🌡️")


def format_weather_line(weather: dict[str, Any] | None) -> str:
    if not weather:
        return ""
    icon = weather.get("icon") or weather_icon(weather.get("code"))
    loc = weather.get("location", "")
    condition = weather.get("condition", "")
    sym = weather.get("unit", "°")
    hi = weather.get("high")
    lo = weather.get("low")
    if hi is not None and lo is not None:
        temps = f"H {round(float(hi))}{sym} / L {round(float(lo))}{sym}"
        body = f"{condition} · {temps}" if condition else temps
    else:
        body = weather.get("summary", condition)
    prefix = f"{icon} {loc}: " if loc else f"{icon} "
    return prefix + body
