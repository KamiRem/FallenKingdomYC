package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.block.data.Orientable;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.event.world.*;
import org.bukkit.command.CommandSender;
import java.util.*;

/** Deux cadres officiels, aucune recherche ni création de portail Vanilla à l'arrivée. */
final class NetherPortalService implements Listener {
    record Frame(String world,int x,int y,int z,Axis axis,int width,int height,Location exit) {
        World level(){return Bukkit.getWorld(world);}
        Location at(int u,int v){return new Location(level(),x+(axis==Axis.X?u:0),y+v,z+(axis==Axis.Z?u:0));}
        boolean includes(Location at){if(!world.equals(at.getWorld().getName()))return false;int u=axis==Axis.X?at.getBlockX()-x:at.getBlockZ()-z;
            return (axis==Axis.X?at.getBlockZ()==z:at.getBlockX()==x)&&u>=0&&u<width&&at.getBlockY()>=y&&at.getBlockY()<y+height;}
        boolean loaded(){if(level()==null)return false;for(int u=-1;u<=width;u++){Location at=at(u,0);if(!level().isChunkLoaded(at.getBlockX()>>4,at.getBlockZ()>>4))return false;}return true;}
        void load(){for(int u=-1;u<=width;u++){Location at=at(u,0);if(!level().isChunkGenerated(at.getBlockX()>>4,at.getBlockZ()>>4))throw new IllegalArgumentException("Chunk de portail absent ; aucune génération automatique.");level().getChunkAt(at.getBlockX()>>4,at.getBlockZ()>>4,false);}}
        boolean intact(boolean requirePortal){
            if(!loaded())return false;
            for(int u=-1;u<=width;u++)for(int v=-1;v<=height;v++){
                Material type=at(u,v).getBlock().getType();boolean edge=u==-1||u==width||v==-1||v==height;
                if(edge&&type!=Material.OBSIDIAN||!edge&&(requirePortal?type!=Material.NETHER_PORTAL:!type.isAir()&&type!=Material.NETHER_PORTAL))return false;
            }return true;
        }
        void render(boolean open){if(!loaded())return;for(int u=0;u<width;u++)for(int v=0;v<height;v++){
            Block block=at(u,v).getBlock();if(open){Orientable data=(Orientable)Material.NETHER_PORTAL.createBlockData();data.setAxis(axis);if(!data.equals(block.getBlockData()))block.setBlockData(data,false);}
            else if(block.getType()==Material.NETHER_PORTAL)block.setType(Material.AIR,false);
        }}
    }
    private final FKAmis plugin;final Map<String,Frame> frames=new HashMap<>();private final Map<UUID,Long> cooldown=new HashMap<>();private final Map<UUID,UUID> pending=new HashMap<>();
    private boolean activated;private UUID permit;private Location permittedDestination;
    NetherPortalService(FKAmis plugin,ConfigurationSection saved){
        this.plugin=plugin;if(saved!=null){if(saved.getInt("version",1)!=1)throw new IllegalArgumentException("Version future des portails.");activated=saved.getBoolean("activated");
            for(String side:List.of("overworld","nether")){var section=saved.getConfigurationSection(side);if(section!=null){World world=Objects.requireNonNull(Bukkit.getWorld(section.getString("world")),"Dimension de portail absente.");
                var exit=section.getConfigurationSection("exit");Frame frame=new Frame(world.getName(),section.getInt("x"),section.getInt("y"),section.getInt("z"),Axis.valueOf(section.getString("axis")),section.getInt("width"),section.getInt("height"),new Location(world,exit.getDouble("x"),exit.getDouble("y"),exit.getDouble("z"),(float)exit.getDouble("yaw"),0));validate(frame,side,false);frames.put(side,frame);}}
        }updateProtection();
    }
    boolean open(){return activated&&plugin.state.running()&&plugin.state.day>=plugin.getConfig().getInt("nether-day")&&frames.size()==2;}
    private void validate(Frame frame,String side,boolean inspect){
        World world=frame.level();if(world==null||frame.axis==Axis.Y||frame.width<2||frame.width>4||frame.height<3||frame.height>5||frame.y<=world.getMinHeight()+2||frame.y+frame.height+2>=world.getMaxHeight()
            ||Math.abs((long)frame.x)>29_999_000||Math.abs((long)frame.z)>29_999_000||frame.exit==null||frame.exit.getWorld()!=world||!Double.isFinite(frame.exit.getX())||!Double.isFinite(frame.exit.getY())||!Double.isFinite(frame.exit.getZ())
            ||Math.abs(frame.exit.getX()-frame.x)>8||Math.abs(frame.exit.getZ()-frame.z)>8||Math.abs(frame.exit.getY()-frame.y)>2||frame.includes(frame.exit)||!world.getWorldBorder().isInside(frame.exit))throw new IllegalArgumentException("Cadre de portail invalide.");
        if(side.equals("overworld")&&(world.getEnvironment()!=World.Environment.NORMAL||Math.hypot(frame.x,frame.z)>64||plugin.territory(frame.at(0,0))!=null))throw new IllegalArgumentException("Le portail Overworld doit être neutre, à moins de 64 blocs du centre.");
        if(side.equals("nether")&&world.getEnvironment()!=World.Environment.NETHER)throw new IllegalArgumentException("Enregistrer le retour dans le Nether.");
        if(inspect&&(!frame.intact(false)||!TravelSafety.safe(frame.exit)))throw new IllegalArgumentException("Cadre complet et sortie sûre nécessaires, sans lave ni obstruction.");
    }
    private Frame detect(Player player,String side){
        Block target=player.getTargetBlockExact(6);if(target==null)throw new IllegalArgumentException("Viser un cadre d'obsidienne complet à six blocs maximum.");
        List<Frame> found=new ArrayList<>();
        for(Axis axis:List.of(Axis.X,Axis.Z))for(int w=2;w<=4;w++)for(int h=3;h<=5;h++)for(int u=-1;u<=w;u++)for(int v=-1;v<=h;v++){
            int x=target.getX()-(axis==Axis.X?u:0),z=target.getZ()-(axis==Axis.Z?u:0),y=target.getY()-v;
            Frame candidate=new Frame(player.getWorld().getName(),x,y,z,axis,w,h,null);if(!candidate.intact(false))continue;
            Location exit=TravelSafety.nearby(candidate.at(w/2,0),at->!candidate.includes(at));if(exit==null)continue;
            Frame frame=new Frame(candidate.world,x,y,z,axis,w,h,exit);try{validate(frame,side,true);}catch(IllegalArgumentException ignored){continue;}
            boolean collision=false;for(int i=-1;i<=w;i++)for(int j=-1;j<=h;j++)if(plugin.protectedPlaces.containsExceptPortals(frame.at(i,j)))collision=true;
            if(!collision)found.add(frame);
        }
        return found.stream().min(Comparator.comparingDouble(f->f.at(0,0).distanceSquared(player.getLocation()))).orElseThrow(()->new IllegalArgumentException("Aucun cadre sûr, neutre et distinct des volumes protégés trouvé."));
    }
    void command(CommandSender sender,String[] args){
        if(!plugin.mayAdmin(sender))throw new IllegalArgumentException("Portail réservé à l'arbitre UUID et à la console.");
        if(args.length<3||!args[1].equals("portal"))throw new IllegalArgumentException("nether portal register overworld|nether / activate / deactivate / status");
        switch(args[2]){
            case "status"->sender.sendMessage("Portail officiel : "+frames.keySet()+", activation administrative "+activated+", voyage actuellement "+(open()?"ouvert":"fermé/suspendu")+". Aucune sortie Vanilla générée.");
            case "register"->{if(args.length!=4||!Set.of("overworld","nether").contains(args[3])||!(sender instanceof Player player)||activated)throw new IllegalArgumentException("Arbitre en jeu : nether portal register overworld|nether, après désactivation.");Frame frame=detect(player,args[3]);frames.put(args[3],frame);updateProtection();save(sender,"register "+args[3]);}
            case "activate"->{if(!plugin.state.running()||plugin.state.day<plugin.getConfig().getInt("nether-day")||frames.size()!=2)throw new IllegalArgumentException("Deux cadres officiels enregistrés et phase Nether active, hors pause, requis.");frames.forEach((side,frame)->{frame.load();validate(frame,side,true);});activated=true;if(!plugin.saveState()){activated=false;throw new IllegalArgumentException("Écriture refusée ; portail non activé.");}sync();audit(sender,"activate");}
            case "deactivate"->{activated=false;frames.values().forEach(f->f.render(false));save(sender,"deactivate");}
            default->throw new IllegalArgumentException("nether portal register|activate|deactivate|status");
        }
    }
    private void save(CommandSender sender,String action){if(!plugin.saveState())throw new IllegalArgumentException("État non sauvegardé ; arrêt de sécurité.");audit(sender,action);sender.sendMessage("§aPortail officiel enregistré ; consulter nether portal status.");}
    private void audit(CommandSender sender,String action){plugin.administrators.audit(sender instanceof Player p?p.getUniqueId():new UUID(0,0),"PORTAIL "+action);}
    private void updateProtection(){if(plugin.protectedPlaces==null)return;List<ProtectedPlaces.Box> areas=new ArrayList<>();frames.forEach((side,f)->areas.add(new ProtectedPlaces.Box("nether-portal:"+side,f.world,f.x-2,f.y-2,f.z-2,f.x+(f.axis==Axis.X?f.width:0)+2,f.y+f.height+2,f.z+(f.axis==Axis.Z?f.width:0)+2)));plugin.protectedPlaces.portals(areas);}
    void sync(){boolean open=open();for(Frame frame:frames.values()){if(open)frame.load();if(frame.loaded()){if(open&&!frame.intact(false)){activated=false;plugin.saveState();}frame.render(open&&activated);}}}
    void tick(){if(!open())return;for(Frame frame:frames.values())if(frame.loaded()&&(!frame.intact(true)||!TravelSafety.safe(frame.exit))){activated=false;frames.values().forEach(f->f.render(false));plugin.saveState();plugin.getLogger().warning("Portail officiel endommagé ou sortie obstruée : voyages désactivés, intervention arbitre requise.");break;}}
    boolean permits(PlayerTeleportEvent event){return event.getPlayer().getUniqueId().equals(permit)&&permittedDestination!=null&&event.getTo()!=null&&event.getTo().getWorld().equals(permittedDestination.getWorld())&&event.getTo().distanceSquared(permittedDestination)<.01;}
    private void travel(Player player){
        if(!open()||(!plugin.activeParticipant(player)&&!plugin.isAdministrator(player))||player.getGameMode()==GameMode.SPECTATOR||pending.containsKey(player.getUniqueId())||cooldown.getOrDefault(player.getUniqueId(),0L)>System.nanoTime())return;
        String origin=player.getWorld().getEnvironment()==World.Environment.NETHER?"nether":"overworld";Frame source=frames.get(origin),target=frames.get(origin.equals("nether")?"overworld":"nether");
        if(source==null||target==null||!source.includes(player.getLocation())||!source.intact(true)||!player.getPassengers().isEmpty())return;
        UUID ticket=UUID.randomUUID();pending.put(player.getUniqueId(),ticket);
        Set<Long> chunks=new HashSet<>();for(int u=-1;u<=target.width;u++){Location at=target.at(u,0);chunks.add(((long)(at.getBlockX()>>4)<<32)^((at.getBlockZ()>>4)&0xffffffffL));}chunks.add(((long)(target.exit.getBlockX()>>4)<<32)^((target.exit.getBlockZ()>>4)&0xffffffffL));
        var loads=chunks.stream().map(key->target.level().getChunkAtAsync((int)(key>>32),(int)(long)key,false)).toList();
        java.util.concurrent.CompletableFuture.allOf(loads.toArray(java.util.concurrent.CompletableFuture[]::new)).whenComplete((unused,error)->Bukkit.getScheduler().runTask(plugin,()->{
            if(!pending.remove(player.getUniqueId(),ticket))return;
            if(error!=null||loads.stream().anyMatch(f->f.getNow(null)==null)||!player.isOnline()||Bukkit.getPlayer(player.getUniqueId())!=player||!open()||!source.includes(player.getLocation())||!source.intact(true)||!target.intact(true)||!TravelSafety.safe(target.exit))return;
            if(player.isInsideVehicle())player.leaveVehicle();permit=player.getUniqueId();permittedDestination=target.exit;
            try{if(player.teleport(target.exit,PlayerTeleportEvent.TeleportCause.NETHER_PORTAL))cooldown.put(player.getUniqueId(),System.nanoTime()+3_000_000_000L);}finally{permit=null;permittedDestination=null;}
        }));
    }
    @EventHandler(priority=EventPriority.LOWEST) public void portal(PlayerPortalEvent event){if(event.getCause()!=PlayerTeleportEvent.TeleportCause.NETHER_PORTAL)return;event.setCanCreatePortal(false);event.setSearchRadius(0);event.setCreationRadius(0);boolean earlier=event.isCancelled();event.setCancelled(true);if(!earlier)travel(event.getPlayer());}
    @EventHandler(priority=EventPriority.HIGHEST) public void teleport(PlayerTeleportEvent event){
        if(event.getTo()==null)return;boolean crosses=event.getFrom().getWorld()!=event.getTo().getWorld()&&(event.getFrom().getWorld().getEnvironment()==World.Environment.NETHER||event.getTo().getWorld().getEnvironment()==World.Environment.NETHER);
        boolean observing=plugin.spectators!=null&&(plugin.spectators.permits(event)||event.getCause()==PlayerTeleportEvent.TeleportCause.SPECTATE&&plugin.spectators.eligible(event.getPlayer()));
        if(!permits(event)&&(event.getCause()==PlayerTeleportEvent.TeleportCause.NETHER_PORTAL||crosses&&!plugin.isAdministrator(event.getPlayer())&&!plugin.returningToSafety&&!observing))event.setCancelled(true);
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void create(PortalCreateEvent event){if(event.getReason()!=PortalCreateEvent.CreateReason.END_PLATFORM)event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void entity(EntityPortalEvent event){if(event.getFrom().getWorld().getEnvironment()==World.Environment.NETHER||event.getTo()!=null&&event.getTo().getWorld().getEnvironment()==World.Environment.NETHER)event.setCancelled(true);}
    @EventHandler(priority=EventPriority.HIGHEST) public void ready(io.papermc.paper.event.entity.EntityPortalReadyEvent event){if(event.getPortalType()==PortalType.NETHER&&!(event.getEntity() instanceof Player))event.setCancelled(true);}
    @EventHandler public void loaded(ChunkLoadEvent event){for(Frame frame:frames.values())if(frame.level()==event.getWorld()&&frame.loaded()&&Math.abs((frame.x>>4)-event.getChunk().getX())<=1&&Math.abs((frame.z>>4)-event.getChunk().getZ())<=1)frame.render(open()&&frame.intact(false));}
    @EventHandler public void quit(PlayerQuitEvent event){pending.remove(event.getPlayer().getUniqueId());cooldown.remove(event.getPlayer().getUniqueId());}
    void save(ConfigurationSection section){section.set("version",1);section.set("activated",activated);frames.forEach((side,f)->{section.set(side+".world",f.world);section.set(side+".x",f.x);section.set(side+".y",f.y);section.set(side+".z",f.z);section.set(side+".axis",f.axis.name());section.set(side+".width",f.width);section.set(side+".height",f.height);section.set(side+".exit.x",f.exit.getX());section.set(side+".exit.y",f.exit.getY());section.set(side+".exit.z",f.exit.getZ());section.set(side+".exit.yaw",f.exit.getYaw());});}
    void close(){pending.clear();cooldown.clear();}
}
