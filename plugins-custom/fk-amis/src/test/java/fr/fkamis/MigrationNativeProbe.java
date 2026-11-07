package fr.fkamis;

import com.google.gson.GsonBuilder;
import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fallenkingdom.commands.abstraction.CommandResult;
import fr.devsylone.fallenkingdom.utils.RulesFormatter;
import fr.devsylone.fkpi.FkPI;
import fr.devsylone.fkpi.rules.Rule;
import org.bukkit.*;
import org.bukkit.command.*;
import org.bukkit.entity.Player;
import org.bukkit.event.player.AsyncPlayerChatEvent;
import org.bukkit.event.server.ServerCommandEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.Proxy;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

/** Intégration native sur fixture uniquement ; aucun client et aucune livraison réseau de chat. */
public final class MigrationNativeProbe extends JavaPlugin {
    private final List<String> passed = new ArrayList<>();
    private final List<String> messages = new ArrayList<>();
    private Path repo;
    private Object field(Object value, String name) throws Exception {
        var field = value.getClass().getDeclaredField(name); field.setAccessible(true); return field.get(value);
    }
    private void check(boolean value, String label) {
        if (!value) throw new AssertionError(label);
        passed.add(label); getLogger().info("NATIVE PROBE PASS " + label);
    }
    @Override public void onEnable() {
        Path instance = Bukkit.getWorldContainer().toPath().toAbsolutePath().normalize();
        if (!instance.getFileName().toString().startsWith("probe-native-26-3") || !Boolean.getBoolean("fk.nativeprobe")) {
            getServer().shutdown(); return;
        }
        repo = instance.getParent().getParent();
        Bukkit.getScheduler().runTaskLater(this, () -> {
            try { run(); }
            catch (Throwable error) { getLogger().log(Level.SEVERE,"NATIVE PROBE FAILED", error); }
            finally { Bukkit.shutdown(); }
        }, 60);
    }
    private CommandSender sender(boolean admin) {
        return (CommandSender) Proxy.newProxyInstance(getClassLoader(), new Class<?>[]{admin?ConsoleCommandSender.class:CommandSender.class}, (proxy, method, args) -> {
            return switch (method.getName()) {
                case "getName" -> "MigrationConsole";
                case "getServer" -> Bukkit.getServer();
                case "hasPermission", "isPermissionSet", "isOp" -> admin;
                case "sendMessage" -> { for (Object item : args) {
                    if (item instanceof String[] array) messages.addAll(Arrays.asList(array));
                    else messages.add(String.valueOf(item));
                } yield null; }
                case "hashCode" -> 1;
                case "equals" -> proxy == args[0];
                default -> method.getReturnType() == boolean.class ? false : null;
            };
        });
    }
    private Player actor(String name, World world) {
        UUID id = UUID.nameUUIDFromBytes(name.getBytes(StandardCharsets.UTF_8));
        return (Player) Proxy.newProxyInstance(getClassLoader(), new Class<?>[]{Player.class}, (proxy, method, args) -> switch (method.getName()) {
            case "getName" -> name;
            case "getUniqueId" -> id;
            case "getWorld" -> world;
            case "getLocation" -> new Location(world, 0, 80, 0);
            case "isOnline" -> false;
            case "hashCode" -> id.hashCode();
            case "equals" -> proxy == args[0];
            case "toString" -> name;
            default -> method.getReturnType() == boolean.class ? false : null;
        });
    }
    private void run() throws Exception {
        Map<String,String> defaults = new TreeMap<>();
        for (Material material : Material.values()) {
            if (material.isBlock() && !material.name().startsWith("LEGACY_"))
                defaults.put(material.getKey().toString(), material.createBlockData().getAsString());
        }
        Files.createDirectories(repo.resolve("tests/results"));
        Files.writeString(repo.resolve("tests/results/block-defaults-26.3.json"),new GsonBuilder().create().toJson(defaults),StandardCharsets.UTF_8);
        Fk fk = Fk.getInstance();
        FKAmis companion = (FKAmis) Bukkit.getPluginManager().getPlugin("FKAmis");
        check(fk.isEnabled() && companion != null && companion.isEnabled(), "deux plugins actifs");
        check(Bukkit.getOnlinePlayers().isEmpty(), "zéro client authentifié");
        Object state = field(companion, "state");
        check((int)field(state,"day") == 0 && !(boolean)field(state,"started"), "jour zéro avant recette");
        check(((Map<?,?>)field(companion,"roster")).isEmpty() && ((Map<?,?>)field(companion,"objectives")).isEmpty(), "aucun roster ni objectif initial");
        var teams = FkPI.getInstance().getTeamManager();
        check(new HashSet<>(teams.getTeamNames()).equals(Set.of("Rouge", "Bleue", "Verte", "Jaune")), "quatre équipes natives exactes");
        Map<String,int[]> centers = Map.of("Rouge",new int[]{-240,113,-240}, "Bleue",new int[]{200,66,-200},
                "Verte",new int[]{-200,65,240}, "Jaune",new int[]{280,70,200});
        for (var entry : centers.entrySet()) {
            var team = teams.getTeam(entry.getKey()); var base = team.getBase(); var at = base.getCenter(); int[] c = entry.getValue();
            check(base.getRadius() == 80 && at.getBlockX() == c[0] && at.getBlockY() == c[1] && at.getBlockZ() == c[2]
                    && at.getWorld().getName().equals("world") && team.getPlayers().isEmpty(), "territoire initial " + entry.getKey());
        }
        Set<World.Environment> dimensions = new HashSet<>();
        Bukkit.getWorlds().forEach(w -> dimensions.add(w.getEnvironment()));
        check(dimensions.containsAll(Set.of(World.Environment.NORMAL, World.Environment.NETHER, World.Environment.THE_END)), "trois dimensions chargées");
        check(Bukkit.getWorld("world").getWorldBorder().getSize() == 1200, "bordure 1200 blocs");
        check(FkPI.getInstance().getRulesManager().getRule(Rule.PVP_CAP) == 2
                && FkPI.getInstance().getRulesManager().getRule(Rule.TNT_CAP) == 3, "synchronisation jours natifs 2 et 3");
        check(fk.getDisplayService() != null && fk.getScoreboardManager() != null, "services affichage natifs disponibles");
        check(!RulesFormatter.formatRules().isEmpty(), "formatage interface des règles natif");
        CommandSender admin = sender(true);
        for (String command : List.of("help", "team list", "rules list")) {
            messages.clear();
            var result = fk.getCommandManager().executeCommand(fk, admin, "fk", new ArrayList<>(List.of(command.split(" "))));
            check(result == CommandResult.SUCCESS && !messages.isEmpty(), "commande native " + command);
        }
        var completions = fk.getCommandManager().tabCompleteCommand(fk, admin, new ArrayList<>(List.of("")));
        check(completions.contains("team") && completions.contains("rules"), "complétion native enregistrée");
        for (String command : List.of("help", "status", "supply status", "teams tpall")) {
            messages.clear();
            companion.onCommand(admin, companion.getCommand("fka"), "fka", command.split(" "));
            check(!messages.isEmpty(), "commande complément " + command);
        }
        messages.clear(); companion.onCommand(sender(false), companion.getCommand("fka"), "fka", new String[]{"start"});
        check(messages.stream().anyMatch(m -> m.contains("Permission fkamis.admin")), "permission administrateur exigée");
        ServerCommandEvent bypass = new ServerCommandEvent(admin, "fk game start");
        Bukkit.getPluginManager().callEvent(bypass);
        check(bypass.isCancelled() && !(boolean)field(state,"started"), "lancement natif bloqué par FKAmis");
        World world = Objects.requireNonNull(Bukkit.getWorld("world"));
        Player red = actor("MigrationChatRed",world), blue = actor("MigrationChatBlue",world);
        teams.addPlayer(red.getName(),"Rouge"); teams.addPlayer(blue.getName(),"Bleue");
        check(teams.getPlayerTeam(red).getName().equals("Rouge"), "résolution équipe auteur chat");
        AsyncPlayerChatEvent privateChat = new AsyncPlayerChatEvent(false,red,"secret-fixture",new HashSet<>(Set.of(red,blue)));
        Bukkit.getPluginManager().callEvent(privateChat);
        check(!privateChat.getRecipients().contains(blue) && privateChat.getFormat().contains("%s"), "chat équipe écarte adversaire au niveau événement");
        AsyncPlayerChatEvent global = new AsyncPlayerChatEvent(false,red,"!public-fixture",new HashSet<>(Set.of(red,blue)));
        Bukkit.getPluginManager().callEvent(global);
        check(global.getMessage().equals("public-fixture") && global.getRecipients().contains(blue), "préfixe global natif conserve destinataires");
        check(!(boolean)field(state,"started") && (int)field(state,"day") == 0 && ((Map<?,?>)field(companion,"roster")).isEmpty(), "aucune partie ni attribution FKAmis lancée");
        Map<String,Object> report = new LinkedHashMap<>(); report.put("passed",passed); report.put("authenticatedPlayers",0);
        report.put("simulatedChatActors",2); report.put("networkChatDeliveryTested",false);
        report.put("clientInterfaceRenderingTested",false);
        Files.createDirectories(repo.resolve("tests/results"));
        Files.writeString(repo.resolve("tests/results/native-26.3-integration.json"),new GsonBuilder().setPrettyPrinting().create().toJson(report)+"\n",StandardCharsets.UTF_8);
        getLogger().info("NATIVE PROBE SUCCESS " + passed.size());
    }
}
