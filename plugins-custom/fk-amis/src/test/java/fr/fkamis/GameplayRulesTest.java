package fr.fkamis;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class GameplayRulesTest {
    private GameplayRules.Side red(boolean base){return new GameplayRules.Side("Rouge",true,base);}
    private GameplayRules.Side blue(boolean base){return new GameplayRules.Side("Bleue",true,base);}
    @Test void naturalDangersStayActiveInEveryPhaseAndTerritory(){
        for(int day:new int[]{1,2,3})for(boolean base:new boolean[]{false,true})
            assertTrue(GameplayRules.mayDamage(true,day,2,3,null,red(base),false));
    }
    @Test void pvpStartsDayTwoOnlyOutsideProtectedBases(){
        assertFalse(GameplayRules.mayDamage(true,1,2,3,red(false),blue(false),false));
        assertTrue(GameplayRules.mayDamage(true,2,2,3,red(false),blue(false),false));
        assertFalse(GameplayRules.mayDamage(true,2,2,3,red(true),blue(false),false));
        assertFalse(GameplayRules.mayDamage(true,2,2,3,red(false),blue(true),false));
        assertTrue(GameplayRules.mayDamage(true,3,2,3,red(true),blue(true),false));
    }
    @Test void friendlyFireNeverUnlocksButSelfDamageRemains(){
        for(int day:new int[]{1,2,3}){
            assertFalse(GameplayRules.mayDamage(true,day,2,3,red(false),red(false),false));
            assertTrue(GameplayRules.mayDamage(true,day,2,3,red(false),red(false),true));
        }
    }
    @Test void pauseAndEliminationsRemainProtected(){
        assertFalse(GameplayRules.mayDamage(false,1,2,3,null,red(false),false));
        assertFalse(GameplayRules.mayDamage(true,3,2,3,null,new GameplayRules.Side("Rouge",false,false),false));
        assertFalse(GameplayRules.mayDamage(true,3,2,3,new GameplayRules.Side("Rouge",false,false),blue(false),false));
    }
    @Test void directEnemyMiningAndObjectivesStayProtectedAfterAssaults(){
        for(int day:new int[]{1,2,3}){
            assertFalse(GameplayRules.mayMineEnemy(true,true,false,false));
            assertTrue(GameplayRules.mayMineEnemy(true,true,true,false));
            assertFalse(GameplayRules.mayMineEnemy(true,true,true,true));
        }
        assertTrue(GameplayRules.mayMineEnemy(true,false,false,false));
    }
    @Test void gatheringRequiresPauseAndConfirmationAfterStart(){
        assertTrue(GameplayRules.mayGather(false,true,false,false));
        assertFalse(GameplayRules.mayGather(true,false,false,true));
        assertFalse(GameplayRules.mayGather(true,true,false,false));
        assertTrue(GameplayRules.mayGather(true,true,false,true));
        assertFalse(GameplayRules.mayGather(true,true,true,true));
    }
}
