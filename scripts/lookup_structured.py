from pathlib import Path
import json

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
STRUCTURED_FILE = ENGINE_ROOT / "derived" / "structured_building_blocks_v2.json"


def load_structured():
    if not STRUCTURED_FILE.exists():
        raise FileNotFoundError(f"Missing file: {STRUCTURED_FILE}")
    return json.loads(STRUCTURED_FILE.read_text(encoding="utf-8"))


def flatten_text(value):
    """
    Recursively flatten nested dict/list/string content into one lowercase text blob.
    """
    parts = []

    if isinstance(value, dict):
        for k, v in value.items():
            parts.append(str(k))
            parts.append(flatten_text(v))
    elif isinstance(value, list):
        for item in value:
            parts.append(flatten_text(item))
    elif value is None:
        pass
    else:
        parts.append(str(value))

    return " ".join(part for part in parts if part).lower()


def find_by_name(entries, query):
    q = query.strip().lower()
    matches = []

    for entry in entries:
        outer_name = entry.get("name", "").strip().lower()
        parsed_name = entry.get("parsed", {}).get("name", "").strip().lower()

        if q in outer_name or q in parsed_name:
            matches.append(entry)

    return matches


def find_by_word(entries, query):
    q = query.strip().lower()
    matches = []

    for entry in entries:
        searchable = flatten_text(entry.get("parsed", {}))
        if q in searchable:
            matches.append(entry)

    return matches


def find_by_theme(entries, query):
    """
    Theme search is broader than word search.
    It checks:
    - entry name
    - family
    - relative path
    - source file
    - all parsed content
    """
    q = query.strip().lower()
    matches = []

    for entry in entries:
        theme_blob = " ".join([
            entry.get("name", ""),
            entry.get("family", ""),
            entry.get("relative_path", ""),
            entry.get("source_file", ""),
            flatten_text(entry.get("parsed", {})),
        ]).lower()

        if q in theme_blob:
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
    print("Search modes: name | word | theme")
    mode = input("Enter search mode: ").strip().lower()
    query = input("Enter search query: ").strip()

    if not query:
        print("No query entered.")
        return

    if mode == "name":
        matches = find_by_name(entries, query)
    elif mode == "word":
        matches = find_by_word(entries, query)
    elif mode == "theme":
        matches = find_by_theme(entries, query)
    else:
        print(f"Invalid mode: {mode}")
        print("Use one of: name, word, theme")
        return

    if not matches:
        print(f"No matches found for [{mode}]: {query}")
        return

    print(f"\nFound {len(matches)} match(es) for [{mode}]: {query}\n")

    for entry in matches:
        pretty_print_entry(entry)


if __name__ == "__main__":
    main()