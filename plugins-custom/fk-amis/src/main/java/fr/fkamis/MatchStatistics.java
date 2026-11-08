package fr.fkamis;

import com.google.gson.*;
import java.util.*;

/** Modèle persistant unique ; les agrégats d'équipe sont calculés, jamais dupliqués. */
final class MatchStatistics {
    static final Gson JSON=new GsonBuilder().disableHtmlEscaping().create();
    int schema=1;String matchId=UUID.randomUUID().toString();boolean partial;
    long startedAt,finishedAt,activeMillis,pausedMillis;String winner="";
    Map<UUID,Member> players=new LinkedHashMap<>();List<String> eliminationOrder=new ArrayList<>();
    Map<String,Long> eliminatedAt=new HashMap<>();Set<String> capturedObjectives=new HashSet<>(),handledDeaths=new HashSet<>();
    Map<String,Integer> ranks=new HashMap<>();
    transient JsonObject original=new JsonObject();
    static final class Member {
        UUID uuid;String name,team;int kills,deaths,pvpDeaths,captures,life;double dealt,received;long activeMillis;
        Member(UUID uuid,String name,String team){this.uuid=uuid;this.name=name;this.team=team;}
    }
    record TeamTotals(int members,int kills,int deaths,int captures,int lost,long survivalMillis,int rank){}
    static MatchStatistics read(String json) {
        MatchStatistics value=JSON.fromJson(json,MatchStatistics.class);
        if(value==null||value.schema!=1)throw new IllegalArgumentException("Version future ou invalide des statistiques ; conserver state.yml.");
        UUID.fromString(value.matchId);value.original=JsonParser.parseString(json).getAsJsonObject();
        if(value.players==null||value.eliminationOrder==null||value.eliminatedAt==null||value.capturedObjectives==null||value.handledDeaths==null||value.ranks==null||value.teamCaptureEvents==null||value.winner==null)throw new IllegalArgumentException("Collections statistiques absentes ou invalides.");
        if(value.activeMillis<0||value.pausedMillis<0||value.startedAt<0||value.finishedAt<0)throw new IllegalArgumentException("Compteurs statistiques négatifs.");
        for(var entry:value.players.entrySet()) {
            Member member=entry.getValue();
            if(member==null||!entry.getKey().equals(member.uuid)||member.team==null||member.name==null||member.kills<0||member.deaths<0||member.pvpDeaths<0||member.captures<0||member.life<0||member.activeMillis<0
                    ||!Double.isFinite(member.dealt)||!Double.isFinite(member.received)||member.dealt<0||member.received<0)
                throw new IllegalArgumentException("Statistiques joueur invalides.");
        }
        return value;
    }
    String json() {JsonObject merged=original.deepCopy();JsonObject current=JSON.toJsonTree(this).getAsJsonObject();
        if(merged.has("players")&&merged.get("players").isJsonObject())merged.getAsJsonObject("players").keySet().removeIf(key->!current.getAsJsonObject("players").has(key));
        merge(merged,current);return JSON.toJson(merged);}
    private static void merge(JsonObject target,JsonObject source) {
        source.entrySet().forEach(entry->{if(entry.getValue().isJsonObject()&&target.has(entry.getKey())&&target.get(entry.getKey()).isJsonObject())merge(target.getAsJsonObject(entry.getKey()),entry.getValue().getAsJsonObject());else target.add(entry.getKey(),entry.getValue().deepCopy());});
    }
    Member member(UUID id,String name,String team){Member member=players.computeIfAbsent(id,key->new Member(id,name,team));member.name=name;if(startedAt==0)member.team=team;return member;}
    void elapsed(long millis,boolean running,Collection<UUID> present) {
        if(millis<0)throw new IllegalArgumentException("Durée négative.");if(startedAt==0||finishedAt!=0)return;
        if(running){activeMillis+=millis;for(UUID id:present){Member member=players.get(id);if(member!=null)member.activeMillis+=millis;}}
        else pausedMillis+=millis;
    }
    boolean death(UUID victim,UUID killer) {
        Member dead=players.get(victim);if(dead==null||!handledDeaths.add(victim+"/"+dead.life))return false;
        dead.deaths++;Member attacker=killer==null?null:players.get(killer);
        if(attacker!=null&&!attacker.team.equals(dead.team)&&!victim.equals(killer)){attacker.kills++;dead.pvpDeaths++;}return true;
    }
    void respawn(UUID player){Member member=players.get(player);if(member!=null&&handledDeaths.contains(player+"/"+member.life))member.life++;}
    void damage(UUID attacker,UUID victim,double amount) {
        if(!Double.isFinite(amount)||amount<=0)return;Member from=players.get(attacker),to=players.get(victim);
        if(from!=null&&to!=null&&!from.team.equals(to.team)&&!attacker.equals(victim)){from.dealt+=amount;to.received+=amount;}
    }
    void capture(String attacker,String defender,Collection<UUID> participants) {
        if(!capturedObjectives.add(defender))return;
        for(UUID id:new HashSet<>(participants)){Member member=players.get(id);if(member!=null&&member.team.equals(attacker))member.captures++;}
    }
    void eliminated(String team,int rank){if(!eliminationOrder.contains(team)){eliminationOrder.add(team);eliminatedAt.put(team,activeMillis);ranks.put(team,rank);}}
    TeamTotals team(String team) {
        var members=players.values().stream().filter(p->p.team.equals(team)).toList();
        int captures=0;
        // Une capture d'équipe est distincte du nombre de participants crédités.
        for(String key:teamCaptureEvents)if(key.startsWith(team+"/"))captures++;
        int rank=winner.isEmpty()?0:winner.equals(team)?1:ranks.getOrDefault(team,0);
        return new TeamTotals(members.size(),members.stream().mapToInt(p->p.kills).sum(),members.stream().mapToInt(p->p.deaths).sum(),captures,
            eliminatedAt.containsKey(team)?1:0,eliminatedAt.getOrDefault(team,activeMillis),rank);
    }
    Set<String> teamCaptureEvents=new HashSet<>();
    void captureEvent(String attacker,String defender,Collection<UUID> participants){if(capturedObjectives.contains(defender))return;capture(attacker,defender,participants);teamCaptureEvents.add(attacker+"/"+defender);}
    long totalMillis(long now){return startedAt==0?0:Math.max(activeMillis+pausedMillis,(finishedAt==0?now:finishedAt)-startedAt);}
}
