package fr.fkamis;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class AnnouncementsTest {
    @Test void accentsAndPunctuationRemainLiteral() {
        assertEquals("Événement spécial — à l'arène !",Announcements.validate(" Événement spécial — à l'arène ! "));
        assertEquals("<red>texte",Announcements.validate("<red>texte"));
    }
    @Test void rejectsOverflowEmptyAndFormattingInjection() {
        for(String input:new String[]{" ","a".repeat(241),"§cRouge","&cRouge","texte\nligne","texte\u202Eevil"})
            assertThrows(IllegalArgumentException.class,()->Announcements.validate(input));
        assertEquals(240,Announcements.validate("a".repeat(240)).length());
    }
    @Test void longTitleIsTruncatedWithoutSplittingUnicode() {
        String text="😀".repeat(100);String subtitle=Announcements.subtitle(text);
        assertEquals(80,subtitle.codePointCount(0,subtitle.length())); assertTrue(subtitle.endsWith("…"));
    }
}
