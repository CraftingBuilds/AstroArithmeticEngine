#!/usr/bin/env python3

import json
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


def load(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp_paragraphs(dynamic_amount: int) -> int:
    if dynamic_amount < 3:
        return 3
    elif dynamic_amount > 17:
        return 17
    return dynamic_amount


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


def get_priority_text(d):
    if not isinstance(d, dict):
        return {"primary": "", "traits": [], "strengths": [], "challenges": [], "archetype": "", "spiritual": ""}

    primary = ""

    reading_modes = d.get("reading_modes", {})
    if isinstance(reading_modes, dict):
        primary = first_nonempty(
            reading_modes.get("natal_chart"),
            reading_modes.get("soul_path"),
        )

    primary = first_nonempty(
        primary,
        d.get("Natal Chart"),
        d.get("Natal Function"),
        d.get("Use in Natal Charts"),
        d.get("Use in natal charts"),
        d.get("natal_chart"),
        d.get("natal_function"),
        d.get("core_function"),
        d.get("astrological_role"),
        d.get("description"),
        d.get("house_description"),
        d.get("general_meaning"),
        d.get("iam_statement"),
        d.get("use_in_practice"),
        d.get("metaphysical_layer"),
    )

    traits = ensure_list(d.get("core_traits")) or ensure_list(d.get("thematic_keywords")) or ensure_list(d.get("keywords"))
    strengths = ensure_list(d.get("strengths"))
    challenges = ensure_list(d.get("challenges"))

    archetype = ""
    behavioral = d.get("behavioral_patterns", {})
    if isinstance(behavioral, dict):
        archetype = first_nonempty(behavioral.get("Archetype"), behavioral.get("archetype"))

    spiritual = ""
    spiritual_pathways = d.get("spiritual_pathways", {})
    if isinstance(spiritual_pathways, dict):
        bits = []
        for k, v in spiritual_pathways.items():
            if v:
                bits.append(f"{k}: {v}")
        spiritual = "; ".join(bits)

    metaphysical = d.get("metaphysical_spiritual_layer", {})
    if isinstance(metaphysical, dict):
        bits = []
        for k, v in metaphysical.items():
            if v:
                bits.append(f"{k}: {v}")
        if bits and not spiritual:
            spiritual = "; ".join(bits)

    return {
        "primary": primary,
        "traits": traits,
        "strengths": strengths,
        "challenges": challenges,
        "archetype": archetype,
        "spiritual": spiritual,
    }


def fuse_unit(unit):
    body_name = unit.get("body_name", "Unknown")
    sign_name = unit.get("sign_name", "Unknown")
    house_name = unit.get("house_name", "Unknown")

    body = get_priority_text(unit.get("body_interpretation"))
    sign = get_priority_text(unit.get("sign_interpretation"))
    house = get_priority_text(unit.get("house_interpretation"))

    body_primary = body["primary"]
    sign_primary = sign["primary"]
    house_primary = house["primary"]

    traits = sign["traits"] or body["traits"]
    strengths = sign["strengths"] or body["strengths"]
    challenges = sign["challenges"] or body["challenges"]
    archetype = sign["archetype"] or body["archetype"]
    spiritual = sign["spiritual"] or body["spiritual"] or house["spiritual"]

    sentences = []

    sentences.append(
        f"{body_name} in {sign_name} in the {house_name} should be read as a fused natal pattern rather than a simple placement label."
    )

    if body_primary:
        sentences.append(body_primary)

    if sign_primary:
        sentences.append(
            f"When filtered through {sign_name}, this energy takes on a distinct tonal quality. {sign_primary}"
        )

    if house_primary:
        sentences.append(
            f"Placed within the {house_name}, the placement is further directed into a specific field of life experience. {house_primary}"
        )

    if traits:
        sentences.append(
            f"This gives the placement a recognizable behavioral texture shaped by {list_to_sentence(traits[:5])}."
        )

    if strengths:
        sentences.append(
            f"At its strongest, it can express through {list_to_sentence(strengths[:4])}."
        )

    if challenges:
        sentences.append(
            f"At the same time, its shadow may emerge through {list_to_sentence(challenges[:4])}, especially when the placement is stressed or poorly integrated."
        )

    if archetype:
        sentences.append(
            f"Archetypally, this placement leans toward {archetype}."
        )

    if spiritual:
        sentences.append(
            f"At the spiritual level, it also carries implications that can be summarized as follows: {spiritual}."
        )

    sentences.append(
        f"Taken together, this means the native does not merely possess {body_name} in {sign_name} in the {house_name}; the native lives that fusion as a coherent behavioral, psychological, and developmental pattern."
    )

    return " ".join(sentences)


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


def build_opening(chart, placements, aspects):
    metadata = chart.get("metadata", {})
    date_time = metadata.get("date_time", {})
    geo = metadata.get("geo_location", {})

    date_val = first_nonempty(date_time.get("Date"), date_time.get("date"))
    location_val = first_nonempty(geo.get("Location"), geo.get("location"))

    top_placements = [f"{p.get('body_name')} in {p.get('sign_name')} ({p.get('house_name')})" for p in placements[:8]]
    top_aspects = [aspect_sentence(a) for a in aspects[:6]]

    p1 = (
        f"The native’s chart, when approached as a living whole rather than a collection of disconnected signatures, reveals a coherent psycho-spiritual architecture. "
        f"Generated from chart data for {date_val or 'an unknown date'} in {location_val or 'an unknown location'}, this chapter does not simply restate isolated placements; it resolves them into a unified pattern of thought, feeling, embodiment, relational tension, karmic instruction, and spiritual direction."
    )

    p2 = (
        f"At the surface level, the chart is immediately distinguished by the prominence of {list_to_sentence(top_placements)}. "
        f"These placements do not operate independently of one another. They create a central field of identity formation through which the native’s experience of self, environment, communication, vulnerability, and purpose becomes organized."
    )

    p3 = (
        f"What gives this chart its movement, however, is not placement alone but the dynamic pressure created by aspects such as {list_to_sentence(top_aspects)}. "
        f"These dynamics ensure that the chart is never static. It is always in process, always generating friction, adaptation, and the possibility of integration."
    )

    return [p1, p2, p3]


def build_tension_paragraph(aspects, domain_name):
    tension_aspects = [a for a in aspects if a.get("aspect_name") in TENSION][:5]
    harmony_aspects = [a for a in aspects if a.get("aspect_name") in HARMONY][:5]

    bits = []

    if tension_aspects:
        bits.append(
            f"Within the {domain_name} field, the principal tensions emerge through {list_to_sentence([aspect_sentence(a) for a in tension_aspects])}."
        )

    if harmony_aspects:
        bits.append(
            f"Yet this field is not held together by conflict alone. It is also stabilized by harmonizing dynamics such as {list_to_sentence([aspect_sentence(a) for a in harmony_aspects])}."
        )

    bits.append(
        f"The result is a domain that develops through tension rather than being destroyed by it. Conflict here functions as pressure for refinement, while harmony provides channels through which the native may organize and direct the same energy more consciously."
    )

    return " ".join(bits)


def build_resolution_paragraph(domain_name):
    resolutions = {
        "mental": "disciplined clarity, structured reflection, and deliberate use of language",
        "emotional": "containment, emotional honesty, and practices that metabolize feeling without collapse",
        "physical": "embodiment, movement, and the conscious regulation of tension in the body",
        "spiritual": "lived alignment, ritualized intention, and devotion that remains grounded in experience",
        "relational": "clear agreements, truthful exchange, and boundaries that do not sever intimacy",
        "karmic": "recognition of repeated patterns and disciplined participation in the chart’s evolutionary demand",
    }

    target = resolutions.get(domain_name, "disciplined integration across the native’s lived experience")

    return (
        f"For this reason, the {domain_name} domain should not be treated as descriptive background. "
        f"It is an active developmental field requiring conscious engagement. "
        f"The native moves toward integration here through {target}, allowing the symbolic pressure of the chart to become usable rather than merely overwhelming."
    )


def build_section(title, units, aspects, domain_name):
    paragraphs = []

    if not units:
        paragraphs.append(
            f"The {domain_name} domain does not collapse into one narrow center of gravity within this chart. "
            f"Instead, it is distributed across multiple placements and must be read contextually, in relation to the chart as a whole."
        )
        paragraphs.append(
            f"This does not weaken the domain. It suggests that the native experiences this field through layered interaction rather than a singular defining signature."
        )
        paragraphs.append(build_resolution_paragraph(domain_name))
        return paragraphs

    unit_texts = [fuse_unit(u) for u in units[:6]]

    # Paragraph 1: establish the field
    leading_names = [f"{u.get('body_name')} in {u.get('sign_name')} in the {u.get('house_name')}" for u in units[:4]]
    paragraphs.append(
        f"The {domain_name} domain of the chart is not passive or incidental. It is actively shaped by {list_to_sentence(leading_names)}, creating a field that develops through lived contact rather than abstract theory alone. "
        f"What appears at first to be a set of separate placements quickly reveals itself as a continuous pattern of cause, response, and adaptation."
    )

    # Placement paragraphs, smoothly threaded
    transition_index = 0
    for i, t in enumerate(unit_texts):
        if i == 0:
            paragraphs.append(t)
        else:
            transition = TRANSITIONS[transition_index % len(TRANSITIONS)]
            transition_index += 1
            paragraphs.append(f"{transition} {t}")

    # Tension/Harmony paragraph
    paragraphs.append(build_tension_paragraph(aspects, domain_name))

    # Resolution paragraph
    paragraphs.append(build_resolution_paragraph(domain_name))

    dynamic_amount = len(unit_texts) + max(1, len(aspects[:6]) // 2)
    paragraph_count = clamp_paragraphs(dynamic_amount)

    return paragraphs[:paragraph_count]


def build_cross_domain_section(mental_units, emotional_units, physical_units, spiritual_units):
    mental_names = [u.get("body_name") for u in mental_units[:4]]
    emotional_names = [u.get("body_name") for u in emotional_units[:4]]
    physical_names = [u.get("body_name") for u in physical_units[:4]]
    spiritual_names = [u.get("body_name") for u in spiritual_units[:4]]

    p1 = (
        f"No major domain in this chart operates in isolation. The mental field, shaped heavily through {list_to_sentence(mental_names)}, influences how the native interprets experience before it is ever emotionally processed. "
        f"The emotional field, in turn, redirects the force of that interpretation into felt intensity, while the physical field registers the result somatically through the body’s changing state."
    )

    p2 = (
        f"This means the native’s psychological life is recursive. Emotional strain can distort thought; overactive thought can intensify bodily tension; bodily tension can limit spiritual receptivity; and spiritual uncertainty can send instability back into both mind and feeling. "
        f"Meanwhile, the spiritual domain, especially where {list_to_sentence(spiritual_names)} are active, continually attempts to reorganize the other three by forcing them toward larger meaning."
    )

    p3 = (
        f"The task of integration is therefore systemic. The native cannot heal purely through cognition, nor purely through feeling, nor purely through ritual. Growth requires recognizing the way these domains interact and building practices that allow one system to stabilize another rather than amplify its imbalance."
    )

    return [p1, p2, p3]


def build_final_resolution():
    return [
        "In conclusion, the native’s chart should be understood as a living architecture rather than a symbolic inventory. Its most important signatures do not simply describe temperament; they describe the way identity, emotion, embodiment, conflict, and meaning are forced into dialogue with one another.",
        "The chart’s complexity is not evidence of confusion. It is evidence of depth. What the native is being asked to do is not to simplify the self into a single trait, but to bring multiple active systems into lawful relationship.",
        "For the practitioner, this means that interpretation must move beyond naming placements and into teaching the native how those placements behave, why they behave that way, and what kinds of discipline, awareness, and ritual support their full integration."
    ]


def main():
    chart_id = input("Enter Chart ID: ").strip()
    folder = BASE / chart_id

    chart = load(folder / "normalized_chart.json")
    resolved = load(folder / "resolved_interpretations.json")

    placements = ensure_list(resolved.get("resolved_placements"))
    aspects = ensure_list(resolved.get("resolved_aspects"))

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
    mental = build_section("Mental Profile", mental_units, mental_aspects, "mental")
    emotional = build_section("Emotional Profile", emotional_units, emotional_aspects, "emotional")
    physical = build_section("Physical Profile", physical_units, physical_aspects, "physical")
    spiritual = build_section("Spiritual Profile", spiritual_units, spiritual_aspects, "spiritual")
    relational = build_section("Relational Integration", relational_units, relational_aspects, "relational")
    karmic = build_section("Karmic Axis and Development", karmic_units, karmic_aspects, "karmic")
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


if __name__ == "__main__":
    main()