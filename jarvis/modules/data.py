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
    elif m := re.search(r"\b(?:of|for)\s+[`'\"]?(\w[\w-]*)[`'\"]?", lower):
        column = m.group(1).strip()
    return {"chart_type": chart_type, "column": column or None}


class DataEngine:
    def __init__(self):
        self.conversation = Conversation(
            f"You are {assistant_name()} Data Analyst. Help users understand and analyze data."
        )
        self.dataset: dict | None = None
        self.dataset_path: Path | None = None
        self._truncated = False
        self._streaming = False
        self._last_chart_path: str | None = None

    def _require_dataset(self) -> dict:
        if self.dataset is None:
            raise RuntimeError("No dataset loaded")
        return self.dataset

    def _should_stream(self, path: Path) -> bool:
        try:
            return path.stat().st_size >= STREAM_THRESHOLD_BYTES
        except OSError:
            return False

    def _load_csv_streaming(self, path: Path) -> dict:
        preview: list[dict] = []
        columns: list[str] = []
        total = 0
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            columns = list(reader.fieldnames or [])
            for row in reader:
                total += 1
                if len(preview) < PREVIEW_ROWS:
                    preview.append(row)
        self._streaming = True
        return {
            "type": "csv",
            "columns": columns,
            "rows": preview,
            "row_count": total,
            "streaming": True,
            "file_size": path.stat().st_size,
        }

    def _load_csv(self, path: Path) -> dict:
        if self._should_stream(path):
            return self._load_csv_streaming(path)
        with open(path, newline="", encoding="utf-8", errors="ignore") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if len(rows) > MAX_DATA_ROWS:
            rows = rows[:MAX_DATA_ROWS]
            self._truncated = True
        return {
            "type": "csv",
            "columns": list(rows[0].keys()) if rows else [],
            "rows": rows,
            "row_count": len(rows),
        }

    def _is_json_lines(self, path: Path) -> bool:
        checked = 0
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    return False
                if not isinstance(obj, dict):
                    return False
                checked += 1
                if checked >= 2:
                    return True
        return checked == 1

    def _load_json_lines(self, path: Path) -> dict:
        preview: list[dict] = []
        columns: list[str] = []
        total = 0
        with open(path, encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    continue
                total += 1
                if not columns:
                    columns = list(obj.keys())
                if len(preview) < PREVIEW_ROWS:
                    preview.append(obj)
        self._streaming = True
        return {
            "type": "json",
            "columns": columns,
            "rows": preview,
            "row_count": total,
            "streaming": True,
            "jsonl": True,
            "file_size": path.stat().st_size,
        }

    def _load_json(self, path: Path) -> dict:
        if self._should_stream(path) and self._is_json_lines(path):
            return self._load_json_lines(path)
        if self._should_stream(path):
            raise RuntimeError(
                f"JSON file is {_human_size(path.stat().st_size)} — use JSON Lines (.jsonl) or CSV for large files."
            )
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            rows = data[:MAX_DATA_ROWS]
            if len(data) > MAX_DATA_ROWS:
                self._truncated = True
            cols = list(rows[0].keys()) if rows and isinstance(rows[0], dict) else []
            return {"type": "json", "columns": cols, "rows": rows, "row_count": len(rows)}
        return {"type": "json", "data": data, "row_count": 1}

    def _load_xlsx(self, path: Path) -> dict:
        try:
            import openpyxl
        except ImportError:
            raise RuntimeError("Install openpyxl: pip install openpyxl")
        stream = self._should_stream(path)
        wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
        ws = wb.active
        if ws is None:
            wb.close()
            raise RuntimeError("Workbook has no active sheet")
        rows_iter = ws.iter_rows(values_only=True)
        headers = [str(h) if h is not None else f"col{i}" for i, h in enumerate(next(rows_iter, []))]
        rows: list[dict] = []
        total = 0
        for row in rows_iter:
            total += 1
            if len(rows) < (PREVIEW_ROWS if stream else MAX_DATA_ROWS):
                rows.append({headers[i]: row[i] for i in range(min(len(headers), len(row)))})
            elif not stream:
                self._truncated = True
                break
        wb.close()
        if stream:
            self._streaming = True
            return {
                "type": "xlsx",
                "columns": headers,
                "rows": rows,
                "row_count": total,
                "streaming": True,
                "file_size": path.stat().st_size,
            }
        return {"type": "xlsx", "columns": headers, "rows": rows, "row_count": len(rows)}

    def _load_sqlite(self, path: Path, table: str | None = None) -> dict:
        import sqlite3
        conn = sqlite3.connect(str(path))
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        if not table:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
            tables = [r[0] for r in cur.fetchall()]
            if not tables:
                conn.close()
                raise RuntimeError("No tables in database")
            table = tables[0]
        cur.execute(f"SELECT COUNT(*) FROM [{table}]")
        total = int(cur.fetchone()[0])
        limit = PREVIEW_ROWS if total > MAX_DATA_ROWS else min(total, MAX_DATA_ROWS)
        cur.execute(f"SELECT * FROM [{table}] LIMIT {limit}")
        rows_raw = cur.fetchall()
        columns = [d[0] for d in cur.description] if cur.description else []
        rows = [dict(r) for r in rows_raw]
        conn.close()
        if total > MAX_DATA_ROWS:
            self._streaming = True
            self._truncated = True
        return {
            "type": "sqlite",
            "table": table,
            "columns": columns,
            "rows": rows,
            "row_count": total,
            "streaming": total > MAX_DATA_ROWS,
        }

    def dataframe(self):
        """Pandas DataFrame or None (preview rows when streaming)."""
        if not self.dataset or not self.dataset.get("rows"):
            return None
        try:
            import pandas as pd
        except ImportError:
            return None
        return pd.DataFrame(self.dataset["rows"])

    def _pandas_chunks(self):
        """Yield pandas DataFrame chunks for streaming tabular files."""
        import pandas as pd

        if not self.dataset_path or not self.dataset:
            return
        dtype = self.dataset.get("type")
        if dtype == "csv":
            yield from pd.read_csv(
                self.dataset_path,
                chunksize=CHUNK_SIZE,
                encoding="utf-8",
                on_bad_lines="skip",
            )
        elif dtype == "json" and self.dataset.get("jsonl"):
            batch: list[dict] = []
            with open(self.dataset_path, encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    batch.append(json.loads(line))
                    if len(batch) >= CHUNK_SIZE:
                        yield pd.DataFrame(batch)
                        batch = []
            if batch:
                yield pd.DataFrame(batch)
        elif dtype == "xlsx":
            try:
                yield from pd.read_excel(self.dataset_path, chunksize=CHUNK_SIZE)
            except (ValueError, TypeError):
                df = pd.read_excel(self.dataset_path)
                yield df

    def _resolve_column_name(self, name: str, columns: list) -> str | None:
        if name in columns:
            return name
        lower = name.lower()
        for c in columns:
            if str(c).lower() == lower:
                return c
        return None

    def _streaming_numeric_agg(self, column: str, op: str) -> str | None:
        """Chunked sum/mean/min/max over full file."""
        try:
            import pandas as pd
        except ImportError:
            return None
        ds = self.dataset
        if not ds:
            return None
        cols = ds.get("columns") or []
        col = self._resolve_column_name(column, cols)
        if not col:
            return None
        total_sum = 0.0
        count = 0
        vmin = vmax = None
        for chunk in self._pandas_chunks():
            if col not in chunk.columns:
                continue
            s = pd.to_numeric(chunk[col], errors="coerce").dropna()
            if s.empty:
                continue
            if op == "mean" or op == "sum":
                total_sum += float(s.sum())
                count += int(s.count())
            elif op == "min":
                val = float(s.min())
                vmin = val if vmin is None else min(vmin, val)
            elif op == "max":
                val = float(s.max())
                vmax = val if vmax is None else max(vmax, val)
        if op == "mean":
            return f"Average **{col}**: **{total_sum / count:.4g}** (full file, {count} numeric values)." if count else None
        if op == "sum":
            return f"Sum of **{col}**: **{total_sum:.4g}** (full file)." if count else None
        if op == "min" and vmin is not None:
            return f"Min **{col}**: **{vmin}** (full file)."
        if op == "max" and vmax is not None:
            return f"Max **{col}**: **{vmax}** (full file)."
        return None

    def _streaming_groupby_sum(self, group_col: str, value_col: str) -> str | None:
        try:
            import pandas as pd
        except ImportError:
            return None
        ds = self.dataset
        if not ds:
            return None
        cols = ds.get("columns") or []
        g = self._resolve_column_name(group_col, cols)
        v = self._resolve_column_name(value_col, cols)
        if not g or not v:
            return None
        acc: dict = {}
        for chunk in self._pandas_chunks():
            if g not in chunk.columns or v not in chunk.columns:
                continue
            tmp = chunk.copy()
            tmp[v] = pd.to_numeric(tmp[v], errors="coerce")
            grouped = tmp.groupby(g)[v].sum()
            for key, val in grouped.items():
                acc[key] = acc.get(key, 0.0) + float(val)
        if not acc:
            return None
        lines = [f"{k}: {val:.4g}" for k, val in sorted(acc.items(), key=lambda x: -x[1])[:20]]
        return f"Group by **{g}**, sum **{v}** (full file):\n```\n" + "\n".join(lines) + "\n```"

    def _stream_column_values(self, column: str, limit: int = 50000) -> list:
        values: list = []
        for chunk in self._pandas_chunks():
            if column not in chunk.columns:
                continue
            values.extend(chunk[column].dropna().astype(str).tolist())
            if len(values) >= limit:
                break
        return values[:limit]

    def sql_query(self, query: str) -> str:
        if not self.dataset or self.dataset.get("type") != "sqlite":
            return "ERROR: Load a .db/.sqlite file first."
        if not self.dataset_path:
            return "ERROR: No database path."
        q = query.strip().upper()
        if not q.startswith("SELECT"):
            return "ERROR: Only SELECT queries are allowed."
        import sqlite3
        try:
            conn = sqlite3.connect(str(self.dataset_path))
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute(query)
            rows = [dict(r) for r in cur.fetchall()[:100]]
            conn.close()
            return json.dumps(rows, indent=2, default=str)
        except Exception as e:
            return f"ERROR: {e}"

    def load_dataset(self, path: str) -> str:
        try:
            self._truncated = False
            self._streaming = False
            resolved = fs.resolve_path(path, base=PROJECT_ROOT)
            if not resolved.exists():
                return f"ERROR: File not found: {resolved}"

            suffix = resolved.suffix.lower()
            if suffix == ".csv":
                self.dataset = self._load_csv(resolved)
            elif suffix == ".json":
                self.dataset = self._load_json(resolved)
            elif suffix in (".xlsx", ".xlsm"):
                self.dataset = self._load_xlsx(resolved)
            elif suffix in (".db", ".sqlite", ".sqlite3"):
                self.dataset = self._load_sqlite(resolved)
            else:
                return f"ERROR: Unsupported format: {suffix} (use .csv, .json, .xlsx, .db)"

            self.dataset_path = resolved
            return "OK"
        except Exception as e:
            return f"ERROR: {e}"

    def preview(self, limit: int = 5) -> dict:
        if not self.dataset:
            return {}
        rows = self.dataset.get("rows") or []
        return {
            "path": str(self.dataset_path) if self.dataset_path else "",
            "name": self.dataset_path.name if self.dataset_path else "",
            "type": self.dataset.get("type", ""),
            "columns": self.dataset.get("columns") or (list(rows[0].keys()) if rows else []),
            "row_count": self.dataset.get("row_count", 0),
            "rows": rows[:limit],
            "truncated": self._truncated,
            "streaming": bool(self.dataset.get("streaming")),
            "file_size": self.dataset.get("file_size"),
        }

    def describe_stats(self) -> str:
        if self._streaming and self.dataset:
            ds = self.dataset
            lines = [
                f"Shape: {ds.get('row_count', 0)} rows × {len(ds.get('columns') or [])} columns",
                "Mode: **streaming** (preview only in memory, stats scan file in chunks)",
            ]
            if ds.get("file_size"):
                lines.append(f"File size: {_human_size(int(ds['file_size']))}")
            if ds.get("columns"):
                lines.append(f"Columns: {', '.join(str(c) for c in ds['columns'])}")
            try:
                chunk = next(self._pandas_chunks())
                if chunk is not None and not chunk.empty:
                    nulls = chunk.isnull().sum()
                    if nulls.any():
                        lines.append(
                            "Null counts (first chunk): "
                            + ", ".join(f"{k}={int(v)}" for k, v in nulls.items() if v)
                        )
                    desc = chunk.describe(include="all", datetime_is_numeric=True).transpose()
                    lines.append("Statistics (first chunk):\n" + desc.to_string(max_cols=8)[:2500])
            except (StopIteration, ImportError, Exception):
                pass
            return "\n".join(lines)

        df = self.dataframe()
        if df is not None and not df.empty:
            lines = [
                f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
                f"Columns: {', '.join(str(c) for c in df.columns)}",
            ]
            nulls = df.isnull().sum()
            if nulls.any():
                lines.append("Null counts: " + ", ".join(f"{k}={int(v)}" for k, v in nulls.items() if v))
            try:
                desc = df.describe(include="all", datetime_is_numeric=True).transpose()
                lines.append("Statistics:\n" + desc.to_string(max_cols=8)[:3000])
            except Exception:
                pass
            return "\n".join(lines)
        return self._summary()

    def _summary(self) -> str:
        if not self.dataset:
            return "No dataset loaded."
        ds = self.dataset
        lines = [f"File: {self.dataset_path}", f"Type: {ds['type']}", f"Rows: {ds.get('row_count', 0)}"]
        if self.dataset.get("streaming"):
            lines.append(f"(streaming — showing first {len(ds.get('rows') or [])} preview rows)")
        elif self._truncated:
            lines.append(f"(truncated to first {MAX_DATA_ROWS} rows)")
        if ds.get("columns"):
            lines.append(f"Columns: {', '.join(ds['columns'])}")
        if ds.get("table"):
            lines.append(f"Table: {ds['table']}")
        if ds.get("rows"):
            preview = json.dumps(ds["rows"][:5], indent=2, default=str)
            lines.append(f"Preview (first 5 rows):\n{preview}")
        elif ds.get("data"):
            preview = json.dumps(ds["data"], indent=2, default=str)[:2000]
            lines.append(f"Data preview:\n{preview}")
        return "\n".join(lines)

    def compute_answer(self, question: str) -> str | None:
        """Try pandas-backed answer before LLM."""
        q = question.lower().strip()
        if re.search(r"\b(how many rows|row count|number of rows|count rows)\b", q):
            n = self.dataset.get("row_count") if self.dataset else 0
            note = " (full file count)" if self._streaming else ""
            return f"The dataset has **{n}** rows{note}."

        if self._streaming:
            ds = self.dataset
            if ds and ds.get("type") == "sqlite":
                if m := re.search(
                    r"\b(?:what(?:'s| is)\s+the\s+)?(?:average|mean|avg)(?:\s+(?:of|for))?\s+(?:the\s+)?[`'\"]?(\w[\w-]*)[`'\"]?",
                    q,
                ):
                    ans = self._sqlite_numeric_agg(m.group(1), "mean")
                    if ans:
                        return ans
                if m := re.search(r"\b(?:sum|total)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
                    ans = self._sqlite_numeric_agg(m.group(1), "sum")
                    if ans:
                        return ans
                if m := re.search(r"\b(?:max|maximum|highest)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
                    ans = self._sqlite_numeric_agg(m.group(1), "max")
                    if ans:
                        return ans
                if m := re.search(r"\b(?:min|minimum|lowest)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
                    ans = self._sqlite_numeric_agg(m.group(1), "min")
                    if ans:
                        return ans
            if m := re.search(
                r"\b(?:what(?:'s| is)\s+the\s+)?(?:average|mean|avg)(?:\s+(?:of|for))?\s+(?:the\s+)?[`'\"]?(\w[\w-]*)[`'\"]?",
                q,
            ):
                ans = self._streaming_numeric_agg(m.group(1), "mean")
                if ans:
                    return ans
            if m := re.search(r"\b(?:sum|total)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
                ans = self._streaming_numeric_agg(m.group(1), "sum")
                if ans:
                    return ans
            if m := re.search(r"\b(?:max|maximum|highest)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
                ans = self._streaming_numeric_agg(m.group(1), "max")
                if ans:
                    return ans
            if m := re.search(r"\b(?:min|minimum|lowest)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
                ans = self._streaming_numeric_agg(m.group(1), "min")
                if ans:
                    return ans
            if m := re.search(
                r"\bgroup\s+by\s+[`'\"]?(\w[\w-]*)[`'\"]?\s+(?:sum|total)\s+[`'\"]?(\w[\w-]*)[`'\"]?",
                q,
            ):
                ans = self._streaming_groupby_sum(m.group(1), m.group(2))
                if ans:
                    return ans
            if re.search(r"\b(describe|statistics|stats|summary)\b", q):
                return self.describe_stats()

        df = self.dataframe()
        if df is None or df.empty:
            if re.search(r"\b(what columns|column names|list columns)\b", q) and self.dataset:
                cols = self.dataset.get("columns") or []
                return "Columns: " + ", ".join(f"`{c}`" for c in cols)
            return None

        import pandas as pd

        if m := re.search(
            r"\b(?:what(?:'s| is)\s+the\s+)?(?:average|mean|avg)(?:\s+(?:of|for))?\s+(?:the\s+)?[`'\"]?(\w[\w-]*)[`'\"]?",
            q,
        ):
            col = self._resolve_column(m.group(1), df)
            if col:
                s = pd.to_numeric(df[col], errors="coerce")
                return f"Average **{col}**: **{s.mean():.4g}** (numeric values only)."

        if m := re.search(r"\b(?:sum|total)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
            col = self._resolve_column(m.group(1), df)
            if col:
                s = pd.to_numeric(df[col], errors="coerce")
                return f"Sum of **{col}**: **{s.sum():.4g}**."

        if m := re.search(r"\b(?:max|maximum|highest)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
            col = self._resolve_column(m.group(1), df)
            if col:
                return f"Max **{col}**: **{df[col].max()}**."

        if m := re.search(r"\b(?:min|minimum|lowest)\s+(?:of\s+)?[`'\"]?(\w[\w-]*)[`'\"]?", q):
            col = self._resolve_column(m.group(1), df)
            if col:
                return f"Min **{col}**: **{df[col].min()}**."

        if m := re.search(
            r"\bgroup\s+by\s+[`'\"]?(\w[\w-]*)[`'\"]?\s+(?:sum|total)\s+[`'\"]?(\w[\w-]*)[`'\"]?",
            q,
        ):
            g, v = self._resolve_column(m.group(1), df), self._resolve_column(m.group(2), df)
            if g and v:
                tmp = df.copy()
                tmp[v] = pd.to_numeric(tmp[v], errors="coerce")
                out = tmp.groupby(g)[v].sum()
                return f"Group by **{g}**, sum **{v}**:\n```\n{out.head(20).to_string()}\n```"

        if re.search(r"\b(describe|statistics|stats|summary)\b", q):
            return self.describe_stats()

        return None

    @staticmethod
    def _to_numeric(val):
        try:
            return float(val)
        except (TypeError, ValueError):
            return float("nan")

    def _resolve_column(self, name: str, df) -> str | None:
        if name in df.columns:
            return name
        lower = name.lower()
        for c in df.columns:
            if str(c).lower() == lower:
                return c
        return None

    def _clean_streaming(self, instruction: str) -> tuple[str, int]:
        """Stream-clean large CSV/JSONL via sqlite scratch DB."""
        import sqlite3

        import pandas as pd

        if not self.dataset_path:
            return "ERROR: No dataset path.", 0
        lower = instruction.lower()
        STREAM_DIR.mkdir(parents=True, exist_ok=True)
        tmp_db = STREAM_DIR / f"{self.dataset_path.stem}_clean.db"
        if tmp_db.exists():
            tmp_db.unlink()
        conn = sqlite3.connect(str(tmp_db))
        table = "data"
        ds = self._require_dataset()
        before = int(ds.get("row_count") or 0)
        try:
            for chunk in self._pandas_chunks():
                if "drop null" in lower or "remove null" in lower:
                    chunk = chunk.dropna()
                if re.search(r"\bfill\s+nulls?\b", lower):
                    chunk = chunk.fillna(0)
                chunk.to_sql(table, conn, if_exists="append", index=False)
            if re.search(r"\b(drop|remove)\s+duplicate", lower) or "duplicate" in lower:
                conn.execute(f"CREATE TABLE clean AS SELECT DISTINCT * FROM {table}")
                conn.execute(f"DROP TABLE {table}")
                conn.execute("ALTER TABLE clean RENAME TO data")
                table = "data"
            after = int(conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            out = EXPORT_DIR / f"{self.dataset_path.stem}_cleaned_{stamp}.csv"
            EXPORT_DIR.mkdir(parents=True, exist_ok=True)
            first_write = True
            offset = 0
            while True:
                rows = conn.execute(
                    f"SELECT * FROM {table} LIMIT {CHUNK_SIZE} OFFSET {offset}"
                ).fetchall()
                if not rows:
                    break
                cols = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
                chunk_df = pd.DataFrame(rows, columns=cols)
                chunk_df.to_csv(out, mode="w" if first_write else "a", header=first_write, index=False)
                first_write = False
                offset += CHUNK_SIZE
        finally:
            conn.close()
            tmp_db.unlink(missing_ok=True)

        self.load_dataset(str(out))
        return f"Stream-cleaned file → **{out.name}** ({before} → {after} rows).", max(0, before - after)

    def clean(self, instruction: str = "") -> tuple[str, int]:
        """Clean dataset; returns (summary, rows_affected)."""
        ds = self.dataset
        if self._streaming and ds and ds.get("type") in ("csv", "json"):
            return self._clean_streaming(instruction)
        df = self.dataframe()
        if df is None:
            return "ERROR: No tabular dataset loaded.", 0
        before = len(df)
        lower = instruction.lower()

        if re.search(r"\b(drop|remove)\s+duplicate", lower) or "duplicate" in lower:
            df = df.drop_duplicates()

        for col in df.columns:
            if re.search(rf"\bfill\s+nulls?\s+in\s+{re.escape(str(col))}\b", lower, re.I):
                df[col] = df[col].fillna(0)
            elif re.search(r"\bfill\s+nulls?\b", lower) and col == df.columns[0]:
                df = df.fillna(0)

        if "drop null" in lower or "remove null" in lower:
            df = df.dropna()

        self._sync_dataset_from_df(df)
        return f"Cleaned dataset: {before} → {len(df)} rows.", before - len(df)

    def _sync_dataset_from_df(self, df) -> None:
        ds = self._require_dataset()
        rows = df.astype(object).where(df.notnull(), None).to_dict(orient="records")
        ds["rows"] = rows
        ds["row_count"] = len(rows)
        ds["columns"] = list(df.columns)

    def _sqlite_numeric_agg(self, column: str, op: str) -> str | None:
        import sqlite3

        ds = self.dataset
        if not self.dataset_path or not ds or ds.get("type") != "sqlite":
            return None
        table = ds.get("table")
        col = self._resolve_column_name(column, ds.get("columns") or [])
        if not table or not col:
            return None
        sql_map = {
            "mean": f"SELECT AVG([{col}]) FROM [{table}]",
            "sum": f"SELECT SUM([{col}]) FROM [{table}]",
            "min": f"SELECT MIN([{col}]) FROM [{table}]",
            "max": f"SELECT MAX([{col}]) FROM [{table}]",
        }
        query = sql_map.get(op)
        if not query:
            return None
        conn = sqlite3.connect(str(self.dataset_path))
        try:
            val = conn.execute(query).fetchone()[0]
        finally:
            conn.close()
        if val is None:
            return None
        labels = {"mean": "Average", "sum": "Sum of", "min": "Min", "max": "Max"}
        return f"{labels[op]} **{col}**: **{val}** (full database)."

    def _export_streaming(self, dest: Path, fmt: str) -> str:
        """Write full file to export path in chunks."""
        import shutil

        src = self.dataset_path
        if not src:
            return "ERROR: No dataset path."
        ds = self.dataset
        if fmt == "csv" and dest.suffix.lower() == ".csv" and ds and ds.get("type") == "csv":
            shutil.copy2(src, dest)
            return str(dest)
        first_chunk = True
        if dest.suffix.lower() == ".csv" or fmt == "csv":
            for chunk in self._pandas_chunks():
                chunk.to_csv(dest, mode="w" if first_chunk else "a", header=first_chunk, index=False)
                first_chunk = False
        else:
            with open(dest, "w", encoding="utf-8") as f:
                f.write("[\n")
                first_rec = True
                for chunk in self._pandas_chunks():
                    for rec in chunk.to_dict(orient="records"):
                        if not first_rec:
                            f.write(",\n")
                        f.write(json.dumps(rec, default=str))
                        first_rec = False
                f.write("\n]\n")
        if first_chunk:
            return "ERROR: Nothing to export."
        return str(dest)

    @staticmethod
    def _plain_text(text: str) -> str:
        return re.sub(r"\*\*([^*]+)\*\*", r"\1", text or "")

    def _latest_chart_path(self, chart_path: str | None = None) -> str | None:
        if chart_path and Path(chart_path).exists():
            return chart_path
        if self._last_chart_path and Path(self._last_chart_path).exists():
            return self._last_chart_path
        if CHART_DIR.exists():
            charts = sorted(CHART_DIR.glob("chart_*.png"), key=lambda p: p.stat().st_mtime, reverse=True)
            if charts:
                return str(charts[0])
        return None

    def export_pdf(self, dest: Path, chart_path: str | None = None) -> str:
        """Build a shareable PDF report: summary, preview table, optional chart."""
        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_pdf import PdfPages
        except ImportError:
            return "ERROR: Install matplotlib for PDF export: pip install matplotlib"

        if not self.dataset:
            return "ERROR: No dataset loaded."

        dest = Path(dest)
        dest.parent.mkdir(parents=True, exist_ok=True)
        name = self.dataset_path.name if self.dataset_path else "dataset"
        generated = datetime.now().strftime("%Y-%m-%d %H:%M")
        stats = self._plain_text(self.describe_stats())
        cols = self.dataset.get("columns") or []
        preview_rows = (self.dataset.get("rows") or [])[:30]
        row_count = self.dataset.get("row_count", len(preview_rows))

        meta_lines = [
            f"File: {name}",
            f"Rows: {row_count:,}" if isinstance(row_count, int) else f"Rows: {row_count}",
            f"Columns: {len(cols)}",
            f"Generated: {generated}",
        ]
        if self.dataset.get("streaming"):
            meta_lines.append("Mode: streaming (preview rows shown below)")
        if self.dataset.get("file_size"):
            meta_lines.append(f"Size: {_human_size(int(self.dataset['file_size']))}")

        with PdfPages(dest) as pdf:
            fig = plt.figure(figsize=(8.5, 11))
            fig.text(0.5, 0.72, f"{assistant_name()} Data Report", ha="center", fontsize=20, weight="bold")
            fig.text(0.5, 0.62, name, ha="center", fontsize=14)
            y = 0.48
            for line in meta_lines:
                fig.text(0.5, y, line, ha="center", fontsize=11)
                y -= 0.05
            fig.text(0.5, 0.08, f"{assistant_name()} · local data analysis", ha="center", fontsize=9, color="#666")
            pdf.savefig(fig, bbox_inches="tight")
            plt.close(fig)

            wrapped = textwrap.wrap(stats, width=100) or [stats]
            chunk_size = 42
            for i in range(0, len(wrapped), chunk_size):
                block = wrapped[i : i + chunk_size]
                fig = plt.figure(figsize=(8.5, 11))
                title = "Summary & statistics" if i == 0 else "Summary (continued)"
                fig.text(0.08, 0.94, title, fontsize=14, weight="bold")
                fig.text(0.08, 0.90, "\n".join(block), fontsize=8, family="monospace", va="top")
                pdf.savefig(fig, bbox_inches="tight")
                plt.close(fig)

            if cols and preview_rows:
                per_page = 18
                for page_start in range(0, len(preview_rows), per_page):
                    page_rows = preview_rows[page_start : page_start + per_page]
                    fig, ax = plt.subplots(figsize=(11, 8.5))
                    ax.axis("off")
                    label = "Data preview"
                    if page_start:
                        label += f" (rows {page_start + 1}+)"
                    ax.set_title(label, fontsize=12, loc="left", pad=12)
                    cell_text = [[str(r.get(c, ""))[:48] for c in cols] for r in page_rows]
                    table = ax.table(
                        cellText=cell_text,
                        colLabels=[str(c)[:24] for c in cols],
                        loc="upper center",
                        cellLoc="left",
                    )
                    table.auto_set_font_size(False)
                    table.set_fontsize(7)
                    table.scale(1, 1.15)
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close(fig)

            chart = self._latest_chart_path(chart_path)
            if chart:
                try:
                    img = plt.imread(chart)
                    fig, ax = plt.subplots(figsize=(11, 8.5))
                    ax.imshow(img)
                    ax.axis("off")
                    ax.set_title("Chart", fontsize=12, loc="left")
                    pdf.savefig(fig, bbox_inches="tight")
                    plt.close(fig)
                except Exception:
                    pass

        return str(dest)

    def export(self, out_path: str | None = None, fmt: str = "csv", chart_path: str | None = None) -> str:
        if not self.dataset:
            return "ERROR: No tabular dataset to export."
        EXPORT_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        stem = self.dataset_path.stem if self.dataset_path else "export"
        if out_path:
            dest = fs.resolve_path(out_path, base=DATA_DIR)
        else:
            ext = { "csv": ".csv", "json": ".json", "pdf": ".pdf" }.get(fmt, ".csv")
            dest = EXPORT_DIR / f"{stem}_{stamp}{ext}"
        dest.parent.mkdir(parents=True, exist_ok=True)

        if fmt == "pdf" or dest.suffix.lower() == ".pdf":
            return self.export_pdf(dest, chart_path=chart_path)

        if self._streaming and self.dataset.get("rows") is not None:
            return self._export_streaming(dest, fmt)

        rows = self.dataset.get("rows") or []
        if not rows:
            return "ERROR: No tabular dataset to export."
        cols = self.dataset.get("columns") or list(rows[0].keys())
        if dest.suffix.lower() == ".csv":
            with open(dest, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
                w.writeheader()
                w.writerows(rows)
        else:
            dest.write_text(json.dumps(rows, indent=2, default=str), encoding="utf-8")
        return str(dest)

    def chart(self, column: str | None = None, chart_type: str = "bar") -> str:
        if not self.dataset or not self.dataset.get("rows"):
            return "ERROR: No tabular dataset loaded."
        try:
            import matplotlib
            matplotlib.use("Agg")
            from collections import Counter

            import matplotlib.pyplot as plt

            df = self.dataframe()
            rows = self.dataset["rows"]
            cols = self.dataset.get("columns") or list(rows[0].keys())
            col = column or cols[0]
            if df is not None and col not in df.columns:
                col = self._resolve_column(col, df) or cols[0]

            if self._streaming:
                values = self._stream_column_values(col)
            else:
                values = [r.get(col, "") for r in rows if r.get(col) not in (None, "")]
            safe_col = re.sub(r"[^\w-]", "_", str(col))[:40]
            out = CHART_DIR / f"chart_{safe_col}_{chart_type}.png"
            out.parent.mkdir(parents=True, exist_ok=True)

            plt.figure(figsize=(9, 4.5))
            if chart_type == "line":
                import pandas as pd
                if self._streaming:
                    nums = pd.to_numeric(pd.Series(self._stream_column_values(col, 5000)), errors="coerce").dropna()
                elif df is not None and col in df.columns:
                    nums = pd.to_numeric(df[col], errors="coerce").dropna()
                else:
                    nums = pd.Series(dtype=float)
                if not nums.empty:
                    plt.plot(nums.to_numpy()[:80])
                plt.title(f"{col} (line)")
            elif chart_type == "pie":
                counts = Counter(str(v) for v in values[:40])
                labels, sizes = zip(*counts.most_common(12)) if counts else ([], [])
                if labels:
                    plt.pie(sizes, labels=labels, autopct="%1.0f%%")
                plt.title(f"{col} (pie)")
            elif chart_type == "hist":
                import pandas as pd
                if self._streaming:
                    nums = pd.to_numeric(pd.Series(self._stream_column_values(col, 100000)), errors="coerce").dropna()
                elif df is not None and col in df.columns:
                    nums = pd.to_numeric(df[col], errors="coerce").dropna()
                else:
                    nums = pd.Series(dtype=float)
                if not nums.empty:
                    plt.hist(nums, bins=min(20, max(5, len(nums) // 5)))
                plt.title(f"{col} (histogram)")
            else:
                counts = Counter(str(v) for v in values[:40])
                labels, sizes = zip(*counts.most_common(15)) if counts else ([], [])
                plt.bar(labels, sizes)
                plt.xticks(rotation=45, ha="right")
                plt.title(f"{col} ({chart_type})")
            plt.tight_layout()
            plt.savefig(out, dpi=120)
            plt.close()
            self._last_chart_path = str(out)
            return str(out)
        except Exception as e:
            return f"ERROR: {e}"

    def handle(self, prompt: str) -> bool:
        if prompt.lower() == "exit":
            return False

        if prompt.startswith("load "):
            result = self.load_dataset(prompt[5:].strip())
            if result.startswith("ERROR:"):
                print(f"\n{result}\n")
            else:
                print(f"\nDataset loaded: {self.dataset_path}\n")
                print(self.describe_stats())
                print()
            return True

        if prompt == "summary":
            print(f"\n{self.describe_stats()}\n")
            return True

        if prompt.startswith("query "):
            if not self.dataset:
                print("\nNo dataset loaded. Use: load <path>\n")
                return True
            question = prompt[6:].strip()
            computed = self.compute_answer(question)
            if computed:
                print(f"\n{computed}\n")
                return True
            context = self.describe_stats()
            answer = llm.ask(llm.general_model(), [{
                "role": "user",
                "content": f"Dataset:\n{context}\n\nQuestion: {question}",
            }])
            print()
            print(answer)
            print()
            return True

        if prompt.startswith("export "):
            out = prompt[7:].strip() or None
            path = self.export(out)
            print(f"\n{path}\n" if not path.startswith("ERROR") else f"\n{path}\n")
            return True

        if prompt.startswith("clean"):
            summary, _ = self.clean(prompt)
            print(f"\n{summary}\n")
            return True

        if prompt == "clear":
            self.dataset = None
            self.dataset_path = None
            self.conversation.clear()
            print("\nDataset cleared.\n")
            return True

        if not self.dataset:
            print("\nLoad a dataset first: load <path.csv|json>\n")
            return True

        self.conversation.add_system(self._summary())
        self.conversation.add_user(prompt)
        answer = llm.ask(llm.general_model(), self.conversation.messages)
        self.conversation.add_assistant(answer)
        print()
        print(answer)
        print()
        return True


def main():
    engine = DataEngine()
    print("\nJarvis Data Analyst")
    print("Type 'exit' to quit.")
    print("Commands:")
    print("  load <path>     load CSV, JSON, XLSX, or SQLite")
    print("  summary         show dataset overview")
    print("  query <question> ask about the data")
    print("  export [path]   export rows to CSV/JSON/PDF report")
    print("  clean           drop duplicates / fill nulls")
    print("  clear           unload dataset\n")

    while True:
        try:
            prompt = input("Data > ")
            if not engine.handle(prompt):
                break
        except KeyboardInterrupt:
            print("\n")
            break
        except Exception as e:
            print(f"\nERROR: {e}\n")
