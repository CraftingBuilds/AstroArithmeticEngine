from pathlib import Path
import json
import re

ENGINE_ROOT = Path("/mnt/storage/AstroArithmeticEngine")
DERIVED_DIR = ENGINE_ROOT / "derived"

MASTER_INDEX_FILE = DERIVED_DIR / "building_blocks_master_index.json"
OUTPUT_FILE = DERIVED_DIR / "structured_building_blocks_v2.json"


# =========================================================
# GLYPH REGISTRY + SAFE RESOLUTION
# =========================================================

GLYPH_MAP = {
    "Sun": "☉",
    "Moon": "☽",
    "Mercury": "☿",
    "Venus": "♀",
    "Earth": "♁",
    "Mars": "♂",
    "Jupiter": "♃",
    "Saturn": "♄",
    "Uranus": "♅",
    "Neptune": "♆",
    "Pluto": "♇",
    "North Node": "☊",
    "South Node": "☋",
    "Ceres": "⚳",
    "Eris": "⚴",
    "Makemake": "⚵",
    "Haumea": "⚶",
    "Aries": "♈",
    "Taurus": "♉",
    "Gemini": "♊",
    "Cancer": "♋",
    "Leo": "♌",
    "Virgo": "♍",
    "Libra": "♎",
    "Scorpio": "♏",
    "Sagittarius": "♐",
    "Capricorn": "♑",
    "Aquarius": "♒",
    "Pisces": "♓",
}

KNOWN_GLYPHS = set(GLYPH_MAP.values()) | {
    "♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓",
    "☊", "☋", "⚳", "⚴", "⚵", "⚶", "⚸"
}


def generate_shortcode(name: str) -> str:
    parts = re.split(r"[\s\-/]+", name.strip())
    parts = [p for p in parts if p]
    if not parts:
        return "UNK"
    if len(parts) == 1:
        return parts[0][:3].upper()
    return "".join(p[0] for p in parts[:3]).upper()


def extract_explicit_glyph(text: str):
    """
    Only trust a dedicated 'Glyph:' field.
    Do NOT treat random em dashes in prose as missing glyphs.
    """
    m = re.search(r'^\s*Glyph:\s*(.*?)\s*$', text, re.MULTILINE)
    if not m:
        return None
    value = m.group(1).strip()
    if value in ("", "—", "-", "N/A", "n/a", "None", "none"):
        return None
    return value


def extract_inline_label_value(text: str, label: str, stop_labels=None):
    """
    Extract value for inline labels like:
    Aspect Degree: 0 Glyph: ♂ Description: ...
    """
    if stop_labels is None:
        stop_labels = []

    pattern = re.escape(label) + r"\s*(.*)"
    m = re.search(pattern, text, re.DOTALL)
    if not m:
        return None

    remainder = m.group(1)

    stop_index = None
    for stop in stop_labels:
        sm = re.search(r"\b" + re.escape(stop) + r"\s*", remainder)
        if sm:
            idx = sm.start()
            if stop_index is None or idx < stop_index:
                stop_index = idx

    value = remainder if stop_index is None else remainder[:stop_index]
    value = clean_text(value)
    return value if value else None


def extract_aspect_degree_and_glyph(text: str):
    """
    Handles both:
    Aspect Degree: 0
    Glyph: ♂

    and:
    Aspect Degree: 0 Glyph: ♂
    """
    degree = extract_inline_label_value(
        text,
        "Aspect Degree:",
        stop_labels=["Glyph:", "Description:", "KeyTraits:", "Example Interpretation:", "Use in Practice:"]
    )

    glyph = extract_inline_label_value(
        text,
        "Glyph:",
        stop_labels=["Description:", "KeyTraits:", "Example Interpretation:", "Use in Practice:"]
    )

    if glyph in ("", "—", "-", "N/A", "n/a", "None", "none"):
        glyph = None

    return degree, glyph


