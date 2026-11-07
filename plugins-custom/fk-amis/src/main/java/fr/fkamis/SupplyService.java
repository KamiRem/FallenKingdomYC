package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.*;
import org.bukkit.command.CommandSender;
import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.entity.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.PlayerInteractEvent;
import org.bukkit.inventory.*;
import org.bukkit.inventory.meta.EnchantmentStorageMeta;
import org.bukkit.persistence.PersistentDataType;

import java.io.File;
import java.util.*;

/** Conteneurs fixes vides et lots virtuels à attribution unique ; aucun terrain modifié en session. */
final class SupplyService implements Listener {
    record Site(String id, String zone, Location location) {}
    enum Status { ACTIVE, CLAIMED, EXPIRED }
    static final class Drop {
        long event; int ttl; Status status; List<ItemStack> items;
        Drop(long event, int ttl, Status status, List<ItemStack> items) {
            this.event = event; this.ttl = ttl; this.status = status; this.items = items;
        }
    }
    private final FKAmis plugin;
    private final NamespacedKey key;
    private final Random random = new Random();
    final Map<String, Site> sites = new LinkedHashMap<>();
    final Map<String, Drop> drops = new HashMap<>();
    final List<String> previous = new ArrayList<>();
    final List<String> history = new ArrayList<>();
    SupplyClock clock;
    long event;
    boolean enabled, testMode;
    int interval, maxActive, lifetime;
    private boolean zones;
    private LootTable table;
    private int siteGeneration;

    SupplyService(FKAmis plugin, ConfigurationSection saved) throws Exception {
        this.plugin = plugin; key = new NamespacedKey(plugin, "supply-id");
        File file = new File(plugin.getDataFolder(), "supplies.yml");
        if (!file.exists()) plugin.saveResource("supplies.yml", false);
        configure(YamlConfiguration.loadConfiguration(file));
        if (saved != null) {
            clock.remaining = saved.getInt("remaining", interval); event = saved.getLong("event");
            enabled = saved.getBoolean("enabled", enabled);
            previous.addAll(saved.getStringList("previous")); history.addAll(saved.getStringList("history"));
            ConfigurationSection section = saved.getConfigurationSection("drops");
            if (section != null) for (String id : section.getKeys(false)) {
                if (!sites.containsKey(id)) throw new IllegalStateException("Site actif absent de configuration : " + id);
                List<ItemStack> items = new ArrayList<>();
                for (Object value : section.getList(id + ".items", List.of())) {
                    if (!(value instanceof ItemStack item) || LootTable.forbidden(item.getType().name())) throw new IllegalStateException("Lot sauvegardé invalide.");
                    items.add(item);
                }
                drops.put(id, new Drop(section.getLong(id + ".event"), section.getInt(id + ".ttl"),
                        Status.valueOf(section.getString(id + ".status")), items));
            }
        }
        if (clock.remaining < 1 || clock.remaining > interval || activeCount() > maxActive) throw new IllegalStateException("Minuteur de ravitaillement corrompu.");
        loadSites();
    }

    private void loadSites() {
        int generation = ++siteGeneration;
        plugin.chunkLeases.release("supplies");
        for (Site site : sites.values()) {
            if (site.location.getWorld().isChunkLoaded(site.location.getBlockX() >> 4, site.location.getBlockZ() >> 4)) {
                plugin.chunkLeases.retain(site.location.getWorld().getChunkAt(site.location.getBlockX() >> 4, site.location.getBlockZ() >> 4),"supplies");
                continue;
            }
            site.location.getWorld().getChunkAtAsync(site.location.getBlockX() >> 4, site.location.getBlockZ() >> 4, false)
                .thenAccept(chunk -> {
                    if (chunk == null) { plugin.getLogger().warning("Site non prégénéré : " + site.id); return; }
                    if (plugin.isEnabled()) Bukkit.getScheduler().runTask(plugin, () -> {
                        if (generation == siteGeneration) plugin.chunkLeases.retain(chunk,"supplies");
                    });
                });
        }
    }

