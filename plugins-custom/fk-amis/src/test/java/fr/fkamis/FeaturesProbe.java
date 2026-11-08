package fr.fkamis;

import com.google.gson.GsonBuilder;
import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fkpi.FkPI;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.command.CommandSender;
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

/** Recette des huit demandes sur Paper réel ; Player sont des doubles, sans réseau. */
public final class FeaturesProbe extends JavaPlugin {
    private JavaPlugin companion; private Object state; private World world; private int size,phase;
    private Map<UUID,String> roster; private Map<String,Location> objectives,spawns;
    private final List<Actor> actors=new ArrayList<>(); private final List<String> passed=new ArrayList<>();
    private Actor admin; private int index; private boolean veto;
    private final List<String> teams=List.of("Rouge","Bleue","Verte","Jaune");
    private Object field(Object o,String n)throws Exception { Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o); }
    private void set(Object o,String n,Object v)throws Exception { Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v); }
    private Object call(Object o,String n,Class<?>[] t,Object...a)throws Exception { Method m=o.getClass().getDeclaredMethod(n,t);m.setAccessible(true);return m.invoke(o,a); }
    private void check(boolean ok,String label) { if(!ok)throw new AssertionError(label);passed.add(label);getLogger().info("FEATURES PROBE PASS "+label); }
    private void command(String...a) { companion.onCommand(Bukkit.getConsoleSender(),companion.getCommand("fka"),"fka",a); }
    private void later(Runnable run) { Bukkit.getScheduler().runTaskLater(this,()->{try{run.run();}catch(Throwable e){fail(e);}},20); }
    @Override @SuppressWarnings("unchecked") public void onEnable() {
        try {
            if(!Boolean.getBoolean("fk.featuresprobe") || !Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize().getFileName().toString().startsWith("probe-features")) throw new IllegalStateException("Copie de recette isolée requise.");
            companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");state=field(companion,"state");world=Bukkit.getWorld("world");
            size=Integer.getInteger("fk.featuresprobe.size",2);phase=Integer.getInteger("fk.featuresprobe.phase",0);
            roster=(Map<UUID,String>)field(companion,"roster");objectives=(Map<String,Location>)field(companion,"objectives");spawns=(Map<String,Location>)field(companion,"spawns");
            Bukkit.getPluginManager().registerEvents(new Listener(){@EventHandler(priority=EventPriority.HIGH) public void block(BlockPlaceEvent e){if(veto)e.setCancelled(true);}},this);
            Bukkit.getScheduler().runTaskLater(this,()->{try{if(Boolean.getBoolean("fk.featuresprobe.baseline"))baseline();else if(phase==0)lobby();else if(phase==1)initial();else restart();}catch(Throwable e){fail(e);}},40);
        }catch(Throwable e){fail(e);}
    }
    @SuppressWarnings("unchecked") private void baseline()throws Exception {
        Actor red=new Actor("RougeBaseline"),blue=new Actor("BleueBaseline");actors.add(red);actors.add(blue);
        for(Actor actor:actors) {String team=actor==red?"Rouge":"Bleue";roster.put(actor.id,team);((Map<UUID,String>)field(companion,"rosterNames")).put(actor.id,actor.name);FkPI.getInstance().getTeamManager().addPlayer(actor.name,team);}
        set(state,"started",true);phase(1,false);
        Skeleton skeleton=world.spawn(new Location(world,25,200,20),Skeleton.class);skeleton.setAI(false);
        Arrow arrow=world.spawn(new Location(world,25,201,20),Arrow.class);arrow.setShooter(skeleton);
        check(!hit(arrow,blue.player,DamageType.ARROW,skeleton).isCancelled(),"ancien JAR autorise flèche squelette avec DamageSource réel J1");
        check(call(field(companion,"damageAttribution"),"damageOwner",new Class<?>[]{EntityDamageEvent.class},hit(arrow,blue.player,DamageType.ARROW,skeleton))==null,"ancien JAR identifie le tireur squelette comme PvE");
        check(hit(red.player,blue.player,DamageType.PLAYER_ATTACK,red.player).isCancelled(),"ancien JAR bloque PvP J1");
        Arrow playerArrow=world.spawn(new Location(world,25,201,21),Arrow.class);playerArrow.setShooter(red.player);
        check(hit(playerArrow,blue.player,DamageType.ARROW,red.player).isCancelled(),"ancien JAR bloque flèche joueur J1");
        phase(1,true);check(hit(arrow,blue.player,DamageType.ARROW,skeleton).isCancelled(),"ancien JAR bloque flèche squelette en pause");
        for(Entity entity:List.of(skeleton,arrow,playerArrow))entity.remove();finish();
    }
    private void lobby()throws Exception {
        check(Bukkit.getOnlinePlayers().isEmpty(),"aucun compte authentifié");
        check(!(boolean)field(state,"started") && world.getDifficulty()==Difficulty.NORMAL,"jour zéro difficulté NORMAL");
        check(Boolean.FALSE.equals(world.getGameRuleValue(GameRules.LOCATOR_BAR)),"locator_bar désactivé avant partie");
        check(Boolean.FALSE.equals(world.getGameRuleValue(GameRules.SPAWN_MOBS)),"spawn_mobs désactivé avant partie");
        check(Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"minecraft:gamerule minecraft:locator_bar false"),"syntaxe console namespacée locator_bar reconnue 26.3");
        Location at=(Location)call(field(companion,"centralSpawn"),"resolve",new Class<?>[]{});
        set(state,"started",true); Cow cow=world.spawn(at,Cow.class); cow.setPersistent(true);cow.setRemoveWhenFarAway(false);cow.customName(net.kyori.adventure.text.Component.text("Gardien QA"));
        cow.setSilent(true);cow.setAI(true);cow.setInvulnerable(false); set(state,"started",false);
        ArmorStand stand=world.spawn(at.clone().add(3,0,0),ArmorStand.class);TextDisplay display=world.spawn(at.clone().add(3,1,0),TextDisplay.class);
        call(field(companion,"lobbyMobs"),"synchronize",new Class<?>[]{});
        check(cow.isValid() && !cow.hasAI() && cow.isInvulnerable(),"mob existant suspendu sans suppression");
        check(stand.isValid() && display.isValid(),"armor stand et display préservés");
        for(var reason:List.of(CreatureSpawnEvent.SpawnReason.NATURAL,CreatureSpawnEvent.SpawnReason.SPAWNER,CreatureSpawnEvent.SpawnReason.BREEDING,CreatureSpawnEvent.SpawnReason.SPAWNER_EGG)) {
            var event=new CreatureSpawnEvent(cow,reason);Bukkit.getPluginManager().callEvent(event);check(event.isCancelled(),"spawn bloqué jour zéro "+reason);
        }
        Files.createDirectories(getDataFolder().toPath());Files.writeString(getDataFolder().toPath().resolve("cow.txt"),cow.getUniqueId().toString());
        announceChecks("avant départ");finish();
    }
    @SuppressWarnings("unchecked") private void initial()throws Exception {
        UUID id=UUID.fromString(Files.readString(getDataFolder().toPath().resolve("cow.txt")));Location center=(Location)call(field(companion,"centralSpawn"),"resolve",new Class<?>[]{});
        world.getChunkAt(center); Cow cow=(Cow)Bukkit.getEntity(id);
        check(cow!=null && !cow.hasAI() && cow.isInvulnerable(),"suspension mob et UUID conservés après redémarrage J0");
        check(Boolean.FALSE.equals(world.getGameRuleValue(GameRules.LOCATOR_BAR)),"locator_bar persistant après redémarrage");
        for(String team:teams) for(int n=0;n<size;n++) {
            Actor actor=new Actor(team+n);actors.add(actor);roster.put(actor.id,team);((Map<UUID,String>)field(companion,"rosterNames")).put(actor.id,actor.name);
            FkPI.getInstance().getTeamManager().addPlayer(actor.name,team);
        }
        admin=new Actor("ArbitreQA");command("admin","grant",admin.id.toString(),"confirm");call(companion,"applyMode",new Class<?>[]{Player.class},admin.player);
        check(admin.mode==GameMode.CREATIVE && !roster.containsKey(admin.id),"arbitre UUID indépendant du format "+size);
        command("start");check(!(boolean)field(state,"started"),"start normal refuse les acteurs non connectés réellement");
        check(roster.size()==4*size && (long)call(companion,"teamSize",new Class<?>[]{String.class},"Rouge")==size,"quatre équipes complètes format "+size);
        call(field(companion,"teamTeleports"),"begin",new Class<?>[]{CommandSender.class,boolean.class,Collection.class},Bukkit.getConsoleSender(),false,actors.stream().map(a->a.player).toList());
        later(()->{try {
            check(actors.stream().allMatch(a->a.teleported==1),"tpall fonctionne pour "+(4*size)+" acteurs");
            // Le moteur est lancé avec les effectifs officiels ; aucun faux client n'est ajouté à Bukkit.
            call(state,"start",new Class<?>[]{Collection.class,boolean.class,int.class},List.of(size,size,size,size),false,size);
            call(companion,"syncNative",new Class<?>[]{});
            check(cow.isValid() && cow.hasAI() && !cow.isInvulnerable() && cow.isSilent(),"mob restauré au départ avec UUID et propriétés d'origine");
            check(Boolean.TRUE.equals(world.getGameRuleValue(GameRules.SPAWN_MOBS)) && world.getDifficulty()==Difficulty.NORMAL,"spawn naturel réactivé au départ NORMAL");
            var spawn=new CreatureSpawnEvent(cow,CreatureSpawnEvent.SpawnReason.NATURAL);Bukkit.getPluginManager().callEvent(spawn);check(!spawn.isCancelled(),"spawn de mob autorisé après départ");
            check(Boolean.FALSE.equals(world.getGameRuleValue(GameRules.LOCATOR_BAR)),"locator_bar reste désactivé au lancement");
            gameplay();
        }catch(Throwable error){fail(error);}});
    }
    private void phase(int day,boolean pause)throws Exception {set(state,"day",day);set(state,"paused",pause);call(companion,"syncNative",new Class<?>[]{});}
    private EntityDamageByEntityEvent hit(Entity source,Player victim,DamageType type,Entity causing) {
        DamageSource damage=DamageSource.builder(type).withDirectEntity(source).withCausingEntity(causing).build();
        var event=new EntityDamageByEntityEvent(source,victim,source instanceof Projectile?EntityDamageEvent.DamageCause.PROJECTILE:EntityDamageEvent.DamageCause.ENTITY_ATTACK,damage,4);
        Bukkit.getPluginManager().callEvent(event);return event;
    }
    private BlockPlaceEvent place(Actor actor,Block block) {
        var event=new BlockPlaceEvent(block,block.getState(),block.getRelative(0,-1,0),new ItemStack(block.getType()),actor.player,true,EquipmentSlot.HAND);Bukkit.getPluginManager().callEvent(event);return event;
    }
    private void gameplay()throws Exception {
        Actor red=actors.getFirst(),blue=actors.get(size);red.at=new Location(world,20.5,200,20.5);blue.at=new Location(world,23.5,200,20.5);
        Skeleton skeleton=world.spawn(new Location(world,25,200,20),Skeleton.class);skeleton.setAI(false);
        Arrow mobArrow=world.spawn(new Location(world,25,201,20),Arrow.class);mobArrow.setShooter(skeleton);
        check(!hit(mobArrow,blue.player,DamageType.ARROW,skeleton).isCancelled(),"J1 flèche squelette avec DamageSource ARROW autorisée");
        check(call(field(companion,"damageAttribution"),"damageOwner",new Class<?>[]{EntityDamageEvent.class},hit(mobArrow,blue.player,DamageType.ARROW,skeleton))==null,"flèche squelette attribuée PvE sans UUID joueur");
        check(!hit(mobArrow,blue.player,DamageType.ARROW,red.player).isCancelled(),"tireur squelette prioritaire sur source joueur incohérente");
        Arrow playerArrow=world.spawn(new Location(world,25,201,21),Arrow.class);playerArrow.setShooter(red.player);
        check(hit(playerArrow,blue.player,DamageType.ARROW,red.player).isCancelled(),"J1 flèche joueur interdite");
        check(hit(red.player,blue.player,DamageType.PLAYER_ATTACK,red.player).isCancelled(),"J1 mêlée PvP interdite");
        phase(2,false);check(!hit(playerArrow,blue.player,DamageType.ARROW,red.player).isCancelled(),"J2 flèche PvP neutre autorisée");
        blue.at=spawns.get("Bleue").clone();check(hit(playerArrow,blue.player,DamageType.ARROW,red.player).isCancelled(),"J2 PvP base protégée");
        phase(1,true);check(hit(mobArrow,blue.player,DamageType.ARROW,skeleton).isCancelled(),"pause bloque flèche PvE");
        for(Entity entity:List.of(skeleton,mobArrow,playerArrow))entity.remove();
        Block neutral=world.getBlockAt(22,200,22);neutral.setType(Material.STONE,false);
        for(int day=1;day<=3;day++) {
            phase(day,false);check(!place(red,neutral).isCancelled(),"construction neutre J"+day);
            var destroy=new BlockBreakEvent(neutral,red.player);Bukkit.getPluginManager().callEvent(destroy);check(!destroy.isCancelled(),"minage neutre J"+day);
        }
        neutral.setType(Material.CHEST,false);check(!place(red,neutral).isCancelled(),"coffre ordinaire neutre autorisé");
        veto=true;check(place(red,neutral).isCancelled(),"annulation d'un autre plugin conservée en zone neutre");veto=false;
        Block own=spawns.get("Rouge").clone().add(2,0,0).getBlock();own.setType(Material.STONE,false);check(!place(red,own).isCancelled(),"construction propre base autorisée");
        Block enemy=spawns.get("Bleue").clone().add(2,0,0).getBlock();enemy.setType(Material.STONE,false);
        check(place(red,enemy).isCancelled(),"construction ordinaire ennemie interdite J3");
        var breaking=new BlockBreakEvent(enemy,red.player);Bukkit.getPluginManager().callEvent(breaking);check(breaking.isCancelled(),"minage ennemi interdit J3");
        phase(1,true);check(place(red,neutral).isCancelled(),"construction refusée en pause");
        phase(1,false);red.mode=GameMode.SPECTATOR;check(place(red,neutral).isCancelled(),"construction refusée en spectateur");red.mode=GameMode.SURVIVAL;
        respawns();announceChecks("active");phase(1,true);announceChecks("pause");phase(3,false);capture();
    }
    private void respawns()throws Exception {
        Actor red=actors.getFirst();Object central=field(companion,"centralSpawn");Location safe=(Location)call(central,"resolve",new Class<?>[]{});
        check((boolean)call(central,"safe",new Class<?>[]{Location.class},safe),"centre naturel sûr carré 3x3");
        check(Math.abs(safe.getX())<=16.5 && Math.abs(safe.getZ())<=16.5,"centre proche de X0 Z0");
        Location original=spawns.get("Rouge").clone();
        for(String context:List.of("sans lit","lit détruit","base","neutre","assaut")) {
            var event=new PlayerRespawnEvent(red.player,original,false);Bukkit.getPluginManager().callEvent(event);
            check(event.getRespawnLocation().equals(safe),"respawn central "+context);
        }
        var bed=new PlayerRespawnEvent(red.player,original,true);Bukkit.getPluginManager().callEvent(bed);check(bed.getRespawnLocation().equals(original),"lit vanilla valide conservé");
        var adminRespawn=new PlayerRespawnEvent(admin.player,original,false);Bukkit.getPluginManager().callEvent(adminRespawn);check(adminRespawn.getRespawnLocation().equals(original),"arbitre exclu du respawn participant");
        check(spawns.get("Rouge").equals(original),"spawn initial équipe intact après morts");
        Block floor=safe.clone().subtract(0,1,0).getBlock();Material previous=floor.getType();floor.setType(Material.LAVA,false);
        check(!(boolean)call(central,"safe",new Class<?>[]{Location.class},safe),"centre lave rejeté");floor.setType(previous,false);
        Block feet=safe.getBlock();feet.setType(Material.WATER,false);check(!(boolean)call(central,"safe",new Class<?>[]{Location.class},safe),"centre eau rejeté");feet.setType(Material.STONE,false);
        check(!(boolean)call(central,"safe",new Class<?>[]{Location.class},safe),"centre obstrué rejeté");feet.setType(Material.AIR,false);
    }
    private void announceChecks(String context)throws Exception {
        Object service=field(companion,"announcements");Actor viewer=actors.isEmpty()?new Actor("Lecteur"):actors.getFirst();int old=viewer.titles;
        call(service,"send",new Class<?>[]{CommandSender.class,String.class,Collection.class},Bukkit.getConsoleSender(),"Événement spécial à l'arène !",List.of(viewer.player));
        check(viewer.titles==old+1 && viewer.sounds>0 && viewer.chat>0,"annonce console titre/chat/son "+context);
        int count=viewer.titles;
        try {call(service,"send",new Class<?>[]{CommandSender.class,String.class,Collection.class},viewer.player,"Non autorisé",List.of(viewer.player));}catch(InvocationTargetException expected){}
        check(viewer.titles==count,"annonce ordinaire refusée "+context);
        command("announce","a".repeat(241));check(viewer.titles==count,"annonce trop longue refusée "+context);
        if(admin!=null) {call(service,"send",new Class<?>[]{CommandSender.class,String.class,Collection.class},admin.player,"Message arbitre",List.of(viewer.player));check(viewer.titles==count+1,"annonce arbitre UUID "+context);}
    }
    @SuppressWarnings("unchecked") private void capture()throws Exception {
        Set<String> validated=(Set<String>)field(companion,"validated");
        for(String team:teams) {
            Location at=spawns.get(team).getBlock().getLocation();
            for(int x=-3;x<=3;x++)for(int z=-3;z<=3;z++){at.clone().add(x,-1,z).getBlock().setType(Material.STONE,false);for(int y=0;y<5;y++)at.clone().add(x,y,z).getBlock().setType(Material.AIR,false);}
            at.getBlock().setType(Material.CHEST,false);objectives.put(team,at);validated.add(team);
        }
        check((boolean)call(companion,"roomValid",new Class<?>[]{String.class},"Bleue"),"salle validée avec géométrie accessible");
        Actor red=actors.getFirst();Location goal=objectives.get("Bleue");
        List<Player> attack=new ArrayList<>();for(int n=0;n<Math.min(2,size);n++){Actor actor=actors.get(n);actor.at=goal.clone().add(n==0?1.5:-.5,0,.5);actor.at.setYaw(180);attack.add(actor.player);}
        check((int)call(companion,"requiredAttackers",new Class<?>[]{String.class},"Rouge")==Math.min(2,size),"seuil basé sur effectif officiel format "+size);
        advance("Bleue",attack,21);Object clock=((Map<?,?>)field(companion,"captures")).get("Bleue");
        check((int)field(clock,"elapsedTicks")==20,"capture progresse dos au coffre sans hasLineOfSight");
        if(size>=3) {
            Actor extra=actors.get(2);extra.at=new Location(world,20.5,200,20.5);
            Bukkit.getPluginManager().callEvent(new PlayerMoveEvent(extra.player,extra.at,extra.at.clone().add(1,0,0)));
            check((int)field(clock,"elapsedTicks")==20,"allié supplémentaire hors rayon ne réinitialise pas la capture");
        }
        Actor remoteDefender=actors.get(size);remoteDefender.at=new Location(world,30.5,200,30.5);
        Bukkit.getPluginManager().callEvent(new PlayerDeathEvent(remoteDefender.player,DamageSource.builder(DamageType.FALL).build(),new ArrayList<>(),0,"fixture hors salle"));
        check((int)field(clock,"elapsedTicks")==20,"mort d'un défenseur éloigné ne réinitialise pas une capture");
        red.at.add(10,0,0);advance("Bleue",attack,1);check((int)field(clock,"elapsedTicks")==0,"sortie rayon interrompt sans réduire le seuil");red.at=goal.clone().add(1.5,0,.5);
        red.dead=true;advance("Bleue",attack,2);check((int)field(clock,"elapsedTicks")==0,"mort attaquant interrompt");red.dead=false;
        red.online=false;advance("Bleue",attack,2);check((int)field(clock,"elapsedTicks")==0,"déconnexion attaquant ne réduit pas le seuil officiel");red.online=true;
        Actor defender=actors.get(size);defender.at=goal.clone().add(.5,0,1.5);List<Player> contested=new ArrayList<>(attack);contested.add(defender.player);advance("Bleue",contested,2);check((int)field(clock,"elapsedTicks")==0,"défenseur conteste");
        Actor green=actors.get(2*size);green.at=defender.at;List<Player> mixed=new ArrayList<>(attack);mixed.add(green.player);advance("Bleue",mixed,2);check((int)field(clock,"elapsedTicks")==0,"deux équipes attaquantes interrompent");
        red.at=goal.clone().add(2.5,0,.5);for(int z=-3;z<=3;z++)for(int y=0;y<3;y++)goal.clone().add(1,y,z).getBlock().setType(Material.STONE,false);
        advance("Bleue",attack,2);check((int)field(clock,"elapsedTicks")==0,"capture à travers paroi pleine refusée");
        for(int z=-3;z<=3;z++)for(int y=0;y<3;y++)goal.clone().add(1,y,z).getBlock().setType(Material.AIR,false);
        red.at=goal.clone().add(1.5,2,.5);advance("Bleue",attack,2);check((int)field(clock,"elapsedTicks")==0,"capture depuis autre étage refusée");
        red.at=goal.clone().add(1.5,0,.5);admin.at=red.at;advance("Bleue",List.of(admin.player),2);check((int)field(clock,"elapsedTicks")==0,"arbitre jamais attaquant");
        red.mode=GameMode.SPECTATOR;advance("Bleue",attack,2);check((int)field(clock,"elapsedTicks")==0,"spectateur jamais attaquant");red.mode=GameMode.SURVIVAL;
        advance("Bleue",attack,21);command("pause");check((int)field(clock,"elapsedTicks")==0,"pause réinitialise capture");command("resume");
        advance("Bleue",attack,21);check((int)field(clock,"elapsedTicks")==20,"capture en cours avant redémarrage");
        call(companion,"saveState",new Class<?>[]{});finish();
    }
    private void advance(String defender,Collection<Player> attack,int ticks)throws Exception {for(int n=0;n<ticks;n++)call(companion,"advanceCapture",new Class<?>[]{String.class,Collection.class},defender,attack);}
    @SuppressWarnings("unchecked") private void restart()throws Exception {
        check((boolean)field(state,"paused") && (int)field(state,"day")==3,"redémarrage en pause jour3");
        check(((Map<?,?>)field(companion,"captures")).isEmpty(),"capture partielle abandonnée au redémarrage");
        check(roster.size()==4*size,"UUID et équipes du format conservés après redémarrage");
        check(Boolean.FALSE.equals(world.getGameRuleValue(GameRules.LOCATOR_BAR)) && Boolean.TRUE.equals(world.getGameRuleValue(GameRules.SPAWN_MOBS)),"gamerules correctes après redémarrage en partie");
        for(String team:teams)for(int n=0;n<size;n++)actors.add(new Actor(team+n));
        admin=new Actor("ArbitreQA");call(companion,"applyMode",new Class<?>[]{Player.class},admin.player);check(admin.mode==GameMode.CREATIVE,"arbitre persistant après redémarrage");
        command("resume");
        for(String defender:List.of("Bleue","Verte","Jaune")) {
            Location goal=objectives.get(defender);List<Player> attack=new ArrayList<>();
            for(int n=0;n<Math.min(2,size);n++){Actor actor=actors.get(n);actor.at=goal.clone().add(n==0?1.5:-.5,0,.5);attack.add(actor.player);}
            advance(defender,attack,1201);check(((Set<?>)field(state,"eliminated")).contains(defender),"capture complète 60s élimine "+defender+" format "+size);
            Actor eliminated=actors.get(teams.indexOf(defender)*size);call(companion,"applyMode",new Class<?>[]{Player.class},eliminated.player);
            check(eliminated.mode==GameMode.SPECTATOR,"éliminé reste spectateur "+defender);
            var respawn=new PlayerRespawnEvent(eliminated.player,spawns.get(defender),false);Bukkit.getPluginManager().callEvent(respawn);call(companion,"applyMode",new Class<?>[]{Player.class},eliminated.player);
            check(eliminated.mode==GameMode.SPECTATOR,"mort après capture conserve spectateur "+defender);
        }
        check("Rouge".equals(field(state,"winner")) && (boolean)field(state,"paused"),"victoire du dernier royaume format "+size);
        call(companion,"saveState",new Class<?>[]{});finish();
    }
    private final class Actor implements InvocationHandler {
        final UUID id;final String name;final Player player;final PlayerInventory inventory;final PersistentDataContainer data;
        Location at=new Location(world,20.5,200,20.5);GameMode mode=GameMode.SURVIVAL;boolean dead,online=true;int titles,sounds,chat,teleported;
        Actor(String name) {this.name=name;id=UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8));
            Block chest=world.getBlockAt(44,200,index++);chest.setType(Material.CHEST,false);data=((Chest)chest.getState()).getPersistentDataContainer();Inventory storage=Bukkit.createInventory(null,54);
            inventory=(PlayerInventory)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{PlayerInventory.class},(p,m,a)->{if(m.getName().equals("getItemInMainHand")||m.getName().equals("getItemInOffHand"))return new ItemStack(Material.AIR);try{return Inventory.class.getMethod(m.getName(),m.getParameterTypes()).invoke(storage,a);}catch(NoSuchMethodException e){return def(m.getReturnType());}});
            player=(Player)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{Player.class},this);
        }
        @Override public Object invoke(Object proxy,Method method,Object[] args) {return switch(method.getName()) {
            case "getName","getDisplayName"->name;case "getUniqueId"->id;case "getWorld"->at.getWorld();case "getLocation"->at.clone();case "getEyeLocation"->at.clone().add(0,1.62,0);
            case "getGameMode"->mode;case "getInventory"->inventory;case "getPersistentDataContainer"->data;case "getEntityId"->Math.abs(id.hashCode());case "getMetadata"->List.of();case "getServer"->Bukkit.getServer();case "getScoreboard"->Bukkit.getScoreboardManager().getNewScoreboard();
            case "isOnline"->online;case "isDead"->dead;case "isValid"->true;case "getHealth"->20d;case "hasLineOfSight"->throw new AssertionError("aucun appel de ligne de vue autorisé");
            case "setGameMode"->{var event=new PlayerGameModeChangeEvent(player,(GameMode)args[0]);Bukkit.getPluginManager().callEvent(event);if(!event.isCancelled())mode=event.getNewGameMode();yield null;}
            case "teleport"->{var event=new PlayerTeleportEvent(player,at,(Location)args[0],PlayerTeleportEvent.TeleportCause.PLUGIN);Bukkit.getPluginManager().callEvent(event);if(!event.isCancelled()){at=event.getTo();teleported++;}yield !event.isCancelled();}
            case "showTitle"->{titles++;yield null;}case "playSound"->{sounds++;yield null;}case "sendMessage"->{chat++;yield null;}
            case "hashCode"->id.hashCode();case "equals"->proxy==args[0];case "toString"->name;default->def(method.getReturnType());};}
    }
    private static Object def(Class<?> t){if(t==boolean.class)return false;if(t==int.class)return 0;if(t==long.class)return 0L;if(t==double.class)return 0d;if(t==float.class)return 0f;return null;}
    private void finish()throws Exception {
        Path root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize().getParent().getParent().resolve("tests/results");Files.createDirectories(root);
        Files.writeString(root.resolve("features-"+size+"-"+phase+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("passed",passed,"authenticatedPlayers",0,"simulatedActors",actors.size(),"format",size))+"\n");
        getLogger().info("FEATURES PROBE SUCCESS "+passed.size());Bukkit.shutdown();
    }
    private void fail(Throwable error){getLogger().log(Level.SEVERE,"FEATURES PROBE FAILED",error);Bukkit.shutdown();}
}
