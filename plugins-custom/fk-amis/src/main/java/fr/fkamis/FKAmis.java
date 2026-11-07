package fr.fkamis;

import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fallenkingdom.game.Game;
import fr.devsylone.fkpi.FkPI;
import fr.devsylone.fkpi.managers.TeamManager;
import fr.devsylone.fkpi.rules.Rule;
import fr.devsylone.fkpi.teams.*;
import fr.devsylone.fkpi.util.Color;
import org.bukkit.*;
import org.bukkit.block.Block;
import org.bukkit.command.*;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.player.*;
import org.bukkit.event.server.ServerCommandEvent;
import org.bukkit.plugin.java.JavaPlugin;

import java.io.*;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.logging.Level;

public final class FKAmis extends JavaPlugin implements Listener, CommandExecutor, TabCompleter {
    final MatchState state = new MatchState();
    final Map<String, Location> objectives = new HashMap<>();
    final Set<String> validated = new HashSet<>();
    final Set<String> terrainValidated = new HashSet<>();
    final Map<String, Location> spawns = new HashMap<>();
    final Map<String, CaptureClock> captures = new HashMap<>();
    final Map<UUID, String> roster = new HashMap<>();
    private final Map<UUID, String> rosterNames = new HashMap<>();
    private boolean internalCommand;
    private boolean ready;
    private boolean pregenerating;
    boolean returningToSafety;
    private ItemBan itemBan;
    SupplyService supplies;
    DamageAttribution damageAttribution;
    TeamTeleportService teamTeleports;
    ChunkLeases chunkLeases;
    private ConfigurationSection savedSupplies;

    TeamManager teams() { return FkPI.getInstance().getTeamManager(); }
    List<String> expectedTeams() { return getConfig().getStringList("teams"); }
    int assaultDay() { return getConfig().getInt("assault-day"); }
    boolean frozen() { return !state.running(); }
    boolean eliminated(Player player) {
        String team = roster.get(player.getUniqueId());
        return team == null || state.eliminated.contains(team);
    }
    boolean blocked(Player player) {
        if (!state.started && player.hasPermission("fkamis.admin") && player.getGameMode() == GameMode.CREATIVE) return false;
        return frozen() || eliminated(player) || player.getGameMode() != GameMode.SURVIVAL;
    }
    Team team(Player p) { return teams().getTeam(roster.get(p.getUniqueId())); }
    Team territory(Location at) { return teams().getBase(at).map(Base::getTeam).orElse(null); }
    boolean protectedAt(Player player, Location at) {
        Team owner = territory(at);
        return blocked(player) || (owner != null && !owner.equals(team(player)) && !state.assaults(assaultDay()));
    }
    boolean objectiveAt(Location at) {
        return objectives.values().stream().anyMatch(l -> sameBlock(l, at));
    }
    static boolean sameBlock(Location a, Location b) {
        return a.getWorld().equals(b.getWorld()) && a.getBlockX() == b.getBlockX()
                && a.getBlockY() == b.getBlockY() && a.getBlockZ() == b.getBlockZ();
    }

    @Override public void onEnable() {
        try {
            saveDefaultConfig();
            if (!"2.24.9".equals(Fk.getInstance().getDescription().getVersion()))
                throw new IllegalStateException("FallenKingdom 2.24.9 requis : contrôler toute mise à jour.");
            if (new HashSet<>(expectedTeams()).size() != 4 || expectedTeams().size() != 4)
                throw new IllegalStateException("Quatre noms d'équipes distincts requis.");
            if (getConfig().getInt("pvp-day") < 1 || assaultDay() < getConfig().getInt("pvp-day")
                    || getConfig().getInt("nether-day") < 1 || getConfig().getInt("capture-seconds") < 1 || getConfig().getInt("capture-seconds") > 3600
                    || getConfig().getInt("capture-players") < 1 || getConfig().getInt("capture-players") > 2
                    || !Double.isFinite(getConfig().getDouble("capture-radius")) || getConfig().getDouble("capture-radius") <= 0
                    || getConfig().getDouble("capture-radius") > 8 || getConfig().getInt("border-size") < 600 || getConfig().getInt("border-size") > 4000)
                throw new IllegalStateException("Configuration des phases/captures invalide.");
            loadState();
            for (int i = 0; i < expectedTeams().size(); i++) {
                String name = expectedTeams().get(i);
                Team t = teams().getTeam(name);
                if (t == null) t = teams().createTeam(name);
                t.setColor(Color.of(List.of("#ff5555", "#5555ff", "#55ff55", "#ffff55").get(i)));
            }
            configureNative();
            state.paused = true; // Reprise toujours explicite, même après arrêt brutal.
            syncNative();
            Objects.requireNonNull(getCommand("fka")).setExecutor(this);
            Objects.requireNonNull(getCommand("fka")).setTabCompleter(this);
            getServer().getPluginManager().registerEvents(this, this);
            chunkLeases = new ChunkLeases(this);
            damageAttribution = new DamageAttribution(this);
            teamTeleports = new TeamTeleportService(this);
            getServer().getPluginManager().registerEvents(new Protections(this), this);
            getServer().getPluginManager().registerEvents(damageAttribution, this);
            itemBan = new ItemBan(this);
            getServer().getPluginManager().registerEvents(itemBan, this);
            supplies = new SupplyService(this, savedSupplies);
            getServer().getPluginManager().registerEvents(supplies, this);
            World world = Objects.requireNonNull(Bukkit.getWorld("world"), "Monde world absent");
            world.getWorldBorder().setCenter(0, 0);
            world.getWorldBorder().setSize(getConfig().getInt("border-size"));
            for (World w : Bukkit.getWorlds()) {
                if (w.getEnvironment() == World.Environment.NETHER) {
                    w.getWorldBorder().setCenter(0, 0);
                    w.getWorldBorder().setSize(getConfig().getInt("border-size") / 8.0);
                }
            }
            ready = true;
            saveState();
            for (Player p : Bukkit.getOnlinePlayers()) reconcilePlayer(p);
            Bukkit.getScheduler().runTaskTimer(this, this::tick, 20, 20);
            Bukkit.getScheduler().runTaskTimer(this, this::captureTick, 1, 1);
            getLogger().info("FKAmis prêt : quatre royaumes, phases manuelles, reprise en pause.");
        } catch (Exception ex) {
            getLogger().log(Level.SEVERE, "Démarrage refusé ; conserver les fichiers et restaurer une sauvegarde.", ex);
            getServer().shutdown();
        }
    }

