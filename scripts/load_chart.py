from pathlib import Path
import json
import sys

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
SECURE_CHARTS = ENGINE_ROOT / "secure_charts"


REQUIRED_TOP_LEVEL_KEYS = [
    "chart_id",
    "chart_folder",
    "source",
    "metadata",
    "zodiac",
    "heliocentric",
    "houses",
    "house_rulers",
    "dignities",
    "elements",
    "quadruplicities",
    "mutual_receptions",
    "fixed_star_conjunctions",
    "parallels",
    "contra_parallels",
    "aspects",
    "notes",
    "parser_warnings",
    "unresolved_values",
]

REQUIRED_NESTED_KEYS = {
    "metadata": ["date_time", "geo_location", "summary", "parameters"],
    "zodiac": ["tropical", "sidereal"],
    "heliocentric": ["tropical", "sidereal"],
    "houses": ["tropical", "sidereal"],
    "house_rulers": ["tropical", "sidereal"],
    "dignities": ["tropical", "sidereal"],
    "elements": ["tropical", "sidereal"],
    "quadruplicities": ["tropical", "sidereal"],
    "mutual_receptions": ["tropical", "sidereal"],
}


def get_chart_paths(chart_id: str) -> dict:
    chart_dir = SECURE_CHARTS / chart_id
    normalized_chart = chart_dir / "normalized_chart.json"

    return {
        "chart_dir": chart_dir,
        "normalized_chart": normalized_chart,
    }


def load_json_file(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}") from e


def validate_top_level_keys(chart: dict) -> list[str]:
    errors = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in chart:
            errors.append(f"Missing top-level key: {key}")

    return errors


def validate_nested_keys(chart: dict) -> list[str]:
    errors = []

    for parent_key, child_keys in REQUIRED_NESTED_KEYS.items():
        parent = chart.get(parent_key)

        if not isinstance(parent, dict):
            errors.append(f"Expected '{parent_key}' to be a dictionary")
            continue

        for child in child_keys:
            if child not in parent:
                errors.append(f"Missing nested key: {parent_key}.{child}")

    return errors


def validate_chart(chart: dict) -> list[str]:
    errors = []
    errors.extend(validate_top_level_keys(chart))
    errors.extend(validate_nested_keys(chart))
    return errors


def count_section_items(chart: dict) -> dict:
    def safe_len(value):
        return len(value) if isinstance(value, list) else 0

    counts = {
        "zodiac_tropical": safe_len(chart.get("zodiac", {}).get("tropical")),
        "zodiac_sidereal": safe_len(chart.get("zodiac", {}).get("sidereal")),
        "heliocentric_tropical": safe_len(chart.get("heliocentric", {}).get("tropical")),
        "heliocentric_sidereal": safe_len(chart.get("heliocentric", {}).get("sidereal")),
        "houses_tropical": safe_len(chart.get("houses", {}).get("tropical")),
        "houses_sidereal": safe_len(chart.get("houses", {}).get("sidereal")),
        "house_rulers_tropical": safe_len(chart.get("house_rulers", {}).get("tropical")),
        "house_rulers_sidereal": safe_len(chart.get("house_rulers", {}).get("sidereal")),
        "dignities_tropical": safe_len(chart.get("dignities", {}).get("tropical")),
        "dignities_sidereal": safe_len(chart.get("dignities", {}).get("sidereal")),
        "elements_tropical": safe_len(chart.get("elements", {}).get("tropical")),
        "elements_sidereal": safe_len(chart.get("elements", {}).get("sidereal")),
        "quadruplicities_tropical": safe_len(chart.get("quadruplicities", {}).get("tropical")),
        "quadruplicities_sidereal": safe_len(chart.get("quadruplicities", {}).get("sidereal")),
        "mutual_receptions_tropical": safe_len(chart.get("mutual_receptions", {}).get("tropical")),
        "mutual_receptions_sidereal": safe_len(chart.get("mutual_receptions", {}).get("sidereal")),
        "notes": safe_len(chart.get("notes")),
        "parser_warnings": safe_len(chart.get("parser_warnings")),
        "unresolved_values": safe_len(chart.get("unresolved_values")),
    }

    return counts


def print_chart_summary(chart: dict) -> None:
    metadata = chart.get("metadata", {})
    date_time = metadata.get("date_time", {})
    geo_location = metadata.get("geo_location", {})

    counts = count_section_items(chart)

    print("\n=== Chart Summary ===")
    print(f"Chart ID: {chart.get('chart_id', 'UNKNOWN')}")
    print(f"Chart Folder: {chart.get('chart_folder', 'UNKNOWN')}")
    print(f"Date: {date_time.get('Date', 'UNKNOWN')}")
    print(f"Location: {geo_location.get('Location', 'UNKNOWN')}")
    print("")
    print("Section counts:")
    for key, value in counts.items():
        print(f"  {key}: {value}")


def load_chart(chart_id: str) -> dict:
    paths = get_chart_paths(chart_id)

    if not paths["chart_dir"].exists():
        raise FileNotFoundError(f"Chart folder does not exist: {paths['chart_dir']}")

    chart = load_json_file(paths["normalized_chart"])

    errors = validate_chart(chart)
    if errors:
        error_text = "\n".join(errors)
        raise ValueError(f"Chart validation failed:\n{error_text}")

    return chart


def main():
    chart_id = input("Enter Chart ID: ").strip()

    if not chart_id:
        print("No Chart ID entered. Exiting.")
        sys.exit(1)

    try:
        chart = load_chart(chart_id)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    print_chart_summary(chart)
    print("\nChart loaded successfully.")


if __name__ == "__main__":
    main()