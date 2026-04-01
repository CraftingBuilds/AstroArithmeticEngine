from pathlib import Path
import json
import re

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
DERIVED_DIR = ENGINE_ROOT / "derived"

MASTER_INDEX_FILE = DERIVED_DIR / "building_blocks_master_index.json"
OUTPUT_FILE = DERIVED_DIR / "structured_building_blocks.json"


# =========================
# BASIC HELPERS
# =========================

def load_index():
    if not MASTER_INDEX_FILE.exists():
        raise FileNotFoundError(f"Missing index file: {MASTER_INDEX_FILE}")
    return json.loads(MASTER_INDEX_FILE.read_text(encoding="utf-8"))


def clean_text(text: str) -> str:
    if text is None:
        return ""
    text = text.replace("\u00a0", " ")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    return text.strip()


def split_lines(text: str):
    return [line.strip() for line in clean_text(text).split("\n")]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", clean_text(text))


def extract_between(text: str, start_label: str, end_labels=None):
    """
    Extract block after start_label until next matching end label.
    """
    if end_labels is None:
        end_labels = []

    pattern = re.escape(start_label) + r"\s*(.*)"
    start_match = re.search(pattern, text, re.DOTALL)
    if not start_match:
        return None

    start_index = start_match.start(1)
    remainder = text[start_index:]

    end_index = None
    for label in end_labels:
        m = re.search(r"\n\s*" + re.escape(label) + r"\s*", remainder)
        if m:
            candidate = m.start()
            if end_index is None or candidate < end_index:
                end_index = candidate

    if end_index is None:
        return clean_text(remainder)

    return clean_text(remainder[:end_index])


def extract_line_value(text: str, label: str):
    m = re.search(rf"^{re.escape(label)}\s*(.+)$", text, re.MULTILINE)
    if m:
        return clean_text(m.group(1))
    return None


def extract_inline_after_label(text: str, label: str):
    m = re.search(rf"{re.escape(label)}\s*(.+)", text)
    if m:
        return clean_text(m.group(1))
    return None


def extract_list_after_header(text: str, header: str, stop_headers=None):
    block = extract_between(text, header, stop_headers or [])
    if not block:
        return []

    items = []
    for line in split_lines(block):
        line = line.strip("•*- \t")
        if line:
            items.append(line)
    return items


def parse_colon_lines(block: str):
    """
    Parse lines like:
    Label: Value
    """
    data = {}
    for line in split_lines(block):
        if ":" in line:
            key, value = line.split(":", 1)
            data[normalize_space(key)] = clean_text(value)
    return data


def detect_family(entry):
    path = " / ".join(entry.get("category_path", []))

    if "Fixed Stars" in path:
        return "fixed_star"

    if "Aspects" in path:
        return "aspect"

    if "Houses" in path:
        return "house"

    if "Signs" in path:
        return "sign"

    if "Planets (Classic and Modern)" in path:
        return "planet"

    if any(x in path for x in [
        "Asteroids",
        "Calculated Points",
        "Centaurs & Deep Space Bodies",
        "Dwarf Planets & Distant Bodies",
        "Esoteric and Hypothetical Points",
        "Lunar Nodes & Moons",
        "Special Points in Advanced Systems",
    ]):
        return "body_point"

    return "unknown"


def parse_tags_from_block(text: str):
    lines = split_lines(text)
    tags = []

    capture = False
    for line in lines:
        low = line.lower()
        if low == "tags" or low == "🔖 tags":
            capture = True
            continue

        if capture:
            if not line:
                break
            if line.startswith("#"):
                tags.extend([tag.strip("#") for tag in line.split() if tag.startswith("#")])
            elif ":" not in line and len(line) < 80:
                tags.append(line)
            else:
                # stop if we've moved into another section
                break

    return tags


# =========================
# ASPECT PARSER
# =========================

