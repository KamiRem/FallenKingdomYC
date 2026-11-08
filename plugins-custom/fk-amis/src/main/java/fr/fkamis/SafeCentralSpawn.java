package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.*;
import java.util.*;

/** Cherche un carré debout 3x3 existant près de 0,0 ; ne place ni ne génère de blocs. */
final class SafeCentralSpawn {
    private final FKAmis plugin;
    private Location cached;
    private static final Set<Material> DANGER=EnumSet.of(Material.LAVA,Material.WATER,Material.FIRE,Material.SOUL_FIRE,
            Material.CAMPFIRE,Material.SOUL_CAMPFIRE,Material.MAGMA_BLOCK,Material.CACTUS,Material.SWEET_BERRY_BUSH,
            Material.WITHER_ROSE,Material.POWDER_SNOW,Material.POINTED_DRIPSTONE);
    SafeCentralSpawn(FKAmis plugin) { this.plugin=plugin; }
    boolean safe(Location at) {
        World world=at.getWorld();
        if (at.getY() <= world.getMinHeight() || at.getY() > world.getMaxHeight()-2) return false;
        for(int dx=-1;dx<=1;dx++) for(int dz=-1;dz<=1;dz++) {
            Location cell=at.clone().add(dx,0,dz);
            if(!world.isChunkLoaded(cell.getBlockX()>>4,cell.getBlockZ()>>4) || !world.getWorldBorder().isInside(cell)
                    || plugin.territory(cell)!=null || plugin.objectiveAt(cell)
                    || plugin.supplies!=null && plugin.supplies.managed(cell)) return false;
            Block feet=cell.getBlock(),head=feet.getRelative(BlockFace.UP),floor=feet.getRelative(BlockFace.DOWN);
            if(!feet.isPassable() || !head.isPassable() || feet.isLiquid() || head.isLiquid()
                    || !floor.getBlockData().isFaceSturdy(BlockFace.UP,BlockSupport.FULL)
                    || DANGER.contains(feet.getType()) || DANGER.contains(head.getType()) || DANGER.contains(floor.getType())) return false;
        }
        return true;
    }
    Location resolve() {
        if(cached!=null && safe(cached)) return cached.clone();
        World world=Objects.requireNonNull(Bukkit.getWorld("world"));
        // Rayon borné, colonnes classées par distance, uniquement dans les chunks existants.
        List<int[]> columns=new ArrayList<>();
        for(int x=-16;x<=16;x++) for(int z=-16;z<=16;z++) columns.add(new int[]{x,z});
        columns.sort(java.util.Comparator.comparingInt(c->c[0]*c[0]+c[1]*c[1]));
        Set<Long> checked=new HashSet<>();
        for(int[] column:columns) {
            int x=column[0],z=column[1]; boolean loaded=true;
            for(int cx=(x-1)>>4;cx<=(x+1)>>4;cx++) for(int cz=(z-1)>>4;cz<=(z+1)>>4;cz++) {
                long key=((long)cx<<32)^(cz&0xffffffffL);
                if(checked.add(key) && world.isChunkGenerated(cx,cz)) world.getChunkAt(cx,cz,false).addPluginChunkTicket(plugin);
                if(!world.isChunkLoaded(cx,cz)) loaded=false;
            }
            if(!loaded) continue;
            int y=world.getHighestBlockYAt(x,z,HeightMap.MOTION_BLOCKING_NO_LEAVES)+1;
            Location at=new Location(world,x+.5,y,z+.5);
            if(safe(at)) { cached=at; plugin.getLogger().info("Réapparition centrale sûre : "+at.getBlockX()+" "+y+" "+at.getBlockZ()+" ; inspection humaine requise."); return at.clone(); }
        }
        throw new IllegalStateException("Aucun espace sûr 3x3 dans les 16 blocs autour de 0,0 ; faire sécuriser le centre par l'arbitre sur une copie, sans régénérer le monde.");
    }
}
