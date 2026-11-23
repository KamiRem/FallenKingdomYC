package fr.fkamis;

import java.util.*;

/** Mémoire transitoire de position, sans modification des droits ni de la partie. */
final class TerritoryTransitions {
    record Change(String left,String entered) { boolean empty(){return left==null&&entered==null;} }
    private final Map<UUID,String> positions=new HashMap<>();
    static boolean eligible(boolean administrator,boolean eliminated,boolean spectator){return administrator||!eliminated&&!spectator;}
    Change accept(UUID id,String from,String to,boolean eligible,boolean nativeAlreadySent){
        String previous=positions.containsKey(id)?positions.get(id):from;
        positions.put(id,to);
        if(!eligible||nativeAlreadySent||Objects.equals(previous,to))return new Change(null,null);
        return new Change(previous,to);
    }
    void forget(UUID id){positions.remove(id);}
    void clear(){positions.clear();}
}
