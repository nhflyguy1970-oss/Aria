"""Export router training JSONL from registered actions."""

from __future__ import annotations

import json
import logging
import os
import subprocess
from pathlib import Path

from jarvis.config import DATA_DIR

log = logging.getLogger("jarvis.router_training")

OUT = DATA_DIR / "router_training.jsonl"
FG_OUT = DATA_DIR / "functiongemma_training.jsonl"
MODELFILE = DATA_DIR / "router.Modelfile"


def export_training_jsonl() -> Path:
    from jarvis.handlers import ensure_handlers_loaded
    from jarvis.handlers.registry import all_actions

    ensure_handlers_loaded()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for row in all_actions():
        name = row.get("action") or ""
        if row.get("info") or not row.get("registered"):
            continue
        user = f"Please {(row.get('description') or name.replace('_', ' ')).strip()}"
        assistant = json.dumps(
            {"action": name, "params": {}, "thinking": row.get("module") or "tool"}
        )
        row = {
            "messages": [
                {"role": "user", "content": user},
                {"role": "assistant", "content": assistant},
            ]
        }
        lines.append(json.dumps(row, ensure_ascii=False))
    OUT.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return OUT


def _functiongemma_training_samples() -> dict[str, list[tuple[str, str]]]:
    """Core router actions → (user utterance, call body) for fine-tune."""
    return {
        "planner_set_timer": [
            ("set a timer for 5 minutes", "call:planner_set_timer{duration: 5 minutes}"),
            ("timer 10 minutes", "call:planner_set_timer{duration: 10 minutes}"),
            ("start a countdown for 30 seconds", "call:planner_set_timer{duration: 30 seconds}"),
            ("set a timer for one hour", "call:planner_set_timer{duration: 1 hour}"),
            ("five minute timer", "call:planner_set_timer{duration: 5 minutes}"),
        ],
        "planner_set_alarm": [
            ("wake me at 7am", "call:planner_set_alarm{time: 7am}"),
            ("set an alarm for 6:30 tomorrow", "call:planner_set_alarm{time: 6:30 tomorrow}"),
            ("alarm at 8am", "call:planner_set_alarm{time: 8am}"),
        ],
        "planner_add_task": [
            ("add task buy milk", "call:planner_add_task{text: buy milk}"),
            ("add a task call dentist", "call:planner_add_task{text: call dentist}"),
            ("task pick up dry cleaning", "call:planner_add_task{text: pick up dry cleaning}"),
        ],
        "planner_today": [
            ("what's on my planner today", "call:planner_today{}"),
            ("planner today", "call:planner_today{}"),
            ("today's schedule", "call:planner_today{}"),
        ],
        "morning_briefing": [
            ("good morning briefing", "call:morning_briefing{}"),
            ("good morning", "call:morning_briefing{}"),
            ("morning briefing please", "call:morning_briefing{}"),
        ],
        "curated_briefing": [
            ("news briefing", "call:curated_briefing{}"),
            ("curated news", "call:curated_briefing{}"),
            ("tech headlines", "call:curated_briefing{}"),
        ],
        "ha_control": [
            ("turn on office lights", "call:ha_control{target: office lights, action: on}"),
            ("turn off the lab lights", "call:ha_control{target: lab lights, action: off}"),
            ("toggle bedroom lamp", "call:ha_control{target: bedroom lamp, action: toggle}"),
            ("turn on the lights", "call:ha_control{target: lights, action: on}"),
            ("turn off the bedroom lights", "call:ha_control{target: bedroom lights, action: off}"),
            ("turn on the living room lights", "call:ha_control{target: living room lights, action: on}"),
        ],
        "ha_status": [
            ("smart home status", "call:ha_status{}"),
            ("home assistant status", "call:ha_status{}"),
        ],
        "web_search": [
            ("search for latest AI news", "call:web_search{query: latest AI news}"),
            ("search the web for python 3.13 release", "call:web_search{query: python 3.13 release}"),
        ],
        "weather_forecast": [
            ("weather in Austin", "call:weather_forecast{location: Austin}"),
            ("forecast for Boston", "call:weather_forecast{location: Boston}"),
        ],
        "generate_cad": [
            ("design a hose adapter", "call:generate_cad{prompt: hose adapter}"),
            ("generate a cad bracket for the shelf", "call:generate_cad{prompt: bracket for the shelf}"),
            ("create an stl phone stand", "call:generate_cad{prompt: phone stand}"),
            ("make a 3d part cup holder", "call:generate_cad{prompt: cup holder}"),
        ],
        "iterate_cad": [
            ("make it taller", "call:iterate_cad{prompt: make it taller}"),
            ("iterate the design add mounting holes", "call:iterate_cad{prompt: add mounting holes}"),
            ("modify the cad make the walls thinner", "call:iterate_cad{prompt: make the walls thinner}"),
            ("change the model to be wider", "call:iterate_cad{prompt: make it wider}"),
            ("make it thicker", "call:iterate_cad{prompt: make it thicker}"),
            ("edit the design round the corners", "call:iterate_cad{prompt: round the corners}"),
        ],
        "audio_stop": [
            ("stop audio", "call:audio_stop{}"),
            ("stop playback", "call:audio_stop{}"),
            ("stop speaking", "call:audio_stop{}"),
        ],
        "audio_pause": [
            ("pause audio", "call:audio_pause{}"),
            ("pause playback", "call:audio_pause{}"),
        ],
        "system_info": [
            ("system status", "call:system_info{}"),
            ("what's running", "call:system_info{}"),
            ("gpu status", "call:system_info{}"),
        ],
        "chat": [
            ("hello", "call:chat{}"),
            ("thanks", "call:chat{}"),
            ("how are you", "call:chat{}"),
        ],
        "thinking": [
            ("explain step by step why recursion overflows", "call:thinking{}"),
            ("debug this pytest failure", "call:thinking{}"),
        ],
        "nonthinking": [
            ("hi there", "call:nonthinking{}"),
            ("quick question", "call:nonthinking{}"),
        ],
    }


