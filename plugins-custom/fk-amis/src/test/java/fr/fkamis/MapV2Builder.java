package fr.fkamis;

import com.google.gson.*;
import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fkpi.FkPI;
import fr.devsylone.fkpi.teams.*;
import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.EntityType;
import org.bukkit.inventory.ItemStack;
import org.bukkit.persistence.PersistentDataType;
import org.bukkit.plugin.java.JavaPlugin;
import org.bukkit.scheduler.BukkitRunnable;

import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Outil de chantier séparé : refuse toute instance autre que runtime/map-v2. */
public final class MapV2Builder extends JavaPlugin {
    private final Gson gson = new GsonBuilder().setPrettyPrinting().create();
    private final ArrayDeque<Runnable> work = new ArrayDeque<>();
    private final List<Map<String,Object>> bases = new ArrayList<>(), monuments = new ArrayList<>(), supplies = new ArrayList<>();
    private final List<Map<String,Object>> landscape = new ArrayList<>();
    private final Map<Long,Integer> groundCache = new HashMap<>();
    private final Map<String,org.bukkit.block.data.BlockData> dataCache = new HashMap<>();
    private final Set<Long> roads = new HashSet<>();
    private final Set<Long> modifiedColumns = new HashSet<>();
    private final Map<String,Integer> cleanedNatural = new TreeMap<>();
    private Path repo, instance, marker;
    private World world;
    private JavaPlugin companion;
    private long changed;
    private int peakQueue;
    private double worstSliceMs;

