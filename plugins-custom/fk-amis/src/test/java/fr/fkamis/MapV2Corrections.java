package fr.fkamis;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.block.Chest;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.logging.Level;

/** Outil de nettoyage séparé. Aucun appel au constructeur de terrain ni au remplissage de coffres. */
public final class MapV2Corrections extends JavaPlugin {
    record Column(int x,int z,int minY,String zone){}
    private final Gson gson=new GsonBuilder().setPrettyPrinting().create();
    private final Map<String,Column> columns=new LinkedHashMap<>();
    private final Map<String,Map<String,Integer>> counts=new TreeMap<>();
    private final List<Integer> passes=new ArrayList<>();
    private final Set<String> protectedBlocks=new HashSet<>();
    private World world;private Path repo,instance;private JsonObject built;private boolean frozen;
    private TerrainCleanup cleaner;private Map<String,String> protectedBefore;private int passChanges,pass,visited;
    private double worstSlice;
    @Override public void onEnable(){
        try{
            instance=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();repo=instance.getParent().getParent();
            if(!instance.getFileName().toString().equals("map-v2-fixes")||!Boolean.getBoolean("fk.corrections.authorized"))throw new IllegalStateException("Nettoyage réservé à la copie runtime/map-v2-fixes.");
            var companion=Objects.requireNonNull(Bukkit.getPluginManager().getPlugin("FKAmis"));
            var state=companion.getClass().getDeclaredField("state");state.setAccessible(true);Object value=state.get(companion);
            var started=value.getClass().getDeclaredField("started");started.setAccessible(true);
            var objectives=companion.getClass().getDeclaredField("objectives");objectives.setAccessible(true);
            if(started.getBoolean(value)||!((Map<?,?>)objectives.get(companion)).isEmpty())throw new IllegalStateException("Nettoyage interdit après départ ou déclaration d'objectifs.");
            world=Objects.requireNonNull(Bukkit.getWorld("world"));
            built=JsonParser.parseString(Files.readString(instance.resolve("map-v2-construction.json"))).getAsJsonObject();
            frozen=Bukkit.getServerTickManager().isFrozen();
            Bukkit.getScheduler().runTaskAsynchronously(this,()->{
                try{plan();Bukkit.getScheduler().runTask(this,this::preload);}
                catch(Throwable ex){Bukkit.getScheduler().runTask(this,()->fail(ex));}
            }); // Le calcul des coordonnées ne lit aucun bloc ; il reste hors du thread de jeu.
        }catch(Throwable ex){fail(ex);}
    }
    private int n(JsonObject o,String k){return o.get(k).getAsInt();}
    private void add(int x,int z,int min,String zone){String key=x+":"+z;columns.putIfAbsent(key,new Column(x,z,min,zone));}
    private void disc(int x,int z,int radius,int min,String zone){for(int dx=-radius;dx<=radius;dx++)for(int dz=-radius;dz<=radius;dz++)if(dx*dx+dz*dz<=radius*radius)add(x+dx,z+dz,min,zone);}
    private boolean base(int x,int z){for(JsonElement e:built.getAsJsonArray("bases")){var b=e.getAsJsonObject();if(Math.abs(x-n(b,"x"))<=81&&Math.abs(z-n(b,"z"))<=81)return true;}return false;}
    private void path(int x1,int z1,int x2,int z2){
        double length=Math.hypot(x2-x1,z2-z1);if(length<1)return;
        for(int i=0;i<=(int)length;i++){
            double t=i/length;int x=(int)Math.round(x1+(x2-x1)*t+Math.sin(t*Math.PI)*Math.sin(t*6)*5),z=(int)Math.round(z1+(z2-z1)*t+Math.sin(t*Math.PI)*Math.cos(t*5)*5);
            for(int dx=-8;dx<=8;dx++)for(int dz=-8;dz<=8;dz++)if(!base(x+dx,z+dz))add(x+dx,z+dz,40,"sentiers-et-lisières");
        }
    }
    private void plan()throws Exception{
        for(JsonElement e:built.getAsJsonArray("monuments")){
            var m=e.getAsJsonObject();var plan=JsonParser.parseString(Files.readString(repo.resolve("maps/v2/structures/"+m.get("id").getAsString()+".json"))).getAsJsonObject();
            for(JsonElement p:plan.getAsJsonArray("blocks")){var b=p.getAsJsonArray();protectedBlocks.add((n(m,"x")+b.get(0).getAsInt())+":"+(n(m,"y")+b.get(1).getAsInt())+":"+(n(m,"z")+b.get(2).getAsInt()));}
        }
        for(JsonElement e:built.getAsJsonArray("bases")){
            var b=e.getAsJsonObject();int x=n(b,"x"),z=n(b,"z"),min=n(b,"minY")-16;
            for(int dx=-88;dx<=88;dx++)for(int dz=-88;dz<=88;dz++){
                double d=Math.hypot(dx,dz);if(d<=88)add(x+dx,z+dz,min,b.get("team").getAsString()+(d<=32?"/cœur":"/transition"));
            }
        }
        var hub=built.getAsJsonArray("monuments").get(0).getAsJsonObject();int hx=n(hub,"x"),hz=n(hub,"z");
        for(JsonElement e:built.getAsJsonArray("bases")){var b=e.getAsJsonObject();int x=n(b,"x"),z=n(b,"z");double d=Math.hypot(hx-x,hz-z);path((int)Math.round(x+(hx-x)/d*84),(int)Math.round(z+(hz-z)/d*84),hx,hz);}
        for(JsonElement e:built.getAsJsonArray("monuments")){var m=e.getAsJsonObject();path(hx,hz,n(m,"x"),n(m,"z"));disc(n(m,"x"),n(m,"z"),40,40,"abords-monuments");}
        path(hx,hz,40,265);path(40,265,0,350);disc(0,265,39,40,"rives-du-lac");
        for(JsonElement e:built.getAsJsonArray("supplies")){var m=e.getAsJsonObject();disc(n(m,"x"),n(m,"z"),16,n(m,"y")-20,"abords-ravitaillements");}
        getLogger().info("CORRECTIONS CLEAN : "+columns.size()+" colonnes ; blocs de monuments protégés, drapeaux hors catalogue naturel.");
    }
    private void preload(){
        Set<String> seen=new HashSet<>();ArrayDeque<int[]> chunks=new ArrayDeque<>();
        for(Column c:columns.values())for(int dx=-1;dx<=1;dx++)for(int dz=-1;dz<=1;dz++){int x=(c.x>>4)+dx,z=(c.z>>4)+dz;if(seen.add(x+":"+z))chunks.add(new int[]{x,z});}
        new BukkitRunnable(){int active;
            @Override public void run(){
                if(chunks.isEmpty()&&active==0){cancel();try{Bukkit.getServerTickManager().setFrozen(true);protectedBefore=snapshot();nextPass();}catch(Throwable ex){fail(ex);}return;}
                while(active<3&&!chunks.isEmpty()){
                    int[] c=chunks.removeFirst();active++;
                    world.getChunkAtAsync(c[0],c[1],false).whenComplete((chunk,error)->Bukkit.getScheduler().runTask(MapV2Corrections.this,()->{
                        active--;if(error!=null||chunk==null){cancel();fail(new IllegalStateException("Chunk source absent",error));}else chunk.addPluginChunkTicket(MapV2Corrections.this);
                    }));
                }
            }
        }.runTaskTimer(this,1,1);
    }
    private Map<String,String> snapshot()throws Exception{
        Map<String,String> result=new TreeMap<>();
        for(JsonElement e:built.getAsJsonArray("monuments")){
            var m=e.getAsJsonObject();var plan=JsonParser.parseString(Files.readString(repo.resolve("maps/v2/structures/"+m.get("id").getAsString()+".json"))).getAsJsonObject();
            StringBuilder content=new StringBuilder();
            for(JsonElement b:plan.getAsJsonArray("blocks")){
                var a=b.getAsJsonArray();var block=world.getBlockAt(n(m,"x")+a.get(0).getAsInt(),n(m,"y")+a.get(1).getAsInt(),n(m,"z")+a.get(2).getAsInt());
                content.append(block.getBlockData().getAsString()).append(';');
                if(block.getState()instanceof Chest chest)content.append(Arrays.toString(chest.getBlockInventory().getContents()));
            }
            result.put(m.get("id").getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content.toString().getBytes(StandardCharsets.UTF_8))));
        }
        for(JsonElement e:built.getAsJsonArray("bases")){
            var b=e.getAsJsonObject();StringBuilder content=new StringBuilder();
            for(int y=n(b,"flagY");y<n(b,"flagY")+9;y++)content.append(world.getBlockAt(n(b,"x"),y,n(b,"z")).getBlockData().getAsString());
            for(int h=5;h<=7;h++)for(int dx=1;dx<=4;dx++)content.append(world.getBlockAt(n(b,"x")+dx,n(b,"flagY")+h,n(b,"z")+(dx==4?1:0)).getBlockData().getAsString());
            result.put("drapeau-"+b.get("team").getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(content.toString().getBytes(StandardCharsets.UTF_8))));
        }
        for(JsonElement e:built.getAsJsonArray("supplies")){var s=e.getAsJsonObject();Chest c=(Chest)world.getBlockAt(n(s,"x"),n(s,"y"),n(s,"z")).getState();result.put(s.get("id").getAsString(),c.getBlockData().getAsString()+Arrays.toString(c.getBlockInventory().getContents()));}
        return result;
    }
    private void nextPass(){
        cleaner=new TerrainCleanup();passChanges=0;pass++;Iterator<Column> iterator=columns.values().iterator();
        new BukkitRunnable(){
            @Override public void run(){long start=System.nanoTime();
                try{
                    int processed=0;while(iterator.hasNext()&&processed++<60&&System.nanoTime()-start<5_000_000){
                        Column c=iterator.next();var removed=cleaner.cleanColumn(world,c.x,c.z,c.minY,b->protectedBlocks.contains(b.getX()+":"+b.getY()+":"+b.getZ()));visited++;
                        int changed=removed.values().stream().mapToInt(Integer::intValue).sum();passChanges+=changed;
                        if(changed>0){var byType=counts.computeIfAbsent(c.zone,k->new TreeMap<>());removed.forEach((type,count)->byType.merge(type,count,Integer::sum));}
                    }
                    worstSlice=Math.max(worstSlice,(System.nanoTime()-start)/1e6);
                    if(!iterator.hasNext()){
                        cancel();passes.add(passChanges);getLogger().info("CORRECTIONS CLEAN pass="+pass+" removed="+passChanges);
                        if(passChanges==0){if(!protectedBefore.equals(snapshot()))throw new AssertionError("Une zone protégée a changé.");finish();}
                        else if(pass>=16)throw new AssertionError("Nettoyage non convergent.");else nextPass();
                    }
                }catch(Throwable ex){cancel();fail(ex);}
            }
        }.runTaskTimer(this,1,1);
    }
    private void finish()throws Exception{
        world.save();Bukkit.getServerTickManager().setFrozen(frozen);
        Map<String,Object> report=new LinkedHashMap<>();report.put("instance","runtime/map-v2-fixes");report.put("zones",counts);report.put("passChanges",passes);
        report.put("columns",columns.size());report.put("visitedColumns",visited);report.put("worstSliceMs",worstSlice);report.put("idempotent",passes.getLast()==0);
        report.put("protectedSnapshotsUnchanged",true);report.put("protectedSnapshots",protectedBefore);report.put("terrainRebuilt",false);report.put("lootRegenerated",false);report.put("visualValidation",false);
        Files.writeString(repo.resolve("tests/results/v2-fixes-cleanup.json"),gson.toJson(report)+"\n",StandardCharsets.UTF_8);
        getLogger().info("CORRECTIONS CLEAN SUCCESS removed="+passes.stream().mapToInt(Integer::intValue).sum());Bukkit.shutdown();
    }
    private void fail(Throwable ex){getLogger().log(Level.SEVERE,"CORRECTIONS FAILED",ex);Bukkit.shutdown();}
    @Override public void onDisable(){if(world!=null)world.removePluginChunkTickets(this);Bukkit.getServerTickManager().setFrozen(frozen);}
}