def extract_title_leading_glyph(lines):
    """
    Check the first few meaningful lines for a leading glyph token only.
    Example: '♃ Jupiter – The Expanding Flame of Wisdom'
    """
    for line in lines[:8]:
        s = line.strip()
        if not s:
            continue
        first = s.split()[0]
        if first in KNOWN_GLYPHS:
            return first
    return None


def resolve_glyph(name: str, text: str, lines):
    explicit = extract_explicit_glyph(text)
    if explicit:
        return {"glyph": explicit, "glyph_class": "explicit_field"}

    title_glyph = extract_title_leading_glyph(lines)
    if title_glyph:
        return {"glyph": title_glyph, "glyph_class": "title_glyph"}

    if name in GLYPH_MAP:
        return {"glyph": GLYPH_MAP[name], "glyph_class": "standard_unicode"}

    return {"glyph": generate_shortcode(name), "glyph_class": "shortcode"}


# =========================================================
# BASIC HELPERS
# =========================================================

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
    return [line.rstrip() for line in clean_text(text).split("\n")]


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", clean_text(text))


def strip_md(text: str) -> str:
    if text is None:
        return ""
    t = clean_text(text)
    t = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", t)
    t = re.sub(r"\[\[([^\]]+)\]\]", r"\1", t)
    t = re.sub(r"[*_`>#]", "", t)
    t = re.sub(r"^\s*[-•]\s*", "", t)
    t = normalize_space(t)
    return t


def clean_key(key: str) -> str:
    return strip_md(key).strip(": ").strip()


def is_heading_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return False
    if s.startswith("#"):
        return True
    if s in ("---", "***", "___"):
        return True
    if re.match(r"^[#]{1,6}\s+", s):
        return True
    return False


def heading_matches(line: str, heading: str) -> bool:
    s = line.strip()
    h = heading.strip()
    if s == h:
        return True
    if strip_md(s) == strip_md(h):
        return True
    if s.startswith(h):
        return True
    return False


def find_heading_index(lines, heading):
    for i, line in enumerate(lines):
        if heading_matches(line, heading):
            return i
    return None


def collect_block(lines, start_heading, stop_headings=None):
    """
    Collect lines after a heading until next matching stop heading, or next markdown divider/major heading.
    """
    if stop_headings is None:
        stop_headings = []

    start_idx = find_heading_index(lines, start_heading)
    if start_idx is None:
        return None

    collected = []
    i = start_idx + 1

    while i < len(lines):
        line = lines[i]
        s = line.strip()

        if any(heading_matches(line, h) for h in stop_headings):
            break

        if s in ("---", "***", "___"):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines) and is_heading_line(lines[j]):
                break

        if collected and is_heading_line(line):
            break

        collected.append(line)
        i += 1

    return "\n".join(collected).strip()


def parse_bullets(block: str):
    if not block:
        return []
    out = []
    for line in split_lines(block):
        s = line.strip()
        if not s or s in ("---", "***", "___"):
            continue
        s = re.sub(r"^\s*[-•]\s*", "", s)
        s = strip_md(s)
        if s:
            out.append(s)
    return out


def parse_colon_lines(block: str):
    data = {}
    if not block:
        return data
    for line in split_lines(block):
        s = line.strip()
        if not s or s in ("---", "***", "___") or is_heading_line(s):
            continue
        s = re.sub(r"^\s*[-•]\s*", "", s)
        if ":" in s:
            key, value = s.split(":", 1)
            ck = clean_key(key)
            cv = strip_md(value)
            if ck:
                data[ck] = cv
    return data


def parse_tags_block(block: str):
    if not block:
        return []
    tags = []
    for token in block.replace("\n", " ").split():
        if token.startswith("#"):
            tags.append(token.strip("#"))
    return tags


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


# =========================================================
# PARSER FAMILIES
# =========================================================

