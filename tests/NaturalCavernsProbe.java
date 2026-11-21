package fr.fkamis.validation;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.block.data.BlockData;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.configuration.file.YamlConfiguration;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.Level;

/** Sonde séparée : lecture sur copie loopback exclusivement, jamais dans FKAmis. */
public final class NaturalCavernsProbe extends JavaPlugin {
    private World world;
    private JsonObject plan;
    private final Map<String,BlockData> states=new HashMap<>();
    private final Map<Long,Material> beforePhysics=new HashMap<>();
    private final Map<World,Integer> randomTicks=new HashMap<>();
    private final List<String> checks=new ArrayList<>();
    private int checked;
    private static long pos(int x,int y,int z){return ((x&0x3ffffffL)<<38)|((z&0x3ffffffL)<<12)|(y&0xfffL);}
    @Override public void onEnable(){try{
        if(!Boolean.getBoolean("fk.natural.validation")||!Bukkit.getIp().equals("127.0.0.1")||Bukkit.getPort()!=25624||!Bukkit.getOnlinePlayers().isEmpty())throw new IllegalStateException("Copie loopback 25624 sans joueurs requise");
        Path file=Path.of(System.getProperty("fk.natural.plan"));
        String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
        if(!hash.equals(System.getProperty("fk.natural.plan.sha256")))throw new IllegalStateException("Plan différent");
        plan=JsonParser.parseString(Files.readString(file)).getAsJsonObject();
        if(!Set.of("V2.1-natural-caverns-r1","V2.1-natural-caverns-r2").contains(plan.get("variant").getAsString())||!plan.get("passed").getAsBoolean())throw new IllegalStateException("Plan non validé");
        world=Bukkit.getWorld("world");Bukkit.getServerTickManager().setFrozen(true);
        for(World w:Bukkit.getWorlds()){randomTicks.put(w,w.getGameRuleValue(GameRules.RANDOM_TICK_SPEED));w.setGameRule(GameRules.RANDOM_TICK_SPEED,0);}
        Bukkit.getScheduler().runTaskLater(this,()->{try{load();}catch(Throwable t){fail(t);}},5);
    }catch(Throwable t){fail(t);}}
    private void load(){
        List<CompletableFuture<?>> pending=new ArrayList<>();
        for(JsonElement raw:plan.getAsJsonArray("chunks")){
            JsonArray at=raw.getAsJsonArray();int x=at.get(0).getAsInt(),z=at.get(1).getAsInt();
            if(!world.isChunkGenerated(x,z))throw new IllegalStateException("Chunk absent, aucune génération permise");
            pending.add(world.getChunkAtAsync(x,z,false));
        }
        CompletableFuture.allOf(pending.toArray(CompletableFuture[]::new)).whenComplete((v,error)->Bukkit.getScheduler().runTask(this,()->{try{
            if(error!=null)throw new IllegalStateException("Chargement interrompu",error);
            for(JsonElement raw:plan.getAsJsonArray("chunks")){JsonArray at=raw.getAsJsonArray();world.addPluginChunkTicket(at.get(0).getAsInt(),at.get(1).getAsInt(),this);}
            verify();snapshot();Bukkit.getServerTickManager().setFrozen(false);
            Bukkit.getScheduler().runTaskLater(this,()->{try{physics();finish();}catch(Throwable t){fail(t);}},200);
        }catch(Throwable t){fail(t);}}));
    }
    private void verify()throws Exception{
        for(JsonElement raw:plan.getAsJsonArray("blocks")){
            JsonObject block=raw.getAsJsonObject();JsonArray p=block.getAsJsonArray("at");String s=block.get("after").getAsString();
            BlockData expected=states.computeIfAbsent(s,Bukkit::createBlockData);
            if(!world.getBlockAt(p.get(0).getAsInt(),p.get(1).getAsInt(),p.get(2).getAsInt()).getBlockData().matches(expected))throw new AssertionError("Bloc enregistré différent du plan");
            checked++;
        }
        JavaPlugin fk=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FallenKingdom");
        JavaPlugin amis=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");
        if(fk==null||amis==null||!fk.isEnabled()||!amis.isEnabled()||Bukkit.getMaxPlayers()!=20||amis.getConfig().getInt("players-per-team")!=4)throw new AssertionError("Plugins/capacités incorrects");
        var state=YamlConfiguration.loadConfiguration(Path.of("plugins/FKAmis/state.yml").toFile());
        if(state.getBoolean("started")||state.getInt("day")!=0)throw new AssertionError("Partie non initiale");
        for(String team:List.of("Rouge","Bleue","Verte","Jaune")){
            if(state.getInt("native.TeamManager."+team+".Base.Radius")!=40)throw new AssertionError("Rayon différent");
            var method=amis.getClass().getDeclaredMethod("safeSpawn",String.class);method.setAccessible(true);
            if(!(boolean)method.invoke(amis,team))throw new AssertionError("Spawn non praticable");
        }
        checks.add(checked+" états de blocs Paper conformes");checks.add("Deux plugins de jeu actifs, vingt places, quatre membres, quatre rayons 40 et quatre spawns sûrs");
        checks.add("Jour zéro non lancé, aucun joueur authentifié");
    }
    private void snapshot(){
        for(JsonElement raw:plan.getAsJsonArray("caverns")){
            JsonArray box=raw.getAsJsonObject().getAsJsonArray("bbox"),a=box.get(0).getAsJsonArray(),b=box.get(1).getAsJsonArray();
            for(int x=a.get(0).getAsInt();x<=b.get(0).getAsInt();x++)for(int y=a.get(1).getAsInt();y<=b.get(1).getAsInt();y++)for(int z=a.get(2).getAsInt();z<=b.get(2).getAsInt();z++)beforePhysics.put(pos(x,y,z),world.getBlockAt(x,y,z).getType());
        }
    }
    private void physics(){
        int fluidChanges=0;
        for(JsonElement raw:plan.getAsJsonArray("caverns")){
            JsonObject cave=raw.getAsJsonObject();JsonArray box=cave.getAsJsonArray("bbox"),a=box.get(0).getAsJsonArray(),b=box.get(1).getAsJsonArray();
            for(int x=a.get(0).getAsInt();x<=b.get(0).getAsInt();x++)for(int y=a.get(1).getAsInt();y<=b.get(1).getAsInt();y++)for(int z=a.get(2).getAsInt();z<=b.get(2).getAsInt();z++){
                Material old=beforePhysics.get(pos(x,y,z)),actual=world.getBlockAt(x,y,z).getType();
                if(actual!=old){
                    if(actual!=Material.WATER||!old.isAir())throw new AssertionError("Changement de terrain inattendu pendant dix secondes");
                    fluidChanges++;
                }
            }
        }
        if(fluidChanges>512)throw new AssertionError("Propagation d'eau trop importante");
        checks.add("Dix secondes de simulation, nouveaux blocs d'eau : "+fluidChanges);
    }
    private void finish()throws Exception{
        randomTicks.forEach((w,v)->w.setGameRule(GameRules.RANDOM_TICK_SPEED,v));world.removePluginChunkTickets(this);
        var result=new LinkedHashMap<String,Object>();result.put("passed",true);result.put("blocksChecked",checked);result.put("chunksLoaded",plan.getAsJsonArray("chunks").size());result.put("checks",checks);result.put("authenticatedClients",0);result.put("visualInspection",false);result.put("publicPortExposed",false);
        Files.writeString(Path.of("natural-caverns-paper-probe.json"),new GsonBuilder().setPrettyPrinting().create().toJson(result));
        getLogger().info("NATURAL CAVERNS PAPER VALIDATION SUCCESS");Bukkit.shutdown();
    }
    private void fail(Throwable t){getLogger().log(Level.SEVERE,"NATURAL CAVERNS PAPER VALIDATION FAILED",t);Bukkit.shutdown();}
}
