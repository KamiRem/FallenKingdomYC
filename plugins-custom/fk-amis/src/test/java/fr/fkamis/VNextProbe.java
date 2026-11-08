package fr.fkamis;

import com.google.gson.*;
import fr.devsylone.fkpi.FkPI;
import net.kyori.adventure.bossbar.BossBar;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.damage.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.*;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.util.Vector;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Événements Paper réels et interfaces Player de fixture, jamais des clients authentifiés. */
public final class VNextProbe extends JavaPlugin {
    private JavaPlugin companion;private Object state;private World world;private Path output;private int phase,index;
    private Map<UUID,String> roster,names;private final List<Actor> actors=new ArrayList<>();private Actor admin;
    private final List<String> passed=new ArrayList<>();private final List<String> teams=List.of("Rouge","Bleue","Verte","Jaune");
    private Object field(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
    private void set(Object o,String name,Object value)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);f.set(o,value);}
    private Object call(Object o,String name,Class<?>[] types,Object...args)throws Exception{Method method=o.getClass().getDeclaredMethod(name,types);method.setAccessible(true);return method.invoke(o,args);}
    private void check(boolean ok,String label){if(!ok)throw new AssertionError(label);passed.add(label);getLogger().info("VNEXT PROBE PASS "+label);}
    private void command(CommandSender sender,String...args){companion.onCommand(sender,companion.getCommand("fka"),"fka",args);}
    private void command(String...args){command(Bukkit.getConsoleSender(),args);}
    private Path file(String name){return companion.getDataFolder().toPath().resolve(name);}
    @Override @SuppressWarnings("unchecked") public void onEnable(){try{
        Path root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();if(!root.getFileName().toString().startsWith("probe-vnext")||!Boolean.getBoolean("fk.vnext"))throw new IllegalStateException("Copie VNext isolée requise.");
        output=root.getParent().getParent().resolve("tests/results");Files.createDirectories(output);companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");world=Bukkit.getWorld("world");state=field(companion,"state");roster=(Map<UUID,String>)field(companion,"roster");names=(Map<UUID,String>)field(companion,"rosterNames");phase=Integer.getInteger("fk.vnext.phase",0);
        Bukkit.getScheduler().runTaskLater(this,()->{try{if(phase==0)settings();else if(phase==1)gameplay();else if(phase==2)restart();else afterReset();}catch(Throwable error){fail(error);}},40);
    }catch(Throwable error){fail(error);}}
    private void settings()throws Exception {
        check(Bukkit.getOnlinePlayers().isEmpty(),"zéro client authentifié");check(!(boolean)field(state,"started"),"jour zéro conservé à la migration");
        admin=new Actor("ArbitreVNext",false);command("admin","grant",admin.id.toString(),"confirm");call(companion,"applyMode",new Class<?>[]{Player.class},admin.player);
        check(admin.mode==GameMode.CREATIVE,"arbitre UUID préservé");Actor ordinary=new Actor("Ordinaire",true);
        String before=Files.readString(file("config.yml"));command(ordinary.player,"config","set","players-per-team","4");check(Files.readString(file("config.yml")).equals(before),"OP ordinaire ne modifie pas les règles");
        for(String value:List.of("0","5","NaN","2.5")){command("config","set","players-per-team",value);check(Files.readString(file("config.yml")).equals(before),"capacité invalide refusée "+value);}
        command("config","set","capture-radius","1");check(Files.readString(file("config.yml")).equals(before),"rayon de capture impossible refusé");
        command("config","set","pvp-day","4");check(Files.readString(file("config.yml")).equals(before),"jours incohérents refusés");
        command(admin.player,"config","set","players-per-team","3");command("config","set","supply-interval-seconds","1200");
        check(companion.getConfig().getInt("players-per-team")==3,"configuration arbitre appliquée");
        check((int)field(field(companion,"supplies"),"interval")==1200,"intervalle ravitaillement unique modifié");
        check(Files.readString(file("config.yml")).contains("custom-vnext-note")&&Files.readString(file("supplies.yml")).contains("custom-vnext-supply"),"paramètres inconnus conservés");
        command("config","validate");command("config","diff");command("config","get","players-per-team");
        command(ordinary.player,"info");command(ordinary.player,"info","teams");command(ordinary.player,"stats","match");
        check(ordinary.messages.stream().noneMatch(s->s.contains("spawns.")||s.contains("objectives.")||s.contains(" -240 ")),"informations publiques sans positions secrètes");
        command("reset","prepare");Object plan=field(field(companion,"resets"),"plan");String token=(String)call(plan,"token",new Class<?>[]{});
        command("reset","confirm","incorrect");check(!Files.exists(file("reset-request.json")),"mauvais jeton refusé sans demande destructive");
        command("config","set","players-per-team","4");command("reset","confirm",token);check(!Files.exists(file("reset-request.json")),"jeton invalidé par changement de configuration");command("reset","cancel");
        command("config","set","players-per-team","3");call(companion,"saveState",new Class<?>[]{});finish();
    }
    @SuppressWarnings("unchecked") private void gameplay()throws Exception {
        check(companion.getConfig().getInt("players-per-team")==3&&(int)field(field(companion,"supplies"),"interval")==1200,"configuration persistante après redémarrage");
        command("config","defaults");check(companion.getConfig().getInt("players-per-team")==2,"défauts validés appliqués avant partie");
        for(String team:teams)for(int n=0;n<2;n++){Actor actor=new Actor(team+"VN"+n,false);actors.add(actor);roster.put(actor.id,team);names.put(actor.id,actor.name);FkPI.getInstance().getTeamManager().addPlayer(actor.name,team);}
        admin=new Actor("ArbitreVNext",false);call(companion,"applyMode",new Class<?>[]{Player.class},admin.player);
        call(state,"start",new Class<?>[]{Collection.class,boolean.class,int.class},List.of(2,2,2,2),false,2);call(companion,"syncNative",new Class<?>[]{});
        String config=Files.readString(file("config.yml"));command("config","set","capture-seconds","10");check(Files.readString(file("config.yml")).equals(config),"règles structurantes verrouillées dès le départ");
        command("reset","prepare");check(field(field(companion,"resets"),"plan")==null,"reset refusé en partie active");
        regions();graceAndStats();captures();performance();
        var yaml=YamlConfiguration.loadConfiguration(file("state.yml").toFile());check(yaml.getInt("custom-vnext-state.keep")==42,"champs d'état inconnus conservés après les mutations");
        Object statistics=field(companion,"statistics"),model=field(statistics,"model");String id=(String)field(model,"matchId");
        Files.writeString(getDataFolder().toPath().resolve("expected.json"),new Gson().toJson(Map.of("matchId",id,"statistics",(String)call(model,"json",new Class<?>[]{}))));finish();
    }
    private void regions()throws Exception {
        Object places=field(companion,"protectedPlaces");List<?> boxes=(List<?>)field(places,"boxes");Actor red=actors.getFirst();int checked=0;
        for(Object box:boxes){int x=(int)field(box,"minX"),y=(int)field(box,"minY"),z=(int)field(box,"minZ");Block block=world.getBlockAt(x,y,z);Material original=block.getType();block.setType(Material.STONE,false);
            var destroy=new BlockBreakEvent(block,red.player);Bukkit.getPluginManager().callEvent(destroy);check(destroy.isCancelled(),"destruction protégée "+(++checked));
            check(place(red,block).isCancelled(),"obstruction protégée "+checked);check(!place(admin,block).isCancelled(),"arbitre peut bâtir zone "+checked);block.setType(original,false);
        }
        check(checked==16,"sept monuments, huit ravitaillements, un centre protégés");
        Location at=(Location)call(field(companion,"centralSpawn"),"resolve",new Class<?>[]{});Block protectedBlock=at.clone().subtract(0,1,0).getBlock();Block neutral=world.getBlockAt(160,200,160);neutral.setType(Material.STONE,false);
        var flow=new BlockFromToEvent(world.getBlockAt(at.getBlockX()-4,at.getBlockY(),at.getBlockZ()),world.getBlockAt(at.getBlockX()-3,at.getBlockY(),at.getBlockZ()));Bukkit.getPluginManager().callEvent(flow);check(flow.isCancelled(),"liquide entrant dans le centre refusé");
        Block moved=world.getBlockAt(at.getBlockX()-4,at.getBlockY(),at.getBlockZ());var piston=new BlockPistonExtendEvent(moved.getRelative(BlockFace.WEST),List.of(moved),BlockFace.EAST);Bukkit.getPluginManager().callEvent(piston);check(piston.isCancelled(),"piston vers la limite du centre refusé");
        Creeper creeper=world.spawn(new Location(world,160,202,160),Creeper.class);creeper.setAI(false);
        var blast=new EntityExplodeEvent(creeper,at,new ArrayList<>(List.of(protectedBlock,neutral)),1,ExplosionResult.DESTROY);Bukkit.getPluginManager().callEvent(blast);check(!blast.blockList().contains(protectedBlock)&&blast.blockList().contains(neutral),"explosion garde la structure mais permet destruction neutre");
        red.at=at;var damage=new EntityDamageByEntityEvent(creeper,red.player,EntityDamageEvent.DamageCause.ENTITY_EXPLOSION,DamageSource.builder(DamageType.EXPLOSION).withCausingEntity(creeper).withDirectEntity(creeper).build(),5);Bukkit.getPluginManager().callEvent(damage);check(!damage.isCancelled(),"creeper blesse normalement le participant dans une zone protégée");creeper.remove();
        FallingBlock falling=world.spawnFallingBlock(at.clone().add(0,4,0),Material.SAND.createBlockData());var gravity=new EntityChangeBlockEvent(falling,protectedBlock,Material.SAND.createBlockData());Bukkit.getPluginManager().callEvent(gravity);check(gravity.isCancelled(),"bloc gravitaire ne remplace pas le sol protégé");falling.remove();
        var dispense=new BlockDispenseEvent(protectedBlock,new ItemStack(Material.LAVA_BUCKET),new Vector(1,0,0));Bukkit.getPluginManager().callEvent(dispense);check(dispense.isCancelled(),"distributeur dans la zone protégé");
        check(!place(red,neutral).isCancelled(),"construction neutre extérieure toujours autorisée");
    }
    private BlockPlaceEvent place(Actor actor,Block block){var e=new BlockPlaceEvent(block,block.getState(),block.getRelative(0,-1,0),new ItemStack(Material.STONE),actor.player,true,EquipmentSlot.HAND);Bukkit.getPluginManager().callEvent(e);return e;}
    private EntityDamageByEntityEvent hit(Actor attacker,Actor target){var e=new EntityDamageByEntityEvent(attacker.player,target.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK,DamageSource.builder(DamageType.PLAYER_ATTACK).withCausingEntity(attacker.player).withDirectEntity(attacker.player).build(),4);Bukkit.getPluginManager().callEvent(e);if(!e.isCancelled())target.lastDamage=e;return e;}
    private PlayerRespawnEvent respawn(Actor actor){return new PlayerRespawnEvent(actor.player,actor.at,false,false,false,PlayerRespawnEvent.RespawnReason.DEATH);}
    @SuppressWarnings("unchecked") private void graceAndStats()throws Exception {
        command("nextday");Actor red=actors.get(0),blue=actors.get(2);red.at=new Location(world,160.5,200,160.5);blue.at=red.at.clone().add(3,0,0);
        Object grace=field(companion,"respawnProtection");Map<UUID,Long> expires=(Map<UUID,Long>)field(grace,"expires");
        Bukkit.getPluginManager().callEvent(respawn(red));long deadline=expires.get(red.id);
        check(hit(red,blue).isCancelled()&&hit(blue,red).isCancelled(),"protection de respawn réciproque PvP");
        var tp=new PlayerTeleportEvent(red.player,red.at,red.at.clone().add(1,0,0),PlayerTeleportEvent.TeleportCause.PLUGIN);Bukkit.getPluginManager().callEvent(tp);
        // Le callback natif de scoreboard exige un client enregistré ; cette fixture
        // appelle seulement le handler FKAmis, le corps NMS est testé séparément.
        call(companion,"onWorldChanged",new Class<?>[]{PlayerChangedWorldEvent.class},new PlayerChangedWorldEvent(red.player,world));check(expires.get(red.id)==deadline,"téléportation et monde ne prolongent pas la protection");
        Skeleton mob=world.spawn(red.at.clone().add(4,0,0),Skeleton.class);mob.setAI(false);Arrow arrow=mob.launchProjectile(Arrow.class,new Vector(0,0,1));var pve=new EntityDamageByEntityEvent(arrow,red.player,EntityDamageEvent.DamageCause.PROJECTILE,DamageSource.builder(DamageType.ARROW).withDirectEntity(arrow).withCausingEntity(mob).build(),4);Bukkit.getPluginManager().callEvent(pve);check(!pve.isCancelled(),"protection de respawn ne désactive pas le PvE");arrow.remove();mob.remove();
        expires.put(red.id,System.currentTimeMillis()-1);check(!(boolean)call(grace,"active",new Class<?>[]{UUID.class},red.id),"protection expire sans reconnexion");
        check(!hit(red,blue).isCancelled(),"PvP neutre J2 fonctionne après expiration");
        Object stats=field(companion,"statistics"),model=field(stats,"model");Map<?,?> members=(Map<?,?>)field(model,"players");
        check(((Number)field(members.get(red.id),"dealt")).doubleValue()==4,"dégâts PvP enregistrés après protections");
        var death=new PlayerDeathEvent(blue.player,DamageSource.builder(DamageType.PLAYER_ATTACK).withCausingEntity(red.player).withDirectEntity(red.player).build(),new ArrayList<>(),0,"fixture");Bukkit.getPluginManager().callEvent(death);Bukkit.getPluginManager().callEvent(death);
        check((int)field(members.get(red.id),"kills")==1&&(int)field(members.get(blue.id),"deaths")==1,"kill attribué et mort dédupliquée");
        Bukkit.getPluginManager().callEvent(respawn(blue));Bukkit.getPluginManager().callEvent(new PlayerDeathEvent(blue.player,DamageSource.builder(DamageType.LAVA).build(),new ArrayList<>(),0,"nature"));
        check((int)field(members.get(blue.id),"deaths")==2&&(int)field(members.get(red.id),"kills")==1,"mort naturelle compte sans inventer un kill");
        check(!members.containsKey(admin.id),"arbitre exclu des statistiques compétitives");expires.clear();
    }
    @SuppressWarnings("unchecked") private void captures()throws Exception {
        Map<String,Location> goals=(Map<String,Location>)field(companion,"objectives"),spawns=(Map<String,Location>)field(companion,"spawns");
        for(String team:teams){Location goal=spawns.get(team).getBlock().getLocation();for(int x=-2;x<=2;x++)for(int z=-2;z<=2;z++){goal.clone().add(x,-1,z).getBlock().setType(Material.STONE,false);for(int y=0;y<3;y++)goal.clone().add(x,y,z).getBlock().setType(Material.AIR,false);}goal.getBlock().setType(Material.CHEST,false);goals.put(team,goal);command("room","validate",team);}
        command("nextday");Object display=field(companion,"captureDisplay");Actor red=actors.get(0),ally=actors.get(1),blue=actors.get(2);Location goal=goals.get("Bleue");red.at=goal.clone().add(1.5,0,.5);ally.at=goal.clone().add(-.5,0,.5);
        List<Player> attackers=List.of(red.player,ally.player);advance("Bleue",attackers,41);
        Map<?,?> attempts=(Map<?,?>)field(display,"attempts");Object attempt=attempts.get("Bleue");BossBar bar=(BossBar)field(attempt,"bar");
        check(Math.abs(bar.progress()-40f/1200)<.0001,"BossBar suit exactement le CaptureClock");check(red.bars>0&&ally.bars>0&&admin.bars==0,"BossBar visible seulement pour les attaquants éligibles");
        blue.at=goal.clone().add(.5,0,1.5);advance("Bleue",List.of(red.player,ally.player,blue.player),1);check(!attempts.containsKey("Bleue")&&red.bars==0,"contestation retire la barre et remet à zéro");
        advance("Bleue",attackers,21);command("pause");check(attempts.isEmpty()&&red.bars==0,"pause retire toutes les BossBars");command("resume");
        for(String defender:List.of("Bleue","Verte","Jaune")){goal=goals.get(defender);red.at=goal.clone().add(1.5,0,.5);ally.at=goal.clone().add(-.5,0,.5);advance(defender,attackers,1201);check(((Set<?>)field(state,"eliminated")).contains(defender),"capture et élimination "+defender);}
        check("Rouge".equals(field(state,"winner"))&&attempts.isEmpty(),"victoire et interfaces nettoyées");
        Object model=field(field(companion,"statistics"),"model");Map<?,?> members=(Map<?,?>)field(model,"players");check((int)field(members.get(red.id),"captures")==3,"participations aux captures enregistrées une seule fois");
        String id=(String)field(model,"matchId");check(Files.isRegularFile(file("history/"+id+"/result.json"))&&Files.isRegularFile(file("history/"+id+"/result.csv"))&&Files.isRegularFile(file("history/"+id+"/result-teams.csv")),"bilan JSON et CSV joueur/équipe archivés");
    }
    private void advance(String defender,Collection<Player> candidates,int ticks)throws Exception{for(int n=0;n<ticks;n++)call(companion,"advanceCapture",new Class<?>[]{String.class,Collection.class},defender,candidates);}
    private void performance()throws Exception {
        Object places=field(companion,"protectedPlaces"),display=field(companion,"captureDisplay");
        Location neutral=new Location(world,160,200,160);Method contains=places.getClass().getDeclaredMethod("contains",Location.class);contains.setAccessible(true);
        for(int n=0;n<10000;n++)contains.invoke(places,neutral);
        long start=System.nanoTime();for(int n=0;n<100000;n++)contains.invoke(places,neutral);double regionNs=(System.nanoTime()-start)/100000d;
        Class<?> clockClass=Class.forName("fr.fkamis.CaptureClock",true,companion.getClass().getClassLoader());Constructor<?> constructor=clockClass.getDeclaredConstructor();constructor.setAccessible(true);Object clock=constructor.newInstance();set(clock,"attacker","Rouge");set(clock,"elapsedTicks",600);
        Method update=display.getClass().getDeclaredMethod("update",String.class,clockClass,Collection.class,boolean.class);update.setAccessible(true);
        List<Player> viewers=List.of(actors.get(0).player,actors.get(1).player);start=System.nanoTime();for(int n=0;n<2000;n++)update.invoke(display,"mesure-technique",clock,viewers,false);double barNs=(System.nanoTime()-start)/2000d;call(display,"clear",new Class<?>[]{String.class},"mesure-technique");
        Class<?> modelClass=field(field(companion,"statistics"),"model").getClass();Constructor<?> modelConstructor=modelClass.getDeclaredConstructor();modelConstructor.setAccessible(true);Object model=modelConstructor.newInstance();
        for(int n=0;n<16;n++)call(model,"member",new Class<?>[]{UUID.class,String.class,String.class},UUID.nameUUIDFromBytes(("perf"+n).getBytes(StandardCharsets.UTF_8)),"Perf"+n,teams.get(n/4));
        start=System.nanoTime();for(int n=0;n<1000;n++)call(model,"json",new Class<?>[]{});double statisticsNs=(System.nanoTime()-start)/1000d;
        var result=new LinkedHashMap<String,Object>();result.put("regionLookupMeanNsWithReflection",regionNs);result.put("bossBarUpdateTwoSimulatedViewersMeanNs",barNs);result.put("statisticsSerialization16MembersMeanNs",statisticsNs);result.put("heapUsedBytes",java.lang.management.ManagementFactory.getMemoryMXBean().getHeapMemoryUsage().getUsed());result.put("tps",Bukkit.getTPS());result.put("averageMspt",Bukkit.getAverageTickTime());result.put("authenticatedPlayers",0);result.put("scope","Micro-mesures locales, interfaces simulées ; pas une mesure multijoueur ni MineStrator.");
        Files.writeString(output.resolve("vnext-performance.json"),new GsonBuilder().setPrettyPrinting().create().toJson(result)+"\n");check(regionNs>0&&barNs>0&&statisticsNs>0,"coûts techniques régions, BossBar et statistiques mesurés");
    }
    private void restart()throws Exception {
        JsonObject expected=JsonParser.parseString(Files.readString(getDataFolder().toPath().resolve("expected.json"))).getAsJsonObject();Object model=field(field(companion,"statistics"),"model");
        check("Rouge".equals(field(state,"winner")),"victoire persistante après redémarrage");check(expected.get("statistics").getAsString().equals(call(model,"json",new Class<?>[]{})),"statistiques terminées immuables après redémarrage");
        String history=Files.readString(file("history/"+expected.get("matchId").getAsString()+"/result.json"));check(history.equals(expected.get("statistics").getAsString()+"\n"),"historique précédent non réécrit");
        confirmReset();
    }
    private void afterReset()throws Exception {
        check(!(boolean)field(state,"started")&&(int)field(state,"day")==0,"reset logique jour zéro");check(roster.isEmpty()&&((Map<?,?>)field(companion,"objectives")).isEmpty(),"reset retire appartenances et objectifs");
        check(((Map<?,?>)field(companion,"spawns")).size()==4&&FkPI.getInstance().getTeamManager().getTeams().size()==4,"territoires et spawns conservés");
        admin=new Actor("ArbitreVNext",false);check((boolean)call(field(companion,"administrators"),"contains",new Class<?>[]{UUID.class},admin.id),"arbitre conservé après reset");
        check(((Map<?,?>)field(field(field(companion,"statistics"),"model"),"players")).isEmpty(),"nouvelle collecte sans anciennes statistiques");
        try(var history=Files.list(file("history"))){check(history.findAny().isPresent(),"historiques conservés après reset");}
        confirmReset();
    }
    private void confirmReset()throws Exception {
        command("reset","prepare");Object plan=field(field(companion,"resets"),"plan");Method token=plan.getClass().getDeclaredMethod("token");token.setAccessible(true);String value=(String)token.invoke(plan);
        command("reset","confirm",value);check(Files.exists(file("reset-request.json")),"confirmation crée une demande à froid");
        JsonObject request=JsonParser.parseString(Files.readString(file("reset-request.json"))).getAsJsonObject();check(request.get("sourceStateSha256").getAsString().equals(sha(Files.readString(file("state.yml")))),"aucun état vierge appliqué pendant Paper");
        Files.writeString(getDataFolder().toPath().resolve("reset-token.txt"),value);finish();
    }
    private String sha(String text)throws Exception{return HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(text.getBytes(StandardCharsets.UTF_8)));}
    private final class Actor implements InvocationHandler {
        final UUID id;final String name;final boolean op;final Player player;final PlayerInventory inventory;final PersistentDataContainer data;
        final List<String> messages=new ArrayList<>();Location at=new Location(world,160.5,200,160.5);GameMode mode=GameMode.SURVIVAL;int bars;EntityDamageEvent lastDamage;
        Actor(String name,boolean op){this.name=name;this.op=op;id=UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8));Block block=world.getBlockAt(150,200,index++);block.setType(Material.CHEST,false);data=((Chest)block.getState()).getPersistentDataContainer();Inventory storage=Bukkit.createInventory(null,54);
            inventory=(PlayerInventory)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{PlayerInventory.class},(p,m,a)->{if(m.getName().equals("getItemInMainHand")||m.getName().equals("getItemInOffHand"))return new ItemStack(Material.AIR);try{return Inventory.class.getMethod(m.getName(),m.getParameterTypes()).invoke(storage,a);}catch(NoSuchMethodException e){return def(m.getReturnType());}});
            player=(Player)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{Player.class},this);
        }
        @Override public Object invoke(Object proxy,Method method,Object[] args){return switch(method.getName()){
            case "getUniqueId"->id;case "getName","getDisplayName"->name;case "getWorld"->at.getWorld();case "getLocation"->at.clone();case "getEyeLocation"->at.clone().add(0,1.62,0);
            case "getGameMode"->mode;case "getInventory"->inventory;case "getPersistentDataContainer"->data;case "getLastDamageCause"->lastDamage;case "getHealth"->20d;case "isOnline","isValid"->true;case "isOp","hasPermission"->op;
            case "getScoreboard"->Bukkit.getScoreboardManager().getNewScoreboard();case "getServer"->Bukkit.getServer();case "getMetadata"->List.of();
            case "setGameMode"->{var e=new PlayerGameModeChangeEvent(player,(GameMode)args[0]);Bukkit.getPluginManager().callEvent(e);if(!e.isCancelled())mode=e.getNewGameMode();yield null;}
            case "sendMessage"->{if(args!=null&&args.length>0)messages.add(String.valueOf(args[args.length-1]));yield null;}
            case "showBossBar"->{bars++;yield null;}case "hideBossBar"->{bars--;yield null;}
            case "hashCode"->id.hashCode();case "equals"->proxy==args[0];case "toString"->name;default->def(method.getReturnType());};}
    }
    private static Object def(Class<?> t){if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==double.class)return 0d;if(t==float.class)return 0f;return null;}
    private void finish()throws Exception {Files.writeString(output.resolve("vnext-phase-"+phase+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("passed",passed,"authenticatedClients",0,"simulatedPlayerActors",actors.size()))+"\n");getLogger().info("VNEXT PROBE SUCCESS "+passed.size());Bukkit.shutdown();}
    private void fail(Throwable error){getLogger().log(Level.SEVERE,"VNEXT PROBE FAILED",error);Bukkit.shutdown();}
}
