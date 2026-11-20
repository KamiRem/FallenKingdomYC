package fr.fkamis;

import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.plugin.java.JavaPlugin;
import java.lang.reflect.*;
import java.util.*;
import java.util.logging.Level;

/** Commandes réelles et corps NMS sans clients authentifiés, uniquement en copie jetable. */
public final class FourPlayersProbe extends JavaPlugin {
    private JavaPlugin companion;private final List<Player> actors=new ArrayList<>();
    private Object field(Object o,String name)throws Exception{return SyntheticPlayer.field(o,name);}
    private Object call(Object o,String name,Class<?>[] types,Object...args)throws Exception {var m=o.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(o,args);}
    private void command(String...args){companion.onCommand(Bukkit.getConsoleSender(),companion.getCommand("fka"),"fka",args);}
    private void check(boolean ok,String text){if(!ok)throw new AssertionError(text);getLogger().info("FOUR PLAYERS PROBE PASS "+text);}
    @Override public void onEnable(){
        if(!Boolean.getBoolean("fk.fourplayers")||!Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize().getFileName().toString().startsWith("probe-fourplayers"))throw new IllegalStateException("Copie isolée requise");
        Bukkit.getScheduler().runTaskLater(this,()->{try{test();}catch(Throwable e){getLogger().log(Level.SEVERE,"FOUR PLAYERS PROBE FAILED",e);}finally{for(Player p:actors)try{SyntheticPlayer.remove(p);}catch(Exception e){getLogger().log(Level.SEVERE,"Nettoyage des corps NMS",e);}Bukkit.shutdown();}},40);
    }
    @SuppressWarnings("unchecked") private void test()throws Exception {
        companion=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");
        Map<UUID,String> roster=(Map<UUID,String>)field(companion,"roster");
        var teams=List.of("Rouge","Bleue","Verte","Jaune");World world=Bukkit.getWorld("world");
        Location at=new Location(world,160.5,200,160.5);
        check(Bukkit.getOnlinePlayers().isEmpty()&&Bukkit.getMaxPlayers()==20,"20 places, zéro client authentifié");
        for(int i=0;i<16;i++)actors.add(SyntheticPlayer.create("Quatre"+i,at));
        Player admin=SyntheticPlayer.create("ArbitreQuatre",at);actors.add(admin);command("admin","grant",admin.getUniqueId().toString(),"confirm");
        for(int member=0;member<4;member++)for(int team=0;team<4;team++){
            Player p=actors.get(team*4+member);command("assign",p.getName(),teams.get(team));
            check(roster.get(p.getUniqueId()).equals(teams.get(team))&&(long)call(companion,"teamSize",new Class<?>[]{String.class},teams.get(team))==member+1,"affectation officielle "+(member+1)+"/4 "+teams.get(team));
        }
        Player extra=SyntheticPlayer.create("Cinquieme",at);actors.add(extra);
        command("assign",extra.getName(),"Rouge");check(!roster.containsKey(extra.getUniqueId())&&roster.size()==16,"cinquième refusé sans mutation");
        command("assign",admin.getName(),"Rouge");check(!roster.containsKey(admin.getUniqueId())&&admin.getGameMode()==GameMode.CREATIVE,"arbitre exclu des effectifs");
        Player red=actors.get(3);command("unassign",red.getName());check(roster.size()==15,"retrait avant partie");
        command("assign",red.getName(),"Bleue");check(!roster.containsKey(red.getUniqueId()),"transfert vers équipe pleine refusé");
        command("assign",red.getName(),"Rouge");check(roster.size()==16,"réaffectation avant départ");
        command("start");check(!(boolean)field(field(companion,"state"),"started"),"confirmation des terrains toujours obligatoire");
        // Précondition synthétique de recette ; ne constitue aucune inspection humaine.
        ((Set<String>)field(companion,"terrainValidated")).addAll(teams);
        command("start");check((boolean)field(field(companion,"state"),"started"),"lancement réel par commande avec seize participants");
        command("unassign",red.getName());check(roster.size()==16,"effectifs verrouillés après départ");
        for(Player p:actors.subList(0,16))check(p.getGameMode()==GameMode.SURVIVAL,"participant en SURVIVAL");
        var statistics=field(companion,"statistics");call(statistics,"pulse",new Class<?>[]{});Object model=field(statistics,"model");
        check(((Map<?,?>)field(model,"players")).size()==16&&!((Map<?,?>)field(model,"players")).containsKey(admin.getUniqueId()),"statistiques de seize participants sans arbitre");
        for(String team:teams){Object totals=call(model,"team",new Class<?>[]{String.class},team);check((int)call(totals,"members",new Class<?>[]{})==4,"statistiques équipe de quatre "+team);}
        command("config","validate");command("info","teams");command("stats","match");command("save");
        check(roster.size()==16,"sauvegarde sans perte d’effectif");
        getLogger().info("FOUR PLAYERS PROBE SUCCESS");
    }
}
