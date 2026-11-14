package fr.fkamis;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import java.nio.file.*;
import java.lang.reflect.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.Level;

/** Outil de construction séparé, interdit dans le JAR de jeu et sur une partie jouée. */
public final class MapV21Builder extends JavaPlugin {
    private World world;private Path root;private JavaPlugin companion;private JsonObject plan;private JsonArray blocks;private int next,changed;private long started;
    private final List<String> checks=new ArrayList<>();
    private final Map<World,Integer> randomTicks=new HashMap<>();private final Map<World,Boolean> timeAdvances=new HashMap<>();
    @Override public void onEnable(){try{
        root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();
        if(!Boolean.getBoolean("fk.mapv21")||!root.getFileName().toString().startsWith("map-v21-")||!Bukkit.getOnlinePlayers().isEmpty())throw new IllegalStateException("Copie initiale map-v21-* isolée requise.");
        companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");world=Bukkit.getWorld("world");
        var state=new org.bukkit.configuration.file.YamlConfiguration();state.load(root.resolve("plugins/FKAmis/state.yml").toFile());
        if(state.getBoolean("started")||state.getInt("day")!=0||state.contains("roster")&&!state.getConfigurationSection("roster").getKeys(false).isEmpty()||state.contains("objectives")&&!state.getConfigurationSection("objectives").getKeys(false).isEmpty())throw new IllegalStateException("Aucune construction sur une partie jouée.");
        plan=JsonParser.parseString(Files.readString(root.resolve("map-v21-plan.json"))).getAsJsonObject();blocks=plan.getAsJsonArray("blocks");
        if(plan.get("schema").getAsInt()!=1||!plan.get("passed").getAsBoolean()||plan.getAsJsonArray("collisions").size()!=0||blocks.size()>50_000||blocks.size()<20_000)throw new IllegalStateException("Plan de collision invalide.");
        for(World level:Bukkit.getWorlds()){randomTicks.put(level,level.getGameRuleValue(GameRules.RANDOM_TICK_SPEED));timeAdvances.put(level,level.getGameRuleValue(GameRules.ADVANCE_TIME));level.setGameRule(GameRules.RANDOM_TICK_SPEED,0);level.setGameRule(GameRules.ADVANCE_TIME,false);}
        Bukkit.getScheduler().runTaskLater(this,()->{try{load();}catch(Throwable error){fail(error);}},30);
    }catch(Throwable error){fail(error);}}
    private void load(){
        List<CompletableFuture<?>> pending=new ArrayList<>();
        for(JsonElement element:plan.getAsJsonArray("chunks")){var at=element.getAsJsonArray();int x=at.get(0).getAsInt(),z=at.get(1).getAsInt();if(!world.isChunkGenerated(x,z))throw new IllegalStateException("Chunk source absent ; aucune génération.");pending.add(world.getChunkAtAsync(x,z,false));}
        CompletableFuture.allOf(pending.toArray(CompletableFuture[]::new)).whenComplete((unused,error)->Bukkit.getScheduler().runTask(this,()->{try{
            if(error!=null)throw new IllegalStateException("Chargement source interrompu.",error);
            for(JsonElement element:plan.getAsJsonArray("chunks")){var at=element.getAsJsonArray();world.addPluginChunkTicket(at.get(0).getAsInt(),at.get(1).getAsInt(),this);}
            for(JsonElement element:blocks){JsonObject block=element.getAsJsonObject();JsonArray at=block.getAsJsonArray("at");Material expected=Material.matchMaterial(block.get("before").getAsString());if(world.getBlockAt(at.get(0).getAsInt(),at.get(1).getAsInt(),at.get(2).getAsInt()).getType()!=expected)throw new IllegalStateException("Source différente depuis l'aperçu : "+at);}
            checks.add("Tous les matériaux sources vérifiés avant modification");started=System.nanoTime();paint();
        }catch(Throwable failure){fail(failure);}}));
    }
    private void paint(){
        new org.bukkit.scheduler.BukkitRunnable(){public void run(){try{
            int end=Math.min(next+900,blocks.size());for(;next<end;next++){var item=blocks.get(next).getAsJsonObject();var at=item.getAsJsonArray("at");var block=world.getBlockAt(at.get(0).getAsInt(),at.get(1).getAsInt(),at.get(2).getAsInt());var data=Bukkit.createBlockData(item.get("after").getAsString());if(!block.getBlockData().equals(data)){block.setBlockData(data,false);changed++;}}
            if(next==blocks.size()){cancel();verify();}
        }catch(Throwable error){cancel();fail(error);}}}.runTaskTimer(this,1,1);
    }
    private void verify()throws Exception{
        for(JsonElement element:blocks){var item=element.getAsJsonObject();var at=item.getAsJsonArray("at");if(!world.getBlockAt(at.get(0).getAsInt(),at.get(1).getAsInt(),at.get(2).getAsInt()).getBlockData().matches(Bukkit.createBlockData(item.get("after").getAsString())))throw new AssertionError("Bloc de sortie différent : "+at);}
        checks.add(blocks.size()+" blocs de sortie et états d'escalier conformes");
        for(var team:fr.devsylone.fkpi.FkPI.getInstance().getTeamManager().getTeams()){
            var base=team.getBase();if(base==null||base.getRadius()!=40)throw new AssertionError("Rayon de territoire différent de 40.");
            Location c=base.getCenter();for(int y:new int[]{world.getMinHeight()+2,world.getMaxHeight()-2})for(int dx:new int[]{-40,40})for(int dz:new int[]{-40,40})if(!base.contains(new Location(world,c.getBlockX()+dx,y,c.getBlockZ()+dz)))throw new AssertionError("Limite verticale ou coin incorrect.");
            for(int dx:new int[]{-41,41})if(base.contains(c.clone().add(dx,0,0)))throw new AssertionError("Périmètre externe incorrect.");
            Method safe=companion.getClass().getDeclaredMethod("safeSpawn",String.class);safe.setAccessible(true);if(!(boolean)safe.invoke(companion,team.getName()))throw new AssertionError("Spawn non praticable : "+team.getName());
            checks.add("Spawn et huit coins verticaux vérifiés : "+team.getName());
        }
        Bukkit.getServerTickManager().setFrozen(true);randomTicks.forEach((level,value)->level.setGameRule(GameRules.RANDOM_TICK_SPEED,value));timeAdvances.forEach((level,value)->level.setGameRule(GameRules.ADVANCE_TIME,value));
        checks.add("Règles de croissance et de temps rétablies après le chantier");world.save();world.removePluginChunkTickets(this);
        var report=new LinkedHashMap<String,Object>();report.put("passed",true);report.put("authenticatedClients",0);report.put("plannedBlocks",blocks.size());report.put("changedBlocks",changed);report.put("chunks",plan.getAsJsonArray("chunks"));report.put("caverns",plan.getAsJsonArray("caverns"));report.put("checks",checks);report.put("constructionMillis",(System.nanoTime()-started)/1_000_000);report.put("visualInspection",false);
        Files.writeString(root.resolve("map-v21-build-report.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report)+"\n");
        getLogger().info("MAP V21 BUILD SUCCESS");Bukkit.shutdown();
    }
    private void fail(Throwable error){getLogger().log(Level.SEVERE,"MAP V21 BUILD FAILED",error);Bukkit.shutdown();}
}
