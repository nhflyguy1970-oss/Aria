"""Cloud spending and disclosure policy — private and unpaid unless approved.

Two owner decisions gate every paid cloud call, and both are explicit:

* **Authorization** — a time-limited grant naming the provider, the ARIA roles
  it covers, a spending cap, and which context classes may be shared. No
  active authorization, no call. Authorizations are created only by the owner
  (API/CLI), never by ARIA itself.
* **Budget** — operator-set monthly caps (total and per provider), a per-task
  cap, and per-model prices. A call whose worst-case cost cannot be priced, or
  would exceed any cap, is refused before anything is sent. Defaults are all
  zero: nothing is billable until the owner sets a budget.

Disclosure: by default a cloud model receives only the current request and a
neutral instruction. Recent conversation, retrieved conversation history, ACM
memory, ARIA's system prompt and project context each need to be granted.
Health context is never sent. A payload containing any Owner Vault secret is
refused outright; other credential-shaped strings are redacted. Every
disclosure is recorded: which classes, how much, to which provider and model,
for which task — content itself is fingerprinted, not stored.

This module decides; ``jarvis.inference.gateway`` enforces at the call site and
``providers.base._send`` re-checks the reservation immediately before the
request leaves the machine.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import re
import sqlite3
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from jarvis.config import DATA_DIR
from jarvis.inference import boundary

DB_PATH = DATA_DIR / "cloud_ledger.db"
BUDGET_FILE = DATA_DIR / "cloud_budget.json"

# Context classes a grant may name.
CURRENT_TURN = "current_turn"
RECENT_CONVERSATION = "recent_conversation"
CONTINUITY = "continuity"
MEMORY = "memory"
SYSTEM_PROMPT = "system_prompt"
PROJECT = "project"
GRANTABLE = (CURRENT_TURN, RECENT_CONVERSATION, CONTINUITY, MEMORY, SYSTEM_PROMPT, PROJECT)
NEVER_SHARED = ("health",)

NEUTRAL_INSTRUCTION = (
    "You are assisting ARIA's owner with one request. Answer it directly. You have no "
    "access to their memory, files or history beyond what is included here."
)
RECENT_TURNS = 6


class PolicyRefused(boundary.CloudNotPermitted):
    """Not authorized, over budget, unpriced, or would disclose something private."""


class NotAuthorized(PolicyRefused):
    pass


class BudgetExceeded(PolicyRefused):
    pass


class Unpriced(PolicyRefused):
    pass


class SecretInPayload(PolicyRefused):
    pass


# ------------------------------------------------------------------ storage

_init_lock = threading.Lock()
_initialised: set[str] = set()


def _conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def _init() -> None:
    if str(DB_PATH) in _initialised and DB_PATH.exists():
        return
    with _init_lock:
        from jarvis.live_data_guard import assert_live_write_allowed

        assert_live_write_allowed(DB_PATH)
        with _conn() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS authorizations (
                    id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    roles TEXT NOT NULL,
                    context_classes TEXT NOT NULL,
                    max_cost_usd REAL NOT NULL,
                    spent_usd REAL NOT NULL DEFAULT 0,
                    created_at REAL NOT NULL,
                    expires_at REAL NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0,
                    note TEXT NOT NULL DEFAULT ''
                );
                CREATE TABLE IF NOT EXISTS usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    month TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    role TEXT NOT NULL,
                    authorization_id TEXT NOT NULL,
                    receipt_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    input_tokens INTEGER,
                    output_tokens INTEGER,
                    estimated_usd REAL,
                    billing TEXT NOT NULL DEFAULT 'api'
                );
                CREATE INDEX IF NOT EXISTS ix_usage_month ON usage(month, provider);
                CREATE TABLE IF NOT EXISTS disclosures (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ts REAL NOT NULL,
                    receipt_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    role TEXT NOT NULL,
                    authorization_id TEXT NOT NULL,
                    classes TEXT NOT NULL,
                    withheld TEXT NOT NULL,
                    chars INTEGER NOT NULL,
                    sha256 TEXT NOT NULL
                );
                """
            )
        _initialised.add(str(DB_PATH))


def reset_for_tests() -> None:
    _initialised.clear()


def _month(ts: float | None = None) -> str:
    return datetime.fromtimestamp(ts or time.time()).strftime("%Y-%m")


# ------------------------------------------------------------------ budget config


def load_budget() -> dict[str, Any]:
    """Operator budget. Missing file = zero budget: no paid calls at all."""
    defaults: dict[str, Any] = {
        "monthly_total_usd": 0.0,
        "per_task_max_usd": 0.0,
        "providers": {},  # {"anthropic": {"monthly_usd": 5.0}}
        "prices": {},  # {"anthropic/<model>": {"input_per_mtok": 3.0, "output_per_mtok": 15.0}}
    }
    try:
        data = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return defaults
    return {**defaults, **(data if isinstance(data, dict) else {})}


