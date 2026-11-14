package fr.fkamis;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.event.world.PortalCreateEvent;
import org.bukkit.inventory.ItemStack;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Vector;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

public final class VNext1Probe extends JavaPlugin implements Listener {
    private JavaPlugin companion;private Object state;private World world,nether;private final List<Player> players=new ArrayList<>();private Player admin,red,blue,eliminated;private final List<String> checks=new ArrayList<>();private Path root;
    private int naturalPortalAttempts;private final Map<String,Integer> ignitionAttempts=new LinkedHashMap<>();
    private int deniedIgnitions,deniedDispenses;
    private Object field(Object o,String name)throws Exception{return SyntheticPlayer.field(o,name);}
    private void set(Object o,String name,Object value)throws Exception{SyntheticPlayer.set(o,name,value);}
    private Object call(Object o,String name,Class<?>[] types,Object...args)throws Exception{Method m=o.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(o,args);}
    private void check(boolean value,String name){if(!value)throw new AssertionError(name);checks.add(name);getLogger().info("VNEXT1 PROBE PASS "+name);}
    private void command(CommandSender sender,String...args){companion.onCommand(sender,companion.getCommand("fka"),"fka",args);}
    private void command(String...args){command(Bukkit.getConsoleSender(),args);}
    @Override public void onEnable(){root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();if(!root.getFileName().toString().startsWith("probe-vnext1")||!Boolean.getBoolean("fk.vnext1"))throw new IllegalStateException("Copie isolée requise.");Bukkit.getPluginManager().registerEvents(this,this);Bukkit.getScheduler().runTaskLater(this,()->{try{if(Boolean.getBoolean("fk.vnext1.restart"))restart();else start();}catch(Throwable error){fail(error);}},40);}
    private void later(int ticks,Checked task){Bukkit.getScheduler().runTaskLater(this,()->{try{task.run();}catch(Throwable error){fail(error);}},ticks);}
    @FunctionalInterface interface Checked {void run()throws Exception;}
    @SuppressWarnings("unchecked") private Player participant(String name,String team,Location at)throws Exception{
        UUID id=UUID.nameUUIDFromBytes(("VNext1Probe:"+name).getBytes(java.nio.charset.StandardCharsets.UTF_8));((Map<UUID,String>)field(companion,"roster")).put(id,team);((Map<UUID,String>)field(companion,"rosterNames")).put(id,name);fr.devsylone.fkpi.FkPI.getInstance().getTeamManager().addPlayer(name,team);
        Player p=SyntheticPlayer.create(name,at);players.add(p);call(companion,"applyMode",new Class<?>[]{Player.class},p);return p;
    }
    private void platform(World level,int x,int y,int z){for(int dx=-6;dx<=6;dx++)for(int dz=-6;dz<=6;dz++){level.getChunkAt((x+dx)>>4,(z+dz)>>4).addPluginChunkTicket(this);level.getBlockAt(x+dx,y-1,z+dz).setType(Material.STONE,false);for(int dy=0;dy<7;dy++)level.getBlockAt(x+dx,y+dy,z+dz).setType(Material.AIR,false);}}
    private void start()throws Exception{
        companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");state=field(companion,"state");world=Bukkit.getWorld("world");nether=Bukkit.getWorlds().stream().filter(w->w.getEnvironment()==World.Environment.NETHER).findFirst().orElseThrow();platform(world,160,200,160);
        for(var team:fr.devsylone.fkpi.FkPI.getInstance().getTeamManager().getTeams()){check(team.getBase().getRadius()==40,"rayon 40 "+team.getName());Location c=team.getBase().getCenter();check(team.getBase().contains(c.clone().add(40,-30,40))&&!team.getBase().contains(c.clone().add(41,0,0)),"bornes carrées et verticales "+team.getName());}
        int n=0;for(String team:List.of("Rouge","Bleue","Verte","Jaune"))for(int i=0;i<2;i++)participant("VN1"+team+i,team,new Location(world,158.5+(n++%5),200,158.5+n/5));
        red=players.get(0);blue=players.get(2);eliminated=players.get(4);
        admin=SyntheticPlayer.create("VN1Arbitre",new Location(world,160.5,200,163.5));players.add(admin);command("admin","grant",admin.getUniqueId().toString(),"confirm");
        call(state,"start",new Class<?>[]{Collection.class,boolean.class,int.class},List.of(2,2,2,2),false,2);call(companion,"syncNative",new Class<?>[]{});
        check(admin.getGameMode()==GameMode.CREATIVE&&admin.getAllowFlight(),"arbitre créatif et vol conservés");check(red.getGameMode()==GameMode.SURVIVAL&&!red.getAllowFlight(),"allow-flight serveur n’accorde aucun vol SURVIVAL");
        getLogger().info("BORDERS overworld="+world.getWorldBorder().getSize()+" nether="+nether.getWorldBorder().getSize());
        check(nether.getWorldBorder().getSize()>59_000_000&&world.getWorldBorder().getSize()==companion.getConfig().getInt("border-size"),"bordure Overworld conservée, Nether technique étendu");
        Object guidance=field(companion,"baseGuidance");call(guidance,"privacy",new Class<?>[]{Player.class,boolean.class},red,false);check(red.getAttribute(org.bukkit.attribute.Attribute.WAYPOINT_TRANSMIT_RANGE).getValue()==0&&red.getAttribute(org.bukkit.attribute.Attribute.WAYPOINT_RECEIVE_RANGE).getValue()==0&&!world.getGameRuleValue(GameRules.LOCATOR_BAR),"aucune transmission/réception native de positions");
        command(red,"base");String guidanceText=SyntheticPlayer.lastActionBar(red);check(guidanceText!=null&&guidanceText.contains("Rouge")&&!guidanceText.contains("Bleue"),"texte sortant limité à sa propre base");Location blueAt=blue.getLocation();blue.teleport(blueAt.clone().add(2,0,0));command(red,"base");check(guidanceText.equals(SyntheticPlayer.lastActionBar(red)),"déplacement adverse sans effet sur guidage envoyé");pause();disconnect();spectators();portals();
    }
    private void pause()throws Exception{
        Location anchor=red.getLocation();boolean gravity=red.hasGravity();command("pause");Object service=field(companion,"pauseControl");check(!red.hasGravity(),"gravité suspendue à la transition de pause");
        var move=new PlayerMoveEvent(red,anchor,anchor.clone().add(2,3,1));Bukkit.getPluginManager().callEvent(move);check(move.getTo().distanceSquared(anchor)<.01,"déplacement horizontal et vertical ancré");
        var tp=new PlayerTeleportEvent(red,anchor,anchor.clone().add(3,0,0),PlayerTeleportEvent.TeleportCause.COMMAND);Bukkit.getPluginManager().callEvent(tp);check(tp.isCancelled(),"téléportation participant refusée en pause");
        Arrow arrow=world.spawn(anchor.clone().add(0,3,0),Arrow.class);arrow.setShooter(red);var launch=new ProjectileLaunchEvent(arrow);Bukkit.getPluginManager().callEvent(launch);check(launch.isCancelled(),"projectile participant refusé en pause");arrow.remove();
        Entity boat=world.spawnEntity(anchor.clone().add(2,0,0),EntityType.OAK_BOAT);var mount=new EntityMountEvent(red,boat);Bukkit.getPluginManager().callEvent(mount);check(mount.isCancelled(),"véhicule refusé en pause");boat.remove();
        var velocity=new PlayerVelocityEvent(red,new Vector(2,3,0));Bukkit.getPluginManager().callEvent(velocity);check(velocity.isCancelled(),"knockback refusé en pause");
        var adminMove=new PlayerMoveEvent(admin,admin.getLocation(),admin.getLocation().add(1,2,0));Bukkit.getPluginManager().callEvent(adminMove);check(adminMove.getTo().getY()!=adminMove.getFrom().getY(),"arbitre mobile pendant pause");
        command("resume");check(red.hasGravity()==gravity&&!((Map<?,?>)field(service,"anchors")).containsKey(red.getUniqueId()),"reprise restaure gravité et retire ancrage");
    }
    private void disconnect()throws Exception{
        int threshold=(int)call(companion,"requiredAttackers",new Class<?>[]{String.class},"Rouge");Bukkit.getPluginManager().callEvent(new PlayerQuitEvent(red,"fixture sans déconnexion réseau"));
        check(!(boolean)field(state,"paused")&&!Bukkit.getServerTickManager().isFrozen(),"déconnexion en jeu ne met pas en pause");check((int)call(companion,"requiredAttackers",new Class<?>[]{String.class},"Rouge")==threshold&&threshold==2,"effectif officiel conservé après départ");
        Object grace=field(companion,"respawnProtection");check(!(boolean)call(grace,"active",new Class<?>[]{UUID.class},red.getUniqueId()),"départ et retour sans nouvelle grâce de respawn");
        Bukkit.getPluginManager().callEvent(new PlayerJoinEvent(red,"fixture sans authentification"));
    }
    @SuppressWarnings("unchecked") private void spectators()throws Exception{
        ((Set<String>)field(state,"eliminated")).add("Verte");call(companion,"applyMode",new Class<?>[]{Player.class},eliminated);
        Object service=field(companion,"spectators");command(eliminated,"spectate");check(eliminated.getOpenInventory().getTopInventory().getSize()==27,"menu d’observation ouvert pour éliminé");
        int food=eliminated.getInventory().getItem(0)==null?0:eliminated.getInventory().getItem(0).getAmount();command(eliminated,"spectate",blue.getName());check(eliminated.getLocation().distanceSquared(blue.getLocation())<25&&eliminated.getGameMode()==GameMode.SPECTATOR,"téléportation vers actif sans réintégration");check((eliminated.getInventory().getItem(0)==null?0:eliminated.getInventory().getItem(0).getAmount())==food,"inventaire spectateur non rétabli ou modifié");
        boolean denied=false;try{call(service,"follow",new Class<?>[]{Player.class,Player.class},red,blue);}catch(InvocationTargetException expected){denied=true;}check(denied,"participant actif ne peut pas observer par téléportation");
        command("pause");var move=new PlayerMoveEvent(eliminated,eliminated.getLocation(),eliminated.getLocation().add(1,1,0));Bukkit.getPluginManager().callEvent(move);check(move.getTo().distanceSquared(move.getFrom())<.01,"spectateur également figé en pause");command("resume");
    }
    @SuppressWarnings({"unchecked","rawtypes"}) private void portals()throws Exception{
        Object service=field(companion,"netherPortals");platform(world,12,72,0);platform(nether,0,82,0);
        Class<?> frameClass=Class.forName("fr.fkamis.NetherPortalService$Frame",true,companion.getClass().getClassLoader());Constructor<?> constructor=frameClass.getDeclaredConstructors()[0];constructor.setAccessible(true);
        Map frames=(Map)field(service,"frames");
        for(var endpoint:List.of(new Object[]{"overworld",world,12,72,0},new Object[]{"nether",nether,0,82,0})){
            String side=(String)endpoint[0];World level=(World)endpoint[1];int x=(int)endpoint[2],y=(int)endpoint[3],z=(int)endpoint[4];
            for(int u=-1;u<=2;u++)for(int v=-1;v<=3;v++)level.getBlockAt(x+u,y+v,z).setType(u==-1||u==2||v==-1||v==3?Material.OBSIDIAN:Material.AIR,false);
            Location exit=new Location(level,x+.5,y,z+2.5);Object frame=constructor.newInstance(level.getName(),x,y,z,Axis.X,2,3,exit);call(service,"validate",new Class<?>[]{frameClass,String.class,boolean.class},frame,side,true);frames.put(side,frame);
        }
        frames.clear();for(var endpoint:List.of(new Object[]{"overworld",world,12,72,0},new Object[]{"nether",nether,0,82,0})){
            String side=(String)endpoint[0];World level=(World)endpoint[1];int x=(int)endpoint[2],y=(int)endpoint[3],z=(int)endpoint[4];Location view=new Location(level,x+1.5,y,z+5.5);view.setDirection(new Vector(x-.5-(x+1.5),y+.5-(y+1.62),z+.5-(z+5.5)));admin.teleport(view,PlayerTeleportEvent.TeleportCause.PLUGIN);command(admin,"nether","portal","register",side);check(frames.containsKey(side),"enregistrement réel par cadre visé "+side);
        }
        call(service,"updateProtection",new Class<?>[]{});command("nether","portal","activate");check(!(boolean)field(service,"activated"),"activation Nether J1 refusée");
        for(var reason:org.bukkit.event.world.PortalCreateEvent.CreateReason.values()){var create=new PortalCreateEvent(new ArrayList<>(),world,red,reason);Bukkit.getPluginManager().callEvent(create);check(create.isCancelled()==(reason!=PortalCreateEvent.CreateReason.END_PLATFORM),"contrôle création Nether sans bloquer plateforme End "+reason);}
        command("nextday");command("nether","portal","activate");check((boolean)field(service,"activated")&&world.getBlockAt(12,72,0).getType()==Material.NETHER_PORTAL&&nether.getBlockAt(0,82,0).getType()==Material.NETHER_PORTAL,"deux surfaces officielles réelles activées J2");
        var bypass=new PlayerTeleportEvent(red,red.getLocation(),new Location(nether,2000,82,2000),PlayerTeleportEvent.TeleportCause.ENDER_PEARL);Bukkit.getPluginManager().callEvent(bypass);check(bypass.isCancelled(),"contournement interdimensionnel par perle refusé");
        performance();ignition();
        red.getInventory().setItem(0,new ItemStack(Material.BREAD,7));red.teleport(new Location(world,12.5,72,.5),PlayerTeleportEvent.TeleportCause.PLUGIN);
        var event=new PlayerPortalEvent(red,red.getLocation(),nether.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(event);check(event.isCancelled()&&!event.getCanCreatePortal(),"recherche et génération Vanilla neutralisées");
        later(30,()->{Class<?> safety=Class.forName("fr.fkamis.TravelSafety",true,companion.getClass().getClassLoader());Method safe=safety.getDeclaredMethod("safe",Location.class);safe.setAccessible(true);check(red.getWorld()==nether&&(boolean)safe.invoke(null,red.getLocation()),"route Overworld vers sortie Nether officielle sûre");check(red.getInventory().getItem(0).getAmount()==7,"inventaire conservé au voyage Nether");
            command(red,"base");check(SyntheticPlayer.lastActionBar(red).contains("direction indisponible"),"aucune fausse direction entre dimensions");
            String name=red.getName();Location at=red.getLocation();Bukkit.getPluginManager().callEvent(new PlayerQuitEvent(red,"test logout Nether"));red.saveData();players.remove(red);SyntheticPlayer.remove(red);red=SyntheticPlayer.create(name,at);red.loadData();players.add(red);Bukkit.getPluginManager().callEvent(new PlayerJoinEvent(red,"test reconnexion Nether"));call(companion,"applyMode",new Class<?>[]{Player.class},red);check(red.getWorld()==nether&&red.getInventory().getItem(0).getAmount()==7&&!(boolean)field(state,"paused"),"reconnexion Nether sans pause ni perte d’inventaire");
            later(65,()->{red.teleport(new Location(nether,.5,82,.5),PlayerTeleportEvent.TeleportCause.PLUGIN);var back=new PlayerPortalEvent(red,red.getLocation(),world.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.NETHER_PORTAL);Bukkit.getPluginManager().callEvent(back);later(30,()->{check(red.getWorld()==world&&red.getLocation().getX()>10&&red.getLocation().getX()<16,"retour forcé vers unique sortie Overworld");command("pause");check(world.getBlockAt(12,72,0).getType()==Material.AIR,"surfaces suspendues en pause");command("resume");check(world.getBlockAt(12,72,0).getType()==Material.NETHER_PORTAL,"surfaces rétablies à la reprise");nether.getBlockAt(-1,82,0).setType(Material.AIR,false);call(service,"tick",new Class<?>[]{});check(!(boolean)field(service,"activated"),"suppression accidentelle détectée sans génération de sortie");finish();});});});
    }
    private void restart()throws Exception{
        companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");state=field(companion,"state");world=Bukkit.getWorld("world");nether=Bukkit.getWorlds().stream().filter(w->w.getEnvironment()==World.Environment.NETHER).findFirst().orElseThrow();Object service=field(companion,"netherPortals");
        check((boolean)field(state,"paused"),"redémarrage garde la pause administrative");check(((Map<?,?>)field(service,"frames")).size()==2&&!(boolean)field(service,"activated"),"cadres persistants et portail endommagé toujours fermé");check(!(boolean)call(service,"open",new Class<?>[]{}),"aucune réactivation ou nouvelle sortie au redémarrage");finish();
    }
    @EventHandler(priority=EventPriority.MONITOR) public void observedPortal(PortalCreateEvent event){if(event.getReason()==PortalCreateEvent.CreateReason.FIRE){naturalPortalAttempts++;if(!event.isCancelled())throw new AssertionError("Une création alternative a été autorisée.");}}
    @EventHandler(priority=EventPriority.MONITOR) public void observedDispense(BlockDispenseEvent event){if(event.isCancelled())deniedDispenses++;getLogger().info("NATIVE DISPENSE "+event.getItem().getType()+" cancelled="+event.isCancelled());}
    @EventHandler(priority=EventPriority.MONITOR) public void observedIgnition(BlockIgniteEvent event){if(event.isCancelled())deniedIgnitions++;getLogger().info("NATIVE IGNITION "+event.getCause()+" cancelled="+event.isCancelled()+" at="+event.getBlock().getLocation());}
    private void ignition()throws Exception{
        platform(world,28,72,0);for(int u=-1;u<=2;u++)for(int v=-1;v<=3;v++)world.getBlockAt(28+u,72+v,0).setType(u==-1||u==2||v==-1||v==3?Material.OBSIDIAN:Material.AIR,false);
        for(Material tool:List.of(Material.FLINT_AND_STEEL,Material.FIRE_CHARGE)){
            for(int u=0;u<2;u++)for(int v=0;v<3;v++)world.getBlockAt(28+u,72+v,0).setType(Material.AIR,false);
            red.getInventory().setItemInMainHand(new ItemStack(tool));int before=naturalPortalAttempts;SyntheticPlayer.useOn(red,world.getBlockAt(28,71,0));
            ignitionAttempts.put(tool.name(),naturalPortalAttempts-before);check(naturalPortalAttempts>before&&world.getBlockAt(28,73,0).getType()!=Material.NETHER_PORTAL,"ignition Vanilla bloquée "+tool);
        }
        for(int u=0;u<2;u++)for(int v=0;v<3;v++)world.getBlockAt(28+u,72+v,0).setType(Material.AIR,false);
        Block block=world.getBlockAt(28,72,1);block.setType(Material.DISPENSER,false);var facing=(org.bukkit.block.data.Directional)block.getBlockData();facing.setFacing(BlockFace.NORTH);block.setBlockData(facing,false);Dispenser dispenser=(Dispenser)block.getState();dispenser.getInventory().setItem(0,new ItemStack(Material.FLINT_AND_STEEL));int before=naturalPortalAttempts,denied=deniedIgnitions+deniedDispenses;boolean executed=dispenser.dispense();ignitionAttempts.put("DISPENSER",naturalPortalAttempts-before);check(executed&&(naturalPortalAttempts>before||deniedIgnitions+deniedDispenses>denied)&&world.getBlockAt(28,73,0).getType()!=Material.NETHER_PORTAL,"ignition réelle par distributeur bloquée");
        var lava=new BlockIgniteEvent(world.getBlockAt(12,72,0),BlockIgniteEvent.IgniteCause.LAVA,(Entity)null);Bukkit.getPluginManager().callEvent(lava);check(lava.isCancelled(),"ignition lave sur volume officiel protégée");
    }
    private void finish()throws Exception{
        int physicalPlayers=players.size();
        for(Player p:new ArrayList<>(players))SyntheticPlayer.remove(p);players.clear();
        Path out=root.getParent().getParent().resolve("tests/results");Files.createDirectories(out);Files.writeString(out.resolve("vnext1-probe"+(Boolean.getBoolean("fk.vnext1.restart")?"-restart":"")+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("passed",true,"checks",checks,"authenticatedClients",0,"realNmsPlayers",physicalPlayers,"clientRenderingVerified",false,"nativeIgnitions",ignitionAttempts,"nativeDispensesCancelled",deniedDispenses))+"\n");
        getLogger().info("VNEXT1 PROBE SUCCESS");Bukkit.shutdown();
    }
    @FunctionalInterface private interface Measured {void run()throws Exception;}
    private double measure(int count,Measured operation)throws Exception{
        for(int n=0;n<Math.min(count,1000);n++)operation.run();
        long at=System.nanoTime();for(int n=0;n<count;n++)operation.run();return (System.nanoTime()-at)/(double)count;
    }
    private void performance()throws Exception{
        var data=new LinkedHashMap<String,Object>();Location at=red.getLocation();
        Object pause=field(companion,"pauseControl"),guidance=field(companion,"baseGuidance"),portals=field(companion,"netherPortals"),places=field(companion,"protectedPlaces");
        Method move=pause.getClass().getDeclaredMethod("move",PlayerMoveEvent.class);move.setAccessible(true);
        Method show=guidance.getClass().getDeclaredMethod("show",Player.class);show.setAccessible(true);
        Method tick=portals.getClass().getDeclaredMethod("tick");tick.setAccessible(true);
        Method contains=places.getClass().getDeclaredMethod("contains",Location.class);contains.setAccessible(true);
        int chunks=Bukkit.getWorlds().stream().mapToInt(w->w.getLoadedChunks().length).sum();
        data.put("activeMovementListenerMeanNs",measure(20000,()->move.invoke(pause,new PlayerMoveEvent(red,at,at.clone().add(.01,0,0)))));
        data.put("allMovementListenersMeanNs",measure(10000,()->Bukkit.getPluginManager().callEvent(new PlayerMoveEvent(red,at,at.clone().add(.01,0,0)))));
        data.put("ownBaseActionBarMeanNs",measure(2000,()->show.invoke(guidance,red)));
        data.put("twoOpenPortalChecksMeanNs",measure(2000,()->tick.invoke(portals)));
        data.put("protectedPlaceLookupMeanNs",measure(100000,()->contains.invoke(places,at)));
        command("pause");data.put("pausedMovementListenerMeanNs",measure(20000,()->move.invoke(pause,new PlayerMoveEvent(red,at,at.clone().add(.01,.01,0)))));command("resume");
        data.put("additionalLoadedChunksDuringMicrobench",Bukkit.getWorlds().stream().mapToInt(w->w.getLoadedChunks().length).sum()-chunks);
        data.put("heapUsedBytes",java.lang.management.ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed());
        data.put("tps",Bukkit.getTPS());data.put("averageMspt",Bukkit.getAverageTickTime());data.put("authenticatedClients",0);data.put("realNmsPlayers",players.size());
        data.put("scope","Micro-mesures locales avec réflexion, corps NMS sans clients ni réseau ; aucune certification MineStrator.");
        Path output=root.getParent().getParent().resolve("tests/results/vnext1-performance.json");Files.createDirectories(output.getParent());Files.writeString(output,new GsonBuilder().setPrettyPrinting().create().toJson(data)+"\n");
        check(((Number)data.get("additionalLoadedChunksDuringMicrobench")).intValue()==0,"micro-mesures mouvement/guidage/portails sans chunk supplémentaire");
    }
    private void fail(Throwable error){getLogger().log(Level.SEVERE,"VNEXT1 PROBE FAILED",error);try{for(Player p:players)SyntheticPlayer.remove(p);}catch(Exception ignored){}Bukkit.shutdown();}
}
