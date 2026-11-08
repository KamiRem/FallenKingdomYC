package fr.fkamis;

import org.bukkit.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.CreatureSpawnEvent;
import org.bukkit.event.entity.EntityTransformEvent;
import org.bukkit.event.player.PlayerJoinEvent;
import org.bukkit.event.player.PlayerChangedWorldEvent;
import org.bukkit.event.world.*;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.util.Vector;

/** Suspend les mobs existants sans perte d'UUID, équipement, gardiens ou montures. */
final class LobbyMobs implements Listener {
    private final FKAmis plugin;
    private final NamespacedKey saved;
    LobbyMobs(FKAmis plugin) { this.plugin=plugin; saved=new NamespacedKey(plugin,"lobby-mob-flags-v1"); }
    void synchronize() { for(World world:Bukkit.getWorlds()) { rules(world); for(LivingEntity entity:world.getLivingEntities()) update(entity); } }
    private void rules(World world) {
        world.setGameRule(GameRules.LOCATOR_BAR,false);
        world.setGameRule(GameRules.SPAWN_MOBS,plugin.state.started);
        world.setDifficulty(Difficulty.NORMAL);
    }
    void update(Entity entity) {
        if(!(entity instanceof Mob mob)) return; // Armor stands, displays, joueurs : jamais modifiés.
        String flags=mob.getPersistentDataContainer().get(saved,PersistentDataType.STRING);
        if(!plugin.state.started) {
            if(flags==null) {
                flags=(mob.hasAI()?"1":"0")+(mob.hasGravity()?"1":"0")+(mob.isInvulnerable()?"1":"0")
                        +(mob.isSilent()?"1":"0")+(mob.isCollidable()?"1":"0")+(mob.getRemoveWhenFarAway()?"1":"0")+(mob.isPersistent()?"1":"0");
                mob.getPersistentDataContainer().set(saved,PersistentDataType.STRING,flags);
            }
            mob.setAI(false); mob.setGravity(false); mob.setInvulnerable(true); mob.setSilent(true); mob.setCollidable(false); mob.setVelocity(new Vector());
            mob.setRemoveWhenFarAway(false);mob.setPersistent(true);
            for(Player player:mob.getWorld().getPlayers()) player.hideEntity(plugin,mob);
        } else if(flags!=null) {
            if(!flags.matches("[01]{7}")) throw new IllegalStateException("Drapeaux de suspension de mob invalides ; conserver le monde et examiner la sauvegarde.");
            mob.setAI(flags.charAt(0)=='1'); mob.setGravity(flags.charAt(1)=='1'); mob.setInvulnerable(flags.charAt(2)=='1');
            mob.setSilent(flags.charAt(3)=='1'); mob.setCollidable(flags.charAt(4)=='1');
            mob.setRemoveWhenFarAway(flags.charAt(5)=='1');mob.setPersistent(flags.charAt(6)=='1');
            mob.getPersistentDataContainer().remove(saved);
            for(Player player:mob.getWorld().getPlayers()) player.showEntity(plugin,mob);
        }
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void spawn(CreatureSpawnEvent event) {
        if(!plugin.state.started && event.getEntity() instanceof Mob) event.setCancelled(true);
    }
    @EventHandler public void entities(EntitiesLoadEvent event) { for(Entity entity:event.getEntities()) update(entity); }
    @EventHandler public void world(WorldLoadEvent event) { rules(event.getWorld()); }
    @EventHandler public void join(PlayerJoinEvent event) {
        hide(event.getPlayer());
    }
    private void hide(Player player) { if(!plugin.state.started) for(Entity entity:player.getWorld().getEntities()) if(entity instanceof Mob) player.hideEntity(plugin,entity); }
    @EventHandler public void changed(PlayerChangedWorldEvent event) { hide(event.getPlayer()); }
    @EventHandler(priority=EventPriority.HIGHEST) public void transform(EntityTransformEvent event) { if(!plugin.state.started)event.setCancelled(true); }
}
