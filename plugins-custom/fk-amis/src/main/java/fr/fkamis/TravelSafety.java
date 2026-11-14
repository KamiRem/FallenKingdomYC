package fr.fkamis;

import org.bukkit.*;

/** Vérifications bornées sur des chunks déjà chargés, sans génération implicite. */
final class TravelSafety {
    static boolean safe(Location at){
        World world=at.getWorld();if(world==null||!Double.isFinite(at.getX())||!Double.isFinite(at.getY())||!Double.isFinite(at.getZ())
            ||at.getY()<world.getMinHeight()+1||at.getY()+2>=world.getMaxHeight()||!world.getWorldBorder().isInside(at)
            ||!world.isChunkLoaded(at.getBlockX()>>4,at.getBlockZ()>>4))return false;
        var feet=at.getBlock();var head=feet.getRelative(0,1,0);var floor=feet.getRelative(0,-1,0);
        return feet.isPassable()&&head.isPassable()&&!feet.isLiquid()&&!head.isLiquid()&&floor.getType().isSolid()
            &&!danger(feet.getType())&&!danger(head.getType())&&!danger(floor.getType());
    }
    static boolean danger(Material type){return switch(type){case LAVA,FIRE,SOUL_FIRE,MAGMA_BLOCK,CAMPFIRE,SOUL_CAMPFIRE,CACTUS,POWDER_SNOW,SWEET_BERRY_BUSH,WITHER_ROSE,NETHER_PORTAL,END_PORTAL->true;default->false;};}
    static Location nearby(Location target){
        return nearby(target,at->true);
    }
    static Location nearby(Location target,java.util.function.Predicate<Location> accept){
        for(int radius=1;radius<=3;radius++)for(int dy:new int[]{0,1,2,-1})for(int x=-radius;x<=radius;x++)for(int z=-radius;z<=radius;z++){
            if(Math.max(Math.abs(x),Math.abs(z))!=radius)continue;
            Location at=new Location(target.getWorld(),target.getBlockX()+x+.5,target.getBlockY()+dy,target.getBlockZ()+z+.5,target.getYaw(),0);
            if(accept.test(at)&&safe(at))return at;
        }return null;
    }
}
