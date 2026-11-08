package fr.fkamis;

import com.google.gson.GsonBuilder;
import fr.devsylone.fkpi.FkPI;
import org.bukkit.*;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.inventory.ItemStack;
import org.bukkit.block.Block;
import org.bukkit.block.BlockFace;
import org.bukkit.block.Dispenser;
import org.bukkit.block.data.Directional;
import org.bukkit.event.player.PlayerRespawnEvent;
import org.bukkit.util.Vector;
import org.bukkit.plugin.java.JavaPlugin;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Diagnostic séparé : IA, projectile et santé NMS réels, zéro client authentifié. */
public final class PvEPhysicsProbe extends JavaPlugin implements Listener {
    private JavaPlugin companion;private Object state;private World world;
    private Skeleton skeleton;private LivingEntity target;private Player player,attacker;private Object observedSource;
    private Entity extra;private int cancelled;private Location arena;private int matrixIndex;
    private final List<Checked> matrix=new ArrayList<>();
    private int shots,hits,damages;private final List<Map<String,Object>> cases=new ArrayList<>();
    private Object field(Object object,String name)throws Exception {for(Class<?> c=object.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(object);}catch(NoSuchFieldException ignored){}throw new NoSuchFieldException(name);}
    private void set(Object object,String name,Object value)throws Exception {for(Class<?> c=object.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(object,value);return;}catch(NoSuchFieldException ignored){}throw new NoSuchFieldException(name);}
    private Object invoke(Object object,String name,Class<?>[] types,Object...args)throws Exception {Method m=object.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(object,args);}
    private Class<?> type(String name)throws Exception {return Class.forName(name);}
    private void later(int ticks,Checked action){Bukkit.getScheduler().runTaskLater(this,()->{try{action.run();}catch(Throwable e){fail(e);}},ticks);}
    @FunctionalInterface interface Checked {void run()throws Exception;}
    @Override public void onEnable(){try{
        if(!Boolean.getBoolean("fk.physics")||!Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize().getFileName().toString().startsWith("pve-"))throw new IllegalStateException("Copie physique isolée requise.");
        companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");state=field(companion,"state");world=Bukkit.getWorld("world");
        Bukkit.getPluginManager().registerEvents(this,this);later(40,this::start);
    }catch(Throwable e){fail(e);}}
    private void start()throws Exception {
        set(state,"started",true);set(state,"paused",false);set(state,"day",1);invoke(companion,"syncNative",new Class<?>[]{});
        world.setTime(18000);world.setDifficulty(Difficulty.NORMAL);
        for(int cx=9;cx<=10;cx++)for(int cz=9;cz<=10;cz++)world.getChunkAt(cx,cz).setForceLoaded(true);
        for(int x=154;x<=166;x++)for(int z=154;z<=172;z++){world.getBlockAt(x,199,z).setType(Material.STONE,false);for(int y=200;y<=205;y++)world.getBlockAt(x,y,z).setType(Material.AIR,false);}
        IronGolem golem=world.spawn(new Location(world,160.5,200,158.5),IronGolem.class);golem.setAI(false);golem.setRemoveWhenFarAway(false);target=golem;
        alwaysActive(golem);
        prepareSkeleton();measure("baseline_ia_golem",240,()->{
            if(Boolean.getBoolean("fk.physics.fixed")){if(shots==0||hits==0||target.getHealth()>=100)throw new AssertionError("Le squelette corrigé doit tirer et blesser le golem.");playerCases();}
            else baselineControls();
        });
    }
    private void alwaysActive(Entity entity)throws Exception {Object handle=entity.getClass().getMethod("getHandle").invoke(entity);set(handle,"defaultActivationState",true);}
    private void prepareSkeleton()throws Exception {
        if(skeleton!=null)skeleton.remove();shots=hits=damages=0;
        skeleton=world.spawn(new Location(world,160.5,200,166.5),Skeleton.class);skeleton.setRemoveWhenFarAway(false);skeleton.setPersistent(true);
        skeleton.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));skeleton.setTarget(target);alwaysActive(skeleton);
        observedSource=skeleton;
    }
    private void measure(String label,int ticks,Checked next)throws Exception {
        double before=target.getHealth();UUID uuid=target.getUniqueId();
        later(ticks,()->{var row=new LinkedHashMap<String,Object>();row.put("case",label);row.put("shots",shots);row.put("hits",hits);row.put("damageEvents",damages);row.put("healthBefore",before);row.put("healthAfter",target.getHealth());row.put("victimType",target.getType().name());row.put("skeletonTicksLived",skeleton.getTicksLived());row.put("hasAI",skeleton.hasAI());row.put("hasTarget",skeleton.getTarget()!=null);row.put("lineOfSight",skeleton.hasLineOfSight(target));
            cases.add(row);getLogger().info("PHYSICS CASE "+new GsonBuilder().create().toJson(row));next.run();});
    }
    private void baselineControls()throws Exception {
        // Interrompre seulement le tick périodique 20 ticks qui appelle ItemBan.sweep.
        int cancelled=0;
        for(var task:Bukkit.getScheduler().getPendingTasks())if(task.getOwner()==companion) {
            try {Method m=task.getClass().getDeclaredMethod("getPeriod");m.setAccessible(true);if(((Number)m.invoke(task)).longValue()==20){task.cancel();cancelled++;}}catch(NoSuchMethodException ignored){}
        }
        if(cancelled!=1)throw new AssertionError("Un seul tick FKAmis doit être suspendu : "+cancelled);
        target.setHealth(100);prepareSkeleton();measure("sans_balaye_equipement",240,()->{
            if(shots==0||hits==0||target.getHealth()>=100)throw new AssertionError("Le témoin doit tirer et diminuer la santé réelle.");
            target.setHealth(100);prepareSkeleton();
            var reset=Bukkit.getScheduler().runTaskTimer(this,()->skeleton.getEquipment().setItemInMainHand(skeleton.getEquipment().getItemInMainHand().clone()),20,20);
            measure("arc_identique_reapplique_chaque_seconde",240,()->{reset.cancel();playerCases();});
        });
    }
    private Player createPlayer()throws Exception {return createPlayer("PhysicsParticipant","PhysicsPart","Rouge",new Location(world,160.5,200,158.5));}
    @SuppressWarnings("unchecked") private Player createPlayer(String identity,String name,String team,Location at)throws Exception {
        Object server=Bukkit.getServer().getClass().getMethod("getServer").invoke(Bukkit.getServer());Object level=world.getClass().getMethod("getHandle").invoke(world);
        UUID id=UUID.nameUUIDFromBytes(identity.getBytes(java.nio.charset.StandardCharsets.UTF_8));
        Object profile=type("com.mojang.authlib.GameProfile").getConstructor(UUID.class,String.class).newInstance(id,name);
        Object info=type("net.minecraft.server.level.ClientInformation").getMethod("createDefault").invoke(null);
        Object body=type("net.minecraft.server.level.ServerPlayer").getConstructor(type("net.minecraft.server.MinecraftServer"),type("net.minecraft.server.level.ServerLevel"),type("com.mojang.authlib.GameProfile"),type("net.minecraft.server.level.ClientInformation")).newInstance(server,level,profile,info);
        Object flow=Enum.valueOf((Class<Enum>)type("net.minecraft.network.protocol.PacketFlow"),"SERVERBOUND");
        Object connection=type("net.minecraft.network.Connection").getConstructor(type("net.minecraft.network.protocol.PacketFlow")).newInstance(flow);
        set(connection,"address",new java.net.InetSocketAddress("127.0.0.1",1));
        Object cookie=type("net.minecraft.server.network.CommonListenerCookie").getMethod("createInitial",type("com.mojang.authlib.GameProfile"),boolean.class).invoke(null,profile,false);
        Object listener=type("net.minecraft.server.network.ServerGamePacketListenerImpl").getConstructor(type("net.minecraft.server.MinecraftServer"),type("net.minecraft.network.Connection"),type("net.minecraft.server.level.ServerPlayer"),type("net.minecraft.server.network.CommonListenerCookie")).newInstance(server,connection,body,cookie);
        set(body,"connection",listener);set(listener,"clientLoadedTimeoutTimer",0);set(listener,"waitingForRespawn",false);
        Player bukkit=(Player)body.getClass().getMethod("getBukkitEntity").invoke(body);
        ((Map<UUID,String>)field(companion,"roster")).put(id,team);((Map<UUID,String>)field(companion,"rosterNames")).put(id,bukkit.getName());FkPI.getInstance().getTeamManager().addPlayer(bukkit.getName(),team);
        body.getClass().getMethod("snapTo",double.class,double.class,double.class).invoke(body,at.getX(),at.getY(),at.getZ());
        level.getClass().getMethod("addNewPlayer",type("net.minecraft.server.level.ServerPlayer")).invoke(level,body);
        bukkit.setGameMode(GameMode.SURVIVAL);bukkit.setInvulnerable(false);bukkit.setNoDamageTicks(0);
        return bukkit;
    }
    private void playerCases()throws Exception {
        if(target!=null)target.remove();player=createPlayer();target=player;
        player.setHealth(20);prepareSkeleton();measure("ia_vers_participant_survival_j1",240,()->{
            if(shots==0||hits==0||damages==0||player.getHealth()>=20)throw new AssertionError("Chaîne tir -> impact -> événement -> santé participant non démontrée.");
            if(Boolean.getBoolean("fk.physics.fixed"))matrix();else finish();
        });
    }
    private void position(Player p,Location at)throws Exception{Object body=p.getClass().getMethod("getHandle").invoke(p);body.getClass().getMethod("snapTo",double.class,double.class,double.class).invoke(body,at.getX(),at.getY(),at.getZ());p.setVelocity(new Vector());}
    private void resetCase(int day,boolean base)throws Exception{
        if(skeleton!=null){skeleton.remove();skeleton=null;}if(extra!=null){extra.remove();extra=null;}
        for(Arrow arrow:world.getEntitiesByClass(Arrow.class))arrow.remove();
        arena=new Location(world,base?-239.5:160.5,200,base?-239.5:158.5);
        for(int x=arena.getBlockX()-7;x<=arena.getBlockX()+7;x++)for(int z=arena.getBlockZ()-7;z<=arena.getBlockZ()+11;z++){
            world.getChunkAt(x>>4,z>>4).setForceLoaded(true);world.getBlockAt(x,199,z).setType(Material.STONE,false);for(int y=200;y<=205;y++)world.getBlockAt(x,y,z).setType(Material.AIR,false);
        }
        set(state,"day",day);set(state,"paused",false);invoke(companion,"syncNative",new Class<?>[]{});position(player,arena);
        if(attacker!=null)position(attacker,arena.clone().add(40,0,40)); // empêcher l'IA de choisir le second corps, plus proche.
        player.setHealth(20);player.setNoDamageTicks(0);player.setFireTicks(0);player.getInventory().setArmorContents(new ItemStack[4]);
        target=player;shots=hits=damages=cancelled=0;observedSource=null;
    }
    private void matrixMeasure(String label,int ticks,boolean hurt,boolean requireImpact)throws Exception{
        double before=player.getHealth();int day=(int)field(state,"day");String territory=String.valueOf(invoke(companion,"territory",new Class<?>[]{Location.class},arena));GameMode mode=player.getGameMode();
        later(ticks,()->{double after=player.getHealth();var row=new LinkedHashMap<String,Object>();row.put("case",label);row.put("day",day);row.put("territory",territory);row.put("mode",mode.name());row.put("playerPosition",List.of(player.getX(),player.getY(),player.getZ()));row.put("shotsOrLaunches",shots);row.put("hits",hits);row.put("damageEvents",damages);row.put("cancelledDamageEvents",cancelled);row.put("healthBefore",before);row.put("healthAfter",after);row.put("expectedHealthLoss",hurt);cases.add(row);getLogger().info("PHYSICS CASE "+new GsonBuilder().create().toJson(row));
            if(hurt?after>=before:after!=before)throw new AssertionError("Santé physique inattendue : "+label);
            if(requireImpact&&hits==0)throw new AssertionError("Impact physique absent : "+label);
            nextMatrix();});
    }
    private void naturalSkeleton()throws Exception{
        skeleton=world.spawn(arena.clone().add(0,0,8),Skeleton.class,org.bukkit.event.entity.CreatureSpawnEvent.SpawnReason.NATURAL);
        skeleton.getEquipment().setItemInMainHand(new ItemStack(Material.BOW));skeleton.setTarget(player);alwaysActive(skeleton);observedSource=skeleton;
    }
    private void launchAtPlayer(Player source){observedSource=source;source.launchProjectile(Arrow.class,player.getEyeLocation().toVector().subtract(source.getEyeLocation().toVector()).normalize().multiply(1.6));}
    @SuppressWarnings("unchecked") private void matrix()throws Exception{
        attacker=createPlayer("PhysicsAttacker","PhysicsAtk","Bleue",new Location(world,164,200,164));
        matrix.add(()->{resetCase(2,false);player.getInventory().setArmorContents(new ItemStack[]{new ItemStack(Material.IRON_BOOTS),new ItemStack(Material.IRON_LEGGINGS),new ItemStack(Material.IRON_CHESTPLATE),new ItemStack(Material.IRON_HELMET)});naturalSkeleton();matrixMeasure("squelette_natural_j2_armure_fer",220,true,true);});
        matrix.add(()->{resetCase(3,true);naturalSkeleton();matrixMeasure("squelette_natural_j3_base",220,true,true);});
        matrix.add(()->{resetCase(1,false);Bukkit.dispatchCommand(Bukkit.getConsoleSender(),"minecraft:summon minecraft:skeleton "+arena.getX()+" 200 "+(arena.getZ()+8));skeleton=world.getNearbyEntities(arena,2,3,10).stream().filter(e->e instanceof Skeleton).map(e->(Skeleton)e).findFirst().orElseThrow();skeleton.setTarget(player);alwaysActive(skeleton);observedSource=skeleton;matrixMeasure("squelette_commande_summon_j1",220,true,true);});
        matrix.add(()->{resetCase(1,false);Zombie zombie=world.spawn(arena.clone().add(0,0,1.2),Zombie.class);zombie.setTarget(player);zombie.setShouldBurnInDay(false);alwaysActive(zombie);extra=zombie;observedSource=zombie;matrixMeasure("zombie_ia_melee_j1",100,true,false);});
        matrix.add(()->{resetCase(2,false);Creeper creeper=world.spawn(arena.clone().add(0,0,4.5),Creeper.class);creeper.setAI(false);alwaysActive(creeper);extra=creeper;observedSource=creeper;creeper.ignite();matrixMeasure("creeper_explosion_physique_j2",60,true,false);});
        matrix.add(()->{resetCase(1,false);position(attacker,arena.clone().add(0,0,7));launchAtPlayer(attacker);matrixMeasure("fleche_joueur_j1_refusee",45,false,true);});
        matrix.add(()->{resetCase(2,false);position(attacker,arena.clone().add(0,0,7));launchAtPlayer(attacker);matrixMeasure("fleche_joueur_j2_neutre",45,true,true);});
        matrix.add(()->{resetCase(2,true);position(attacker,arena.clone().add(0,0,7));launchAtPlayer(attacker);matrixMeasure("fleche_joueur_j2_base_refusee",45,false,true);});
        matrix.add(()->{resetCase(3,true);position(attacker,arena.clone().add(0,0,7));launchAtPlayer(attacker);matrixMeasure("fleche_joueur_j3_base",45,true,true);});
        matrix.add(()->{resetCase(3,false);Block block=world.getBlockAt(arena.getBlockX(),201,arena.getBlockZ()+5);block.setType(Material.DISPENSER,false);Directional facing=(Directional)block.getBlockData();facing.setFacing(BlockFace.NORTH);block.setBlockData(facing,false);Dispenser dispenser=(Dispenser)block.getState();dispenser.getInventory().addItem(new ItemStack(Material.ARROW,3));observedSource=dispenser.getBlockProjectileSource();invoke(field(companion,"damageAttribution"),"mark",new Class<?>[]{Block.class,Material.class,UUID.class},block,Material.DISPENSER,attacker.getUniqueId());if(!dispenser.dispense())throw new AssertionError("Distributeur inactif");matrixMeasure("distributeur_reel_attribue_j3",45,true,true);});
        matrix.add(()->{resetCase(3,false);Bukkit.getPluginManager().callEvent(new PlayerRespawnEvent(player,arena,false,false,false,PlayerRespawnEvent.RespawnReason.DEATH));naturalSkeleton();matrixMeasure("squelette_apres_respawn_grace_pvp",100,true,true);});
        matrix.add(()->{resetCase(3,false);((Set<UUID>)field(field(companion,"administrators"),"ids")).add(player.getUniqueId());player.setGameMode(GameMode.CREATIVE);position(attacker,arena.clone().add(0,0,7));launchAtPlayer(attacker);matrixMeasure("arbitre_creatif_fleche_physique",45,false,false);});
        matrix.add(()->{resetCase(3,false);((Set<UUID>)field(field(companion,"administrators"),"ids")).remove(player.getUniqueId());((Set<String>)field(state,"eliminated")).add("Rouge");player.setGameMode(GameMode.SPECTATOR);position(attacker,arena.clone().add(0,0,7));launchAtPlayer(attacker);matrixMeasure("elimine_spectateur_fleche_physique",45,false,false);});
        nextMatrix();
    }
    private void nextMatrix()throws Exception{if(matrixIndex<matrix.size())matrix.get(matrixIndex++).run();else{player.getInventory().setItem(0,new ItemStack(Material.BREAD,7));player.saveData();finish();}}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void bow(EntityShootBowEvent e){if(e.getEntity()==observedSource)shots++;}
    private boolean sameSource(Object source){if(source instanceof org.bukkit.projectiles.BlockProjectileSource a&&observedSource instanceof org.bukkit.projectiles.BlockProjectileSource b)return a.getBlock().equals(b.getBlock());return Objects.equals(source,observedSource);}
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void launch(ProjectileLaunchEvent e){if(e.getEntity().getShooter()!=skeleton&&sameSource(e.getEntity().getShooter()))shots++;}
    @EventHandler(priority=EventPriority.MONITOR) public void hit(ProjectileHitEvent e){if(sameSource(e.getEntity().getShooter())){getLogger().info("PHYSICS HIT entity="+(e.getHitEntity()==null?"null":e.getHitEntity().getName())+" block="+e.getHitBlock()+" at="+e.getEntity().getLocation());if(e.getHitEntity()==target)hits++;}}
    @EventHandler(priority=EventPriority.MONITOR) public void damage(EntityDamageByEntityEvent e){if(e.getEntity()==target&&(e.getDamager()==observedSource||e.getDamager() instanceof Projectile p&&sameSource(p.getShooter()))){damages++;if(e.isCancelled())cancelled++;getLogger().info("PHYSICS DAMAGE cancelled="+e.isCancelled()+" final="+e.getFinalDamage()+" health="+target.getHealth());}}
    private void finish()throws Exception {
        Path root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize().getParent().getParent().resolve("tests/results");Files.createDirectories(root);
        Files.writeString(root.resolve("physics-"+(Boolean.getBoolean("fk.physics.fixed")?"fixed":"baseline")+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("cases",cases,"authenticatedClients",0,"realNmsPlayerBody",true,"note","Un corps ServerPlayer synthétique, sans protocole réseau ni session authentifiée ; santé et collisions physiques réelles."))+"\n");
        if(skeleton!=null)skeleton.remove();getLogger().info("PHYSICS PROBE SUCCESS");Bukkit.shutdown();
    }
    private void fail(Throwable e){getLogger().log(Level.SEVERE,"PHYSICS PROBE FAILED",e);Bukkit.shutdown();}
}
