package fr.fkamis;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import org.bukkit.command.CommandSender;

/** Lecture de l'état et du compteur de ravitaillement existants, aucune coordonnée secrète. */
final class MatchInformation {
    private final FKAmis plugin;
    MatchInformation(FKAmis plugin){this.plugin=plugin;}
    void command(CommandSender sender,String[] args){
        String action=args.length>1?args[1]:"match";
        sender.sendMessage(Component.text("FALLEN KINGDOM — INFORMATIONS",NamedTextColor.GOLD));
        switch(action){
            case "match" -> {
                sender.sendMessage(Component.text("Jour "+plugin.state.day+" | "+(!plugin.state.started?"Installation":!plugin.state.winner.isEmpty()?"Terminée":plugin.state.paused?"Pause":"En cours"),NamedTextColor.YELLOW));
                phases(sender);sender.sendMessage(Component.text("Royaumes actifs : "+plugin.expectedTeams().stream().filter(t->!plugin.state.eliminated.contains(t)).count()+"/4",NamedTextColor.WHITE));supplies(sender);
            }
            case "teams" -> plugin.expectedTeams().forEach(name->sender.sendMessage(Component.text(name+" : "+plugin.teamSize(name)+" membre(s), "+(plugin.state.eliminated.contains(name)?"éliminé":"actif"),NamedTextColor.WHITE)));
            case "phases" -> phases(sender);
            case "supplies" -> supplies(sender);
            default -> throw new IllegalArgumentException("info [teams|phases|supplies]");
        }
    }
    private String unlocked(int day){return !plugin.state.running()?"suspendu":plugin.state.day>=day?"ouvert":"fermé";}
    private void phases(CommandSender sender){sender.sendMessage(Component.text("PvP : "+unlocked(plugin.getConfig().getInt("pvp-day"))+" | Assauts : "+unlocked(plugin.assaultDay())+" | Nether : "+unlocked(plugin.getConfig().getInt("nether-day"))+" | End : "+(plugin.state.endOpen?"ouvert":"fermé"),NamedTextColor.WHITE));}
    private void supplies(CommandSender sender){sender.sendMessage(Component.text("Ravitaillements : "+(!plugin.supplies.enabled?"désactivés":Statistics.duration(plugin.supplies.clock.remaining*1000L)+" avant événement, "+plugin.supplies.activeCount()+" lot(s) actif(s)")+(!plugin.state.running()?" (compteur suspendu)":""),NamedTextColor.AQUA));}
}
