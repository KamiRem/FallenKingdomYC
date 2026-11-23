package fr.fkamis;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class TerritoryTransitionsTest {
    @Test void entryExitAndNoSpam(){
        var t=new TerritoryTransitions();UUID id=UUID.randomUUID();
        assertEquals(new TerritoryTransitions.Change(null,"Verte"),t.accept(id,null,"Verte",true,false));
        for(int i=0;i<40;i++)assertTrue(t.accept(id,"Verte","Verte",true,false).empty());
        assertEquals(new TerritoryTransitions.Change("Verte",null),t.accept(id,"Verte",null,true,false));
        assertTrue(t.accept(id,null,null,true,false).empty());
    }
    @Test void teleportBetweenTeamsAndWorlds(){
        var t=new TerritoryTransitions();UUID id=UUID.randomUUID();t.accept(id,null,"Rouge",true,false);
        assertEquals(new TerritoryTransitions.Change("Rouge","Bleue"),t.accept(id,"Rouge","Bleue",true,false));
        assertEquals(new TerritoryTransitions.Change("Bleue",null),t.accept(id,"Bleue",null,true,false));
        assertEquals(new TerritoryTransitions.Change(null,"Jaune"),t.accept(id,null,"Jaune",true,false));
    }
    @Test void nativeDeliverySuppressesFallbackAndStillUpdatesPosition(){
        var t=new TerritoryTransitions();UUID id=UUID.randomUUID();
        assertTrue(t.accept(id,null,"Rouge",true,true).empty());
        assertTrue(t.accept(id,"Rouge","Rouge",true,false).empty());
        assertEquals("Rouge",t.accept(id,"Rouge",null,true,false).left());
    }
    @Test void survivalCreativeAdminAndEliminatedSpectator(){
        assertTrue(TerritoryTransitions.eligible(false,false,false));
        assertTrue(TerritoryTransitions.eligible(true,false,false));
        assertTrue(TerritoryTransitions.eligible(true,false,true));
        assertFalse(TerritoryTransitions.eligible(false,true,false));
        assertFalse(TerritoryTransitions.eligible(false,true,true));
        assertFalse(TerritoryTransitions.eligible(false,false,true));
        var t=new TerritoryTransitions();UUID id=UUID.randomUUID();assertTrue(t.accept(id,null,"Verte",false,false).empty());
        assertTrue(t.accept(id,"Verte","Verte",true,false).empty());
    }
    @Test void joinQuitAndDifferentPlayersDoNotShareState(){
        var t=new TerritoryTransitions();UUID a=UUID.randomUUID(),b=UUID.randomUUID();
        assertEquals("Rouge",t.accept(a,null,"Rouge",true,false).entered());
        assertEquals("Rouge",t.accept(b,null,"Rouge",true,false).entered());
        t.forget(a);assertEquals("Rouge",t.accept(a,null,"Rouge",true,false).entered());
        t.clear();assertEquals("Bleue",t.accept(b,null,"Bleue",true,false).entered());
    }
}
