package fr.fkamis;

import com.destroystokyo.paper.event.player.PlayerStartSpectatingEntityEvent;
import net.kyori.adventure.text.Component;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.*;
import java.util.*;

/** Sélections UUID revérifiées au clic ; aucun retour à SURVIVAL ni modification d'inventaire. */
final class SpectatorService implements Listener {
    private final FKAmis plugin;private final Set<UUID> viewers=new HashSet<>();
    private UUID moving;private Location destination;
    private static final class Menu implements InventoryHolder {
        final UUID viewer;final List<UUID> targets;Inventory inventory;
        Menu(UUID viewer,List<UUID> targets){this.viewer=viewer;this.targets=targets;}
        public Inventory getInventory(){return inventory;}
    }
    SpectatorService(FKAmis plugin){this.plugin=plugin;}
    boolean permits(PlayerTeleportEvent event){return event.getPlayer().getUniqueId().equals(moving)&&destination!=null&&event.getTo()!=null&&destination.getWorld().equals(event.getTo().getWorld())&&destination.distanceSquared(event.getTo())<.01;}
    boolean owns(Player player,Inventory inventory){return inventory.getHolder() instanceof Menu menu&&menu.viewer.equals(player.getUniqueId())&&eligible(player)&&plugin.state.started&&plugin.state.winner.isEmpty()&&(!plugin.state.paused||plugin.isAdministrator(player));}
    boolean eligible(Player player){return plugin.isAdministrator(player)||(plugin.eliminated(player)&&player.getGameMode()==GameMode.SPECTATOR);}
    boolean target(Player player){return player!=null&&player.isOnline()&&plugin.activeParticipant(player)&&player.getGameMode()==GameMode.SURVIVAL&&!player.isDead()
        &&(player.getWorld().getEnvironment()!=World.Environment.NETHER||plugin.state.day>=plugin.getConfig().getInt("nether-day"))
        &&(player.getWorld().getEnvironment()!=World.Environment.THE_END||plugin.state.endOpen);}
    private void check(Player player){if(!eligible(player)||!plugin.state.started||!plugin.state.winner.isEmpty()||plugin.state.paused&&!plugin.isAdministrator(player))throw new IllegalArgumentException("Observation réservée aux éliminés et arbitres, pendant une partie ouverte ; aucun déplacement de spectateur en pause.");}
    void command(Player player,String[] args){
        check(player);if(args.length==2){follow(player,Bukkit.getPlayerExact(args[1]));return;}if(args.length!=1)throw new IllegalArgumentException("spectate [pseudo]");
        List<? extends Player> targets=Bukkit.getOnlinePlayers().stream().filter(this::target).sorted(Comparator.comparing(Player::getName)).toList();
        Menu menu=new Menu(player.getUniqueId(),targets.stream().map(Player::getUniqueId).toList());menu.inventory=Bukkit.createInventory(menu,27,Component.text("Suivre un joueur actif"));
        for(int slot=0;slot<targets.size();slot++){Player current=targets.get(slot);ItemStack icon=new ItemStack(Material.ENDER_EYE);var meta=icon.getItemMeta();meta.displayName(Component.text(current.getName()+" — "+plugin.roster.get(current.getUniqueId())));icon.setItemMeta(meta);menu.inventory.setItem(slot,icon);}
        viewers.add(player.getUniqueId());player.openInventory(menu.inventory);
    }
    void follow(Player viewer,Player selected){
        check(viewer);if(!target(selected))throw new IllegalArgumentException("Cible active connectée requise.");Location destination=TravelSafety.nearby(selected.getLocation());
        if(destination==null)throw new IllegalArgumentException("Aucune position sûre chargée près de cette cible.");
        if(viewer.getGameMode()==GameMode.SPECTATOR)viewer.setSpectatorTarget(null);
        viewer.closeInventory();moving=viewer.getUniqueId();this.destination=destination;
        try{if(!viewer.teleport(destination,PlayerTeleportEvent.TeleportCause.PLUGIN))throw new IllegalArgumentException("Téléportation refusée par une protection.");}finally{moving=null;this.destination=null;}
        viewer.sendMessage(Component.text("Observation de "+selected.getName()+"."));
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void click(InventoryClickEvent event){
        if(!(event.getView().getTopInventory().getHolder() instanceof Menu menu))return;event.setCancelled(true);
        if(!(event.getWhoClicked() instanceof Player player)||!menu.viewer.equals(player.getUniqueId())||event.getRawSlot()<0||event.getRawSlot()>=menu.targets.size())return;
        try{follow(player,Bukkit.getPlayer(menu.targets.get(event.getRawSlot())));}catch(IllegalArgumentException error){player.sendMessage("§e"+error.getMessage());player.closeInventory();}
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void drag(InventoryDragEvent event){if(event.getView().getTopInventory().getHolder() instanceof Menu)event.setCancelled(true);}
    @EventHandler public void closed(InventoryCloseEvent event){if(event.getInventory().getHolder() instanceof Menu)viewers.remove(event.getPlayer().getUniqueId());}
    @EventHandler public void quit(PlayerQuitEvent event){viewers.remove(event.getPlayer().getUniqueId());}
    @EventHandler(priority=EventPriority.HIGHEST) public void nativeMenu(PlayerStartSpectatingEntityEvent event){if(!eligible(event.getPlayer())||!plugin.state.running()||!(event.getNewSpectatorTarget() instanceof Player player)||!target(player))event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void nativeTeleport(PlayerTeleportEvent event){
        if(event.getCause()!=PlayerTeleportEvent.TeleportCause.SPECTATE||plugin.isAdministrator(event.getPlayer()))return;
        if(!eligible(event.getPlayer())||!plugin.state.running()||event.getTo()==null||Bukkit.getOnlinePlayers().stream().noneMatch(p->target(p)&&p.getWorld().equals(event.getTo().getWorld())&&p.getLocation().distanceSquared(event.getTo())<4))event.setCancelled(true);
    }
    void sync(){if(!plugin.state.running())close();}
    void close(){for(UUID id:new HashSet<>(viewers)){Player player=Bukkit.getPlayer(id);if(player!=null)player.closeInventory();}viewers.clear();}
}
