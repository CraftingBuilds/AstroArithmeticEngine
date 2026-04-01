from pathlib import Path
import json
import sys

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
SECURE_CHARTS = ENGINE_ROOT / "secure_charts"

ANGULAR_HOUSES = {"1", "4", "7", "10"}
LUMINARIES = {"Sun", "Moon"}
ANGLES = {"Ascendant", "Descendant", "Midheaven", "Imum Coeli"}
NODES = {"North Node", "South Node"}

HOUSE_RULER_MAP = {
    "Aries": ["Mars"],
    "Taurus": ["Venus"],
    "Gemini": ["Mercury"],
    "Cancer": ["Moon"],
    "Leo": ["Sun"],
    "Virgo": ["Mercury"],
    "Libra": ["Venus"],
    "Scorpio": ["Mars", "Pluto"],
    "Sagittarius": ["Jupiter"],
    "Capricorn": ["Saturn"],
    "Aquarius": ["Saturn", "Uranus"],
    "Pisces": ["Jupiter", "Neptune"],
    # abbreviated signs from Time Nomad
    "Ari": ["Mars"],
    "Tau": ["Venus"],
    "Gem": ["Mercury"],
    "Can": ["Moon"],
    "Leo": ["Sun"],
    "Vir": ["Mercury"],
    "Lib": ["Venus"],
    "Sco": ["Mars", "Pluto"],
    "Sag": ["Jupiter"],
    "Cap": ["Saturn"],
    "Aqu": ["Saturn", "Uranus"],
    "Pis": ["Jupiter", "Neptune"],
}


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
        "aspects_file": chart_dir / "aspects.json",
        "output_file": chart_dir / "significance_rankings.json",
    }


def get_sidereal_placements(chart: dict) -> list:
    return chart.get("zodiac", {}).get("sidereal", [])


def get_sidereal_houses(chart: dict) -> list:
    return chart.get("houses", {}).get("sidereal", [])


def get_sidereal_house_rulers(chart: dict) -> list:
    return chart.get("house_rulers", {}).get("sidereal", [])


def build_house_lookup(houses: list) -> dict:
    lookup = {}
    for house in houses:
        house_num = house.get("house_number")
        for occ in house.get("occupants", []):
            lookup[occ.get("body")] = house_num
    return lookup


def get_chart_ruler(chart: dict) -> list:
    """
    Uses the sidereal 1st house cusp sign.
    """
    houses = get_sidereal_houses(chart)
    if not houses:
        return []

    first_house = None
    for h in houses:
        if h.get("house_number") == "1":
            first_house = h
            break

    if not first_house:
        return []

    sign = first_house.get("sign")
    return HOUSE_RULER_MAP.get(sign, [])


def parse_orb_to_float(orb_str: str) -> float | None:
    """
    Converts strings like '1º 38'' into float degrees.
    """
    if not orb_str:
        return None

    orb_str = orb_str.strip()
    parts = orb_str.replace('"', "").split("º")
    if len(parts) != 2:
        return None

    try:
        degrees = float(parts[0].strip())
        minutes_part = parts[1].replace("'", "").strip()
        minutes = float(minutes_part) if minutes_part else 0.0
        return degrees + (minutes / 60.0)
    except ValueError:
        return None


def score_placements(chart: dict) -> list:
    placements = get_sidereal_placements(chart)
    houses = get_sidereal_houses(chart)
    house_lookup = build_house_lookup(houses)
    chart_rulers = set(get_chart_ruler(chart))

    ranked = []

    for p in placements:
        body = p.get("body")
        score = 0
        reasons = []

        if body in LUMINARIES:
            score += 5
            reasons.append("luminary")

        if body in ANGLES:
            score += 6
            reasons.append("angle")

        if body in NODES:
            score += 4
            reasons.append("nodal axis")

        house_num = house_lookup.get(body)
        if house_num in ANGULAR_HOUSES:
            score += 4
            reasons.append(f"angular house ({house_num})")

        if body in chart_rulers:
            score += 5
            reasons.append("chart ruler")

        ranked.append({
            "type": "placement",
            "body": body,
            "sign": p.get("sign"),
            "degree": p.get("degree"),
            "house": house_num,
            "score": score,
            "reasons": reasons
        })

    return ranked


def score_aspects(aspects: list) -> list:
    ranked = []

    for aspect in aspects:
        body_a = aspect.get("body_a")
        body_b = aspect.get("body_b")
        aspect_name = aspect.get("aspect_name")
        orb = parse_orb_to_float(aspect.get("orb"))

        score = 0
        reasons = []

        if body_a in LUMINARIES or body_b in LUMINARIES:
            score += 3
            reasons.append("involves luminary")

        if body_a in ANGLES or body_b in ANGLES:
            score += 3
            reasons.append("involves angle")

        if body_a in NODES or body_b in NODES:
            score += 2
            reasons.append("involves node")

        if orb is not None:
            if orb < 1:
                score += 5
                reasons.append("very tight orb (<1°)")
            elif orb < 2:
                score += 4
                reasons.append("tight orb (<2°)")
            elif orb < 3:
                score += 2
                reasons.append("moderate orb (<3°)")

        ranked.append({
            "type": "aspect",
            "body_a": body_a,
            "aspect_name": aspect_name,
            "body_b": body_b,
            "orb": aspect.get("orb"),
            "score": score,
            "reasons": reasons
        })

    return ranked


def build_rankings(chart: dict, aspects: list) -> dict:
    placement_rankings = score_placements(chart)
    aspect_rankings = score_aspects(aspects)

    placement_rankings.sort(key=lambda x: x["score"], reverse=True)
    aspect_rankings.sort(key=lambda x: x["score"], reverse=True)

    return {
        "chart_id": chart.get("chart_id"),
        "chart_ruler_candidates": get_chart_ruler(chart),
        "placements_ranked": placement_rankings,
        "aspects_ranked": aspect_rankings
    }


def main():
    chart_id = input("Enter Chart ID: ").strip()
    if not chart_id:
        print("No Chart ID entered. Exiting.")
        sys.exit(1)

    try:
        paths = get_chart_paths(chart_id)
        chart = load_json(paths["normalized_chart"])
        aspects = load_json(paths["aspects_file"])
        rankings = build_rankings(chart, aspects)

        with open(paths["output_file"], "w", encoding="utf-8") as f:
            json.dump(rankings, f, indent=2, ensure_ascii=False)

        print("\nDone.")
        print(f"Wrote significance rankings to: {paths['output_file']}")
        print(f"Top placement: {rankings['placements_ranked'][0]['body'] if rankings['placements_ranked'] else 'NONE'}")
        if rankings["aspects_ranked"]:
            top_aspect = rankings["aspects_ranked"][0]
            print(f"Top aspect: {top_aspect['body_a']} {top_aspect['aspect_name']} {top_aspect['body_b']}")
        else:
            print("Top aspect: NONE")

    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
