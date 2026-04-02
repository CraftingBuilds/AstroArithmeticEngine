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
        return {
            "primary": "",
            "traits": [],
            "strengths": [],
            "challenges": [],
            "archetype": "",
            "spiritual": "",
            "keywords": [],
        }

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
    keywords = ensure_list(d.get("keywords"))

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


def summarize_fused_unit(unit):
    body_name = unit.get("body_name", "Unknown")
    sign_name = unit.get("sign_name", "Unknown")
    house_name = unit.get("house_name", "Unknown")

    body = get_priority_text(unit.get("body_interpretation"))
    sign = get_priority_text(unit.get("sign_interpretation"))
    house = get_priority_text(unit.get("house_interpretation"))

    return {
        "body_name": body_name,
        "sign_name": sign_name,
        "house_name": house_name,
        "body": body,
        "sign": sign,
        "house": house,
        "score": unit.get("significance", {}).get("score", 0),
    }


def write_fused_paragraph(unit, idx=0):
    u = summarize_fused_unit(unit)

    body_name = u["body_name"]
    sign_name = u["sign_name"]
    house_name = u["house_name"]

    b = u["body"]
    s = u["sign"]
    h = u["house"]

    body_primary = b["primary"]
    sign_primary = s["primary"]
    house_primary = h["primary"]

    traits = s["traits"] or b["traits"]
    strengths = s["strengths"] or b["strengths"]
    challenges = s["challenges"] or b["challenges"]
    archetype = s["archetype"] or b["archetype"]
    spiritual = s["spiritual"] or b["spiritual"] or h["spiritual"]
    keywords = s["keywords"] or b["keywords"]

    opener = (
        f"{body_name} in {sign_name} in the {house_name} becomes one of the clearest ways this chapter’s domain takes shape."
        if idx == 0 else
        f"{TRANSITIONS[idx % len(TRANSITIONS)]} {body_name} in {sign_name} in the {house_name} adds another important layer to the same field."
    )

    parts = [opener]

    if body_primary:
        parts.append(
            f"As a planetary or symbolic body, {body_name} carries the following core meaning: {body_primary}"
        )

    if sign_primary:
        parts.append(
            f"When this force is filtered through {sign_name}, its expression changes in tone and method. {sign_primary}"
        )

    if house_primary:
        parts.append(
            f"Because it is placed in the {house_name}, the placement is directed into a specific life arena rather than remaining abstract. {house_primary}"
        )

    if traits:
        parts.append(
            f"In lived behavior, this fusion tends to show itself through qualities such as {list_to_sentence(traits[:5])}."
        )

    if strengths:
        parts.append(
            f"At its best, the placement can express through {list_to_sentence(strengths[:4])}, giving the native a usable strength rather than a merely symbolic trait."
        )

    if challenges:
        parts.append(
            f"At the same time, its shadow may appear through {list_to_sentence(challenges[:4])}, especially when the placement is overstimulated, poorly contained, or acting defensively."
        )

    if keywords:
        parts.append(
            f"Keyword-wise, the placement resonates with {list_to_sentence(keywords[:5])}, which further clarifies its lived style."
        )

    if archetype:
        parts.append(
            f"Archetypally, this placement leans toward {archetype}, meaning it tends to organize experience around a recognizable symbolic posture."
        )

    if spiritual:
        parts.append(
            f"On the spiritual level, the placement also carries implications that can be summarized as follows: {spiritual}."
        )

    parts.append(
        f"Taken together, this means the native does not simply ‘have’ {body_name} in {sign_name} in the {house_name}; the native lives that combination as a unified psychological and developmental pattern."
    )

    return " ".join(parts)


def write_field_paragraph(domain_name, units):
    top_names = [f"{u.get('body_name')} in {u.get('sign_name')} in the {u.get('house_name')}" for u in units[:5]]

    return (
        f"The {domain_name} field of the chart should be understood as a structured domain of life rather than a vague category. "
        f"It is primarily shaped by {list_to_sentence(top_names)}, indicating that this part of the native’s system is built through recurring contact between identity, experience, and symbolic pressure. "
        f"These placements do not simply sit beside one another. They cooperate, collide, and reinforce one another, creating a field that develops through lived reality."
    )


