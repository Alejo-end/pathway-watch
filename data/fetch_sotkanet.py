"""Download the open Sotkanet indicators and the county map. No API key needed.

    uv run python data/fetch_sotkanet.py            # every indicator and the map
    uv run python data/fetch_sotkanet.py 6411 3336  # only these indicators

Writes data/raw/regions.json, data/raw/sotkanet_<id>.json and web/counties.geojson.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))  # the script runs from data/, the indicator list lives in backend/

from backend.indicators import SOTKANET  # noqa: E402
RAW = ROOT / "data" / "raw"
API = "https://sotkanet.fi/rest/1.1"
GEO = (
    "https://geo.stat.fi/geoserver/tilastointialueet/wfs?service=WFS&version=2.0.0"
    "&request=GetFeature&typeName=tilastointialueet:hyvinvointialue4500k_2024"
    "&outputFormat=application/json&srsName=EPSG:4326"
)

def main() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    # Sotkanet answers 403 to the default httpx user agent.
    headers = {"User-Agent": "pathway-watch/0.1 (open data client)"}
    with httpx.Client(timeout=60, headers=headers) as http:
        regions = http.get(f"{API}/regions").json()
        keep = [r for r in regions if r["category"] in ("HYVINVOINTIALUE", "MAA")]
        (RAW / "regions.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1))
        ids = {r["id"] for r in keep}
        only = {int(a) for a in sys.argv[1:]}  # optional: refresh only these indicator IDs
        for ind, (_, start, end) in SOTKANET.items():
            if only and ind not in only:
                continue
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
        if only:
            return
        geo = http.get(GEO).json()
        (ROOT / "web" / "counties.geojson").write_text(json.dumps(geo))
        print("map", len(geo["features"]), "counties")


if __name__ == "__main__":
    main()
