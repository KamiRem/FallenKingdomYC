package fr.fkamis;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.*;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import org.bukkit.persistence.PersistentDataType;

/** Repli API sans entité, paquet NMS, objectif ni ticket de chunk. */
final class BaseGuidance implements Listener {
    private final FKAmis plugin;private int seconds;
    BaseGuidance(FKAmis plugin){this.plugin=plugin;}
    static String arrow(double dx,double dz,float yaw){
        double relative=Math.toDegrees(Math.atan2(-dx,dz))-yaw;
        int sector=Math.floorMod((int)Math.floor((relative+22.5)/45),8);
        return new String[]{"↑","↗","→","↘","↓","↙","←","↖"}[sector];
    }
    private void attribute(Player player,Attribute type,String name,boolean restore){
        var value=player.getAttribute(type);if(value==null)return;
        var key=new NamespacedKey(plugin,"guidance-original-"+name);var data=player.getPersistentDataContainer();
        if(restore){Double old=data.get(key,PersistentDataType.DOUBLE);if(old!=null){value.setBaseValue(old);data.remove(key);}}
        else {if(!data.has(key,PersistentDataType.DOUBLE))data.set(key,PersistentDataType.DOUBLE,value.getBaseValue());if(value.getBaseValue()!=0)value.setBaseValue(0);}
    }
    void privacy(Player player,boolean restore){attribute(player,Attribute.WAYPOINT_TRANSMIT_RANGE,"transmit",restore);attribute(player,Attribute.WAYPOINT_RECEIVE_RANGE,"receive",restore);}
    void show(Player player){
        if(!plugin.activeParticipant(player))return;
        Location base=plugin.spawns.get(plugin.roster.get(player.getUniqueId()));if(base==null)return;
        String text;
        if(!base.getWorld().equals(player.getWorld()))text="Base : "+base.getWorld().getName()+" — direction indisponible dans cette dimension";
        else {Location at=player.getLocation();double dx=base.getX()-at.getX(),dz=base.getZ()-at.getZ();text="Base "+plugin.roster.get(player.getUniqueId())+" : "+arrow(dx,dz,at.getYaw())+" "+Math.round(Math.hypot(dx,dz))+" m";}
        player.sendActionBar(Component.text(text,NamedTextColor.GOLD));
    }
    void tick(){
        for(World world:Bukkit.getWorlds())if(Boolean.TRUE.equals(world.getGameRuleValue(GameRules.LOCATOR_BAR)))world.setGameRule(GameRules.LOCATOR_BAR,false);
        if(++seconds%2!=0)return;
        for(Player player:Bukkit.getOnlinePlayers()){privacy(player,false);if(plugin.state.running()&&!plugin.respawnProtection.active(player.getUniqueId()))show(player);}
    }
    @EventHandler(priority=EventPriority.LOWEST) public void join(PlayerJoinEvent event){privacy(event.getPlayer(),false);}
    @EventHandler public void quit(PlayerQuitEvent event){privacy(event.getPlayer(),true);}
    void close(){for(Player player:Bukkit.getOnlinePlayers())privacy(player,true);}
}
