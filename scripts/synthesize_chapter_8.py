#!/usr/bin/env python3

import json
import re
from pathlib import Path

BASE = Path("/mnt/storage/AstroArithmeticEngine/secure_charts")

MENTAL = {"Mercury", "Moon", "Saturn", "Jupiter", "Uranus", "North Node", "South Node", "Sun"}
EMOTIONAL = {"Moon", "Venus", "Chiron", "Neptune", "Lilith", "Black Moon", "Juno"}
PHYSICAL = {"Ascendant", "Mars", "Saturn", "Sun", "Midheaven", "Imum Coeli", "Descendant"}
SPIRITUAL = {"Sun", "Jupiter", "Neptune", "Pluto", "North Node", "South Node", "Chiron", "Black Moon"}
RELATIONAL = {"Venus", "Mars", "Descendant", "Juno", "Moon", "Lilith", "Black Moon", "Pluto"}
KARMIC = {"North Node", "South Node", "Saturn", "Chiron", "Pluto", "Black Moon", "Sun", "Moon"}

TENSION = {"Square", "Opposition", "Quincunx", "Inconjunction", "Sesquiquadrate", "Semisquare"}
HARMONY = {"Trine", "Sextile", "Conjunction"}

TRANSITIONS = [
    "At the same time,",
    "What deepens this pattern is that",
    "This becomes even more pronounced when",
    "Seen from another angle,",
    "However,",
    "At a deeper level,",
    "What complicates the matter is that",
    "As a result,",
]

LAYER_PHRASES = [
    "modifies the expression further",
    "introduces a new behavioral dynamic",
    "shifts the emphasis of the field",
    "complicates the pattern in a meaningful way",
    "refines how the system operates",
]

# Used to prevent full encyclopedic repeats across domains
SEEN_PLACEMENTS = set()


