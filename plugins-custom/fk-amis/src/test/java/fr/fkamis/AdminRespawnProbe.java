package fr.fkamis;

import com.google.gson.GsonBuilder;
import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fkpi.FkPI;
import fr.devsylone.fkpi.rules.Rule;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.command.*;
import org.bukkit.damage.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.*;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Événements Paper réels, acteurs Player simulés, jamais neuf connexions authentifiées. */
public final class AdminRespawnProbe extends JavaPlugin {
    private JavaPlugin companion; private Object state,admins; private World world; private Path repo;
    private final List<String> passed=new ArrayList<>();
    private final List<Actor> participants=new ArrayList<>();
    private Actor arbiter;
    private int actorIndex;
    private Object field(Object o,String name)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(o);}
    private void set(Object o,String name,Object value)throws Exception{Field f=o.getClass().getDeclaredField(name);f.setAccessible(true);f.set(o,value);}
    private Object call(Object o,String name,Class<?>[] types,Object...args)throws Exception{Method m=o.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(o,args);}
    private void check(boolean condition,String label){if(!condition)throw new AssertionError(label);passed.add(label);getLogger().info("ADMIN PROBE PASS "+label);}
    private void command(String...args){companion.onCommand(Bukkit.getConsoleSender(),Objects.requireNonNull(companion.getCommand("fka")),"fka",args);}
    @Override public void onEnable(){
        try {
            Path root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();
            if(!root.getFileName().toString().startsWith("probe-admin")||!Boolean.getBoolean("fk.adminprobe"))throw new IllegalStateException("Fixture admin isolée requise.");
            repo=root.getParent().getParent(); companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");
            state=field(companion,"state");admins=field(companion,"administrators");world=Bukkit.getWorld("world");
            Bukkit.getScheduler().runTaskLater(this,()->{try{if(Boolean.getBoolean("fk.adminprobe.restart"))restart();else initial();finish();}catch(Throwable error){fail(error);}},60);
        }catch(Throwable error){fail(error);}
    }
    @SuppressWarnings("unchecked") private void initial()throws Exception{
        check(Bukkit.getOnlinePlayers().isEmpty(),"zéro client authentifié");
        check(Bukkit.getMaxPlayers()==10,"dix places techniques pour huit participants et un arbitre");
        check(FkPI.getInstance().getRulesManager().getRule(Rule.DEATH_LIMIT)==0,"limite de morts native fixée à zéro");
        int tipsTask=(int)field(Fk.getInstance().getTipsManager(),"task");
        check(!Bukkit.getScheduler().isQueued(tipsTask),"tâche périodique native de tips arrêtée");
        check((int)call(field(companion,"nativeAdminBridge"),"size",new Class<?>[]{})>0,"délégation des protections natives installée");
        Actor fresh=new Actor("Nouveau",false);fresh.mode=GameMode.SPECTATOR;
        call(companion,"reconcilePlayer",new Class<?>[]{Player.class},fresh.player);
        check(fresh.mode==GameMode.SURVIVAL,"nouveau visiteur en survie avant attribution");
        Map<UUID,String> roster=(Map<UUID,String>)field(companion,"roster");
        Map<UUID,String> names=(Map<UUID,String>)field(companion,"rosterNames");
        for(String team:List.of("Rouge","Bleue","Verte","Jaune"))for(int n=0;n<2;n++){
            Actor actor=new Actor(team+n,false);participants.add(actor);roster.put(actor.id,team);names.put(actor.id,actor.name);
            FkPI.getInstance().getTeamManager().addPlayer(actor.name,team);
        }
        arbiter=new Actor("Arbitre",false);command("admin","grant",arbiter.id.toString());
        check(!(boolean)call(admins,"contains",new Class<?>[]{UUID.class},arbiter.id),"attribution arbitre sans confirmation refusée");
        command("admin","grant",arbiter.id.toString(),"confirm");
        call(companion,"reconcilePlayer",new Class<?>[]{Player.class},arbiter.player);
        check(arbiter.mode==GameMode.CREATIVE&&arbiter.flight,"arbitre en créatif avec vol");
        check(!roster.containsKey(arbiter.id),"arbitre absent du roster");
        command("admin","grant",participants.getFirst().id.toString(),"confirm");
        check(!(boolean)call(admins,"contains",new Class<?>[]{UUID.class},participants.getFirst().id),"participant ne peut pas devenir arbitre sans retrait explicite");
        List<Actor> nine=new ArrayList<>(participants);nine.add(arbiter);int active=0;
        for(Actor actor:nine)if((boolean)call(companion,"activeParticipant",new Class<?>[]{Player.class},actor.player))active++;
        check(nine.size()==9&&active==8,"neuf acteurs simulés, huit participants comptabilisés");
        check(!(boolean)call(companion,"blocked",new Class<?>[]{Player.class},arbiter.player),"arbitre autorisé pendant installation/pause");
        for(var team:FkPI.getInstance().getTeamManager().getTeams()){
            Block block=team.getBase().getCenter().clone().add(1,2,1).getBlock();block.setType(Material.STONE,false);arbiter.at=block.getLocation();
            BlockBreakEvent destroy=new BlockBreakEvent(block,arbiter.player);Bukkit.getPluginManager().callEvent(destroy);
            check(!destroy.isCancelled(),"arbitre destruction royaume "+team.getName());
            BlockPlaceEvent place=new BlockPlaceEvent(block,block.getState(),block.getRelative(0,-1,0),new ItemStack(Material.STONE),arbiter.player,true,EquipmentSlot.HAND);
            Bukkit.getPluginManager().callEvent(place);check(!place.isCancelled(),"arbitre construction royaume "+team.getName());
        }
        Actor op=new Actor("OperateurOrdinaire",true);op.at=arbiter.at;
        BlockBreakEvent forbidden=new BlockBreakEvent(op.at.getBlock(),op.player);Bukkit.getPluginManager().callEvent(forbidden);
        check(forbidden.isCancelled(),"OP sans rôle ne contourne pas la protection");
        UUID intruder=UUID.nameUUIDFromBytes("Intrus".getBytes(StandardCharsets.UTF_8));
        companion.onCommand(op.player,companion.getCommand("fka"),"fka",new String[]{"admin","grant",intruder.toString(),"confirm"});
        check(!(boolean)call(admins,"contains",new Class<?>[]{UUID.class},intruder),"OP en jeu ne peut pas accorder le rôle console");
        var wrongMode=new PlayerGameModeChangeEvent(arbiter.player,GameMode.SPECTATOR);Bukkit.getPluginManager().callEvent(wrongMode);
        check(wrongMode.isCancelled(),"arbitre ne devient pas spectateur par une transition automatique");
        Map<String,Location> goals=(Map<String,Location>)field(companion,"objectives");
        goals.put("Rouge",arbiter.at.clone());
        var sensitiveBreak=new BlockBreakEvent(arbiter.at.getBlock(),arbiter.player);Bukkit.getPluginManager().callEvent(sensitiveBreak);
        check(sensitiveBreak.isCancelled(),"objectif protégé même pour l'arbitre sans autorisation ciblée");
        Class<?> permitClass=Class.forName("fr.fkamis.Administrators$Permit",true,companion.getClass().getClassLoader());
        var permitConstructor=permitClass.getDeclaredConstructor(Location.class,long.class);permitConstructor.setAccessible(true);
        Map<UUID,Object> permits=(Map<UUID,Object>)field(admins,"permits");
        permits.put(arbiter.id,permitConstructor.newInstance(arbiter.at.clone(),System.nanoTime()+60_000_000_000L));
        var explicit=new BlockBreakEvent(arbiter.at.getBlock(),arbiter.player);Bukkit.getPluginManager().callEvent(explicit);
        check(!explicit.isCancelled(),"autorisation ciblée permet une intervention sensible simulée");
        var used=new BlockBreakEvent(arbiter.at.getBlock(),arbiter.player);Bukkit.getPluginManager().callEvent(used);
        check(used.isCancelled(),"autorisation sensible consommée après une seule action");
        goals.clear();
        var supplyBlock=world.getBlockAt(-100,67,-100);
        var supplyClick=new PlayerInteractEvent(arbiter.player,Action.RIGHT_CLICK_BLOCK,null,supplyBlock,org.bukkit.block.BlockFace.UP,EquipmentSlot.HAND);
        Bukkit.getPluginManager().callEvent(supplyClick);
        check(supplyClick.isCancelled(),"arbitre ne consomme pas un ravitaillement");
        var supplyBreak=new BlockBreakEvent(supplyBlock,arbiter.player);Bukkit.getPluginManager().callEvent(supplyBreak);
        check(supplyBreak.isCancelled(),"site de ravitaillement protégé contre destruction accidentelle");
        var edit=new PlayerCommandPreprocessEvent(arbiter.player,"/fill 0 0 0 10 10 10 air");Bukkit.getPluginManager().callEvent(edit);
        check(edit.isCancelled(),"édition avancée sans événements réservée à la console explicite");
        var move=new PlayerMoveEvent(arbiter.player,arbiter.at,arbiter.at.clone().add(1,0,0));Bukkit.getPluginManager().callEvent(move);
        check(move.getTo().getX()!=move.getFrom().getX(),"arbitre libre de se déplacer en pause");
        World end=Bukkit.getWorlds().stream().filter(w->w.getEnvironment()==World.Environment.THE_END).findFirst().orElseThrow();
        var teleport=new PlayerTeleportEvent(arbiter.player,arbiter.at,end.getSpawnLocation(),PlayerTeleportEvent.TeleportCause.COMMAND);
        Bukkit.getPluginManager().callEvent(teleport);check(!teleport.isCancelled(),"arbitre accès dimension fermée");
        var invulnerable=new EntityDamageEvent(arbiter.player,EntityDamageEvent.DamageCause.LAVA,8);Bukkit.getPluginManager().callEvent(invulnerable);
        check(invulnerable.isCancelled(),"arbitre hors des dégâts PvE");
        set(state,"started",true);set(state,"day",1);set(state,"paused",false);call(companion,"syncNative",new Class<?>[]{});
        call(companion,"onQuit",new Class<?>[]{PlayerQuitEvent.class},new PlayerQuitEvent(arbiter.player,"fixture"));
        check(!(boolean)field(state,"paused"),"déconnexion arbitre ne met pas en pause");
        Actor red=participants.getFirst();
        var neutral=new EntityDamageByEntityEvent(arbiter.player,red.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK,4);Bukkit.getPluginManager().callEvent(neutral);
        check(neutral.isCancelled(),"arbitre ne blesse pas les participants");
        for(EntityDamageEvent.DamageCause cause:List.of(EntityDamageEvent.DamageCause.ENTITY_ATTACK,EntityDamageEvent.DamageCause.LAVA,
                EntityDamageEvent.DamageCause.FALL,EntityDamageEvent.DamageCause.PROJECTILE,EntityDamageEvent.DamageCause.ENTITY_EXPLOSION)){
            DamageSource source=DamageSource.builder(switch(cause){case LAVA->DamageType.LAVA;case FALL->DamageType.FALL;default->DamageType.GENERIC;}).build();
            var death=new PlayerDeathEvent(red.player,source,new ArrayList<>(),0,"mort fixture");
            Bukkit.getPluginManager().callEvent(death);
            call(companion,"reconcilePlayer",new Class<?>[]{Player.class},red.player);
            check(red.mode==GameMode.SURVIVAL&&((Set<?>)field(state,"eliminated")).isEmpty(),"mort/réapparition illimitée "+cause);
        }
        set(state,"day",3);
        for(int i=0;i<10;i++){
            Bukkit.getPluginManager().callEvent(new PlayerDeathEvent(red.player,DamageSource.builder(DamageType.FALL).build(),new ArrayList<>(),0,"fixture"));
            call(companion,"reconcilePlayer",new Class<?>[]{Player.class},red.player);
        }
        check(red.mode==GameMode.SURVIVAL&&((Set<?>)field(state,"eliminated")).isEmpty(),"dix morts successives aucune élimination");
        check((int)field(state,"day")==3,"morts pendant assaut ne changent pas le jour");
        set(state,"day",1);
        Location bed=new Location(world,10.5,100,10.5);var respawn=new PlayerRespawnEvent(red.player,bed,true);
        Bukkit.getPluginManager().callEvent(respawn);check(respawn.getRespawnLocation().equals(bed),"lit personnel valide conservé");
        // Le probe de phases existant vérifie le seuil de capture et la victoire, sans changement de moteur.
        call(companion,"eliminate",new Class<?>[]{String.class},"Rouge");
        call(companion,"reconcilePlayer",new Class<?>[]{Player.class},red.player);
        check(red.mode==GameMode.SPECTATOR,"capture validée joueur en spectateur");
        Bukkit.getPluginManager().callEvent(new PlayerDeathEvent(red.player,DamageSource.builder(DamageType.FALL).build(),new ArrayList<>(),0,"fixture"));
        call(companion,"reconcilePlayer",new Class<?>[]{Player.class},red.player);
        check(red.mode==GameMode.SPECTATOR,"éliminé reste spectateur après mort et reconnexion");
        call(companion,"reconcilePlayer",new Class<?>[]{Player.class},arbiter.player);
        check(arbiter.mode==GameMode.CREATIVE&&!((Set<?>)field(state,"eliminated")).contains(null),"arbitre non éliminé après capture");
        call(companion,"saveState",new Class<?>[]{});
        Files.writeString(getDataFolder().toPath().resolve("expected.json"),"{\"admin\":\""+arbiter.id+"\",\"red\":\""+red.id+"\"}",StandardCharsets.UTF_8);
    }
    private void restart()throws Exception{
        var expected=com.google.gson.JsonParser.parseString(Files.readString(getDataFolder().toPath().resolve("expected.json"))).getAsJsonObject();
        Actor red=new Actor("Rouge0",false),admin=new Actor("Arbitre",false);
        check(((Set<?>)field(state,"eliminated")).contains("Rouge"),"élimination persistante après redémarrage");
        check((boolean)call(admins,"contains",new Class<?>[]{UUID.class},UUID.fromString(expected.get("admin").getAsString())),"autorisation UUID persistante");
        call(companion,"reconcilePlayer",new Class<?>[]{Player.class},red.player);call(companion,"reconcilePlayer",new Class<?>[]{Player.class},admin.player);
        check(red.mode==GameMode.SPECTATOR&&admin.mode==GameMode.CREATIVE,"reprise spectateur éliminé et créatif arbitre");
        check(FkPI.getInstance().getRulesManager().getRule(Rule.DEATH_LIMIT)==0,"reprise toujours sans limite de vies");
        check(!Bukkit.getScheduler().isQueued((int)field(Fk.getInstance().getTipsManager(),"task")),"reprise tips toujours désactivés");
        command("admin","revoke",admin.id.toString(),"confirm");
        check(!(boolean)call(admins,"contains",new Class<?>[]{UUID.class},admin.id),"révocation rôle persistée");
    }
    private final class Actor implements InvocationHandler{
        final String name;final UUID id;final Player player;final PlayerInventory inventory;final boolean op;final PersistentDataContainer data;
        Location at=new Location(world,0.5,100,0.5);GameMode mode=GameMode.SURVIVAL;boolean flight;
        Actor(String name,boolean op){this.name=name;this.op=op;id=UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8));
            Block container=world.getBlockAt(44,200,actorIndex++);container.setType(Material.CHEST,false);data=((org.bukkit.block.Chest)container.getState()).getPersistentDataContainer();
            Inventory storage=Bukkit.createInventory(null,54);
            inventory=(PlayerInventory)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{PlayerInventory.class},(p,m,a)->{
                if(m.getName().equals("getItemInMainHand")||m.getName().equals("getItemInOffHand"))return new ItemStack(Material.AIR);
                try{return Inventory.class.getMethod(m.getName(),m.getParameterTypes()).invoke(storage,a);}catch(NoSuchMethodException ex){return def(m.getReturnType());}});
            player=(Player)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{Player.class},this);
        }
        @Override public Object invoke(Object proxy,Method m,Object[] args){return switch(m.getName()){
            case "getName","getDisplayName"->name;case "getUniqueId"->id;case "getWorld"->at.getWorld();case "getLocation"->at.clone();case "getEyeLocation"->at.clone().add(0,1.6,0);
            case "getGameMode"->mode;case "getInventory"->inventory;case "getPersistentDataContainer"->data;case "getScoreboard"->Bukkit.getScoreboardManager().getNewScoreboard();case "getServer"->Bukkit.getServer();
            case "isOp","hasPermission"->op;case "isOnline"->true;case "getHealth"->20d;case "getAllowFlight"->flight;
            case "setAllowFlight"->{flight=(boolean)args[0];yield null;}
            case "setGameMode"->{var e=new PlayerGameModeChangeEvent(player,(GameMode)args[0]);Bukkit.getPluginManager().callEvent(e);if(!e.isCancelled())mode=e.getNewGameMode();yield null;}
            case "hasLineOfSight"->true;case "getMetadata"->List.of();case "hashCode"->id.hashCode();case "equals"->proxy==args[0];case "toString"->name;
            default->def(m.getReturnType());};}
    }
    private static Object def(Class<?> type){if(type==boolean.class)return false;if(type==int.class)return 0;if(type==long.class)return 0L;if(type==double.class)return 0d;if(type==float.class)return 0f;return null;}
    private void finish()throws Exception{
        Files.createDirectories(repo.resolve("tests/results"));
        String phase=Boolean.getBoolean("fk.adminprobe.restart")?"restart":"initial";
        var report=new LinkedHashMap<String,Object>();report.put("passed",passed);report.put("authenticatedPlayers",0);report.put("simulatedPlayers",9);
        report.put("note","Événements et données serveur réels ; neuf interfaces Player sans clients ni connexions authentifiées.");
        Files.writeString(repo.resolve("tests/results/admin-respawn-"+phase+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(report)+"\n",StandardCharsets.UTF_8);
        getLogger().info("ADMIN PROBE SUCCESS "+passed.size());Bukkit.shutdown();
    }
    private void fail(Throwable error){getLogger().log(Level.SEVERE,"ADMIN PROBE FAILED",error);Bukkit.shutdown();}
}