def parse_aspect_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    aspect_degree, inline_glyph = extract_aspect_degree_and_glyph(text)

    if inline_glyph:
        glyph_info = {"glyph": inline_glyph, "glyph_class": "inline_field"}
    else:
        glyph_info = resolve_glyph(entry["name"], text, lines)

    description = collect_block(lines, "Description:", ["KeyTraits:", "Example Interpretation:", "Use in Practice:"])
    key_traits = parse_bullets(collect_block(lines, "KeyTraits:", ["Example Interpretation:", "Use in Practice:"]))
    example_interpretation = collect_block(lines, "Example Interpretation:", ["Use in Practice:"])
    use_in_practice = collect_block(lines, "Use in Practice:", [])

    if not description:
        description = extract_inline_label_value(
            text,
            "Description:",
            stop_labels=["KeyTraits:", "Example Interpretation:", "Use in Practice:"]
        )

    if not key_traits:
        key_block = extract_inline_label_value(
            text,
            "KeyTraits:",
            stop_labels=["Example Interpretation:", "Use in Practice:"]
        )
        if key_block:
            pieces = re.split(r"\s+-\s+", " " + key_block)
            key_traits = [strip_md(x) for x in pieces if strip_md(x)]

    if not example_interpretation:
        example_interpretation = extract_inline_label_value(
            text,
            "Example Interpretation:",
            stop_labels=["Use in Practice:"]
        )

    if not use_in_practice:
        use_in_practice = extract_inline_label_value(
            text,
            "Use in Practice:",
            stop_labels=[]
        )

    return {
        "name": entry["name"],
        "family": "aspect",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
        "aspect_degree": strip_md(aspect_degree) if aspect_degree else None,
        "description": strip_md(description) if description else None,
        "key_traits": key_traits,
        "example_interpretation": strip_md(example_interpretation) if example_interpretation else None,
        "use_in_practice": strip_md(use_in_practice) if use_in_practice else None,
    }


def parse_body_point_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)
    glyph_info = resolve_glyph(entry["name"], text, lines)

    display_title = entry["name"]
    epithet = None
    for line in lines[:12]:
        s = strip_md(line)
        if " – " in s:
            display_title = s
            _, right = s.split(" – ", 1)
            epithet = right.strip()
            break
        if " - " in s:
            display_title = s
            _, right = s.split(" - ", 1)
            epithet = right.strip()
            break

    tags = []
    tags_idx = find_heading_index(lines, "tags")
    if tags_idx is not None:
        i = tags_idx + 1
        while i < len(lines):
            s = lines[i].strip()
            if not s:
                i += 1
                continue
            if is_heading_line(s) or s in ("Interpretive Basis", "Orbital Signature", "House and Aspect Relevance", "Backlinks"):
                break
            if ":" not in s and len(s) < 80:
                tags.append(strip_md(s))
                i += 1
                continue
            break

    mythic_root = collect_block(lines, "Mythic Root:", ["Core Function:", "Astrological Role:", "Orbital Signature"])
    core_function = collect_block(lines, "Core Function:", ["Astrological Role:", "Orbital Signature"])
    astrological_role = collect_block(lines, "Astrological Role:", ["Orbital Signature", "Keywords / Powerwords", "House and Aspect Relevance"])

    orbital_signature = parse_colon_lines(collect_block(lines, "Orbital Signature", ["Keywords / Powerwords", "House and Aspect Relevance", "Use in Astrology Arith(m)etic", "Backlinks"]))

    keywords_block = collect_block(lines, "Keywords / Powerwords", ["House and Aspect Relevance", "Use in Astrology Arith(m)etic", "Backlinks"])
    keywords = []
    if keywords_block:
        keywords = [strip_md(x) for x in re.split(r",|\n", keywords_block) if strip_md(x)]

    house_aspect_relevance = parse_colon_lines(collect_block(lines, "House and Aspect Relevance", ["Use in Astrology Arith(m)etic", "Backlinks"]))
    ai_usage = collect_block(lines, "Use in Astrology Arith(m)etic", ["Backlinks"])
    backlinks = parse_bullets(collect_block(lines, "Backlinks", []))

    return {
        "name": entry["name"],
        "display_title": display_title,
        "epithet": epithet,
        "family": "body_point",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
        "tags": tags,
        "mythic_root": strip_md(mythic_root) if mythic_root else None,
        "core_function": strip_md(core_function) if core_function else None,
        "astrological_role": strip_md(astrological_role) if astrological_role else None,
        "orbital_signature": orbital_signature,
        "keywords": keywords,
        "house_aspect_relevance": house_aspect_relevance,
        "ai_usage": strip_md(ai_usage) if ai_usage else None,
        "backlinks": backlinks,
    }