    private void configure(YamlConfiguration config) {
        int nextInterval = config.getInt("interval-seconds", 1800);
        int nextMax = config.getInt("max-active", 2), nextLifetime = config.getInt("lifetime-seconds", 600);
        if (nextInterval < 60 || nextInterval > 86400 || nextMax < 1 || nextMax > 2 || nextLifetime < 30 || nextLifetime > nextInterval)
            throw new IllegalArgumentException("Intervalle 60..86400, maximum 1..2, durée 30..intervalle requis.");
        Map<String, Integer> caps = new HashMap<>();
        var capSection = Objects.requireNonNull(config.getConfigurationSection("caps"));
        for (String name : capSection.getKeys(false)) caps.put(name, capSection.getInt(name));
        List<LootTable.Tier> tiers = new ArrayList<>();
        var tierSection = Objects.requireNonNull(config.getConfigurationSection("tiers"));
        for (String name : tierSection.getKeys(false)) {
            List<LootTable.Entry> entries = new ArrayList<>();
            for (Map<?, ?> values : config.getMapList("tiers." + name + ".entries")) {
                String material = String.valueOf(values.get("material"));
                Material kind = Material.valueOf(material);
                if (((Number) values.get("max")).intValue() > kind.getMaxStackSize())
                    throw new IllegalArgumentException("Quantité supérieure à une pile autorisée : " + material);
                String enchant = values.containsKey("enchant") ? String.valueOf(values.get("enchant")) : "";
                int level = values.containsKey("level") ? ((Number) values.get("level")).intValue() : 0;
                if (!enchant.isEmpty() && (!material.equals("ENCHANTED_BOOK") || !Set.of("minecraft:efficiency", "minecraft:protection").contains(enchant)))
                    throw new IllegalArgumentException("Enchantement de ravitaillement interdit.");
                entries.add(new LootTable.Entry(material, ((Number) values.get("min")).intValue(), ((Number) values.get("max")).intValue(),
                        ((Number) values.get("cost")).intValue(), enchant, level));
            }
            tiers.add(new LootTable.Tier(name, config.getInt("tiers." + name + ".weight"), entries));
        }
        LootTable nextTable = new LootTable(tiers, caps, config.getInt("rolls-per-chest"), config.getInt("chest-budget"), config.getInt("event-budget"));
        Map<String, Site> nextSites = new LinkedHashMap<>();
        ConfigurationSection locationSection = config.getConfigurationSection("locations");
        if (locationSection != null) for (String id : locationSection.getKeys(false)) {
            if (!id.matches("[a-z0-9_-]{1,32}")) throw new IllegalArgumentException("Identifiant de site invalide.");
            String path = "locations." + id;
            World world = Objects.requireNonNull(Bukkit.getWorld(config.getString(path + ".world", "world")), "Monde de ravitaillement absent.");
            if (!world.getName().equals("world")) throw new IllegalArgumentException("Les ravitaillements sont réservés au monde principal.");
            Location at = new Location(world, config.getInt(path + ".x"), config.getInt(path + ".y"), config.getInt(path + ".z"));
            if (nextSites.values().stream().anyMatch(s -> FKAmis.sameBlock(s.location, at))) throw new IllegalArgumentException("Deux sites occupent le même bloc.");
            nextSites.put(id, new Site(id, config.getString(path + ".zone", id), at));
        }
        if (nextSites.size() > 16) throw new IllegalArgumentException("Seize sites maximum.");
        if (!nextSites.keySet().containsAll(drops.keySet())) throw new IllegalArgumentException("Un site persistant manque à la configuration.");
        table = nextTable; interval = nextInterval; maxActive = nextMax; lifetime = nextLifetime;
        zones = config.getBoolean("announce-zones", true); testMode = config.getBoolean("test-mode", false);
        enabled = config.getBoolean("enabled", false); sites.clear(); sites.putAll(nextSites);
        clock = new SupplyClock(interval);
    }

