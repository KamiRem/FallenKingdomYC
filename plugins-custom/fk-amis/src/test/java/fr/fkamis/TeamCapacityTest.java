package fr.fkamis;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class TeamCapacityTest {
    @Test void allFourFormatsStartAndResolveVictory() {
        for(int size=1;size<=4;size++) {
            MatchState match=new MatchState(); match.start(List.of(size,size,size,size),false,size);
            assertTrue(match.running()); assertEquals(1,match.day);
            var teams=List.of("Rouge","Bleue","Verte","Jaune");
            for(String team:List.of("Rouge","Bleue","Jaune")) match.eliminate(team,teams);
            assertEquals("Verte",match.winner); assertTrue(match.paused);
        }
    }
    @Test void rejectInvalidCapacitiesAndIncompleteOrOverflowingTeams() {
        for(int size:new int[]{0,5}) assertThrows(IllegalArgumentException.class,()->TeamCapacity.validate(size));
        for(int size=1;size<=4;size++) {
            int capacity=size;
            assertThrows(IllegalStateException.class,()->new MatchState().start(List.of(capacity,capacity,capacity,0),false,capacity));
            assertThrows(IllegalStateException.class,()->new MatchState().start(List.of(capacity+1,capacity,capacity,capacity),true,capacity));
        }
    }
    @Test void mixedTeamsOfOneToFourStartWithoutOverride() {
        MatchState match=new MatchState();match.start(List.of(1,2,3,4),false,4);
        assertTrue(match.running());
        assertThrows(IllegalStateException.class,()->new MatchState().start(List.of(4,4,4,5),true,4));
        assertThrows(IllegalStateException.class,()->new MatchState().start(List.of(4,4,4,0),true,4));
    }
    @Test void sixteenMemberStatisticsAndVictorySurviveSerialization() {
        MatchStatistics model=new MatchStatistics();var teams=List.of("Rouge","Bleue","Verte","Jaune");
        for(int i=0;i<16;i++)model.member(new UUID(0,i+1),"Participant"+i,teams.get(i/4));
        model.captureEvent("Rouge","Bleue",List.of(new UUID(0,1),new UUID(0,2),new UUID(0,3),new UUID(0,4)));
        model.eliminated("Bleue",4);model.eliminated("Verte",3);model.eliminated("Jaune",2);model.winner="Rouge";
        MatchStatistics restored=MatchStatistics.read(model.json());
        assertEquals(16,restored.players.size());
        for(String team:teams)assertEquals(4,restored.team(team).members());
        assertEquals(1,restored.team("Rouge").captures());assertEquals(1,restored.team("Rouge").rank());
        assertEquals(4,restored.players.values().stream().filter(p->p.captures==1).count());
        assertEquals(model.json(),restored.json());
    }
    @Test void officialRosterControlsCaptureThresholdDespiteDisconnects() {
        for(int size=1;size<=4;size++) assertEquals(Math.min(2,size),TeamCapacity.attackers(2,size));
        assertEquals(0,TeamCapacity.attackers(2,0));
        assertEquals(2,TeamCapacity.attackers(2,3)); // Aucun effectif connecté dans cette API.
    }
    @Test void capacityChangesNeverEraseExistingRosters() {
        assertThrows(IllegalArgumentException.class,()->TeamCapacity.existing(1,2,false,List.of(2,2,2,2)));
        assertDoesNotThrow(()->TeamCapacity.existing(3,2,false,List.of(2,2,2,2)));
        assertThrows(IllegalArgumentException.class,()->TeamCapacity.existing(3,2,true,List.of(2,2,2,2)));
        assertDoesNotThrow(()->TeamCapacity.existing(2,2,true,List.of(2,2,2,2)));
    }
    @Test void captureClockCompletesForAllFourFormats() {
        for(int size=1;size<=4;size++) {
            assertTrue(size>=TeamCapacity.attackers(2,size));
            CaptureClock clock=new CaptureClock(); clock.advance("Rouge",false,1200);
            for(int tick=1;tick<1200;tick++) assertFalse(clock.advance("Rouge",false,1200));
            assertTrue(clock.advance("Rouge",false,1200));
        }
    }
}
