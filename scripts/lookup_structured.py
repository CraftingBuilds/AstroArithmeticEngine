from pathlib import Path
import json

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
STRUCTURED_FILE = ENGINE_ROOT / "derived" / "structured_building_blocks_v2.json"


def load_structured():
    if not STRUCTURED_FILE.exists():
        raise FileNotFoundError(f"Missing file: {STRUCTURED_FILE}")
    return json.loads(STRUCTURED_FILE.read_text(encoding="utf-8"))


def find_entries(entries, name_query):
    q = name_query.strip().lower()
    matches = []

    for entry in entries:
        outer_name = entry.get("name", "").strip().lower()
        parsed_name = entry.get("parsed", {}).get("name", "").strip().lower()

        if q == outer_name or q == parsed_name:
            matches.append(entry)

    return matches


def pretty_print_entry(entry):
    print("=" * 80)
    print(f"NAME: {entry.get('name')}")
    print(f"FAMILY: {entry.get('family')}")
    print(f"RELATIVE PATH: {entry.get('relative_path')}")
    print(f"SOURCE FILE: {entry.get('source_file')}")
    print("-" * 80)
    print(json.dumps(entry.get("parsed", {}), indent=2, ensure_ascii=False))
    print("=" * 80)
    print()


def main():
    entries = load_structured()

    print("Structured Lookup")
    print("-----------------")
    query = input("Enter exact entry name: ").strip()

    matches = find_entries(entries, query)

    if not matches:
        print(f"No matches found for: {query}")
        return

    print(f"\nFound {len(matches)} match(es).\n")

    for entry in matches:
        pretty_print_entry(entry)


if __name__ == "__main__":
    main()
