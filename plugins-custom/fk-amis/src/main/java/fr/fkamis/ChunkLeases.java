package fr.fkamis;

import org.bukkit.Chunk;
import org.bukkit.World;
import java.util.*;

/** Un ticket Paper par chunk, partagé entre services sans annuler leurs besoins respectifs. */
final class ChunkLeases {
    private record Key(World world,int x,int z){}
    private final FKAmis plugin;
    private final Map<Key,Set<String>> held=new HashMap<>();
    ChunkLeases(FKAmis plugin){this.plugin=plugin;}
    void retain(Chunk chunk,String owner){
        Key key=new Key(chunk.getWorld(),chunk.getX(),chunk.getZ());
        if(!held.containsKey(key))chunk.addPluginChunkTicket(plugin);
        held.computeIfAbsent(key,k->new HashSet<>()).add(owner);
    }
    void release(String owner){
        Iterator<Map.Entry<Key,Set<String>>> entries=held.entrySet().iterator();
        while(entries.hasNext()){
            var entry=entries.next();entry.getValue().remove(owner);
            if(entry.getValue().isEmpty()){Key key=entry.getKey();key.world.removePluginChunkTicket(key.x,key.z,plugin);entries.remove();}
        }
    }
}
