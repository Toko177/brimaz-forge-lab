package forge.game.card;

import java.util.Comparator;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.LongAdder;

/**
 * V28 optional READ-ONLY frequency profiler for the real Forge
 * cardHasProperty rules predicate. NEVER caches or bypasses any predicate.
 * Inactive unless -Dbrimaz.profilePropertyQueries=true.
 */
public final class CardPropertyQueryProfiler {
    private CardPropertyQueryProfiler() {}
    public static final boolean ENABLED =
        Boolean.getBoolean("brimaz.profilePropertyQueries");
    private static final ConcurrentHashMap<String,LongAdder> COUNTS =
        new ConcurrentHashMap<>();
    private static final LongAdder TOTAL = new LongAdder();
    private static final int MAX_LABELS = 256;
    private static final String OTHER = "<other-or-overflow>";

    static {
        if (ENABLED) {
            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("FOUR_AI_PROPERTY_PROFILE_TOTAL calls="+TOTAL.sum()
                    +" distinctLabels="+COUNTS.size());
                COUNTS.entrySet().stream()
                    .sorted(Comparator.comparingLong(
                        (Map.Entry<String, LongAdder> item) -> item.getValue().sum()
                    ).reversed())
                    .limit(40)
                    .forEachOrdered(item -> System.out.println(
                         "FOUR_AI_PROPERTY_TOP calls="+item.getValue().sum()
                         +" property="+item.getKey()));
            },"four-ai-property-profile-summary"));
        }
    }

    public static void observe(final String property) {
        if (!ENABLED) return;
        TOTAL.increment();
        String label=property==null?"<null>":property;
        // Bound memory, aggregate exotic dynamically generated script names.
        if (label.length()>80) label=label.substring(0,80)+"...";
        if (!COUNTS.containsKey(label) && COUNTS.size()>=MAX_LABELS) {
            label=OTHER;
        }
        COUNTS.computeIfAbsent(label,k -> new LongAdder()).increment();
    }

    public static long total() { return TOTAL.sum(); }
    public static long count(final String property) {
        LongAdder value=COUNTS.get(property);
        return value==null?0:value.sum();
    }
}
