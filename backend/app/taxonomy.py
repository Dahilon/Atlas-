"""
Taxonomy mapping from GDELT event attributes to high-level categories.

This is deliberately simple and transparent for v1. We use a combination
of EventCode prefixes and QuadClass to map into a tight set of buckets:

- Armed Conflict
- Civil Unrest
- Diplomacy / Sanctions
- Economic Disruption
- Infrastructure / Energy
- Crime / Terror
"""

from __future__ import annotations

from typing import Optional


def map_event_to_category(
    event_code: Optional[str],
    quad_class: Optional[int],
    goldstein: Optional[float],
) -> str:
    """
    Map a GDELT EventCode / QuadClass / GoldsteinScale triple
    into a high-level human-readable category.

    The rules are intentionally coarse but deterministic.
    """

    if event_code:
        prefix2 = event_code[:2]
        prefix3 = event_code[:3]

        # Armed conflict (military, violent clashes)
        if prefix2 in {"18", "19", "20"}:
            return "Armed Conflict"

        # Civil unrest (protests, demonstrations, strikes)
        if prefix2 in {"14"} or prefix3 in {"141", "142"}:
            return "Civil Unrest"

        # Diplomacy / sanctions / political pressure
        if prefix2 in {"07", "08", "09"}:
            return "Diplomacy / Sanctions"

        # Economic disruption (boycotts, embargoes, trade disputes)
        if prefix2 in {"10", "11"}:
            return "Economic Disruption"

        # Infrastructure / energy (attacks on infrastructure, energy assets)
        if prefix3 in {"192", "193"}:
            return "Infrastructure / Energy"

        # Crime / terror (generic conflict, non-state violence)
        if prefix2 in {"17"}:
            return "Crime / Terror"

    # Fallback by QuadClass if EventCode is missing or ambiguous
    if quad_class is not None:
        if quad_class in (3, 4):
            # Material / verbal conflict
            return "Crime / Terror"
        if quad_class in (1, 2):
            # Cooperation / mild tension
            return "Diplomacy / Sanctions"

    return "Civil Unrest"

