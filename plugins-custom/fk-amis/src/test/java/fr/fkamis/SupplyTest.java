package fr.fkamis;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import java.util.*;

class SupplyTest {
    private LootTable table() {
        return new LootTable(List.of(
                new LootTable.Tier("common",65,List.of(new LootTable.Entry("COAL",4,8,1,"",0))),
                new LootTable.Tier("uncommon",28,List.of(new LootTable.Entry("IRON_INGOT",3,6,3,"",0))),
                new LootTable.Tier("rare",7,List.of(new LootTable.Entry("DIAMOND",1,2,24,"",0)))),
                Map.of("COAL",16,"IRON_INGOT",12,"DIAMOND",2),3,48,96);
    }
    @Test void thirtyMinutesMeans1800ActiveSeconds() {
        SupplyClock clock=new SupplyClock(1800);
        for(int i=0;i<1799;i++)assertFalse(clock.advance(true,false,false,true));
        assertEquals(1,clock.remaining);assertTrue(clock.advance(true,false,false,true));
    }
    @Test void pregamePauseVictoryAndNoParticipantsStopClock() {
        SupplyClock clock=new SupplyClock(1500);
        for(int i=0;i<5000;i++) {
            assertFalse(clock.advance(false,false,false,true)); assertFalse(clock.advance(true,true,false,true));
            assertFalse(clock.advance(true,false,true,true)); assertFalse(clock.advance(true,false,false,false));
        }
        assertEquals(1500,clock.remaining);
    }
    @Test void persistedRemainingResumesWithoutOfflineCatchup() {
        SupplyClock original=new SupplyClock(1800);
        for(int i=0;i<135;i++)original.advance(true,false,false,true);
        SupplyClock restored=new SupplyClock(original.remaining);
        assertEquals(1665,restored.remaining); restored.advance(true,false,false,true);assertEquals(1664,restored.remaining);
    }
    @Test void weightedCategoriesMatchConfiguredProbabilities() {
        LootTable t=table();Random r=new Random(12);Map<String,Integer> frequencies=new HashMap<>();
        for(int i=0;i<100000;i++)frequencies.merge(t.category(r),1,Integer::sum);
        assertEquals(.65,frequencies.get("common")/100000.0,.006);
        assertEquals(.28,frequencies.get("uncommon")/100000.0,.006);
        assertEquals(.07,frequencies.get("rare")/100000.0,.006);
    }
    @Test void quantitiesBudgetsAndRollCountsAreBounded() {
        LootTable t=table();Random r=new Random(47);
        for(int event=0;event<10000;event++) {
            Map<String,Integer> total=new HashMap<>();int eventCost=0;
            for(var bundle:t.draw(2,r)) {
                assertTrue(bundle.size()<=3);int cost=0;
                for(var item:bundle) {
                    assertFalse(LootTable.forbidden(item.material())); total.merge(item.material(),item.amount(),Integer::sum);
                    cost+=item.amount()*(item.material().equals("DIAMOND")?24:item.material().equals("IRON_INGOT")?3:1);
                }
                assertTrue(cost<=48);eventCost+=cost;
            }
            assertTrue(eventCost<=96);total.forEach((m,n)->assertTrue(n<=t.caps.get(m)));
        }
    }
    @Test void forbiddenLootCannotBeConfigured() {
        for(String material:List.of("NETHERITE_SWORD","ANCIENT_DEBRIS","ELYTRA","TOTEM_OF_UNDYING","ENCHANTED_GOLDEN_APPLE","COMMAND_BLOCK")) {
            assertTrue(LootTable.forbidden(material));
            assertThrows(IllegalArgumentException.class,()->new LootTable(List.of(new LootTable.Tier("bad",100,List.of(
                    new LootTable.Entry(material,1,1,1,"",0)))),Map.of(material,1),3,48,96));
        }
    }
}
