package forge.ai;

import forge.ai.ability.IncubateAi;
import forge.ai.ability.CannotPlayAi;
import forge.game.ability.ApiType;

/** Real patched Forge proof that Incubate has a dedicated AI evaluation. */
public final class BrimazV12IncubateChecks {
    public static void main(String[] args) {
        SpellAbilityAi eval = SpellApiToAi.Converter.get(ApiType.Incubate);
        if (eval == null) throw new AssertionError("Incubate is not mapped");
        if (!(eval instanceof IncubateAi)) {
            throw new AssertionError("Incubate must have its own AI evaluation class: "
                    + eval.getClass().getName());
        }
        if (eval instanceof CannotPlayAi) {
            throw new AssertionError("Incubate must not route into stock CannotPlayAi");
        }
        System.out.println("V12_INCUBATE_MAPPED " + eval.getClass().getName());
        System.out.println("V12_INCUBATE_TESTS_OK");
    }
}