def parse_aspect_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    name = entry["name"]
    aspect_degree = extract_line_value(text, "Aspect Degree:")
    glyph = extract_line_value(text, "Glyph:")

    description = extract_between(
        text,
        "Description:",
        ["KeyTraits:", "Example Interpretation:", "Use in Practice:"]
    )

    key_traits = extract_list_after_header(
        text,
        "KeyTraits:",
        ["Example Interpretation:", "Use in Practice:"]
    )

    example_interpretation = extract_between(
        text,
        "Example Interpretation:",
        ["Use in Practice:"]
    )

    use_in_practice = extract_between(
        text,
        "Use in Practice:",
        []
    )

    return {
        "name": name,
        "family": "aspect",
        "aspect_degree": aspect_degree,
        "glyph": glyph,
        "description": description,
        "key_traits": key_traits,
        "example_interpretation": example_interpretation,
        "use_in_practice": use_in_practice,
    }


# =========================
# BODY / POINT PARSER
# =========================

def parse_body_point_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    title_line = None
    for line in lines[:12]:
        if " – " in line or " - " in line:
            title_line = line
            break

    display_title = title_line if title_line else entry["name"]

    epithet = None
    if title_line:
        if " – " in title_line:
            parts = title_line.split(" – ", 1)
            epithet = clean_text(parts[1])
        elif " - " in title_line:
            parts = title_line.split(" - ", 1)
            epithet = clean_text(parts[1])

    tags = parse_tags_from_block(text)

    mythic_root = extract_between(
        text,
        "Mythic Root:",
        ["Core Function:", "Astrological Role:", "Orbital Signature", "Keywords / Powerwords"]
    )

    core_function = extract_between(
        text,
        "Core Function:",
        ["Astrological Role:", "Orbital Signature", "Keywords / Powerwords"]
    )

    astrological_role = extract_between(
        text,
        "Astrological Role:",
        ["Orbital Signature", "Keywords / Powerwords"]
    )

    orbital_block = extract_between(
        text,
        "Orbital Signature",
        ["Keywords / Powerwords", "House and Aspect Relevance", "Use in Astrology Arith(m)etic", "Backlinks"]
    )
    orbital_signature = parse_colon_lines(orbital_block) if orbital_block else {}

    keywords_block = extract_between(
        text,
        "Keywords / Powerwords",
        ["House and Aspect Relevance", "Use in Astrology Arith(m)etic", "Backlinks"]
    )
    keywords = []
    if keywords_block:
        keywords = [clean_text(x) for x in re.split(r",|\n", keywords_block) if clean_text(x)]

    house_aspect_block = extract_between(
        text,
        "House and Aspect Relevance",
        ["Use in Astrology Arith(m)etic", "Backlinks"]
    )
    house_aspect_relevance = parse_colon_lines(house_aspect_block) if house_aspect_block else {}

    ai_usage = extract_between(
        text,
        "Use in Astrology Arith(m)etic",
        ["Backlinks"]
    )

    backlinks_block = extract_between(
        text,
        "Backlinks",
        []
    )
    backlinks = []
    if backlinks_block:
        for line in split_lines(backlinks_block):
            if line:
                backlinks.append(line)

    return {
        "name": entry["name"],
        "display_title": display_title,
        "epithet": epithet,
        "family": "body_point",
        "tags": tags,
        "mythic_root": mythic_root,
        "core_function": core_function,
        "astrological_role": astrological_role,
        "orbital_signature": orbital_signature,
        "keywords": keywords,
        "house_aspect_relevance": house_aspect_relevance,
        "ai_usage": ai_usage,
        "backlinks": backlinks,
    }


# =========================
# FIXED STAR PARSER
# =========================

