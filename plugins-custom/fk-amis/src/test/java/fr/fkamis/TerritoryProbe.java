package fr.fkamis;

import com.google.gson.*;
import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fallenkingdom.display.notification.RegionChange;
import fr.devsylone.fkpi.FkPI;
import fr.devsylone.fkpi.teams.*;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.player.*;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.plugin.java.JavaPlugin;
import java.lang.reflect.*;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Corps serveur synthétiques uniquement, copie locale, aucun client authentifié. */
public final class TerritoryProbe extends JavaPlugin {
    private JavaPlugin plugin;private Object state;private World world;private boolean baseline;
    private final List<Player> actors=new ArrayList<>();private final List<String> checks=new ArrayList<>();
    private final Map<String,Object> observations=new LinkedHashMap<>();
    private Object call(Object o,String name,Class<?>[] types,Object...args)throws Exception{Method m=o.getClass().getDeclaredMethod(name,types);m.setAccessible(true);return m.invoke(o,args);}
    private void set(Object o,String name,Object value)throws Exception{SyntheticPlayer.set(o,name,value);}
    private void check(boolean ok,String label){if(!ok)throw new AssertionError(label);checks.add(label);}
    @Override public void onEnable(){
        if(!Boolean.getBoolean("fk.territory.probe")||!Bukkit.getIp().equals("127.0.0.1"))throw new IllegalStateException("Copie locale isolée requise");
        baseline=Boolean.getBoolean("fk.territory.baseline");
        Bukkit.getScheduler().runTaskLater(this,()->{try{run();}catch(Throwable t){fail(t);}},30);
    }
    private Object connection(Player p)throws Exception{return SyntheticPlayer.field(SyntheticPlayer.field(p.getClass().getMethod("getHandle").invoke(p),"connection"),"connection");}
    @SuppressWarnings("unchecked") private void clear(Player p)throws Exception{((Collection<Object>)SyntheticPlayer.field(connection(p),"pendingActions")).clear();}
    private static String plain(String s){return s.replaceAll("§[0-9a-fk-orxA-FK-ORX]","");}
    private Object packet(Object object,int depth)throws Exception{
        if(object==null||depth>4)return null;
        if(object.getClass().getSimpleName().equals("ClientboundSystemChatPacket"))return object;
        if(!object.getClass().getName().startsWith("net.minecraft.network.Connection"))return null;
        for(Field f:object.getClass().getDeclaredFields()){if(Modifier.isStatic(f.getModifiers()))continue;f.setAccessible(true);Object found=packet(f.get(object),depth+1);if(found!=null)return found;}return null;
    }
    private List<Object> messages(Player p)throws Exception{
        List<Object> out=new ArrayList<>();for(Object pending:(Iterable<?>)SyntheticPlayer.field(connection(p),"pendingActions")){Object found=packet(pending,0);if(found!=null)out.add(found.getClass().getMethod("content").invoke(found));}return out;
    }
    private String text(Object c)throws Exception{return (String)Class.forName("net.minecraft.network.chat.Component").getMethod("getString").invoke(c);}
    private int regions(Player p)throws Exception{int n=0;for(Object c:messages(p)){String s=text(c).toLowerCase(Locale.ROOT);if(s.contains("base")||s.contains("territoire"))n++;}return n;}
    private boolean has(Player p,String expected)throws Exception{for(Object c:messages(p))if(text(c).contains(plain(expected)))return true;return false;}
    @SuppressWarnings("unchecked") private Set<Integer> colors(Object c)throws Exception{
        Set<Integer> result=new HashSet<>();Class<?> component=Class.forName("net.minecraft.network.chat.Component");Object style=component.getMethod("getStyle").invoke(c),color=style.getClass().getMethod("getColor").invoke(style);
        if(color!=null)result.add((int)color.getClass().getMethod("getValue").invoke(color));
        for(Object child:(List<Object>)component.getMethod("getSiblings").invoke(c))result.addAll(colors(child));return result;
    }
    private boolean colored(Player p,int expected)throws Exception{for(Object c:messages(p))if(colors(c).contains(expected))return true;return false;}
    private Player actor(String name,Location at)throws Exception{Player p=SyntheticPlayer.create(name,at);p.setGravity(false);actors.add(p);return p;}
    private void command(String...args){plugin.onCommand(Bukkit.getConsoleSender(),plugin.getCommand("fka"),"fka",args);}
    private Location edge(Base b,int distance){Location p=b.getCenter().clone().add(distance,25,0);p.setY(Math.max(p.getY(),120));return p;}
    private void snap(Player p,Location at)throws Exception{Object body=p.getClass().getMethod("getHandle").invoke(p);body.getClass().getMethod("snapTo",double.class,double.class,double.class).invoke(body,at.getX(),at.getY(),at.getZ());}
    private PlayerMoveEvent move(Player p,Location from,Location to)throws Exception{
        snap(p,from);PlayerMoveEvent e=new PlayerMoveEvent(p,from,to);Bukkit.getPluginManager().callEvent(e);if(!e.isCancelled()&&e.getTo()!=null)snap(p,e.getTo());return e;
    }
    private int entry(Player p,Base base)throws Exception{move(p,p.getLocation(),edge(base,41));clear(p);move(p,edge(base,41),edge(base,40));return regions(p);}
    @SuppressWarnings("unchecked") private void run()throws Exception{
        plugin=(JavaPlugin)Bukkit.getPluginManager().getPlugin("FKAmis");state=SyntheticPlayer.field(plugin,"state");world=Bukkit.getWorld("world");
        var teams=FkPI.getInstance().getTeamManager();List<Team> all=teams.getTeams();Base green=teams.getTeam("Verte").getBase();
        Player admin=actor("TerrAdmin",edge(green,41)),survival=actor("TerrSurvival",edge(green,41)),op=actor("TerrOp",edge(green,41)),spectator=actor("TerrSpectator",edge(green,41));
        command("admin","grant",admin.getUniqueId().toString(),"confirm");op.setOp(true);
        check(admin.getGameMode()==GameMode.CREATIVE,"arbitre Creative réel");
        check(!(boolean)call(plugin,"isAdministrator",new Class<?>[]{Player.class},op),"OP sans rôle arbitre conserve ses restrictions");
        check(!(boolean)SyntheticPlayer.field(state,"started")&&(int)SyntheticPlayer.field(state,"day")==0,"phase initiale jour zéro");
        int adminInitial=entry(admin,green),survivalInitial=entry(survival,green),opInitial=entry(op,green);
        observations.put("day0CreativeAdminMessages",adminInitial);observations.put("day0SurvivalMessages",survivalInitial);observations.put("day0OpMessages",opInitial);
        check(adminInitial==(baseline?0:1),"notification arbitre jour zéro "+(baseline?"absence reproduite":"rétablie"));
        check(survivalInitial==1&&opInitial==1,"Survival et OP : une seule notification native, aucun doublon");
        if(!baseline){
            check(has(admin,new RegionChange(green,RegionChange.MoveType.ENTER).message(admin)),"présentation native et nom de l'équipe conservés");
            check(colored(admin,0x55ff55),"couleur verte présente dans le paquet chat");
        }
        for(Team team:all){Base b=team.getBase();check(b.getRadius()==40&&b.contains(edge(b,40))&&!b.contains(edge(b,41)),"limite native 41/40 "+team.getName());check(entry(admin,b)==(baseline?0:1),"entrée arbitre "+team.getName());if(!baseline)check(colored(admin,Map.of("Rouge",0xff5555,"Bleue",0x5555ff,"Verte",0x55ff55,"Jaune",0xffff55).get(team.getName())),"couleur chat "+team.getName());}
        clear(admin);Location inside=admin.getLocation();for(int i=0;i<25;i++)move(admin,inside,inside.clone().add(0,0,.01));check(regions(admin)==0,"aucun spam à l'intérieur");
        clear(admin);Base last=all.get(all.size()-1).getBase();move(admin,admin.getLocation(),edge(last,41));check(regions(admin)==(baseline?0:1),"sortie vers zone neutre");
        clear(admin);Base red=teams.getTeam("Rouge").getBase();check(admin.teleport(edge(red,39)),"téléportation locale acceptée");check(regions(admin)==(baseline?0:1),"téléportation arbitre dans un territoire");
        ((Map<UUID,String>)SyntheticPlayer.field(plugin,"roster")).put(survival.getUniqueId(),"Verte");teams.addPlayer(survival.getName(),"Verte");
        ((Map<UUID,String>)SyntheticPlayer.field(plugin,"roster")).put(op.getUniqueId(),"Rouge");teams.addPlayer(op.getName(),"Rouge");
        set(state,"started",true);set(state,"day",1);set(state,"paused",false);call(plugin,"syncNative",new Class<?>[]{});
        check(entry(admin,green)==(baseline?0:1),"arbitre pendant partie simulée commencée");check(entry(survival,green)==1&&entry(op,red)==1,"participants après départ, aucun doublon");
        if(!baseline)for(Team team:all){
            Location center=team.getBase().getCenter();var block=world.getHighestBlockAt(center.getBlockX()+39,center.getBlockZ());var original=block.getBlockData();
            var own=new BlockBreakEvent(block,survival);Bukkit.getPluginManager().callEvent(own);check(own.isCancelled()!=team.getName().equals("Verte"),"protection J1 Survival "+team.getName());
            var operator=new BlockBreakEvent(block,op);Bukkit.getPluginManager().callEvent(operator);check(operator.isCancelled()!=team.getName().equals("Rouge"),"OP sans exemption de territoire "+team.getName());
            var arbiter=new BlockBreakEvent(block,admin);Bukkit.getPluginManager().callEvent(arbiter);check(!arbiter.isCancelled(),"exemption arbitre conservée "+team.getName());
            check(original.equals(block.getBlockData()),"événements de test sans destruction de bloc "+team.getName());
        }
        ((Map<UUID,String>)SyntheticPlayer.field(plugin,"roster")).put(spectator.getUniqueId(),"Bleue");((Set<String>)SyntheticPlayer.field(state,"eliminated")).add("Bleue");call(plugin,"applyMode",new Class<?>[]{Player.class},spectator);
        check(spectator.getGameMode()==GameMode.SPECTATOR,"éliminé reste Spectator");check(entry(spectator,red)==1,"éliminé : uniquement message natif préexistant, aucun repli supplémentaire");
        clear(survival);PlayerTeleportEvent denied=new PlayerTeleportEvent(survival,survival.getLocation(),Bukkit.getWorlds().stream().filter(w->w.getEnvironment()==World.Environment.NETHER).findFirst().orElseThrow().getSpawnLocation(),PlayerTeleportEvent.TeleportCause.COMMAND);Bukkit.getPluginManager().callEvent(denied);
        check(denied.isCancelled()&&regions(survival)==0,"changement de dimension refusé sans nouvelle notification ni privilège");
        clear(admin);World nether=denied.getTo().getWorld();check(admin.teleport(new Location(nether,0,120,0)),"arbitre autorisé entre dimensions");check(regions(admin)==(baseline?0:1),"sortie Overworld vers Nether");
        clear(admin);check(admin.teleport(edge(green,39)),"retour Overworld");check(regions(admin)==(baseline?0:1),"entrée après changement de dimension");
        set(state,"paused",true);call(plugin,"syncNative",new Class<?>[]{});check(entry(admin,red)==(baseline?0:1),"arbitre mobile et notifié en pause");
        clear(survival);Location fixed=survival.getLocation();PlayerMoveEvent frozen=move(survival,fixed,fixed.clone().add(3,0,0));check(frozen.getTo().distanceSquared(fixed)<.01&&regions(survival)==0,"pause et ancrage participant conservés");
        check(FkPI.getInstance().getRulesManager().getRule(fr.devsylone.fkpi.rules.Rule.DEEP_PAUSE),"protection native DeepPause inchangée");
        for(Player p:actors){p.setOp(false);command("admin","revoke",p.getUniqueId().toString(),"confirm");Bukkit.getPluginManager().callEvent(new PlayerQuitEvent(p,"sonde locale"));SyntheticPlayer.remove(p);}actors.clear();
        ((Map<?,?>)SyntheticPlayer.field(plugin,"roster")).clear();((Map<?,?>)SyntheticPlayer.field(plugin,"rosterNames")).clear();((Set<?>)SyntheticPlayer.field(state,"eliminated")).clear();set(state,"started",false);set(state,"day",0);set(state,"paused",true);call(plugin,"syncNative",new Class<?>[]{});
        Map<String,Object> report=new LinkedHashMap<>();report.put("passed",true);report.put("baseline",baseline);report.put("checks",checks);report.put("assertions",checks.size());report.put("observations",observations);report.put("authenticatedClients",0);report.put("visualInspection",false);report.put("officialGameStarted",false);
        Files.writeString(Path.of("territory-probe-result.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report));getLogger().info("TERRITORY PROBE SUCCESS");Bukkit.shutdown();
    }
    private void fail(Throwable t){getLogger().log(Level.SEVERE,"TERRITORY PROBE FAILED",t);Bukkit.shutdown();}
}
