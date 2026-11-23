package fr.fkamis;

import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fallenkingdom.display.notification.RegionChange;
import fr.devsylone.fkpi.teams.Team;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import java.util.*;

/** Repli du canal natif de territoire, après les protections et sans doublonner le natif. */
final class TerritoryNotifications implements Listener {
    private final FKAmis plugin;
    private final TerritoryTransitions transitions=new TerritoryTransitions();
    private final Map<PlayerMoveEvent,RegionChange> nativeBefore=new IdentityHashMap<>();
    TerritoryNotifications(FKAmis plugin){this.plugin=plugin;}
    private RegionChange last(Player p){return Fk.getInstance().getPlayerManager().getPlayer(p).getLastRegionChange();}
    private String territory(Location at){Team team=at==null?null:plugin.territory(at);return team==null?null:team.getName();}
    @EventHandler(priority=EventPriority.LOWEST) public void beforeMove(PlayerMoveEvent e){nativeBefore.put(e,last(e.getPlayer()));}
    @EventHandler(priority=EventPriority.LOWEST) public void beforeTeleport(PlayerTeleportEvent e){nativeBefore.put(e,last(e.getPlayer()));}
    private void accepted(PlayerMoveEvent e){
        RegionChange before=nativeBefore.remove(e);
        if(e.isCancelled()||e.getTo()==null)return;
        Player p=e.getPlayer();boolean sent=last(p)!=before;
        boolean eligible=TerritoryTransitions.eligible(plugin.isAdministrator(p),plugin.eliminated(p),p.getGameMode()==GameMode.SPECTATOR);
        var change=transitions.accept(p.getUniqueId(),territory(e.getFrom()),territory(e.getTo()),eligible,sent);
        if(change.left()!=null)send(p,change.left(),RegionChange.MoveType.LEAVE);
        if(change.entered()!=null)send(p,change.entered(),RegionChange.MoveType.ENTER);
    }
    private void send(Player p,String name,RegionChange.MoveType type){
        Team team=plugin.teams().getTeam(name);
        if(team==null||team.getBase()==null)return;
        // Le même canal chat, les traductions et couleurs du JAR officiel inchangé.
        Fk.getInstance().getDisplayService().dispatch(new RegionChange(team.getBase(),type),p);
    }
    @EventHandler(priority=EventPriority.MONITOR) public void moved(PlayerMoveEvent e){accepted(e);}
    @EventHandler(priority=EventPriority.MONITOR) public void teleported(PlayerTeleportEvent e){accepted(e);}
    @EventHandler(priority=EventPriority.MONITOR) public void joined(PlayerJoinEvent e){
        transitions.forget(e.getPlayer().getUniqueId());
        refresh(e.getPlayer());
    }
    @EventHandler(priority=EventPriority.MONITOR) public void changedWorld(PlayerChangedWorldEvent e){refresh(e.getPlayer());}
    private void refresh(Player player){
        Bukkit.getScheduler().runTask(plugin,()->{
            Player p=player;if(!p.isOnline())return;
            boolean eligible=TerritoryTransitions.eligible(plugin.isAdministrator(p),plugin.eliminated(p),p.getGameMode()==GameMode.SPECTATOR);
            var change=transitions.accept(p.getUniqueId(),null,territory(p.getLocation()),eligible,false);
            if(change.left()!=null)send(p,change.left(),RegionChange.MoveType.LEAVE);
            if(change.entered()!=null)send(p,change.entered(),RegionChange.MoveType.ENTER);
        });
    }
    @EventHandler public void quit(PlayerQuitEvent e){transitions.forget(e.getPlayer().getUniqueId());nativeBefore.keySet().removeIf(event->event.getPlayer().equals(e.getPlayer()));}
    void close(){nativeBefore.clear();transitions.clear();}
}
