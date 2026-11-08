package fr.fkamis;

import org.bukkit.*;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.player.PlayerRespawnEvent;
import java.nio.file.*;
import java.util.*;

/** Collecte après les protections ; même instantané atomique que les éliminations. */
final class Statistics implements Listener {
    private final FKAmis plugin;MatchStatistics model;
    private long lastNano=System.nanoTime();private boolean lastStarted,lastRunning;private Set<UUID> lastPresent=Set.of();
    private boolean frozen;private int saveTicks;
    Statistics(FKAmis plugin,String saved){
        this.plugin=plugin;model=saved==null?new MatchStatistics():MatchStatistics.read(saved);
        if(saved==null&&plugin.state.started){model.partial=true;model.startedAt=System.currentTimeMillis();}
        ensureRoster();lastStarted=plugin.state.started;lastRunning=plugin.state.running();
        for(String team:plugin.state.eliminated)if(!model.eliminationOrder.contains(team)){model.eliminatedAt.put(team,0L);} // antérieur inconnu, pas de faux ordre.
        if(saved==null&&!plugin.state.winner.isEmpty()){model.winner=plugin.state.winner;model.finishedAt=System.currentTimeMillis();}
    }
    private void ensureRoster(){if(model.finishedAt!=0)return;plugin.roster.forEach((id,team)->{if(!plugin.administrators.contains(id))model.member(id,plugin.rosterName(id),team);});}
    void pulse(){sample(System.nanoTime(),Bukkit.getOnlinePlayers());}
    void sample(long now,Collection<? extends Player> online){
        if(frozen)return;ensureRoster();long millis=Math.max(0,(now-lastNano)/1_000_000L);lastNano=now;
        if(lastStarted)model.elapsed(millis,lastRunning,lastPresent);
        if(plugin.state.started&&model.startedAt==0){model.startedAt=System.currentTimeMillis();model.players.keySet().retainAll(plugin.roster.keySet());}
        lastStarted=plugin.state.started;lastRunning=plugin.state.running();
        Set<UUID> present=new HashSet<>();for(Player p:online)if(plugin.activeParticipant(p)&&!p.isDead()&&p.getGameMode()==GameMode.SURVIVAL)present.add(p.getUniqueId());lastPresent=present;
    }
    void tick(){pulse();if(plugin.state.started&&++saveTicks>=10){saveTicks=0;plugin.saveState();}}
    void freeze(){pulse();frozen=true;}
    void capture(String attacker,String defender,Collection<UUID> participants){pulse();model.captureEvent(attacker,defender,participants);}
    void eliminated(String team){pulse();model.eliminated(team,5-plugin.state.eliminated.size());}
    void finish(String winner){pulse();if(model.finishedAt==0){model.winner=winner;model.finishedAt=System.currentTimeMillis();}}
    void export(String reason)throws Exception {
        Path folder=plugin.getDataFolder().toPath().resolve("history").resolve(model.matchId);Files.createDirectories(folder);
        String json=model.json()+"\n";Path report=folder.resolve(reason+".json");
        if(Files.exists(report)){if(!Files.readString(report).equals(json))throw new IllegalStateException("Historique existant différent : aucune réécriture de "+report.getFileName());}
        else AtomicData.write(report,json);
        StringBuilder csv=new StringBuilder("uuid,pseudo,equipe,kills,morts,morts_pvp,degats_infliges,degats_recus,captures,temps_actif_ms\n");
        model.players.values().stream().sorted(Comparator.comparing(p->p.uuid.toString())).forEach(p->csv.append(p.uuid).append(',').append(csv(p.name)).append(',').append(csv(p.team)).append(',').append(p.kills).append(',').append(p.deaths).append(',').append(p.pvpDeaths).append(',').append(p.dealt).append(',').append(p.received).append(',').append(p.captures).append(',').append(p.activeMillis).append('\n'));
        Path csvFile=folder.resolve(reason+".csv");if(!Files.exists(csvFile))AtomicData.write(csvFile,csv.toString());
        StringBuilder teamCsv=new StringBuilder("equipe,effectif,kills,morts,captures,objectifs_perdus,eliminee,survie_observee_ms,rang\n");
        for(String name:plugin.expectedTeams()){var t=model.team(name);teamCsv.append(csv(name)).append(',').append(t.members()).append(',').append(t.kills()).append(',').append(t.deaths()).append(',').append(t.captures()).append(',').append(t.lost()).append(',').append(plugin.state.eliminated.contains(name)).append(',').append(t.survivalMillis()).append(',').append(t.rank()).append('\n');}
        Path teamFile=folder.resolve(reason+"-teams.csv");if(!Files.exists(teamFile))AtomicData.write(teamFile,teamCsv.toString());
    }
    private String csv(String value){return '"'+value.replace("\"","\"\"")+'"';}
    private UUID enemy(UUID source,Player victim){
        String team=source==null?null:plugin.roster.get(source);if(team==null||plugin.administrators.contains(source)||plugin.state.eliminated.contains(team)||team.equals(plugin.roster.get(victim.getUniqueId())))return null;return source;
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void damage(EntityDamageEvent event){
        if(!plugin.state.running()||!(event.getEntity() instanceof Player victim)||!plugin.activeParticipant(victim)||victim.getGameMode()!=GameMode.SURVIVAL)return;
        UUID attacker=enemy(plugin.damageAttribution.damageOwner(event),victim);if(attacker==null)return;ensureRoster();
        model.damage(attacker,victim.getUniqueId(),Math.max(0,Math.min(victim.getHealth(),event.getFinalDamage())));
    }
    @EventHandler(priority=EventPriority.MONITOR) public void death(PlayerDeathEvent event){
        Player victim=event.getEntity();if(!plugin.state.running()||!plugin.activeParticipant(victim)||victim.getGameMode()!=GameMode.SURVIVAL)return;
        if(event.getDamageSource().getDamageType().getKey().getKey().equals("generic_kill"))return;
        UUID owner=plugin.damageAttribution.owner(event.getDamageSource().getCausingEntity());
        if(owner==null)owner=plugin.damageAttribution.owner(event.getDamageSource().getDirectEntity());
        if(owner==null&&event.getDamageSource().getCausingEntity()==null&&event.getDamageSource().getDirectEntity()==null&&victim.getLastDamageCause()!=null
                &&event.getDamageSource().getDamageType().equals(victim.getLastDamageCause().getDamageSource().getDamageType()))owner=plugin.damageAttribution.damageOwner(victim.getLastDamageCause());
        if(plugin.administrators.contains(owner))return;ensureRoster();
        if(model.death(victim.getUniqueId(),enemy(owner,victim)))plugin.saveState();
    }
    @EventHandler(priority=EventPriority.MONITOR) public void respawn(PlayerRespawnEvent event){if(plugin.activeParticipant(event.getPlayer()))model.respawn(event.getPlayer().getUniqueId());}
    void command(CommandSender sender,String[] args){
        pulse();String action=args.length>1?args[1]:"match";
        if(model.partial)sender.sendMessage("§eCollecte partielle : données antérieures à VNext inconnues.");
        switch(action){
            case "match" -> sender.sendMessage("§6Statistiques : actif "+duration(model.activeMillis)+", pauses en ligne "+duration(model.pausedMillis)+", total observé "+duration(model.totalMillis(System.currentTimeMillis()))+" | victoire : "+(model.winner.isEmpty()?"en cours":model.winner));
            case "player" -> {if(args.length!=3)throw new IllegalArgumentException("stats player <pseudo>");var p=model.players.values().stream().filter(m->m.name.equalsIgnoreCase(args[2])).findFirst().orElseThrow(()->new IllegalArgumentException("Aucune statistique pour ce joueur."));sender.sendMessage(p.name+" ["+p.team+"] : "+p.kills+" kills, "+p.deaths+" morts (PvP "+p.pvpDeaths+"), dégâts PvP "+Math.round(p.dealt)+" / "+Math.round(p.received)+", captures "+p.captures+", actif "+duration(p.activeMillis));}
            case "team" -> {if(args.length!=3||!plugin.expectedTeams().contains(args[2]))throw new IllegalArgumentException("stats team <équipe>");team(sender,args[2]);}
            case "leaderboard" -> model.players.values().stream().sorted(Comparator.<MatchStatistics.Member>comparingInt(p->p.kills).reversed().thenComparing(p->p.name)).forEach(p->sender.sendMessage(p.name+" ["+p.team+"] : "+p.kills+" kills, "+p.captures+" captures"));
            default -> throw new IllegalArgumentException("stats [match|player pseudo|team équipe|leaderboard]");
        }
    }
    private void team(CommandSender sender,String name){var team=model.team(name);sender.sendMessage(name+" : "+plugin.teamSize(name)+" membres, "+team.kills()+" kills, "+team.deaths()+" morts, "+team.captures()+" captures, objectif perdu "+team.lost()+", survie observée "+duration(team.survivalMillis())+", rang "+(team.rank()==0?"en cours/inconnu":team.rank()));}
    String summary(){return "Victoire "+model.winner+" | kills "+model.players.values().stream().mapToInt(p->p.kills).sum()+" | morts "+model.players.values().stream().mapToInt(p->p.deaths).sum()+" | captures "+model.teamCaptureEvents.size()+" | actif "+duration(model.activeMillis)+" | total observé "+duration(model.totalMillis(System.currentTimeMillis()));}
    static String duration(long millis){long seconds=millis/1000;return (seconds/60)+" min "+(seconds%60)+" s";}
}
