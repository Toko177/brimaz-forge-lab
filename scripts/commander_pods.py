"""Pinned active four-seat Commander matchup rosters.

Only this module defines the two active pods for real Forge gameplay and
the deckbuilding laboratory. Seven SHA256-pinned source decks in forge_decks/
remain unchanged. History and prior campaign rosters remain immutable.

2026-10-12: replace Amalia (Kaal_22193355) as a live opponent in the
artifact pod with Dungeon Party Time (Kaal_10347090), already canonical.
Five eligible distinct Kaal opponents fill six opponent slots: precisely
one cross-pod repeat is deliberate. Every game still has four distinct decks.
"""
ROSTER_VERSION = "2026-10-12-dungeon-replaces-amalia"
CHALLENGER = "Brimaz_V3"
PODS = {
    "aristo": (
        CHALLENGER,
        "Kaal_9594008",  # Radha
        "Kaal_10347090", # Dungeon Party Time
        "Kaal_21930525", # Zimone and Dina
    ),
    "artifact": (
        CHALLENGER,
        "Kaal_23328062", # Lathril
        "Kaal_11485202", # Urza
        "Kaal_10347090", # Dungeon Party Time; cross-pod reuse
    ),
}
# deckbuild_run.verify_inputs combines [candidate] + OPPONENTS[pod].
# Lists intentionally preserve compatibility with the legacy deckbuilder.
OPPONENTS = {pod: list(seats[1:]) for pod, seats in PODS.items()}
RETIRED_FROM_ACTIVE_PODS = ("Kaal_22193355",) # Amalia remains SHA256 pinned.

def verify_rosters():
    if set(PODS) != {"aristo", "artifact"}:
        raise ValueError("Expected exactly the two audited pods")
    for pod, seats in PODS.items():
        if len(seats) != 4 or len(set(seats)) != 4 or seats[0] != CHALLENGER:
            raise ValueError("Not four distinct Commander seats: "+pod)
        if any(deck in RETIRED_FROM_ACTIVE_PODS for deck in seats):
            raise ValueError("Retired deck reintroduced into "+pod)
    if set(OPPONENTS["aristo"]) & set(OPPONENTS["artifact"]) != {"Kaal_10347090"}:
        raise ValueError("Unexpected opponent overlap between pods")
    return True

verify_rosters()
