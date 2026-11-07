package fr.fkamis;

import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class PlayerRolesTest {
    @Test void preparationAndActivePlayersUseSurvival() {
        assertEquals(PlayerRoles.Mode.SURVIVAL,PlayerRoles.mode(false,false,false,false));
        assertEquals(PlayerRoles.Mode.SURVIVAL,PlayerRoles.mode(false,true,false,false));
        assertEquals(PlayerRoles.Mode.SURVIVAL,PlayerRoles.mode(false,true,false,true));
    }
    @Test void tenDeathsDoNotEliminateAnActiveKingdom() {
        MatchState state=new MatchState(); state.start(List.of(2,2,2,2),false);
        for(int death=0;death<10;death++) {
            assertEquals(PlayerRoles.Mode.SURVIVAL,PlayerRoles.mode(false,true,state.eliminated.contains("Rouge"),state.started));
            assertTrue(state.eliminated.isEmpty()); assertEquals(1,state.day);
        }
        state.eliminate("Rouge",List.of("Rouge","Bleue","Verte","Jaune"));
        assertEquals(PlayerRoles.Mode.SPECTATOR,PlayerRoles.mode(false,true,state.eliminated.contains("Rouge"),true));
    }
    @Test void capturedKingdomStaysSpectatorAcrossModeReconciliations() {
        for(int reconnect=0;reconnect<10;reconnect++)
            assertEquals(PlayerRoles.Mode.SPECTATOR,PlayerRoles.mode(false,true,true,true));
    }
    @Test void administratorNeverBecomesParticipantOrSpectator() {
        assertFalse(PlayerRoles.participant(true,false)); assertFalse(PlayerRoles.participant(true,true));
        assertEquals(PlayerRoles.Mode.CREATIVE,PlayerRoles.mode(true,false,false,false));
        assertEquals(PlayerRoles.Mode.CREATIVE,PlayerRoles.mode(true,false,true,true));
    }
    @Test void newcomerAfterLaunchCannotJoinTheCombatWithoutAssignment() {
        assertEquals(PlayerRoles.Mode.SPECTATOR,PlayerRoles.mode(false,false,false,true));
        assertFalse(PlayerRoles.participant(false,false)); assertTrue(PlayerRoles.participant(false,true));
    }
}
