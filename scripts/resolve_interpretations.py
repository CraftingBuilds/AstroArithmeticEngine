from pathlib import Path
import json
import sys

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
SECURE_CHARTS = ENGINE_ROOT / "secure_charts"
DERIVED_DIR = ENGINE_ROOT / "derived"

STRUCTURED_CODEX_FILE = DERIVED_DIR / "structured_building_blocks_v2.json"


def load_json(path: Path):
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_chart_paths(chart_id: str) -> dict:
    chart_dir = SECURE_CHARTS / chart_id
    return {
        "chart_dir": chart_dir,
        "normalized_chart": chart_dir / "normalized_chart.json",
        "rankings_file": chart_dir / "significance_rankings.json",
        "aspects_file": chart_dir / "aspects.json",
        "output_file": chart_dir / "resolved_interpretations.json",
    }


def normalize_sign_name(sign: str) -> str:
    mapping = {
        "Ari": "Aries",
        "Tau": "Taurus",
        "Gem": "Gemini",
        "Can": "Cancer",
        "Leo": "Leo",
        "Vir": "Virgo",
        "Lib": "Libra",
        "Sco": "Scorpio",
        "Sag": "Sagittarius",
        "Cap": "Capricorn",
        "Aqu": "Aquarius",
        "Pis": "Pisces",
    }
    return mapping.get(sign, sign)


def ordinal_house_name(house_num: str) -> str:
    if house_num == "1":
        return "1st House"
    if house_num == "2":
        return "2nd House"
    if house_num == "3":
        return "3rd House"
    return f"{house_num}th House"


def find_codex_entry(codex: list, name: str, family: str | None = None):
    q = name.strip().lower()

    for entry in codex:
        if family and entry.get("family") != family:
            continue

        outer_name = entry.get("name", "").strip().lower()
        parsed_name = entry.get("parsed", {}).get("name", "").strip().lower()

        if q == outer_name or q == parsed_name:
            return entry

    return None


def get_sidereal_house_lookup(chart: dict) -> dict:
    lookup = {}
    for house in chart.get("houses", {}).get("sidereal", []):
        house_num = house.get("house_number")
        if not house_num:
            continue

        house_name = ordinal_house_name(house_num)

        for occ in house.get("occupants", []):
            body = occ.get("body")
            if body:
                lookup[body] = house_name
    return lookup


def build_body_interpretation(body_name: str, sign_name: str, house_name: str, codex: list):
    body_entry = find_codex_entry(codex, body_name)
    sign_entry = find_codex_entry(codex, normalize_sign_name(sign_name), family="sign")
    house_entry = find_codex_entry(codex, house_name, family="house")

    return {
        "body_name": body_name,
        "sign_name": normalize_sign_name(sign_name),
        "house_name": house_name,
        "body_entry_found": body_entry is not None,
        "sign_entry_found": sign_entry is not None,
        "house_entry_found": house_entry is not None,
        "body_interpretation": body_entry.get("parsed") if body_entry else None,
        "sign_interpretation": sign_entry.get("parsed") if sign_entry else None,
        "house_interpretation": house_entry.get("parsed") if house_entry else None,
    }


def build_aspect_interpretation(aspect_row: dict, codex: list):
    aspect_name = aspect_row.get("aspect_name")
    aspect_entry = find_codex_entry(codex, aspect_name, family="aspect")

    return {
        "body_a": aspect_row.get("body_a"),
        "aspect_name": aspect_name,
        "body_b": aspect_row.get("body_b"),
        "orb": aspect_row.get("orb"),
        "aspect_entry_found": aspect_entry is not None,
        "aspect_interpretation": aspect_entry.get("parsed") if aspect_entry else None,
    }


def resolve_placements(chart: dict, rankings: dict, codex: list):
    sidereal_placements = chart.get("zodiac", {}).get("sidereal", [])
    house_lookup = get_sidereal_house_lookup(chart)

    placement_map = {p.get("body"): p for p in sidereal_placements}
    resolved = []

    for ranked in rankings.get("placements_ranked", []):
        body = ranked.get("body")
        placement = placement_map.get(body)

        if not placement:
            resolved.append({
                "type": "placement",
                "body_name": body,
                "resolved": False,
                "reason": "placement not found in sidereal zodiac"
            })
            continue

        sign_name = placement.get("sign")
        house_name = house_lookup.get(body)

        if not house_name:
            resolved.append({
                "type": "placement",
                "body_name": body,
                "resolved": False,
                "reason": "house not found for placement"
            })
            continue

        merged = build_body_interpretation(body, sign_name, house_name, codex)
        merged["type"] = "placement"
        merged["resolved"] = True
        merged["significance"] = {
            "score": ranked.get("score"),
            "reasons": ranked.get("reasons", [])
        }

        resolved.append(merged)

    return resolved


def resolve_aspects(rankings: dict, aspects: list, codex: list):
    resolved = []

    for ranked in rankings.get("aspects_ranked", []):
        matched = None
        for a in aspects:
            if (
                a.get("body_a") == ranked.get("body_a")
                and a.get("body_b") == ranked.get("body_b")
                and a.get("aspect_name") == ranked.get("aspect_name")
                and a.get("orb") == ranked.get("orb")
            ):
                matched = a
                break

        if not matched:
            resolved.append({
                "type": "aspect",
                "resolved": False,
                "reason": "aspect not found in aspects.json",
                "body_a": ranked.get("body_a"),
                "aspect_name": ranked.get("aspect_name"),
                "body_b": ranked.get("body_b"),
            })
            continue

        merged = build_aspect_interpretation(matched, codex)
        merged["type"] = "aspect"
        merged["resolved"] = True
        merged["significance"] = {
            "score": ranked.get("score"),
            "reasons": ranked.get("reasons", [])
        }

        resolved.append(merged)

    return resolved


def main():
    chart_id = input("Enter Chart ID: ").strip()
    if not chart_id:
        print("No Chart ID entered. Exiting.")
        sys.exit(1)

    try:
        paths = get_chart_paths(chart_id)
        chart = load_json(paths["normalized_chart"])
        rankings = load_json(paths["rankings_file"])
        aspects = load_json(paths["aspects_file"])
        codex = load_json(STRUCTURED_CODEX_FILE)

        resolved_placements = resolve_placements(chart, rankings, codex)
        resolved_aspects = resolve_aspects(rankings, aspects, codex)

        output = {
            "chart_id": chart_id,
            "resolved_placements": resolved_placements,
            "resolved_aspects": resolved_aspects
        }

        with open(paths["output_file"], "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print("\nDone.")
        print(f"Wrote resolved interpretations to: {paths['output_file']}")
        print(f"Resolved placements: {sum(1 for x in resolved_placements if x.get('resolved'))}/{len(resolved_placements)}")
        print(f"Resolved aspects: {sum(1 for x in resolved_aspects if x.get('resolved'))}/{len(resolved_aspects)}")

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
