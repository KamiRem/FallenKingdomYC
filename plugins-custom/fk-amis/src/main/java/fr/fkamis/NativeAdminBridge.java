package fr.fkamis;

import fr.devsylone.fallenkingdom.Fk;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.hanging.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.*;
import org.bukkit.plugin.RegisteredListener;
import java.util.*;

/** Délègue les mêmes handlers natifs, sauf exemptions ciblées ; n'annule aucun refus tiers. */
final class NativeAdminBridge {
    private final FKAmis plugin;
    private record Entry(HandlerList list,RegisteredListener original,RegisteredListener wrapper) {}
    private final List<Entry> entries=new ArrayList<>();
    NativeAdminBridge(FKAmis plugin) {
        this.plugin=plugin;
        for (HandlerList list:HandlerList.getHandlerLists()) for (RegisteredListener nativeHandler:list.getRegisteredListeners()) {
            if (nativeHandler.getPlugin()!=Fk.getInstance()) continue;
            String name=nativeHandler.getListener().getClass().getSimpleName();
            if (!Set.of("BlockListener","BucketListener","LockedChestInteractListener","MoveListener","UsePortalListener",
                    "GoToNetherListener","PauseInteractionListener","InventoryListener","FoodListener","DisabledPotionsListener",
                    "PvpListener","DamageListener","RespawnListener","ChangeGamemodeListener").contains(name)) continue;
            RegisteredListener wrapper=new RegisteredListener(nativeHandler.getListener(),(listener,event)->{
                // FKAmis choisit la destination et le mode ; aucun ancien TP natif différé.
                if (name.equals("RespawnListener")&&event instanceof PlayerRespawnEvent) return;
                Player actor=actor(event);
                if (actor!=null&&plugin.isAdministrator(actor)) return;
                // Seul le refus natif de blocs ordinaires hors base est remplacé.
                // La TNT conserve ses garde-fous natifs ; les autres plugins restent autorités.
                if(name.equals("BlockListener") && event instanceof BlockPlaceEvent place
                        && place.getBlock().getType()!=org.bukkit.Material.TNT
                        && plugin.territory(place.getBlock().getLocation())==null
                        && plugin.state.running() && !plugin.blocked(place.getPlayer())
                        && (!(place instanceof BlockMultiPlaceEvent multi) || multi.getReplacedBlockStates().stream().allMatch(b->plugin.territory(b.getLocation())==null))) return;
                if(plugin.diagnostics!=null&&event instanceof EntityDamageEvent damage)plugin.diagnostics.damage(damage,"BEFORE_NATIVE_"+name);
                nativeHandler.callEvent(event);
                if(plugin.diagnostics!=null&&event instanceof EntityDamageEvent damage)plugin.diagnostics.damage(damage,"AFTER_NATIVE_"+name);
            },nativeHandler.getPriority(),plugin,nativeHandler.isIgnoringCancelled());
            list.unregister(nativeHandler); list.register(wrapper); entries.add(new Entry(list,nativeHandler,wrapper));
        }
    }
    private Player actor(Event e) {
        if (e instanceof PlayerEvent p) return p.getPlayer();
        if (e instanceof BlockBreakEvent b) return b.getPlayer();
        if (e instanceof BlockPlaceEvent b) return b.getPlayer();
        if (e instanceof InventoryInteractEvent i && i.getWhoClicked() instanceof Player p) return p;
        if (e instanceof InventoryOpenEvent i && i.getPlayer() instanceof Player p) return p;
        if (e instanceof EntityDamageByEntityEvent d) {
            if (d.getDamager() instanceof Player p) return p;
            if (d.getEntity() instanceof Player p) return p;
        }
        if (e instanceof EntityEvent v && v.getEntity() instanceof Player p) return p;
        if (e instanceof HangingPlaceEvent h) return h.getPlayer();
        if (e instanceof HangingBreakByEntityEvent h && h.getRemover() instanceof Player p) return p;
        return null;
    }
    void close() { for (Entry e:entries) { e.list.unregister(e.wrapper); e.list.register(e.original); } entries.clear(); }
    int size() { return entries.size(); }
}
