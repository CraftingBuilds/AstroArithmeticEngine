from pathlib import Path
import json
import re

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
SECURE_CHARTS = ENGINE_ROOT / "secure_charts"
SCHEMA_DIR = ENGINE_ROOT / "schema"
TEMPLATE_FILE = SCHEMA_DIR / "chart_template.json"


# =========================================================
# HELPERS
# =========================================================

def clean_text(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def split_lines(text: str):
    return clean_text(text).split("\n")


def load_chart_template():
    if not TEMPLATE_FILE.exists():
        raise FileNotFoundError(f"chart_template.json not found: {TEMPLATE_FILE}")
    with open(TEMPLATE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_body_name(name: str) -> str:
    mapping = {
        "ASC": "Ascendant",
        "DSC": "Descendant",
        "MC": "Midheaven",
        "IC": "Imum Coeli",
        "P/Fortune": "Part of Fortune",
        "Bl.Moon": "Black Moon",
        "Black Moon": "Black Moon",
        "N.Node": "North Node",
        "S.Node": "South Node",
    }
    return mapping.get(name.strip(), name.strip())


def normalize_aspect_name(abbrev: str) -> str:
    mapping = {
        "conj.": "Conjunction",
        "opp.": "Opposition",
        "tri.": "Trine",
        "sq.": "Square",
        "sext.": "Sextile",
        "s/sq.": "Semisquare",
        "s/sex.": "Semisextile",
        "sesq.": "Sesquiquadrate",
        "inconj.": "Inconjunction",
        "biq.": "Biquintile",
        "quin.": "Quincunx",  # confirmed operational assumption for now
    }
    return mapping.get(abbrev.strip(), abbrev.strip())


def ensure_chart_paths(chart_id: str):
    chart_dir = SECURE_CHARTS / chart_id
    raw_file = chart_dir / "raw_export.txt"

    normalized_file = chart_dir / "normalized_chart.json"
    aspects_file = chart_dir / "aspects.json"
    fixed_stars_file = chart_dir / "fixed_stars.json"
    parallels_file = chart_dir / "parallels.json"
    contra_parallels_file = chart_dir / "contra_parallels.json"

    if not chart_dir.exists():
        raise FileNotFoundError(f"Chart folder not found: {chart_dir}")

    if not raw_file.exists():
        raise FileNotFoundError(f"raw_export.txt not found: {raw_file}")

    return {
        "chart_dir": chart_dir,
        "raw_file": raw_file,
        "normalized_file": normalized_file,
        "aspects_file": aspects_file,
        "fixed_stars_file": fixed_stars_file,
        "parallels_file": parallels_file,
        "contra_parallels_file": contra_parallels_file,
    }


def get_section_block(text: str, start_header: str, next_headers: list[str]) -> str | None:
    start_idx = text.find(start_header)
    if start_idx == -1:
        return None

    start_idx += len(start_header)
    remainder = text[start_idx:]

    cut_positions = []
    for h in next_headers:
        idx = remainder.find(h)
        if idx != -1:
            cut_positions.append(idx)

    if cut_positions:
        end_idx = min(cut_positions)
        return remainder[:end_idx].strip()

    return remainder.strip()


def parse_key_value_block(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    data = {}
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return data

    last_key = None

    for raw_line in split_lines(block):
        if not raw_line.strip():
            continue

        parts = re.split(r"\t+", raw_line)

        # normal key/value row
        if len(parts) >= 2 and parts[0].strip():
            key = parts[0].strip()
            value = " ".join(p.strip() for p in parts[1:] if p.strip())
            data[key] = value
            last_key = key
            continue

        # continuation row (like GMT line under Time Zone)
        if last_key and len(parts) >= 1 and not parts[0].strip():
            continuation = " ".join(p.strip() for p in parts if p.strip())
            if continuation:
                if data[last_key]:
                    data[last_key] += " | " + continuation
                else:
                    data[last_key] = continuation
                continue

        unresolved_values.append({
            "section": section_name,
            "line": raw_line,
            "reason": "could not parse key/value row"
        })

    return data


# =========================================================
# PARSERS FOR SPECIFIC SECTIONS
# =========================================================

def parse_ecliptic_table(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    entries = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return entries

    for line in split_lines(block):
        raw_line = line
        line = line.strip()
        if not line:
            continue
        if line.startswith("Ecliptic longitude & latitude"):
            continue
        if line.startswith("Planet, celestial longitude, latitude"):
            continue

        parts = re.split(r"\t+", line)
        if len(parts) < 3:
            unresolved_values.append({
                "section": section_name,
                "line": raw_line,
                "reason": "could not parse ecliptic row; expected at least 3 columns"
            })
            continue

        body = normalize_body_name(parts[0])
        sign = parts[1].strip()
        degree = parts[2].strip()

        retrograde = False
        latitude = None

        if len(parts) >= 5:
            retrograde = parts[3].strip() == "R"
            latitude = parts[4].strip()
        elif len(parts) == 4:
            if parts[3].strip() == "R":
                retrograde = True
            else:
                latitude = parts[3].strip()
        elif len(parts) > 5:
            parser_warnings.append({
                "section": section_name,
                "line": raw_line,
                "reason": "extra columns detected in ecliptic row; parsed best-effort"
            })

        entries.append({
            "body": body,
            "sign": sign,
            "degree": degree,
            "retrograde": retrograde,
            "latitude": latitude
        })

    return entries


def parse_fixed_stars(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    rows = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return rows

    for line in split_lines(block):
        raw_line = line
        line = line.strip()
        if not line or line.startswith("Body, Star"):
            continue

        parts = re.split(r"\t+", line)
        if len(parts) < 4:
            unresolved_values.append({
                "section": section_name,
                "line": raw_line,
                "reason": "could not parse fixed star row; expected 4 columns"
            })
            continue

        rows.append({
            "body": normalize_body_name(parts[0]),
            "star": parts[1].strip(),
            "constellation": parts[2].strip(),
            "orb": parts[3].strip()
        })

    return rows


def parse_houses(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    houses = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return houses

    current_house = None

    for raw_line in split_lines(block):
        if not raw_line.strip():
            continue

        if raw_line.strip().startswith("Placidus"):
            continue

        parts = re.split(r"\t+", raw_line)

        # new house row
        if len(parts) >= 5 and parts[0].strip().isdigit():
            if current_house:
                houses.append(current_house)

            current_house = {
                "house_number": parts[0].strip(),
                "sign": parts[3].strip(),
                "cusp_degree": parts[4].strip(),
                "occupants": []
            }
            continue

        # occupant row
        # examples:
        # \tAscendant\t\tCap\t7º 08' 18"
        # \tMoon\t\tCap\t23º 48' 00"
        if current_house and len(parts) >= 4 and not parts[0].strip():
            body = parts[1].strip() if len(parts) > 1 else ""
            sign = parts[2].strip() if len(parts) > 2 else ""
            degree = parts[3].strip() if len(parts) > 3 else ""

            if body and sign and degree:
                current_house["occupants"].append({
                    "body": normalize_body_name(body),
                    "sign": sign,
                    "degree": degree
                })
                continue

        unresolved_values.append({
            "section": section_name,
            "line": raw_line,
            "reason": "could not parse house row"
        })

    if current_house:
        houses.append(current_house)

    return houses


def parse_house_rulers(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    rulers = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return rulers

    current = None

    for raw_line in split_lines(block):
        if not raw_line.strip():
            continue
        if raw_line.strip().startswith("House cusp in"):
            continue

        parts = re.split(r"\t+", raw_line)

        # Main ruler row
        if len(parts) >= 6 and parts[0].startswith("H "):
            if current:
                rulers.append(current)

            current = {
                "house": parts[0].replace("H ", "").strip(),
                "cusp_sign": parts[2].strip(),
                "rulers": [
                    {
                        "ruler": normalize_body_name(parts[4]),
                        "ruler_sign": parts[6].strip() if len(parts) > 6 else None,
                        "role": "primary"
                    }
                ]
            }
            continue

        # Continuation row for co-rulers / secondary rulers
        if current and len(parts) >= 3 and not parts[0].strip():
            ruler = normalize_body_name(parts[1]) if len(parts) > 1 else ""
            ruler_sign = parts[3].strip() if len(parts) > 3 else None
            if ruler:
                current["rulers"].append({
                    "ruler": ruler,
                    "ruler_sign": ruler_sign,
                    "role": "secondary"
                })
                continue

        unresolved_values.append({
            "section": section_name,
            "line": raw_line,
            "reason": "could not parse house ruler row"
        })

    if current:
        rulers.append(current)

    return rulers


def parse_dignities(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    rows = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return rows

    for raw_line in split_lines(block):
        line = raw_line.strip()
        if not line or line.startswith("Body, Sign"):
            continue

        parts = re.split(r"\t+", raw_line)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) < 3:
            unresolved_values.append({
                "section": section_name,
                "line": raw_line,
                "reason": "could not parse dignity row; expected at least 3 columns"
            })
            continue

        body = normalize_body_name(parts[0])
        sign = parts[1]

        essential = None
        house = None
        accidental = None

        dignity_hits = []

        for p in parts[2:]:
            if p.startswith("H "):
                house = p
            elif p in {"DIGN", "DETR", "EXALT", "FALL"}:
                dignity_hits.append(p)

        if len(dignity_hits) >= 1:
            essential = dignity_hits[0]
        if len(dignity_hits) >= 2:
            accidental = dignity_hits[1]
        if len(dignity_hits) > 2:
            parser_warnings.append({
                "section": section_name,
                "line": raw_line,
                "reason": "more than two dignity markers found; parsed best-effort"
            })

        rows.append({
            "body": body,
            "sign": sign,
            "essential_dignity": essential,
            "house": house,
            "accidental_dignity": accidental
        })

    return rows


def parse_element_or_modality(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    groups = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return groups

    current = None

    for raw_line in split_lines(block):
        if not raw_line.strip():
            continue

        line = raw_line.strip()
        if line.startswith("Element, Count") or line.startswith("Type, Count"):
            continue

        parts = re.split(r"\t+", raw_line)

        # New group row
        if len(parts) >= 3 and parts[0].strip():
            if current:
                groups.append(current)

            current = {
                "group": parts[0].strip(),
                "count": parts[1].strip(),
                "bodies": [normalize_body_name(parts[2].strip())]
            }
            continue

        # Continuation body row like: \tJupiter
        if current and len(parts) >= 2 and not parts[0].strip():
            body = None
            for p in parts[1:]:
                if p.strip():
                    body = normalize_body_name(p.strip())
                    break
            if body:
                current["bodies"].append(body)
                continue

        unresolved_values.append({
            "section": section_name,
            "line": raw_line,
            "reason": "could not parse element/modality row"
        })

    if current:
        groups.append(current)

    return groups


def parse_mutual_receptions(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    rows = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return rows

    for line in split_lines(block):
        raw_line = line
        line = line.strip()
        if not line or line.startswith("Body A"):
            continue
        if "None found" in line:
            return []

        parts = re.split(r"\t+", line)
        if len(parts) >= 5:
            rows.append({
                "body_a": normalize_body_name(parts[0]),
                "sign_a": parts[2].strip(),
                "body_b": normalize_body_name(parts[4]),
                "sign_b": parts[6].strip() if len(parts) > 6 else None
            })
        else:
            unresolved_values.append({
                "section": section_name,
                "line": raw_line,
                "reason": "could not parse mutual reception row"
            })

    return rows


def parse_parallel_block(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    rows = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return rows

    for line in split_lines(block):
        raw_line = line
        line = line.strip()
        if not line or line.startswith("Body A, Body B"):
            continue

        parts = re.split(r"\t+", line)
        if len(parts) < 5:
            unresolved_values.append({
                "section": section_name,
                "line": raw_line,
                "reason": "could not parse parallel/contra-parallel row"
            })
            continue

        rows.append({
            "body_a": normalize_body_name(parts[0]),
            "body_b": normalize_body_name(parts[1]),
            "dec_a": parts[2].strip(),
            "dec_b": parts[3].strip(),
            "orb": parts[4].strip()
        })

    return rows


def parse_aspects(block: str, section_name: str, parser_warnings: list, unresolved_values: list):
    rows = []
    if not block:
        parser_warnings.append({
            "section": section_name,
            "line": None,
            "reason": "section block missing or empty"
        })
        return rows

    for line in split_lines(block):
        raw_line = line
        line = line.strip()
        if not line or line.startswith("Body"):
            continue

        parts = re.split(r"\t+", line)
        if len(parts) < 4:
            unresolved_values.append({
                "section": section_name,
                "line": raw_line,
                "reason": "could not parse aspect row; expected at least 4 columns"
            })
            continue

        row = {
            "body_a": normalize_body_name(parts[0]),
            "aspect_abbrev": parts[1].strip(),
            "aspect_name": normalize_aspect_name(parts[1]),
            "body_b": normalize_body_name(parts[2]),
            "orb": parts[3].strip()
        }

        if len(parts) > 4:
            row["motion"] = parts[4].strip()
        if len(parts) > 5:
            row["phase"] = parts[5].strip()
        if len(parts) > 6:
            parser_warnings.append({
                "section": section_name,
                "line": raw_line,
                "reason": "extra columns detected in aspect row; parsed best-effort"
            })

        rows.append(row)

    return rows


# =========================================================
# MAIN PARSER
# =========================================================

def parse_timenomad_export(raw_text: str):
    text = clean_text(raw_text)
    parser_warnings = []
    unresolved_values = []

    section_headers = [
        "Date & Time",
        "Geo Location",
        "Summary",
        "Parameters",
        "Zodiac: tropical",
        "Zodiac: sidereal✦",
        "Heliocentric chart: tropical",
        "Heliocentric chart: sidereal✦",
        "Fixed Stars conjunctions",
        "Houses: tropical",
        "Houses: sidereal✦",
        "Rulers of Houses: tropical",
        "Rulers of Houses: sidereal✦",
        "Dignities: tropical",
        "Dignities: sidereal✦",
        "Triplicities / Elements: tropical",
        "Triplicities / Elements: sidereal✦",
        "Quadruplicities: tropical",
        "Quadruplicities: sidereal✦",
        "Mutual Receptions: tropical",
        "Mutual Receptions: sidereal✦",
        "Parallels",
        "Contra-Parallels",
        "Aspects",
    ]

    def block(name):
        next_headers = [h for h in section_headers if h != name]
        return get_section_block(text, name, next_headers)

    date_time = parse_key_value_block(block("Date & Time"), "Date & Time", parser_warnings, unresolved_values)
    geo_location = parse_key_value_block(block("Geo Location"), "Geo Location", parser_warnings, unresolved_values)
    summary = parse_key_value_block(block("Summary"), "Summary", parser_warnings, unresolved_values)
    parameters = parse_key_value_block(block("Parameters"), "Parameters", parser_warnings, unresolved_values)

    zodiac_tropical = parse_ecliptic_table(block("Zodiac: tropical"), "Zodiac: tropical", parser_warnings, unresolved_values)
    zodiac_sidereal = parse_ecliptic_table(block("Zodiac: sidereal✦"), "Zodiac: sidereal✦", parser_warnings, unresolved_values)
    heliocentric_tropical = parse_ecliptic_table(block("Heliocentric chart: tropical"), "Heliocentric chart: tropical", parser_warnings, unresolved_values)
    heliocentric_sidereal = parse_ecliptic_table(block("Heliocentric chart: sidereal✦"), "Heliocentric chart: sidereal✦", parser_warnings, unresolved_values)

    fixed_stars = parse_fixed_stars(block("Fixed Stars conjunctions"), "Fixed Stars conjunctions", parser_warnings, unresolved_values)

    houses_tropical = parse_houses(block("Houses: tropical"), "Houses: tropical", parser_warnings, unresolved_values)
    houses_sidereal = parse_houses(block("Houses: sidereal✦"), "Houses: sidereal✦", parser_warnings, unresolved_values)

    rulers_tropical = parse_house_rulers(block("Rulers of Houses: tropical"), "Rulers of Houses: tropical", parser_warnings, unresolved_values)
    rulers_sidereal = parse_house_rulers(block("Rulers of Houses: sidereal✦"), "Rulers of Houses: sidereal✦", parser_warnings, unresolved_values)

    dignities_tropical = parse_dignities(block("Dignities: tropical"), "Dignities: tropical", parser_warnings, unresolved_values)
    dignities_sidereal = parse_dignities(block("Dignities: sidereal✦"), "Dignities: sidereal✦", parser_warnings, unresolved_values)

    elements_tropical = parse_element_or_modality(block("Triplicities / Elements: tropical"), "Triplicities / Elements: tropical", parser_warnings, unresolved_values)
    elements_sidereal = parse_element_or_modality(block("Triplicities / Elements: sidereal✦"), "Triplicities / Elements: sidereal✦", parser_warnings, unresolved_values)

    quadruplicities_tropical = parse_element_or_modality(block("Quadruplicities: tropical"), "Quadruplicities: tropical", parser_warnings, unresolved_values)
    quadruplicities_sidereal = parse_element_or_modality(block("Quadruplicities: sidereal✦"), "Quadruplicities: sidereal✦", parser_warnings, unresolved_values)

    receptions_tropical = parse_mutual_receptions(block("Mutual Receptions: tropical"), "Mutual Receptions: tropical", parser_warnings, unresolved_values)
    receptions_sidereal = parse_mutual_receptions(block("Mutual Receptions: sidereal✦"), "Mutual Receptions: sidereal✦", parser_warnings, unresolved_values)

    parallels = parse_parallel_block(block("Parallels"), "Parallels", parser_warnings, unresolved_values)
    contra_parallels = parse_parallel_block(block("Contra-Parallels"), "Contra-Parallels", parser_warnings, unresolved_values)
    aspects = parse_aspects(block("Aspects"), "Aspects", parser_warnings, unresolved_values)

    chart = load_chart_template()

    chart["metadata"]["date_time"] = date_time
    chart["metadata"]["geo_location"] = geo_location
    chart["metadata"]["summary"] = summary
    chart["metadata"]["parameters"] = parameters

    chart["zodiac"]["tropical"] = zodiac_tropical
    chart["zodiac"]["sidereal"] = zodiac_sidereal

    chart["heliocentric"]["tropical"] = heliocentric_tropical
    chart["heliocentric"]["sidereal"] = heliocentric_sidereal

    chart["houses"]["tropical"] = houses_tropical
    chart["houses"]["sidereal"] = houses_sidereal

    chart["house_rulers"]["tropical"] = rulers_tropical
    chart["house_rulers"]["sidereal"] = rulers_sidereal

    chart["dignities"]["tropical"] = dignities_tropical
    chart["dignities"]["sidereal"] = dignities_sidereal

    chart["elements"]["tropical"] = elements_tropical
    chart["elements"]["sidereal"] = elements_sidereal

    chart["quadruplicities"]["tropical"] = quadruplicities_tropical
    chart["quadruplicities"]["sidereal"] = quadruplicities_sidereal

    chart["mutual_receptions"]["tropical"] = receptions_tropical
    chart["mutual_receptions"]["sidereal"] = receptions_sidereal

    chart["fixed_star_conjunctions"] = {
        "file_backed": True,
        "file_name": "fixed_stars.json"
    }

    chart["parallels"] = {
        "file_backed": True,
        "file_name": "parallels.json"
    }

    chart["contra_parallels"] = {
        "file_backed": True,
        "file_name": "contra_parallels.json"
    }

    chart["aspects"] = {
        "file_backed": True,
        "file_name": "aspects.json"
    }

    chart["source"]["source_type"] = "Time Nomad export"
    chart["source"]["raw_text_preserved"] = True
    chart["source"]["source_files"] = {
        "raw_export_file": "raw_export.txt",
        "normalized_chart_file": "normalized_chart.json",
        "fixed_stars_file": "fixed_stars.json",
        "parallels_file": "parallels.json",
        "contra_parallels_file": "contra_parallels.json",
        "aspects_file": "aspects.json"
    }

    if "notes" not in chart or not isinstance(chart["notes"], list):
        chart["notes"] = []

    chart["parser_warnings"] = parser_warnings
    chart["unresolved_values"] = unresolved_values

    sidecars = {
        "fixed_stars": fixed_stars,
        "parallels": parallels,
        "contra_parallels": contra_parallels,
        "aspects": aspects,
    }

    return chart, sidecars


def main():
    chart_id = input("Enter Chart ID (folder name in secure_charts): ").strip()
    if not chart_id:
        print("No Chart ID entered. Exiting.")
        return

    paths = ensure_chart_paths(chart_id)

    raw_text = paths["raw_file"].read_text(encoding="utf-8")
    normalized_chart, sidecars = parse_timenomad_export(raw_text)

    normalized_chart["chart_id"] = chart_id
    normalized_chart["chart_folder"] = str(paths["chart_dir"])

    paths["normalized_file"].write_text(
        json.dumps(normalized_chart, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    paths["fixed_stars_file"].write_text(
        json.dumps(sidecars["fixed_stars"], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    paths["parallels_file"].write_text(
        json.dumps(sidecars["parallels"], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    paths["contra_parallels_file"].write_text(
        json.dumps(sidecars["contra_parallels"], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    paths["aspects_file"].write_text(
        json.dumps(sidecars["aspects"], indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print("\nDone.")
    print(f"Chart folder:            {paths['chart_dir']}")
    print(f"Read from:               {paths['raw_file']}")
    print(f"Wrote normalized:        {paths['normalized_file']}")
    print(f"Wrote fixed stars:       {paths['fixed_stars_file']}")
    print(f"Wrote parallels:         {paths['parallels_file']}")
    print(f"Wrote contra-parallels:  {paths['contra_parallels_file']}")
    print(f"Wrote aspects:           {paths['aspects_file']}")
    print(f"Parser warnings:         {len(normalized_chart['parser_warnings'])}")
    print(f"Unresolved values:       {len(normalized_chart['unresolved_values'])}")


if __name__ == "__main__":
    main()
