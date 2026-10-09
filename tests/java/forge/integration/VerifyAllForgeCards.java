package forge.integration;
import forge.StaticData;
import forge.GuiDesktop;
import forge.gui.GuiBase;
import forge.model.FModel;
import forge.item.PaperCard;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.regex.Pattern;
import java.util.regex.Matcher;
import java.util.ArrayList;
import java.util.List;
public final class VerifyAllForgeCards {
    private static final Pattern ROW=Pattern.compile("^(\\d+)\\s+(.+)$");
    public static void main(String[] argv) throws Exception {
        if (argv.length==0)throw new IllegalArgumentException("Must supply .dck paths");
        GuiBase.setInterface(new GuiDesktop());
        FModel.initialize(null,null);
        List<String> missing=new ArrayList<>();
        int checked=0;
        for(String arg : argv) {
            Path path=Path.of(arg);
            int total=0, found=0;
            for(String line:Files.readAllLines(path)) {
                Matcher m=ROW.matcher(line.trim());
                if(!m.matches())continue;
                int qty=Integer.parseInt(m.group(1));
                String name=m.group(2).trim();
                PaperCard card=StaticData.instance().getCommonCards().getCard(name);
                if(card==null)card=StaticData.instance().getVariantCards().getCard(name);
                if(card==null) {
                    missing.add(path.getFileName()+": "+name);
                    System.out.println("FORGE_CARD_MISSING "+path.getFileName()+" "+name);
                } else {
                    found+=qty;
                }
                total+=qty;
                checked++;
            }
            System.out.println("FORGE_DECK_CARD_CHECK "+path.getFileName()+" total="+total+" resolved="+found);
            if(total!=100 || found!=100)missing.add(path+" total="+total+" found="+found);
        }
        System.out.println("FORGE_ALL_CARD_IDENTIFIERS_CHECKED "+checked);
        if(!missing.isEmpty())throw new IllegalStateException("Missing Forge cards: "+missing);
        System.out.println("FORGE_ALL_SEVEN_DECKS_SUPPORTED");
    }
}
