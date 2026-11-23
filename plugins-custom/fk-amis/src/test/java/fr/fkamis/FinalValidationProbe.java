package fr.fkamis;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.player.*;
import org.bukkit.event.world.PortalCreateEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Vector;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Vérification de paquets serveur, sans connexion ni rendu client. Copie privée uniquement. */
public final class FinalValidationProbe extends JavaPlugin {
    private JavaPlugin fk;private Object state,guidance,portals;private World world,nether;
    private final List<Player> actors=new ArrayList<>();private final List<String> checks=new ArrayList<>();
    private Player admin,op,red;private final List<String> teams=List.of("Rouge","Bleue","Verte","Jaune");
    private Object field(Object o,String n)throws Exception{return SyntheticPlayer.field(o,n);}
    private void set(Object o,String n,Object v)throws Exception{SyntheticPlayer.set(o,n,v);}
    private Object call(Object o,String n,Class<?>[] t,Object...a)throws Exception{Method m=o.getClass().getDeclaredMethod(n,t);m.setAccessible(true);return m.invoke(o,a);}
    private void command(org.bukkit.command.CommandSender sender,String...args){fk.onCommand(sender,fk.getCommand("fka"),"fka",args);}
    private void command(String...args){command(Bukkit.getConsoleSender(),args);}
    private void check(boolean ok,String name){if(!ok)throw new AssertionError(name);checks.add(name);getLogger().info("FINAL PROBE PASS "+name);}
    private void later(int ticks,Checked task){Bukkit.getScheduler().runTaskLater(this,()->{try{task.run();}catch(Throwable e){fail(e);}},ticks);}
    @FunctionalInterface private interface Checked{void run()throws Exception;}
    private Player actor(String name,Location at)throws Exception{Player p=SyntheticPlayer.create(name,at);actors.add(p);return p;}
    @Override public void onEnable(){
        if(!Boolean.getBoolean("fk.finalprobe")||!Bukkit.getIp().equals("127.0.0.1"))throw new IllegalStateException("Sonde locale isolée obligatoire");
        later(40,()->{fk=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");state=field(fk,"state");guidance=field(fk,"baseGuidance");portals=field(fk,"netherPortals");world=Bukkit.getWorld("world");nether=Bukkit.getWorlds().stream().filter(w->w.getEnvironment()==World.Environment.NETHER).findFirst().orElseThrow();
            if(Boolean.getBoolean("fk.finalprobe.restart"))restart();else initial();});
    }
    private void clear(Player p)throws Exception{Object conn=field(field(p.getClass().getMethod("getHandle").invoke(p),"connection"),"connection");((Collection<?>)field(conn,"pendingActions")).clear();}
    private void platform(World w,int x,int y,int z){for(int dx=-6;dx<=6;dx++)for(int dz=-6;dz<=6;dz++){w.getChunkAt((x+dx)>>4,(z+dz)>>4).addPluginChunkTicket(this);w.getBlockAt(x+dx,y-1,z+dz).setType(Material.STONE,false);for(int dy=0;dy<7;dy++)w.getBlockAt(x+dx,y+dy,z+dz).setType(Material.AIR,false);}}
    @SuppressWarnings("unchecked") private void initial()throws Exception{
        check(Bukkit.getOnlinePlayers().isEmpty()&&!(boolean)field(state,"started"),"aucun client authentifié et jour zéro");
        platform(world,160,200,160);
        for(String team:teams){Player p=actor("V22"+team,new Location(world,160.5,200,160.5));command("assign",p.getName(),team);check(((Map<?,?>)field(fk,"roster")).get(p.getUniqueId()).equals(team),"affectation par commande "+team);}
        red=actors.getFirst();admin=actor("V22Arbitre",new Location(world,160.5,200,163.5));command("admin","grant",admin.getUniqueId().toString(),"confirm");
        op=actor("V22Op",new Location(world,161.5,200,163.5));op.setOp(true);
        check(!(boolean)call(fk,"mayAdmin",new Class<?>[]{org.bukkit.command.CommandSender.class},op),"OP sans UUID arbitre ne peut pas administrer");
        command(op,"nether","portal","activate");command(red,"nether","portal","activate");check(!(boolean)field(portals,"activated"),"activation refusée à OP et participant");
        command("start");check(!(boolean)field(state,"started"),"départ refuse les terrains non inspectés");
        ((Set<String>)field(fk,"terrainValidated")).addAll(teams); // Précondition de fixture, aucune inspection humaine revendiquée.
        command("start");check((boolean)field(state,"started")&&(int)field(state,"day")==1,"commande de départ locale J1");
        guidance();portalSetup();
    }
    @SuppressWarnings("unchecked") private void guidance()throws Exception{
        Map<String,Location> spawns=(Map<String,Location>)field(fk,"spawns");String[] expected={"↑","↗","→","↘","↓","↙","←","↖"};
        for(int i=0;i<4;i++){
            Player p=actors.get(i);String team=teams.get(i);Location base=spawns.get(team);
            for(int sector=0;sector<8;sector++){
                double angle=Math.toRadians(45*sector);Location at=base.clone().add(10*Math.sin(angle),15,-10*Math.cos(angle));at.setYaw(0);p.teleport(at);
                clear(p);command(p,"base");String text=SyntheticPlayer.lastActionBar(p);
                check(text!=null&&text.contains(team)&&text.contains(expected[sector])&&text.endsWith("10 m")&&teams.stream().filter(t->!t.equals(team)).noneMatch(text::contains),"paquet ActionBar privé "+team+" secteur "+sector);
            }
            Location at=base.clone().add(0,15,-20);at.setYaw(180);p.teleport(at);clear(p);command(p,"base");check(SyntheticPlayer.lastActionBar(p).contains("↓ 20 m"),"rotation et distance actualisées "+team);
        }
        clear(admin);command(admin,"base");check(SyntheticPlayer.lastActionBar(admin)==null,"arbitre sans guidage vers une équipe");
        clear(op);command(op,"base");check(SyntheticPlayer.lastActionBar(op)==null,"OP hors effectifs sans guidage privé");
        for(Player p:actors.subList(0,4)){call(guidance,"privacy",new Class<?>[]{Player.class,boolean.class},p,false);check(p.getAttribute(org.bukkit.attribute.Attribute.WAYPOINT_TRANSMIT_RANGE).getValue()==0&&p.getAttribute(org.bukkit.attribute.Attribute.WAYPOINT_RECEIVE_RANGE).getValue()==0,"aucun waypoint natif "+p.getName());}
        Location saved=red.getLocation();((Set<String>)field(state,"eliminated")).add("Rouge");call(fk,"applyMode",new Class<?>[]{Player.class},red);clear(red);command(red,"base");check(SyntheticPlayer.lastActionBar(red)==null&&red.getGameMode()==GameMode.SPECTATOR,"éliminé sans guidage ni gain de droits");((Set<String>)field(state,"eliminated")).remove("Rouge");call(fk,"applyMode",new Class<?>[]{Player.class},red);
        command("pause");clear(red);set(guidance,"seconds",1);call(guidance,"tick",new Class<?>[]{});check(SyntheticPlayer.lastActionBar(red)==null,"guidage automatique suspendu en pause");command("resume");
        Object grace=field(fk,"respawnProtection");((Map<UUID,Long>)field(grace,"expires")).put(red.getUniqueId(),System.currentTimeMillis()+5000);clear(red);call(grace,"tick",new Class<?>[]{});set(guidance,"seconds",1);call(guidance,"tick",new Class<?>[]{});check(SyntheticPlayer.lastActionBar(red).startsWith("Protection PvP"),"protection de réapparition prioritaire sur guidage");((Map<?,?>)field(grace,"expires")).clear();
        clear(red);set(guidance,"seconds",0);call(guidance,"tick",new Class<?>[]{});check(SyntheticPlayer.lastActionBar(red)==null,"aucun envoi automatique la première seconde");call(guidance,"tick",new Class<?>[]{});check(SyntheticPlayer.lastActionBar(red)!=null,"rafraîchissement automatique toutes les deux secondes");
        check(!world.getGameRuleValue(GameRules.LOCATOR_BAR),"Locator Bar Vanilla maintenue désactivée");
        String name=red.getName();Location at=red.getLocation();red.saveData();Bukkit.getPluginManager().callEvent(new PlayerQuitEvent(red,"fixture sans réseau"));actors.remove(red);SyntheticPlayer.remove(red);red=actor(name,at);red.loadData();Bukkit.getPluginManager().callEvent(new PlayerJoinEvent(red,"fixture sans authentification"));call(fk,"applyMode",new Class<?>[]{Player.class},red);clear(red);command(red,"base");check(SyntheticPlayer.lastActionBar(red).contains("Rouge"),"guidage de la même équipe après reconnexion");
        var respawn=new PlayerRespawnEvent(red,red.getLocation(),false,false,false,PlayerRespawnEvent.RespawnReason.DEATH);Bukkit.getPluginManager().callEvent(respawn);red.teleport(respawn.getRespawnLocation());
        clear(red);command(red,"base");check(SyntheticPlayer.lastActionBar(red).contains("Rouge"),"guidage calculé depuis le lieu de réapparition");
    }
    @SuppressWarnings("unchecked") private void portalSetup()throws Exception{
        ((Map<UUID,String>)field(fk,"roster")).put(op.getUniqueId(),"Rouge");((Map<UUID,String>)field(fk,"rosterNames")).put(op.getUniqueId(),op.getName());
        fr.devsylone.fkpi.FkPI.getInstance().getTeamManager().addPlayer(op.getName(),"Rouge");call(fk,"applyMode",new Class<?>[]{Player.class},op);
        check(op.isOp()&&op.getGameMode()==GameMode.SURVIVAL&&(boolean)call(fk,"activeParticipant",new Class<?>[]{Player.class},op),"OP testé aussi comme participant actif sans rôle arbitre");
        platform(world,12,72,0);platform(nether,0,82,0);
        for(var end:List.of(new Object[]{"overworld",world,12,72,0},new Object[]{"nether",nether,0,82,0})){
            String side=(String)end[0];World w=(World)end[1];int x=(int)end[2],y=(int)end[3],z=(int)end[4];
            for(int u=-1;u<=2;u++)for(int v=-1;v<=3;v++)w.getBlockAt(x+u,y+v,z).setType(u==-1||u==2||v==-1||v==3?Material.OBSIDIAN:Material.AIR,false);
            Location view=new Location(w,x+1.5,y,z+5.5);view.setDirection(new Vector(-2,-1.12,-5));admin.teleport(view);
            int count=((Map<?,?>)field(portals,"frames")).size();command(red,"nether","portal","register",side);command(op,"nether","portal","register",side);check(((Map<?,?>)field(portals,"frames")).size()==count,"enregistrement refusé participant et OP "+side);
            command(admin,"nether","portal","register",side);check(((Map<?,?>)field(portals,"frames")).containsKey(side),"cadre visé réellement enregistré par arbitre "+side);
        }
        command(admin,"nether","portal","activate");check(!(boolean)field(portals,"activated"),"Nether fermé J1 même pour activation arbitre");
        for(Player p:List.of(red,op)){
            var bypass=new PlayerTeleportEvent(p,p.getLocation(),new Location(nether,.5,82,2.5),PlayerTeleportEvent.TeleportCause.COMMAND);Bukkit.getPluginManager().callEvent(bypass);check(bypass.isCancelled(),"téléportation Nether directe refusée "+p.getName());
        }
        command("nextday");command(admin,"nether","portal","activate");check((boolean)call(portals,"open",new Class<?>[]{}),"deux extrémités ouvertes sur activation arbitre J2");
        for(Player actor:List.of(red,op,admin))for(var reason:List.of(PortalCreateEvent.CreateReason.FIRE,PortalCreateEvent.CreateReason.NETHER_PAIR)){
            var create=new PortalCreateEvent(new ArrayList<>(),world,actor,reason);Bukkit.getPluginManager().callEvent(create);check(create.isCancelled(),"création Vanilla supplémentaire refusée "+actor.getName()+" "+reason);
        }
        red.teleport(new Location(world,28.5,72,.5));var rogue=new PlayerPortalEvent(red,red.getLocation(),nether.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(rogue);
        check(rogue.isCancelled()&&((Map<?,?>)field(portals,"pending")).isEmpty(),"portail hors cadre officiel sans traversée ni demande asynchrone");
        red.getInventory().setItem(0,new ItemStack(Material.BREAD,7));red.teleport(new Location(world,12.5,72,.5));
        var event=new PlayerPortalEvent(red,red.getLocation(),nether.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(event);
        check(event.isCancelled()&&!event.getCanCreatePortal()&&event.getSearchRadius()==0&&event.getCreationRadius()==0,"route Vanilla annulée sans recherche ni création");
        ((Set<String>)field(state,"eliminated")).add("Rouge");call(fk,"applyMode",new Class<?>[]{Player.class},red);
        later(5,()->{
            check(red.getWorld()==world&&red.getGameMode()==GameMode.SPECTATOR&&((Map<?,?>)field(portals,"pending")).isEmpty(),"élimination pendant chargement annule la traversée différée");
            ((Set<String>)field(state,"eliminated")).remove("Rouge");call(fk,"applyMode",new Class<?>[]{Player.class},red);
            var retry=new PlayerPortalEvent(red,red.getLocation(),nether.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(retry);
            later(30,()->{check(red.getWorld()==nether&&red.getInventory().getItem(0).getAmount()==7,"voyage officiel préserve inventaire");clear(red);command(red,"base");check(SyntheticPlayer.lastActionBar(red).contains("direction indisponible"),"guidage Nether sans flèche trompeuse");command("save");finish();});
        });
    }
    private void restart()throws Exception{
        check((boolean)field(state,"paused")&&(int)field(state,"day")==2,"reprise J2 toujours en pause explicite");
        check(((Map<?,?>)field(portals,"frames")).size()==2&&(boolean)field(portals,"activated")&&!(boolean)call(portals,"open",new Class<?>[]{}),"association et activation persistées sans ouverture automatique");
        red=actor("V22Rouge",new Location(nether,.5,82,2.5));red.loadData();Bukkit.getPluginManager().callEvent(new PlayerJoinEvent(red,"fixture après redémarrage"));call(fk,"applyMode",new Class<?>[]{Player.class},red);
        check(red.getInventory().getItem(0)!=null&&red.getInventory().getItem(0).getAmount()==7,"inventaire Nether conservé au redémarrage");
        command("resume");check((boolean)call(portals,"open",new Class<?>[]{}),"ouverture officielle restaurée après reprise manuelle");
        check(red.teleport(new Location(nether,.5,82,.5)),"positionnement vers cadre Nether accepté après reprise");
        for(var endpoint:((Map<?,?>)field(portals,"frames")).entrySet()){
            Object f=endpoint.getValue();
            check((boolean)call(f,"intact",new Class<?>[]{boolean.class},true),"cadre intact après reprise "+endpoint.getKey());
        }
        getLogger().info("FINAL RETURN DIAGNOSTIC world="+red.getWorld().getName()+" mode="+red.getGameMode()+" participant="+call(fk,"activeParticipant",new Class<?>[]{Player.class},red)+" sourceIncludes="+call(((Map<?,?>)field(portals,"frames")).get("nether"),"includes",new Class<?>[]{Location.class},red.getLocation()));
        var back=new PlayerPortalEvent(red,red.getLocation(),world.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(back);
        later(30,()->{check(red.getWorld()==world&&red.getInventory().getItem(0).getAmount()==7,"retour officiel sûr après redémarrage sans perte");clear(red);command(red,"base");check(SyntheticPlayer.lastActionBar(red).contains("Rouge")&&!SyntheticPlayer.lastActionBar(red).contains("indisponible"),"guidage rétabli après retour dimensionnel");
            command("nether","portal","deactivate");check(!(boolean)call(portals,"open",new Class<?>[]{})&&world.getBlockAt(12,72,0).getType()==Material.AIR&&nether.getBlockAt(0,82,0).getType()==Material.AIR,"désactivation retire les deux surfaces");
            red.teleport(new Location(world,12.5,72,.5));var denied=new PlayerPortalEvent(red,red.getLocation(),nether.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(denied);later(5,()->{check(denied.isCancelled()&&red.getWorld()==world,"traversée fermée impossible");finish();});});
    }
    private void finish()throws Exception{
        for(Player p:new ArrayList<>(actors)){p.saveData();if(p.isOp())p.setOp(false);SyntheticPlayer.remove(p);}actors.clear();
        Files.writeString(Bukkit.getWorldContainer().toPath().resolve("final-probe-result-"+(Boolean.getBoolean("fk.finalprobe.restart")?"restart":"initial")+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("passed",true,"checks",checks,"assertions",checks.size(),"authenticatedClients",0,"clientRenderingVerified",false))+"\n");
        getLogger().info("FINAL PROBE SUCCESS");Bukkit.shutdown();
    }
    private void fail(Throwable e){getLogger().log(Level.SEVERE,"FINAL PROBE FAILED",e);for(Player p:actors)try{if(p.isOp())p.setOp(false);SyntheticPlayer.remove(p);}catch(Exception ignored){}Bukkit.shutdown();}
}
