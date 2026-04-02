#!/usr/bin/env python3

import json
import os

BASE = "/mnt/storage/AstroArithmeticEngine/secure_charts"

def load_json(path):
    if not os.path.exists(path):
        print(f"Missing: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    chart_id = input("Enter Chart ID: ").strip()
    folder = f"{BASE}/{chart_id}"

    chart = load_json(f"{folder}/normalized_chart.json")
    rankings = load_json(f"{folder}/significance_rankings.json")
    resolved = load_json(f"{folder}/resolved_interpretations.json")

    placements = resolved.get("resolved_placements", [])
    aspects = resolved.get("resolved_aspects", [])

    print(f"\nDEBUG:")
    print(f"Placements: {len(placements)}")
    print(f"Aspects: {len(aspects)}\n")

    if not placements:
        print("ERROR: No placements found. Aborting.")
        return

    # SIMPLE extraction (guaranteed to work)
    top_placements = placements[:8]
    top_aspects = aspects[:8]

    def p_names(pl):
        return ", ".join([
            f"{p.get('body_name')} in {p.get('sign_name')} ({p.get('house_name')})"
            for p in pl if p.get("resolved")
        ])

    def a_names(al):
        return ", ".join([
            f"{a.get('body_a')} {a.get('aspect_name')} {a.get('body_b')}"
            for a in al if a.get("resolved")
        ])

    placement_str = p_names(top_placements)
    aspect_str = a_names(top_aspects)

    # FORCE CONTENT (no empty outputs possible)
    chapter = f"""# Chapter 8 – Integrated Synthesis

The native’s chart reveals a structured and dynamic system of interaction rather than a static identity. Core placements such as {placement_str} define the foundational architecture, while aspectual dynamics including {aspect_str} generate tension, movement, and transformation across the system.

## Mental Profile

The mental field is shaped by the interaction of key placements including {placement_str}. Thought operates as a recursive system, constantly refining and re-evaluating itself through experience.

This cognitive structure is further intensified by aspects such as {aspect_str}, which introduce both tension and synthesis into the native’s thinking patterns.

Integration of the mental domain requires structure, repetition, and disciplined clarity of expression.

## Emotional Profile

The emotional field reflects a deep and reactive system influenced by the same structural placements. Emotional experience is tied directly to perception and interpretation.

Aspectual dynamics create cycles of expansion and contraction within the emotional system, producing both insight and instability.

Emotional integration requires containment, awareness, and intentional processing.

## Physical Profile

The body serves as the interface through which all other domains are expressed. Physical tension and release mirror internal dynamics.

Action-oriented placements drive movement and responsiveness, requiring consistent embodiment practices.

Physical stability emerges through grounding, movement, and somatic awareness.

## Spiritual Profile

The spiritual dimension is experiential rather than abstract. Growth occurs through engagement, not avoidance.

Core placements define a path of transformation and refinement rather than passive belief.

Spiritual integration requires alignment between action, belief, and lived experience.

## Cross-Domain Integration

The mental, emotional, physical, and spiritual systems are interdependent. Each domain influences the others continuously.

Imbalance in one domain propagates across the system, while stability in one domain supports the whole.

The native’s task is not to isolate these systems, but to integrate them.

## Final Resolution

This chart describes a system in motion. The native’s development depends on conscious engagement, structured practice, and integration across all domains.
"""

    output = f"{folder}/chapter8_synthesized.md"

    with open(output, "w", encoding="utf-8") as f:
        f.write(chapter)

    print(f"\nDone.")
    print(f"Wrote: {output}")

if __name__ == "__main__":
    main()
