"""Download the open Sotkanet indicators and the county map. No API key needed.

    uv run python data/fetch_sotkanet.py

Writes data/raw/regions.json, data/raw/sotkanet_<id>.json and web/counties.geojson.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
API = "https://sotkanet.fi/rest/1.1"
GEO = (
    "https://geo.stat.fi/geoserver/tilastointialueet/wfs?service=WFS&version=2.0.0"
    "&request=GetFeature&typeName=tilastointialueet:hyvinvointialue4500k_2024"
    "&outputFormat=application/json&srsName=EPSG:4326"
)

# Indicator ID -> (first year, last year). Keep in step with backend/indicators.py.
INDICATORS = {
    3627: (2015, 2024),  # five-year survival, bowel cancer
    3625: (2015, 2024),  # five-year survival, breast cancer
    3626: (2015, 2024),  # five-year survival, cervical cancer
    6103: (2022, 2024),  # colorectal screening attendance
    3621: (2015, 2024),  # breast screening attendance
    3620: (2015, 2024),  # cervical screening attendance
    5643: (2017, 2024),  # cancer index, age-standardized
    5093: (2017, 2025),  # special refunds for cancer medicines
    127: (2024, 2024),   # population 31.12.
}


def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    # Sotkanet answers 403 to the default httpx user agent.
    headers = {"User-Agent": "pathway-watch/0.1 (open data client)"}
    with httpx.Client(timeout=60, headers=headers) as http:
        regions = http.get(f"{API}/regions").json()
        keep = [r for r in regions if r["category"] in ("HYVINVOINTIALUE", "MAA")]
        (RAW / "regions.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1))
        ids = {r["id"] for r in keep}
        for ind, (start, end) in INDICATORS.items():
            years = "&".join(f"years={y}" for y in range(start, end + 1))
            rows = http.get(f"{API}/json?indicator={ind}&{years}&genders=total").json()
            rows = [r for r in rows if r["region"] in ids and r.get("value") is not None]
            meta = http.get(f"{API}/indicators/{ind}").json()
            out = {
                "indicator": ind,
                "title": meta.get("title", {}).get("en"),
                "fetched": date.today().isoformat(),
                "url": f"{API}/json?indicator={ind}&{years}&genders=total",
                "rows": rows,
            }
            (RAW / f"sotkanet_{ind}.json").write_text(json.dumps(out, ensure_ascii=False))
            print(ind, len(rows), "rows")
        geo = http.get(GEO).json()
        (ROOT / "web" / "counties.geojson").write_text(json.dumps(geo))
        print("map", len(geo["features"]), "counties")


if __name__ == "__main__":
    main()
