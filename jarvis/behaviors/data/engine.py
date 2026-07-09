"""Data action implementations — load, query, chart, export, and SQL."""

from __future__ import annotations

import re
from pathlib import Path

from jarvis import llm
from jarvis.behaviors.data.context import DataContext
from jarvis.response import err, ok


class DataActionEngine:
    @staticmethod
    def _data_ok(ctx: DataContext, answer: str, **extra) -> dict:
        preview = ctx.data.preview() if ctx.data.dataset else {}
        if preview:
            extra.setdefault("data_preview", preview)
            extra.setdefault("data_path", preview.get("path", ""))
        return ok(answer, module="data", **extra)

    @classmethod
    def _ensure_loaded(cls, ctx: DataContext, message: str) -> dict | None:
        if ctx.data.dataset:
            return None
        if not ctx.session.last_data_path:
            return err("No dataset loaded — attach a CSV, JSON, XLSX, or SQLite file.")
        loaded = cls.data_load(ctx, {"path": ctx.session.last_data_path}, message)
        if not loaded.get("ok"):
            return loaded
        return None

    @classmethod
    def data_load(cls, ctx: DataContext, params: dict, message: str) -> dict:
        path = ctx.session.resolve_data(params.get("path", ""))
        if not path:
            return err("Which data file should I load? Attach one or give me a path.")
        result = ctx.data.load_dataset(path)
        if result.startswith("ERROR:"):
            return err(result)
        ctx.session.note_data(path)
        ctx.session.note_module("data")
        summary = ctx.data.describe_stats()
        return cls._data_ok(
            ctx,
            f"I've loaded **{Path(path).name}**.\n\n{summary}\n\n"
            "Try: row count, average of a column, chart, export, or clean duplicates.",
        )

    @classmethod
    def data_query(cls, ctx: DataContext, params: dict, message: str) -> dict:
        load_err = cls._ensure_loaded(ctx, message)
        if load_err:
            return load_err
        question = params.get("question") or message
        computed = ctx.data.compute_answer(question)
        if computed:
            return cls._data_ok(ctx, computed)
        context = ctx.data.describe_stats()
        answer = llm.ask(
            llm.general_model(),
            [{
                "role": "user",
                "content": f"Dataset:\n{context}\n\nQuestion: {question}\n\nAnswer from the data only.",
            }],
        )
        return cls._data_ok(ctx, answer)

    @classmethod
    def data_summary(cls, ctx: DataContext, params: dict, message: str) -> dict:
        load_err = cls._ensure_loaded(ctx, message)
        if load_err:
            return load_err
        return cls._data_ok(ctx, ctx.data.describe_stats())

    @classmethod
    def data_clean(cls, ctx: DataContext, params: dict, message: str) -> dict:
        load_err = cls._ensure_loaded(ctx, message)
        if load_err:
            return load_err
        instruction = params.get("instruction") or message
        summary, _ = ctx.data.clean(instruction)
        if summary.startswith("ERROR"):
            return err(summary)
        return cls._data_ok(ctx, f"{summary}\n\n{ctx.data.describe_stats()}")

    @classmethod
    def data_export(cls, ctx: DataContext, params: dict, message: str) -> dict:
        load_err = cls._ensure_loaded(ctx, message)
        if load_err:
            return load_err
        if re.search(r"\bpdf\b", message, re.I):
            fmt = "pdf"
        elif re.search(r"\bjson\b", message, re.I):
            fmt = "json"
        else:
            fmt = "csv"
        match = re.search(r"\bto\s+[`'\"]?([^\s`'\"]+\.(?:csv|json|pdf))[`'\"]?", message, re.I)
        out = match.group(1) if match else None
        path = ctx.data.export(out, fmt=fmt)
        if path.startswith("ERROR"):
            return err(path)
        return cls._data_ok(ctx, f"Exported **{Path(path).name}** to `{path}`", export_path=path)

    @classmethod
    def data_chart(cls, ctx: DataContext, params: dict, message: str) -> dict:
        load_err = cls._ensure_loaded(ctx, message)
        if load_err:
            return load_err
        from jarvis.modules.data import parse_chart_request

        spec = parse_chart_request(message)
        column = params.get("column") or spec.get("column")
        chart_type = params.get("chart_type") or spec.get("chart_type") or "bar"
        result = ctx.data.chart(column or None, chart_type=chart_type)
        if result.startswith("ERROR:"):
            return err(result)
        label = f"**{column}** ({chart_type})" if column else chart_type
        return cls._data_ok(ctx, f"Chart for {label}:", chart_path=result)

    @classmethod
    def data_sql(cls, ctx: DataContext, params: dict, message: str) -> dict:
        if not ctx.data.dataset:
            loaded = cls.data_load(ctx, {"path": ctx.session.last_data_path}, message)
            if not loaded.get("ok"):
                return loaded
        query = params.get("query") or message
        if not query.strip().upper().startswith("SELECT"):
            match = re.search(r"(SELECT\s+.+)", message, re.I | re.S)
            query = match.group(1) if match else query
        result = ctx.data.sql_query(query)
        if result.startswith("ERROR:"):
            return err(result)
        return ok(f"**Query results:**\n\n```json\n{result[:6000]}\n```", module="data")