def write_tension_paragraph(domain_name, aspects):
    tension_aspects = [a for a in aspects if a.get("aspect_name") in TENSION][:5]

    if not tension_aspects:
        return (
            f"Tension is not absent from the {domain_name} field, but it is less concentrated in one dramatic line than distributed across the domain more subtly. "
            f"That still matters, because subtle tension often works through repetition rather than spectacle."
        )

    return (
        f"What complicates the {domain_name} field most directly is the presence of tensions such as {list_to_sentence([aspect_sentence(a) for a in tension_aspects])}. "
        f"These aspects do not merely create difficulty; they create developmental friction. "
        f"They show where the native is most likely to feel pulled between incompatible demands, where overcorrection may occur, and where conscious integration is needed if the field is to mature rather than fracture."
    )


def write_harmony_paragraph(domain_name, aspects):
    harmony_aspects = [a for a in aspects if a.get("aspect_name") in HARMONY][:5]

    if not harmony_aspects:
        return (
            f"The {domain_name} field cannot rely on effortless stabilization, which means the native may have to cultivate support deliberately rather than expect it to arise automatically."
        )

    return (
        f"Yet the {domain_name} field is not governed by stress alone. Harmonizing structures such as {list_to_sentence([aspect_sentence(a) for a in harmony_aspects])} create channels of coherence within the same domain. "
        f"These aspects indicate where the native can stabilize, regulate, and draw strength, offering ways of using the chart’s energy constructively rather than being driven by it unconsciously."
    )


def write_integration_paragraph(domain_name):
    domain_map = {
        "mental": "disciplined thinking, structured reflection, speech ethics, and the conscious training of attention",
        "emotional": "containment, truthfulness, emotional metabolizing, and practices that let feeling move without taking over the whole system",
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
        f"These are not decorative add-ons to the interpretation. They are practical methods for converting symbolic pressure into deliberate change, allowing the native to participate consciously in the chart instead of being passively shaped by it."
    )


def build_section(domain_name, units, aspects):
    paragraphs = []

    if not units:
        paragraphs.append(
            f"The {domain_name} domain does not collapse into one narrow center of gravity in this chart. Instead, it is distributed across several factors and must be read in relation to the whole."
        )
        paragraphs.append(
            f"This does not weaken the domain. It means the field emerges through interaction rather than through one dominant symbolic signature."
        )
        paragraphs.append(write_integration_paragraph(domain_name))
        return paragraphs

    paragraphs.append(write_field_paragraph(domain_name, units))

    # Meat: 3–6 fused placement paragraphs, not 0–1
    placement_para_target = min(6, max(3, len(units[:6])))
    for idx, unit in enumerate(units[:placement_para_target]):
        paragraphs.append(write_fused_paragraph(unit, idx))

    paragraphs.append(write_tension_paragraph(domain_name, aspects))
    paragraphs.append(write_harmony_paragraph(domain_name, aspects))
    paragraphs.append(write_integration_paragraph(domain_name))
    paragraphs.append(write_ritual_paragraph(domain_name))

    # Clamp section length to 17 max, but never reduce below the actual meat floor
    if len(paragraphs) < 3:
        while len(paragraphs) < 3:
            paragraphs.append(write_integration_paragraph(domain_name))

    return paragraphs[:17]


def build_cross_domain_section(mental_units, emotional_units, physical_units, spiritual_units):
    mental_names = [u.get("body_name") for u in mental_units[:4]]
    emotional_names = [u.get("body_name") for u in emotional_units[:4]]
    physical_names = [u.get("body_name") for u in physical_units[:4]]
    spiritual_names = [u.get("body_name") for u in spiritual_units[:4]]

    return [
        f"No major domain in this chart operates independently. The mental field, shaped especially through {list_to_sentence(mental_names)}, influences how the native interprets experience before it is emotionally processed. The emotional field, strengthened through {list_to_sentence(emotional_names)}, then charges that interpretation with affect, memory, and reactivity.",
        f"The physical field, marked by {list_to_sentence(physical_names)}, carries the result somatically, which means mental strain and emotional pressure rarely stay abstract for long. Meanwhile, the spiritual field, configured through {list_to_sentence(spiritual_names)}, continually attempts to reorganize the other systems by forcing them toward wider meaning, karmic perspective, and existential coherence.",
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