def _functiongemma_example(action: str, description: str) -> tuple[str, str]:
    """Return (user utterance, function_call target) for a single training row."""
    samples = _functiongemma_training_samples()
    if action in samples:
        return samples[action][0]
    desc = (description or action.replace("_", " ")).strip()
    return f"please {desc}", f"call:{action}{{}}"


_ADA_SKIP_ACTIONS = frozenset({"create_calendar_event"})


def _ada_training_paths() -> list[Path]:
    raw = (os.getenv("JARVIS_FG_ADA_PATHS") or "").strip()
    if raw:
        return [Path(p.strip()) for p in raw.split(":") if p.strip()]
    defaults = [
        Path("/media/jeff/USB/ada_local-main/training_dataset_functions.jsonl"),
        Path("/media/jeff/USB/ada_local-main/training_dataset.jsonl"),
    ]
    return [p for p in defaults if p.is_file()]


def _format_fg_call(action: str, params: dict[str, object]) -> str:
    parts: list[str] = []
    for key, value in params.items():
        if value is None or value == "":
            continue
        parts.append(f"{key}: {value}")
    inner = ", ".join(parts)
    return f"call:{action}{{{inner}}}"


def _map_ada_tool_call(name: str, arguments: dict[str, object]) -> tuple[str, dict[str, object]] | None:
    args = dict(arguments or {})
    if name == "control_light":
        target = str(args.get("device_name") or args.get("device") or "lights")
        action = str(args.get("action") or "toggle")
        out: dict[str, object] = {"target": target, "action": action}
        if args.get("color"):
            out["color"] = args["color"]
        if args.get("brightness") is not None:
            out["brightness"] = args["brightness"]
        return "ha_control", out
    if name == "set_timer":
        return "planner_set_timer", {
            "duration": args.get("duration") or "",
            **({"label": args["label"]} if args.get("label") else {}),
        }
    if name == "set_alarm":
        return "planner_set_alarm", {
            "time": args.get("time") or "",
            **({"label": args["label"]} if args.get("label") else {}),
        }
    if name == "add_task":
        return "planner_add_task", {"text": args.get("text") or ""}
    if name == "web_search":
        return "web_search", {"query": args.get("query") or ""}
    if name == "get_system_info":
        return "system_info", {}
    if name in ("thinking", "nonthinking"):
        return name, {}
    return None


def _parse_ada_row(row: dict) -> tuple[str, str] | None:
    messages = row.get("messages") or []
    user = ""
    for msg in messages:
        if isinstance(msg, dict) and msg.get("role") == "user":
            user = str(msg.get("content") or "").strip()
            break
    if not user:
        return None
    for msg in messages:
        if not isinstance(msg, dict) or msg.get("role") != "assistant":
            continue
        tool_calls = msg.get("tool_calls") or []
        if not tool_calls:
            continue
        tc = tool_calls[0] if isinstance(tool_calls[0], dict) else {}
        fn = tc.get("function") if isinstance(tc.get("function"), dict) else {}
        ada_name = str(fn.get("name") or "").strip()
        if not ada_name or ada_name in _ADA_SKIP_ACTIONS:
            return None
        mapped = _map_ada_tool_call(ada_name, fn.get("arguments") or {})
        if not mapped:
            return None
        action, params = mapped
        if action == "planner_add_task" and not str(params.get("text") or "").strip():
            return None
        if action == "planner_set_timer" and not str(params.get("duration") or "").strip():
            return None
        if action == "planner_set_alarm" and not str(params.get("time") or "").strip():
            return None
        if action == "web_search" and not str(params.get("query") or "").strip():
            return None
        return user, _format_fg_call(action, params)
    return None


