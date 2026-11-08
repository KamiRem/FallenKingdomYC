package fr.fkamis;

import com.google.gson.GsonBuilder;
import org.bukkit.*;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/** Une commande ne remplace aucun état en cours d'utilisation ; application hors ligne obligatoire. */
final class ResetService {
    private final FKAmis plugin;private ResetPlan plan;boolean stopping;
    ResetService(FKAmis plugin){this.plugin=plugin;}
    private Path path(String name){return plugin.getDataFolder().toPath().resolve(name);}
    private void allowed(){if(plugin.state.running())throw new IllegalArgumentException("Mettre la partie en pause ou terminer la partie avant toute préparation.");}
    private String fingerprint(){
        var yaml=plugin.snapshot();yaml.set("vnext.statistics-json",null);yaml.set("vnext.respawn-protection",null);
        return AtomicData.sha(yaml.saveToString()+plugin.getConfig().saveToString());
    }
    void command(CommandSender sender,String[] args)throws Exception {
        if(!plugin.mayAdmin(sender))throw new IllegalArgumentException("Réinitialisation réservée à l'arbitre UUID et à la console.");
        String action=args.length>1?args[1]:"status";
        switch(action) {
            case "status" -> sender.sendMessage("§eReset : "+(plugin.state.running()?"refusé : partie active":"préparation possible")+", "+Bukkit.getOnlinePlayers().size()+" joueur(s) connecté(s), "+(plan==null?"aucun jeton":"jeton jusqu'au "+Instant.ofEpochMilli(plan.expiresAt()))+". Application uniquement à froid ; aucune construction ni inventaire restauré par le reset logique.");
            case "prepare" -> {
                allowed();if(Files.exists(path("reset-request.json")))throw new IllegalArgumentException("Une demande à froid existe déjà : l'exécuter ou l'annuler.");
                plan=ResetPlan.create(fingerprint(),System.currentTimeMillis());
                sender.sendMessage("§ePréparation : arrêt propre puis sauvegarde complète à froid obligatoire. Reset logique : jour/roster/objectifs/statistiques remis à zéro ; carte, inventaires, butins consommés et historique conservés. La restauration complète exige une archive initiale approuvée et une destination neuve.");
                sender.sendMessage("§eDéconnecter tous les joueurs, y compris l'arbitre, puis console : fka reset confirm "+plan.token()+" (5 minutes).");
            }
            case "cancel" -> {plan=null;for(String file:List.of("reset-request.json","reset-candidate.yml"))Files.deleteIfExists(path(file));sender.sendMessage("§aPréparation annulée ; aucun monde ni état de partie modifié.");}
            case "confirm" -> {
                allowed();if(args.length!=3||plan==null)throw new IllegalArgumentException("reset prepare puis reset confirm <jeton>.");
                if(!Bukkit.getOnlinePlayers().isEmpty())throw new IllegalArgumentException("Aucun joueur connecté pendant la confirmation, arbitre compris ; utiliser la console après déconnexion.");
                plan.verify(args[2],fingerprint(),System.currentTimeMillis());stopping=true;plugin.statistics.freeze();
                if(!plugin.saveState())throw new IllegalStateException("État non sauvegardé ; demande refusée.");
                var current=plugin.snapshot();var candidate=logicalCandidate(current,plugin.expectedTeams(),plugin.supplies.interval,plugin.playersPerTeam());
                AtomicData.write(path("reset-candidate.yml"),candidate.saveToString());
                plugin.statistics.export("reset-"+AtomicData.sha(plan.token()).substring(0,12));
                Path root=Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();
                Map<String,Object> request=new LinkedHashMap<>();request.put("schema",1);request.put("tokenSha256",AtomicData.sha(plan.token()));
                request.put("approvedAt",System.currentTimeMillis());request.put("expiresAt",System.currentTimeMillis()+900_000);
                request.put("sourceStateSha256",AtomicData.sha(Files.readString(path("state.yml"))));request.put("candidateSha256",AtomicData.sha(candidate.saveToString()));
                request.put("paperSha256",AtomicData.shaBytes(Files.readAllBytes(root.resolve("paper.jar"))));
                request.put("pluginSha256",AtomicData.shaBytes(Files.readAllBytes(root.resolve("plugins/FKAmis-1.0.0.jar"))));
                request.put("matchId",plugin.statistics.model.matchId);request.put("candidateFile","plugins/FKAmis/reset-candidate.yml");
                AtomicData.write(path("reset-request.json"),new GsonBuilder().setPrettyPrinting().create().toJson(request)+"\n");
                plugin.administrators.audit(sender instanceof Player p?p.getUniqueId():new UUID(0,0),"RESET confirmé ; demande à froid créée, arrêt technique sans mutation de partie");
                sender.sendMessage("§eDemande créée, arrêt propre. Désactiver le redémarrage automatique du panel puis : python maintenance/host_ops.py reset-logical --token <jeton>. Autorisation à froid valable 15 minutes.");
                Bukkit.getScheduler().runTask(plugin,()->Bukkit.shutdown());plan=null;
            }
            default -> throw new IllegalArgumentException("reset status|prepare|confirm <jeton>|cancel");
        }
    }
    static YamlConfiguration logicalCandidate(YamlConfiguration source,List<String> teams,int interval,int capacity) {
        var result=AtomicData.copy(source);
        result.set("day",0);result.set("started",false);result.set("end-open",false);result.set("winner","");
        result.set("eliminated",List.of());result.set("validated",List.of());result.set("terrain-validated",List.of());
        result.set("roster",null);result.set("objectives",null);result.set("players-per-team",capacity);
        for(String team:teams)result.set("native.TeamManager."+team+".Members",List.of());
        result.set("supplies.remaining",interval);result.set("supplies.previous",List.of());
        var drops=result.getConfigurationSection("supplies.drops");
        if(drops!=null)for(String id:drops.getKeys(false))if("ACTIVE".equals(drops.getString(id+".status"))){drops.set(id+".status","EXPIRED");drops.set(id+".ttl",0);drops.set(id+".items",List.of());}
        result.set("vnext.version",1);result.set("vnext.statistics-json",new MatchStatistics().json());result.set("vnext.respawn-protection",null);
        return result;
    }
}
