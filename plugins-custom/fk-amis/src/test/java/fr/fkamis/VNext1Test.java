package fr.fkamis;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class VNext1Test {
    @Test void southFacingPlayerSeesEastOnTheLeft(){assertEquals("←",BaseGuidance.arrow(10,0,0));assertEquals("→",BaseGuidance.arrow(-10,0,0));}
    @Test void facingNorthSeesOwnBaseAhead(){assertEquals("↑",BaseGuidance.arrow(0,-10,180));assertEquals("↓",BaseGuidance.arrow(0,10,180));}
    @Test void yawWrapDoesNotReverseTheMarker(){assertEquals("↑",BaseGuidance.arrow(-10,0,90));assertEquals("↑",BaseGuidance.arrow(-10,0,-270));assertEquals("↑",BaseGuidance.arrow(-10,0,450));}
    @Test void distanceDoesNotChangeDirection(){assertEquals(BaseGuidance.arrow(3,7,38),BaseGuidance.arrow(30,70,38));}
    @Test void diagonalDirectionUsesPlayerOrientation(){assertEquals("↖",BaseGuidance.arrow(10,10,0));assertEquals("↗",BaseGuidance.arrow(-10,10,0));}
}
