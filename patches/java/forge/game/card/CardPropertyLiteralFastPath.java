package forge.game.card;

import forge.game.player.Player;
import java.util.concurrent.atomic.LongAdder;

/**
 * Exactly equivalent fast paths only for these five complete, literal
 * Forge card-property expressions. Called AFTER normal LKI/controller
 * acquisition and phased-out exclusion. Other properties use stock logic.
 */
public final class CardPropertyLiteralFastPath {
    private CardPropertyLiteralFastPath() {}

    public static final boolean ENABLED =
        Boolean.getBoolean("brimaz.fastCardPropertyExactLiterals");
    public static final boolean SHADOW =
        Boolean.getBoolean("brimaz.cardPropertyShadowVerify");
    public static final boolean TRACE =
        Boolean.getBoolean("brimaz.cardPropertyFastTrace");
    private static final LongAdder HITS=new LongAdder();
    private static final LongAdder SHADOW_CHECKED=new LongAdder();
    private static final LongAdder SHADOW_MISMATCHES=new LongAdder();

    static {
        if (ENABLED && TRACE) {
            Runtime.getRuntime().addShutdownHook(new Thread(() ->
                System.out.println("FOUR_AI_V30_CARD_PROPERTY_FAST_STATS hits="
                    +HITS.sum()+" verified="+SHADOW_CHECKED.sum()
                    +" mismatches="+SHADOW_MISMATCHES.sum()),"v30-literal-fast-counter"));
        }
    }

    /**
     * Return null for unknown literals. Exact-branch source equivalence:
     * IsCommander -> card.isCommander(); Self -> card.equals(source);
     * YouCtrl -> controller.equals(sourceController);
     * YouOwn -> card.getOwner().equals(sourceController);
     * Other -> !card.equals(source).
     * The caller handles pre-existing phased-out exclusion FIRST.
     */
    public static Boolean evaluate(final Card card,final String property,
                                   final Player sourceController,final Card source,
                                   final Player lkiController) {
        if (property==null) return null;
        switch(property) {
            case "IsCommander": return card.isCommander();
            case "Self": return card.equals(source);
            case "YouCtrl": return lkiController.equals(sourceController);
            case "YouOwn": return card.getOwner().equals(sourceController);
            case "Other": return !card.equals(source);
            default: return null;
        }
    }

    public static void hit() {
        if (TRACE) HITS.increment();
    }

    public static void verify(final boolean actual,final boolean stock,
                              final String property) {
        if (!SHADOW) return;
        SHADOW_CHECKED.increment();
        if (actual!=stock) {
            SHADOW_MISMATCHES.increment();
            throw new IllegalStateException(
                "FOUR_AI_V30_RULE_EQUIVALENCE_FAILURE property="+property+
                " optimized="+actual+" stock="+stock);
        }
    }
}
