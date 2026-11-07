package fr.fkamis;

import com.google.gson.GsonBuilder;
import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fkpi.FkPI;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.*;
import org.bukkit.inventory.*;
import org.bukkit.persistence.PersistentDataContainer;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.potion.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Chaîne réelle des listeners Paper/FK, acteurs Player simulés : aucun client authentifié. */
public final class GameplayProbe extends JavaPlugin {
    private JavaPlugin companion;private Object state,teleports,attribution;private World world;private Path repo;
    private final List<String> passed=new ArrayList<>();private final List<Actor> actors=new ArrayList<>();
    private Map<UUID,String> roster;private Map<String,Location> spawns;private boolean veto;
    private final List<String> messages=new ArrayList<>();
    private Actor unassigned;
    private Object field(Object o,String n)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);return f.get(o);}
    private void set(Object o,String n,Object v)throws Exception{Field f=o.getClass().getDeclaredField(n);f.setAccessible(true);f.set(o,v);}
    private Object call(Object o,String n,Class<?>[] t,Object...a)throws Exception{Method m=o.getClass().getDeclaredMethod(n,t);m.setAccessible(true);return m.invoke(o,a);}
    private void check(boolean condition,String label){if(!condition)throw new AssertionError(label);passed.add(label);getLogger().info("GAMEPLAY PROBE PASS "+label);}
    private void phase(int day,boolean paused)throws Exception{set(state,"started",day>0);set(state,"day",day);set(state,"paused",paused);set(state,"winner","");call(companion,"syncNative",new Class<?>[]{});}
    private void later(Runnable action){Bukkit.getScheduler().runTaskLater(this,()->{try{action.run();}catch(Throwable ex){fail(ex);}},10);}
    @Override @SuppressWarnings("unchecked") public void onEnable(){
        try{
            Path instance=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();repo=instance.getParent().getParent();
            if(!instance.getFileName().toString().startsWith("probe-v2-fixes")||!Boolean.getBoolean("fk.gameplayprobe"))throw new IllegalStateException("Recette isolée uniquement.");
            companion=(JavaPlugin)Objects.requireNonNull(Bukkit.getPluginManager().getPlugin("FKAmis"));world=Objects.requireNonNull(Bukkit.getWorld("world"));
            state=field(companion,"state");teleports=field(companion,"teamTeleports");attribution=field(companion,"damageAttribution");
            roster=(Map<UUID,String>)field(companion,"roster");spawns=(Map<String,Location>)field(companion,"spawns");
            if((boolean)field(state,"started")||!roster.isEmpty())throw new IllegalStateException("Fixture vierge requise.");
            Bukkit.getPluginManager().registerEvents(new Listener(){@EventHandler(priority=EventPriority.HIGHEST)public void teleport(PlayerTeleportEvent e){if(veto&&e.getPlayer().getUniqueId().equals(actors.getFirst().id))e.setCancelled(true);}},this);
            Bukkit.getScheduler().runTaskLater(this,()->{try{initialize();cleanup();damage();forts();items();gatherInitial();}catch(Throwable ex){fail(ex);}},60);
        }catch(Throwable ex){fail(ex);}
    }
    @SuppressWarnings("unchecked") private void initialize()throws Exception{
        world.setDifficulty(Difficulty.NORMAL);world.setGameRule(GameRules.SPAWN_MOBS,false);
        for(int x=-2;x<=46;x++)for(int z=-2;z<=35;z++){world.getBlockAt(x,199,z).setType(Material.STONE,false);for(int y=200;y<=214;y++)world.getBlockAt(x,y,z).setType(Material.AIR,false);}
        int index=0;
        for(String team:List.of("Rouge","Bleue","Verte","Jaune"))for(int n=1;n<=2;n++){
            Actor actor=new Actor("Fixture"+index,index++);actors.add(actor);roster.put(actor.id,team);
            ((Map<UUID,String>)field(companion,"rosterNames")).put(actor.id,actor.name);
            FkPI.getInstance().getTeamManager().addPlayer(actor.name,team);
        }
        check(Bukkit.getOnlinePlayers().isEmpty(),"aucun client authentifié ; huit interfaces Player de fixture seulement");
        unassigned=new Actor("SansEquipe",8);
        var blue=spawns.get("Bleue").clone();blue.setYaw(90);blue.setPitch(8);spawns.put("Bleue",blue);
    }
    private void cleanup(){
        TerrainCleanup cleaner=new TerrainCleanup();
        for(String material:List.of("DANDELION","SHORT_GRASS","FERN","BUSH","FIREFLY_BUSH","SHORT_DRY_GRASS","DEAD_BUSH")){
            Material type=Material.valueOf(material);Block block=world.getBlockAt(0,205,0);block.setType(type,false);
            check(cleaner.unsupported(block),"support absent détecté : "+material);cleaner.cleanColumn(world,0,0,200);check(block.isEmpty(),"végétation retirée sans drop : "+material);
        }
        world.getBlockAt(2,200,0).setBlockData(Bukkit.createBlockData("minecraft:tall_grass[half=lower]"),false);
        world.getBlockAt(2,201,0).setBlockData(Bukkit.createBlockData("minecraft:tall_grass[half=upper]"),false);
        world.getBlockAt(2,199,0).setType(Material.AIR,false);cleaner.cleanColumn(world,2,0,199);
        check(world.getBlockAt(2,200,0).isEmpty()&&world.getBlockAt(2,201,0).isEmpty(),"deux moitiés d'herbe haute sans sol retirées");
        world.getBlockAt(4,204,0).setBlockData(Bukkit.createBlockData("minecraft:oak_leaves[persistent=false,distance=7]"),false);
        cleaner.cleanColumn(world,4,0,200);check(world.getBlockAt(4,204,0).isEmpty(),"feuilles réellement orphelines retirées");
        world.getBlockAt(8,199,0).setType(Material.DIRT,false);for(int y=200;y<=204;y++)world.getBlockAt(8,y,0).setType(Material.OAK_LOG,false);
        world.getBlockAt(9,204,0).setBlockData(Bukkit.createBlockData("minecraft:oak_leaves[persistent=false,distance=7]"),false);
        cleaner.cleanColumn(world,9,0,200);check(world.getBlockAt(9,204,0).getType()==Material.OAK_LEAVES,"arbre ancré et feuillage connecté préservés malgré distance périmée");
        world.getBlockAt(12,205,0).setBlockData(Bukkit.createBlockData("minecraft:oak_leaves[persistent=true,distance=7]"),false);
        cleaner.cleanColumn(world,12,0,200);check(world.getBlockAt(12,205,0).getType()==Material.OAK_LEAVES,"feuillage décoratif persistant préservé");
        world.getBlockAt(14,206,0).setType(Material.STONE,false);world.getBlockAt(14,205,0).setType(Material.HANGING_ROOTS,false);
        cleaner.cleanColumn(world,14,0,200);check(world.getBlockAt(14,205,0).getType()==Material.HANGING_ROOTS,"plante suspendue naturellement valide préservée");
        check(cleaner.cleanColumn(world,9,0,200).isEmpty()&&cleaner.cleanColumn(world,12,0,200).isEmpty()&&cleaner.cleanColumn(world,14,0,200).isEmpty(),"deuxième nettoyage de fixture sans modification");
    }
    private EntityDamageByEntityEvent hit(Entity attacker,Entity target,EntityDamageEvent.DamageCause cause){var e=new EntityDamageByEntityEvent(attacker,target,cause,4);Bukkit.getPluginManager().callEvent(e);return e;}
    private EntityDamageEvent danger(Player p,EntityDamageEvent.DamageCause cause){var e=new EntityDamageEvent(p,cause,4);Bukkit.getPluginManager().callEvent(e);return e;}
    private void damage()throws Exception{
        phase(1,false);check(world.getDifficulty()==Difficulty.NORMAL,"difficulté normale conservée");
        var a=actors.get(0);var friend=actors.get(1);var b=actors.get(2);
        Zombie zombie=world.spawn(new Location(world,35,200,20),Zombie.class);zombie.setAI(false);
        Skeleton skeleton=world.spawn(new Location(world,37,200,20),Skeleton.class);skeleton.setAI(false);
        Creeper creeper=world.spawn(new Location(world,39,200,20),Creeper.class);creeper.setAI(false);
        check(!hit(zombie,b.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"zombie autorisé à blesser au jour 1");
        Arrow arrow=world.spawn(new Location(world,37,201,20),Arrow.class);arrow.setShooter(skeleton);
        check(!hit(arrow,b.player,EntityDamageEvent.DamageCause.PROJECTILE).isCancelled(),"flèche de squelette autorisée au jour 1");
        check(!hit(creeper,b.player,EntityDamageEvent.DamageCause.ENTITY_EXPLOSION).isCancelled(),"explosion naturelle de creeper autorisée au jour 1");
        for(var cause:List.of(EntityDamageEvent.DamageCause.FALL,EntityDamageEvent.DamageCause.DROWNING,EntityDamageEvent.DamageCause.FIRE,
                EntityDamageEvent.DamageCause.FIRE_TICK,EntityDamageEvent.DamageCause.LAVA,EntityDamageEvent.DamageCause.STARVATION,EntityDamageEvent.DamageCause.POISON,EntityDamageEvent.DamageCause.WITHER))
            check(!danger(b.player,cause).isCancelled(),"danger naturel actif J1 : "+cause);
        check(!hit(a.player,zombie,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"joueur autorisé à se défendre contre un mob au jour 1");
        check(hit(a.player,b.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"mêlée entre adversaires refusée au jour 1");
        Arrow playerArrow=projectile(a.player);
        check(hit(playerArrow,b.player,EntityDamageEvent.DamageCause.PROJECTILE).isCancelled(),"projectile de joueur refusé au jour 1");
        var poison=new PotionEffect(PotionEffectType.POISON,100,0);
        var effect=new EntityPotionEffectEvent(b.player,null,poison,a.player,EntityPotionEffectEvent.Cause.POTION_SPLASH,EntityPotionEffectEvent.Action.ADDED,true);
        Bukkit.getPluginManager().callEvent(effect);check(effect.isCancelled(),"poison attribué à un joueur refusé J1");
        var witchEffect=new EntityPotionEffectEvent(b.player,null,poison,skeleton,EntityPotionEffectEvent.Cause.POTION_SPLASH,EntityPotionEffectEvent.Action.ADDED,true);
        Bukkit.getPluginManager().callEvent(witchEffect);check(!witchEffect.isCancelled(),"effet nocif de mob conservé J1");
        var heal=new EntityPotionEffectEvent(friend.player,null,new PotionEffect(PotionEffectType.REGENERATION,100,0),a.player,EntityPotionEffectEvent.Cause.POTION_SPLASH,EntityPotionEffectEvent.Action.ADDED,true);
        Bukkit.getPluginManager().callEvent(heal);check(!heal.isCancelled(),"soin entre coéquipiers autorisé J1");
        Block lava=world.getBlockAt(42,200,20);lava.setType(Material.LAVA,false);call(attribution,"mark",new Class<?>[]{Block.class,Material.class,UUID.class},lava,Material.LAVA,a.id);
        var trap=new EntityDamageByBlockEvent(lava,b.player,EntityDamageEvent.DamageCause.LAVA,4);Bukkit.getPluginManager().callEvent(trap);
        check(trap.isCancelled(),"lave de joueur attribuée refusée J1");
        lava.setType(Material.STONE,false);var oldMark=new EntityDamageByBlockEvent(lava,b.player,EntityDamageEvent.DamageCause.CONTACT,4);Bukkit.getPluginManager().callEvent(oldMark);
        check(!oldMark.isCancelled(),"attribution périmée rejetée après remplacement du bloc");
        Block eye=b.player.getEyeLocation().getBlock();eye.setType(Material.WATER,false);call(attribution,"mark",new Class<?>[]{Block.class,Material.class,UUID.class},eye,Material.WATER,a.id);
        check(danger(b.player,EntityDamageEvent.DamageCause.DROWNING).isCancelled(),"noyade dans une eau attribuée à un adversaire refusée J1");
        eye.setType(Material.STONE,false);call(attribution,"mark",new Class<?>[]{Block.class,Material.class,UUID.class},eye,Material.STONE,a.id);
        check(danger(b.player,EntityDamageEvent.DamageCause.SUFFOCATION).isCancelled(),"suffocation par bloc attribué refusée J1");eye.setType(Material.AIR,false);
        TNTPrimed playerTnt=world.spawn(new Location(world,42,200,24),TNTPrimed.class);playerTnt.setFuseTicks(10000);call(attribution,"mark",new Class<?>[]{Entity.class,UUID.class},playerTnt,a.id);
        check(hit(playerTnt,b.player,EntityDamageEvent.DamageCause.ENTITY_EXPLOSION).isCancelled(),"TNT attribuée à un joueur refusée J1");playerTnt.remove();
        Block moved=world.getBlockAt(43,200,20),movedTarget=moved.getRelative(BlockFace.EAST);moved.setType(Material.STONE,false);world.getBlockAt(42,200,20).setType(Material.PISTON,false);
        call(attribution,"mark",new Class<?>[]{Block.class,Material.class,UUID.class},moved,Material.STONE,a.id);
        var movement=new BlockPistonExtendEvent(world.getBlockAt(42,200,20),List.of(moved),BlockFace.EAST);Bukkit.getPluginManager().callEvent(movement);
        moved.setType(Material.AIR,false);movedTarget.setType(Material.STONE,false);
        check(!movement.isCancelled()&&a.id.equals(call(attribution,"owner",new Class<?>[]{Block.class},movedTarget)),"attribution suit un déplacement de piston autorisé");
        call(attribution,"mark",new Class<?>[]{Entity.class,UUID.class},creeper,a.id);
        check(hit(creeper,b.player,EntityDamageEvent.DamageCause.ENTITY_EXPLOSION).isCancelled(),"creeper déclenché volontairement attribué au joueur");
        phase(2,false);check(!hit(a.player,b.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"PvP J2 fonctionnel en terrain neutre");
        b.location=spawns.get("Bleue").clone();check(hit(a.player,b.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"PvP J2 refusé dans un royaume protégé");
        check(!hit(zombie,b.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"PvE reste actif dans un royaume protégé");
        phase(3,false);check(!hit(a.player,b.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"PvP J3 autorisé dans un royaume");
        for(int day=1;day<=3;day++){phase(day,false);check(hit(a.player,friend.player,EntityDamageEvent.DamageCause.ENTITY_ATTACK).isCancelled(),"friendly fire refusé J"+day);}
        phase(1,true);check(danger(b.player,EntityDamageEvent.DamageCause.FALL).isCancelled(),"pause conserve la protection générale");
        for(Entity e:List.of(zombie,skeleton,creeper,arrow))e.remove();b.location=new Location(world,1.5,200,1.5);lava.setType(Material.AIR,false);
    }
    @SuppressWarnings("unchecked") private void forts()throws Exception{
        var red=actors.get(0);var blue=actors.get(2);Block wall=world.getBlockAt(210,180,-200),tntBlock=world.getBlockAt(211,180,-200),objective=world.getBlockAt(212,180,-200);
        wall.setType(Material.STONE,false);tntBlock.setType(Material.TNT,false);objective.setType(Material.CHEST,false);
        ((Map<String,Location>)field(companion,"objectives")).put("Bleue",objective.getLocation());
        for(int day=1;day<=3;day++){
            phase(day,false);
            for(Block block:List.of(wall,tntBlock,objective)){var e=new BlockBreakEvent(block,red.player);Bukkit.getPluginManager().callEvent(e);check(e.isCancelled(),"casse adverse refusée J"+day+" : "+block.getType());}
            var own=new BlockBreakEvent(wall,blue.player);Bukkit.getPluginManager().callEvent(own);check(!own.isCancelled(),"propriétaire autorisé à modifier sa défense J"+day);
            TNTPrimed tnt=world.spawn(new Location(world,210.5,180.5,-200.5),TNTPrimed.class);tnt.setFuseTicks(10000);
            world.createExplosion(210.5,180.5,-200.5,4,false,true,tnt);
            check(day<3?wall.getType()==Material.STONE:wall.getType().isAir(),day<3?"explosion sans brèche avant assauts J"+day:"véritable explosion crée une brèche J3");
            check(objective.getType()==Material.CHEST,"coffre objectif survit à l'explosion J"+day);tnt.remove();
        }
        Block edge=world.getBlockAt(281,180,-200);Block enemy=world.getBlockAt(280,180,-200);enemy.setType(Material.STONE,false);
        var piston=new BlockPistonExtendEvent(edge,List.of(enemy),BlockFace.EAST);Bukkit.getPluginManager().callEvent(piston);
        check(piston.isCancelled(),"extraction de blocs adverses par piston refusée même J3");
        ((Map<String,Location>)field(companion,"objectives")).clear();
    }
    private void items()throws Exception{
        Object ban=field(companion,"itemBan");Inventory inventory=Bukkit.createInventory(null,9);
        inventory.setItem(0,new ItemStack(Material.ELYTRA));inventory.setItem(1,new ItemStack(Material.ENCHANTED_GOLDEN_APPLE));inventory.setItem(2,new ItemStack(Material.GOLDEN_APPLE,3));inventory.setItem(3,new ItemStack(Material.NETHERITE_INGOT));inventory.setItem(4,new ItemStack(Material.DIAMOND,2));
        call(ban,"clean",new Class<?>[]{Inventory.class},inventory);
        check(inventory.getItem(0)==null,"élytre retirée par le filtre existant");check(inventory.getItem(1)==null,"pomme enchantée retirée par le filtre existant");
        check(inventory.getItem(2).getAmount()==3,"pommes dorées ordinaires conservées");check(inventory.getItem(3)==null,"netherite reste interdite");check(inventory.getItem(4).getAmount()==2,"autres objets autorisés intacts");
        var consume=new PlayerItemConsumeEvent(actors.getFirst().player,new ItemStack(Material.ENCHANTED_GOLDEN_APPLE));Bukkit.getPluginManager().callEvent(consume);check(consume.isCancelled(),"consommation de pomme enchantée refusée");
        var ordinary=new PlayerItemConsumeEvent(actors.getFirst().player,new ItemStack(Material.GOLDEN_APPLE));Bukkit.getPluginManager().callEvent(ordinary);check(!ordinary.isCancelled(),"consommation de pomme dorée ordinaire autorisée");
        var glide=new EntityToggleGlideEvent(actors.getFirst().player,true);Bukkit.getPluginManager().callEvent(glide);check(glide.isCancelled(),"vol en élytre refusé avant le balayage d'inventaire");
        Object supplies=field(companion,"supplies");Object table=field(supplies,"table");
        for(Object tier:(List<?>)field(table,"tiers"))for(Object entry:(List<?>)call(tier,"entries",new Class<?>[]{})){
            String material=(String)call(entry,"material",new Class<?>[]{});check(!Set.of("ELYTRA","ENCHANTED_GOLDEN_APPLE").contains(material)&&!material.contains("NETHERITE"),"table de ravitaillement autorisée : "+material);
        }
    }
    private CommandSender sender(boolean admin){return (CommandSender)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{CommandSender.class},(p,m,a)->{
        if(m.getName().equals("hasPermission")||m.getName().equals("isOp"))return admin;if(m.getName().equals("getName"))return "FixtureAdmin";
        if(m.getName().equals("sendMessage")&&a!=null)messages.add(Arrays.toString(a));return defaultValue(m.getReturnType());});}
    private void begin(boolean confirm)throws Exception{List<Player> selected=new ArrayList<>(actors.stream().map(a->a.player).toList());selected.add(unassigned.player);call(teleports,"begin",new Class<?>[]{CommandSender.class,boolean.class,Collection.class},sender(true),confirm,selected);}
    private void refused(CommandSender s,boolean confirm,String label)throws Exception{
        int before=actors.stream().mapToInt(a->a.teleported).sum();boolean denied=false;
        try{call(teleports,"begin",new Class<?>[]{CommandSender.class,boolean.class,Collection.class},s,confirm,actors.stream().map(a->a.player).toList());}
        catch(InvocationTargetException ex){denied=ex.getCause()instanceof IllegalArgumentException;}
        check(denied&&actors.stream().mapToInt(a->a.teleported).sum()==before,label);
    }
    private void gatherInitial()throws Exception{
        phase(0,true);refused(sender(false),false,"rassemblement refusé sans permission");
        for(Actor a:actors){a.teleported=0;a.inventory.setItem(0,new ItemStack(Material.DIAMOND,2));}
        begin(false);later(()->{try{
            if(actors.stream().anyMatch(a->a.teleported!=1))for(var entry:spawns.entrySet()){
                Location at=entry.getValue();boolean loaded=world.isChunkLoaded(at.getBlockX()>>4,at.getBlockZ()>>4);
                getLogger().info("SPAWN CHECK "+entry.getKey()+" loaded="+loaded+" equal="+at.equals(spawns.get(entry.getKey()))+" base="+FkPI.getInstance().getTeamManager().getTeam(entry.getKey()).getBase().contains(at)
                        +(loaded?" feet="+at.getBlock().getBlockData().getAsString()+" head="+at.clone().add(0,1,0).getBlock().getBlockData().getAsString()+" floor="+at.clone().subtract(0,1,0).getBlock().getBlockData().getAsString()+" sturdy="+at.clone().subtract(0,1,0).getBlock().getBlockData().isFaceSturdy(BlockFace.UP,BlockSupport.FULL):""));
            }
            check(actors.stream().allMatch(a->a.teleported==1&&a.location.equals(spawns.get(roster.get(a.id)))),"huit acteurs de fixture orientés vers leurs quatre spawns enregistrés");
            check(unassigned.teleported==0,"joueur sans équipe ignoré");
            actors.get(0).online=false;actors.get(1).mode=GameMode.SPECTATOR;for(Actor a:actors)a.teleported=0;
            begin(false);later(this::gatherSkipped);
        }catch(Exception ex){throw new RuntimeException(ex);}});
    }
    private void gatherSkipped(){try{
        check(actors.get(0).teleported==0&&actors.get(1).teleported==0&&actors.subList(2,8).stream().allMatch(a->a.teleported==1),"déconnecté et spectateur ignorés");
        actors.get(0).online=true;actors.get(1).mode=GameMode.SURVIVAL;
        phase(2,false);refused(sender(true),true,"rassemblement refusé pendant combat actif");
        phase(2,true);refused(sender(true),false,"confirmation explicite exigée après début de partie");
        for(Actor a:actors)a.teleported=0;begin(true);later(this::gatherPaused);
    }catch(Exception ex){throw new RuntimeException(ex);}}
    private void gatherPaused(){try{
        check(actors.stream().allMatch(a->a.teleported==1&&a.mode==GameMode.SURVIVAL),"rassemblement confirmé en pause puis modes restaurés");
        check((boolean)field(state,"paused")&&Bukkit.getServerTickManager().isFrozen()&&Fk.getInstance().getGame().isPaused(),"pause native et gel mondial maintenus après rassemblement");
        check(actors.stream().allMatch(a->a.inventory.getItem(0).getAmount()==2)&&roster.size()==8,"équipes et inventaires inchangés par le rassemblement");
        var ordinary=new PlayerTeleportEvent(actors.getFirst().player,actors.getFirst().location,new Location(world,0,200,0),PlayerTeleportEvent.TeleportCause.COMMAND);Bukkit.getPluginManager().callEvent(ordinary);
        check(ordinary.isCancelled(),"téléportation ordinaire toujours refusée en pause");
        Location original=spawns.get("Bleue");spawns.put("Bleue",original.clone().add(0,-2,0));for(Actor a:actors)a.teleported=0;
        begin(true);later(()->{try{
            check(actors.stream().allMatch(a->a.teleported==0),"spawn invalide refuse tout le lot sans téléportation partielle");
            Location edge=original.clone().add(.45,0,0);Block obstacle=world.getBlockAt(edge.getBlockX()+1,edge.getBlockY()+1,edge.getBlockZ());var previous=obstacle.getBlockData();obstacle.setType(Material.STONE,false);spawns.put("Bleue",edge);
            begin(true);later(()->{try{
                check(actors.stream().allMatch(a->a.teleported==0),"obstacle latéral dans le volume du joueur refuse le rassemblement");
                obstacle.setBlockData(previous,false);spawns.put("Bleue",original);veto=true;begin(true);later(this::gatherVeto);
            }catch(Exception ex){throw new RuntimeException(ex);}});
        }catch(Exception ex){throw new RuntimeException(ex);}});
    }catch(Exception ex){throw new RuntimeException(ex);}}
    @SuppressWarnings("unchecked") private void gatherVeto(){try{
        check(actors.getFirst().teleported==0&&actors.getFirst().mode==GameMode.SURVIVAL,"annulation externe respectée et mode restauré");veto=false;
        ((Set<String>)field(state,"eliminated")).add("Rouge");actors.get(0).mode=GameMode.SPECTATOR;actors.get(1).mode=GameMode.SPECTATOR;for(Actor a:actors)a.teleported=0;
        begin(true);later(()->{try{
            check(actors.get(0).teleported==0&&actors.get(1).teleported==0&&actors.get(0).mode==GameMode.SPECTATOR,"éliminés ignorés et jamais remis en survie");
            ((Set<String>)field(state,"eliminated")).clear();roster.clear();((Map<?,?>)field(companion,"rosterNames")).clear();
            for(String team:List.of("Rouge","Bleue","Verte","Jaune")){
                var nativeTeam=FkPI.getInstance().getTeamManager().getTeam(team);
                for(String name:new ArrayList<>(nativeTeam.getPlayers()))nativeTeam.removePlayer(name);
            } // Les noms de fixture ne sont pas des comptes : aucune résolution de profil Mojang.
            phase(0,true);call(companion,"saveState",new Class<?>[]{});finish();
        }catch(Exception ex){throw new RuntimeException(ex);}});
    }catch(Exception ex){throw new RuntimeException(ex);}}
    private Arrow projectile(Player shooter){return (Arrow)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{Arrow.class},(p,m,a)->{
        return switch(m.getName()){
            case "getShooter"->shooter;case "getWorld"->world;case "getLocation"->new Location(world,0,200,0);case "getType"->EntityType.ARROW;
            case "getPersistentDataContainer"->actors.getFirst().data;default->defaultValue(m.getReturnType());};});}
    private final class Actor implements InvocationHandler {
        final UUID id;final String name;final Player player;final PlayerInventory inventory;final PersistentDataContainer data;
        Location location=new Location(world,.5,200,.5);GameMode mode=GameMode.SURVIVAL;boolean online=true;int teleported;
        Actor(String name,int index){this.name=name;id=UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8));
            Inventory storage=Bukkit.createInventory(null,54);inventory=(PlayerInventory)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{PlayerInventory.class},(p,m,a)->{
                if(m.getName().equals("getItemInMainHand"))return storage.getItem(0)==null?new ItemStack(Material.AIR):storage.getItem(0);
                if(m.getName().equals("getItemInOffHand"))return new ItemStack(Material.AIR);
                if(m.getName().equals("getHolder"))return null;
                try{return Inventory.class.getMethod(m.getName(),m.getParameterTypes()).invoke(storage,a);}catch(NoSuchMethodException ex){return defaultValue(m.getReturnType());}
            });
            Block chest=world.getBlockAt(44,200,index);chest.setType(Material.CHEST,false);data=((Chest)chest.getState()).getPersistentDataContainer();
            player=(Player)Proxy.newProxyInstance(getClassLoader(),new Class<?>[]{Player.class},this);
        }
        @Override public Object invoke(Object proxy,Method method,Object[] args){return switch(method.getName()){
            case "getName"->name;case "getUniqueId"->id;case "getWorld"->location.getWorld();case "getLocation"->location.clone();case "getEyeLocation"->location.clone().add(0,1.62,0);case "getType"->EntityType.PLAYER;
            case "getGameMode"->mode;case "isOnline"->online;case "isValid"->true;case "isDead","isOp","hasPermission","hasMetadata","getAllowFlight","isFlying"->false;
            case "getInventory"->inventory;case "getPersistentDataContainer"->data;case "getMetadata"->List.of();case "getEntityId"->Math.abs(id.hashCode());
            case "setGameMode"->{var e=new PlayerGameModeChangeEvent(player,(GameMode)args[0]);Bukkit.getPluginManager().callEvent(e);if(!e.isCancelled())mode=e.getNewGameMode();yield null;}
            case "teleport"->{var e=new PlayerTeleportEvent(player,location,(Location)args[0],args.length>1?(PlayerTeleportEvent.TeleportCause)args[1]:PlayerTeleportEvent.TeleportCause.PLUGIN);Bukkit.getPluginManager().callEvent(e);if(!e.isCancelled()){location=e.getTo().clone();teleported++;}yield !e.isCancelled();}
            case "hashCode"->id.hashCode();case "equals"->proxy==args[0];case "toString"->name;default->defaultValue(method.getReturnType());};}
    }
    private static Object defaultValue(Class<?> type){if(type==boolean.class)return false;if(type==int.class)return 0;if(type==long.class)return 0L;if(type==double.class)return 0d;if(type==float.class)return 0f;if(type==short.class)return (short)0;if(type==byte.class)return (byte)0;if(type==char.class)return (char)0;return null;}
    private void finish()throws Exception{
        Map<String,Object> report=new LinkedHashMap<>();report.put("passed",passed);report.put("authenticatedPlayers",Bukkit.getOnlinePlayers().size());report.put("simulatedPlayers",8);
        report.put("note","Événements Paper réels, mobs et explosions réels ; les huit Player sont des interfaces de fixture, pas des clients ni des sessions réseau. Validation multijoueur restante.");
        Files.writeString(repo.resolve("tests/results/v2-fixes-gameplay.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report)+"\n",StandardCharsets.UTF_8);
        getLogger().info("GAMEPLAY PROBE SUCCESS checks="+passed.size());Bukkit.shutdown();
    }
    private void fail(Throwable ex){getLogger().log(Level.SEVERE,"GAMEPLAY PROBE FAILED",ex);Bukkit.shutdown();}
}
