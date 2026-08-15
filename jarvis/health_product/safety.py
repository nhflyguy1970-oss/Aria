"""Educational medication / supplement interaction hints — not a pharmacist."""

from __future__ import annotations

import re
from typing import Any

from jarvis.health_product import store
from jarvis.health_product.terminology import DISCLAIMER

_BOUNDARY = (
    "These are educational interaction reminders from an offline catalog. "
    "They are incomplete and do not replace a pharmacist or prescriber."
)

# (token_a, token_b, kind, warning)
_CATALOG: list[tuple[str, str, str, str]] = [
    ("metformin", "alcohol", "alcohol", "Alcohol can increase the risk of lactic acidosis and low blood sugar with metformin. Ask a pharmacist or physician before combining."),
    ("warfarin", "vitamin k", "food", "Vitamin K–rich foods (leafy greens) can reduce warfarin effect. Consistency matters — discuss diet with the prescriber."),
    ("warfarin", "ibuprofen", "medication", "NSAIDs such as ibuprofen can increase bleeding risk with warfarin. Confirm with a pharmacist."),
    ("warfarin", "aspirin", "medication", "Aspirin plus warfarin can raise bleeding risk. Confirm with a pharmacist or physician."),
    ("warfarin", "fish oil", "supplement", "Omega-3 / fish oil may add to bleeding risk with anticoagulants. Educational only — ask a pharmacist."),
    ("warfarin", "vitamin e", "supplement", "High-dose vitamin E may affect bleeding risk with warfarin."),
    ("statin", "grapefruit", "grapefruit", "Grapefruit can raise blood levels of some statins. Ask whether your specific statin is affected."),
    ("atorvastatin", "grapefruit", "grapefruit", "Grapefruit can interact with atorvastatin. Discuss with a pharmacist."),
    ("simvastatin", "grapefruit", "grapefruit", "Grapefruit is a well-known interaction with simvastatin."),
    ("lisinopril", "potassium", "supplement", "ACE inhibitors plus potassium supplements or salt substitutes can raise potassium. Confirm with a clinician."),
    ("losartan", "potassium", "supplement", "ARBs plus potassium supplements can raise potassium."),
    ("ssri", "st john", "supplement", "St. John’s wort can interact with many antidepressants. Do not start or stop without clinician advice."),
    ("sertraline", "st john", "supplement", "St. John’s wort can interact with sertraline / SSRIs."),
    ("maoi", "tyramine", "food", "MAOIs and high-tyramine foods can cause dangerous blood-pressure spikes."),
    ("levothyroxine", "calcium", "supplement", "Calcium can reduce levothyroxine absorption if taken together. Spacing doses is a common pharmacist topic."),
    ("levothyroxine", "iron", "supplement", "Iron can reduce levothyroxine absorption if taken together."),
    ("levothyroxine", "coffee", "food", "Coffee close to levothyroxine may reduce absorption for some people."),
    ("antibiotic", "dairy", "food", "Some antibiotics (e.g. tetracyclines, quinolones) bind dairy/calcium. Check the specific antibiotic."),
    ("ciprofloxacin", "dairy", "food", "Dairy / calcium can reduce ciprofloxacin absorption if taken together."),
    ("sildenafil", "nitrate", "medication", "Nitrates plus PDE5 inhibitors can cause a dangerous blood-pressure drop. Emergency-level interaction — discuss only with clinicians."),
    ("nitroglycerin", "sildenafil", "medication", "Nitrates plus PDE5 inhibitors can cause a dangerous blood-pressure drop."),
    ("acetaminophen", "alcohol", "alcohol", "Heavy alcohol use plus acetaminophen can stress the liver."),
    ("ibuprofen", "alcohol", "alcohol", "Alcohol plus NSAIDs can increase stomach-bleeding risk."),
    ("aspirin", "alcohol", "alcohol", "Alcohol plus aspirin can increase stomach-bleeding risk."),
    ("lisinopril", "ibuprofen", "medication", "ACE inhibitors plus NSAIDs can affect kidney function and blood pressure control."),
    ("metformin", "contrast", "medication", "Iodinated contrast and metformin is a hospital/pharmacist topic around procedures."),
    ("potassium", "spironolactone", "medication", "Potassium-sparing diuretics plus potassium supplements can raise potassium."),
    ("amlodipine", "grapefruit", "grapefruit", "Grapefruit may affect some calcium-channel blockers. Ask about your specific medicine."),
    ("magnesium", "antibiotic", "supplement", "Magnesium can bind some antibiotics and reduce absorption if taken together."),
    ("zinc", "antibiotic", "supplement", "Zinc can bind some antibiotics and reduce absorption if taken together."),
    ("vitamin d", "thiazide", "medication", "Thiazide diuretics plus high-dose vitamin D can raise calcium in some people."),
    ("insulin", "alcohol", "alcohol", "Alcohol can unpredictably lower blood sugar when insulin is used."),
    ("glipizide", "alcohol", "alcohol", "Sulfonylureas plus alcohol can increase hypoglycemia risk."),
    ("prednisone", "nsaid", "medication", "Steroids plus NSAIDs can increase stomach-ulcer risk."),
    ("prednisone", "ibuprofen", "medication", "Steroids plus ibuprofen can increase stomach-ulcer risk."),
    ("ssri", "nsaid", "medication", "SSRIs plus NSAIDs can increase bleeding risk."),
    ("sertraline", "ibuprofen", "medication", "SSRIs plus NSAIDs can increase bleeding risk."),
    ("clonidine", "alcohol", "alcohol", "Alcohol can add to blood-pressure lowering and sedation with clonidine."),
    ("benzodiazepine", "alcohol", "alcohol", "Alcohol plus sedatives can dangerously suppress breathing and alertness."),
    ("alprazolam", "alcohol", "alcohol", "Alcohol plus alprazolam can dangerously suppress breathing and alertness."),
    ("opioid", "alcohol", "alcohol", "Alcohol plus opioids can dangerously suppress breathing."),
    ("tramadol", "ssri", "medication", "Tramadol plus SSRIs is a serotonin-syndrome education topic — ask a pharmacist."),
    ("omeprazole", "clopidogrel", "medication", "Some PPIs may reduce clopidogrel activation. Confirm the specific combination."),
    ("ginkgo", "warfarin", "supplement", "Ginkgo plus anticoagulants may increase bleeding risk."),
    ("garlic", "warfarin", "supplement", "High-dose garlic supplements may affect bleeding risk with anticoagulants."),
    ("kava", "alcohol", "alcohol", "Kava plus alcohol can increase sedation and liver stress."),
    ("valerian", "alcohol", "alcohol", "Valerian plus alcohol/sedatives can increase drowsiness."),
    ("melatonin", "sedative", "supplement", "Melatonin plus other sedatives can increase drowsiness."),
    ("iron", "calcium", "supplement", "Iron and calcium can compete for absorption if taken together."),
    ("magnesium", "calcium", "supplement", "High-dose calcium and magnesium together can affect absorption and GI tolerance."),
]


