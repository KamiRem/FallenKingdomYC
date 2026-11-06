package fr.fkamis;

import fr.devsylone.fallenkingdom.Fk;
import fr.devsylone.fkpi.FkPI;
import fr.devsylone.fkpi.teams.Base;
import org.bukkit.*;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Cow;
import org.bukkit.event.entity.EntityDamageEvent;
import org.bukkit.event.inventory.InventoryMoveItemEvent;
import org.bukkit.inventory.*;
import org.bukkit.inventory.meta.*;
import org.bukkit.block.ShulkerBox;
import org.bukkit.plugin.java.JavaPlugin;

import java.lang.reflect.*;
import java.util.*;

/** Plugin de recette construit séparément ; jamais inclus dans le JAR FKAmis livré. */
public final class RuntimeProbe extends JavaPlugin {
    private JavaPlugin companion;
    private int passed;

    @Override public void onEnable() {
        if (!Boolean.getBoolean("fkamis.probe")) { getServer().shutdown(); return; }
        Bukkit.getScheduler().runTaskLater(this, () -> {
            if (Boolean.getBoolean("fkamis.probe.mapseeds")) {
                try { surveySeeds(); }
                catch (Throwable ex) { getLogger().log(java.util.logging.Level.SEVERE, "PROBE FAILED", ex); getServer().shutdown(); }
                return;
            }
            try {
                runChecks();
                getLogger().info("PROBE SUCCESS " + passed);
            }
            catch (Throwable ex) { getLogger().log(java.util.logging.Level.SEVERE, "PROBE FAILED", ex); }
            finally { getServer().shutdown(); }
        }, 40);
    }
    private Object field(Object target, String name) throws Exception {
        Field field = target.getClass().getDeclaredField(name); field.setAccessible(true); return field.get(target);
    }
    private void field(Object target, String name, Object value) throws Exception {
        Field field = target.getClass().getDeclaredField(name); field.setAccessible(true); field.set(target, value);
    }
    private Object invoke(Object target, String name, Class<?>[] types, Object... values) throws Exception {
        Method method = target.getClass().getDeclaredMethod(name, types); method.setAccessible(true); return method.invoke(target, values);
    }
    private void command(String... args) {
        companion.onCommand(Bukkit.getConsoleSender(), Objects.requireNonNull(companion.getCommand("fka")), "fka", args);
    }
    private void check(boolean condition, String label) {
        if (!condition) throw new AssertionError(label);
        passed++; getLogger().info("PROBE PASS " + label);
    }
    private void surveySeeds() throws Exception {
        java.nio.file.Files.createDirectories(getDataFolder().toPath());
        java.util.List<String> lines = new java.util.ArrayList<>();
        lines.add("seed,team,x,z,y,biome,surface");
        long[] seeds = {8675309L, 246813579L, 20261106L, 42L, 123456789L, -19999959L};
        new org.bukkit.scheduler.BukkitRunnable() {
          int next;
          @Override public void run() {
            if (next == seeds.length) { getLogger().info("PROBE SUCCESS seed survey"); cancel(); getServer().shutdown(); return; }
            long seed = seeds[next++];
            try {
            World world = Objects.requireNonNull(new WorldCreator("candidate-" + seed).seed(seed).generateStructures(true).createWorld());
            for (int index = 0; index < 4; index++) {
                int cx = index % 2 == 0 ? -500 : 500, cz = index < 2 ? -500 : 500;
                String team = java.util.List.of("Rouge", "Bleue", "Verte", "Jaune").get(index);
                for (int dx : new int[]{-64, 0, 64}) for (int dz : new int[]{-64, 0, 64}) {
                    int x = cx + dx, z = cz + dz, y = world.getHighestBlockYAt(x, z);
                    lines.add(seed + "," + team + "," + x + "," + z + "," + y + "," + world.getBiome(x,y,z).getKey()
                            + "," + world.getBlockAt(x,y,z).getType());
                }
            }
            java.nio.file.Files.write(getDataFolder().toPath().resolve("seed-survey.csv"), lines, java.nio.charset.StandardCharsets.UTF_8);
            getLogger().info("SEED SURVEY " + seed + " complete");
            Bukkit.unloadWorld(world, true);
            } catch (Throwable ex) { getLogger().log(java.util.logging.Level.SEVERE, "PROBE FAILED", ex); cancel(); getServer().shutdown(); }
          }
        }.runTaskTimer(this, 1, 1);
    }
    @SuppressWarnings("unchecked") private void runChecks() throws Exception {
        companion = (JavaPlugin) Objects.requireNonNull(Bukkit.getPluginManager().getPlugin("FKAmis"));
        Object state = field(companion, "state");
        if (Boolean.getBoolean("fkamis.probe.restore")) {
            check((int) field(state, "day") == 3, "restart retains day three");
            check("Verte".equals(field(state, "winner")), "restart retains winner");
            check(((Set<?>) field(state, "eliminated")).size() == 3, "restart retains eliminations");
            check((boolean) field(state, "paused") && getServer().getServerTickManager().isFrozen(), "restart is frozen");
            command("resume"); check((boolean) field(state, "paused"), "finished match cannot resume");
            return;
        }
        check(FkPI.getInstance().getTeamManager().getTeams().size() == 4, "four native teams");
        command("start"); check(!(boolean) field(state, "started"), "start refuses uninspected terrain");
        World world = Objects.requireNonNull(Bukkit.getWorld("world"));
        Map<String, Location> spawns = (Map<String, Location>) field(companion, "spawns");
        Set<String> terrains = (Set<String>) field(companion, "terrainValidated");
        int index = 0;
        for (var team : FkPI.getInstance().getTeamManager().getTeams()) {
            int x = index % 2 == 0 ? -400 : 400, z = index < 2 ? -400 : 400; index++;
            Location loc = new Location(world, x + .5, world.getHighestBlockYAt(x, z) + 1, z + .5);
            loc.clone().subtract(0, 1, 0).getBlock().setType(Material.STONE);
            loc.getBlock().setType(Material.AIR); loc.clone().add(0, 1, 0).getBlock().setType(Material.AIR);
            // Terrains de fixture seulement, jamais attestation d'équilibre de la carte livrée.
            team.setBase(new Base(team, loc, 60, Material.AIR, (byte) 0));
            spawns.put(team.getName(), loc); terrains.add(team.getName());
        }
        Fk.getInstance().getWorldManager().invalidateBaseWorldsCache(FkPI.getInstance().getTeamManager());
        command("start"); check(!(boolean) field(state, "started"), "start refuses empty roster");
        command("start", "override");
        check((boolean) field(state, "started") && (int) field(state, "day") == 1, "explicit override starts day one");
        check(!Fk.getInstance().getGame().isPvpEnabled() && !Fk.getInstance().getGame().isAssaultsEnabled()
                && !Fk.getInstance().getGame().isNetherEnabled(), "native caps closed day one");
        command("nextday");
        check((int) field(state, "day") == 2 && Fk.getInstance().getGame().isPvpEnabled()
                && Fk.getInstance().getGame().isNetherEnabled() && !Fk.getInstance().getGame().isAssaultsEnabled(), "day two native caps");
        command("nextday"); check((int) field(state, "day") == 2, "day three refuses missing objectives");

        Object ban = field(companion, "itemBan");
        org.bukkit.event.server.ServerCommandEvent bannedCommand = new org.bukkit.event.server.ServerCommandEvent(
                Bukkit.getConsoleSender(), "minecraft:give @a minecraft:netherite_sword");
        Bukkit.getPluginManager().callEvent(bannedCommand);
        check(bannedCommand.isCancelled(), "console give forbidden material blocked");
        org.bukkit.event.server.ServerCommandEvent allowedCommand = new org.bukkit.event.server.ServerCommandEvent(
                Bukkit.getConsoleSender(), "minecraft:give @a minecraft:diamond");
        Bukkit.getPluginManager().callEvent(allowedCommand);
        check(!allowedCommand.isCancelled(), "console give legal material retained");
        Inventory inventory = Bukkit.createInventory(null, 9);
        inventory.setItem(0, new ItemStack(Material.ANCIENT_DEBRIS, 2));
        inventory.setItem(1, new ItemStack(Material.NETHERITE_INGOT));
        inventory.setItem(2, new ItemStack(Material.DIAMOND, 3));
        inventory.setItem(3, new ItemStack(Material.NETHERITE_UPGRADE_SMITHING_TEMPLATE));
        invoke(ban, "clean", new Class<?>[]{Inventory.class}, inventory);
        check(inventory.getItem(0) == null && inventory.getItem(1) == null && inventory.getItem(3) == null
                && inventory.getItem(2).getAmount() == 3, "ban removes only forbidden materials");
        ItemStack shulker = new ItemStack(Material.SHULKER_BOX);
        BlockStateMeta shulkerMeta = (BlockStateMeta) shulker.getItemMeta();
        ShulkerBox box = (ShulkerBox) shulkerMeta.getBlockState();
        box.getInventory().setItem(0, new ItemStack(Material.NETHERITE_SWORD));
        box.getInventory().setItem(1, new ItemStack(Material.BREAD, 5));
        shulkerMeta.setBlockState(box); shulker.setItemMeta(shulkerMeta);
        shulker = (ItemStack) invoke(ban, "sanitize", new Class<?>[]{ItemStack.class}, shulker);
        ShulkerBox cleanBox = (ShulkerBox) ((BlockStateMeta) shulker.getItemMeta()).getBlockState();
        check(cleanBox.getInventory().getItem(0) == null && cleanBox.getInventory().getItem(1).getAmount() == 5, "shulker retains legal contents");
        ItemStack bundle = new ItemStack(Material.BUNDLE);
        BundleMeta bundleMeta = (BundleMeta) bundle.getItemMeta();
        bundleMeta.setItems(List.of(new ItemStack(Material.NETHERITE_SCRAP), new ItemStack(Material.IRON_INGOT, 2)));
        bundle.setItemMeta(bundleMeta);
        bundle = (ItemStack) invoke(ban, "sanitize", new Class<?>[]{ItemStack.class}, bundle);
        check(((BundleMeta) bundle.getItemMeta()).getItems().size() == 1
                && ((BundleMeta) bundle.getItemMeta()).getItems().getFirst().getType() == Material.IRON_INGOT, "bundle retains legal contents");
        Inventory source = Bukkit.createInventory(null, 9), target = Bukkit.createInventory(null, 9);
        source.setItem(0, new ItemStack(Material.NETHERITE_AXE));
        InventoryMoveItemEvent transfer = new InventoryMoveItemEvent(source, source.getItem(0), target, true);
        Bukkit.getPluginManager().callEvent(transfer);
        check(transfer.isCancelled() && source.getItem(0) == null, "hopper transfer forbidden item");

        command("pause");
        check((boolean) field(state, "paused") && getServer().getServerTickManager().isFrozen(), "pause freezes server tick");
        command("resume");
        check(!(boolean) field(state, "paused") && !getServer().getServerTickManager().isFrozen(), "resume unfreezes server tick");
        check(!Fk.getInstance().getGame().isEndEnabled(), "end closed by default");
        command("end", "open"); check(Fk.getInstance().getGame().isEndEnabled(), "end opens administratively");
        command("end", "close"); check(!Fk.getInstance().getGame().isEndEnabled(), "end closes administratively");

        command("pause");
        Map<String, Location> objectives = (Map<String, Location>) field(companion, "objectives");
        for (var team : FkPI.getInstance().getTeamManager().getTeams()) {
            Location base = spawns.get(team.getName()).getBlock().getLocation();
            // Petite fixture technique de salle, exclusivement dans runtime/probe.
            for (int dx = -2; dx <= 2; dx++) for (int dz = -2; dz <= 2; dz++) {
                base.clone().add(dx, -1, dz).getBlock().setType(Material.STONE);
                base.clone().add(dx, 0, dz).getBlock().setType(Material.AIR);
                base.clone().add(dx, 1, dz).getBlock().setType(Material.AIR);
            }
            base.getBlock().setType(Material.CHEST); objectives.put(team.getName(), base);
            command("room", "validate", team.getName());
        }
        Location goal = objectives.get("Rouge");
        Cow observer = world.spawn(goal.clone().add(1.5, 0, .5), Cow.class);
        check(observer.hasLineOfSight(goal.clone().add(.5, 1.01, .5)), "capture target above chest is visible");
        observer.remove();
        command("nextday");
        check((int) field(state, "day") == 3 && Fk.getInstance().getGame().isAssaultsEnabled(), "day three opens with validated objectives");
        command("resume");
        invoke(companion, "eliminate", new Class<?>[]{String.class}, "Rouge");
        invoke(companion, "eliminate", new Class<?>[]{String.class}, "Bleue");
        check(((String) field(state, "winner")).isEmpty(), "two eliminations do not declare victory");
        invoke(companion, "eliminate", new Class<?>[]{String.class}, "Jaune");
        check("Verte".equals(field(state, "winner")) && (boolean) field(state, "paused"), "last kingdom wins");
        YamlConfiguration saved = new YamlConfiguration();
        saved.load(companion.getDataFolder().toPath().resolve("state.yml").toFile());
        check(saved.getInt("day") == 3 && saved.getStringList("eliminated").size() == 3
                && "Verte".equals(saved.getString("winner")), "atomic snapshot persists day elimination winner");
    }
}
