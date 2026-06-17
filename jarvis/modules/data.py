"""Data analysis: CSV, JSON, XLSX, SQLite with pandas when available."""

from __future__ import annotations

import csv
import json
import os
import re
import textwrap
from datetime import datetime
from pathlib import Path

from jarvis import fs, llm
from jarvis.branding import assistant_name
from jarvis.config import DATA_DIR, PROJECT_ROOT
from jarvis.conversation import Conversation

MAX_DATA_ROWS = int(os.getenv("JARVIS_DATA_MAX_ROWS", "50000"))
STREAM_THRESHOLD_BYTES = int(os.getenv("JARVIS_DATA_STREAM_MB", "10")) * 1024 * 1024
PREVIEW_ROWS = int(os.getenv("JARVIS_DATA_PREVIEW_ROWS", "20"))
CHUNK_SIZE = int(os.getenv("JARVIS_DATA_CHUNK_SIZE", "50000"))
EXPORT_DIR = DATA_DIR / "exports"
CHART_DIR = DATA_DIR / "charts"
STREAM_DIR = DATA_DIR / "stream"

def _human_size(n: int) -> str:
    size = float(n)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{int(size)} B" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} GB"

def parse_chart_request(message: str) -> dict:
    """Extract chart type and column from natural language."""
    lower = (message or "").lower()
    chart_type = "bar"
    if re.search(r"\b(pie|donut)\b", lower):
        chart_type = "pie"
    elif re.search(r"\b(line|trend|over time)\b", lower):
        chart_type = "line"
    elif re.search(r"\b(hist|histogram|distribution)\b", lower):
        chart_type = "hist"

    column = ""
    if m := re.search(r"\b(?:chart|graph|plot)\s+(\w[\w\s-]{0,30}?)(?:\s+by|\s*$)", lower):
        column = m.group(1).strip()
    elif m := re.search(r"\b(?:of|for)\s+[`'\"]