def parse_fixed_star_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)
    glyph_info = resolve_glyph(entry["name"], text, lines)

    kw_match = re.search(r'^\s*Keywords:\s*(.+)$', text, re.MULTILINE)
    keywords = [strip_md(x) for x in kw_match.group(1).split(",")] if kw_match else []

    general_meaning = collect_block(lines, "General Meaning:", ["High Expression:", "Shadow Expression:", f"{entry['name']} Conjunction:", "Metaphysical/Esoteric Layer:", "Ritual Application"])
    high_expression = parse_bullets(collect_block(lines, "High Expression:", ["Shadow Expression:", f"{entry['name']} Conjunction:", "Metaphysical/Esoteric Layer:", "Ritual Application"]))
    shadow_expression = parse_bullets(collect_block(lines, "Shadow Expression:", [f"{entry['name']} Conjunction:", "Metaphysical/Esoteric Layer:", "Ritual Application"]))

    conj_block = collect_block(lines, f"{entry['name']} Conjunction:", ["Description:", "Examples:", "Metaphysical/Esoteric Layer:", "Ritual Application"])
    conjunction_rule = strip_md(conj_block) if conj_block else None

    conjunction_description = collect_block(lines, "Description:", ["Examples:", "Metaphysical/Esoteric Layer:", "Ritual Application"])
    examples_block = collect_block(lines, "Examples:", ["Metaphysical/Esoteric Layer:", "Ritual Application"])
    examples = []
    if examples_block:
        for line in split_lines(examples_block):
            s = line.strip()
            if not s or is_heading_line(s):
                continue
            if ":" in s:
                a, b = s.split(":", 1)
                examples.append({
                    "placement": strip_md(a),
                    "interpretation": strip_md(b)
                })
            else:
                examples.append({"text": strip_md(s)})

    metaphysical_layer = collect_block(lines, "Metaphysical/Esoteric Layer:", ["Ritual Application"])
    ritual_block = collect_block(lines, "Ritual Application", [])

    ritual_application = {
        "overview": None,
        "ideal_for": [],
        "not_suited_for": [],
        "effective_timing": None,
        "affirmation": None,
    }

    if ritual_block:
        mode = None
        overview = []
        for line in split_lines(ritual_block):
            s = line.strip()
            ss = strip_md(s).rstrip(":")
            if not s or s in ("---", "***", "___"):
                continue
            low = ss.lower()
            if low == "ideal for":
                mode = "ideal_for"
                continue
            if low == "not suited for":
                mode = "not_suited_for"
                continue
            if low == "effective timing":
                mode = "effective_timing"
                continue
            if low == "affirmation":
                mode = "affirmation"
                continue

            if mode is None:
                overview.append(strip_md(s))
            elif mode in ("ideal_for", "not_suited_for"):
                ritual_application[mode].append(strip_md(s))
            else:
                if ritual_application[mode]:
                    ritual_application[mode] += " " + strip_md(s)
                else:
                    ritual_application[mode] = strip_md(s)

        if overview:
            ritual_application["overview"] = " ".join(overview)

    return {
        "name": entry["name"],
        "family": "fixed_star",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
        "keywords": [k for k in keywords if k],
        "general_meaning": strip_md(general_meaning) if general_meaning else None,
        "high_expression": high_expression,
        "shadow_expression": shadow_expression,
        "conjunction_rule": conjunction_rule,
        "conjunction_description": strip_md(conjunction_description) if conjunction_description else None,
        "examples": examples,
        "metaphysical_layer": strip_md(metaphysical_layer) if metaphysical_layer else None,
        "ritual_application": ritual_application,
    }


