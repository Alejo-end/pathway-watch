"""Download cancer deaths and population by age from Statistics Finland (StatFin PxWeb API, no key).

    uv run python data/fetch_statfin.py

Writes data/raw/statfin_mortality.json with:
- deaths per county, cause and year (table ksyyt 13u5),
- national deaths per five-year age group, cause and year (table ksyyt 11az),
- population per county and five-year age group (table vaerak 11re, summed from municipalities),
- the municipality to county map (classification service, 2026).
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "statfin_mortality.json"
PX = "https://pxdata.stat.fi/PxWeb/api/v1/en/StatFin"
MAP = (
    "https://data.stat.fi/api/classifications/v2/correspondenceTables/"
    "kunta_1_20260101%23hyvinvointialue_1_20260101/maps?format=json"
)
YEARS = [str(y) for y in range(2019, 2026)]
# StatFin cause codes (time series classification). Bowel is colon plus rectum.
CAUSES = {"all": ["04-21"], "lung": ["11"], "pancreas": ["10"], "liver": ["09"],
          "bowel": ["07", "08"], "breast": ["13"], "cervical": ["14"]}
AGE_GROUPS = ["0-4", "5-9", "10-14", "15-19", "20-24", "25-29", "30-34", "35-39", "40-44", "45-49",
              "50-54", "55-59", "60-64", "65-69", "70-74", "75-79", "80-84", "85-89", "90-94", "95-"]
AGE_11AZ = ["000", "1-4"] + AGE_GROUPS[1:]  # 11az splits 0 and 1-4


def group_of(age: int) -> str:
    return AGE_GROUPS[min(age // 5, 19)]


def px(http: httpx.Client, table: str, query: list[dict]) -> dict:
    r = http.post(f"{PX}/{table}", json={"query": query, "response": {"format": "json-stat2"}})
    r.raise_for_status()
    return r.json()


def sel(code: str, values: list[str]) -> dict:
    return {"code": code, "selection": {"filter": "item", "values": values}}


def cells(js: dict):
    """Yield (dict of dimension code -> category code, value) for a json-stat2 response."""
    dims = js["id"]
    cats = [list(js["dimension"][d]["category"]["index"].keys()) for d in dims]
    sizes = js["size"]
    for flat, value in enumerate(js["value"]):
        idx, rest = [], flat
        for s in reversed(sizes):
            idx.append(rest % s)
            rest //= s
        idx.reverse()
        yield {d: cats[i][j] for i, (d, j) in enumerate(zip(dims, idx))}, value


def main() -> None:
    all_codes = sorted({c for v in CAUSES.values() for c in v})
    with httpx.Client(timeout=120, headers={"User-Agent": "pathway-watch/0.1 (open data client)"}) as http:
        urls = http.get(MAP).json()
        muni_to_county = {u.rstrip("/").split("/")[-2]: u.rstrip("/").split("/")[-1] for u in urls}

        meta = http.get(f"{PX}/ksyyt/13u5.px").json()
        area_code = meta["variables"][0]["code"]
        js = px(http, "ksyyt/13u5.px", [
            sel(area_code, ["SSS"] + [f"HVA{c:02d}" for c in range(1, 22)] + ["HVA90"]),
            sel("kuolinsyyt_1_20210101", all_codes), sel("timeperiod_y", YEARS),
            sel("contentscode", ["ksyylkm"]),
        ])
        county_deaths: dict = {}
        for c, v in cells(js):
            region = c[area_code].replace("HVA", "") if c[area_code] != "SSS" else "358"
            county_deaths.setdefault(region, {}).setdefault(c["kuolinsyyt_1_20210101"], {})[c["timeperiod_y"]] = v

        js = px(http, "ksyyt/11az.px", [
            sel("kuolinsyyt_1_20210101", all_codes), sel("ikaryhma_10_20180101", AGE_11AZ),
            sel("sukupuoli_9_20180101", ["SSS"]), sel("timeperiod_y", YEARS),
        ])
        national_deaths: dict = {}
        for c, v in cells(js):
            age = "0-4" if c["ikaryhma_10_20180101"] in ("000", "1-4") else c["ikaryhma_10_20180101"]
            row = national_deaths.setdefault(c["kuolinsyyt_1_20210101"], {}).setdefault(c["timeperiod_y"], {})
            row[age] = row.get(age, 0) + (v or 0)

        meta = http.get(f"{PX}/vaerak/11re.px").json()
        area_code = meta["variables"][0]["code"]
        ages = [f"{a:03d}" for a in range(100)] + ["100-"]
        population: dict = {}
        for year in YEARS:
            js = px(http, "vaerak/11re.px", [
                sel(area_code, ["SSS"] + [f"KU{m}" for m in muni_to_county]),
                sel("ikaryhma_10_20180101", ages), sel("sukupuoli_9_20180101", ["SSS"]),
                sel("timeperiod_y", [year]),
            ])
            for c, v in cells(js):
                area = c[area_code]
                region = "358" if area == "SSS" else muni_to_county.get(area.replace("KU", ""))
                if region is None or v is None:
                    continue
                a = c["ikaryhma_10_20180101"]
                g = "95-" if a == "100-" else group_of(int(a))
                row = population.setdefault(region, {}).setdefault(year, {})
                row[g] = row.get(g, 0) + v
            print("population", year, len(population))

    OUT.write_text(json.dumps({
        "fetched": date.today().isoformat(),
        "causes": CAUSES,
        "age_groups": AGE_GROUPS,
        "county_deaths": county_deaths,
        "national_deaths_by_age": national_deaths,
        "population_by_age": population,
        "tables": {"county_deaths": "ksyyt/13u5", "national_deaths_by_age": "ksyyt/11az",
                   "population_by_age": "vaerak/11re", "municipality_map": MAP},
    }))
    print("wrote", OUT)


if __name__ == "__main__":
    main()