    private void configureNative() {
        var rules = FkPI.getInstance().getRulesManager();
        rules.setRule(Rule.PVP_CAP, getConfig().getInt("pvp-day"));
        rules.setRule(Rule.TNT_CAP, assaultDay());
        rules.setRule(Rule.NETHER_CAP, getConfig().getInt("nether-day"));
        rules.setRule(Rule.END_CAP, state.endOpen ? 1 : Integer.MAX_VALUE);
        rules.setRule(Rule.FRIENDLY_FIRE, false);
        rules.setRule(Rule.DEEP_PAUSE, true);
        rules.setRule(Rule.RESPAWN_AT_HOME, true);
        rules.setRule(Rule.CHEST_LIMIT, 0);
        rules.setRule(Rule.VERTICAL_LIMIT, 0);
        rules.setRule(Rule.BLAST_PROOF_BASE, true);
        rules.getRule(Rule.CHARGED_CREEPERS).setValue(0, 0, 0);
        // Garde la construction FK classique : base personnelle + liste limitée hors base.
        // Objectif explicite et capture contrôlée remplacent la détection globale de tous les coffres.
        FkPI.getInstance().getChestsRoomsManager().setEnabled(false);
    }

    private void nativeCommand(String command) {
        internalCommand = true;
        try { Bukkit.dispatchCommand(Bukkit.getConsoleSender(), command); }
        finally { internalCommand = false; }
    }

    private void syncNative() {
        Game game = Fk.getInstance().getGame();
        Map<World, Long> times = new HashMap<>();
        for (World world : Bukkit.getWorlds()) {
            if (world.getEnvironment() == World.Environment.NORMAL) times.put(world, world.getFullTime());
        }
        game.stopTimer();
        if (game.getState() == Game.GameState.STARTED) nativeCommand("fk game pause");
        YamlConfiguration data = new YamlConfiguration();
        data.set("Day", state.day);
        data.set("Time", 0);
        data.set("State", state.started ? "PAUSE" : "BEFORE_STARTING");
        game.load(data);
        if (state.running()) {
            nativeCommand("fk game resume");
            game.stopTimer(); // Le tick natif n'a jamais l'occasion d'avancer les jours.
        }
        for (var e : times.entrySet()) {
            e.getKey().setFullTime(e.getValue());
            e.getKey().setGameRule(GameRules.ADVANCE_TIME, state.running() || !state.started);
        }
        getServer().getServerTickManager().setFrozen(state.started && frozen());
        captures.values().forEach(CaptureClock::reset);
        updateDisplay();
    }

    private void updateDisplay() {
        String phase = !state.started ? "Installation" : !state.winner.isEmpty() ? "Terminée"
                : state.paused ? "Pause" : state.day < getConfig().getInt("pvp-day") ? "Préparation"
                : state.day < assaultDay() ? "Affrontements" : "Assauts";
        Fk.getInstance().getDisplayService().setScoreboardTitle("§6Fallen Kingdom");
        Fk.getInstance().getDisplayService().setScoreboardLines(List.of(
                "§eJour : " + state.day, "§fPhase : " + phase, "§fÉquipe : {TEAM}",
                "§fRoyaumes : " + (expectedTeams().size() - state.eliminated.size())));
        Fk.getInstance().getDisplayService().updateAll();
    }