def _included_model(aria_model: str) -> bool:
    from jarvis.inference.providers import adapter_for, split_model
    from jarvis.inference.providers.gemini import FREE_TEXT_MODELS
    provider, model = split_model(aria_model)
    adapter = adapter_for(provider)
    return bool(adapter) and (
        provider == "google" and adapter.billing == "gemini_free_tier" and model in FREE_TEXT_MODELS
        or provider == "openai" and adapter.billing == "chatgpt_subscription"
    )


def _included_provider(provider: str) -> bool:
    from jarvis.inference.providers import adapter_for
    adapter = adapter_for(provider)
    return bool(adapter) and adapter.billing in ("gemini_free_tier", "chatgpt_subscription")


def estimate_cost(aria_model: str, input_tokens: int, output_tokens: int) -> float | None:
    if _included_model(aria_model):
        return 0.0
    price = (load_budget().get("prices") or {}).get(aria_model)
    if not isinstance(price, dict):
        return None
    try:
        return round(
            input_tokens / 1e6 * float(price["input_per_mtok"])
            + output_tokens / 1e6 * float(price["output_per_mtok"]),
            6,
        )
    except (KeyError, TypeError, ValueError):
        return None


def monthly_spend(provider: str | None = None, month: str | None = None) -> float:
    _init()
    sql = "SELECT COALESCE(SUM(estimated_usd), 0) FROM usage WHERE month=?"
    args: list[Any] = [month or _month()]
    if provider:
        sql += " AND provider=?"
        args.append(provider)
    with _conn() as conn:
        return float(conn.execute(sql, args).fetchone()[0] or 0.0)


# ------------------------------------------------------------------ authorizations


