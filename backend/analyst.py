"""Three plain sentences for the decision-maker: the gap, the likely step, the first action.

The language model only rewords computed facts. Every sentence must cite fact IDs, and every
number in a sentence must appear in the facts it cites. A sentence that fails either check is
removed before display. Without a model (no credentials, PATHWAY_LLM=0, or an error), a fixed
template writes the sentences from the same facts.
"""

from __future__ import annotations

import json
import os
import re

from .analysis import Data, Fact, Pathway, gap
from .indicators import CANCERS

MODEL = "claude-opus-5-5"
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")

SYSTEM = """You write for a non-technical decision-maker in a Finnish wellbeing services county.
You get a list of facts, each with an ID. Write at most three short sentences in plain English:
1. the gap, 2. the step of the care pathway where it most likely starts, 3. the first action.
Rules:
- Use only the facts given. Do not add numbers, causes, names or claims that are not in the facts.
- Copy every number exactly as it appears in a fact.
- Say "most likely" for the pathway step. Never claim a cause.
- For each sentence, list the IDs of the facts it uses in fact_ids."""

SCHEMA = {
    "type": "object",
    "properties": {
        "sentences": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string"},
                    "fact_ids": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["text", "fact_ids"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["sentences"],
    "additionalProperties": False,
}


def extra_facts(pathway: Pathway, recs: list[dict]) -> list[Fact]:
    out = [Fact("pathway", f"Most likely pathway step: {pathway.label} ({pathway.confidence} confidence). {pathway.reason}", None, "", "pathway_rule")]
    if recs:
        r = recs[0]
        out.append(Fact(f"measure.{r['measure']}", f"Roadmap measure {r['measure']}: {r['action']}", None, "", "roadmap"))
    return out


def numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in NUMBER.findall(text)}


def check(sentences: list[dict], facts: list[Fact]) -> tuple[list[dict], list[dict]]:
    """Split sentences into (kept, removed). A kept sentence cites known facts only, and every
    number in it appears in one of the cited facts."""
    by_id = {f.id: f for f in facts}
    kept, removed = [], []
    for s in sentences:
        ids = [i for i in s.get("fact_ids", []) if i in by_id]
        if not ids or len(ids) != len(s.get("fact_ids", [])):
            removed.append({**s, "reason": "cites no fact or an unknown fact"})
            continue
        allowed = set().union(*(numbers(by_id[i].text) for i in ids))
        bad = numbers(s["text"]) - allowed
        if bad:
            removed.append({**s, "reason": f"numbers not in the cited facts: {sorted(bad)}"})
            continue
        kept.append({"text": s["text"], "fact_ids": ids})
    return kept, removed


def template(data: Data, cancer: str, county: str, pathway: Pathway, recs: list[dict]) -> list[dict]:
    spec = CANCERS[cancer]
    name = data.names[county]
    label = spec["label"].lower()
    s_ind, c_ind = spec["survival"], spec["screening"]
    sg, cg = gap(data, s_ind, county), gap(data, c_ind, county)
    out = []
    if sg.years:
        y = sg.years[-1]
        trend = {
            "below": f"on average {abs(sg.avg_gap):g} points below the national value",
            "above": f"on average {sg.avg_gap:g} points above the national value",
            "near": "close to the national value",
        }[sg.direction]
        out.append({
            "text": f"In {name}, five-year survival for {label} was {sg.county_values[-1]:g}% in {y}, against {sg.national_values[-1]:g}% for Finland, "
                    f"and {trend} over {sg.years[0]}–{y}.",
            "fact_ids": [f"{s_ind}.county.{y}", f"{s_ind}.national.{y}", f"{s_ind}.gap"],
        })
    if pathway.step in ("detection", "later", "watch") and cg.years:
        y = cg.years[-1]
        att = f"{cg.county_values[-1]:g}% against {cg.national_values[-1]:g}% nationally in {y}"
        text = {
            "detection": f"Screening attendance is also low ({att}), so the difference most likely starts at detection.",
            "later": f"Screening attendance is not behind ({att}), so the difference most likely starts later: "
                     f"{pathway.label[0].lower() + pathway.label[1:]}.",
            "watch": f"Screening attendance is low ({att}), which is an early warning at the detection step.",
        }[pathway.step]
        out.append({"text": text, "fact_ids": [f"{c_ind}.county.{y}", f"{c_ind}.national.{y}", "pathway"]})
    if recs:
        r = recs[0]
        action = r["action"].rstrip(".")
        out.append({"text": f"First action: {action[0].lower() + action[1:]} (roadmap measure {r['measure']}).",
                    "fact_ids": [f"measure.{r['measure']}"]})
    return out


def llm_sentences(facts: list[Fact]) -> list[dict] | None:
    """Ask Claude to reword the facts. Returns None when no model is available."""
    if os.getenv("PATHWAY_LLM", "1") == "0":
        return None
    try:
        import anthropic
    except ImportError:
        return None
    payload = [{"id": f.id, "fact": f.text} for f in facts]
    try:
        client = anthropic.Anthropic()
        resp = client.beta.messages.create(
            model=MODEL,
            max_tokens=2000,
            system=SYSTEM,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": SCHEMA}},
            messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
        )
    except anthropic.APIConnectionError:
        return None
    except anthropic.APIStatusError:
        return None
    except anthropic.AnthropicError:
        return None
    except TypeError:  # the SDK found no credentials
        return None
    if resp.stop_reason == "refusal":
        return None
    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        return None
    return json.loads(text).get("sentences", [])


def summarize(data: Data, cancer: str, county: str, pathway: Pathway, recs: list[dict], facts: list[Fact]) -> dict:
    drafted = llm_sentences(facts)
    writer = "model" if drafted else "template"
    kept, removed = check(drafted or template(data, cancer, county, pathway, recs), facts)
    if not kept and drafted:
        writer = "template"
        kept, removed2 = check(template(data, cancer, county, pathway, recs), facts)
        removed += removed2
    return {"sentences": kept, "removed": removed, "writer": writer}