def load(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_list(x):
    return x if isinstance(x, list) else []


def first_nonempty(*values):
    for v in values:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return ""


def list_to_sentence(items):
    items = [str(i).strip() for i in items if str(i).strip()]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def paragraph_count_from_complexity(dynamic_amount: int) -> int:
    if dynamic_amount < 3:
        return 3
    elif dynamic_amount > 17:
        return 17
    return dynamic_amount


def scrub_text(text: str) -> str:
    if not isinstance(text, str):
        return ""

    text = text.strip()
    if not text:
        return ""

    # Remove boilerplate / non-synthesis content
    kill_phrases = [
        "This entry is part of Astrology Arith(m)etic",
        "eventually used to train a personal AI assistant",
        "- Transit Influence:",
        "- Progressed Expression:",
        "- Mundane Astrology:",
        "- Soul Path:",
    ]
    for phrase in kill_phrases:
        text = text.replace(phrase, " ")

    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()

    return text


def split_sentences(text: str):
    text = scrub_text(text)
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [p.strip() for p in parts if p.strip()]


def compress_text(text: str, max_sentences: int = 3, max_chars: int = 420) -> str:
    """
    Keep only the most relevant early text. This avoids encyclopedia dumps.
    """
    text = scrub_text(text)
    if not text:
        return ""

    sentences = split_sentences(text)
    if not sentences:
        return ""

    kept = []
    total = 0
    for s in sentences:
        if len(kept) >= max_sentences:
            break
        if total + len(s) > max_chars and kept:
            break
        kept.append(s)
        total += len(s)

    out = " ".join(kept).strip()
    return out


def get_nested(d, *keys):
    cur = d
    for key in keys:
        if not isinstance(cur, dict):
            return ""
        cur = cur.get(key)
        if cur is None:
            return ""
    return cur if isinstance(cur, str) else ""


def collect_priority_text(d):
    """
    This is the core fix:
    prioritize natal-target fields, especially 'Use in Natal Charts'.
    """
    if not isinstance(d, dict):
        return {
            "primary": "",
            "traits": [],
            "strengths": [],
            "challenges": [],
            "archetype": "",
            "spiritual": "",
            "keywords": [],
        }

    candidates = [
        get_nested(d, "Use in Natal Charts"),
        get_nested(d, "Use in natal charts"),
        get_nested(d, "Natal Chart"),
        get_nested(d, "Natal Function"),
        get_nested(d, "reading_modes", "natal_chart"),
        get_nested(d, "natal_chart"),
        get_nested(d, "natal_function"),
        get_nested(d, "core_function"),
        get_nested(d, "astrological_role"),
        get_nested(d, "description"),
        get_nested(d, "house_description"),
        get_nested(d, "general_meaning"),
        get_nested(d, "iam_statement"),
        get_nested(d, "use_in_practice"),
        get_nested(d, "metaphysical_layer"),
    ]

    primary = ""
    for c in candidates:
        c = compress_text(c, max_sentences=3, max_chars=420)
        if c:
            primary = c
            break

    traits = ensure_list(d.get("core_traits")) or ensure_list(d.get("thematic_keywords")) or ensure_list(d.get("keywords"))
    strengths = ensure_list(d.get("strengths"))
    challenges = ensure_list(d.get("challenges"))
    keywords = ensure_list(d.get("keywords"))

    # Trim noisy lists
    traits = [str(x).strip() for x in traits[:5] if str(x).strip()]
    strengths = [str(x).strip() for x in strengths[:4] if str(x).strip()]
    challenges = [str(x).strip() for x in challenges[:4] if str(x).strip()]
    keywords = [str(x).strip() for x in keywords[:3] if str(x).strip()]

    archetype = ""
    behavioral = d.get("behavioral_patterns", {})
    if isinstance(behavioral, dict):
        archetype = first_nonempty(
            behavioral.get("Archetype"),
            behavioral.get("archetype")
        ).strip()

    spiritual = ""
    for block in [d.get("spiritual_pathways"), d.get("metaphysical_spiritual_layer")]:
        if isinstance(block, dict):
            bits = []
            for k, v in block.items():
                if v:
                    bits.append(f"{k}: {v}")
            if bits:
                spiritual = "; ".join(bits)
                spiritual = compress_text(spiritual, max_sentences=2, max_chars=220)
                break

    return {
        "primary": primary,
        "traits": traits,
        "strengths": strengths,
        "challenges": challenges,
        "archetype": archetype,
        "spiritual": spiritual,
        "keywords": keywords,
    }


def aspect_sentence(a):
    return f"{a.get('body_a')} {a.get('aspect_name')} {a.get('body_b')} ({a.get('orb')})"


def filter_domain(units, allowed):
    filtered = [u for u in units if u.get("body_name") in allowed and u.get("resolved")]
    filtered.sort(key=lambda x: x.get("significance", {}).get("score", 0), reverse=True)
    return filtered


def domain_aspects(aspects, allowed):
    chosen = []
    for a in aspects:
        if not a.get("resolved"):
            continue
        if a.get("body_a") in allowed or a.get("body_b") in allowed:
            chosen.append(a)
    chosen.sort(key=lambda x: x.get("significance", {}).get("score", 0), reverse=True)
    return chosen


def summarize_unit(unit):
    body_name = unit.get("body_name", "Unknown")
    sign_name = unit.get("sign_name", "Unknown")
    house_name = unit.get("house_name", "Unknown")

    body = collect_priority_text(unit.get("body_interpretation"))
    sign = collect_priority_text(unit.get("sign_interpretation"))
    house = collect_priority_text(unit.get("house_interpretation"))

    return {
        "body_name": body_name,
        "sign_name": sign_name,
        "house_name": house_name,
        "body": body,
        "sign": sign,
        "house": house,
        "score": unit.get("significance", {}).get("score", 0),
    }


def build_combined_meaning(u):
    body_name = u["body_name"]
    sign_name = u["sign_name"]
    house_name = u["house_name"]

    body_primary = u["body"]["primary"]
    sign_primary = u["sign"]["primary"]
    house_primary = u["house"]["primary"]

    traits = u["sign"]["traits"] or u["body"]["traits"]
    strengths = u["sign"]["strengths"] or u["body"]["strengths"]
    challenges = u["sign"]["challenges"] or u["body"]["challenges"]
    archetype = u["sign"]["archetype"] or u["body"]["archetype"]
    spiritual = u["sign"]["spiritual"] or u["body"]["spiritual"] or u["house"]["spiritual"]
    keywords = u["sign"]["keywords"] or u["body"]["keywords"]

    chunks = []

    chunks.append(
        f"{body_name} in {sign_name} in the {house_name} must be read as a single fused natal pattern rather than as three unrelated symbolic ingredients."
    )

    if body_primary:
        chunks.append(
            f"At the level of the body itself, {body_name} points toward {body_primary}"
        )

    if sign_primary:
        chunks.append(
            f"When that force is filtered through {sign_name}, its tone changes accordingly: {sign_primary}"
        )

    if house_primary:
        chunks.append(
            f"Placed in the {house_name}, the pattern becomes anchored in a specific field of lived experience: {house_primary}"
        )

    chunks.append(
        f"Taken together, this means the native experiences {body_name} not abstractly, but through the style, rhythm, and demand of {sign_name} operating inside the life terrain of the {house_name}."
    )

    if traits:
        chunks.append(
            f"In practical behavior, this often shows itself through qualities such as {list_to_sentence(traits)}."
        )

    if strengths:
        chunks.append(
            f"At its best, the placement can mature into {list_to_sentence(strengths)}."
        )

    if challenges:
        chunks.append(
            f"Its shadow, however, may emerge through {list_to_sentence(challenges)}, especially when the placement is overstimulated, defensive, or insufficiently integrated."
        )

    if keywords:
        chunks.append(
            f"Keywords such as {list_to_sentence(keywords)} further clarify the native’s lived experience of this pattern."
        )

    if archetype:
        chunks.append(
            f"Archetypally, the placement leans toward {archetype}, which gives the pattern a recognizable symbolic posture."
        )

    if spiritual:
        chunks.append(
            f"At the spiritual layer, it also carries implications summarized as follows: {spiritual}."
        )

    return " ".join(chunks)


def write_fused_paragraph(unit, idx, domain_name):
    u = summarize_unit(unit)

    placement_key = f"{u['body_name']}-{u['sign_name']}-{u['house_name']}"

    if placement_key in SEEN_PLACEMENTS:
        phrase = LAYER_PHRASES[idx % len(LAYER_PHRASES)]
        return (
            f"{TRANSITIONS[idx % len(TRANSITIONS)]} {u['body_name']} in {u['sign_name']} in the {u['house_name']} {phrase}. "
            f"Although this placement has already been established elsewhere in the chapter, it continues to shape the {domain_name} field specifically by redirecting the same pattern into this domain’s distinctive concerns."
        )

    SEEN_PLACEMENTS.add(placement_key)

    opener = (
        f"{u['body_name']} in {u['sign_name']} in the {u['house_name']} becomes one of the clearest expressions of the {domain_name} field."
        if idx == 0 else
        f"{TRANSITIONS[idx % len(TRANSITIONS)]} {u['body_name']} in {u['sign_name']} in the {u['house_name']} {LAYER_PHRASES[idx % len(LAYER_PHRASES)]}."
    )

    combined = build_combined_meaning(u)

    closing = (
        f"This placement does not operate in isolation. It actively interacts with other dominant factors in the chart, shaping and being shaped by the broader structure of the {domain_name} field."
    )

    return " ".join([opener, combined, closing])


def write_field_paragraph(domain_name, units):
    top_names = [f"{u.get('body_name')} in {u.get('sign_name')} in the {u.get('house_name')}" for u in units[:5]]

    return (
        f"The {domain_name} field of the chart should be understood as an active system rather than a loose theme. "
        f"It is primarily shaped by {list_to_sentence(top_names)}, which means this domain develops through repeated contact between identity, circumstance, symbolic pressure, and adaptation. "
        f"These placements do not merely coexist. They cooperate, intensify one another, and sometimes collide, creating a domain that must be interpreted as a living process."
    )


def write_tension_paragraph(domain_name, aspects):
    tension_aspects = [a for a in aspects if a.get("aspect_name") in TENSION][:5]

    if not tension_aspects:
        return (
            f"Tension is not absent from the {domain_name} field, but it is less concentrated in one dramatic line than distributed more subtly across the domain. "
            f"That still matters, because subtle pressure often works through repetition rather than spectacle."
        )

    return (
        f"What most complicates the {domain_name} field is the presence of tensions such as {list_to_sentence([aspect_sentence(a) for a in tension_aspects])}. "
        f"These do not merely signify difficulty. They show where the native is pulled between competing demands, where overcorrection may occur, and where conscious integration is required if the domain is to mature rather than fracture."
    )


def write_harmony_paragraph(domain_name, aspects):
    harmony_aspects = [a for a in aspects if a.get("aspect_name") in HARMONY][:5]

    if not harmony_aspects:
        return (
            f"The {domain_name} field cannot rely on effortless stabilization, which means the native may have to cultivate support deliberately rather than expect it to arise automatically."
        )

    return (
        f"At the same time, the {domain_name} field is not governed by stress alone. Harmonizing structures such as {list_to_sentence([aspect_sentence(a) for a in harmony_aspects])} create channels of coherence within the same domain. "
        f"These aspects show where the native can regulate, stabilize, and draw strength, making it possible to use the chart’s energy constructively rather than being driven by it unconsciously."
    )


def write_integration_paragraph(domain_name):
    domain_map = {
        "mental": "disciplined thinking, structured reflection, speech ethics, and the conscious training of attention",
        "emotional": "containment, truthfulness, emotional metabolizing, and practices that let feeling move without flooding the whole system",
        "physical": "embodiment, movement, posture, regulated force, and somatic awareness of tension before it becomes crisis",
        "spiritual": "lived alignment, devotional seriousness, symbolic literacy, and the refusal to separate meaning from practice",
        "relational": "clear agreements, reciprocal honesty, boundary integrity, and the refusal to mistake intensity for depth",
        "karmic": "recognition of repeated patterning, responsibility for inherited momentum, and deliberate participation in the chart’s evolutionary demand",
    }

    target = domain_map.get(domain_name, "conscious integration")
    return (
        f"For this reason, the {domain_name} domain must be treated as an active site of work rather than passive description. "
        f"The native moves toward maturity here through {target}. "
        f"The goal is not to remove complexity from the field, but to make that complexity usable."
    )


def write_ritual_paragraph(domain_name):
    ritual_map = {
        "mental": "structured journaling, vow-based speech, fixed-hour study, and breath-centering before important communication",
        "emotional": "lunar meditation, water rites, grief release, compassionate boundary work, and intentional feeling practices",
        "physical": "breathwork, movement ritual, martial or strength practices, mirror work, and daily grounding in bodily awareness",
        "spiritual": "ancestral invocation, devotional silence, vow review, altar work, and disciplined symbolic contemplation",
        "relational": "contract review, partnership truth-telling, erotic boundary purification, and ritual clarity around expectations and exchange",
        "karmic": "soul-contract rewriting, seasonal release rites, narrative consecration, and repeated review of what belongs to habit versus destiny",
    }

    prescription = ritual_map.get(domain_name, "intentional ritual practice")
    return (
        f"Ceremonially, this domain responds well to {prescription}. "
        f"These are not decorative additions to the reading. They are practical methods for converting symbolic pressure into deliberate participation, allowing the native to work with the chart rather than be passively shaped by it."
    )


def build_section(domain_name, units, aspects):
    paragraphs = []

    if not units:
        paragraphs.append(
            f"The {domain_name} domain does not collapse into one narrow center of gravity within this chart. Instead, it is distributed across several factors and must be read in relation to the whole."
        )
        paragraphs.append(
            f"This does not weaken the domain. It indicates that the field emerges through layered interaction rather than one dominant symbolic signature."
        )
        paragraphs.append(write_integration_paragraph(domain_name))
        return paragraphs

    paragraphs.append(write_field_paragraph(domain_name, units))

    # Real meat: 3 to 6 fused placement paragraphs minimum
    placement_para_target = min(6, max(3, len(units[:6])))
    for idx, unit in enumerate(units[:placement_para_target]):
        paragraphs.append(write_fused_paragraph(unit, idx, domain_name))

    paragraphs.append(write_tension_paragraph(domain_name, aspects))
    paragraphs.append(write_harmony_paragraph(domain_name, aspects))
    paragraphs.append(write_integration_paragraph(domain_name))
    paragraphs.append(write_ritual_paragraph(domain_name))

    # Dynamic count is a floor, not a target
    dynamic_amount = 1 + placement_para_target + 4
    target = paragraph_count_from_complexity(dynamic_amount)

    while len(paragraphs) < target:
        paragraphs.append(write_integration_paragraph(domain_name))

    return paragraphs[:17]


def build_cross_domain_section(mental_units, emotional_units, physical_units, spiritual_units):
    mental_names = [u.get("body_name") for u in mental_units[:4]]
    emotional_names = [u.get("body_name") for u in emotional_units[:4]]
    physical_names = [u.get("body_name") for u in physical_units[:4]]
    spiritual_names = [u.get("body_name") for u in spiritual_units[:4]]

    return [
        f"No major domain in this chart operates independently. The mental field, shaped especially through {list_to_sentence(mental_names)}, influences how the native interprets experience before it is emotionally processed. The emotional field, strengthened through {list_to_sentence(emotional_names)}, then charges that interpretation with affect, memory, and reactivity.",
        f"The physical field, marked by {list_to_sentence(physical_names)}, carries the result somatically, which means mental strain and emotional pressure rarely remain abstract for long. Meanwhile, the spiritual field, configured through {list_to_sentence(spiritual_names)}, continually attempts to reorganize the other systems by forcing them toward wider meaning, karmic perspective, and existential coherence.",
        "This creates a recursive system. Thought affects feeling, feeling affects embodiment, embodiment affects perception, and perception affects spiritual receptivity. Growth therefore cannot come from isolating one system and ignoring the rest. The native’s path depends on coordinated integration.",
    ]


def build_opening(chart, placements, aspects):
    metadata = chart.get("metadata", {})
    date_time = metadata.get("date_time", {})
    geo = metadata.get("geo_location", {})

    date_val = first_nonempty(date_time.get("Date"), date_time.get("date"))
    location_val = first_nonempty(geo.get("Location"), geo.get("location"))

    top_placements = [f"{p.get('body_name')} in {p.get('sign_name')} ({p.get('house_name')})" for p in placements[:8]]
    top_aspects = [aspect_sentence(a) for a in aspects[:6]]

    return [
        f"The native’s chart, when approached as a living whole rather than a collection of disconnected symbols, reveals a coherent psycho-spiritual architecture. Generated from chart data for {date_val or 'an unknown date'} in {location_val or 'an unknown location'}, this chapter aims not merely to name placements, but to explain how they function together.",
        f"At the structural level, the chart is immediately shaped by the prominence of {list_to_sentence(top_placements)}. These placements create the central field through which identity, adaptation, communication, feeling, embodiment, and meaning are experienced and tested.",
        f"What gives the chart movement, however, is not placement alone but the dynamic force of aspects such as {list_to_sentence(top_aspects)}. These relationships ensure that the chart remains active rather than static, producing friction, support, contradiction, and the possibility of integration.",
    ]


def build_final_resolution():
    return [
        "In conclusion, the native’s chart should be understood as a living architecture rather than a symbolic inventory. Its major signatures do not simply describe temperament; they describe how identity, thought, feeling, embodiment, relationship, karma, and spiritual direction are forced into dialogue with one another.",
        "The chart’s complexity is not evidence of disorder. It is evidence of depth. What the native is being asked to do is not to simplify the self into one trait or one story, but to bring multiple active systems into lawful relationship.",
        "For the practitioner, this means that interpretation must move beyond naming placements and into teaching the native how those placements behave, why they behave that way, how they interact, and what forms of discipline, awareness, and ritual allow them to become integrated rather than merely overwhelming.",
    ]


def main():
    chart_id = input("Enter Chart ID: ").strip()
    folder = BASE / chart_id

    chart = load(folder / "normalized_chart.json")
    resolved = load(folder / "resolved_interpretations.json")

    placements = ensure_list(resolved.get("resolved_placements"))
    aspects = ensure_list(resolved.get("resolved_aspects"))

    placements.sort(key=lambda x: x.get("significance", {}).get("score", 0), reverse=True)
    aspects.sort(key=lambda x: x.get("significance", {}).get("score", 0), reverse=True)

    mental_units = filter_domain(placements, MENTAL)
    emotional_units = filter_domain(placements, EMOTIONAL)
    physical_units = filter_domain(placements, PHYSICAL)
    spiritual_units = filter_domain(placements, SPIRITUAL)
    relational_units = filter_domain(placements, RELATIONAL)
    karmic_units = filter_domain(placements, KARMIC)

    mental_aspects = domain_aspects(aspects, MENTAL)
    emotional_aspects = domain_aspects(aspects, EMOTIONAL)
    physical_aspects = domain_aspects(aspects, PHYSICAL)
    spiritual_aspects = domain_aspects(aspects, SPIRITUAL)
    relational_aspects = domain_aspects(aspects, RELATIONAL)
    karmic_aspects = domain_aspects(aspects, KARMIC)

    opening = build_opening(chart, placements, aspects)
    mental = build_section("mental", mental_units, mental_aspects)
    emotional = build_section("emotional", emotional_units, emotional_aspects)
    physical = build_section("physical", physical_units, physical_aspects)
    spiritual = build_section("spiritual", spiritual_units, spiritual_aspects)
    relational = build_section("relational", relational_units, relational_aspects)
    karmic = build_section("karmic", karmic_units, karmic_aspects)
    cross_domain = build_cross_domain_section(mental_units, emotional_units, physical_units, spiritual_units)
    final_resolution = build_final_resolution()

    out = folder / "chapter8_synthesized.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write("# Chapter 8 – Integrated Synthesis\n\n")

        for p in opening:
            f.write(p + "\n\n")

        f.write("## Mental Profile\n\n")
        for p in mental:
            f.write(p + "\n\n")

        f.write("## Emotional Profile\n\n")
        for p in emotional:
            f.write(p + "\n\n")

        f.write("## Physical Profile\n\n")
        for p in physical:
            f.write(p + "\n\n")

        f.write("## Spiritual Profile\n\n")
        for p in spiritual:
            f.write(p + "\n\n")

        f.write("## Relational Integration\n\n")
        for p in relational:
            f.write(p + "\n\n")

        f.write("## Karmic Axis and Development\n\n")
        for p in karmic:
            f.write(p + "\n\n")

        f.write("## Cross-Domain Integration\n\n")
        for p in cross_domain:
            f.write(p + "\n\n")

        f.write("## Final Resolution\n\n")
        for p in final_resolution:
            f.write(p + "\n\n")

    print(f"\nDone. Wrote: {out}")
    print(f"Mental paragraphs: {len(mental)}")
    print(f"Emotional paragraphs: {len(emotional)}")
    print(f"Physical paragraphs: {len(physical)}")
    print(f"Spiritual paragraphs: {len(spiritual)}")
    print(f"Relational paragraphs: {len(relational)}")
    print(f"Karmic paragraphs: {len(karmic)}")


if __name__ == "__main__":
    main()