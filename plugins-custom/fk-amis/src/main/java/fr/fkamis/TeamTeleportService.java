package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.BlockFace;
import org.bukkit.block.BlockSupport;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.player.PlayerTeleportEvent;
import org.bukkit.util.Vector;
import org.bukkit.util.BoundingBox;
import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Rassemblement administratif borné ; aucune reprise du timer ou du tick des mondes. */
final class TeamTeleportService {
    private final FKAmis plugin;
    private boolean pending;
    private UUID moving;
    private Location destination;
    TeamTeleportService(FKAmis plugin){this.plugin=plugin;}
    private void require(boolean condition,String message){if(!condition)throw new IllegalArgumentException(message);}
    boolean allowsMode(Player p){return p.getUniqueId().equals(moving)&&!plugin.state.running()&&!plugin.eliminated(p);}
    boolean allowsTeleport(PlayerTeleportEvent e){return allowsMode(e.getPlayer())&&e.getCause()==PlayerTeleportEvent.TeleportCause.PLUGIN
            &&destination!=null&&destination.equals(e.getTo());}
    boolean safe(String team,Location at){
        if(at==null||at.getWorld()==null||!at.getWorld().getName().equals("world")||!Double.isFinite(at.getX())||!Double.isFinite(at.getY())||!Double.isFinite(at.getZ())
                ||!Float.isFinite(at.getYaw())||!Float.isFinite(at.getPitch())||at.getY()<at.getWorld().getMinHeight()+1||at.getY()>at.getWorld().getMaxHeight()-2
                ||!at.getWorld().getWorldBorder().isInside(at)||!at.getWorld().isChunkLoaded(at.getBlockX()>>4,at.getBlockZ()>>4))return false;
        var nativeTeam=plugin.teams().getTeam(team);
        if(nativeTeam==null||nativeTeam.getBase()==null||!nativeTeam.getBase().contains(at))return false;
        var feet=at.getBlock();var head=feet.getRelative(BlockFace.UP);var floor=feet.getRelative(BlockFace.DOWN);
        Set<Material> danger=EnumSet.of(Material.LAVA,Material.FIRE,Material.SOUL_FIRE,Material.CAMPFIRE,Material.SOUL_CAMPFIRE,Material.MAGMA_BLOCK,
                Material.CACTUS,Material.SWEET_BERRY_BUSH,Material.WITHER_ROSE,Material.POWDER_SNOW,Material.POINTED_DRIPSTONE);
        BoundingBox body=new BoundingBox(at.getX()-.3,at.getY()+.001,at.getZ()-.3,at.getX()+.3,at.getY()+1.8,at.getZ()+.3);
        for(int x=(int)Math.floor(body.getMinX());x<=(int)Math.floor(body.getMaxX());x++)for(int z=(int)Math.floor(body.getMinZ());z<=(int)Math.floor(body.getMaxZ());z++){
            if(!at.getWorld().isChunkLoaded(x>>4,z>>4)||!at.getWorld().getWorldBorder().isInside(new Location(at.getWorld(),x+.5,at.getY(),z+.5)))return false;
            for(int y=(int)Math.floor(body.getMinY());y<=(int)Math.floor(body.getMaxY());y++){
                var block=at.getWorld().getBlockAt(x,y,z);
                if(block.isLiquid()||danger.contains(block.getType())||!block.isPassable()&&block.getBoundingBox().overlaps(body))return false;
            }
        }
        return feet.isPassable()&&!feet.isLiquid()&&head.isPassable()&&!head.isLiquid()
                &&floor.getBlockData().isFaceSturdy(BlockFace.UP,BlockSupport.FULL)
                &&!danger.contains(feet.getType())&&!danger.contains(head.getType())&&!danger.contains(floor.getType());
    }
    private boolean eligible(Player p){return p.isOnline()&&!p.isDead()&&p.getGameMode()!=GameMode.SPECTATOR&&!plugin.eliminated(p);}
    private CompletableFuture<Chunk> loadPinned(Location at){
        return at.getWorld().getChunkAtAsync(at.getBlockX()>>4,at.getBlockZ()>>4,false).thenCompose(chunk->{
            CompletableFuture<Chunk> ready=new CompletableFuture<>();
            Runnable retain=()->{try{if(chunk!=null)plugin.chunkLeases.retain(chunk,"teleport");ready.complete(chunk);}catch(Throwable ex){ready.completeExceptionally(ex);}};
            if(Bukkit.isPrimaryThread())retain.run();else if(plugin.isEnabled())Bukkit.getScheduler().runTask(plugin,retain);else ready.completeExceptionally(new IllegalStateException("Plugin arrêté."));
            return ready;
        });
    }
    void command(CommandSender sender,String[] args){
        require(args.length==2||args.length==3&&args[2].equalsIgnoreCase("confirm"),"Usage : teams tpall [confirm]");
        require(args[1].equalsIgnoreCase("tpall"),"Usage : teams tpall [confirm]");
        begin(sender,args.length==3,new ArrayList<>(Bukkit.getOnlinePlayers()));
    }
    // Collection injectée exclusivement par la recette API, sans faux compte connecté.
    void begin(CommandSender sender,boolean confirm,Collection<? extends Player> online){
        require(sender.hasPermission("fkamis.admin"),"Permission fkamis.admin requise.");
        require(!pending,"Un rassemblement est déjà en préparation.");
        require(!plugin.state.started||confirm,"Partie commencée : confirmer avec /fka teams tpall confirm pendant la pause.");
        require(GameplayRules.mayGather(plugin.state.started,plugin.state.paused,!plugin.state.winner.isEmpty(),confirm),"Rassemblement autorisé avant partie ou en pause administrative, jamais pendant un combat ni après victoire.");
        List<Player> players=online.stream().filter(this::eligible).map(p->(Player)p).toList();
        if(players.isEmpty()){sender.sendMessage("§eAucun participant connecté à téléporter.");return;}
        Map<String,Location> targets=new LinkedHashMap<>();
        for(Player p:players){
            String team=plugin.roster.get(p.getUniqueId());Location at=plugin.spawns.get(team);
            require(at!=null&&at.getWorld()!=null,"Point d'apparition absent : "+team);
            require(at.getWorld().getName().equals("world")&&Double.isFinite(at.getX())&&Double.isFinite(at.getY())&&Double.isFinite(at.getZ())
                    &&at.getWorld().getWorldBorder().isInside(at),"Point d'apparition hors monde ou bordure : "+team);
            targets.put(team,at.clone());
        }
        boolean started=plugin.state.started;int day=plugin.state.day;
        pending=true;sender.sendMessage("§eVérification des chunks et apparitions de "+players.size()+" participant(s)…");
        plugin.getLogger().info("teams tpall demandé par "+sender.getName()+" ; candidats="+players.size()+" ; partie commencée="+started);
        List<CompletableFuture<Chunk>> loads=new ArrayList<>();
        Set<String> requested=new HashSet<>();
        try{for(Location at:targets.values()){
            for(int x=((int)Math.floor(at.getX()-.3))>>4;x<=((int)Math.floor(at.getX()+.3))>>4;x++)
                for(int z=((int)Math.floor(at.getZ()-.3))>>4;z<=((int)Math.floor(at.getZ()+.3))>>4;z++)
                    if(requested.add(at.getWorld().getUID()+":"+x+":"+z))loads.add(loadPinned(new Location(at.getWorld(),x*16+8,at.getY(),z*16+8)));
        }}
        catch(RuntimeException ex){pending=false;plugin.chunkLeases.release("teleport");throw ex;}
        CompletableFuture.allOf(loads.toArray(CompletableFuture[]::new)).whenComplete((ignored,error)->{
            if(!plugin.isEnabled())return;
            Bukkit.getScheduler().runTask(plugin,()->{
                try{
                    require(error==null&&loads.stream().allMatch(f->f.getNow(null)!=null),"Chunk existant indisponible ; aucun rassemblement effectué.");
                    require(!plugin.state.running()&&plugin.state.started==started&&plugin.state.day==day&&plugin.state.winner.isEmpty(),"État de partie modifié pendant la préparation ; rassemblement annulé.");
                    for(var target:targets.entrySet())require(target.getValue().equals(plugin.spawns.get(target.getKey()))&&safe(target.getKey(),target.getValue()),"Apparition dangereuse ou modifiée : "+target.getKey()+" ; aucun rassemblement effectué.");
                    int done=0,skipped=0,refused=0;
                    plugin.resetCaptures();
                    for(Player p:players){
                        if(!eligible(p)||!targets.containsKey(plugin.roster.get(p.getUniqueId()))){skipped++;continue;}
                        if(transfer(p,targets.get(plugin.roster.get(p.getUniqueId()))))done++;else refused++;
                    }
                    String result="Rassemblement : "+done+" téléporté(s), "+skipped+" ignoré(s), "+refused+" refusé(s).";
                    sender.sendMessage("§a"+result);plugin.getLogger().info("teams tpall par "+sender.getName()+" : "+result);
                }catch(IllegalArgumentException ex){sender.sendMessage("§c"+ex.getMessage());plugin.getLogger().warning("teams tpall annulé : "+ex.getMessage());}
                finally{pending=false;moving=null;destination=null;plugin.chunkLeases.release("teleport");}
            });
        });
    }
    private boolean transfer(Player p,Location target){
        GameMode previous=p.getGameMode();boolean flight=p.getAllowFlight(),flying=p.isFlying();
        moving=p.getUniqueId();destination=target;
        try{
            p.closeInventory();
            // FK refuse les TP survival en pause. Exemption synchrone par joueur : aucun tick libre,
            // aucun dégel global, aucun changement d'équipe ou d'inventaire ; le mode est restauré.
            if(plugin.state.started)p.setGameMode(GameMode.SPECTATOR);
            boolean success=p.teleport(target,PlayerTeleportEvent.TeleportCause.PLUGIN);
            if(success){p.setFallDistance(0);p.setVelocity(new Vector());}
            return success;
        }finally{
            p.setGameMode(previous);p.setAllowFlight(flight);if(flight)p.setFlying(flying);
            moving=null;destination=null;
        }
    }
}
