package fr.fkamis;

import com.google.gson.*;
import org.bukkit.*;
import org.bukkit.plugin.java.JavaPlugin;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.logging.Level;

/** Charge une partie automatique terminée après restauration complète, sans joueur réseau. */
public final class CampaignRestoreProbe extends JavaPlugin {
    private Object field(Object o,String n)throws Exception{return SyntheticPlayer.field(o,n);}
    private Object call(Object o,String n,Class<?>[] t,Object...a)throws Exception{Method m=o.getClass().getDeclaredMethod(n,t);m.setAccessible(true);return m.invoke(o,a);}
    @Override public void onEnable(){
        if(!Boolean.getBoolean("fk.campaign.restore")||!Bukkit.getIp().equals("127.0.0.1"))throw new IllegalStateException("Copie locale isolée requise");
        Bukkit.getScheduler().runTaskLater(this,()->{try{run();}catch(Throwable e){getLogger().log(Level.SEVERE,"CAMPAIGN RESTORE FAILED",e);}finally{Bukkit.shutdown();}},40);
    }
    private void run()throws Exception{
        JavaPlugin fk=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");Object state=field(fk,"state");
        if(!fk.isEnabled()||!Bukkit.getPluginManager().isPluginEnabled("FallenKingdom")||!Bukkit.getOnlinePlayers().isEmpty()||!"Rouge".equals(field(state,"winner"))||!(boolean)field(state,"paused")||(int)field(state,"day")!=3)throw new AssertionError("État final restauré incorrect");
        Map<?,?> roster=(Map<?,?>)field(fk,"roster");if(roster.size()!=16||((Set<?>)field(state,"eliminated")).size()!=3)throw new AssertionError("Effectifs ou éliminations perdus");
        for(String team:List.of("Rouge","Bleue","Verte","Jaune"))if(roster.values().stream().filter(team::equals).count()!=4)throw new AssertionError("Effectif équipe restaurée incorrect");
        Object statistics=field(fk,"statistics"),model=field(statistics,"model");String json=(String)call(model,"json",new Class<?>[]{});
        String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(json.getBytes(StandardCharsets.UTF_8)));
        if(!hash.equals(System.getProperty("fk.campaign.statistics.sha256"))||((Map<?,?>)field(model,"players")).size()!=16)throw new AssertionError("Statistiques finales différentes");
        for(String[] args:new String[][]{{"status"},{"config","validate"},{"stats","match"},{"info","teams"}})fk.onCommand(Bukkit.getConsoleSender(),fk.getCommand("fka"),"fka",args);
        Files.writeString(Path.of("campaign-restore-result.json"),new GsonBuilder().setPrettyPrinting().create().toJson(Map.of("passed",true,"day",3,"winner","Rouge","participants",16,"eliminatedTeams",3,"statisticsSha256",hash,"authenticatedClients",0,"paused",true))+"\n");
        getLogger().info("CAMPAIGN RESTORE SUCCESS");
    }
}
