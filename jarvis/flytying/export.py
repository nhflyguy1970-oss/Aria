"""Export fly-tying recipes as markdown or plain text."""

from __future__ import annotations

from typing import Any


def export_recipe(recipe: dict[str, Any], *, fmt: str = "markdown") -> str:
    name = str(recipe.get("name") or recipe.get("fly_name") or "Pattern")
    lines: list[str] = []
    if fmt == "markdown":
        lines.append(f"# {name}")
        lines.append("")
        if recipe.get("type"):
            lines.append(f"**Type:** {recipe['type']}")
        if recipe.get("hook"):
            lines.append(f"**Hook:** {recipe['hook']}")
        mats = recipe.get("materials") or []
        if mats:
            lines.append("")
            lines.append("## Materials")
            lines.extend(f"- {m}" for m in mats)
        steps = recipe.get("steps") or []
        if steps:
            lines.append("")
            lines.append("## Steps")
            lines.extend(f"{i}. {s}" for i, s in enumerate(steps, 1))
        if recipe.get("source_url"):
            lines.append("")
            lines.append(f"Source: {recipe['source_url']}")
    else:
        lines.append(name)
        if recipe.get("type"):
            lines.append(f"Type: {recipe['type']}")
        if recipe.get("hook"):
            lines.append(f"Hook: {recipe['hook']}")
        mats = recipe.get("materials") or []
        if mats:
            lines.append("Materials: " + "; ".join(str(m) for m in mats))
        steps = recipe.get("steps") or []
        for i, s in enumerate(steps, 1):
            lines.append(f"{i}. {s}")
    return "\n".join(lines).strip() + "\n"


def compare_recipes(recipes: list[dict[str, Any]]) -> str:
    blocks = []
    for r in recipes:
        blocks.append(export_recipe(r, fmt="markdown"))
        blocks.append("---")
    return "\n".join(blocks).rstrip("---\n")
