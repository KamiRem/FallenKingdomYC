package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.Block;
import java.util.*;

/** Composante de cellules debout adjacentes au coffre, sans rayon de regard. */
final class CaptureGeometry {
    private record Cell(int x,int z) {}
    private static final int[][] STEPS={{1,0},{-1,0},{0,1},{0,-1}};
    private final FKAmis plugin;
    CaptureGeometry(FKAmis plugin) { this.plugin=plugin; }
    private boolean open(Location cell) {
        Block feet=cell.getBlock(),head=feet.getRelative(0,1,0),floor=feet.getRelative(0,-1,0);
        return feet.isPassable() && head.isPassable() && !feet.isLiquid() && !head.isLiquid()
                && floor.getType().isSolid() && floor.getType()!=Material.MAGMA_BLOCK
                && floor.getType()!=Material.CAMPFIRE && floor.getType()!=Material.SOUL_CAMPFIRE
                && feet.getType()!=Material.FIRE && feet.getType()!=Material.SOUL_FIRE && feet.getType()!=Material.POWDER_SNOW;
    }
    Set<String> reachable(Location objective,double radius) {
        Location center=objective.clone().add(.5,1,.5);
        Set<Cell> cells=new HashSet<>(); ArrayDeque<Cell> todo=new ArrayDeque<>();
        for(int[] step:STEPS) todo.add(new Cell(objective.getBlockX()+step[0],objective.getBlockZ()+step[1]));
        while(!todo.isEmpty()) {
            Cell cell=todo.remove();
            if(cells.contains(cell)) continue;
            Location feet=new Location(objective.getWorld(),cell.x+.5,objective.getBlockY(),cell.z+.5);
            if(feet.distanceSquared(center)>radius*radius || !Objects.equals(plugin.territory(feet),plugin.territory(objective)) || !open(feet)) continue;
            cells.add(cell);
            for(int[] step:STEPS) todo.add(new Cell(cell.x+step[0],cell.z+step[1]));
        }
        Set<String> result=new HashSet<>();
        for(Cell cell:cells) result.add(cell.x+":"+cell.z);
        return result;
    }
    boolean inside(Location objective,Location feet,double radius,Set<String> reachable) {
        return feet.getWorld().equals(objective.getWorld())
                && Math.abs(feet.getY()-objective.getBlockY())<=.6
                && feet.distanceSquared(objective.clone().add(.5,1,.5))<=radius*radius
                && reachable.contains(feet.getBlockX()+":"+feet.getBlockZ());
    }
}