def parse_fixed_star_note(entry):
    text = clean_text(entry["content"])

    keywords_line = extract_line_value(text, "Keywords:")
    keywords = []
    if keywords_line:
        keywords = [clean_text(x) for x in keywords_line.split(",") if clean_text(x)]

    general_meaning = extract_between(
        text,
        "General Meaning:",
        ["High Expression:", "Shadow Expression:", "Metaphysical/Esoteric Layer:", "Ritual Application"]
    )

    high_expression_block = extract_between(
        text,
        "High Expression:",
        ["Shadow Expression:", "Metaphysical/Esoteric Layer:", "Ritual Application"]
    )
    high_expression = []
    if high_expression_block:
        high_expression = [line.strip("•*- \t") for line in split_lines(high_expression_block) if line]

    shadow_expression_block = extract_between(
        text,
        "Shadow Expression:",
        [f"{entry['name']} Conjunction:", "Description:", "Metaphysical/Esoteric Layer:", "Ritual Application"]
    )
    shadow_expression = []
    if shadow_expression_block:
        shadow_expression = [line.strip("•*- \t") for line in split_lines(shadow_expression_block) if line]

    conjunction_header = extract_line_value(text, f"{entry['name']} Conjunction:")
    if conjunction_header is None:
        m = re.search(rf"{re.escape(entry['name'])}\s+Conjunction:\s*(.+)", text)
        conjunction_header = clean_text(m.group(1)) if m else None

    conjunction_description = extract_between(
        text,
        "Description:",
        ["Examples:", "Metaphysical/Esoteric Layer:", "Ritual Application"]
    )

    examples_block = extract_between(
        text,
        "Examples:",
        ["Metaphysical/Esoteric Layer:", "Ritual Application"]
    )
    examples = []
    if examples_block:
        for line in split_lines(examples_block):
            if ":" in line:
                placement, meaning = line.split(":", 1)
                examples.append({
                    "placement": clean_text(placement),
                    "interpretation": clean_text(meaning)
                })
            elif line:
                examples.append({"text": line})

    metaphysical_layer = extract_between(
        text,
        "Metaphysical/Esoteric Layer:",
        ["Ritual Application"]
    )

    ritual_block = extract_between(
        text,
        "Ritual Application",
        []
    )

    ritual_application = {
        "overview": None,
        "ideal_for": [],
        "not_suited_for": [],
        "effective_timing": None,
        "affirmation": None,
    }

    if ritual_block:
        ritual_lines = split_lines(ritual_block)
        current_section = None
        overview_lines = []

        for line in ritual_lines:
            low = line.lower().rstrip(":")
            if low == "ideal for":
                current_section = "ideal_for"
                continue
            elif low == "not suited for":
                current_section = "not_suited_for"
                continue
            elif low == "effective timing":
                current_section = "effective_timing"
                continue
            elif low == "affirmation":
                current_section = "affirmation"
                continue

            if current_section is None:
                if line:
                    overview_lines.append(line)
            elif current_section in ("ideal_for", "not_suited_for"):
                if line:
                    ritual_application[current_section].append(line.strip("•*- \t"))
            elif current_section in ("effective_timing", "affirmation"):
                if line:
                    if ritual_application[current_section]:
                        ritual_application[current_section] += " " + line
                    else:
                        ritual_application[current_section] = line

        if overview_lines:
            ritual_application["overview"] = " ".join(overview_lines)

    return {
        "name": entry["name"],
        "family": "fixed_star",
        "keywords": keywords,
        "general_meaning": general_meaning,
        "high_expression": high_expression,
        "shadow_expression": shadow_expression,
        "conjunction_rule": conjunction_header,
        "conjunction_description": conjunction_description,
        "examples": examples,
        "metaphysical_layer": metaphysical_layer,
        "ritual_application": ritual_application,
    }


# =========================
# HOUSE PARSER
# =========================