    int activeCount() { return (int) drops.values().stream().filter(d -> d.status == Status.ACTIVE).count(); }
    boolean managed(Location location) { return sites.values().stream().anyMatch(s -> FKAmis.sameBlock(s.location, location)); }
    boolean managed(Inventory inventory) {
        if (inventory.getLocation() != null && managed(inventory.getLocation())) return true;
        if (inventory.getHolder() instanceof DoubleChest doubleChest)
            return (doubleChest.getLeftSide() instanceof Chest c && managed(c.getLocation()))
                    || (doubleChest.getRightSide() instanceof Chest right && managed(right.getLocation()));
        return false;
    }
    boolean eligible(Site site) {
        Location at = site.location;
        if (!at.getWorld().getWorldBorder().isInside(at) || plugin.territory(at) != null || plugin.objectiveAt(at)) return false;
        // Un chunk déchargé est simplement inéligible : aucune génération ni chargement synchrone en session.
        if (!at.getWorld().isChunkLoaded(at.getBlockX() >> 4, at.getBlockZ() >> 4)) return false;
        if (!(at.getBlock().getState() instanceof Chest chest)) return false;
        if (!site.id.equals(chest.getPersistentDataContainer().get(key, PersistentDataType.STRING))) return false;
        if (!chest.getBlockInventory().isEmpty() || !(chest.getBlockData() instanceof org.bukkit.block.data.type.Chest data)
                || data.getType() != org.bukkit.block.data.type.Chest.Type.SINGLE) return false;
        return at.clone().add(0, 1, 0).getBlock().isPassable() && at.clone().subtract(0, 1, 0).getBlock().getType().isSolid();
    }
    void tick(boolean participantOnline) {
        if (!enabled || !plugin.state.running() || !participantOnline) return;
        for (Drop drop : drops.values()) if (drop.status == Status.ACTIVE && --drop.ttl <= 0) {
            drop.status = Status.EXPIRED; drop.items = List.of();
        }
        if (clock.advance(plugin.state.started, plugin.state.paused, !plugin.state.winner.isEmpty(), participantOnline)) {
            clock.remaining = interval; trigger(false);
        }
        plugin.saveState(); // Une seconde maximum de recul après coupure ; aucune émission hors ligne.
    }
    List<String> trigger(boolean test) {
        if (!test && !plugin.state.running()) return List.of();
        int available = maxActive - activeCount();
        if (available <= 0) return List.of();
        List<Site> candidates = sites.values().stream().filter(this::eligible)
                .filter(s -> !drops.containsKey(s.id) || drops.get(s.id).status != Status.ACTIVE).collect(java.util.stream.Collectors.toCollection(ArrayList::new));
        List<Site> fresh = candidates.stream().filter(s -> !previous.contains(s.id)).toList();
        if (fresh.size() >= available) candidates = new ArrayList<>(fresh);
        Collections.shuffle(candidates, random);
        List<Site> selected = new ArrayList<>();
        for (Site s : candidates) {
            if (selected.stream().anyMatch(other -> other.location.distanceSquared(s.location) < 200 * 200)) continue;
            selected.add(s); if (selected.size() == available) break;
        }
        List<List<LootTable.Reward>> rewards = table.draw(selected.size(), random);
        List<String> emitted = new ArrayList<>();
        long eventId = ++event;
        for (int index = 0; index < selected.size(); index++) {
            Site site = selected.get(index);
            List<ItemStack> items = rewards.get(index).stream().map(this::item).toList();
            if (items.isEmpty()) continue;
            drops.put(site.id, new Drop(eventId, lifetime, Status.ACTIVE, items)); emitted.add(site.id);
        }
        previous.clear(); previous.addAll(emitted);
        history.add(eventId + ":" + (test ? "TEST:" : "") + String.join(",", emitted));
        while (history.size() > 50) history.removeFirst();
        plugin.saveState(); // Les lots sont persistés avant toute annonce ou possibilité de récupération.
        if (!emitted.isEmpty()) Bukkit.broadcastMessage("§6Ravitaillement ! " + emitted.size() + " coffre(s) disponible(s) dans les terres neutres."
                + (zones ? " §eZones : " + emitted.stream().map(id -> sites.get(id).zone).toList() : ""));
        return emitted;
    }
    private ItemStack item(LootTable.Reward reward) {
        ItemStack item = new ItemStack(Material.valueOf(reward.material()), reward.amount());
        if (!reward.enchant().isEmpty()) {
            var enchant = Objects.requireNonNull(Registry.ENCHANTMENT.get(NamespacedKey.fromString(reward.enchant())));
            EnchantmentStorageMeta meta = (EnchantmentStorageMeta) item.getItemMeta();
            meta.addStoredEnchant(enchant, reward.level(), false); item.setItemMeta(meta);
        }
        return item;
    }
    boolean reserveClaim(String id) {
        Drop drop = drops.get(id);
        if (drop == null || drop.status != Status.ACTIVE) return false;
        drop.status = Status.CLAIMED;
        history.add(drop.event + ":CLAIM:" + id);
        while (history.size() > 50) history.removeFirst();
        plugin.saveState();
        return true;
    }
    void save(ConfigurationSection section) {
        section.set("remaining", clock.remaining); section.set("enabled", enabled); section.set("event", event);
        section.set("previous", previous); section.set("history", history);
        for (var entry : drops.entrySet()) {
            Drop drop = entry.getValue(); String path = "drops." + entry.getKey();
            section.set(path + ".event", drop.event); section.set(path + ".ttl", drop.ttl);
            section.set(path + ".status", drop.status.name());
            section.set(path + ".items", drop.status == Status.ACTIVE ? drop.items : List.of());
        }
    }
    boolean command(CommandSender sender, String[] args) {
        String action = args.length > 1 ? args[1] : "status";
        if (action.equals("status")) {
            sender.sendMessage("§eRavitaillement " + (enabled ? "activé" : "désactivé") + " ; prochain : " + clock.remaining
                    + " secondes actives ; coffres : " + activeCount() + "/" + maxActive); return true;
        }
        if (!sender.hasPermission("fkamis.admin")) throw new IllegalArgumentException("Permission fkamis.admin requise.");
        switch (action) {
            case "list" -> sites.values().forEach(s -> sender.sendMessage(s.id + " : " + s.location.getBlockX() + " " + s.location.getBlockY() + " " + s.location.getBlockZ()
                    + " ; " + s.zone + " ; " + (drops.containsKey(s.id) ? drops.get(s.id).status : "INACTIF")));
            case "enable" -> { enabled = true; plugin.saveState(); }
            case "disable" -> { enabled = false; for (Drop d : drops.values()) if (d.status == Status.ACTIVE) { d.status = Status.EXPIRED; d.items = List.of(); } plugin.saveState(); }
            case "test" -> {
                if (!testMode || plugin.state.started || args.length != 3 || !args[2].equals("confirm"))
                    throw new IllegalArgumentException("Test réservé à une instance de recette avant partie : supply test confirm.");
                sender.sendMessage("Sites de test activés : " + trigger(true));
            }
            case "reload" -> {
                if (plugin.state.running() || activeCount() > 0) throw new IllegalArgumentException("Mettre en pause et terminer/désactiver les lots actifs avant rechargement.");
                int remaining = clock.remaining;
                YamlConfiguration config = YamlConfiguration.loadConfiguration(new File(plugin.getDataFolder(), "supplies.yml"));
                Map<String, Site> oldSites = new LinkedHashMap<>(sites);
                configure(config);
                if (!sites.keySet().containsAll(drops.keySet())) {
                    sites.clear(); sites.putAll(oldSites); throw new IllegalArgumentException("Ne pas retirer un site encore présent dans l'historique de la partie.");
                }
                clock.remaining = Math.min(remaining, interval); plugin.saveState();
                loadSites();
            }
            case "add" -> {
                if (!(sender instanceof Player p) || plugin.state.started || args.length < 4) throw new IllegalArgumentException("Avant partie en jeu : supply add <id> <zone_sans_espace>");
                Block target = p.getTargetBlockExact(5);
                String id = args[2];
                if (target == null || !target.getWorld().getName().equals("world") || sites.size() >= 16
                        || !(target.getState() instanceof Chest chest) || !id.matches("[a-z0-9_-]{1,32}")
                        || sites.containsKey(id) || managed(target.getLocation()) || plugin.territory(target.getLocation()) != null || plugin.objectiveAt(target.getLocation())
                        || !chest.getBlockInventory().isEmpty()
                        || ((org.bukkit.block.data.type.Chest) chest.getBlockData()).getType() != org.bukkit.block.data.type.Chest.Type.SINGLE)
                    throw new IllegalArgumentException("Cibler un coffre simple vide, neutre, non enregistré du monde principal ; seize sites maximum, identifiant unique requis.");
                chest.getPersistentDataContainer().set(key, PersistentDataType.STRING, id); chest.update(true, false);
                sites.put(id, new Site(id, args[3], target.getLocation())); persistSites(); plugin.saveState();
                loadSites();
            }
            case "remove" -> {
                if (plugin.state.started || args.length != 3 || !sites.containsKey(args[2])) throw new IllegalArgumentException("Avant partie : supply remove <id>");
                if (drops.containsKey(args[2]) && drops.get(args[2]).status == Status.ACTIVE) throw new IllegalArgumentException("Désactiver les lots avant de retirer ce site.");
                Site site = sites.remove(args[2]); drops.remove(site.id); previous.remove(site.id);
                if (site.location.getBlock().getState() instanceof Chest chest) { chest.getPersistentDataContainer().remove(key); chest.update(true, false); }
                persistSites(); plugin.saveState(); // Le coffre physique est conservé.
                loadSites();
            }
            default -> throw new IllegalArgumentException("supply status|list|enable|disable|test confirm|reload|add|remove");
        }
        sender.sendMessage("§aRavitaillement enregistré."); return true;
    }
    private void persistSites() {
        try {
            File file = new File(plugin.getDataFolder(), "supplies.yml");
            YamlConfiguration config = YamlConfiguration.loadConfiguration(file); config.set("locations", null);
            for (Site site : sites.values()) {
                String path = "locations." + site.id;
                config.set(path + ".world", site.location.getWorld().getName()); config.set(path + ".x", site.location.getBlockX());
                config.set(path + ".y", site.location.getBlockY()); config.set(path + ".z", site.location.getBlockZ()); config.set(path + ".zone", site.zone);
            }
            config.save(file);
        } catch (java.io.IOException ex) { throw new IllegalStateException("Écriture des emplacements impossible.", ex); }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void interact(PlayerInteractEvent e) {
        if (e.getClickedBlock() == null || !managed(e.getClickedBlock().getLocation())) return;
        boolean denied = e.useInteractedBlock() == Event.Result.DENY;
        e.setCancelled(true);
        if (e.getHand() != EquipmentSlot.HAND || e.getAction() != Action.RIGHT_CLICK_BLOCK) return;
        Player p = e.getPlayer();
        if (denied || !plugin.state.running() || plugin.blocked(p) || !enabled) { p.sendMessage("§eRavitaillement indisponible pendant la pause ou hors partie."); return; }
        Site site = sites.values().stream().filter(s -> FKAmis.sameBlock(s.location, e.getClickedBlock().getLocation())).findFirst().orElseThrow();
        Drop drop = drops.get(site.id);
        if (drop == null || drop.status != Status.ACTIVE || !eligible(site)) { p.sendMessage("§7Aucun ravitaillement disponible ici."); return; }
        if (p.getInventory().firstEmpty() < 0 || Arrays.stream(p.getInventory().getStorageContents()).filter(Objects::isNull).count() < drop.items.size()) {
            p.sendMessage("§eLibérez " + drop.items.size() + " emplacements pour récupérer tout le lot."); return;
        }
        List<ItemStack> reward = drop.items.stream().map(ItemStack::clone).toList();
        if (!reserveClaim(site.id) || plugin.state.paused) return;
        for (ItemStack stack : reward) {
            if (!p.getInventory().addItem(stack).isEmpty()) throw new IllegalStateException("Inventaire modifié pendant une attribution synchrone.");
        }
        drop.items = List.of(); p.saveData();
        p.sendMessage("§aLot de ravitaillement récupéré.");
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void open(InventoryOpenEvent e) { if (managed(e.getInventory())) e.setCancelled(true); }
    @EventHandler(priority = EventPriority.HIGHEST) public void transfer(InventoryMoveItemEvent e) { if (managed(e.getSource()) || managed(e.getDestination())) e.setCancelled(true); }
    @EventHandler(priority = EventPriority.HIGHEST) public void breakBlock(BlockBreakEvent e) { if (managed(e.getBlock().getLocation())) e.setCancelled(true); }
    @EventHandler(priority = EventPriority.HIGHEST) public void place(BlockPlaceEvent e) {
        if (managed(e.getBlock().getLocation())) e.setCancelled(true);
        if (e.getBlock().getType() == Material.CHEST || e.getBlock().getType() == Material.TRAPPED_CHEST)
            for (var face : List.of(org.bukkit.block.BlockFace.NORTH, org.bukkit.block.BlockFace.SOUTH, org.bukkit.block.BlockFace.EAST, org.bukkit.block.BlockFace.WEST))
                if (managed(e.getBlock().getRelative(face).getLocation())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void explode(EntityExplodeEvent e) { e.blockList().removeIf(b -> managed(b.getLocation())); }
    @EventHandler(priority = EventPriority.HIGHEST) public void explode(BlockExplodeEvent e) { e.blockList().removeIf(b -> managed(b.getLocation())); }
    @EventHandler(priority = EventPriority.HIGHEST) public void piston(BlockPistonExtendEvent e) {
        if (e.getBlocks().stream().anyMatch(b -> managed(b.getLocation()) || managed(b.getRelative(e.getDirection()).getLocation()))) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void piston(BlockPistonRetractEvent e) {
        if (e.getBlocks().stream().anyMatch(b -> managed(b.getLocation()) || managed(b.getRelative(e.getDirection().getOppositeFace()).getLocation()))) e.setCancelled(true);
    }
}