def parse_house_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)
    glyph_info = resolve_glyph(entry["name"], text, lines)

    title = None
    for line in lines[:12]:
        s = strip_md(line)
        if "House of" in s:
            title = s
            break

    core_association = parse_colon_lines(collect_block(lines, "✧ Core Association", ["🧭 Thematic Keywords", "## 🧭 Thematic Keywords", "🜂 House Description", "## 🜂 House Description"]))
    thematic_keywords = parse_bullets(collect_block(lines, "🧭 Thematic Keywords", ["🜂 House Description", "## 🜂 House Description"]))
    house_description = collect_block(lines, "🜂 House Description", ["✴️ Core Themes & Manifestations", "## ✴", "🜍 Physical / Material Correspondences", "## 🜍"])
    core_themes = parse_colon_lines(collect_block(lines, "✴️ Core Themes & Manifestations", ["🜍 Physical / Material Correspondences", "## 🜍"]))
    physical = parse_colon_lines(collect_block(lines, "🜍 Physical / Material Correspondences", ["💠 Metaphysical & Spiritual Layer", "## 💠"]))
    metaphysical = parse_colon_lines(collect_block(lines, "💠 Metaphysical & Spiritual Layer", ["🔁 Opposing House Reflection", "## 🔁"]))

    opposing = collect_block(lines, "🔁 Opposing House Reflection", ["🪞 Example Interpretations", "## 🪞", "✍🏼 Journal Prompts", "## ✍🏼", "🕯️ Affirmation", "## 🕯️"])
    opposing_lines = split_lines(opposing) if opposing else []
    opposing_house_reflection = {}
    axis_interpretation = None
    if opposing_lines:
        first_part = []
        rest = []
        seen_noncolon = False
        for ln in opposing_lines:
            if ":" in ln and not seen_noncolon:
                first_part.append(ln)
            else:
                seen_noncolon = True
                rest.append(ln)
        opposing_house_reflection = parse_colon_lines("\n".join(first_part))
        axis_interpretation = strip_md("\n".join(rest)) if rest else None
        if axis_interpretation:
            opposing_house_reflection["Axis Interpretation"] = axis_interpretation

    examples_block = collect_block(lines, "🪞 Example Interpretations", ["✍🏼 Journal Prompts", "## ✍🏼", "🕯️ Affirmation", "## 🕯️"])
    example_interpretations = []
    if examples_block:
        ex_lines = [ln.strip() for ln in split_lines(examples_block) if ln.strip() and ln.strip() not in ("---", "***", "___")]
        i = 0
        while i < len(ex_lines):
            current = ex_lines[i]
            nxt = ex_lines[i + 1] if i + 1 < len(ex_lines) else None
            if current and nxt and not current.startswith(">") and nxt.startswith(">"):
                example_interpretations.append({
                    "placement": strip_md(current),
                    "interpretation": strip_md(nxt.lstrip("> ").strip())
                })
                i += 2
            else:
                example_interpretations.append({"text": strip_md(current)})
                i += 1

    journal_prompts = parse_bullets(collect_block(lines, "✍🏼 Journal Prompts", ["🕯️ Affirmation", "## 🕯️", "🔖 Tags", "## 🔖"]))
    affirmation = collect_block(lines, "🕯️ Affirmation", ["🔖 Tags", "## 🔖"])
    tags = parse_tags_block(collect_block(lines, "🔖 Tags", []))

    return {
        "name": entry["name"],
        "title": title,
        "family": "house",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
        "core_association": core_association,
        "thematic_keywords": thematic_keywords,
        "house_description": strip_md(house_description) if house_description else None,
        "core_themes_manifestations": core_themes,
        "physical_material_correspondences": physical,
        "metaphysical_spiritual_layer": metaphysical,
        "opposing_house_reflection": opposing_house_reflection,
        "example_interpretations": example_interpretations,
        "journal_prompts": journal_prompts,
        "affirmation": strip_md(affirmation) if affirmation else None,
        "tags": tags,
    }