def parse_house_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    title = None
    for line in lines[:10]:
        if "House of" in line:
            title = line
            break

    basic_assoc_block = extract_between(
        text,
        "✧ Core Association",
        ["🧭 Thematic Keywords", "🜂 House Description"]
    )
    basic_assoc = parse_colon_lines(basic_assoc_block) if basic_assoc_block else {}

    thematic_keywords = extract_list_after_header(
        text,
        "🧭 Thematic Keywords",
        ["🜂 House Description", "✴️ Core Themes & Manifestations"]
    )

    house_description = extract_between(
        text,
        "🜂 House Description",
        ["✴️ Core Themes & Manifestations", "🜍 Physical / Material Correspondences"]
    )

    core_themes_block = extract_between(
        text,
        "✴️ Core Themes & Manifestations",
        ["🜍 Physical / Material Correspondences", "💠 Metaphysical & Spiritual Layer"]
    )
    core_themes = parse_colon_lines(core_themes_block) if core_themes_block else {}

    physical_block = extract_between(
        text,
        "🜍 Physical / Material Correspondences",
        ["💠 Metaphysical & Spiritual Layer", "🔁 Opposing House Reflection"]
    )
    physical_correspondences = parse_colon_lines(physical_block) if physical_block else {}

    metaphysical_block = extract_between(
        text,
        "💠 Metaphysical & Spiritual Layer",
        ["🔁 Opposing House Reflection", "🪞 Example Interpretations"]
    )
    metaphysical_spiritual_layer = parse_colon_lines(metaphysical_block) if metaphysical_block else {}

    opposing_block = extract_between(
        text,
        "🔁 Opposing House Reflection",
        ["🪞 Example Interpretations", "✍🏼 Journal Prompts", "🕯️ Affirmation"]
    )
    opposing_house_reflection = parse_colon_lines(opposing_block) if opposing_block else {}

    example_block = extract_between(
        text,
        "🪞 Example Interpretations",
        ["✍🏼 Journal Prompts", "🕯️ Affirmation", "🔖 Tags"]
    )
    example_interpretations = []
    if example_block:
        lines = split_lines(example_block)
        i = 0
        while i < len(lines):
            line = lines[i]
            if line and i + 1 < len(lines):
                nxt = lines[i + 1]
                if nxt and ":" not in line and not line.startswith("🔖"):
                    example_interpretations.append({
                        "placement": line,
                        "interpretation": nxt
                    })
                    i += 2
                    continue
            if line:
                example_interpretations.append({"text": line})
            i += 1

    journal_prompts = extract_list_after_header(
        text,
        "✍🏼 Journal Prompts",
        ["🕯️ Affirmation", "🔖 Tags"]
    )

    affirmation = extract_between(
        text,
        "🕯️ Affirmation",
        ["🔖 Tags"]
    )

    tags = []
    tags_block = extract_between(text, "🔖 Tags", [])
    if tags_block:
        tags = [tag.strip("#") for tag in tags_block.split() if tag.startswith("#")]

    return {
        "name": entry["name"],
        "title": title,
        "family": "house",
        "core_association": basic_assoc,
        "thematic_keywords": thematic_keywords,
        "house_description": house_description,
        "core_themes_manifestations": core_themes,
        "physical_material_correspondences": physical_correspondences,
        "metaphysical_spiritual_layer": metaphysical_spiritual_layer,
        "opposing_house_reflection": opposing_house_reflection,
        "example_interpretations": example_interpretations,
        "journal_prompts": journal_prompts,
        "affirmation": affirmation,
        "tags": tags,
    }


# =========================
# SIGN PARSER
# =========================

