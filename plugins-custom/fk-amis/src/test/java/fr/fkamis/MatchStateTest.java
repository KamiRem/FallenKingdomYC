package fr.fkamis;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class MatchStateTest {
    private static final List<String> TEAMS = List.of("Rouge", "Bleue", "Verte", "Jaune");
    @Test void refusesIncompleteAndOversizedRoster() {
        MatchState s = new MatchState();
        assertThrows(IllegalStateException.class, () -> s.start(List.of(2, 2, 2, 1), false));
        assertThrows(IllegalStateException.class, () -> s.start(List.of(3, 2, 2, 1), true));
        assertThrows(IllegalStateException.class, () -> s.start(List.of(2, 2), true));
        assertFalse(s.started);
    }
    @Test void explicitOverrideAcceptsSmallRosterButStillFourTeams() {
        MatchState s = new MatchState(); s.start(List.of(1, 1, 1, 1), true);
        assertEquals(1, s.day); assertTrue(s.running());
    }
    @Test void daysRequireManualTransitionAndValidObjectivesAtThree() {
        MatchState s = new MatchState(); s.start(List.of(2, 2, 2, 2), false);
        assertFalse(s.assaults(3)); s.nextDay(3, false); assertEquals(2, s.day);
        assertThrows(IllegalStateException.class, () -> s.nextDay(3, false)); assertEquals(2, s.day);
        s.nextDay(3, true); assertTrue(s.assaults(3));
        s.paused = true; assertFalse(s.assaults(3)); assertEquals(3, s.day);
        s.paused = false; assertTrue(s.assaults(3));
    }
    @Test void thirdEliminationDeclaresOnlyRemainingKingdom() {
        MatchState s = new MatchState(); s.start(List.of(2, 2, 2, 2), false);
        s.eliminate("Rouge", TEAMS); assertEquals("", s.winner);
        s.eliminate("Bleue", TEAMS); assertEquals("", s.winner);
        s.eliminate("Jaune", TEAMS); assertEquals("Verte", s.winner); assertTrue(s.paused);
        assertFalse(s.running()); assertThrows(IllegalStateException.class, () -> s.nextDay(3, true));
    }
    @Test void cannotStartTwiceOrEliminateUnknownTeam() {
        MatchState s = new MatchState(); s.start(List.of(2, 2, 2, 2), false);
        assertThrows(IllegalStateException.class, () -> s.start(List.of(2, 2, 2, 2), false));
        assertThrows(IllegalStateException.class, () -> s.eliminate("Inconnue", TEAMS));
    }
    @Test void captureRequiresSixtyContinuousSamples() {
        CaptureClock clock = new CaptureClock();
        assertFalse(clock.advance("Rouge", false, 1200)); // Détection initiale, zéro tick écoulé.
        for (int i = 0; i < 1199; i++) assertFalse(clock.advance("Rouge", false, 1200));
        assertTrue(clock.advance("Rouge", false, 1200));
    }
    @Test void defenderDisconnectOrTeamChangeResetsCapture() {
        CaptureClock clock = new CaptureClock();
        for (int i = 0; i < 50; i++) clock.advance("Rouge", false, 60);
        assertFalse(clock.advance("Rouge", true, 60)); assertEquals(0, clock.elapsedTicks);
        clock.advance("Rouge", false, 60); clock.advance(null, false, 60); assertEquals(0, clock.elapsedTicks);
        for (int i = 0; i < 50; i++) clock.advance("Rouge", false, 60);
        assertFalse(clock.advance("Bleue", false, 60)); assertEquals(0, clock.elapsedTicks);
    }
}
