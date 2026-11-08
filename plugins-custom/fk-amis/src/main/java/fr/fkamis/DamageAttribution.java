package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.projectiles.BlockProjectileSource;
import java.util.*;

/** Attribution explicite : aucune déduction à partir de la proximité d'un joueur. */
final class DamageAttribution implements Listener {
    private final FKAmis plugin;
    private final NamespacedKey ownerKey,burnKey,burnUntil,fallKey,fallUntil;
    private final Map<String,UUID> priming=new HashMap<>();
    private static final Set<Material> HAZARDS=EnumSet.of(Material.TNT,Material.LAVA,Material.FIRE,Material.SOUL_FIRE,
            Material.CAMPFIRE,Material.SOUL_CAMPFIRE,Material.MAGMA_BLOCK,Material.CACTUS,Material.SWEET_BERRY_BUSH,
            Material.WITHER_ROSE,Material.POWDER_SNOW,Material.POINTED_DRIPSTONE,Material.ANVIL,Material.CHIPPED_ANVIL,
            Material.DAMAGED_ANVIL,Material.DISPENSER,Material.RESPAWN_ANCHOR);
    DamageAttribution(FKAmis plugin){this.plugin=plugin;ownerKey=new NamespacedKey(plugin,"damage-owner");burnKey=new NamespacedKey(plugin,"burn-owner");burnUntil=new NamespacedKey(plugin,"burn-until");fallKey=new NamespacedKey(plugin,"fall-owner");fallUntil=new NamespacedKey(plugin,"fall-until");}
    private NamespacedKey blockKey(Block b){return new NamespacedKey(plugin,"hazard_"+(b.getX()&15)+"_"+b.getY()+"_"+(b.getZ()&15));}
    private String position(Block b){return b.getWorld().getUID()+":"+b.getX()+":"+b.getY()+":"+b.getZ();}
    void mark(Block b,Material type,UUID owner){b.getChunk().getPersistentDataContainer().set(blockKey(b),PersistentDataType.STRING,type.name()+":"+owner);}
    void mark(Entity entity,UUID owner){if(owner!=null)entity.getPersistentDataContainer().set(ownerKey,PersistentDataType.STRING,owner.toString());}
    UUID owner(Block b){return b==null?null:owner(b,b.getType());}
    private UUID owner(Block b,Material type){
        if(b==null)return null;
        String value=b.getChunk().getPersistentDataContainer().get(blockKey(b),PersistentDataType.STRING);
        if(value==null)return null;
        int split=value.indexOf(':');
        if(split<0||!type.name().equals(value.substring(0,split)))return null;
        try{return UUID.fromString(value.substring(split+1));}catch(IllegalArgumentException ex){return null;}
    }
    UUID owner(Entity entity){return owner(entity,0);}
    private UUID owner(Entity entity,int depth){
        if(entity==null||depth>5)return null;
        if(entity instanceof Player p)return p.getUniqueId();
        String value=entity.getPersistentDataContainer().get(ownerKey,PersistentDataType.STRING);
        if(value!=null)try{return UUID.fromString(value);}catch(IllegalArgumentException ignored){}
        if(entity instanceof Projectile p){
            if(p.getShooter()instanceof Entity shooter)return owner(shooter,depth+1);
            if(p.getShooter()instanceof BlockProjectileSource block)return owner(block.getBlock());
        }
        if(entity instanceof Tameable tame&&tame.getOwner()!=null)return tame.getOwner().getUniqueId();
        if(entity instanceof TNTPrimed tnt)return owner(tnt.getSource(),depth+1);
        if(entity instanceof AreaEffectCloud cloud&&cloud.getSource()instanceof Entity source)return owner(source,depth+1);
        return null;
    }
    UUID damageOwner(EntityDamageEvent e){
        // Le tireur réel est prioritaire pour un projectile, jamais le joueur victime
        // ni une source indirecte sans rapport. Conserve les marqueurs de distributeur.
        Entity direct=e instanceof EntityDamageByEntityEvent by?by.getDamager():e.getDamageSource().getDirectEntity();
        if(direct instanceof Projectile projectile && projectile.getShooter() instanceof Mob) return owner(projectile);
        UUID who=owner(e.getDamageSource().getCausingEntity());
        if(who==null)who=owner(e.getDamageSource().getDirectEntity());
        if(who==null&&e instanceof EntityDamageByEntityEvent by)who=owner(by.getDamager());
        if(who==null&&e instanceof EntityDamageByBlockEvent by){
            who=by.getDamagerBlockState()==null?owner(by.getDamager()):owner(by.getDamagerBlockState().getBlock(),by.getDamagerBlockState().getType());
        }
        if(who==null&&e.getEntity()instanceof Player p){
            Block eye=p.getEyeLocation().getBlock();
            if(e.getCause()==EntityDamageEvent.DamageCause.DROWNING&&eye.getType()==Material.WATER
                    ||e.getCause()==EntityDamageEvent.DamageCause.SUFFOCATION&&eye.getType().isSolid())who=owner(eye);
            if(e.getCause()==EntityDamageEvent.DamageCause.FREEZE&&p.getLocation().getBlock().getType()==Material.POWDER_SNOW)who=owner(p.getLocation().getBlock());
            if(e.getCause()==EntityDamageEvent.DamageCause.FALL){
                Long until=p.getPersistentDataContainer().get(fallUntil,PersistentDataType.LONG);
                String value=p.getPersistentDataContainer().get(fallKey,PersistentDataType.STRING);
                if(until!=null&&until>=p.getWorld().getGameTime()&&value!=null)who=UUID.fromString(value);
            }
        }
        if(who==null&&e.getCause()==EntityDamageEvent.DamageCause.FIRE_TICK){
            var pdc=e.getEntity().getPersistentDataContainer();
            Long until=pdc.get(burnUntil,PersistentDataType.LONG);String value=pdc.get(burnKey,PersistentDataType.STRING);
            if(until!=null&&until>=e.getEntity().getWorld().getGameTime()&&value!=null)who=UUID.fromString(value);
        }
        return who;
    }
    private void burn(Entity entity,UUID owner,float duration){
        var pdc=entity.getPersistentDataContainer();
        if(owner==null){pdc.remove(burnKey);pdc.remove(burnUntil);return;}
        pdc.set(burnKey,PersistentDataType.STRING,owner.toString());
        pdc.set(burnUntil,PersistentDataType.LONG,entity.getWorld().getGameTime()+(long)(duration*20)+40);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void place(BlockPlaceEvent e){
        e.getBlock().getChunk().getPersistentDataContainer().remove(blockKey(e.getBlock()));
        if(HAZARDS.contains(e.getBlock().getType())||e.getBlock().getType().isSolid())mark(e.getBlock(),e.getBlock().getType(),e.getPlayer().getUniqueId());
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void breakBlock(BlockBreakEvent e){
        e.getBlock().getChunk().getPersistentDataContainer().remove(blockKey(e.getBlock()));
        for(Player victim:Bukkit.getOnlinePlayers())if(victim.getLocation().clone().subtract(0,.05,0).getBlock().equals(e.getBlock())){
            victim.getPersistentDataContainer().set(fallKey,PersistentDataType.STRING,e.getPlayer().getUniqueId().toString());
            victim.getPersistentDataContainer().set(fallUntil,PersistentDataType.LONG,victim.getWorld().getGameTime()+200);
        }
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void bucket(PlayerBucketEmptyEvent e){
        Material content=switch(e.getBucket()){case LAVA_BUCKET->Material.LAVA;case WATER_BUCKET->Material.WATER;case POWDER_SNOW_BUCKET->Material.POWDER_SNOW;default->null;};
        if(content!=null)mark(e.getBlock(),content,e.getPlayer().getUniqueId());
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void fill(PlayerBucketFillEvent e){e.getBlock().getChunk().getPersistentDataContainer().remove(blockKey(e.getBlock()));}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void flow(BlockFromToEvent e){
        UUID owner=owner(e.getBlock());if(owner!=null&&(e.getBlock().getType()==Material.LAVA||e.getBlock().getType()==Material.WATER))mark(e.getToBlock(),e.getBlock().getType(),owner);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void ignite(BlockIgniteEvent e){
        UUID owner=e.getPlayer()!=null?e.getPlayer().getUniqueId():owner(e.getIgnitingEntity());
        if(owner==null)owner=owner(e.getIgnitingBlock());
        if(owner!=null)mark(e.getBlock(),e.getBlock().getType()==Material.CAMPFIRE||e.getBlock().getType()==Material.SOUL_CAMPFIRE?e.getBlock().getType():Material.FIRE,owner);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void spread(BlockSpreadEvent e){
        UUID owner=owner(e.getSource());if(owner!=null)mark(e.getBlock(),e.getNewState().getType(),owner);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void entityPlace(EntityPlaceEvent e){if(e.getPlayer()!=null)mark(e.getEntity(),e.getPlayer().getUniqueId());}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void use(PlayerInteractEvent e){
        Block block=e.getClickedBlock();
        if(e.getAction()==Action.RIGHT_CLICK_BLOCK&&block!=null&&(block.getType()==Material.RESPAWN_ANCHOR||Tag.BEDS.isTagged(block.getType()))){
            mark(block,block.getType(),e.getPlayer().getUniqueId());
            if(block.getBlockData()instanceof org.bukkit.block.data.type.Bed bed){
                Block other=block.getRelative(bed.getPart()==org.bukkit.block.data.type.Bed.Part.FOOT?bed.getFacing():bed.getFacing().getOppositeFace());
                mark(other,other.getType(),e.getPlayer().getUniqueId());
            }
        }
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void use(PlayerInteractEntityEvent e){
        if(e.getRightClicked()instanceof Creeper&&(e.getPlayer().getInventory().getItem(e.getHand()).getType()==Material.FLINT_AND_STEEL
                ||e.getPlayer().getInventory().getItem(e.getHand()).getType()==Material.FIRE_CHARGE))mark(e.getRightClicked(),e.getPlayer().getUniqueId());
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void crystal(EntityDamageByEntityEvent e){
        if(e.getEntity()instanceof EnderCrystal)mark(e.getEntity(),owner(e.getDamager()));
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void prime(TNTPrimeEvent e){
        UUID who=owner(e.getPrimingEntity());if(who==null)who=owner(e.getPrimingBlock());if(who==null)who=owner(e.getBlock());
        if(who!=null){String position=position(e.getBlock());priming.put(position,who);Bukkit.getScheduler().runTask(plugin,()->priming.remove(position));}
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void spawn(EntitySpawnEvent e){
        if(e.getEntity()instanceof TNTPrimed||e.getEntity()instanceof FallingBlock){
            Location origin=e.getEntity().getOrigin();Block block=(origin==null?e.getLocation():origin).getBlock();
            UUID who=priming.remove(position(block));if(who==null)who=owner(block);mark(e.getEntity(),who);
        }
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void burn(EntityCombustByEntityEvent e){burn(e.getEntity(),owner(e.getCombuster()),e.getDuration());}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void burn(EntityCombustByBlockEvent e){burn(e.getEntity(),owner(e.getCombuster()),e.getDuration());}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void falling(EntityChangeBlockEvent e){
        if(e.getEntity()instanceof FallingBlock){
            UUID who=owner(e.getEntity());
            if(who!=null&&!e.getTo().isAir())mark(e.getBlock(),e.getTo(),who);else mark(e.getEntity(),owner(e.getBlock()));
        }
    }
    private void moved(List<Block> blocks,BlockFace direction){
        record Move(Block source,Material material,UUID owner){}
        List<Move> moves=blocks.stream().map(b->new Move(b,b.getType(),owner(b))).toList();
        for(Move move:moves)move.source.getChunk().getPersistentDataContainer().remove(blockKey(move.source));
        for(Move move:moves){Block target=move.source.getRelative(direction);target.getChunk().getPersistentDataContainer().remove(blockKey(target));if(move.owner!=null)mark(target,move.material,move.owner);}
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void piston(BlockPistonExtendEvent e){moved(e.getBlocks(),e.getDirection());}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void piston(BlockPistonRetractEvent e){moved(e.getBlocks(),e.getDirection().getOppositeFace());}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void explosion(EntityExplodeEvent e){for(Block b:e.blockList())b.getChunk().getPersistentDataContainer().remove(blockKey(b));}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void explosion(BlockExplodeEvent e){for(Block b:e.blockList())b.getChunk().getPersistentDataContainer().remove(blockKey(b));}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void burned(BlockBurnEvent e){e.getBlock().getChunk().getPersistentDataContainer().remove(blockKey(e.getBlock()));}
    @EventHandler(priority=EventPriority.MONITOR) public void landed(EntityDamageEvent e){
        if(e.getCause()==EntityDamageEvent.DamageCause.FALL){e.getEntity().getPersistentDataContainer().remove(fallKey);e.getEntity().getPersistentDataContainer().remove(fallUntil);}
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void grounded(PlayerMoveEvent e){
        Player p=e.getPlayer();if(p.getPersistentDataContainer().has(fallKey)&&p.getLocation().clone().subtract(0,.05,0).getBlock().getType().isSolid()){
            p.getPersistentDataContainer().remove(fallKey);p.getPersistentDataContainer().remove(fallUntil);
        }
    }
}