def parse_sign_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    subtitle = None
    for line in lines[:10]:
        if "•" in line and entry["name"] in line:
            subtitle = line
            break

    basic_block = extract_between(
        text,
        "✧ Basic Information",
        ["🗣️ I AM Statement", "🔑 Core Traits"]
    )
    basic_information = parse_colon_lines(basic_block) if basic_block else {}

    iam_statement = extract_between(
        text,
        "🗣️ I AM Statement",
        ["🔑 Core Traits", "🌿 Strengths"]
    )

    core_traits = extract_list_after_header(
        text,
        "🔑 Core Traits",
        ["🌿 Strengths", "🜄 Challenges / Shadow Aspects"]
    )

    strengths = extract_list_after_header(
        text,
        "🌿 Strengths",
        ["🜄 Challenges / Shadow Aspects", "🜚 Behavioral Patterns & Archetype"]
    )

    challenges = extract_list_after_header(
        text,
        "🜄 Challenges / Shadow Aspects",
        ["🜚 Behavioral Patterns & Archetype", "🌌 In Relationships"]
    )

    behavioral_block = extract_between(
        text,
        "🜚 Behavioral Patterns & Archetype",
        ["🌌 In Relationships", "🪷 Spiritual Pathways"]
    )
    behavioral_patterns = parse_colon_lines(behavioral_block) if behavioral_block else {}
    behavioral_summary = None
    if behavioral_block:
        # keep non-colon prose too
        non_colon_lines = [line for line in split_lines(behavioral_block) if ":" not in line]
        if non_colon_lines:
            behavioral_summary = " ".join(non_colon_lines)

    relationships_block = extract_between(
        text,
        "🌌 In Relationships",
        ["🪷 Spiritual Pathways", "✍🏼 Journal Prompts"]
    )
    relationships = parse_colon_lines(relationships_block) if relationships_block else {}

    spiritual_block = extract_between(
        text,
        "🪷 Spiritual Pathways",
        ["✍🏼 Journal Prompts", "🛠️ Use in Practice"]
    )
    spiritual_pathways = parse_colon_lines(spiritual_block) if spiritual_block else {}

    journal_prompts = extract_list_after_header(
        text,
        "✍🏼 Journal Prompts",
        ["🛠️ Use in Practice", "🌠 Fixed Stars & Notable Degrees", "🕯️ Affirmation"]
    )

    use_in_practice = extract_between(
        text,
        "🛠️ Use in Practice",
        ["🌠 Fixed Stars & Notable Degrees", "🕯️ Affirmation", "🔖 Tags"]
    )

    fixed_stars_block = extract_between(
        text,
        "🌠 Fixed Stars & Notable Degrees",
        ["🕯️ Affirmation", "🔖 Tags"]
    )
    fixed_stars_notable_degrees = []
    if fixed_stars_block:
        for line in split_lines(fixed_stars_block):
            if line.lower().startswith("degree"):
                continue
            if line:
                fixed_stars_notable_degrees.append(line)

    affirmation = extract_between(
        text,
        "🕯️ Affirmation",
        ["🔖 Tags"]
    )

    tags = []
    tags_block = extract_between(text, "🔖 Tags", [])
    if tags_block:
        tags = [tag.strip("#") for tag in tags_block.split() if tag.startswith("#")]

    return {
        "name": entry["name"],
        "subtitle": subtitle,
        "family": "sign",
        "basic_information": basic_information,
        "iam_statement": iam_statement,
        "core_traits": core_traits,
        "strengths": strengths,
        "challenges": challenges,
        "behavioral_patterns": {
            **behavioral_patterns,
            "summary": behavioral_summary,
        },
        "relationships": relationships,
        "spiritual_pathways": spiritual_pathways,
        "journal_prompts": journal_prompts,
        "use_in_practice": use_in_practice,
        "fixed_stars_notable_degrees": fixed_stars_notable_degrees,
        "affirmation": affirmation,
        "tags": tags,
    }


# =========================
# PLANET PARSER
# =========================