def create_authorization(
    provider: str,
    *,
    max_cost_usd: float,
    context_classes: list[str] | tuple[str, ...] = (CURRENT_TURN,),
    roles: list[str] | tuple[str, ...] = ("*",),
    expires_in_s: float = 3600.0,
    note: str = "",
) -> str:
    """Owner action. Never called by ARIA on its own behalf."""
    if provider not in ("openai", "anthropic", "google"):
        raise ValueError(f"unknown provider {provider!r}")
    classes = sorted(set(context_classes) | {CURRENT_TURN})
    bad = [c for c in classes if c not in GRANTABLE]
    if bad:
        raise ValueError(f"not grantable: {bad} (health and credentials are never shared)")
    if max_cost_usd < 0 or max_cost_usd == 0 and not _included_provider(provider):
        raise ValueError("zero-cost grants require an explicitly configured free/subscription provider")
    _init()
    aid = "auth_" + uuid.uuid4().hex[:12]
    now = time.time()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO authorizations (id, provider, roles, context_classes, max_cost_usd,
                   created_at, expires_at, note) VALUES (?,?,?,?,?,?,?,?)""",
            (aid, provider, json.dumps(list(roles)), json.dumps(classes), float(max_cost_usd),
             now, now + float(expires_in_s), note[:200]),
        )
    return aid


def revoke_authorization(authorization_id: str) -> bool:
    _init()
    with _conn() as conn:
        return conn.execute(
            "UPDATE authorizations SET revoked=1 WHERE id=?", (authorization_id,)
        ).rowcount > 0


def _auth_row(row: sqlite3.Row) -> dict[str, Any]:
    d = dict(row)
    d["roles"] = json.loads(d["roles"])
    d["context_classes"] = json.loads(d["context_classes"])
    d["remaining_usd"] = round(d["max_cost_usd"] - d["spent_usd"], 6)
    d["active"] = not d["revoked"] and d["expires_at"] > time.time() and (d["remaining_usd"] > 0 or d["max_cost_usd"] == 0 and _included_provider(d["provider"]))
    return d


def list_authorizations(*, active_only: bool = False) -> list[dict[str, Any]]:
    _init()
    with _conn() as conn:
        rows = [_auth_row(r) for r in conn.execute("SELECT * FROM authorizations ORDER BY created_at DESC")]
    return [r for r in rows if r["active"]] if active_only else rows


def active_authorization(provider: str, role: str) -> dict[str, Any] | None:
    for auth in list_authorizations(active_only=True):
        if auth["provider"] == provider and ("*" in auth["roles"] or role in auth["roles"]):
            return auth
    return None


# ------------------------------------------------------------------ reservations


@dataclass
class Reservation:
    id: str
    provider: str
    model: str  # aria id, e.g. "anthropic/<model>"
    role: str
    authorization_id: str
    context_classes: list[str]
    worst_case_usd: float


_current: contextvars.ContextVar[Reservation | None] = contextvars.ContextVar(
    "cloud_reservation", default=None
)


def preflight(provider: str, aria_model: str, role: str, *, input_tokens: int, max_output_tokens: int) -> Reservation:
    """Authorize and price a call before anything is sent. Raises PolicyRefused."""
    auth = active_authorization(provider, role)
    if auth is None:
        raise NotAuthorized(
            f"no active owner authorization for paid {provider} inference (role {role!r})"
        )
    worst = estimate_cost(aria_model, input_tokens, max_output_tokens)
    if worst is None:
        raise Unpriced(f"no price configured for {aria_model}; refusing an unbounded charge")
    budget = load_budget()
    limits = [("authorization", auth["remaining_usd"])]
    per_task = float(budget.get("per_task_max_usd") or 0)
    limits.append(("per-task cap", per_task))
    prov_cap = float(((budget.get("providers") or {}).get(provider) or {}).get("monthly_usd") or 0)
    limits.append((f"{provider} monthly cap", prov_cap - monthly_spend(provider)))
    total_cap = float(budget.get("monthly_total_usd") or 0)
    limits.append(("monthly total cap", total_cap - monthly_spend()))
    for name, remaining in limits:
        if worst > remaining:
            raise BudgetExceeded(
                f"estimated worst case ${worst:.4f} exceeds the {name} (${max(0.0, remaining):.4f} left)"
            )
    return Reservation(
        id=uuid.uuid4().hex[:12],
        provider=provider,
        model=aria_model,
        role=role,
        authorization_id=auth["id"],
        context_classes=list(auth["context_classes"]),
        worst_case_usd=worst,
    )


def activate(reservation: Reservation | None) -> contextvars.Token:
    return _current.set(reservation)


def deactivate(token: contextvars.Token) -> None:
    _current.reset(token)


def require_reservation(provider: str) -> Reservation:
    """Called immediately before paid traffic leaves the machine."""
    res = _current.get()
    if res is None or res.provider != provider:
        raise NotAuthorized(f"paid {provider} call without an authorized reservation")
    return res


def record_usage(
    reservation: Reservation,
    *,
    receipt_id: str,
    status: str,
    input_tokens: int | None,
    output_tokens: int | None,
) -> float:
    """Charge what was actually used (worst case when the provider did not say)."""
    if input_tokens is None and output_tokens is None and status != "completed":
        cost = 0.0 if status == "refused" else reservation.worst_case_usd
    else:
        cost = estimate_cost(reservation.model, int(input_tokens or 0), int(output_tokens or 0))
        cost = reservation.worst_case_usd if cost is None else cost
    from jarvis.inference.providers import adapter_for
    billing = adapter_for(reservation.provider).billing
    _init()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO usage (ts, month, provider, model, role, authorization_id, receipt_id,
                   status, input_tokens, output_tokens, estimated_usd, billing) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (time.time(), _month(), reservation.provider, reservation.model, reservation.role,
             reservation.authorization_id, receipt_id, status, input_tokens, output_tokens, cost, billing),
        )
        conn.execute(
            "UPDATE authorizations SET spent_usd = spent_usd + ? WHERE id=?",
            (cost, reservation.authorization_id),
        )
    return cost


def usage_rows(limit: int = 50) -> list[dict[str, Any]]:
    _init()
    with _conn() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM usage ORDER BY id DESC LIMIT ?", (limit,))]


# ------------------------------------------------------------------ disclosure

_BLOCK_CLASSES = (
    (re.compile(r"^Health record context", re.M), "health"),
    (re.compile(r"^(?:Persistent cognitive context \(ACM\)|Relevant memories:|User profile:|Memory:|"
                r"Answer personal questions from this profile)", re.M), MEMORY),
    (re.compile(r"^Conversation history \(", re.M), CONTINUITY),
    (re.compile(r"^(?:Project checkpoint|\*\*World state\*\*|Project context|Active project)", re.M), PROJECT),
)
_SECRET_SHAPES = re.compile(
    r"\b(?:sk|pk|rk|ghp|gho|github_pat|xox[abp]|AIza)[-_A-Za-z0-9]{16,}|"
    r"\b(?:api[_ -]?key|token|secret|password|passwd)\s*[:=]\s*\S+",
    re.I,
)


def _classify_block(block: str) -> str:
    for pattern, cls in _BLOCK_CLASSES:
        if pattern.search(block):
            return cls
    return SYSTEM_PROMPT


def _vault_secrets() -> list[str]:
    from jarvis.security.owner.provider_credentials import (
        AUTHORIZED_PROVIDER_FIELDS,
        resolve_provider_secret,
    )

    found = []
    for field in AUTHORIZED_PROVIDER_FIELDS:
        try:
            res = resolve_provider_secret(field)
        except Exception:  # noqa: BLE001
            continue
        if res is not None and res.value and len(res.value) >= 8:
            found.append(res.value)
    from jarvis.inference.chatgpt_oauth import sensitive_values
    found.extend(sensitive_values())
    return found


@dataclass
class Disclosure:
    messages: list[dict[str, Any]]
    shared: dict[str, int]  # class -> chars
    withheld: dict[str, int]
    sha256: str


def prepare_messages(messages: list[dict[str, Any]], classes: list[str]) -> Disclosure:
    """Build the payload a cloud model may see under this grant."""
    allowed = set(classes) | {CURRENT_TURN}
    shared: dict[str, int] = {}
    withheld: dict[str, int] = {}

    def note(bucket: dict[str, int], cls: str, n: int) -> None:
        bucket[cls] = bucket.get(cls, 0) + n

    system_parts: list[str] = []
    for m in messages:
        if m.get("role") != "system":
            continue
        for block in re.split(r"\n\s*\n", str(m.get("content") or "")):
            if not block.strip():
                continue
            cls = _classify_block(block)
            if cls in allowed and cls not in NEVER_SHARED:
                system_parts.append(block)
                note(shared, cls, len(block))
            else:
                note(withheld, cls, len(block))

    turns = [m for m in messages if m.get("role") != "system"]
    last_user = max((i for i, m in enumerate(turns) if m.get("role") == "user"), default=None)
    kept: list[dict[str, Any]] = []
    for i, m in enumerate(turns):
        if i == last_user or (last_user is not None and i > last_user):
            kept.append(m)  # the request itself, and any tool exchange it started
            note(shared, CURRENT_TURN, len(str(m.get("content") or "")))
        elif RECENT_CONVERSATION in allowed and last_user is not None and i >= last_user - RECENT_TURNS:
            kept.append(m)
            note(shared, RECENT_CONVERSATION, len(str(m.get("content") or "")))
        else:
            note(withheld, RECENT_CONVERSATION, len(str(m.get("content") or "")))

    instruction = NEUTRAL_INSTRUCTION if SYSTEM_PROMPT not in allowed else ""
    system_text = "\n\n".join(p for p in [instruction, *system_parts] if p)
    out = ([{"role": "system", "content": system_text}] if system_text else []) + kept

    blob = json.dumps(out, ensure_ascii=False)
    if "Health record context (authoritative local PHR" in blob:
        raise PolicyRefused("health context cannot be sent to a cloud provider")
    for secret in _vault_secrets():
        if secret in blob:
            raise SecretInPayload("the request contains an Owner Vault secret; not sent")
    redacted = []
    for m in out:
        m = dict(m)
        if isinstance(m.get("content"), str):
            m["content"] = _SECRET_SHAPES.sub("[redacted]", m["content"])
        redacted.append(m)
    payload = json.dumps(redacted, ensure_ascii=False)
    return Disclosure(
        messages=redacted,
        shared=shared,
        withheld=withheld,
        sha256=hashlib.sha256(payload.encode("utf-8")).hexdigest(),
    )


def record_disclosure(
    disclosure: Disclosure,
    *,
    receipt_id: str,
    provider: str,
    model: str,
    role: str,
    authorization_id: str,
) -> None:
    _init()
    with _conn() as conn:
        conn.execute(
            """INSERT INTO disclosures (ts, receipt_id, provider, model, role, authorization_id,
                   classes, withheld, chars, sha256) VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (time.time(), receipt_id, provider, model, role, authorization_id,
             json.dumps(disclosure.shared), json.dumps(disclosure.withheld),
             sum(disclosure.shared.values()), disclosure.sha256),
        )


def disclosure_rows(limit: int = 50) -> list[dict[str, Any]]:
    _init()
    with _conn() as conn:
        rows = [dict(r) for r in conn.execute("SELECT * FROM disclosures ORDER BY id DESC LIMIT ?", (limit,))]
    for r in rows:
        r["classes"] = json.loads(r["classes"])
        r["withheld"] = json.loads(r["withheld"])
    return rows


def status() -> dict[str, Any]:
    budget = load_budget()
    return {
        "budget": {
            "monthly_total_usd": budget.get("monthly_total_usd"),
            "per_task_max_usd": budget.get("per_task_max_usd"),
            "providers": budget.get("providers"),
            "priced_models": sorted((budget.get("prices") or {}).keys()),
        },
        "spend_this_month_usd": round(monthly_spend(), 6),
        "authorizations_active": [
            {k: a[k] for k in ("id", "provider", "roles", "context_classes", "remaining_usd", "expires_at")}
            for a in list_authorizations(active_only=True)
        ],
    }
