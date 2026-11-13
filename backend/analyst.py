"""Three plain sentences for the decision-maker: the gap, the likely step, the first action.

A fixed template writes them from the computed facts. If Anthropic credentials are present
and PATHWAY_LLM is not 0, the language model rewords the facts instead. Either way, `check`
removes a sentence before display if it breaks one of its rules.

What `check` cannot do: it compares numbers and quantity words with the cited facts, but it
does not read meaning. A sentence that gives a county's number to the country, or that adds
a claim without numbers, passes. The template cannot make these errors. The model can, so
the prompt forbids them and the page says which of the two wrote the text.
"""

from __future__ import annotations

import json
import os
import re

from . import nordcan
from .analysis import Pathway, gap
from .facts import Fact
from .indicators import CANCERS, has_county_survival
from .mortality import shared as shared_mortality
from .sotkanet import CountyData

MODEL = "claude-opus-5-5"
NUMBER = re.compile(r"\d+(?:[.,]\d+)*")
# Quantities written as words. A sentence may use one only if a cited fact uses it too.
QUANTITY_WORDS = re.compile(
    r"\b(half|twice|double[ds]?|triple[ds]?|thrice|quadruple[ds]?|two|three|four|five|six|seven|eight|nine|ten|"
    r"dozens?|hundreds?|thousands?|millions?)\b", re.I)

SYSTEM = """You write for a non-technical decision-maker in a Finnish wellbeing services county.
You get a list of facts, each with an ID. Write at most three short sentences in plain English:
1. the gap, 2. the step of the care pathway where it most likely starts, 3. the first action.
Rules:
- Use only the facts given. Do not add numbers, causes, names or claims that are not in the facts.
- Copy every number exactly as it appears in a fact.
- Keep each number with the place and year it belongs to in the fact. Write quantities as digits, not words.
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


def numbers(text: str) -> set[str]:
    return {n.replace(",", ".") for n in NUMBER.findall(text)}


def quantity_words(text: str) -> set[str]:
    return {w.lower() for w in QUANTITY_WORDS.findall(text)}


def check(sentences: list[dict], facts: list[Fact]) -> tuple[list[dict], list[dict]]:
    """Split sentences into (kept, removed). A sentence is kept only if:

    1. it cites at least one fact, and every ID it cites exists;
    2. every number in it appears in one of the cited facts;
    3. every quantity word in it ("twice", "half", "three") appears in one of the cited facts.
    """
    by_id = {f.id: f for f in facts}
    kept, removed = [], []
    for s in sentences:
        cited = s.get("fact_ids", [])
        if not cited or any(i not in by_id for i in cited):
            removed.append({**s, "reason": "cites no fact or an unknown fact"})
            continue
        source_text = " ".join(by_id[i].text for i in cited)
        bad = numbers(s["text"]) - numbers(source_text)
        if bad:
            removed.append({**s, "reason": f"numbers not in the cited facts: {sorted(bad)}"})
            continue
        bad = quantity_words(s["text"]) - quantity_words(source_text)
        if bad:
            removed.append({**s, "reason": f"quantity words not in the cited facts: {sorted(bad)}"})
            continue
        kept.append({"text": s["text"], "fact_ids": cited})
    return kept, removed


def _first_action_sentence(recs: list[dict]) -> list[dict]:
    if not recs:
        return []
    r = recs[0]
    action = r["action"].rstrip(".")
    return [{"text": f"First action: {action[0].lower() + action[1:]} (roadmap measure {r['measure']}).",
             "fact_ids": [f"measure.{r['measure']}"]}]


def template(data: CountyData, cancer: str, county: str, pathway: Pathway, recs: list[dict]) -> list[dict]:
    """The fixed wording. Each sentence names the facts it restates."""
    if has_county_survival(cancer):
        return _county_sentences(data, cancer, county, pathway) + _first_action_sentence(recs)
    return _national_sentences(data, cancer, county, pathway) + _first_action_sentence(recs)


def _county_sentences(data: CountyData, cancer: str, county: str, pathway: Pathway) -> list[dict]:
    spec = CANCERS[cancer]
    name, label = data.names[county], spec["label"].lower()
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
            "text": f"In {name}, five-year survival for {label} was {sg.county_values[-1]:g}% in {y}, against "
                    f"{sg.national_values[-1]:g}% for Finland, and {trend} over {sg.years[0]}–{y}.",
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
    return out


def _national_sentences(data: CountyData, cancer: str, county: str, pathway: Pathway) -> list[dict]:
    """For a cancer with no county survival data: county mortality, then Finland against the Nordic level."""
    name, label = data.names[county], CANCERS[cancer]["label"].lower()
    out = []
    mort = shared_mortality()
    if mort.ok:
        m = mort.smr(cancer, county)
        word = {"worse": "more than", "better": "fewer than", "near": "about as many as"}[m.direction]
        out.append({
            "text": f"In {name}, {round(m.deaths_per_year)} people died of {label} each year in {m.years[0]}–{m.years[-1]}, "
                    f"{word} the county's age structure predicts (SMR {m.smr}, {m.confidence} confidence).",
            "fact_ids": [f"mort.{cancer}.yearly"],
        })
    b = nordcan.benchmark(nordcan.load(), cancer)
    if b["gap"] is not None:
        out.append({
            "text": f"Nationally, five-year survival is {b['finland']}% against a Nordic level of {b['nordic']}%, "
                    f"so the gap most likely starts at {pathway.label.lower()}.",
            "fact_ids": [f"nordcan.{cancer}", "pathway"],
        })
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


def summarize(data: CountyData, cancer: str, county: str, pathway: Pathway, recs: list[dict], facts: list[Fact]) -> dict:
    """The checked sentences, the removed ones with the reason, and who wrote them ("model" or "template").
    If the model's draft loses every sentence in the check, the template takes over."""
    drafted = llm_sentences(facts)
    writer = "model" if drafted else "template"
    kept, removed = check(drafted or template(data, cancer, county, pathway, recs), facts)
    if not kept and drafted:
        writer = "template"
        kept, removed2 = check(template(data, cancer, county, pathway, recs), facts)
        removed += removed2
    return {"sentences": kept, "removed": removed, "writer": writer}