def parse_planet_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    subtitle = None
    for line in lines[:10]:
        if " – " in line or " - " in line:
            if entry["name"] in line:
                subtitle = line
                break

    description = extract_between(
        text,
        "Description:",
        ["Natal Chart:", "Soul Path:", "Transit Influence:", "Progressed Expression:"]
    )

    natal_chart = extract_between(
        text,
        "Natal Chart:",
        ["Soul Path:", "Transit Influence:", "Progressed Expression:", "Mundane Astrology:"]
    )

    soul_path = extract_between(
        text,
        "Soul Path:",
        ["Transit Influence:", "Progressed Expression:", "Mundane Astrology:", "Keywords / Powerwords:"]
    )

    transit_influence = extract_between(
        text,
        "Transit Influence:",
        ["Progressed Expression:", "Mundane Astrology:", "Keywords / Powerwords:"]
    )

    progressed_expression = extract_between(
        text,
        "Progressed Expression:",
        ["Mundane Astrology:", "Keywords / Powerwords:"]
    )

    mundane_astrology = extract_between(
        text,
        "Mundane Astrology:",
        ["Keywords / Powerwords:", "Essential Dignitaries:", "Time-Table:"]
    )

    keywords_block = extract_between(
        text,
        "Keywords / Powerwords:",
        ["Essential Dignitaries:", "Time-Table:", "Fixed Star Associations:", "Correspondences"]
    )
    keywords = []
    if keywords_block:
        keywords = [clean_text(x) for x in re.split(r",|\n", keywords_block) if clean_text(x)]

    dignities_block = extract_between(
        text,
        "Essential Dignitaries:",
        ["Time-Table:", "Fixed Star Associations:", "Correspondences"]
    )
    essential_dignities = parse_colon_lines(dignities_block) if dignities_block else {}

    timetable_block = extract_between(
        text,
        "Time-Table:",
        ["Fixed Star Associations:", "Correspondences"]
    )
    timetable = parse_colon_lines(timetable_block) if timetable_block else {}

    fixed_star_block = extract_between(
        text,
        "Fixed Star Associations:",
        ["Correspondences"]
    )
    fixed_star_associations = []
    if fixed_star_block:
        for line in split_lines(fixed_star_block):
            if ":" in line:
                star, meaning = line.split(":", 1)
                fixed_star_associations.append({
                    "star": clean_text(star),
                    "meaning": clean_text(meaning)
                })
            elif line:
                fixed_star_associations.append({"text": line})

    correspondences_block = extract_between(
        text,
        "Correspondences",
        []
    )
    correspondences = parse_colon_lines(correspondences_block) if correspondences_block else {}

    return {
        "name": entry["name"],
        "subtitle": subtitle,
        "family": "planet",
        "description": description,
        "reading_modes": {
            "natal_chart": natal_chart,
            "soul_path": soul_path,
            "transit_influence": transit_influence,
            "progressed_expression": progressed_expression,
            "mundane_astrology": mundane_astrology,
        },
        "keywords": keywords,
        "essential_dignities": essential_dignities,
        "time_table": timetable,
        "fixed_star_associations": fixed_star_associations,
        "correspondences": correspondences,
    }


# =========================
# UNKNOWN / FALLBACK
# =========================

def parse_unknown(entry):
    return {
        "name": entry["name"],
        "family": "unknown",
    }


def parse_entry(entry):
    family = detect_family(entry)

    if family == "aspect":
        parsed = parse_aspect_note(entry)
    elif family == "body_point":
        parsed = parse_body_point_note(entry)
    elif family == "fixed_star":
        parsed = parse_fixed_star_note(entry)
    elif family == "house":
        parsed = parse_house_note(entry)
    elif family == "sign":
        parsed = parse_sign_note(entry)
    elif family == "planet":
        parsed = parse_planet_note(entry)
    else:
        parsed = parse_unknown(entry)

    return {
        "name": entry["name"],
        "family": family,
        "category_path": entry.get("category_path", []),
        "relative_path": entry.get("relative_path"),
        "source_file": entry.get("source_file"),
        "parsed": parsed,
        "raw_content": entry.get("content", ""),
    }


def main():
    entries = load_index()
    structured = []

    family_counts = {}

    for entry in entries:
        out = parse_entry(entry)
        structured.append(out)
        fam = out["family"]
        family_counts[fam] = family_counts.get(fam, 0) + 1

    OUTPUT_FILE.write_text(
        json.dumps(structured, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

    print(f"Structured building blocks written to: {OUTPUT_FILE}")
    print(f"Total entries: {len(structured)}")
    print("Family counts:")
    for family, count in sorted(family_counts.items()):
        print(f"  {family}: {count}")


if __name__ == "__main__":
    main()