def _tokens_for(name: str) -> list[str]:
    n = (name or "").lower()
    bits = re.findall(r"[a-z0-9]+", n)
    extra = []
    if "statin" in n or any(x in n for x in ("atorva", "simva", "rosuva", "prava", "lova")):
        extra.append("statin")
    if any(x in n for x in ("sertraline", "fluoxetine", "escitalopram", "paroxetine", "citalopram", "ssri")):
        extra.append("ssri")
    if "nsaid" in n or any(x in n for x in ("ibuprofen", "naproxen", "meloxicam", "diclofenac")):
        extra.append("nsaid")
    if any(x in n for x in ("amoxicillin", "azithromycin", "doxycycline", "ciprofloxacin", "levofloxacin", "antibiotic")):
        extra.append("antibiotic")
    if any(x in n for x in ("alprazolam", "lorazepam", "diazepam", "clonazepam")):
        extra.append("benzodiazepine")
    if any(x in n for x in ("oxycodone", "hydrocodone", "morphine", "tramadol", "codeine")):
        extra.append("opioid")
    if any(x in n for x in ("nitroglycerin", "isosorbide")):
        extra.append("nitrate")
    return list(dict.fromkeys(bits + extra + [n.strip()]))


def scan_interactions(extra_names: list[str] | None = None) -> dict[str, Any]:
    meds = store.list_table("medications", "status=?", ("current",), limit=80)
    supps = store.list_table("supplements", "status=?", ("current",), limit=80)
    names = [str(m.get("name") or "") for m in meds] + [str(s.get("name") or "") for s in supps]
    names += [n for n in (extra_names or []) if n]
    token_map: dict[str, str] = {}
    for name in names:
        for tok in _tokens_for(name):
            token_map.setdefault(tok, name)
    warnings = []
    seen = set()
    for a, b, kind, text in _CATALOG:
        left = [k for k in token_map if a in k or k in a]
        right = [k for k in token_map if b in k or k in b]
        # alcohol / grapefruit / food may not be on the med list — still surface if the drug is present
        if kind in ("alcohol", "grapefruit", "food"):
            if left and (a, b, kind) not in seen:
                seen.add((a, b, kind))
                warnings.append(
                    {
                        "kind": kind,
                        "items": [token_map[left[0]], b],
                        "warning": text,
                        "trust": "low",
                    }
                )
            continue
        if left and right and token_map[left[0]].lower() != token_map[right[0]].lower():
            key = tuple(sorted((token_map[left[0]].lower(), token_map[right[0]].lower())) + [kind])
            if key in seen:
                continue
            seen.add(key)
            warnings.append(
                {
                    "kind": kind,
                    "items": [token_map[left[0]], token_map[right[0]]],
                    "warning": text,
                    "trust": "low",
                }
            )
    lines = ["**Medication safety (educational)**", "", _BOUNDARY, ""]
    if not warnings:
        lines.append("No catalog matches among current medications/supplements. Absence of a warning is not proof of safety.")
    else:
        for w in warnings:
            lines.append(f"• {' × '.join(w['items'])} ({w['kind']}): {w['warning']}")
    lines += ["", "_" + DISCLAIMER + "_"]
    return {
        "ok": True,
        "intent": "safety",
        "warnings": warnings,
        "offline": True,
        "boundary": _BOUNDARY,
        "message": "\n".join(lines),
        "disclaimer": DISCLAIMER,
    }