def parse_sign_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)

    basic_information = parse_colon_lines(collect_block(lines, "✧ Basic Information", ["🗣️ I AM Statement", "## 🗣️", "🔑 Core Traits", "## 🔑"]))

    sign_symbol = basic_information.get("Symbol")
    if sign_symbol and sign_symbol not in ("—", "-", "None", "none"):
        glyph_info = {"glyph": sign_symbol, "glyph_class": "sign_symbol"}
    else:
        glyph_info = resolve_glyph(entry["name"], text, lines)

    subtitle = None
    for line in lines[:10]:
        s = strip_md(line)
        if entry["name"] in s and "•" in s:
            subtitle = s
            break

    iam_statement = collect_block(lines, "🗣️ I AM Statement", ["🔑 Core Traits", "## 🔑", "🌿 Strengths", "## 🌿"])
    core_traits = parse_bullets(collect_block(lines, "🔑 Core Traits", ["🌿 Strengths", "## 🌿"]))
    strengths = parse_bullets(collect_block(lines, "🌿 Strengths", ["🜄 Challenges / Shadow Aspects", "## 🜄"]))
    challenges = parse_bullets(collect_block(lines, "🜄 Challenges / Shadow Aspects", ["🜚 Behavioral Patterns & Archetype", "## 🜚"]))

    behavioral_block = collect_block(lines, "🜚 Behavioral Patterns & Archetype", ["🌌 In Relationships", "## 🌌", "🪷 Spiritual Pathways", "## 🪷"])
    behavioral_patterns = parse_colon_lines(behavioral_block)
    if behavioral_block:
        non_colon = [strip_md(ln) for ln in split_lines(behavioral_block) if ln.strip() and ":" not in ln]
        if non_colon:
            behavioral_patterns["Summary"] = " ".join(non_colon)

    relationships = parse_colon_lines(collect_block(lines, "🌌 In Relationships", ["🪷 Spiritual Pathways", "## 🪷", "✍🏼 Journal Prompts", "## ✍🏼"]))
    spiritual = parse_colon_lines(collect_block(lines, "🪷 Spiritual Pathways", ["✍🏼 Journal Prompts", "## ✍🏼", "🛠️ Use in Practice", "## 🛠️"]))
    journal_prompts = parse_bullets(collect_block(lines, "✍🏼 Journal Prompts", ["🛠️ Use in Practice", "## 🛠️", "🌠 Fixed Stars & Notable Degrees", "## 🌠", "🕯️ Affirmation", "## 🕯️"]))
    use_in_practice = collect_block(lines, "🛠️ Use in Practice", ["🌠 Fixed Stars & Notable Degrees", "## 🌠", "🕯️ Affirmation", "## 🕯️", "🔖 Tags", "## 🔖"])

    fixed_stars_block = collect_block(lines, "🌠 Fixed Stars & Notable Degrees", ["🕯️ Affirmation", "## 🕯️", "🔖 Tags", "## 🔖"])
    fixed_stars_notable_degrees = []
    if fixed_stars_block:
        for ln in split_lines(fixed_stars_block):
            s = ln.strip()
            if not s or s.lower().startswith("degree"):
                continue
            fixed_stars_notable_degrees.append(strip_md(s))

    affirmation = collect_block(lines, "🕯️ Affirmation", ["🔖 Tags", "## 🔖"])
    tags = parse_tags_block(collect_block(lines, "🔖 Tags", []))

    return {
        "name": entry["name"],
        "subtitle": subtitle,
        "family": "sign",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
        "basic_information": basic_information,
        "iam_statement": strip_md(iam_statement) if iam_statement else None,
        "core_traits": core_traits,
        "strengths": strengths,
        "challenges": challenges,
        "behavioral_patterns": behavioral_patterns,
        "relationships": relationships,
        "spiritual_pathways": spiritual,
        "journal_prompts": journal_prompts,
        "use_in_practice": strip_md(use_in_practice) if use_in_practice else None,
        "fixed_stars_notable_degrees": fixed_stars_notable_degrees,
        "affirmation": strip_md(affirmation) if affirmation else None,
        "tags": tags,
    }


