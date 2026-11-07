package fr.fkamis;

/** Règles de phase pures ; une source absente signifie PvE/environnement, jamais « joueur présumé ». */
final class GameplayRules {
    record Side(String team,boolean active,boolean inBase){}
    static boolean mayDamage(boolean running,int day,int pvpDay,int assaultDay,Side attacker,Side defender,boolean self){
        if(!running||!defender.active)return false;
        if(attacker==null||self)return true;
        return attacker.active&&attacker.team!=null&&!attacker.team.equals(defender.team)&&day>=pvpDay
                &&(day>=assaultDay||!attacker.inBase&&!defender.inBase);
    }
    static boolean mayMineEnemy(boolean started,boolean hasOwner,boolean own,boolean objective){
        return !objective&&(!started||!hasOwner||own);
    }
    static boolean mayGather(boolean started,boolean paused,boolean finished,boolean confirmed){
        return !finished&&(!started||paused&&confirmed);
    }
}
