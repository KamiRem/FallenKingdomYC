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

import java.util.*;

/** Protections complémentaires, sans annuler les refus des listeners FallenKingdom. */
final class Protections implements Listener {
    private final FKAmis plugin;
    Protections(FKAmis plugin) { this.plugin = plugin; }

    private boolean beforeAssaults() { return !plugin.state.assaults(plugin.assaultDay()); }
    private boolean protectedBlock(Block block) {
        return plugin.objectiveAt(block.getLocation()) || plugin.frozen()
                || (beforeAssaults() && plugin.territory(block.getLocation()) != null);
    }
    private Player source(Entity entity) {
        if (entity instanceof Player player) return player;
        if (entity instanceof Projectile projectile && projectile.getShooter() instanceof Player player) return player;
        if (entity instanceof Tameable tameable && tameable.getOwner() instanceof Player player) return player;
        if (entity instanceof TNTPrimed tnt && tnt.getSource() instanceof Player player) return player;
        if (entity instanceof AreaEffectCloud cloud && cloud.getSource() instanceof Player player) return player;
        return null;
    }
    private boolean noCombat(Player attacker, Player defender) {
        if (plugin.frozen() || plugin.eliminated(defender)) return true;
        if (attacker != null && (plugin.blocked(attacker) || Objects.equals(plugin.team(attacker), plugin.team(defender)))) return true;
        if (plugin.state.day < plugin.getConfig().getInt("pvp-day")) return true;
        // Avant les assauts les royaumes sont des refuges, même pour des tirs venant de l'extérieur.
        return beforeAssaults() && (plugin.territory(defender.getLocation()) != null
                || (attacker != null && plugin.territory(attacker.getLocation()) != null));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void blockBreak(BlockBreakEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation()) || plugin.objectiveAt(e.getBlock().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void blockPlace(BlockPlaceEvent e) {
        if (plugin.protectedAt(e.getPlayer(), e.getBlock().getLocation()) || plugin.objectiveAt(e.getBlock().getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void multiPlace(BlockMultiPlaceEvent e) {
        if (e.getReplacedBlockStates().stream().anyMatch(b -> plugin.protectedAt(e.getPlayer(), b.getLocation())
                || plugin.objectiveAt(b.getLocation()))) e.setCancelled(true);
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
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void hanging(HangingBreakByEntityEvent e) {
        Player p = source(e.getRemover());
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
        if (plugin.frozen()) e.setCancelled(true);
        if (e.getEntity() instanceof Player p && plugin.eliminated(p)) e.setCancelled(true);
        if (e.getEntity() instanceof Player p && plugin.state.day < plugin.getConfig().getInt("pvp-day")
                && Set.of(EntityDamageEvent.DamageCause.FIRE, EntityDamageEvent.DamageCause.FIRE_TICK,
                    EntityDamageEvent.DamageCause.LAVA, EntityDamageEvent.DamageCause.POISON,
                    EntityDamageEvent.DamageCause.WITHER, EntityDamageEvent.DamageCause.BLOCK_EXPLOSION,
                    EntityDamageEvent.DamageCause.ENTITY_EXPLOSION).contains(e.getCause())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void combat(EntityDamageByEntityEvent e) {
        Player attacker = source(e.getDamager());
        if (e.getEntity() instanceof Player defender) {
            // Explosions et dégâts sans auteur certain sont bloqués avant le PvP et dans les refuges.
            if ((attacker != null || e.getDamager() instanceof TNTPrimed || e.getDamager() instanceof Explosive)
                    && noCombat(attacker, defender)) e.setCancelled(true);
        } else if (plugin.frozen() || (attacker != null && plugin.protectedAt(attacker, e.getEntity().getLocation()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void potion(PotionSplashEvent e) {
        Player attacker = source(e.getEntity());
        for (LivingEntity entity : e.getAffectedEntities()) {
            if (plugin.frozen() || (entity instanceof Player p && noCombat(attacker, p))
                    || (attacker != null && plugin.protectedAt(attacker, entity.getLocation()))) e.setIntensity(entity, 0);
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void combust(EntityCombustByEntityEvent e) {
        Player attacker = source(e.getCombuster());
        if (plugin.frozen() || (e.getEntity() instanceof Player p && noCombat(attacker, p))
                || (attacker != null && plugin.protectedAt(attacker, e.getEntity().getLocation()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void cloud(AreaEffectCloudApplyEvent e) {
        Player attacker = source(e.getEntity());
        e.getAffectedEntities().removeIf(entity -> plugin.frozen() || (entity instanceof Player p && noCombat(attacker, p))
                || (attacker != null && plugin.protectedAt(attacker, entity.getLocation())));
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
            if (beforeAssaults() && (!Objects.equals(plugin.territory(piston.getLocation()), plugin.territory(b.getLocation()))
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
        if (plugin.frozen()) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void move(PlayerMoveEvent e) {
        if (plugin.state.started && plugin.frozen() && e.hasChangedPosition()) e.setTo(e.getFrom());
        if (e.hasChangedPosition() && e.getTo() != null) plugin.checkCaptureMovement(e.getPlayer(), e.getTo());
    }
    private boolean dimensionClosed(World world) {
        return (world.getEnvironment() == World.Environment.NETHER && (!plugin.state.started
                || plugin.state.day < plugin.getConfig().getInt("nether-day")))
                || (world.getEnvironment() == World.Environment.THE_END && !plugin.state.endOpen);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void teleport(PlayerTeleportEvent e) {
        if (e.getTo() != null && (dimensionClosed(e.getTo().getWorld()) || (plugin.state.started && plugin.frozen()
                && !(plugin.returningToSafety && e.getTo().getWorld().getEnvironment() == World.Environment.NORMAL)))) e.setCancelled(true);
        plugin.resetCaptures();
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void portal(PlayerPortalEvent e) {
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
        if (plugin.returningToSafety) return;
        if (plugin.state.started && !plugin.eliminated(e.getPlayer()) && e.getNewGameMode() != GameMode.SURVIVAL) e.setCancelled(true);
        if (plugin.state.started && plugin.eliminated(e.getPlayer()) && e.getNewGameMode() != GameMode.SPECTATOR) e.setCancelled(true);
    }
    @EventHandler public void death(PlayerDeathEvent e) { plugin.resetCaptures(); }
}
