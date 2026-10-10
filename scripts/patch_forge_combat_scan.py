#!/usr/bin/env python3
"""Opt-in, four-seat Forge 2.0.15 combat trigger scan optimization.

Replaces allocation-heavy flattened FCollection scans in the two
before-first-strike destruction predicates with a direct nested traversal.
Both paths use exactly the same trigger predicate. A JVM system property
can shadow-verify the direct traversal against the original deduplicated
collection scan on the SAME battlefield/attacker/blocker.

Flags (set through JAVA_TOOL_OPTIONS, before -jar):
  -Dbrimaz.fastCombatTriggerScan=true
  -Dbrimaz.verifyCombatTriggerScan=true

The Forge engine remains authoritative for legality and all combat damage.
This patch changes no attacks, blocks, scores, costs or card definitions.
"""
import argparse
import hashlib
import pathlib
import subprocess
import tempfile
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("--jar", required=True)
p.add_argument("--tag", default="forge-2.0.15")
args = p.parse_args()
jar = pathlib.Path(args.jar).resolve()
if not jar.is_file():
    p.error("Missing Forge jar")

source_path = "forge-ai/src/main/java/forge/ai/ComputerUtilCombat.java"
url = f"https://raw.githubusercontent.com/Card-Forge/forge/{args.tag}/{source_path}"
with urllib.request.urlopen(url, timeout=90) as response:
    source = response.read().decode("utf-8")

# Fail closed on source drift: exactly two sites, at exact method signatures.
scan_header = "        final FCollection<Trigger> theTriggers = new FCollection<>();"
if source.count(scan_header) != 2:
    raise RuntimeError("Unexpected upstream combat trigger scan count")

def replace_scan(text, signature, original_tail, against_attacker):
    start = text.index(signature)
    scan_start = text.index(scan_header, start)
    scan_end = text.index(original_tail, scan_start) + len(original_tail)
    # Keep the method's closing brace; the block ends at its own return false.
    if scan_end - scan_start > 2500 or scan_end - scan_start < 400:
        raise RuntimeError("Unexpected original scan length: " + signature)
    return (
        text[:scan_start]
        + "        return brimazEarlyDestroyTrigger(attacker, blocker, "
        + str(against_attacker).lower() + ");\n"
        + text[scan_end:]
    )

source = replace_scan(
    source,
    "    public static boolean canDestroyAttackerBeforeFirstStrike(",
    "        return false;\n",
    True,
)
source = replace_scan(
    source,
    "    public static boolean canDestroyBlockerBeforeFirstStrike(",
    "    \treturn false;\n",
    False,
)
if source.count(scan_header):
    raise RuntimeError("Original trigger allocations still present in methods")

helper = r'''
    // Decision-only optimization shared by ALL four AI seats.
    // The original flattened FCollection scan is retained as the control arm.
    private static final boolean BRIMAZ_FAST_COMBAT_TRIGGER_SCAN =
            Boolean.getBoolean("brimaz.fastCombatTriggerScan");
    private static final boolean BRIMAZ_VERIFY_COMBAT_TRIGGER_SCAN =
            Boolean.getBoolean("brimaz.verifyCombatTriggerScan");

    private static boolean brimazTriggerDestroys(final Card attacker, final Card blocker,
            final Trigger trigger, final boolean againstAttacker) {
        final Card source = trigger.getHostCard();

        if (!combatTriggerWillTrigger(attacker, blocker, trigger, null)) {
            return false;
        }
        final SpellAbility sa = trigger.ensureAbility();
        if (sa == null || !ApiType.Destroy.equals(sa.getApi()) || !sa.hasParam("Defined")) {
            return false;
        }
        final String defined = sa.getParam("Defined");
        if (defined.startsWith(againstAttacker ? "TriggeredAttacker" : "TriggeredBlocker")) {
            return true;
        }
        if (defined.equals("Self") && source.equals(againstAttacker ? attacker : blocker)) {
            return true;
        }
        return defined.equals("TriggeredTarget")
                && source.equals(againstAttacker ? blocker : attacker);
    }

    private static boolean brimazScanCombatDestroyTriggers(final Card attacker,
            final Card blocker, final boolean againstAttacker, final boolean nested) {
        final Game game = attacker.getGame();
        if (nested) {
            // No intermediate collection; short-circuit as soon as a matching
            // legal/triggering Destroy ability is found. No heuristic shortcut.
            for (Card card : game.getCardsIn(ZoneType.Battlefield)) {
                for (Trigger trigger : card.getTriggers()) {
                    if (brimazTriggerDestroys(attacker, blocker, trigger, againstAttacker)) {
                        return true;
                    }
                }
            }
            return false;
        }

        // Reference: byte-for-byte ordering/collection semantics of Forge 2.0.15.
        final FCollection<Trigger> theTriggers = new FCollection<>();
        for (Card card : game.getCardsIn(ZoneType.Battlefield)) {
            theTriggers.addAll(card.getTriggers());
        }
        for (Trigger trigger : theTriggers) {
            if (brimazTriggerDestroys(attacker, blocker, trigger, againstAttacker)) {
                return true;
            }
        }
        return false;
    }

    private static boolean brimazEarlyDestroyTrigger(final Card attacker,
            final Card blocker, final boolean againstAttacker) {
        if (!BRIMAZ_FAST_COMBAT_TRIGGER_SCAN) {
            return brimazScanCombatDestroyTriggers(attacker, blocker, againstAttacker, false);
        }
        final boolean quick = brimazScanCombatDestroyTriggers(attacker, blocker,
                againstAttacker, true);
        if (BRIMAZ_VERIFY_COMBAT_TRIGGER_SCAN) {
            final boolean reference = brimazScanCombatDestroyTriggers(attacker, blocker,
                    againstAttacker, false);
            if (quick != reference) {
                throw new IllegalStateException(
                        "COMBAT_TRIGGER_SCAN_MISMATCH attacker=" + attacker.getName()
                        + " blocker=" + blocker.getName()
                        + " againstAttacker=" + againstAttacker
                        + " nested=" + quick + " original=" + reference);
            }
        }
        return quick;
    }

'''
anchor = "    // can the combatant be potentially destroyed or is it potentially indestructible?"
if source.count(anchor) != 1:
    raise RuntimeError("Cannot locate safe insertion point")
source = source.replace(anchor, helper + anchor, 1)
if source.count("brimazEarlyDestroyTrigger(attacker, blocker,") != 2:
    raise RuntimeError("Expected two call-site replacements")
with tempfile.TemporaryDirectory() as tmp:
    root = pathlib.Path(tmp)
    java = root / source_path.removeprefix("forge-ai/src/main/java/")
    java.parent.mkdir(parents=True, exist_ok=True)
    java.write_text(source, encoding="utf-8")
    classes = root / "classes"
    classes.mkdir()
    subprocess.run(
        ["javac", "--release", "21", "-cp", str(jar), "-d", str(classes), str(java)],
        check=True, timeout=240,
    )
    compiled = classes / "forge/ai/ComputerUtilCombat.class"
    if not compiled.is_file():
        raise RuntimeError("ComputerUtilCombat.class missing after compilation")
    subprocess.run(
        ["jar", "uf", str(jar), "-C", str(classes), "forge/ai/ComputerUtilCombat.class"],
        check=True, timeout=120,
    )
    print("COMBAT_SCAN_CLASS_SHA256", hashlib.sha256(compiled.read_bytes()).hexdigest())
print("COMBAT_SCAN_JAR_SHA256", hashlib.sha256(jar.read_bytes()).hexdigest())