    @Override public void onEnable() {
        try {
            instance = Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();
            boolean verificationCopy=instance.getFileName().toString().equals("map-v2-fixes")&&System.getProperty("fk.mapv2.mode","").equals("verify");
            if ((!instance.getFileName().toString().equals("map-v2")&&!verificationCopy) || !Boolean.getBoolean("fk.mapv2.authorized"))
                throw new IllegalStateException("Chantier autorisé uniquement dans runtime/map-v2.");
            repo = instance.getParent().getParent(); marker = instance.resolve("map-v2-construction.json");
            world = Objects.requireNonNull(Bukkit.getWorld("world"));
            companion = (JavaPlugin) Objects.requireNonNull(Bukkit.getPluginManager().getPlugin("FKAmis"));
            if ((boolean) field(field(companion,"state"),"started") || !((Map<?,?>) field(companion,"objectives")).isEmpty())
                throw new IllegalStateException("Ne jamais construire dans une partie commencée ou contenant des objectifs.");
            Bukkit.getScheduler().runTaskLater(this, () -> {
                try {
                    String mode = System.getProperty("fk.mapv2.mode", "survey");
                    preload(() -> {
                        try {
                            if (mode.equals("survey")) { survey(); stopLater(); }
                            else if (mode.equals("build")) { if (Files.exists(marker)) throw new IllegalStateException("Chantier déjà engagé : restaurer une copie avant de recommencer."); plan(); runWork(); }
                            else if (mode.equals("verify")) { readBuilt(); verify(); stopLater(); }
                            else if (mode.equals("repair-loot")) { readBuilt(); repairLoot(); verify(); getLogger().info("MAP V2 REPAIR-LOOT SUCCESS"); stopLater(); }
                            else throw new IllegalArgumentException("Mode de chantier inconnu.");
                        } catch (Throwable ex) { fail(ex); }
                    });
                } catch (Throwable ex) { fail(ex); }
            }, 30);
        } catch (Throwable ex) { fail(ex); }
    }
    private void fail(Throwable ex) { getLogger().log(Level.SEVERE,"MAP V2 FAILED",ex); Bukkit.shutdown(); }
    private void stopLater() { Bukkit.getScheduler().runTaskLater(this,Bukkit::shutdown,40); }
    private void preload(Runnable then) {
        Set<Long> chunks=new LinkedHashSet<>();
        for(int x=-550;x<=550;x+=16)for(int z=-550;z<=550;z+=16) {
            boolean nearBase=Math.abs(Math.abs(x)-240)<155&&Math.abs(Math.abs(z)-240)<155;
            boolean axis=Math.abs(x)<112||Math.abs(z)<112;
            if(nearBase||axis)chunks.add(position(x>>4,z>>4));
        }
        ArrayDeque<Long> pending=new ArrayDeque<>(chunks);
        new BukkitRunnable(){
            int active;
            @Override public void run(){
                if(pending.isEmpty()&&active==0){cancel();then.run();return;}
                while(active<3&&!pending.isEmpty()){
                    long p=pending.removeFirst();int x=(int)(p>>32),z=(int)p;active++;
                    world.getChunkAtAsync(x,z,false).whenComplete((chunk,ex)->Bukkit.getScheduler().runTask(MapV2Builder.this,()->{
                        active--;
                        if(ex!=null||chunk==null){cancel();fail(new IllegalStateException("Chunk de chantier non prégénéré "+x+","+z,ex));return;}
                        chunk.addPluginChunkTicket(MapV2Builder.this);
                    }));
                }
            }
        }.runTaskTimer(this,1,1);
    }
    private Object field(Object object, String name) throws Exception {
        Field f = object.getClass().getDeclaredField(name); f.setAccessible(true); return f.get(object);
    }
    private Object invoke(Object object, String name) throws Exception {
        Method m = object.getClass().getDeclaredMethod(name); m.setAccessible(true); return m.invoke(object);
    }
    private Map<String,Object> record(Object... pairs) {
        Map<String,Object> out = new LinkedHashMap<>();
        for (int i=0;i<pairs.length;i+=2) out.put((String)pairs[i],pairs[i+1]); return out;
    }
    private void write(Path path, Object value) throws Exception {
        Files.createDirectories(path.getParent()); Files.writeString(path,gson.toJson(value)+"\n",StandardCharsets.UTF_8);
    }
    private static int number(Map<String,Object> r,String name) { return ((Number)r.get(name)).intValue(); }
    private long position(int x,int z) { return ((long)x<<32) ^ (z&0xffffffffL); }
    private boolean groundMaterial(Material material) {
        String s=material.name();
        return Set.of("GRASS_BLOCK","DIRT","COARSE_DIRT","ROOTED_DIRT","PODZOL","SAND","RED_SAND","GRAVEL","CLAY",
                "MOSS_BLOCK","MUD","PACKED_MUD","SNOW_BLOCK","MYCELIUM").contains(s)
                || s.equals("STONE") || s.equals("ANDESITE") || s.equals("GRANITE") || s.equals("DIORITE") || s.contains("TERRACOTTA");
    }
    private int ground(int x,int z) {
        return groundCache.computeIfAbsent(position(x,z), ignored -> {
            int y=world.getHighestBlockYAt(x,z,HeightMap.MOTION_BLOCKING_NO_LEAVES);
            for (;y>world.getMinHeight()+2;y--) if (groundMaterial(world.getBlockAt(x,y,z).getType())) return y;
            throw new IllegalStateException("Colonne sans terrain naturel à "+x+","+z);
        });
    }
    private Map<String,Object> inspect(int x,int z,int radius) {
        int low=999,high=-999,water=0,samples=0;
        List<Integer> ys=new ArrayList<>();
        for(int dx=-radius;dx<=radius;dx+=16) for(int dz=-radius;dz<=radius;dz+=16) {
            int y=ground(x+dx,z+dz); ys.add(y); low=Math.min(low,y); high=Math.max(high,y); samples++;
            Material above=world.getBlockAt(x+dx,y+1,z+dz).getType(); if(above==Material.WATER||above==Material.LAVA) water++;
        }
        Collections.sort(ys); int median=ys.get(ys.size()/2);
        return record("x",x,"z",z,"groundY",median,"minY",low,"maxY",high,"wetSamples",water,"samples",samples,
                "biome",world.getBiome(x,ground(x,z)+1,z).getKey().toString(),
                "score",high-low+water*12+Math.abs(Math.abs(x)-240)*.04+Math.abs(Math.abs(z)-240)*.04);
    }
    private void survey() throws Exception {
        List<Map<String,Object>> candidates=new ArrayList<>();
        String[] names={"Rouge","Bleue","Verte","Jaune"};
        for(int i=0;i<4;i++) {
            Map<String,Object> best=null;
            for(int ax:new int[]{200,240,280}) for(int az:new int[]{200,240,280}) {
                int x=i%2==0?-ax:ax,z=i<2?-az:az;
                Map<String,Object> sample=inspect(x,z,32); sample.put("team",names[i]); candidates.add(sample);
                if(best==null||((Number)sample.get("score")).doubleValue()<((Number)best.get("score")).doubleValue()) best=sample;
            }
            best=new LinkedHashMap<>(Objects.requireNonNull(best)); best.put("radius",80); bases.add(best);
        }
        List<Map<String,Object>> poi=new ArrayList<>();
        String[] ids={"cercle-des-quatre-vents","temple-des-racines","mine-des-brumes","tour-des-vents","camp-des-eclaireurs","sanctuaire-des-sources","crypte-des-veilleurs"};
        int[][] targets={{0,0},{0,-400},{400,0},{0,350},{-400,0},{0,175},{0,-175}};
        for(int i=0;i<ids.length;i++){
            Map<String,Object> best=null;
            for(int dx:new int[]{-80,-40,0,40,80})for(int dz:new int[]{-48,0,48}){
                int x=targets[i][0]+dx,z=targets[i][1]+dz;
                if(insideBase(x,z,38))continue;
                Map<String,Object> sample=inspect(x,z,16);
                if(number(sample,"wetSamples")>0||number(sample,"groundY")<64||number(sample,"maxY")-number(sample,"minY")>24)continue;
                double score=((Number)sample.get("score")).doubleValue()+Math.hypot(dx,dz)*.08;
                sample.put("poiScore",score);
                if(best==null||score<((Number)best.get("poiScore")).doubleValue())best=sample;
            }
            if(best==null)throw new IllegalStateException("Aucun terrain sec et accessible trouvé pour "+ids[i]);
            best.put("id",ids[i]);poi.add(best);
        }
        List<Map<String,Object>> siteSelected=new ArrayList<>();
        int[][] wanted={{-100,-100},{100,-100},{-100,100},{100,100},{0,-480},{480,0},{0,480},{-480,0}};
        String[] zones={"Carrefour nord-ouest","Carrefour nord-est","Carrefour sud-ouest","Carrefour sud-est","Lisière nord","Crête est","Vallon sud","Bois ouest"};
        for(int i=0;i<wanted.length;i++){
            Map<String,Object> best=null;
            for(int dx:new int[]{-80,-40,0,40,80})for(int dz:new int[]{-80,-40,0,40,80}){
                int x=wanted[i][0]+dx,z=wanted[i][1]+dz;
                if(Math.abs(x)>560||Math.abs(z)>560)continue;
                if(insideBase(x,z,6)||poi.stream().anyMatch(p->Math.hypot(number(p,"x")-x,number(p,"z")-z)<(p.get("id").toString().startsWith("mine")?40:35)))continue;
                if(siteSelected.stream().anyMatch(s->Math.hypot(number(s,"x")-x,number(s,"z")-z)<65))continue;
                int y=ground(x,z);if(y<63||world.getBlockAt(x,y+1,z).isLiquid())continue;
                double score=Math.hypot(dx,dz);
                if(best==null||score<((Number)best.get("score")).doubleValue())best=record("x",x,"z",z,"groundY",y,"score",score);
            }
            if(best==null)throw new IllegalStateException("Aucun support sec trouvé pour le site "+i);
            best.put("id","supply-"+(i+1));best.put("zone",zones[i]);siteSelected.add(best);
        }
        Map<String,Object> report=record("schema",1,"seed",world.getSeed(),"border",1200,"candidates",candidates,"selected",bases,"poiSelected",poi,"siteSelected",siteSelected,"visualValidation",false);
        write(repo.resolve("maps/v2/terrain-survey.json"),report);
        getLogger().info("MAP V2 SURVEY SUCCESS : "+gson.toJson(bases));
    }
    @SuppressWarnings("unchecked") private void plan() throws Exception {
        Map<String,Object> survey=gson.fromJson(Files.readString(repo.resolve("maps/v2/terrain-survey.json")),Map.class);
        bases.addAll((List<Map<String,Object>>)survey.get("selected"));
        if(((Number)survey.get("seed")).longValue()!=world.getSeed()) throw new IllegalStateException("Graine du relevé différente.");
        write(marker,record("status","IN_PROGRESS","seed",world.getSeed()));
        world.getWorldBorder().setCenter(0,0); world.getWorldBorder().setSize(1200);
        for(Map<String,Object> base:bases) {
            int cx=number(base,"x"),cz=number(base,"z"),y=number(base,"groundY");
            terraform(cx,cz,y,32,80,true);
            work.add(()->{ try{ establishBase(base); }catch(Exception ex){throw new IllegalStateException(ex);} });
        }
        List<Map<String,Object>> poiSelected=(List<Map<String,Object>>)Objects.requireNonNull(survey.get("poiSelected"));
        for(Map<String,Object> poi:poiSelected) {
            String id=(String)poi.get("id"); int x=number(poi,"x"),z=number(poi,"z");
            int y=number(poi,"groundY")+1; Map<String,Object> monument=record("id",id,"x",x,"y",y,"z",z,"radius",id.startsWith("mine")?30:id.startsWith("crypte")?26:19);
            assertNeutral(x,z,number(monument,"radius")); monuments.add(monument);
            if(!id.startsWith("crypte")) terraform(x,z,y-1,id.startsWith("cercle")?16:13,id.startsWith("mine")?34:26,false);
            else terraform(x,z+23,y-1,4,11,false);
            JsonObject blueprint=JsonParser.parseString(Files.readString(repo.resolve("maps/v2/structures/"+id+".json"))).getAsJsonObject();
            for(JsonElement item:blueprint.getAsJsonArray("blocks")) {
                JsonArray b=item.getAsJsonArray(); int bx=x+b.get(0).getAsInt(),by=y+b.get(1).getAsInt(),bz=z+b.get(2).getAsInt(); String type=b.get(3).getAsString();
                work.add(()->put(bx,by,bz,type));
            }
            for(JsonElement item:blueprint.getAsJsonArray("loot")) {
                JsonObject chest=item.getAsJsonObject();
                work.add(()->fillMonument(x+chest.get("x").getAsInt(),y+chest.get("y").getAsInt(),z+chest.get("z").getAsInt(),chest));
            }
            work.add(()->monument.put("placed",true));
            if(id.startsWith("crypte"))for(int step=0;step<4;step++){
                int entryZ=z+23-step,feet=y-step;
                work.add(()->{for(int dx=-1;dx<=1;dx++)for(int yy=feet;yy<=world.getHighestBlockYAt(x+dx,entryZ);yy++)put(x+dx,yy,entryZ,"minecraft:air");});
            }
        }
        // Vallon lacustre et cascade, modelés uniquement dans la zone neutre.
        lake(0,265,13); waterfall(24,175);
        Map<String,Object> hub=monuments.getFirst();int hubX=number(hub,"x"),hubZ=number(hub,"z");
        for(Map<String,Object> base:bases) {
            int cx=number(base,"x"),cz=number(base,"z");
            double d=Math.hypot(hubX-cx,hubZ-cz); int sx=(int)Math.round(cx+(hubX-cx)/d*84),sz=(int)Math.round(cz+(hubZ-cz)/d*84);
            path(sx,sz,hubX,hubZ);
        }
        for(Map<String,Object> m:monuments)path(hubX,hubZ,number(m,"x"),number(m,"z"));
        path(hubX,hubZ,40,265);path(40,265,0,350);
        rocksAndVegetation();
        for(Map<String,Object> selectedSite:(List<Map<String,Object>>)Objects.requireNonNull(survey.get("siteSelected"))) {
            int x=number(selectedSite,"x"),z=number(selectedSite,"z"),y=number(selectedSite,"groundY")+1; String id=(String)selectedSite.get("id");
            assertNeutral(x,z,4); terraform(x,z,y-1,3,8,false);
            Map<String,Object> site=record("id",id,"zone",selectedSite.get("zone"),"x",x,"y",y,"z",z); supplies.add(site);
            work.add(()->{
                for(int dx=-1;dx<=1;dx++) for(int dz=-1;dz<=1;dz++) put(x+dx,y-1,z+dz,"minecraft:mossy_stone_bricks");
                put(x,y,z,"minecraft:chest[facing=south,type=single,waterlogged=false]");
                Chest chest=(Chest)world.getBlockAt(x,y,z).getState();
                chest.getPersistentDataContainer().set(new NamespacedKey(companion,"supply-id"),PersistentDataType.STRING,id);
                chest.getBlockInventory().clear(); chest.update(true,false);
            });
        }
        peakQueue=work.size();
    }
    private void assertNeutral(int x,int z,int radius) {
        for(Map<String,Object> b:bases) if(Math.abs(number(b,"x")-x)<=80+radius && Math.abs(number(b,"z")-z)<=80+radius)
            throw new IllegalStateException("Point d'intérêt dans un royaume : "+x+","+z);
    }
    private boolean insideBase(int x,int z,int margin) {
        return bases.stream().anyMatch(b->Math.abs(number(b,"x")-x)<=80+margin&&Math.abs(number(b,"z")-z)<=80+margin);
    }
    private void put(int x,int y,int z,String block) {
        var data=dataCache.computeIfAbsent(block,Bukkit::createBlockData);
        Block target=world.getBlockAt(x,y,z);
        if(!target.getBlockData().equals(data)) { target.setBlockData(data,false); changed++; modifiedColumns.add(position(x,z)); }
    }
    private void terraform(int cx,int cz,int center,int inner,int outer,boolean kingdom) {
        for(int dx=-outer;dx<=outer;dx++) for(int dz=-outer;dz<=outer;dz++) {
            double distance=Math.hypot(dx,dz); if(distance>outer) continue;
            int x=cx+dx,z=cz+dz;
            double t=Math.max(0,Math.min(1,(distance-inner)/(outer-inner))); double smooth=t*t*(3-2*t);
            double micro=kingdom?(Math.sin(dx/16.0)+Math.cos(dz/21.0))*.8:0;
            work.add(()->{
                int old=ground(x,z);
                int target=(int)Math.round(old*smooth+(center+micro)*(1-smooth));
                int ny=Math.max(old-12,Math.min(old+(kingdom?24:12),target));
                if(ny==old&&distance>inner+4) return;
                int top=world.getHighestBlockYAt(x,z,HeightMap.WORLD_SURFACE);
                for(int y=ny+1;y<=Math.max(top,ny+2);y++) put(x,y,z,"minecraft:air");
                for(int y=Math.min(old-2,ny-3);y<ny-2;y++) put(x,y,z,"minecraft:stone");
                put(x,ny-2,z,"minecraft:dirt");put(x,ny-1,z,"minecraft:dirt");put(x,ny,z,"minecraft:grass_block");
                groundCache.put(position(x,z),ny);
            });
        }
    }
    @SuppressWarnings("unchecked") private void establishBase(Map<String,Object> base) throws Exception {
        String name=(String)base.get("team"); int x=number(base,"x"),z=number(base,"z"),y=ground(x,z)+1;
        Team team=Objects.requireNonNull(FkPI.getInstance().getTeamManager().getTeam(name));
        team.setBase(new Base(team,new Location(world,x+.5,y,z+.5),80,Material.AIR,(byte)0));
        Fk.getInstance().getWorldManager().invalidateBaseWorldsCache(FkPI.getInstance().getTeamManager());
        ((Map<String,Location>)field(companion,"spawns")).put(name,new Location(world,x-7+.5,ground(x-7,z)+1,z+.5));
        ((Set<String>)field(companion,"terrainValidated")).remove(name); // Validation visuelle toujours humaine.
        String color=switch(name){case "Rouge"->"red";case "Bleue"->"blue";case "Verte"->"green";default->"yellow";};
        for(int dx=-2;dx<=2;dx++) for(int dz=-2;dz<=2;dz++) if(dx*dx+dz*dz<=5) put(x+dx,ground(x+dx,z+dz),z+dz,"minecraft:mossy_stone_bricks");
        for(int h=0;h<9;h++) put(x,y+h,z,"minecraft:spruce_fence");
        for(int h=5;h<=7;h++) for(int offset=1;offset<=4;offset++) put(x+offset,y+h,z+(offset==4?1:0),"minecraft:"+color+"_wool");
        base.put("flagY",y); base.put("flagHeight",9);base.put("flagColor",color);
        base.put("spawn",record("x",x-7+.5,"y",ground(x-7,z)+1,"z",z+.5));
        base.put("terrainPrepared",true);base.put("visualValidation",false);
    }
    private void fillMonument(int x,int y,int z,JsonObject recipe) {
        if(!(world.getBlockAt(x,y,z).getState() instanceof Chest chest)) throw new IllegalStateException("Coffre de monument absent.");
        if(!chest.getBlockInventory().isEmpty()) throw new IllegalStateException("Le chantier refuse un conteneur déjà rempli.");
        for(JsonElement element:recipe.getAsJsonArray("items")) {
            JsonObject item=element.getAsJsonObject(); String material=item.get("material").getAsString();
            if(!Set.of("GOLD_INGOT","LAPIS_LAZULI","BOOK","BREAD","IRON_INGOT","COAL","COPPER_INGOT","IRON_PICKAXE","ARROW","COOKED_BEEF","SHIELD","LEATHER","TORCH","DIAMOND").contains(material)) throw new IllegalStateException("Loot fixe interdit.");
            chest.getSnapshotInventory().addItem(new ItemStack(Material.valueOf(material),item.get("amount").getAsInt()));
        }
        chest.update(true,false);
    }
    private void repairLoot() throws Exception {
        if((long)field(field(companion,"supplies"),"event")!=0L)throw new IllegalStateException("Réparation interdite après un événement de ravitaillement.");
        List<Runnable> pending=new ArrayList<>();
        for(Map<String,Object>m:monuments){
            JsonObject plan=JsonParser.parseString(Files.readString(repo.resolve("maps/v2/structures/"+m.get("id")+".json"))).getAsJsonObject();
            for(JsonElement element:plan.getAsJsonArray("loot")){
                JsonObject loot=element.getAsJsonObject();int x=number(m,"x")+loot.get("x").getAsInt(),y=number(m,"y")+loot.get("y").getAsInt(),z=number(m,"z")+loot.get("z").getAsInt();
                if(!(world.getBlockAt(x,y,z).getState()instanceof Chest chest)||!chest.getBlockInventory().isEmpty())throw new IllegalStateException("Réparation refusée : coffre absent ou non vide.");
                pending.add(()->fillMonument(x,y,z,loot));
            }
        }
        if(pending.size()!=6)throw new IllegalStateException("Six coffres de monument attendus.");
        pending.forEach(Runnable::run);world.save();
    }
    private void path(int x1,int z1,int x2,int z2) {
        double length=Math.hypot(x2-x1,z2-z1);
        if(length<1)return;
        for(int n=0;n<=(int)length;n++) {
            double t=n/length; int cx=(int)Math.round(x1+(x2-x1)*t+Math.sin(t*Math.PI)*Math.sin(t*6)*5);
            int cz=(int)Math.round(z1+(z2-z1)*t+Math.sin(t*Math.PI)*Math.cos(t*5)*5);
            for(int dx=-1;dx<=1;dx++) for(int dz=-1;dz<=1;dz++) {
                int x=cx+dx,z=cz+dz; if(insideBase(x,z,1)||monuments.stream().anyMatch(m->Math.hypot(number(m,"x")-x,number(m,"z")-z)<number(m,"radius")+1)) continue;
                work.add(()->{
                    if(!roads.add(position(x,z)))return;
                    int y=ground(x,z); Material above=world.getBlockAt(x,y+1,z).getType();
                    if(above==Material.LAVA)return;
                    if(above==Material.WATER){
                        int surface=world.getHighestBlockYAt(x,z,HeightMap.MOTION_BLOCKING_NO_LEAVES);
                        while(surface>y&&world.getBlockAt(x,surface,z).getType()!=Material.WATER)surface--;
                        int deck=surface+1;
                        if(Math.floorMod(x,4)==0||Math.floorMod(z,4)==0)for(int support=y+1;support<deck;support++)put(x,support,z,"minecraft:oak_log[axis=y]");
                        put(x,deck,z,"minecraft:oak_planks");return;
                    }
                    put(x,y,z,((x*17+z*31)&7)==0?"minecraft:gravel":"minecraft:dirt_path");
                    int top=world.getHighestBlockYAt(x,z,HeightMap.WORLD_SURFACE);
                    for(int yy=y+1;yy<=Math.max(y+3,top);yy++)if(!world.getBlockAt(x,yy,z).isLiquid())put(x,yy,z,"minecraft:air");
                });
            }
        }
    }
    private void lake(int cx,int cz,int r) {
        int level=ground(cx,cz)-1;
        terraform(cx,cz,level,r+2,r+18,false);
        landscape.add(record("type","lac","x",cx,"y",level,"z",cz,"radius",r));
        for(int dx=-r-4;dx<=r+4;dx++) for(int dz=-r-4;dz<=r+4;dz++) {
            double d=Math.hypot(dx,dz); if(d>r+3)continue; int x=cx+dx,z=cz+dz;
            work.add(()->{
                if(d<r) {
                    int bottom=level-1-(int)Math.round((1-d/r)*2);
                    for(int y=bottom;y<=level;y++) put(x,y,z,y==bottom?"minecraft:clay":"minecraft:water[level=0]");
                    for(int y=level+1;y<=Math.max(level+2,world.getHighestBlockYAt(x,z));y++) put(x,y,z,"minecraft:air");
                } else {
                    for(int y=level-3;y<=level;y++) put(x,y,z,y==level?"minecraft:grass_block":"minecraft:dirt");
                    for(int y=level+1;y<=world.getHighestBlockYAt(x,z);y++) put(x,y,z,"minecraft:air");
                }
            });
        }
    }
    private void waterfall(int cx,int cz) {
        int y=ground(cx,cz);
        landscape.add(record("type","cascade_rocaille","x",cx,"y",y,"z",cz));
        for(int dx=-5;dx<=5;dx++) for(int dz=-5;dz<=5;dz++) {
            int x=cx+dx,z=cz+dz; double d=Math.hypot(dx,dz); boolean channel=dz==0&&dx>=0;
            if(d>5)continue;
            work.add(()->{
                int h=(int)Math.max(0,6-d*1.2);
                for(int yy=ground(x,z);yy<=y+h;yy++) put(x,yy,z,"minecraft:mossy_cobblestone");
                if(channel) for(int yy=y;yy<=y+h+1;yy++) put(x,yy,z,"minecraft:water[level=0]");
            });
        }
    }
    private void rocksAndVegetation() {
        Random random=new Random(732401);
        for(int i=0;i<110;i++) {
            int x=random.nextInt(1060)-530,z=random.nextInt(1060)-530;
            if(insideBase(x,z,12)||monuments.stream().anyMatch(m->Math.hypot(number(m,"x")-x,number(m,"z")-z)<number(m,"radius")+12))continue;
            int y=ground(x,z); if(world.getBlockAt(x,y+1,z).isLiquid())continue;
            if(i%4==0) {
                landscape.add(record("type","rochers","x",x,"y",y,"z",z));
                for(int dx=-2;dx<=2;dx++) for(int dz=-2;dz<=2;dz++) for(int dy=0;dy<=2;dy++) {
                    if(dx*dx+dz*dz+dy*dy>6)continue; int bx=x+dx,by=y+dy,bz=z+dz;
                    work.add(()->put(bx,by,bz,(bx+bz)%3==0?"minecraft:moss_block":"minecraft:andesite"));
                }
            } else {
                int fy=y+1; String plant=i%3==0?"minecraft:fern":"minecraft:poppy";
                work.add(()->{if(world.getBlockAt(x,fy,z).getType()==Material.AIR&&world.getBlockAt(x,fy-1,z).getType()==Material.GRASS_BLOCK)put(x,fy,z,plant);});
            }
        }
    }
    private void runWork() {
        getLogger().info("MAP V2 BUILD : "+work.size()+" opérations préparées.");
        new BukkitRunnable(){
            int ticks;
            @Override public void run(){
                long start=System.nanoTime();
                try {
                    int processed=0;
                    while(!work.isEmpty()&&processed++<300&&System.nanoTime()-start<6_000_000)work.removeFirst().run();
                    worstSliceMs=Math.max(worstSliceMs,(System.nanoTime()-start)/1e6);
                    if(++ticks%200==0)getLogger().info("MAP V2 BUILD remaining="+work.size()+" changed="+changed);
                    if(work.isEmpty()) {cancel();prepareCleanup();}
                }catch(Throwable ex){cancel();fail(ex);}
            }
        }.runTaskTimer(this,1,1);
    }
    private void prepareCleanup(){
        Bukkit.getScheduler().runTaskAsynchronously(this,()->{
            Set<String> protectedBlocks=new HashSet<>();
            try{
                for(Map<String,Object> m:monuments){
                    var plan=JsonParser.parseString(Files.readString(repo.resolve("maps/v2/structures/"+m.get("id")+".json"))).getAsJsonObject();
                    for(JsonElement element:plan.getAsJsonArray("blocks")){var b=element.getAsJsonArray();protectedBlocks.add((number(m,"x")+b.get(0).getAsInt())+":"+(number(m,"y")+b.get(1).getAsInt())+":"+(number(m,"z")+b.get(2).getAsInt()));}
                }
            }catch(Throwable ex){Bukkit.getScheduler().runTask(this,()->fail(ex));return;}
            Set<Long> expanded=new HashSet<>();
            for(long column:modifiedColumns){int x=(int)(column>>32),z=(int)column;
                for(int dx=-8;dx<=8;dx++)for(int dz=-8;dz<=8;dz++)expanded.add(position(x+dx,z+dz));
            }
            Bukkit.getScheduler().runTask(this,()->cleanupAfterTerrain(0,expanded,protectedBlocks));
        });
    }
    private void cleanupAfterTerrain(int pass,Set<Long> expanded,Set<String> protectedBlocks) {
        if(pass>=16){fail(new IllegalStateException("Nettoyage naturel non convergent."));return;}
        Iterator<Long> iterator=expanded.iterator();TerrainCleanup cleaner=new TerrainCleanup();
        new BukkitRunnable(){int removed;
            @Override public void run(){long start=System.nanoTime();
                try{
                    int processed=0;while(iterator.hasNext()&&processed++<40&&System.nanoTime()-start<5_000_000){
                        long p=iterator.next();int x=(int)(p>>32),z=(int)p;
                        if(!world.isChunkLoaded(x>>4,z>>4))continue;
                        var result=cleaner.cleanColumn(world,x,z,40,b->protectedBlocks.contains(b.getX()+":"+b.getY()+":"+b.getZ()));removed+=result.values().stream().mapToInt(Integer::intValue).sum();
                        result.forEach((type,count)->cleanedNatural.merge(type,count,Integer::sum));
                    }
                    if(!iterator.hasNext()){cancel();changed+=removed;if(removed==0)finish();else cleanupAfterTerrain(pass+1,expanded,protectedBlocks);}
                }catch(Throwable ex){cancel();fail(ex);}
            }
        }.runTaskTimer(this,1,1);
    }
    private void finish() throws Exception {
        YamlConfiguration config=new YamlConfiguration();
        Path configPath=instance.resolve("plugins/FKAmis/supplies.yml");
        try(var stream=Objects.requireNonNull(companion.getResource("supplies.yml"))) {
            config.loadFromString(new String(stream.readAllBytes(),StandardCharsets.UTF_8));
        }
        config.set("enabled",true);config.set("test-mode",false);
        for(Map<String,Object> site:supplies){
            String path="locations."+site.get("id");
            config.set(path+".world","world");
            for(String key:List.of("x","y","z","zone"))config.set(path+"."+key,site.get(key));
        }
        config.save(configPath.toFile());
        companion.onCommand(Bukkit.getConsoleSender(),Objects.requireNonNull(companion.getCommand("fka")),"fka",new String[]{"supply","reload"});
        invoke(companion,"saveState");
        Map<String,Object> crypt=monuments.stream().filter(m->m.get("id").equals("crypte-des-veilleurs")).findFirst().orElseThrow();
        List<String> guardians=new ArrayList<>();
        for(int offset:new int[]{-3,3}) {
            var skeleton=world.spawn(new Location(world,number(crypt,"x")+offset+.5,number(crypt,"y")-13,number(crypt,"z")+4.5),org.bukkit.entity.Skeleton.class);
            skeleton.setRemoveWhenFarAway(false); skeleton.setPersistent(true);
            guardians.add(skeleton.getUniqueId().toString());
        }
        crypt.put("guardians",guardians);
        world.save();
        Map<String,Object> report=record("schema",1,"status","BUILT","world","runtime/map-v2/world","seed",world.getSeed(),"border",1200,
                "bases",bases,"monuments",monuments,"supplies",supplies,"landscape",landscape,"changedBlocks",changed,
                "peakQueuedOperations",peakQueue,"worstConstructionSliceMs",worstSliceMs,"cleanedNatural",cleanedNatural,"visualValidation",false,"prebuiltForts",0);
        write(marker,report);write(repo.resolve("maps/v2/built-manifest.json"),report);
        write(repo.resolve("maps/monuments.json"),monuments);write(repo.resolve("maps/supply-locations.json"),supplies);
        verify();getLogger().info("MAP V2 BUILD SUCCESS changed="+changed); stopLater();
    }
    @SuppressWarnings("unchecked") private void readBuilt() throws Exception {
        Map<String,Object> report=gson.fromJson(Files.readString(marker),Map.class);
        bases.addAll((List<Map<String,Object>>)report.get("bases"));monuments.addAll((List<Map<String,Object>>)report.get("monuments"));
        supplies.addAll((List<Map<String,Object>>)report.get("supplies"));
    }
    @SuppressWarnings("unchecked") private void verify() throws Exception {
        List<String> passed=new ArrayList<>();
        Map<String,Material> preserved=new HashMap<>();JsonArray previousDifferences=new JsonArray();
        if(instance.getFileName().toString().equals("map-v2-fixes")){
            previousDifferences=JsonParser.parseString(Files.readString(repo.resolve("maps/v2-corrections/preexisting-differences.json"))).getAsJsonObject().getAsJsonArray("differences");
            for(JsonElement entry:previousDifferences){var e=entry.getAsJsonObject();preserved.put(e.get("monument").getAsString()+":"+e.get("x").getAsInt()+":"+e.get("y").getAsInt()+":"+e.get("z").getAsInt(),Objects.requireNonNull(Material.matchMaterial(e.get("source").getAsString())));}
        }
        if(world.getWorldBorder().getSize()!=1200||bases.size()!=4||monuments.size()!=7||supplies.size()!=8)throw new AssertionError("Dimensions ou effectifs de carte invalides.");
        passed.add("Bordure 1200, quatre terrains, sept monuments, huit supports");
        List<Map<String,Object>> distanceReport=new ArrayList<>();
        for(int i=0;i<4;i++)for(int j=i+1;j<4;j++){
            Map<String,Object>a=bases.get(i),b=bases.get(j);int dx=Math.abs(number(a,"x")-number(b,"x")),dz=Math.abs(number(a,"z")-number(b,"z"));
            double distance=Math.hypot(dx,dz);
            if(dx<=160&&dz<=160)throw new AssertionError("Chevauchement de royaumes.");
            if((i/2==j/2||i%2==j%2)&&(distance<400||distance>600))throw new AssertionError("Distance voisine hors cible : "+distance);
            distanceReport.add(record("from",a.get("team"),"to",b.get("team"),"distance",distance));
        }
        passed.add("Aucun chevauchement ; voisins entre 400 et 600 blocs");
        for(Map<String,Object>b:bases){
            int x=number(b,"x"),z=number(b,"z"),y=number(b,"flagY");String color=(String)b.get("flagColor");
            if(world.getBlockAt(x,y+8,z).getType()!=Material.SPRUCE_FENCE||world.getBlockAt(x+2,y+6,z).getType()!=Material.valueOf(color.toUpperCase()+"_WOOL"))throw new AssertionError("Drapeau incorrect : "+b.get("team"));
            Map<String,Object> spawn=(Map<String,Object>)b.get("spawn");Location at=new Location(world,((Number)spawn.get("x")).doubleValue(),number(spawn,"y"),((Number)spawn.get("z")).doubleValue());
            if(!at.getBlock().isPassable()||!at.clone().add(0,1,0).getBlock().isPassable()||!at.clone().subtract(0,1,0).getBlock().getType().isSolid())throw new AssertionError("Spawn dangereux.");
            int min=999,max=-999;
            for(int dx:new int[]{-24,-12,12,24})for(int dz:new int[]{-24,-12,12,24}){
                int surface=world.getHighestBlockYAt(x+dx,z+dz,HeightMap.MOTION_BLOCKING_NO_LEAVES);
                min=Math.min(min,surface);max=Math.max(max,surface);
                if(world.getBlockAt(x+dx,surface,z+dz).isLiquid())throw new AssertionError("Eau sur la surface constructible.");
            }
            b.put("innerGroundRange",max-min);
            if(max-min>6)throw new AssertionError("Terrain central encore trop accidenté : "+b.get("team")+" "+(max-min));
            passed.add("Drapeau "+color+" et spawn sûr : "+b.get("team"));
        }
        for(Map<String,Object>m:monuments){
            assertNeutral(number(m,"x"),number(m,"z"),number(m,"radius"));
            JsonObject plan=JsonParser.parseString(Files.readString(repo.resolve("maps/v2/structures/"+m.get("id")+".json"))).getAsJsonObject();
            for(JsonElement element:plan.getAsJsonArray("blocks")){
                JsonArray b=element.getAsJsonArray();int x=number(m,"x")+b.get(0).getAsInt(),y=number(m,"y")+b.get(1).getAsInt(),z=number(m,"z")+b.get(2).getAsInt();
                var expected=Bukkit.createBlockData(b.get(3).getAsString());
                // Vignes, feuilles et fluides peuvent évoluer naturellement ; les blocs solides doivent exister.
                Material actual=world.getBlockAt(x,y,z).getType();
                if(expected.getMaterial().isSolid()&&actual!=expected.getMaterial()&&preserved.get(m.get("id")+":"+x+":"+y+":"+z)!=actual)throw new AssertionError("Bloc de monument différent du plan ET de la source : "+m.get("id")+" "+x+" "+y+" "+z);
                if(expected.getMaterial().isAir()&&world.getBlockAt(x,y,z).isLiquid())throw new AssertionError("Accès inondé : "+m.get("id")+" "+x+" "+y+" "+z);
            }
            passed.add((preserved.isEmpty()?"Blocs solides du monument vérifiés : ":"Blocs de monument conformes au plan ou à la source conservée : ")+m.get("id"));
            for(JsonElement element:plan.getAsJsonArray("loot")){
                JsonObject loot=element.getAsJsonObject();
                Block block=world.getBlockAt(number(m,"x")+loot.get("x").getAsInt(),number(m,"y")+loot.get("y").getAsInt(),number(m,"z")+loot.get("z").getAsInt());
                if(!(block.getState()instanceof Chest chest))throw new AssertionError("Coffre de monument absent.");
                Map<Material,Integer> expected=new HashMap<>(),actual=new HashMap<>();
                for(JsonElement item:loot.getAsJsonArray("items"))expected.merge(Material.valueOf(item.getAsJsonObject().get("material").getAsString()),item.getAsJsonObject().get("amount").getAsInt(),Integer::sum);
                for(var item:chest.getBlockInventory().getContents())if(item!=null)actual.merge(item.getType(),item.getAmount(),Integer::sum);
                if(!expected.equals(actual))throw new AssertionError("Butin fixe différent du plan : "+m.get("id"));
                passed.add("Butin fixe exact et accès sans liquide : "+m.get("id"));
            }
        }
        for(JsonElement entry:previousDifferences){var e=entry.getAsJsonObject();
            if(world.getBlockAt(e.get("x").getAsInt(),e.get("y").getAsInt(),e.get("z").getAsInt()).getType()!=Material.matchMaterial(e.get("source").getAsString()))throw new AssertionError("Modification préexistante non préservée : "+entry);
        }
        if(!previousDifferences.isEmpty())passed.add(previousDifferences.size()+" différences préexistantes des monuments conservées");
        for(Map<String,Object>s:supplies){
            int x=number(s,"x"),y=number(s,"y"),z=number(s,"z");assertNeutral(x,z,4);
            if(!(world.getBlockAt(x,y,z).getState()instanceof Chest chest)||!s.get("id").equals(chest.getPersistentDataContainer().get(new NamespacedKey(companion,"supply-id"),PersistentDataType.STRING))||!chest.getBlockInventory().isEmpty())throw new AssertionError("Support de ravitaillement incorrect.");
        }
        passed.add("Huit coffres fixes identifiés, vides et neutres");
        if(!((Map<?,?>)field(companion,"objectives")).isEmpty())throw new AssertionError("Un objectif secret a été créé par erreur.");
        passed.add("Aucune salle ni objectif secret précréé");
        write(repo.resolve("tests/results/"+(instance.getFileName().toString().equals("map-v2-fixes")?"v2-fixes-world.json":"map-v2-world.json")),record("instance","runtime/"+instance.getFileName(),"passed",passed,"distances",distanceReport,"preservedSourceDifferences",previousDifferences.size(),"visualValidation",false,
                "note","Contrôles techniques de blocs réels ; inspection avec client Minecraft restante."));
        getLogger().info("MAP V2 VERIFY SUCCESS checks="+passed.size());
    }
}
