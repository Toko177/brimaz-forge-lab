package forge.integration;

import forge.GuiDesktop;
import forge.gui.GuiBase;
import forge.model.FModel;
import forge.StaticData;
import forge.item.PaperCard;
import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

public final class AuditCardAIHints {
    static Pattern ROW=Pattern.compile("^(\\d+)\\s+(.+)$");
    public static void main(String[] argv) throws Exception {
        GuiBase.setInterface(new GuiDesktop());
        FModel.initialize(null,null);
        Map<String,List<String>> exceptions=new LinkedHashMap<>();
        for (String input: argv) {
            Path file=Path.of(input);
            List<String> excludes=new ArrayList<>();
            List<String> random=new ArrayList<>();
            int total=0;
            for (String line: Files.readAllLines(file)) {
                Matcher m=ROW.matcher(line.strip());
                if(!m.matches())continue;
                int n=Integer.parseInt(m.group(1));
                String name=m.group(2);
                PaperCard card=StaticData.instance().getCommonCards().getCard(name);
                if (card==null)card=StaticData.instance().getVariantCards().getCard(name);
                if(card==null)throw new IllegalStateException("Missing Forge card "+name);
                total+=n;
                if(card.getRules().getAiHints().getRemAIDecks())excludes.add(name);
                if(card.getRules().getAiHints().getRemRandomDecks())random.add(name);
            }
            if(total!=100)throw new IllegalStateException("Invalid deck length "+file+" "+total);
            exceptions.put(file.getFileName().toString(),excludes);
            System.out.println("AI_CARD_DENYLIST "+file.getFileName()+" "+excludes.size()+" "+excludes);
            System.out.println("AI_CARD_RANDOM_HINT "+file.getFileName()+" "+random.size()+" "+random);
        }
        int brimaz=exceptions.getOrDefault("Brimaz_V3.dck",List.of()).size();
        System.out.println("BRIMAZ_FORGE_AI_BLOCKED_MAIN_CARDS "+brimaz);
        System.out.println("ALL_AI_CARD_HINTS_AUDITED");
    }
}
