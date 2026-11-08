package fr.fkamis;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.hanging.*;
import org.bukkit.event.inventory.InventoryMoveItemEvent;
import org.bukkit.event.player.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Petites emprises indexées par chunk ; aucun parcours global du monde pendant les événements. */
final class ProtectedPlaces implements Listener {
    record Box(String id,String world,int minX,int minY,int minZ,int maxX,int maxY,int maxZ) {
        boolean contains(int x,int y,int z){return x>=minX&&x<=maxX&&y>=minY&&y<=maxY&&z>=minZ&&z<=maxZ;}
    }
    private final FKAmis plugin;private final List<Box> boxes=new ArrayList<>();private final Map<String,List<Box>> chunks=new HashMap<>();
    private Location center;
    ProtectedPlaces(FKAmis plugin)throws Exception {
        this.plugin=plugin;
        Path metadata=Bukkit.getWorldContainer().toPath().resolve("map-v2-construction.json");
        if(!Files.isRegularFile(metadata))throw new IllegalStateException("map-v2-construction.json absent : conserver les données et restaurer les métadonnées de la carte approuvée.");
        JsonObject bounds;
        try(var input=new InputStreamReader(Objects.requireNonNull(plugin.getResource("landmark-bounds.json")),StandardCharsets.UTF_8)){bounds=JsonParser.parseReader(input).getAsJsonObject();}
        JsonArray monuments=JsonParser.parseString(Files.readString(metadata,StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("monuments");
        Set<String> seen=new HashSet<>();
        for(JsonElement element:monuments) {
            JsonObject monument=element.getAsJsonObject();String id=monument.get("id").getAsString();
            if(!bounds.has(id)||!seen.add(id))throw new IllegalStateException("Monument inconnu ou dupliqué : "+id);
            JsonArray area=bounds.getAsJsonArray(id);int x=monument.get("x").getAsInt(),y=monument.get("y").getAsInt(),z=monument.get("z").getAsInt();
            boxes.add(new Box(id,"world",x+area.get(0).getAsInt()-1,y+area.get(1).getAsInt()-1,z+area.get(2).getAsInt()-1,
                x+area.get(3).getAsInt()+1,y+area.get(4).getAsInt()+2,z+area.get(5).getAsInt()+1));
        }
        if(seen.size()!=7||!seen.equals(bounds.keySet()))throw new IllegalStateException("Les sept monuments approuvés sont requis.");
        for(var site:plugin.supplies.sites.values()) {Location at=site.location();boxes.add(new Box("supply:"+site.id(),at.getWorld().getName(),at.getBlockX()-2,at.getBlockY()-1,at.getBlockZ()-2,at.getBlockX()+2,at.getBlockY()+3,at.getBlockZ()+2));}
        updateCenter(plugin.centralSpawn.resolve());
    }
    void updateCenter(Location location) {
        if(center!=null&&FKAmis.sameBlock(center,location))return;
        center=location.clone();boxes.removeIf(b->b.id.equals("central-spawn"));
        boxes.add(new Box("central-spawn",center.getWorld().getName(),center.getBlockX()-3,center.getBlockY()-2,center.getBlockZ()-3,center.getBlockX()+3,center.getBlockY()+4,center.getBlockZ()+3));
        reindex();
    }
    private String chunk(String world,int x,int z){return world+":"+x+":"+z;}
    private void reindex(){
        chunks.clear();for(Box box:boxes){World world=Bukkit.getWorld(box.world);
            if(world==null||box.minX>box.maxX||box.minZ>box.maxZ||box.minY>box.maxY||box.minY<world.getMinHeight()||box.maxY>=world.getMaxHeight()
                ||Math.abs((long)box.minX)>29_999_000||Math.abs((long)box.maxX)>29_999_000||Math.abs((long)box.minZ)>29_999_000||Math.abs((long)box.maxZ)>29_999_000
                ||(long)box.maxX-box.minX>96||(long)box.maxZ-box.minZ>96)throw new IllegalStateException("Emprise protégée invalide : "+box.id);
            for(int x=box.minX>>4;x<=box.maxX>>4;x++)for(int z=box.minZ>>4;z<=box.maxZ>>4;z++)chunks.computeIfAbsent(chunk(box.world,x,z),key->new ArrayList<>()).add(box);
        }
    }
    boolean contains(Location at){return chunks.getOrDefault(chunk(at.getWorld().getName(),at.getBlockX()>>4,at.getBlockZ()>>4),List.of()).stream().anyMatch(b->b.contains(at.getBlockX(),at.getBlockY(),at.getBlockZ()));}
    boolean forbidden(Player player,Location at){return !plugin.isAdministrator(player)&&contains(at);}
    @EventHandler(priority=EventPriority.HIGHEST) public void place(BlockPlaceEvent e){if(forbidden(e.getPlayer(),e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void place(BlockMultiPlaceEvent e){if(e.getReplacedBlockStates().stream().anyMatch(b->forbidden(e.getPlayer(),b.getLocation())))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void destroy(BlockBreakEvent e){if(forbidden(e.getPlayer(),e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void empty(PlayerBucketEmptyEvent e){if(forbidden(e.getPlayer(),e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void fill(PlayerBucketFillEvent e){if(forbidden(e.getPlayer(),e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void flow(BlockFromToEvent e){if(contains(e.getBlock().getLocation())||contains(e.getToBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void explode(EntityExplodeEvent e){e.blockList().removeIf(b->contains(b.getLocation()));}
    @EventHandler(priority=EventPriority.HIGHEST) public void explode(BlockExplodeEvent e){e.blockList().removeIf(b->contains(b.getLocation()));}
    private boolean piston(Block piston,List<Block> blocks,BlockFace face){return contains(piston.getLocation())||blocks.stream().anyMatch(b->contains(b.getLocation())||contains(b.getRelative(face).getLocation()));}
    @EventHandler(priority=EventPriority.HIGHEST) public void piston(BlockPistonExtendEvent e){if(piston(e.getBlock(),e.getBlocks(),e.getDirection()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void piston(BlockPistonRetractEvent e){if(piston(e.getBlock(),e.getBlocks(),e.getDirection().getOppositeFace()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void fire(BlockIgniteEvent e){if(contains(e.getBlock().getLocation())&&(e.getPlayer()==null||!plugin.isAdministrator(e.getPlayer())))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void burn(BlockBurnEvent e){if(contains(e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void spread(BlockSpreadEvent e){if(contains(e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void change(EntityChangeBlockEvent e){if(contains(e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void form(EntityBlockFormEvent e){if(contains(e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void grow(org.bukkit.event.world.StructureGrowEvent e){if(e.getPlayer()==null||!plugin.isAdministrator(e.getPlayer()))e.getBlocks().removeIf(b->contains(b.getLocation()));}
    @EventHandler(priority=EventPriority.HIGHEST) public void dispense(BlockDispenseEvent e){
        Block block=e.getBlock();if(contains(block.getLocation())||block.getBlockData() instanceof org.bukkit.block.data.Directional d&&contains(block.getRelative(d.getFacing()).getLocation()))e.setCancelled(true);
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void moveInventory(InventoryMoveItemEvent e){
        Location from=e.getSource().getLocation(),to=e.getDestination().getLocation();if(from!=null&&contains(from)||to!=null&&contains(to))e.setCancelled(true);
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void hanging(HangingBreakByEntityEvent e){if(contains(e.getEntity().getLocation())&&!(e.getRemover() instanceof Player p&&plugin.isAdministrator(p)))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void hanging(HangingPlaceEvent e){if(e.getPlayer()==null?contains(e.getBlock().getLocation()):forbidden(e.getPlayer(),e.getBlock().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void stand(PlayerArmorStandManipulateEvent e){if(forbidden(e.getPlayer(),e.getRightClicked().getLocation()))e.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void technicalDamage(EntityDamageByEntityEvent e){
        if(!contains(e.getEntity().getLocation()))return;
        if(e.getEntity() instanceof ArmorStand||e.getEntity() instanceof Hanging||e.getDamager() instanceof FallingBlock) {
            UUID owner=plugin.damageAttribution.owner(e.getDamager());if(!plugin.administrators.contains(owner))e.setCancelled(true);
        }
    }
}
