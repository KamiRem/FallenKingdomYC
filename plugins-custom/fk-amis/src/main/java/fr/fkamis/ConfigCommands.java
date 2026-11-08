package fr.fkamis;

import org.bukkit.command.CommandSender;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import java.nio.file.*;
import java.util.*;

/** Une seule configuration effective ; l'intervalle reste dans supplies.yml. */
final class ConfigCommands {
    private final FKAmis plugin;
    ConfigCommands(FKAmis plugin){this.plugin=plugin;}
    Map<String,Number> values() {
        Map<String,Number> result=new TreeMap<>();
        GameSettings.DEFAULTS.forEach((key,value)->{
            Object raw=key.equals("supply-interval-seconds")?plugin.supplies.interval:plugin.getConfig().get(key,value);
            if(!(raw instanceof Number number))throw new IllegalArgumentException("Valeur numérique invalide : "+key);
            result.put(key,number);
        });
        return result;
    }
    void validate(Map<String,Number> values) {
        GameSettings.validate(values,plugin.expectedTeams().stream().map(t->(int)plugin.teamSize(t)).toList());
        if(values.get("supply-interval-seconds").intValue()<plugin.supplies.lifetime)
            throw new IllegalArgumentException("L'intervalle ne peut pas être inférieur à la durée des lots (supplies.yml lifetime-seconds).");
    }
    void command(CommandSender sender,String[] args)throws Exception {
        if(!plugin.mayAdmin(sender))throw new IllegalArgumentException("Configuration réservée à l'arbitre UUID et à la console.");
        String action=args.length>1?args[1]:"list";Map<String,Number> values=values();
        switch(action) {
            case "list" -> {values.forEach((key,value)->sender.sendMessage(key+": "+value));sender.sendMessage("damage-debug: "+plugin.getConfig().getBoolean("damage-debug"));}
            case "get" -> {if(args.length!=3)throw new IllegalArgumentException("Usage : config get <paramètre>");if(args[2].equals("damage-debug"))sender.sendMessage("damage-debug: "+plugin.getConfig().getBoolean("damage-debug"));else {if(!values.containsKey(args[2]))throw new IllegalArgumentException("Paramètre inconnu.");sender.sendMessage(args[2]+": "+values.get(args[2]));}}
            case "validate" -> {validate(values);sender.sendMessage("§aConfiguration cohérente avec les effectifs et les ravitaillements.");}
            case "diff" -> values.forEach((key,value)->{if(value.doubleValue()!=GameSettings.DEFAULTS.get(key).doubleValue())sender.sendMessage(key+": "+value+" (défaut "+GameSettings.DEFAULTS.get(key)+")");});
            case "defaults" -> {requireMutable();validate(GameSettings.DEFAULTS);apply(new TreeMap<>(GameSettings.DEFAULTS));audit(sender,"defaults");sender.sendMessage("§aDéfauts validés et enregistrés ; paramètres inconnus conservés.");}
            case "set" -> {
                if(args.length!=4)throw new IllegalArgumentException("Usage : config set <paramètre> <valeur>");
                if(args[2].equals("damage-debug")) {
                    if(!Set.of("true","false").contains(args[3]))throw new IllegalArgumentException("damage-debug : true ou false.");
                    var raw=load("config.yml");raw.set("damage-debug",Boolean.parseBoolean(args[3]));AtomicData.write(path("config.yml"),raw.saveToString());
                    plugin.getConfig().set("damage-debug",Boolean.parseBoolean(args[3]));plugin.diagnostics.describeHandlers();
                } else {requireMutable();values.put(args[2],GameSettings.parse(args[2],args[3]));validate(values);apply(values);}
                audit(sender,args[2]+"="+args[3]);sender.sendMessage("§aConfiguration enregistrée atomiquement.");
            }
            default -> throw new IllegalArgumentException("config list|get|set|validate|defaults|diff");
        }
    }
    private void requireMutable() {if(plugin.state.started)throw new IllegalArgumentException("Règles structurantes verrouillées depuis le départ, y compris en pause ; préparer une nouvelle partie.");if(plugin.supplies.activeCount()>0)throw new IllegalArgumentException("Des lots sont actifs : modification refusée.");}
    private Path path(String name){return plugin.getDataFolder().toPath().resolve(name);}
    private YamlConfiguration load(String name)throws Exception {var yaml=new YamlConfiguration();yaml.load(path(name).toFile());return yaml;}
    private void apply(Map<String,Number> values)throws Exception {
        var raw=load("config.yml");values.forEach((key,value)->{if(!key.equals("supply-interval-seconds"))raw.set(key,value);});
        // Paramètre de ravitaillement : une clé de stockage existante, jamais un second compteur.
        int nextInterval=values.get("supply-interval-seconds").intValue();
        Map<String,String> updates=new LinkedHashMap<>();updates.put("config.yml",raw.saveToString());
        if(nextInterval!=plugin.supplies.interval){var supply=load("supplies.yml");supply.set("interval-seconds",nextInterval);updates.put("supplies.yml",supply.saveToString());}
        try {SettingsTransaction.commit(plugin.getDataFolder().toPath(),updates);}
        catch(Exception error){plugin.getServer().shutdown();throw error;}
        if(nextInterval!=plugin.supplies.interval)plugin.supplies.changeInterval(nextInterval);
        values.forEach((key,value)->{if(!key.equals("supply-interval-seconds"))plugin.getConfig().set(key,value);});
        plugin.refreshRules();plugin.saveState();
    }
    private void audit(CommandSender sender,String detail){plugin.administrators.audit(sender instanceof Player p?p.getUniqueId():new UUID(0,0),"CONFIG "+detail);}
}
