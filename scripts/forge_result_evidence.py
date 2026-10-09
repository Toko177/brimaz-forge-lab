"""Independent checks for the four-seat Forge Commander result transcript.

This is an evidence check, not a proof that Forge implements every Oracle rule.
Do not select or alter games/seeds in order to manufacture Brimaz victories.
"""
import re

_MATCH = re.compile(
    r"^Ai\(1\)-(.+?) vs Ai\(2\)-(.+?) vs Ai\(3\)-(.+?) vs Ai\(4\)-(.+?) - one game of Commander seed",
    re.M,
)
_RESULT = re.compile(
    r"^Game Result: Game\s+\d+\s+ended in\s+(\d+)\s*ms\.\s*Ai\((\d+)\)-(.+?) has won!",
    re.M,
)
_OUTCOME = re.compile(
    r"^Game Outcome: Ai\((\d+)\)-(.+?) has (won|lost) because (.+?)\s*$",
    re.M,
)


def verify_result_evidence(raw, game, seats):
    """Return a list of disqualifying evidence issues; fail closed on ambiguity.

    Historical games without clock_seconds used Forge's original 360 s limit.
    For new games, the actual configured Forge simulation-clock is mandatory
    via batch.py's clock_seconds.  The 2.5 s guard is the batch classifier's
    existing conservative stop-margin, not a claim of a particular Forge rule.
    """
    issues = []
    declarations = _MATCH.findall(raw)
    if len(declarations) != 1:
        issues.append("Expected exactly one four-player Commander declaration")
        declared = None
    else:
        # Forge declares players with '[Default]'/'[Experimental]' profile
        # suffixes; Game Outcome / Game Result omit these suffixes.
        declared = tuple(re.sub(r" \[(?:Default|Experimental|Cautious|Reckless)\]$", "", name)
                         for name in declarations[0])

    results = _RESULT.findall(raw)
    if len(results) != 1:
        issues.append(f"Expected one Game Result, found {len(results)}")
        result = None
    else:
        result = results[0]

    outcomes = _OUTCOME.findall(raw)
    if len(outcomes) != 4:
        issues.append(f"Expected four individual Game Outcome entries, found {len(outcomes)}")

    indexed = {}
    for seat_text, name, state, reason in outcomes:
        seat = int(seat_text)
        if seat not in (1, 2, 3, 4) or seat in indexed:
            issues.append("Duplicate or invalid Game Outcome seat " + seat_text)
            continue
        indexed[seat] = (name.strip(), state, reason.strip())
        if not reason.strip():
            issues.append("Missing outcome reason for seat " + seat_text)
        if declared and name.strip() != declared[seat - 1]:
            issues.append("Game Outcome seat name differs from Commander declaration")
    if set(indexed) != {1, 2, 3, 4}:
        issues.append("Game Outcome does not cover exactly four distinct seats")

    winners = [seat for seat, (_, state, _) in indexed.items() if state == "won"]
    losers = [seat for seat, (_, state, _) in indexed.items() if state == "lost"]
    if len(winners) != 1 or len(losers) != 3:
        issues.append("Expected one won outcome and three lost outcomes")

    if len(seats) != 4 or len(set(seats)) != 4:
        issues.append("Expected four distinct canonical deck identities")
    winner = winners[0] if len(winners) == 1 else None
    if result:
        milliseconds, result_seat_text, result_name = result
        result_seat = int(result_seat_text)
        if not 1 <= result_seat <= 4:
            issues.append("Game Result winner seat outside four seats")
        if winner != result_seat:
            issues.append("Game Result does not match the four Game Outcome records")
        if declared and 1 <= result_seat <= 4 and result_name.strip() != declared[result_seat - 1]:
            issues.append("Game Result winner name differs from Commander declaration")
        if game.get("winner_seat") != result_seat:
            issues.append("Manifest winner seat differs from raw Game Result")
        if len(seats) == 4 and 1 <= result_seat <= 4 and game.get("winner_deck") != seats[result_seat - 1]:
            issues.append("Manifest winner deck differs from raw Game Result")
        if game.get("game_milliseconds") != int(milliseconds):
            issues.append("Manifest engine duration differs from raw Game Result")
        clock = game.get("clock_seconds", 360)
        if type(clock) is not int or clock <= 2:
            issues.append("Missing or invalid configured simulation-clock seconds")
        elif int(milliseconds) >= clock * 1000 - 2500:
            issues.append("Game Result lies within 2.5 s of configured simulation cutoff")
    if "Brimaz_V3" in seats and len(seats) == 4:
        if game.get("brimaz_seat") != seats.index("Brimaz_V3") + 1:
            issues.append("Brimaz seat differs from canonical deck order")
    if winner is not None and "Brimaz_V3" in seats and len(seats) == 4:
        expected = winner == seats.index("Brimaz_V3") + 1
        if game.get("brimaz_win") is not expected:
            issues.append("Manifest Brimaz win flag differs from four player outcomes")
    if game.get("status") != "complete":
        issues.append("Game is not marked naturally complete")
    if game.get("process_exit") != 0:
        issues.append("Forge process exit is nonzero")
    if "Stopping slow match as draw" in raw:
        issues.append("Forge ended game artificially at its simulation cutoff")
    return issues


def inspect_ai_quality_signatures(raw):
    """Warnings indicate AI quality or responsiveness, not rules illegality."""
    return {
        "evaluation_timeouts": raw.count("java.util.concurrent.TimeoutException"),
        "invalid_attack_fallbacks": raw.count("AI Attack declaration invalid"),
        "incubate_handler_warnings": raw.count("No AI assigned for API: Incubate"),
        "decision_thread_timeout_samples": raw.count("AI eval thread at timeout:"),
    }