    private void tick() {
        if (supplies != null) supplies.tick(Bukkit.getOnlinePlayers().stream().anyMatch(p -> !eliminated(p) && !p.isDead()));
        // Pas d'horloge de jours, pas de progression hors session.
        Fk.getInstance().getGame().stopTimer();
        itemBan.sweep();
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (eliminated(p) && p.getGameMode() != GameMode.SPECTATOR
                    && (state.started || !p.hasPermission("fkamis.admin"))) p.setGameMode(GameMode.SPECTATOR);
        }
        if (state.running()) {
            for (var entry : objectives.entrySet()) {
                if (!state.eliminated.contains(entry.getKey()) && (validated.contains(entry.getKey()) || state.day >= assaultDay()) && !roomValid(entry.getKey())) {
                    state.paused = true;
                    syncNative(); saveState();
                    Bukkit.broadcastMessage("§cObjectif invalide : partie mise en pause pour vérification administrative.");
                    return;
                }
            }
        }
    }

    private void captureTick() {
        if (!state.assaults(assaultDay())) { captures.values().forEach(CaptureClock::reset); return; }
        for (String defender : expectedTeams()) {
            if (state.eliminated.contains(defender)) continue;
            Location center = objectives.get(defender).clone().add(.5, 1, .5);
            double radius = getConfig().getDouble("capture-radius");
            List<Player> nearby = center.getWorld().getNearbyPlayers(center, radius).stream()
                    .filter(p -> !p.isDead() && !blocked(p) && p.getLocation().distanceSquared(center) <= radius * radius
                            && p.hasLineOfSight(center.clone().add(0, .01, 0))).toList();
            Map<String, Long> counts = new HashMap<>();
            for (Player p : nearby) counts.merge(roster.get(p.getUniqueId()), 1L, Long::sum);
            List<String> attackers = counts.keySet().stream().filter(t -> !defender.equals(t)).toList();
            String candidate = attackers.size() == 1 && counts.get(attackers.getFirst()) >= getConfig().getInt("capture-players")
                    ? attackers.getFirst() : null;
            CaptureClock clock = captures.computeIfAbsent(defender, k -> new CaptureClock());
            String previous = clock.attacker;
            int priorTicks = clock.elapsedTicks;
            boolean won = clock.advance(candidate, counts.containsKey(defender), getConfig().getInt("capture-seconds") * 20);
            if (!clock.attacker.isEmpty() && !clock.attacker.equals(previous)) notifyTeams(defender, clock.attacker, "§cCapture engagée ! Défendez votre objectif.");
            if (priorTicks > 0 && clock.elapsedTicks == 0) notifyTeams(defender, previous, "§eCapture interrompue.");
            if (won) { eliminate(defender); return; }
        }
    }

    private void notifyTeams(String a, String b, String message) {
        for (Player p : Bukkit.getOnlinePlayers()) {
            String t = roster.get(p.getUniqueId());
            if (Objects.equals(t, a) || Objects.equals(t, b)) p.sendMessage(message);
        }
    }

    void resetCaptures() { captures.values().forEach(CaptureClock::reset); }

    void checkCaptureMovement(Player player, Location destination) {
        if (!state.assaults(assaultDay()) || eliminated(player)) return;
        String movingTeam = roster.get(player.getUniqueId());
        double radius = getConfig().getDouble("capture-radius");
        for (var e : captures.entrySet()) {
            CaptureClock clock = e.getValue();
            if (clock.attacker.isEmpty()) continue;
            Location center = objectives.get(e.getKey()).clone().add(.5, 1, .5);
            boolean inside = destination.getWorld().equals(center.getWorld()) && destination.distanceSquared(center) <= radius * radius;
            if ((clock.attacker.equals(movingTeam) && !inside) || (!clock.attacker.equals(movingTeam) && inside)) {
                notifyTeams(e.getKey(), clock.attacker, "§eCapture interrompue."); clock.reset();
            }
        }
    }

    boolean roomValid(String name) {
        Location objective = objectives.get(name);
        Team team = teams().getTeam(name);
        if (!validated.contains(name) || objective == null || team == null || team.getBase() == null
                || !team.getBase().contains(objective)) return false;
        if (objective.getBlock().getType() != Material.CHEST) return false;
        if (!objective.clone().add(0, 1, 0).getBlock().isPassable()) return false;
        // Deux joueurs doivent pouvoir se tenir près du coffre. L'accès depuis l'extérieur reste une inspection humaine.
        int standable = 0;
        for (int x = -2; x <= 2; x++) for (int z = -2; z <= 2; z++) {
            Location feet = objective.clone().add(x, 0, z);
            if (feet.getBlock().isPassable() && feet.clone().add(0, 1, 0).getBlock().isPassable()
                    && feet.clone().subtract(0, 1, 0).getBlock().getType().isSolid()
                    && team.getBase().contains(feet) && feet.distanceSquared(objective) <= 4) standable++;
        }
        return standable >= 2;
    }

    private void eliminate(String defender) {
        state.eliminate(defender, expectedTeams());
        captures.values().forEach(CaptureClock::reset);
        saveState(); // L'élimination est durable avant le prochain tick.
        for (Player p : Bukkit.getOnlinePlayers()) if (eliminated(p)) p.setGameMode(GameMode.SPECTATOR);
        Bukkit.broadcastMessage("§cLe royaume " + defender + " est éliminé.");
        if (!state.winner.isEmpty()) Bukkit.broadcastMessage("§6Victoire du royaume " + state.winner + " !");
        syncNative(); saveState();
    }

    @Override public boolean onCommand(CommandSender sender, Command command, String label, String[] args) {
        try {
            if (args.length > 0 && args[0].equalsIgnoreCase("supply")) return supplies.command(sender, args);
            if (args.length == 0 || args[0].equalsIgnoreCase("status")) {
                sender.sendMessage("§6Jour " + state.day + " | " + (state.running() ? "en cours" : "en pause / installation")
                        + " | Royaumes actifs : " + expectedTeams().stream().filter(t -> !state.eliminated.contains(t)).toList());
                return true;
            }
            if (args[0].equalsIgnoreCase("help")) {
                sender.sendMessage("/fka status ; /fka supply status ; /fka room register (coffre ciblé, message privé)");
                if (sender.hasPermission("fkamis.admin")) sender.sendMessage(
                        "Admin : assign <pseudo connecté> <équipe>, unassign <pseudo>, territory <équipe> <rayon>, "
                        + "terrain <équipe> confirm, spawn <équipe>, start [override], pause, resume, nextday, "
                        + "end <open|close>, room <validate|invalidate|inspect> <équipe>, teams tpall [confirm], win <équipe>, save, pregen, survey");
                return true;
            }
            if (args[0].equalsIgnoreCase("room") && args.length == 2 && args[1].equalsIgnoreCase("register")) {
                registerRoom(player(sender)); return true;
            }
            require(sender.hasPermission("fkamis.admin"), "Permission fkamis.admin requise.");
            switch (args[0].toLowerCase(Locale.ROOT)) {
                case "teams" -> { teamTeleports.command(sender,args); return true; }
                case "assign" -> {
                    require(args.length == 3 && !state.started, "Usage avant partie : assign <pseudo connecté> <équipe>");
                    Player p = Objects.requireNonNull(Bukkit.getPlayerExact(args[1]), "Joueur non connecté.");
                    Team t = getTeam(args[2]);
                    require(!roster.containsKey(p.getUniqueId()), "Retirer d'abord le joueur de son équipe.");
                    require(t.getPlayers().size() < 2, "Deux joueurs maximum par équipe.");
                    teams().addPlayer(p.getName(), t.getName());
                    roster.put(p.getUniqueId(), t.getName()); rosterNames.put(p.getUniqueId(), p.getName());
                    p.setGameMode(GameMode.SURVIVAL);
                }
                case "unassign" -> {
                    require(args.length == 2 && !state.started, "Usage avant partie : unassign <pseudo>");
                    UUID id = rosterNames.entrySet().stream().filter(e -> e.getValue().equalsIgnoreCase(args[1]))
                            .map(Map.Entry::getKey).findFirst().orElseThrow(() -> new IllegalArgumentException("Joueur absent."));
                    teams().removePlayerOfHisTeam(rosterNames.remove(id)); roster.remove(id);
                    Player p = Bukkit.getPlayer(id); if (p != null) p.setGameMode(GameMode.SPECTATOR);
                }
                case "territory" -> {
                    require(args.length == 3 && !state.started, "Usage avant partie : territory <équipe> <rayon>");
                    Player p = player(sender); Team t = getTeam(args[1]); int radius = Integer.parseInt(args[2]);
                    require(p.getWorld().getName().equals("world") && radius >= 40 && radius <= 150, "Monde world, rayon entre 40 et 150.");
                    Location at = p.getLocation();
                    if (supplies != null) require(supplies.sites.values().stream().noneMatch(s -> s.location().getWorld().equals(at.getWorld())
                            && Math.abs(s.location().getBlockX()-at.getBlockX()) <= radius+2 && Math.abs(s.location().getBlockZ()-at.getBlockZ()) <= radius+2),
                            "Un emplacement de ravitaillement chevauche ce territoire.");
                    double edge = getConfig().getInt("border-size") / 2.0;
                    require(Math.abs(at.getBlockX()) + radius + 4 < edge && Math.abs(at.getBlockZ()) + radius + 4 < edge, "Territoire trop proche de la bordure.");
                    for (Team other : teams().getTeams()) {
                        if (other.equals(t) || other.getBase() == null) continue;
                        Location c = other.getBase().getCenter(); int separation = radius + other.getBase().getRadius() + 100;
                        require(Math.abs(c.getX() - at.getX()) > separation || Math.abs(c.getZ() - at.getZ()) > separation,
                                "Territoires trop proches ou superposés.");
                    }
                    // Ne jamais appeler construct() : aucun bloc, drapeau ni mur n'est placé.
                    t.setBase(new Base(t, at.clone(), radius, Material.AIR, (byte) 0));
                    Fk.getInstance().getWorldManager().invalidateBaseWorldsCache(teams());
                    spawns.put(t.getName(), at.clone());
                    terrainValidated.remove(t.getName()); validated.remove(t.getName()); objectives.remove(t.getName());
                }
                case "terrain" -> {
                    require(args.length == 3 && args[2].equalsIgnoreCase("confirm") && !state.started,
                            "Après inspection : terrain <équipe> confirm");
                    Team t = getTeam(args[1]); require(t.getBase() != null, "Territoire absent.");
                    terrainValidated.add(t.getName());
                }
                case "spawn" -> {
                    require(args.length == 2 && !state.started, "Usage avant partie : spawn <équipe>");
                    Player p = player(sender); Team t = getTeam(args[1]);
                    require(t.getBase() != null && t.getBase().contains(p.getLocation()), "Point hors du territoire.");
                    spawns.put(t.getName(), p.getLocation().clone());
                }
                case "start" -> {
                    boolean override = args.length == 2 && args[1].equalsIgnoreCase("override");
                    require(args.length == 1 || override, "Usage : start [override]");
                    require(teams().getTeamNames().size() == 4 && teams().getTeamNames().containsAll(expectedTeams()), "Liste d'équipes incohérente.");
                    require(terrainValidated.containsAll(expectedTeams()), "Inspecter et confirmer les quatre terrains naturels.");
                    for (String name : expectedTeams()) require(safeSpawn(name), "Point d'apparition dangereux ou absent : " + name);
                    for (var e : roster.entrySet()) {
                        Player p = Bukkit.getPlayer(e.getKey());
                        require(override || p != null, "Tous les joueurs doivent être connectés, ou utiliser override.");
                        require(override || !Objects.requireNonNull(p).isOp(), "Retirer OP aux participants avant le lancement.");
                    }
                    state.start(expectedTeams().stream().map(t -> getTeam(t).getPlayers().size()).toList(), override);
                    for (Player p : Bukkit.getOnlinePlayers()) if (!eliminated(p)) {
                        p.closeInventory(); p.setGameMode(GameMode.SURVIVAL); p.teleport(spawns.get(roster.get(p.getUniqueId())));
                    }
                    syncNative(); Bukkit.broadcastMessage("§6Début de la partie : jour 1, préparation !");
                }
                case "pause" -> {
                    require(state.running(), "Aucune partie active."); state.paused = true;
                    Bukkit.getOnlinePlayers().forEach(Player::closeInventory); syncNative();
                    Bukkit.broadcastMessage("§ePartie en pause.");
                }
                case "resume" -> {
                    require(state.started && state.paused && state.winner.isEmpty(), "Reprise impossible.");
                    require(state.day < assaultDay() || expectedTeams().stream().filter(t -> !state.eliminated.contains(t)).allMatch(this::roomValid),
                            "Les objectifs actifs doivent être valides avant la reprise.");
                    state.paused = false; syncNative(); Bukkit.broadcastMessage("§aPartie reprise.");
                }
                case "nextday" -> {
                    state.nextDay(assaultDay(), expectedTeams().stream().filter(t -> !state.eliminated.contains(t)).allMatch(this::roomValid));
                    syncNative(); Bukkit.broadcastMessage("§6Jour " + state.day + " : "
                            + (state.day >= assaultDay() ? "assauts ouverts" : state.day >= getConfig().getInt("pvp-day") ? "PvP ouvert hors royaumes protégés" : "préparation"));
                }
                case "end" -> {
                    require(args.length == 2 && (args[1].equals("open") || args[1].equals("close")), "Usage : end <open|close>");
                    if (args[1].equals("close")) require(Bukkit.getOnlinePlayers().stream().noneMatch(p -> p.getWorld().getEnvironment() == World.Environment.THE_END), "Faire revenir les joueurs de l'End avant sa fermeture.");
                    state.endOpen = args[1].equals("open"); configureNative(); syncNative();
                }
                case "room" -> {
                    require(args.length == 3, "Usage : room <validate|invalidate|inspect> <équipe>");
                    String name = getTeam(args[2]).getName();
                    require(objectives.containsKey(name), "Aucun objectif enregistré.");
                    switch (args[1]) {
                        case "validate" -> {
                            require(!state.running() || state.day < assaultDay(), "Mettre la partie en pause avant modification.");
                            validated.add(name);
                            if (!roomValid(name)) { validated.remove(name); throw new IllegalArgumentException("Coffre/espace/territoire invalide."); }
                            sender.sendMessage("Validation enregistrée. L'accès légitime doit avoir été inspecté manuellement.");
                        }
                        case "invalidate" -> {
                            require(!state.running() || state.day < assaultDay(), "Mettre en pause avant invalidation."); validated.remove(name);
                        }
                        case "inspect" -> {
                            Location l = objectives.get(name);
                            sender.sendMessage("§7[Privé admin] " + name + " : " + l.getWorld().getName() + " " + l.getBlockX() + " " + l.getBlockY() + " " + l.getBlockZ() + " ; valide=" + roomValid(name));
                        }
                        default -> throw new IllegalArgumentException("Action de salle inconnue.");
                    }
                }
                case "win" -> {
                    require(args.length == 2 && state.started && state.winner.isEmpty(), "Usage en partie : win <équipe>");
                    String name = getTeam(args[1]).getName(); require(!state.eliminated.contains(name), "Équipe déjà éliminée.");
                    state.winner = name; state.paused = true; syncNative();
                    Bukkit.broadcastMessage("§6Victoire administrative du royaume " + name + " !");
                }
                case "save" -> {
                    Bukkit.getOnlinePlayers().forEach(Player::saveData);
                    Bukkit.getWorlds().forEach(World::save);
                    Fk.getInstance().getSaveableManager().delayedSaveAll();
                }
                case "pregen" -> { pregen(sender); return true; }
                case "survey" -> { survey(sender); return true; }
                default -> throw new IllegalArgumentException("Commande inconnue : /fka help");
            }
            saveState(); updateDisplay(); sender.sendMessage("§aOpération enregistrée.");
        } catch (IllegalArgumentException | IllegalStateException | NullPointerException ex) {
            sender.sendMessage("§c" + ex.getMessage());
        }
        return true;
    }

    private void registerRoom(Player p) {
        require(state.running() && state.day < assaultDay() && !eliminated(p), "Enregistrer pendant la préparation, avant les assauts.");
        Block block = p.getTargetBlockExact(5);
        require(block != null && block.getType() == Material.CHEST, "Cibler un coffre ordinaire à cinq blocs maximum.");
        require(supplies == null || !supplies.managed(block.getLocation()), "Un coffre de ravitaillement ne peut pas devenir un objectif secret.");
        Team t = team(p); require(t != null && t.getBase() != null && t.getBase().contains(block), "Coffre hors de votre territoire.");
        objectives.put(t.getName(), block.getLocation()); validated.remove(t.getName()); saveState();
        p.sendMessage("§aObjectif secret enregistré ; demander une inspection privée à l'administrateur.");
    }

    private boolean safeSpawn(String name) {
        Location at = spawns.get(name); Team t = getTeam(name);
        return at != null && t.getBase() != null && t.getBase().contains(at) && at.getBlock().isPassable()
                && at.clone().add(0, 1, 0).getBlock().isPassable()
                && at.clone().subtract(0, 1, 0).getBlock().getType().isSolid();
    }

    private void pregen(CommandSender sender) {
        require(!state.started && !pregenerating, "Prégénération réservée à l'installation ; tâche déjà active possible.");
        require(Bukkit.getOnlinePlayers().stream().noneMatch(p -> !p.hasPermission("fkamis.admin")), "Aucun joueur pendant la prégénération.");
        World world = Objects.requireNonNull(Bukkit.getWorld("world"));
        int r = (getConfig().getInt("border-size") / 2 + 32) >> 4;
        var chunks = new ArrayDeque<int[]>();
        for (int x = -r; x <= r; x++) for (int z = -r; z <= r; z++) chunks.add(new int[]{x, z});
        pregenerating = true; sender.sendMessage("Prégénération naturelle lancée : " + chunks.size() + " chunks.");
        int total = chunks.size();
        new org.bukkit.scheduler.BukkitRunnable() {
            int pending;
            int completed;
            boolean failed;
            @Override public void run() {
                if (failed) return;
                if (chunks.isEmpty() && pending == 0) {
                    pregenerating = false; world.save(); sender.sendMessage("Prégénération terminée ; inspection des quatre terrains requise."); cancel(); return;
                }
                while (pending < 3 && !chunks.isEmpty()) {
                    int[] c = chunks.remove(); pending++;
                    world.getChunkAtAsync(c[0], c[1], true).whenComplete((chunk, failure) ->
                        Bukkit.getScheduler().runTask(FKAmis.this, () -> {
                            pending--;
                            if (failure != null) { failed = true; pregenerating = false; cancel(); getLogger().log(Level.SEVERE, "Prégénération interrompue", failure); return; }
                            completed++; world.unloadChunkRequest(c[0], c[1]);
                            if (completed % 1000 == 0) sender.sendMessage("Prégénération : " + completed + "/" + total + " chunks.");
                        }));
                }
            }
        }.runTaskTimer(this, 1, 1);
    }

    private void survey(CommandSender sender) {
        require(!state.started, "Inspection disponible avant la partie.");
        World world = Objects.requireNonNull(Bukkit.getWorld("world"));
        List<String> report = new ArrayList<>(List.of("equipe,x,z,y,biome"));
        for (Team t : teams().getTeams()) {
            int candidate = expectedTeams().indexOf(t.getName());
            int cx = t.getBase() == null ? (candidate % 2 == 0 ? -500 : 500) : t.getBase().getCenter().getBlockX();
            int cz = t.getBase() == null ? (candidate < 2 ? -500 : 500) : t.getBase().getCenter().getBlockZ();
            for (int dx : new int[]{-64, 0, 64}) for (int dz : new int[]{-64, 0, 64}) {
                int x = cx + dx, z = cz + dz, y = world.getHighestBlockYAt(x, z);
                report.add(t.getName() + "," + x + "," + z + "," + y + "," + world.getBiome(x, y, z).getKey());
            }
        }
        try { Files.write(getDataFolder().toPath().resolve("terrain-survey.csv"), report, StandardCharsets.UTF_8); }
        catch (IOException ex) { throw new IllegalStateException("Impossible d'écrire le rapport.", ex); }
        sender.sendMessage("Rapport terrain privé écrit. Ressources, structures et accès restent à inspecter en jeu.");
    }

    private Team getTeam(String name) {
        require(expectedTeams().contains(name), "Équipe inconnue : " + expectedTeams());
        return Objects.requireNonNull(teams().getTeam(name), "Équipe native absente.");
    }
    private static Player player(CommandSender sender) {
        require(sender instanceof Player, "Commande à exécuter en jeu."); return (Player) sender;
    }
    private static void require(boolean condition, String message) {
        if (!condition) throw new IllegalArgumentException(message);
    }

    private void loadState() throws Exception {
        Path file = getDataFolder().toPath().resolve("state.yml");
        if (!Files.exists(file)) {
            require(!Fk.getInstance().getGame().hasStarted(), "État FKAmis absent sur une partie native commencée : restaurer une sauvegarde complète.");
            return;
        }
        YamlConfiguration yaml = new YamlConfiguration(); yaml.load(file.toFile());
        require(yaml.getInt("schema") == 1, "Schéma de sauvegarde invalide.");
        state.day = yaml.getInt("day"); state.started = yaml.getBoolean("started"); state.paused = true;
        savedSupplies = yaml.getConfigurationSection("supplies");
        state.endOpen = yaml.getBoolean("end-open"); state.winner = yaml.getString("winner", "");
        state.eliminated.addAll(yaml.getStringList("eliminated"));
        require(state.day >= 0 && (state.started == (state.day > 0)) && expectedTeams().containsAll(state.eliminated)
                && (state.winner.isEmpty() || expectedTeams().contains(state.winner)), "État logique corrompu.");
        ConfigurationSection nativeTeams = Objects.requireNonNull(yaml.getConfigurationSection("native"), "Équipes natives absentes.");
        FkPI.getInstance().load(nativeTeams);
        for (String name : expectedTeams()) {
            if (yaml.contains("objectives." + name)) objectives.put(name, readLocation(yaml, "objectives." + name));
            if (yaml.contains("spawns." + name)) spawns.put(name, readLocation(yaml, "spawns." + name));
        }
        validated.addAll(yaml.getStringList("validated")); terrainValidated.addAll(yaml.getStringList("terrain-validated"));
        ConfigurationSection identities = yaml.getConfigurationSection("roster");
        if (identities != null) for (String key : identities.getKeys(false)) {
            UUID id = UUID.fromString(key); String team = identities.getString(key + ".team");
            require(expectedTeams().contains(team), "Équipe d'identité inconnue.");
            roster.put(id, team); rosterNames.put(id, Objects.requireNonNull(identities.getString(key + ".name")));
        }
        for (String name : expectedTeams()) {
            Team t = teams().getTeam(name);
            require(t != null && t.getPlayers().size() <= 2, "Équipes incohérentes.");
            Set<String> names = new HashSet<>();
            roster.forEach((id, team) -> { if (name.equals(team)) names.add(rosterNames.get(id)); });
            require(names.equals(new HashSet<>(t.getPlayers())), "Identités et équipe native incohérentes.");
        }
    }

    private Location readLocation(YamlConfiguration yaml, String key) {
        World world = Objects.requireNonNull(Bukkit.getWorld(yaml.getString(key + ".world", "world")), "Monde de sauvegarde absent.");
        return new Location(world, yaml.getDouble(key + ".x"), yaml.getDouble(key + ".y"), yaml.getDouble(key + ".z"),
                (float) yaml.getDouble(key + ".yaw"), (float) yaml.getDouble(key + ".pitch"));
    }
    private void writeLocation(YamlConfiguration yaml, String key, Location l) {
        yaml.set(key + ".world", l.getWorld().getName()); yaml.set(key + ".x", l.getX());
        yaml.set(key + ".y", l.getY()); yaml.set(key + ".z", l.getZ());
        yaml.set(key + ".yaw", l.getYaw()); yaml.set(key + ".pitch", l.getPitch());
    }

    void saveState() {
        if (!ready) return;
        try {
            YamlConfiguration yaml = new YamlConfiguration();
            yaml.set("schema", 1); yaml.set("day", state.day); yaml.set("started", state.started);
            yaml.set("end-open", state.endOpen); yaml.set("winner", state.winner);
            yaml.set("eliminated", new ArrayList<>(state.eliminated));
            yaml.set("validated", new ArrayList<>(validated)); yaml.set("terrain-validated", new ArrayList<>(terrainValidated));
            for (var e : objectives.entrySet()) writeLocation(yaml, "objectives." + e.getKey(), e.getValue());
            for (var e : spawns.entrySet()) writeLocation(yaml, "spawns." + e.getKey(), e.getValue());
            for (var e : roster.entrySet()) {
                yaml.set("roster." + e.getKey() + ".team", e.getValue());
                yaml.set("roster." + e.getKey() + ".name", rosterNames.get(e.getKey()));
            }
            FkPI.getInstance().save(yaml.createSection("native"));
            if (supplies != null) supplies.save(yaml.createSection("supplies"));
            Path temporary = getDataFolder().toPath().resolve("state.yml.tmp");
            Files.writeString(temporary, yaml.saveToString(), StandardCharsets.UTF_8);
            try (FileChannel channel = FileChannel.open(temporary, StandardOpenOption.WRITE)) { channel.force(true); }
            Files.move(temporary, getDataFolder().toPath().resolve("state.yml"), StandardCopyOption.ATOMIC_MOVE, StandardCopyOption.REPLACE_EXISTING);
        } catch (IOException ex) {
            state.paused = true;
            getLogger().log(Level.SEVERE, "Écriture atomique impossible, arrêt de sécurité. Ne pas supprimer state.yml.", ex);
            getServer().shutdown();
        }
    }

    private void reconcilePlayer(Player p) {
        String name = roster.get(p.getUniqueId());
        if (name != null) {
            String previous = rosterNames.get(p.getUniqueId());
            if (!p.getName().equals(previous)) {
                if (teams().getPlayerTeam(previous) != null) teams().removePlayerOfHisTeam(previous);
                teams().addPlayer(p.getName(), name); rosterNames.put(p.getUniqueId(), p.getName()); saveState();
            }
        }
        if (eliminated(p) && (state.started || !p.hasPermission("fkamis.admin"))) p.setGameMode(GameMode.SPECTATOR);
        else if (state.started) p.setGameMode(GameMode.SURVIVAL);
        itemBan.clean(p.getInventory());
        World.Environment environment = p.getWorld().getEnvironment();
        if ((environment == World.Environment.NETHER && state.day < getConfig().getInt("nether-day"))
                || (environment == World.Environment.THE_END && !state.endOpen)) {
            returningToSafety = true;
            GameMode previousMode = p.getGameMode();
            try {
                // La pause native refuse les téléportations survival. Le passage temporaire
                // en spectateur permet uniquement ce retour contrôlé vers l'Overworld.
                p.setGameMode(GameMode.SPECTATOR);
                p.teleport(Objects.requireNonNull(Bukkit.getWorld("world")).getSpawnLocation());
            } finally { p.setGameMode(previousMode); returningToSafety = false; }
        }
    }

    @EventHandler public void onJoin(PlayerJoinEvent e) { Bukkit.getScheduler().runTask(this, () -> reconcilePlayer(e.getPlayer())); }
    @EventHandler public void onQuit(PlayerQuitEvent e) {
        captures.values().forEach(CaptureClock::reset);
        if (state.running() && roster.containsKey(e.getPlayer().getUniqueId()) && !eliminated(e.getPlayer())) {
            state.paused = true; syncNative(); saveState();
            Bukkit.broadcastMessage("§eDéconnexion d'un participant : partie mise en pause. Reprise administrative requise.");
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void onRespawn(PlayerRespawnEvent e) {
        String name = roster.get(e.getPlayer().getUniqueId());
        if (name != null && !state.eliminated.contains(name) && safeSpawn(name)) e.setRespawnLocation(spawns.get(name));
    }

    private boolean forbiddenNative(String input) {
        String trimmed = input.strip().toLowerCase(Locale.ROOT);
        if (trimmed.startsWith("/")) trimmed = trimmed.substring(1);
        String root = trimmed.split("\\s+", 2)[0];
        return Set.of("fk", "fallenkingdom", "fallenkingdom:fk", "fallenkingdom:fallenkingdom").contains(root)
                && !(trimmed.matches("[^ ]+ +rules +list *") || trimmed.matches("[^ ]+ +team +list *"));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void command(PlayerCommandPreprocessEvent e) {
        String normalized = e.getMessage().toLowerCase(Locale.ROOT);
        if (forbiddenNative(normalized) || (state.started && roster.containsKey(e.getPlayer().getUniqueId())
                && !normalized.matches("^/(fka|fkamis:fka)(\\s.*)?$") && !normalized.matches("^/(fk|fallenkingdom:fk) (team|rules) list\\s*$"))) {
            e.setCancelled(true); e.getPlayer().sendMessage("§cUtiliser /fka ; commandes de partie natives verrouillées.");
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void command(ServerCommandEvent e) {
        if (!internalCommand && forbiddenNative(e.getCommand())) {
            e.setCancelled(true); e.getSender().sendMessage("Utiliser fka : commandes natives verrouillées pour garantir la cohérence et la confidentialité.");
        }
    }

    @Override public List<String> onTabComplete(CommandSender s, Command c, String alias, String[] args) {
        if (!s.hasPermission("fkamis.admin")) return args.length == 1 ? List.of("status", "help", "room", "supply") : args.length == 2 && args[0].equals("supply") ? List.of("status") : List.of();
        if (args.length == 2 && args[0].equals("supply")) return List.of("status", "list", "enable", "disable", "reload", "test", "add", "remove").stream().filter(a -> a.startsWith(args[1])).toList();
        if (args.length == 2 && args[0].equalsIgnoreCase("teams")) return List.of("tpall");
        if (args.length == 3 && args[0].equalsIgnoreCase("teams") && args[1].equalsIgnoreCase("tpall")) return List.of("confirm");
        if (args.length == 1) return List.of("status", "help", "supply", "teams", "assign", "unassign", "territory", "terrain", "spawn", "start", "pause", "resume", "nextday", "end", "room", "win", "save", "pregen", "survey").stream().filter(t -> t.startsWith(args[0])).toList();
        return List.of();
    }

    @Override public void onDisable() {
        if (!ready) return;
        state.paused = true;
        Fk.getInstance().getGame().stopTimer();
        saveState();
        getServer().getServerTickManager().setFrozen(false);
        for (World world : Bukkit.getWorlds()) world.removePluginChunkTickets(this);
    }
}
