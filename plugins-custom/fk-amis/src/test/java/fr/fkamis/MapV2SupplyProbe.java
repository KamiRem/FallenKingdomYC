package fr.fkamis;

import com.google.gson.GsonBuilder;
import org.bukkit.*;
import org.bukkit.block.Chest;
import org.bukkit.block.BlockFace;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.event.block.BlockPistonExtendEvent;
import org.bukkit.event.inventory.InventoryMoveItemEvent;
import org.bukkit.inventory.*;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Recette sans clients authentifiés : événements API et états simulés, dans une copie séparée. */
public final class MapV2SupplyProbe extends JavaPlugin {
    private JavaPlugin companion;
    private Object service,state;
    private final List<String> passed=new ArrayList<>();
    private Path repo;
    @Override public void onEnable() {
        try {
            Path instance=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();
            if(!instance.getFileName().toString().startsWith("map-v2-qa")||!Boolean.getBoolean("fk.supplyprobe"))throw new IllegalStateException("Recette isolée uniquement.");
            repo=instance.getParent().getParent(); companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");
            service=field(companion,"supplies");state=field(companion,"state");
            Bukkit.getScheduler().runTaskLater(this,()->{
                try {
                    if(Boolean.getBoolean("fk.supplyprobe.restart"))restart();else initial();
                    Bukkit.getScheduler().runTaskLater(this,()->finish(),200);
                }catch(Throwable ex){fail(ex);}
            },60);
        }catch(Throwable ex){fail(ex);}
    }
    private Object field(Object object,String name)throws Exception{Field f=object.getClass().getDeclaredField(name);f.setAccessible(true);return f.get(object);}
    private void set(Object object,String name,Object value)throws Exception{Field f=object.getClass().getDeclaredField(name);f.setAccessible(true);f.set(object,value);}
    private Object call(Object object,String name,Class<?>[] types,Object...args)throws Exception{Method m=object.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(object,args);}
    private void check(boolean condition,String label){if(!condition)throw new AssertionError(label);passed.add(label);getLogger().info("SUPPLY PROBE PASS "+label);}
    private void command(String...args){companion.onCommand(Bukkit.getConsoleSender(),Objects.requireNonNull(companion.getCommand("fka")),"fka",args);}
    private int active()throws Exception{return (int)call(service,"activeCount",new Class<?>[]{});}
    private int remaining()throws Exception{return (int)field(field(service,"clock"),"remaining");}
    private void tick(boolean participants)throws Exception{call(service,"tick",new Class<?>[]{boolean.class},participants);}
    @SuppressWarnings("unchecked") private List<String> previous()throws Exception{return new ArrayList<>((List<String>)field(service,"previous"));}
    private void mode(boolean started,boolean paused,String winner)throws Exception{
        set(state,"started",started);set(state,"paused",paused);set(state,"winner",winner);set(state,"day",started?2:0);
        call(companion,"syncNative",new Class<?>[]{});
    }
    @SuppressWarnings("unchecked") private void initial()throws Exception{
        check((boolean)field(service,"enabled"),"ravitaillement activé dans le profil v2");
        check((int)field(service,"interval")==1800&&(int)field(service,"maxActive")==2,"intervalle 1800 secondes et plafond de deux coffres");
        Map<String,Object> sites=(Map<String,Object>)field(service,"sites");
        check(sites.size()==8,"huit emplacements persistants");
        check(remaining()==1800,"compteur initial complet");
        tick(true);check(remaining()==1800&&active()==0,"aucun événement avant lancement");
        mode(true,true,"");tick(true);check(remaining()==1800,"pause ne consomme pas de temps");
        mode(true,false,"Rouge");tick(true);check(remaining()==1800,"victoire ne consomme pas de temps");
        mode(true,false,"");tick(false);check(remaining()==1800,"aucun temps sans participant connecté");
        for(Object site:sites.values()){
            check((boolean)call(service,"eligible",new Class<?>[]{site.getClass()},site),"support éligible "+call(site,"id",new Class<?>[]{}));
        }
        set(field(service,"clock"),"remaining",1);tick(true);
        check(active()==2,"deux lots émis au terme du compteur");
        check(remaining()==1800,"minuteur réarmé atomiquement avant émission");
        var save=new YamlConfiguration();save.load(companion.getDataFolder().toPath().resolve("state.yml").toFile());
        check(save.getInt("supplies.remaining")==1800&&save.getLong("supplies.event")==1,"événement et temps durablement écrits");
        List<String> first=previous();call(service,"trigger",new Class<?>[]{boolean.class},false);
        check(active()==2&&(long)field(service,"event")==1,"aucune accumulation au-delà de deux lots");
        Map<String,Object> drops=(Map<String,Object>)field(service,"drops");
        for(Object drop:drops.values()) for(ItemStack item:(List<ItemStack>)field(drop,"items")) {
            check(!item.getType().name().contains("NETHERITE")&&item.getType()!=Material.ANCIENT_DEBRIS
                    &&!Set.of(Material.ELYTRA,Material.TOTEM_OF_UNDYING,Material.ENCHANTED_GOLDEN_APPLE).contains(item.getType()),"butin réel autorisé "+item.getType());
        }
        command("supply","disable");command("supply","enable");
        set(field(service,"clock"),"remaining",1);tick(true);
        List<String> second=previous();
        check(Collections.disjoint(first,second),"emplacements différents quand assez de sites sont libres");
        check(active()==2,"deuxième événement également borné");
        String claimed=second.getFirst();
        check((boolean)call(service,"reserveClaim",new Class<?>[]{String.class},claimed),"première réservation d'un lot autorisée");
        check(!(boolean)call(service,"reserveClaim",new Class<?>[]{String.class},claimed),"deuxième réservation du même lot refusée");
        for(Object site:sites.values()){
            Location location=(Location)call(site,"location",new Class<?>[]{});
            check(((Chest)location.getBlock().getState()).getBlockInventory().isEmpty(),"coffre physique vide après émission/réservation");
        }
        Object selectedSite=sites.get(second.getLast());Location at=(Location)call(selectedSite,"location",new Class<?>[]{});
        Chest chest=(Chest)at.getBlock().getState();
        InventoryMoveItemEvent transfer=new InventoryMoveItemEvent(chest.getBlockInventory(),new ItemStack(Material.IRON_INGOT),Bukkit.createInventory(null,9),true);
        Bukkit.getPluginManager().callEvent(transfer);check(transfer.isCancelled(),"transfert par entonnoir bloqué");
        BlockPistonExtendEvent piston=new BlockPistonExtendEvent(at.clone().add(-1,0,0).getBlock(),List.of(at.getBlock()),BlockFace.EAST);
        Bukkit.getPluginManager().callEvent(piston);check(piston.isCancelled(),"déplacement par piston bloqué");
        int now=remaining();mode(true,true,"");tick(true);check(remaining()==now,"pause pendant un événement conserve le temps");
        mode(false,true,"");
        call(companion,"saveState",new Class<?>[]{});
        save.load(companion.getDataFolder().toPath().resolve("state.yml").toFile());
        check(save.getString("supplies.drops."+claimed+".status").equals("CLAIMED"),"réservation écrite avant remise d'objets");
        check(save.getStringList("supplies.history").stream().anyMatch(v->v.contains(":CLAIM:")),"historique des récupérations conservé");
        var snapshot=new LinkedHashMap<String,Object>();snapshot.put("claimed",claimed);snapshot.put("remaining",remaining());snapshot.put("event",field(service,"event"));snapshot.put("active",active());
        Files.writeString(getDataFolder().toPath().resolve("expected.json"),new GsonBuilder().create().toJson(snapshot),StandardCharsets.UTF_8);
    }
    private void restart()throws Exception{
        var expected=com.google.gson.JsonParser.parseString(Files.readString(getDataFolder().toPath().resolve("expected.json"))).getAsJsonObject();
        check(remaining()==expected.get("remaining").getAsInt(),"temps restant conservé au redémarrage sans rattrapage");
        check((long)field(service,"event")==expected.get("event").getAsLong(),"numéro d'événement conservé");
        check(active()==expected.get("active").getAsInt(),"lots actifs conservés au redémarrage");
        check(!(boolean)call(service,"reserveClaim",new Class<?>[]{String.class},expected.get("claimed").getAsString()),"lot déjà réservé toujours inaccessible après redémarrage");
        int before=remaining();tick(false);check(remaining()==before,"reprise sans joueurs ne déclenche aucun rattrapage");
        command("supply","test","confirm");check((long)field(service,"event")==expected.get("event").getAsLong(),"commande de test désactivée dans le profil officiel");
    }
    private void finish(){
        try{
            Files.createDirectories(repo.resolve("tests/results"));
            String phase=Boolean.getBoolean("fk.supplyprobe.restart")?"restart":"initial";
            Map<String,Object> data=new LinkedHashMap<>();data.put("passed",passed);data.put("players",Bukkit.getOnlinePlayers().size());
            data.put("measurementTicks",200);data.put("tps1m",Bukkit.getTPS()[0]);data.put("averageTickMs",Bukkit.getAverageTickTime());
            data.put("note","États et événements API simulés, aucun client authentifié ; mesure serveur sans huit joueurs.");
            String prefix=System.getProperty("fk.supplyprobe.reportprefix","map-v2-supply");
            if(!Set.of("map-v2-supply","v2-fixes-supply").contains(prefix))throw new IllegalArgumentException("Préfixe de recette inconnu.");
            Files.writeString(repo.resolve("tests/results/"+prefix+"-"+phase+".json"),new GsonBuilder().setPrettyPrinting().create().toJson(data),StandardCharsets.UTF_8);
            getLogger().info("SUPPLY PROBE SUCCESS "+passed.size()); Bukkit.shutdown();
        }catch(Throwable ex){fail(ex);}
    }
    private void fail(Throwable ex){getLogger().log(Level.SEVERE,"SUPPLY PROBE FAILED",ex);Bukkit.shutdown();}
}
