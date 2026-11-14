package fr.fkamis;

import org.bukkit.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.event.vehicle.VehicleEnterEvent;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;
import java.util.*;

/** Ancrage à la transition et aux événements, aucune téléportation périodique. */
final class PauseControl implements Listener {
    private final FKAmis plugin;private final NamespacedKey gravity;private final Map<UUID,Location> anchors=new HashMap<>();
    PauseControl(FKAmis plugin){this.plugin=plugin;gravity=new NamespacedKey(plugin,"pause-original-gravity");}
    boolean frozen(Player player){return plugin.state.started&&!plugin.state.running()&&!plugin.isAdministrator(player);}
    private void restore(Player player){var data=player.getPersistentDataContainer();Byte value=data.get(gravity,PersistentDataType.BYTE);if(value!=null){player.setGravity(value==1);player.setVelocity(new Vector());player.setFallDistance(0);data.remove(gravity);}anchors.remove(player.getUniqueId());}
    private void arm(Player player,Location at){
        anchors.put(player.getUniqueId(),at.clone());var data=player.getPersistentDataContainer();
        if(!data.has(gravity,PersistentDataType.BYTE))data.set(gravity,PersistentDataType.BYTE,(byte)(player.hasGravity()?1:0));
        if(player.isInsideVehicle())player.leaveVehicle();player.setGravity(false);player.setVelocity(new Vector());player.setFallDistance(0);
        if(player.getGameMode()==GameMode.SPECTATOR&&player.getSpectatorTarget()!=null)player.setSpectatorTarget(null);
        player.setSwimming(false);player.setGliding(false);
    }
    void sync(){for(Player player:Bukkit.getOnlinePlayers())if(frozen(player)){if(!anchors.containsKey(player.getUniqueId()))arm(player,player.getLocation());}else restore(player);}
    @EventHandler(priority=EventPriority.HIGHEST) public void move(PlayerMoveEvent event){
        Player player=event.getPlayer();if(!frozen(player)||!event.hasChangedPosition())return;
        Location anchor=anchors.computeIfAbsent(player.getUniqueId(),id->event.getFrom().clone()).clone();
        if(event.getTo()!=null){anchor.setYaw(event.getTo().getYaw());anchor.setPitch(event.getTo().getPitch());}event.setTo(anchor);
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void teleport(PlayerTeleportEvent event){
        if(frozen(event.getPlayer())&&!plugin.teamTeleports.allowsTeleport(event)&&!plugin.returningToSafety)event.setCancelled(true);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void teleported(PlayerTeleportEvent event){if(frozen(event.getPlayer())&&event.getTo()!=null)arm(event.getPlayer(),event.getTo());}
    @EventHandler(priority=EventPriority.HIGHEST) public void velocity(PlayerVelocityEvent event){if(frozen(event.getPlayer()))event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void mount(EntityMountEvent event){if(event.getEntity() instanceof Player player&&frozen(player))event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void vehicle(VehicleEnterEvent event){if(event.getEntered() instanceof Player player&&frozen(player))event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void launch(ProjectileLaunchEvent event){if(event.getEntity().getShooter() instanceof Player player&&frozen(player))event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void bow(EntityShootBowEvent event){if(event.getEntity() instanceof Player player&&frozen(player))event.setCancelled(true);}
    @EventHandler(priority=EventPriority.MONITOR) public void respawn(PlayerRespawnEvent event){if(frozen(event.getPlayer())){anchors.put(event.getPlayer().getUniqueId(),event.getRespawnLocation().clone());Bukkit.getScheduler().runTask(plugin,()->{if(event.getPlayer().isOnline()&&frozen(event.getPlayer()))arm(event.getPlayer(),event.getRespawnLocation());});}}
    @EventHandler(priority=EventPriority.MONITOR) public void joined(PlayerJoinEvent event){if(frozen(event.getPlayer()))arm(event.getPlayer(),event.getPlayer().getLocation());else restore(event.getPlayer());}
    @EventHandler public void quit(PlayerQuitEvent event){restore(event.getPlayer());}
    void close(){for(Player player:Bukkit.getOnlinePlayers())restore(player);anchors.clear();}
}