def load_ada_training_rows() -> list[tuple[str, str]]:
    """Load Ada FunctionGemma rows from USB paths, mapped to ARIA router actions."""
    if os.getenv("JARVIS_FG_IMPORT_ADA", "1").strip().lower() in ("0", "false", "no"):
        return []
    rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for path in _ada_training_paths():
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            log.warning("Ada training path unreadable %s: %s", path, exc)
            continue
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            parsed = _parse_ada_row(row)
            if not parsed:
                continue
            key = (parsed[0].lower(), parsed[1])
            if key in seen:
                continue
            seen.add(key)
            rows.append(parsed)
    return rows


def export_functiongemma_jsonl(*, core_only: bool = True) -> Path:
    """Export FunctionGemma fine-tuning JSONL (tool-call targets)."""
    from jarvis.functiongemma_router import _ROUTER_ACTIONS, build_tool_schema

    FG_OUT.parent.mkdir(parents=True, exist_ok=True)
    tools = [build_tool_schema(a) for a in _ROUTER_ACTIONS]
    lines: list[str] = []
    core_samples = _functiongemma_training_samples()
    seen_rows: set[tuple[str, str]] = set()

    def append_row(user: str, call_body: str) -> None:
        key = (user.lower().strip(), call_body)
        if key in seen_rows:
            return
        seen_rows.add(key)
        assistant = f"<start_function_call>{call_body}<end_function_call>"
        lines.append(
            json.dumps(
                {
                    "messages": [
                        {
                            "role": "developer",
                            "content": "You are a model that can do function calling with the following functions",
                        },
                        {"role": "user", "content": user},
                        {"role": "assistant", "content": assistant},
                    ],
                    "tools": tools,
                },
                ensure_ascii=False,
            )
        )

    if core_only:
        for action in _ROUTER_ACTIONS:
            pairs = core_samples.get(action)
            if pairs:
                for user, call_body in pairs:
                    append_row(user, call_body)
            else:
                user, call_body = _functiongemma_example(action, "")
                append_row(user, call_body)
    else:
        from jarvis.handlers import ensure_handlers_loaded
        from jarvis.handlers.registry import all_actions

        ensure_handlers_loaded()
        for row in all_actions():
            name = row.get("action") or ""
            if row.get("info") or not row.get("registered"):
                continue
            user, call_body = _functiongemma_example(name, row.get("description") or "")
            append_row(user, call_body)

    ada_rows = load_ada_training_rows()
    for user, call_body in ada_rows:
        append_row(user, call_body)
    if ada_rows:
        log.info("Merged %d Ada training rows into FunctionGemma export", len(ada_rows))

    FG_OUT.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
    return FG_OUT


