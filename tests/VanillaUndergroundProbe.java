package fr.fkamis.validation;

import com.google.gson.*;
import fr.devsylone.fkpi.FkPI;
import org.bukkit.*;
import org.bukkit.block.data.BlockData;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.plugin.java.JavaPlugin;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.Level;

/** Validation moteur d'une copie V2.2 isolée, sans clients ni changement de terrain. */
public final class VanillaUndergroundProbe extends JavaPlugin {
    private World world;private JsonObject plan;private int checked;
    private final Map<String,BlockData> states=new HashMap<>();private final Set<String> chunks=new HashSet<>();
    @Override public void onEnable(){try{
        if(!Boolean.getBoolean("fk.vanilla.probe")||!Bukkit.getIp().equals("127.0.0.1")||Bukkit.getPort()!=25630||!Bukkit.getOnlinePlayers().isEmpty())throw new IllegalStateException("Copie loopback 25630 requise");
        Path file=Path.of(System.getProperty("fk.vanilla.plan"));String sha=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(file)));
        if(!sha.equals(System.getProperty("fk.vanilla.plan.sha256")))throw new IllegalStateException("Plan changé");
        plan=JsonParser.parseString(Files.readString(file)).getAsJsonObject();
        if(!plan.get("variant").getAsString().equals("V2.2-vanilla-underground")||!plan.get("sourceArchiveSha256").getAsString().equals("8120f618b09b47cb0fac10e667324d06a96ca3a2c8114b1bf42193604349f5de"))throw new IllegalStateException("Terrain non approuvé");
        world=Bukkit.getWorld("world");Bukkit.getServerTickManager().setFrozen(true);Bukkit.getScheduler().runTaskLater(this,()->{try{load();}catch(Throwable t){fail(t);}},5);
    }catch(Throwable t){fail(t);}}
    private void load(){
        List<CompletableFuture<?>> pending=new ArrayList<>();
        for(JsonElement raw:plan.getAsJsonArray("checkPoints")){JsonArray p=raw.getAsJsonArray();int x=p.get(0).getAsInt()>>4,z=p.get(2).getAsInt()>>4;
            if(!chunks.add(x+":"+z))continue;if(!world.isChunkGenerated(x,z))throw new IllegalStateException("Génération refusée");pending.add(world.getChunkAtAsync(x,z,false));}
        CompletableFuture.allOf(pending.toArray(CompletableFuture[]::new)).whenComplete((v,error)->Bukkit.getScheduler().runTask(this,()->{try{if(error!=null)throw new IllegalStateException(error);verify();}catch(Throwable t){fail(t);}}));
    }
    private void verify()throws Exception{
        for(JsonElement raw:plan.getAsJsonArray("blocks")){JsonObject b=raw.getAsJsonObject();JsonArray p=b.getAsJsonArray("at");String s=b.get("after").getAsString();
            if(!world.getBlockAt(p.get(0).getAsInt(),p.get(1).getAsInt(),p.get(2).getAsInt()).getBlockData().matches(states.computeIfAbsent(s,Bukkit::createBlockData)))throw new AssertionError("Bloc naturel différent après chargement Paper");checked++;}
        JavaPlugin amis=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis"),fk=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FallenKingdom");
        if(!amis.isEnabled()||!fk.isEnabled()||Bukkit.getMaxPlayers()!=20||amis.getConfig().getInt("players-per-team")!=4||amis.getConfig().getInt("capture-seconds")!=60||amis.getConfig().getDouble("capture-radius")!=2.5)throw new AssertionError("Règles ou plugins différents");
        for(var team:FkPI.getInstance().getTeamManager().getTeams()){
            var base=team.getBase();if(base==null||base.getRadius()!=40)throw new AssertionError("Rayon non conforme");
            Location center=base.getCenter();
            for(int y:new int[]{world.getMinHeight()+2,world.getMaxHeight()-2})for(int dx:new int[]{-40,40})for(int dz:new int[]{-40,40})if(!base.contains(new Location(world,center.getBlockX()+dx,y,center.getBlockZ()+dz)))throw new AssertionError("Coins territoriaux incorrects");
            if(base.contains(center.clone().add(41,0,0)))throw new AssertionError("Limite externe incorrecte");
            var m=amis.getClass().getDeclaredMethod("safeSpawn",String.class);m.setAccessible(true);if(!(boolean)m.invoke(amis,team.getName()))throw new AssertionError("Spawn non praticable");
        }
        var state=YamlConfiguration.loadConfiguration(Path.of("plugins/FKAmis/state.yml").toFile());if(state.getBoolean("started")||state.getInt("day")!=0)throw new AssertionError("Partie initiale altérée");
        Map<String,Object> result=new LinkedHashMap<>();result.put("passed",true);result.put("naturalBlocksChecked",checked);result.put("footprintChunksLoaded",chunks.size());result.put("territoriesAndSpawnsVerified",4);result.put("day",0);result.put("gameStarted",false);result.put("authenticatedClients",0);result.put("visualInspection",false);result.put("generationPerformed",false);
        Files.writeString(Path.of("vanilla-paper-result.json"),new GsonBuilder().setPrettyPrinting().create().toJson(result));getLogger().info("VANILLA UNDERGROUND PAPER SUCCESS");Bukkit.shutdown();
    }
    private void fail(Throwable t){getLogger().log(Level.SEVERE,"VANILLA UNDERGROUND PAPER FAILED",t);Bukkit.shutdown();}
}
