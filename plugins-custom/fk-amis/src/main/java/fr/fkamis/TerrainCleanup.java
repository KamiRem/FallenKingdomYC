package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.block.data.Bisected;
import org.bukkit.block.data.type.Leaves;
import java.util.*;
import java.util.function.Predicate;

/** Nettoyage ponctuel de supports naturels, sans physique, drops ni changement de terrain. */
public final class TerrainCleanup {
    private static final List<BlockFace> FACES = List.of(BlockFace.UP, BlockFace.DOWN, BlockFace.NORTH, BlockFace.SOUTH, BlockFace.EAST, BlockFace.WEST);
    private static final Set<String> PLANTS = Set.of("SHORT_GRASS", "TALL_GRASS", "FERN", "LARGE_FERN", "DEAD_BUSH",
            "BUSH", "FIREFLY_BUSH", "SHORT_DRY_GRASS", "TALL_DRY_GRASS", "AZALEA", "FLOWERING_AZALEA",
            "PINK_PETALS", "WILDFLOWERS", "LEAF_LITTER", "MOSS_CARPET", "PALE_MOSS_CARPET", "PALE_HANGING_MOSS",
            "VINE", "CAVE_VINES", "CAVE_VINES_PLANT", "TWISTING_VINES", "TWISTING_VINES_PLANT", "WEEPING_VINES", "WEEPING_VINES_PLANT",
            "GLOW_LICHEN", "HANGING_ROOTS", "SMALL_DRIPLEAF", "BIG_DRIPLEAF", "BIG_DRIPLEAF_STEM", "SPORE_BLOSSOM",
            "BROWN_MUSHROOM", "RED_MUSHROOM", "CRIMSON_FUNGUS", "WARPED_FUNGUS", "CRIMSON_ROOTS", "WARPED_ROOTS", "NETHER_SPROUTS",
            "SUGAR_CANE", "CACTUS", "CACTUS_FLOWER", "BAMBOO", "BAMBOO_SAPLING", "SWEET_BERRY_BUSH", "SNOW", "LILY_PAD",
            "SEAGRASS", "TALL_SEAGRASS", "KELP", "KELP_PLANT", "SEA_PICKLE", "POINTED_DRIPSTONE");
    private final Map<String, Boolean> roots = new HashMap<>();
    private static String key(Block b) { return b.getWorld().getUID()+":"+b.getX()+":"+b.getY()+":"+b.getZ(); }
    private static boolean loaded(Block b) { return b.getY() >= b.getWorld().getMinHeight() && b.getY() < b.getWorld().getMaxHeight()
            && b.getWorld().isChunkLoaded(b.getX() >> 4, b.getZ() >> 4); }
    public boolean natural(Block b) {
        Material m=b.getType();
        return Tag.LEAVES.isTagged(m)||Tag.FLOWERS.isTagged(m)||Tag.SAPLINGS.isTagged(m)||Tag.CROPS.isTagged(m)||PLANTS.contains(m.name());
    }
    private boolean rootedLog(Block start) {
        String id=key(start);if(roots.containsKey(id))return roots.get(id);
        Set<Block> seen=new HashSet<>();ArrayDeque<Block> queue=new ArrayDeque<>();queue.add(start);
        boolean supported=false;
        while(!queue.isEmpty()) {
            Block b=queue.removeFirst();if(!seen.add(b))continue;
            if(seen.size()>4096){supported=true;break;} // Ambiguïté : préserver le grand arbre.
            for(BlockFace face:FACES){
                Block next=b.getRelative(face);
                if(!loaded(next)){supported=true;continue;} // Ne jamais générer un chunk pour décider.
                if(Tag.LOGS.isTagged(next.getType()))queue.add(next);
                else if(!Tag.LEAVES.isTagged(next.getType())&&next.getType().isSolid())supported=true;
            }
        }
        for(Block b:seen)roots.put(key(b),supported);
        return supported;
    }
    private boolean connectedLeaf(Block start) {
        record Step(Block block,int distance){}
        Set<Block> seen=new HashSet<>();ArrayDeque<Step> queue=new ArrayDeque<>();queue.add(new Step(start,0));
        while(!queue.isEmpty()){
            Step step=queue.removeFirst();if(!seen.add(step.block))continue;
            for(BlockFace face:FACES){
                Block next=step.block.getRelative(face);
                if(!loaded(next))return true;
                if(Tag.LOGS.isTagged(next.getType())&&rootedLog(next))return true;
                if(step.distance<5&&Tag.LEAVES.isTagged(next.getType()))queue.add(new Step(next,step.distance+1));
            }
        }
        return false;
    }
    public boolean unsupported(Block b) {
        if(!natural(b))return false;
        var data=b.getBlockData();
        if(data instanceof Leaves leaves)return !leaves.isPersistent()&&!connectedLeaf(b);
        if(data instanceof Bisected halves){
            Block other=b.getRelative(halves.getHalf()==Bisected.Half.TOP?BlockFace.DOWN:BlockFace.UP);
            if(other.getType()!=b.getType()||!(other.getBlockData()instanceof Bisected pair)||pair.getHalf()==halves.getHalf())return true;
            if(!other.getBlockData().isSupported(other))return true;
        }
        return !data.isSupported(b);
    }
    /** Retourne les matériaux supprimés ; le caller borne strictement les colonnes et protège les monuments. */
    public Map<String,Integer> cleanColumn(World world,int x,int z,int minY) {
        return cleanColumn(world,x,z,minY,b->false);
    }
    public Map<String,Integer> cleanColumn(World world,int x,int z,int minY,Predicate<Block> protectedBlock) {
        Map<String,Integer> removed=new TreeMap<>();
        int top=Math.min(world.getMaxHeight()-1,world.getHighestBlockYAt(x,z,HeightMap.WORLD_SURFACE)+2);
        for(int y=top;y>=Math.max(world.getMinHeight(),minY);y--){
            Block block=world.getBlockAt(x,y,z);
            if(!protectedBlock.test(block)&&unsupported(block)){removed.merge(block.getType().name(),1,Integer::sum);block.setType(Material.AIR,false);}
        }
        return removed;
    }
}