def train_functiongemma_router(*, output_dir: str | None = None) -> dict:
    """Export FG dataset and fine-tune when unsloth/transformers training is available."""
    path = export_functiongemma_jsonl()
    if not path.is_file() or path.stat().st_size == 0:
        return {"ok": False, "error": "No FunctionGemma training rows exported"}

    out = Path(output_dir or (DATA_DIR / "models" / "functiongemma-aria"))
    out.mkdir(parents=True, exist_ok=True)

    try:
        import torch
        import unsloth  # noqa: F401
        from datasets import load_dataset
        from trl import SFTTrainer
        from transformers import TrainingArguments
        from unsloth import FastLanguageModel

        model_id = (
            os.getenv("JARVIS_FUNCTIONGEMMA_BASE")
            or os.getenv("JARVIS_FUNCTIONGEMMA_MODEL")
            or "google/functiongemma-270m-it"
        )
        max_seq = int(os.getenv("JARVIS_FUNCTIONGEMMA_MAX_SEQ", "1024"))
        use_4bit = (
            os.getenv("JARVIS_FUNCTIONGEMMA_4BIT", "0").strip().lower() in ("1", "true", "yes")
            and not getattr(torch.version, "hip", None)
        )
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_id,
            max_seq_length=max_seq,
            load_in_4bit=use_4bit,
            dtype=None,
        )
        model = FastLanguageModel.get_peft_model(
            model,
            r=int(os.getenv("JARVIS_FUNCTIONGEMMA_LORA_R", "16")),
            lora_alpha=int(os.getenv("JARVIS_FUNCTIONGEMMA_LORA_ALPHA", "16")),
            target_modules=["q_proj", "k_proj", "v_proj", "o_proj"],
        )
        ds = load_dataset("json", data_files=str(path), split="train")

        def to_text(row):
            return {
                "text": tokenizer.apply_chat_template(
                    row["messages"],
                    tools=row.get("tools") or [],
                    tokenize=False,
                )
            }

        ds = ds.map(to_text, remove_columns=ds.column_names)
        epochs = int(os.getenv("JARVIS_FUNCTIONGEMMA_EPOCHS", "3"))
        use_bf16 = bool(getattr(torch.version, "hip", None)) or (
            torch.cuda.is_available() and torch.cuda.is_bf16_supported()
        )
        trainer = SFTTrainer(
            model=model,
            processing_class=tokenizer,
            train_dataset=ds,
            args=TrainingArguments(
                output_dir=str(out),
                per_device_train_batch_size=1,
                gradient_accumulation_steps=4,
                num_train_epochs=epochs,
                learning_rate=2e-4,
                logging_steps=5,
                save_steps=100,
                save_total_limit=1,
                report_to="none",
                fp16=False,
                bf16=use_bf16,
                gradient_checkpointing=True,
            ),
        )
        try:
            trainer.train()
        except Exception as train_exc:
            log.warning("trainer.train cleanup issue (checkpoint may still exist): %s", train_exc)
        ckpt = Path(trainer.state.best_model_checkpoint or "")
        if not ckpt.is_dir():
            checkpoints = sorted(out.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[-1]))
            ckpt = checkpoints[-1] if checkpoints else Path()
        if not ckpt.is_dir():
            return {"ok": False, "error": "Training produced no checkpoint", "exported": str(path)}
        merged = out / "merged"
        merged.mkdir(parents=True, exist_ok=True)
        try:
            from peft import PeftModel

            base_model, tok = FastLanguageModel.from_pretrained(
                model_name=model_id,
                max_seq_length=max_seq,
                load_in_4bit=False,
            )
            peft = PeftModel.from_pretrained(base_model, str(ckpt))
            merged_model = peft.merge_and_unload()
            merged_model.save_pretrained(str(merged))
            tok.save_pretrained(str(merged))
            save_dir = merged
        except Exception as merge_exc:
            log.warning("merge failed, saving adapter only: %s", merge_exc)
            save_dir = ckpt
        return {
            "ok": True,
            "path": str(save_dir),
            "adapter_path": str(ckpt),
            "rows": len(ds),
            "backend": "unsloth",
            "base_model": model_id,
            "hint": f"Set JARVIS_FUNCTIONGEMMA_MODEL={save_dir}",
        }
    except ImportError as exc:
        return {
            "ok": True,
            "exported": str(path),
            "rows": len(path.read_text(encoding="utf-8").splitlines()),
            "backend": "export_only",
            "hint": (
                "Install unsloth + trl for local fine-tune, or upload "
                f"{path} to Colab (google-gemma/functiongemma fine-tuning guide). "
                "Then set JARVIS_FUNCTIONGEMMA_MODEL to the saved folder."
            ),
            "import_error": str(exc),
        }
    except Exception as exc:
        log.warning("FunctionGemma train failed: %s", exc)
        return {"ok": False, "error": str(exc), "exported": str(path)}


def train_router_model(*, name: str = "jarvis-router") -> dict:
    """Build Ollama Modelfile from exported JSONL and run `ollama create`."""
    from jarvis.local_router import router_model

    path = export_training_jsonl()
    if not path.is_file() or path.stat().st_size == 0:
        return {"ok": False, "error": "No training rows exported"}

    examples: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
            msgs = row.get("messages") or []
            if len(msgs) >= 2:
                examples.append(
                    f"User: {msgs[0].get('content', '')}\nAssistant: {msgs[1].get('content', '')}"
                )
        except json.JSONDecodeError:
            continue
        if len(examples) >= 24:
            break

    base = router_model()
    body = [
        f"FROM {base}",
        "PARAMETER temperature 0",
        "PARAMETER num_predict 120",
        'SYSTEM You are a fast intent router. Reply with ONLY one JSON object.',
        "",
    ]
    for ex in examples:
        body.append(f"MESSAGE user {ex.split(chr(10))[0].replace('User: ', '')}")
        if "\n" in ex:
            body.append(f"MESSAGE assistant {ex.split(chr(10), 1)[1].replace('Assistant: ', '')}")
    MODELFILE.write_text("\n".join(body) + "\n", encoding="utf-8")

    try:
        proc = subprocess.run(
            ["ollama", "create", name, "-f", str(MODELFILE)],
            capture_output=True,
            text=True,
            timeout=600,
            check=False,
        )
        if proc.returncode != 0:
            return {
                "ok": False,
                "error": (proc.stderr or proc.stdout or "ollama create failed")[:400],
                "modelfile": str(MODELFILE),
            }
        return {"ok": True, "model": name, "modelfile": str(MODELFILE), "examples": len(examples)}
    except Exception as exc:
        log.warning("router train failed: %s", exc)
        return {"ok": False, "error": str(exc), "modelfile": str(MODELFILE)}
