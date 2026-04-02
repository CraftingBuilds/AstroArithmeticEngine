#!/usr/bin/env python3

import json
from pathlib import Path

BASE = Path("/mnt/storage/AstroArithmeticEngine/secure_charts")

MENTAL = {"Mercury", "Moon", "Saturn", "Jupiter", "Uranus", "North Node", "South Node"}
EMOTIONAL = {"Moon", "Venus", "Chiron", "Neptune", "Lilith", "Black Moon"}
PHYSICAL = {"Ascendant", "Mars", "Saturn", "Sun", "Midheaven"}
SPIRITUAL = {"Sun", "Jupiter", "Neptune", "Pluto", "North Node", "South Node", "Chiron"}

TENSION = {"Square", "Opposition", "Quincunx", "Inconjunction", "Sesquiquadrate", "Semisquare"}
HARMONY = {"Trine", "Sextile", "Conjunction"}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def clamp(n):
    if n < 3:
        return 3
    elif n > 17:
        return 17
    return n


def get_text(d):
    if not isinstance(d, dict):
        return ""
    for k in [
        "Natal Chart",
        "Use in Natal Charts",
        "description",
        "core_function",
        "astrological_role"
    ]:
        if k in d and d[k]:
            return d[k]
    return ""


def fuse_unit(u):
    body = u.get("body_name")
    sign = u.get("sign_name")
    house = u.get("house_name")

    b = get_text(u.get("body_interpretation"))
    s = get_text(u.get("sign_interpretation"))
    h = get_text(u.get("house_interpretation"))

    sentence = f"{body} in {sign} in the {house} operates as a unified pattern."

    if b:
        sentence += f" {b}"
    if s:
        sentence += f" {s}"
    if h:
        sentence += f" {h}"

    return sentence


def filter_domain(units, allowed):
    return [u for u in units if u.get("body_name") in allowed]


def aspect_text(a):
    return f"{a.get('body_a')} {a.get('aspect_name')} {a.get('body_b')}"


def build_section(name, units, aspects):
    text = []

    units = sorted(units, key=lambda x: x.get("significance", {}).get("score", 0), reverse=True)

    fused = [fuse_unit(u) for u in units[:6]]

    tension = [a for a in aspects if a.get("aspect_name") in TENSION][:4]
    harmony = [a for a in aspects if a.get("aspect_name") in HARMONY][:4]

    dynamic = len(fused) + len(tension)
    paragraphs = clamp(dynamic)

    # paragraph 1 -- field
    text.append(
        f"The {name} domain of the chart emerges as a structured field of interaction rather than a fixed trait. "
        f"It is shaped most strongly by {' , '.join([u.get('body_name') for u in units[:5]])}, "
        f"indicating that this dimension of life is actively constructed through experience rather than passively inherited."
    )

    # placement-driven paragraphs
    for i in range(min(len(fused), paragraphs - 2)):
        transition = "This becomes more apparent when" if i == 0 else "Building on this,"
        text.append(f"{transition} {fused[i]}")

    # tension paragraph
    if tension:
        text.append(
            f"What complicates this field further is the presence of tensions such as "
            f"{', '.join([aspect_text(a) for a in tension])}, "
            f"which introduce friction that forces development rather than allowing stagnation."
        )

    # harmony paragraph
    if harmony:
        text.append(
            f"At the same time, supportive dynamics such as "
            f"{', '.join([aspect_text(a) for a in harmony])} "
            f"offer stabilization, suggesting that the native is not confined to conflict but is capable of integration."
        )

    # closing paragraph
    text.append(
        f"Ultimately, the {name} domain must be approached as something to be consciously worked with. "
        f"It is not static, and its expression depends on the native’s willingness to engage, refine, and direct its energy."
    )

    return text[:paragraphs]


def main():
    chart_id = input("Enter Chart ID: ").strip()
    folder = BASE / chart_id

    resolved = load(folder / "resolved_interpretations.json")

    placements = resolved.get("resolved_placements", [])
    aspects = resolved.get("resolved_aspects", [])

    mental = build_section("mental", filter_domain(placements, MENTAL), aspects)
    emotional = build_section("emotional", filter_domain(placements, EMOTIONAL), aspects)
    physical = build_section("physical", filter_domain(placements, PHYSICAL), aspects)
    spiritual = build_section("spiritual", filter_domain(placements, SPIRITUAL), aspects)

    output = folder / "chapter8_synthesized.md"

    with open(output, "w", encoding="utf-8") as f:
        f.write("# Chapter 8 – Integrated Synthesis\n\n")

        for section_name, section in [
            ("Mental Profile", mental),
            ("Emotional Profile", emotional),
            ("Physical Profile", physical),
            ("Spiritual Profile", spiritual),
        ]:
            f.write(f"## {section_name}\n\n")
            for p in section:
                f.write(p + "\n\n")

    print(f"\nDone. Wrote: {output}")


if __name__ == "__main__":
    main()