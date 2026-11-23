package fr.fkamis;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

final class BaseGuidanceTest {
    @Test void allEightDirectionsAndWrappedPlayerRotations(){
        String[] arrows={"↑","↗","→","↘","↓","↙","←","↖"};
        for(float yaw:new float[]{0,37,90,180,-270,450})for(int sector=0;sector<8;sector++){
            double angle=Math.toRadians(yaw+45*sector);
            assertEquals(arrows[sector],BaseGuidance.arrow(-10*Math.sin(angle),10*Math.cos(angle),yaw));
        }
    }
    @Test void sectorBoundaryChangesOnlyAfterHalfSector(){
        assertEquals("↑",BaseGuidance.arrow(0,10,22.49f));
        assertEquals("↖",BaseGuidance.arrow(0,10,22.51f));
    }
}
