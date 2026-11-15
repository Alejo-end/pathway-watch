"""Download THL's specialised care queues for the specialties on the cancer pathways. No API key needed.

    uv run python data/fetch_thl_queues.py

Writes data/raw/thl_eshjono.json: for each wellbeing services county (THL's provider), each specialty
and each of the last six month-ends, the referrals processed and those processed after more than 21 days,
and the patients waiting for treatment and those waiting more than 90 days. Source: THL Sampo cube
"Hoitoa ja hoidon tarpeen arviointia odottavat erikoisaloittain" (eshjono/jonotilanne).
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "thl_eshjono.json"
CUBE = "https://sampo.thl.fi/pivot/prod/fi/eshjono/jonotilanne/fact_eshjono_jonotilanne"
ALL_PROVIDERS = 976329

# THL specialty code -> label. The pathway each one serves is set in backend/queues.py.
SPECIALTIES = {
    "10G": "Gastroenterology",
    "20G": "Gastrointestinal surgery",
    "30": "Gynaecology",
    "80": "Respiratory medicine",
    "65": "Oncology and radiotherapy",
}
# THL measure id -> our key. Counts, so that the app can pool months and suppress small numbers.
MEASURES = {
    980625: "referrals_processed",
    980628: "referrals_over_21_days",
    738214: "waiting",
    738219: "waiting_over_90_days",
}
MONTHS = 6


def _tree(http: httpx.Client) -> list[dict]:
    text = http.get(f"{CUBE}.dimensions.json").text
    return json.loads(text[text.index("["):text.rindex("]") + 1])


def _walk(node: dict):
    yield node
    for child in node.get("children", []):
        yield from _walk(child)


def main() -> None:
    headers = {"User-Agent": "pathway-watch/0.1 (open data client)"}
    with httpx.Client(timeout=60, headers=headers) as http:
        dims = {d["id"]: d for d in _tree(http)}
        specialties = {}
        for n in _walk(dims["erikoisala"]):
            m = re.match(r"^(\w+) ", n.get("label", ""))
            if n.get("stage") == "ea" and m and m.group(1) in SPECIALTIES:
                specialties[m.group(1)] = n["sid"]
        months = [n for n in _walk(dims["ajankohta"]) if n.get("stage") == "ajankohta"]
        months = sorted(months, key=lambda n: tuple(reversed(n["label"].split("."))))[-MONTHS:]
        measure = ".".join(str(m) for m in MEASURES)
        rows = []
        for code, sid in specialties.items():
            for month in months:
                # The expanded row holds every county and the total for all of them.
                url = (f"{CUBE}.json?row=tuottaja-{ALL_PROVIDERS}L&column=measure-{measure}"
                       f"&filter=erikoisala-{sid}&filter=ajankohta-{month['sid']}")
                ds = http.get(url).json()["dataset"]
                cat = ds["dimension"]["tuottaja"]["category"]
                order = sorted(cat["index"], key=cat["index"].get)
                mcat = ds["dimension"]["measure"]["category"]
                morder = sorted(mcat["index"], key=mcat["index"].get)
                for i, p in enumerate(order):
                    label = cat["label"][p]
                    entry = {"provider": "Finland" if label == "Kaikki hyvinvointialueet" else label,
                             "specialty": code, "month": month["label"]}
                    for j, m in enumerate(morder):
                        v = ds["value"].get(str(i * len(morder) + j))
                        entry[MEASURES[int(m)]] = None if v in (None, "..", "") else float(v)
                    rows.append(entry)
            print(code, "done")
    OUT.write_text(json.dumps({
        "source": "thl_eshjono",
        "title": "THL, access to specialised health care: patients waiting for treatment and referrals processed, by specialty",
        "url": CUBE,
        "fetched": date.today().isoformat(),
        "specialties": SPECIALTIES,
        "months": [m["label"] for m in months],
        "rows": rows,
    }, ensure_ascii=False))
    print(len(rows), "rows")


if __name__ == "__main__":
    main()
