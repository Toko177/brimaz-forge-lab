package forge.ai;

import java.util.concurrent.ConcurrentHashMap;

/**
 * Per-AI, per-real-game cooldown for spell-ability evaluation that actually
 * exceeded the Forge FutureTask timeout. This is NOT a card legality rule.
 * Card IDs are scoped by the AiController owning this object.
 */
public final class AiTimeoutCooldownPolicy {
    private final ConcurrentHashMap<Integer, Integer> cooldownEndTurn = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<Integer, Integer> strikes = new ConcurrentHashMap<>();

    public synchronized int recordTimeout(final int cardId, final int currentTurn) {
        if (cardId <= 0 || currentTurn < 0) return -1;
        int count = strikes.merge(cardId, 1, Integer::sum);
        // 1st timeout: 4 global turns; repeat: 8, then 12, capped at 16.
        int ttl = Math.min(16, count * 4);
        int until = currentTurn + ttl;
        cooldownEndTurn.put(cardId, until);
        return until;
    }

    public boolean shouldSkip(final int cardId, final int currentTurn) {
        if (cardId <= 0 || currentTurn < 0) return false;
        Integer end = cooldownEndTurn.get(cardId);
        if (end == null) return false;
        if (currentTurn <= end) return true;
        cooldownEndTurn.remove(cardId, end);
        return false;
    }

    public int strikeCount(final int cardId) {
        return strikes.getOrDefault(cardId, 0);
    }
}
