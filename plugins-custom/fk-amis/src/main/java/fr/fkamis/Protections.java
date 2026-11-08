package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.hanging.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.Inventory;
import org.bukkit.potion.PotionEffectTypeCategory;

import java.util.*;

/** Protections complémentaires ; l'arbitre explicite conserve les gardes des objectifs/sites. */
final class Protections implements Listener {
    private final FKAmis plugin;
    Protections(FKAmis plugin) { this.plugin = plugin; }

    private boolean beforeAssaults() { return !plugin.state.assaults(plugin.assaultDay()); }
    private boolean protectedBlock(Block block) {
        return plugin.objectiveAt(block.getLocation()) || plugin.frozen()
                || (beforeAssaults() && plugin.territory(block.getLocation()) != null);
    }
    private UUID source(Entity entity) { return plugin.damageAttribution.owner(entity); }
    private boolean noCombat(UUID attacker, Player defender) {
        if (plugin.isAdministrator(defender) || plugin.administrators.contains(attacker)) return true;
        if(attacker!=null&&!attacker.equals(defender.getUniqueId())&&plugin.respawnProtection!=null
                &&(plugin.respawnProtection.active(attacker)||plugin.respawnProtection.active(defender.getUniqueId())))return true;
        Player online=attacker==null?null:Bukkit.getPlayer(attacker);
        String team=attacker==null?null:plugin.roster.get(attacker);
        GameplayRules.Side source=attacker==null?null:new GameplayRules.Side(team,team!=null&&!plugin.state.eliminated.contains(team)
                &&(online==null||!plugin.blocked(online)),online!=null&&plugin.territory(online.getLocation())!=null);
        var victim=new GameplayRules.Side(plugin.roster.get(defender.getUniqueId()),plugin.activeParticipant(defender),plugin.territory(defender.getLocation())!=null);
        return !GameplayRules.mayDamage(plugin.state.running(),plugin.state.day,plugin.getConfig().getInt("pvp-day"),plugin.assaultDay(),source,victim,defender.getUniqueId().equals(attacker));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void blockBreak(BlockBreakEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) {
            if (plugin.objectiveAt(e.getBlock().getLocation())&&!plugin.administrators.sensitive(e.getPlayer(),e.getBlock().getLocation())) e.setCancelled(true);
            return;
        }
        var owner=plugin.territory(e.getBlock().getLocation());
        if (plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation()) || !GameplayRules.mayMineEnemy(plugin.state.started,owner!=null,
                owner!=null&&owner.equals(plugin.team(e.getPlayer())),plugin.objectiveAt(e.getBlock().getLocation()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void blockPlace(BlockPlaceEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) {
            if (plugin.objectiveAt(e.getBlock().getLocation())&&!plugin.administrators.sensitive(e.getPlayer(),e.getBlock().getLocation())) e.setCancelled(true);
            return;
        }
        if (plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation()) || plugin.objectiveAt(e.getBlock().getLocation())
                || !plugin.mayPlace(e.getPlayer(),e.getBlock())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void multiPlace(BlockMultiPlaceEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) {
            if (e.getReplacedBlockStates().stream().anyMatch(b->plugin.objectiveAt(b.getLocation())&&!plugin.administrators.sensitive(e.getPlayer(),b.getLocation()))) e.setCancelled(true);
            return;
        }
        if (e.getReplacedBlockStates().stream().anyMatch(b -> plugin.protectedAt(e.getPlayer(), b.getLocation())
                || plugin.objectiveAt(b.getLocation()) || !plugin.mayPlace(e.getPlayer(),b.getBlock()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void bucket(PlayerBucketEmptyEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void bucket(PlayerBucketFillEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void interact(PlayerInteractEvent e) {
        if (plugin.blocked(e.getPlayer()) || (e.getClickedBlock() != null
                && plugin.protectedAt(e.getPlayer(), e.getClickedBlock().getLocation()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void entityInteract(PlayerInteractEntityEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getRightClicked().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void entityInteractAt(PlayerInteractAtEntityEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getRightClicked().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void armorStand(PlayerArmorStandManipulateEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getRightClicked().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void shear(PlayerShearEntityEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getEntity().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void fishing(PlayerFishEvent e) {
        if (plugin.blocked(e.getPlayer()) || (e.getCaught() != null && plugin.protectedAt(e.getPlayer(), e.getCaught().getLocation()))) e.setCancelled(true);
        if(e.getCaught() instanceof Player p&&noCombat(e.getPlayer().getUniqueId(),p))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void hanging(HangingBreakByEntityEvent e) {
        UUID id=source(e.getRemover());Player p=id==null?null:Bukkit.getPlayer(id);
        if (p!=null&&plugin.isAdministrator(p)) return;
        if (protectedBlock(e.getEntity().getLocation().getBlock()) || (p != null && plugin.protectedAt(p, e.getEntity().getLocation()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void hanging(HangingPlaceEvent e) {
        if (e.getPlayer() != null && plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void open(InventoryOpenEvent e) {
        if (e.getPlayer() instanceof Player p && (plugin.blocked(p)
                || inventoryLocations(e.getInventory()).stream().anyMatch(at -> plugin.protectedAt(p, at)))) e.setCancelled(true);
    }
    private List<Location> inventoryLocations(Inventory inventory) {
        List<Location> positions = new ArrayList<>();
        if (inventory.getLocation() != null) positions.add(inventory.getLocation());
        if (inventory.getHolder() instanceof org.bukkit.block.DoubleChest doubleChest) {
            if (doubleChest.getLeftSide() instanceof org.bukkit.block.Chest c) positions.add(c.getLocation());
            if (doubleChest.getRightSide() instanceof org.bukkit.block.Chest c) positions.add(c.getLocation());
        }
        return positions;
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void click(InventoryClickEvent e) {
        if (e.getWhoClicked() instanceof Player p && (plugin.blocked(p)
                || inventoryLocations(e.getView().getTopInventory()).stream().anyMatch(at -> plugin.protectedAt(p, at)))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void drag(InventoryDragEvent e) {
        if (e.getWhoClicked() instanceof Player p && (plugin.blocked(p)
                || inventoryLocations(e.getView().getTopInventory()).stream().anyMatch(at -> plugin.protectedAt(p, at)))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void drop(PlayerDropItemEvent e) {
        if (plugin.blocked(e.getPlayer())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void pickup(EntityPickupItemEvent e) {
        if (e.getEntity() instanceof Player p && plugin.protectedAt(p, e.getItem().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void hopper(InventoryPickupItemEvent e) {
        if (plugin.frozen() || (beforeAssaults() && plugin.territory(e.getItem().getLocation()) != null)) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void transfer(InventoryMoveItemEvent e) {
        if (plugin.frozen()) { e.setCancelled(true); return; }
        if (beforeAssaults()) {
            List<Location> source = inventoryLocations(e.getSource()), destination = inventoryLocations(e.getDestination());
            if (source.isEmpty() || destination.isEmpty()) { e.setCancelled(true); return; }
            for (Location a : source) for (Location b : destination)
                if (!Objects.equals(plugin.territory(a), plugin.territory(b))) e.setCancelled(true);
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void damage(EntityDamageEvent e) {
        if(plugin.diagnostics!=null)plugin.diagnostics.damage(e,"BEFORE_FKAMIS_PROTECTIONS");
        try {
        if (e.getEntity() instanceof Player arbiter && plugin.isAdministrator(arbiter)) { e.setCancelled(true); return; }
        UUID owner=plugin.damageAttribution.damageOwner(e);
        if (!(e.getEntity() instanceof Player)&&plugin.administrators.contains(owner)) return;
        if (plugin.frozen()) e.setCancelled(true);
        if (e.getEntity() instanceof Player p && plugin.eliminated(p)) e.setCancelled(true);
        if(e.getEntity() instanceof Player p&&noCombat(plugin.damageAttribution.damageOwner(e),p))e.setCancelled(true);
        } finally {if(plugin.diagnostics!=null)plugin.diagnostics.damage(e,"AFTER_FKAMIS_PROTECTIONS");}
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void combat(EntityDamageByEntityEvent e) {
        if (plugin.administrators.contains(source(e.getDamager()))) {
            if (e.getEntity() instanceof Player) e.setCancelled(true);
            return;
        }
        UUID id=source(e.getDamager());Player attacker=id==null?null:Bukkit.getPlayer(id);
        if(!(e.getEntity() instanceof Player)&&(plugin.frozen()||attacker!=null&&
                (e.getEntity() instanceof Enemy?plugin.blocked(attacker):plugin.protectedAt(attacker,e.getEntity().getLocation()))))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void potion(PotionSplashEvent e) {
        UUID attacker = source(e.getEntity());
        boolean harmful=e.getPotion().getEffects().stream().anyMatch(effect->effect.getType().getCategory()==PotionEffectTypeCategory.HARMFUL);
        for (LivingEntity entity : e.getAffectedEntities()) {
            if (plugin.frozen() || harmful&&entity instanceof Player p&&noCombat(attacker,p)) e.setIntensity(entity, 0);
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void combust(EntityCombustByEntityEvent e) {
        UUID attacker = source(e.getCombuster());
        if (plugin.frozen() || e.getEntity() instanceof Player p && noCombat(attacker, p)) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void combust(EntityCombustByBlockEvent e) {
        if(plugin.frozen()||e.getEntity() instanceof Player p&&noCombat(plugin.damageAttribution.owner(e.getCombuster()),p))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void effect(EntityPotionEffectEvent e) {
        if(e.getNewEffect()!=null&&e.getNewEffect().getType().getCategory()==PotionEffectTypeCategory.HARMFUL&&e.getEntity()instanceof Player p
                &&noCombat(source(e.getSource()),p))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void cloud(AreaEffectCloudApplyEvent e) {
        UUID attacker = source(e.getEntity());
        boolean harmful=e.getEntity().getCustomEffects().stream().anyMatch(effect->effect.getType().getCategory()==PotionEffectTypeCategory.HARMFUL)
                ||e.getEntity().getBasePotionType()!=null&&e.getEntity().getBasePotionType().getPotionEffects().stream().anyMatch(effect->effect.getType().getCategory()==PotionEffectTypeCategory.HARMFUL);
        e.getAffectedEntities().removeIf(entity -> plugin.frozen() || harmful&&entity instanceof Player p&&noCombat(attacker,p));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void explosion(EntityExplodeEvent e) {
        e.blockList().removeIf(this::protectedBlock);
        if (plugin.frozen()) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void explosion(BlockExplodeEvent e) {
        e.blockList().removeIf(this::protectedBlock);
        if (plugin.frozen()) e.setCancelled(true);
    }
    private boolean pistonForbidden(Block piston, List<Block> blocks, org.bukkit.block.BlockFace direction) {
        if (plugin.frozen()) return true;
        for (Block b : blocks) {
            Block target = b.getRelative(direction);
            if (plugin.objectiveAt(b.getLocation()) || plugin.objectiveAt(target.getLocation())) return true;
            if ((!Objects.equals(plugin.territory(piston.getLocation()), plugin.territory(b.getLocation()))
                    || !Objects.equals(plugin.territory(piston.getLocation()), plugin.territory(target.getLocation())))) return true;
        }
        return false;
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void piston(BlockPistonExtendEvent e) {
        if (pistonForbidden(e.getBlock(), e.getBlocks(), e.getDirection())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void piston(BlockPistonRetractEvent e) {
        if (pistonForbidden(e.getBlock(), e.getBlocks(), e.getDirection().getOppositeFace())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void fluid(BlockFromToEvent e) {
        if (plugin.frozen() || plugin.objectiveAt(e.getToBlock().getLocation()) ||
                (beforeAssaults() && !Objects.equals(plugin.territory(e.getBlock().getLocation()), plugin.territory(e.getToBlock().getLocation())))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void fire(BlockIgniteEvent e) {
        if (protectedBlock(e.getBlock())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void fire(BlockBurnEvent e) {
        if (protectedBlock(e.getBlock())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void spread(BlockSpreadEvent e) {
        if (plugin.frozen() || plugin.objectiveAt(e.getBlock().getLocation()) ||
                (beforeAssaults() && !Objects.equals(plugin.territory(e.getSource().getLocation()), plugin.territory(e.getBlock().getLocation())))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void change(EntityChangeBlockEvent e) {
        if (protectedBlock(e.getBlock()) || (beforeAssaults() && plugin.territory(e.getEntity().getLocation()) != null)) e.setCancelled(true);
        if(plugin.territory(e.getBlock().getLocation())!=null&&(e.getEntity()instanceof Enderman||e.getEntity()instanceof Wither))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void form(EntityBlockFormEvent e) {
        if (protectedBlock(e.getBlock())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void grow(org.bukkit.event.world.StructureGrowEvent e) {
        if (plugin.frozen()) { e.setCancelled(true); return; }
        e.getBlocks().removeIf(b -> plugin.objectiveAt(b.getLocation()) || (beforeAssaults()
                && !Objects.equals(plugin.territory(e.getLocation()), plugin.territory(b.getLocation()))));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void dispense(BlockDispenseEvent e) {
        // Sans attribution fiable : projectiles et seaux automatiques fermés avant les assauts.
        if (beforeAssaults()) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void food(FoodLevelChangeEvent e) {
        if (e.getEntity() instanceof Player p&&plugin.isAdministrator(p)) return;
        if (plugin.frozen()) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void move(PlayerMoveEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (plugin.state.started && plugin.frozen() && e.hasChangedPosition()) e.setTo(e.getFrom());
        // La présence de capture est recalculée chaque tick ; un troisième allié
        // en déplacement ailleurs ne doit jamais réinitialiser les deux attaquants.
    }
    private boolean dimensionClosed(World world) {
        return (world.getEnvironment() == World.Environment.NETHER && (!plugin.state.started
                || plugin.state.day < plugin.getConfig().getInt("nether-day")))
                || (world.getEnvironment() == World.Environment.THE_END && !plugin.state.endOpen);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void teleport(PlayerTeleportEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (e.getTo() != null && (dimensionClosed(e.getTo().getWorld()) || (plugin.state.started && plugin.frozen()
                && !plugin.teamTeleports.allowsTeleport(e)&& !(plugin.returningToSafety && e.getTo().getWorld().getEnvironment() == World.Environment.NORMAL)))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void portal(PlayerPortalEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (e.getTo() != null && (dimensionClosed(e.getTo().getWorld()) || plugin.frozen())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void portal(EntityPortalEvent e) {
        if (e.getTo() != null && (dimensionClosed(e.getTo().getWorld()) || plugin.frozen())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void bed(PlayerBedEnterEvent e) {
        // Le sommeil ne passe jamais une phase ; éviter les changements de temps du plugin principal.
        if (plugin.blocked(e.getPlayer())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void mode(PlayerGameModeChangeEvent e) {
        if (plugin.returningToSafety||plugin.teamTeleports.allowsMode(e.getPlayer())) return;
        if (e.getNewGameMode()!=plugin.desiredMode(e.getPlayer())) e.setCancelled(true);
    }
}
