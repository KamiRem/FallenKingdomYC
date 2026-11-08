package fr.fkamis;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.*;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.PlayerRespawnEvent;
import java.util.*;

/** Échéances absolues persistées : connexion, monde et téléportation ne les prolongent pas. */
final class RespawnProtection implements Listener {
    private final FKAmis plugin;final Map<UUID,Long> expires=new HashMap<>();
    RespawnProtection(FKAmis plugin,ConfigurationSection saved){this.plugin=plugin;if(saved!=null)for(String key:saved.getKeys(false))expires.put(UUID.fromString(key),saved.getLong(key));}
    boolean active(UUID id){if(id==null)return false;Long end=expires.get(id);long now=System.currentTimeMillis();if(end==null)return false;if(end<=now||end-now>30_000){expires.remove(id);return false;}return true;}
    @EventHandler(priority=EventPriority.MONITOR) public void respawn(PlayerRespawnEvent event){
        if(event.getRespawnReason()!=PlayerRespawnEvent.RespawnReason.DEATH||!plugin.activeParticipant(event.getPlayer())||!plugin.state.started)return;
        int seconds=plugin.getConfig().getInt("respawn-protection-seconds",5);if(seconds<=0)return;
        expires.put(event.getPlayer().getUniqueId(),System.currentTimeMillis()+seconds*1000L);plugin.saveState();
    }
    void tick(){
        for(Player player:Bukkit.getOnlinePlayers())if(plugin.activeParticipant(player)&&active(player.getUniqueId()))
            player.sendActionBar(Component.text("Protection PvP : "+((expires.get(player.getUniqueId())-System.currentTimeMillis()+999)/1000)+" s",NamedTextColor.AQUA));
        expires.entrySet().removeIf(e->e.getValue()<=System.currentTimeMillis());
    }
    void save(ConfigurationSection section){expires.forEach((id,end)->section.set(id.toString(),end));}
}