def parse_planet_note(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)
    glyph_info = resolve_glyph(entry["name"], text, lines)

    subtitle = None
    for line in lines[:10]:
        s = strip_md(line)
        if entry["name"] in s and (" – " in s or " - " in s):
            subtitle = s
            break

    description = collect_block(lines, "Description:", ["Natal Chart:", "Soul Path:", "Transit Influence:", "Progressed Expression:", "Mundane Astrology:", "Keywords / Powerwords:"])
    natal_chart = collect_block(lines, "Natal Chart:", ["Soul Path:", "Transit Influence:", "Progressed Expression:", "Mundane Astrology:", "Keywords / Powerwords:"])
    soul_path = collect_block(lines, "Soul Path:", ["Transit Influence:", "Progressed Expression:", "Mundane Astrology:", "Keywords / Powerwords:"])
    transit_influence = collect_block(lines, "Transit Influence:", ["Progressed Expression:", "Mundane Astrology:", "Keywords / Powerwords:"])
    progressed_expression = collect_block(lines, "Progressed Expression:", ["Mundane Astrology:", "Keywords / Powerwords:"])
    mundane_astrology = collect_block(lines, "Mundane Astrology:", ["Keywords / Powerwords:", "Essential Dignitaries:", "Time-Table:", "Fixed Star Associations:", "Correspondences"])

    keywords_block = collect_block(lines, "Keywords / Powerwords:", ["Essential Dignitaries:", "Time-Table:", "Fixed Star Associations:", "Correspondences"])
    keywords = []
    if keywords_block:
        keywords = [strip_md(x) for x in re.split(r",|\n", keywords_block) if strip_md(x)]

    essential_dignities = parse_colon_lines(collect_block(lines, "Essential Dignitaries:", ["Time-Table:", "Fixed Star Associations:", "Correspondences"]))
    time_table = parse_colon_lines(collect_block(lines, "Time-Table:", ["Fixed Star Associations:", "Correspondences"]))

    fixed_star_block = collect_block(lines, "Fixed Star Associations:", ["Correspondences"])
    fixed_star_associations = []
    if fixed_star_block:
        for ln in split_lines(fixed_star_block):
            s = ln.strip()
            if not s or is_heading_line(s):
                continue
            if ":" in s:
                star, meaning = s.split(":", 1)
                fixed_star_associations.append({
                    "star": strip_md(star),
                    "meaning": strip_md(meaning)
                })
            else:
                fixed_star_associations.append({"text": strip_md(s)})

    correspondences = parse_colon_lines(collect_block(lines, "Correspondences", []))

    return {
        "name": entry["name"],
        "subtitle": subtitle,
        "family": "planet",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
        "description": strip_md(description) if description else None,
        "reading_modes": {
            "natal_chart": strip_md(natal_chart) if natal_chart else None,
            "soul_path": strip_md(soul_path) if soul_path else None,
            "transit_influence": strip_md(transit_influence) if transit_influence else None,
            "progressed_expression": strip_md(progressed_expression) if progressed_expression else None,
            "mundane_astrology": strip_md(mundane_astrology) if mundane_astrology else None,
        },
        "keywords": keywords,
        "essential_dignities": essential_dignities,
        "time_table": time_table,
        "fixed_star_associations": fixed_star_associations,
        "correspondences": correspondences,
    }


def parse_unknown(entry):
    text = clean_text(entry["content"])
    lines = split_lines(text)
    glyph_info = resolve_glyph(entry["name"], text, lines)
    return {
        "name": entry["name"],
        "family": "unknown",
        "glyph": glyph_info["glyph"],
        "glyph_class": glyph_info["glyph_class"],
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
