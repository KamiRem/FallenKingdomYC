package fr.fkamis;

import org.bukkit.*;
import org.bukkit.block.Container;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.block.BlockBreakEvent;
import org.bukkit.event.block.BlockPlaceEvent;
import org.bukkit.event.entity.*;
import org.bukkit.event.inventory.*;
import org.bukkit.event.player.*;
import org.bukkit.event.world.LootGenerateEvent;
import org.bukkit.event.server.ServerCommandEvent;
import org.bukkit.inventory.*;
import org.bukkit.inventory.meta.*;

import java.util.*;
import java.util.regex.Pattern;

/** Filtrage ciblÃ© : les objets autorisÃ©s et les conteneurs sont conservÃ©s. */
final class ItemBan implements Listener {
    private final FKAmis plugin;
    private final Set<Material> banned = EnumSet.noneOf(Material.class);
    private final List<Pattern> commandPatterns = new ArrayList<>();

    ItemBan(FKAmis plugin) {
        this.plugin = plugin;
        for (Material m : Material.values()) {
            if (plugin.getConfig().getBoolean("ban-netherite-family") &&
                    (m.name().contains("NETHERITE") || m == Material.ANCIENT_DEBRIS)) banned.add(m);
        }
        for (String name : plugin.getConfig().getStringList("extra-banned")) {
            Material m = Material.matchMaterial(name);
            if (m == null) throw new IllegalArgumentException("MatÃ©riau interdit inconnu : " + name);
            banned.add(m);
        }
        for (Material material : banned) commandPatterns.add(Pattern.compile(
                "(?<![a-z0-9_])" + Pattern.quote(material.name().toLowerCase(Locale.ROOT)) + "(?![a-z0-9_])"));
        Iterator<Recipe> recipes = Bukkit.recipeIterator();
        while (recipes.hasNext()) if (denied(recipes.next().getResult())) recipes.remove();
    }
    boolean denied(ItemStack item) { return item != null && banned.contains(item.getType()); }
    private boolean forbiddenCommand(String command) {
        String normalized = command.toLowerCase(Locale.ROOT).strip();
        if (normalized.startsWith("/")) normalized = normalized.substring(1);
        String root = normalized.split("\\s+", 2)[0].replace("minecraft:", "");
        if (!Set.of("give", "item", "loot", "summon", "data", "execute").contains(root)) return false;
        String line = normalized;
        return commandPatterns.stream().anyMatch(p -> p.matcher(line).find());
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void command(ServerCommandEvent e) {
        if (forbiddenCommand(e.getCommand())) { e.setCancelled(true); e.getSender().sendMessage("Objet interdit : commande refusÃ©e."); }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void command(PlayerCommandPreprocessEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (forbiddenCommand(e.getMessage())) { e.setCancelled(true); e.getPlayer().sendMessage("Â§cObjet interdit : commande refusÃ©e."); }
    }

    ItemStack sanitize(ItemStack item) { return sanitize(item, 0); }
    private ItemStack sanitize(ItemStack item, int depth) {
        if (item == null || denied(item)) return null;
        // Les conteneurs imbriquÃ©s vanilla restent trÃ¨s peu profonds. Ne jamais supprimer
        // un objet autorisÃ© pour une profondeur anormale : bloquer plutÃ´t l'utilisation.
        if (depth > 32) throw new IllegalStateException("Objet imbriquÃ© anormal : inspection administrative requise.");
        ItemMeta meta = item.getItemMeta();
        if (meta instanceof BlockStateMeta block && block.getBlockState() instanceof Container box) {
            Inventory inventory = box.getInventory();
            for (int i = 0; i < inventory.getSize(); i++) inventory.setItem(i, sanitize(inventory.getItem(i), depth + 1));
            block.setBlockState(box); item.setItemMeta(block);
        } else if (meta instanceof BundleMeta bundle) {
            List<ItemStack> cleaned = new ArrayList<>();
            for (ItemStack content : bundle.getItems()) {
                ItemStack result = sanitize(content, depth + 1); if (result != null) cleaned.add(result);
            }
            bundle.setItems(cleaned); item.setItemMeta(bundle);
        }
        return item;
    }

    void clean(Inventory inventory) {
        for (int i = 0; i < inventory.getSize(); i++) inventory.setItem(i, sanitize(inventory.getItem(i)));
    }
    void sweep() {
        for (Player p : Bukkit.getOnlinePlayers()) {
            if (plugin.isAdministrator(p)) continue;
            clean(p.getInventory()); clean(p.getEnderChest());
            p.setItemOnCursor(sanitize(p.getItemOnCursor()));
            clean(p.getOpenInventory().getTopInventory());
        }
        for (World world : Bukkit.getWorlds()) {
            for (Item item : world.getEntitiesByClass(Item.class)) {
                ItemStack result = sanitize(item.getItemStack());
                if (result == null) item.remove(); else if (!result.equals(item.getItemStack())) item.setItemStack(result);
            }
            for (LivingEntity entity : world.getLivingEntities()) {
                if (entity instanceof Player || entity.getEquipment() == null) continue;
                EntityEquipment equipment = entity.getEquipment();
                equipment.setItemInMainHand(sanitize(equipment.getItemInMainHand()));
                equipment.setItemInOffHand(sanitize(equipment.getItemInOffHand()));
                ItemStack[] armor = equipment.getArmorContents();
                for (int i = 0; i < armor.length; i++) armor[i] = sanitize(armor[i]);
                equipment.setArmorContents(armor);
            }
        }
    }
    private void later(Player player) {
        Bukkit.getScheduler().runTask(plugin, () -> {
            if (player.isOnline() && !plugin.isAdministrator(player)) { clean(player.getInventory()); player.setItemOnCursor(sanitize(player.getItemOnCursor())); }
        });
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void craft(PrepareItemCraftEvent e) {
        if (denied(e.getInventory().getResult())) e.getInventory().setResult(null);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void craft(CraftItemEvent e) {
        if (denied(e.getRecipe().getResult())) { e.setCancelled(true); e.getInventory().setResult(null); }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void smith(PrepareSmithingEvent e) {
        if (denied(e.getResult())) e.setResult(null);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void smith(SmithItemEvent e) {
        if (denied(e.getCurrentItem())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void click(InventoryClickEvent e) {
        if (e.getWhoClicked() instanceof Player p && plugin.isAdministrator(p)) return;
        if (denied(e.getCurrentItem()) || denied(e.getCursor()) ||
                (e.getHotbarButton() >= 0 && denied(e.getWhoClicked().getInventory().getItem(e.getHotbarButton())))) e.setCancelled(true);
        if (e.getWhoClicked() instanceof Player p) later(p);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void drag(InventoryDragEvent e) {
        if (e.getWhoClicked() instanceof Player p && plugin.isAdministrator(p)) return;
        if (e.getNewItems().values().stream().anyMatch(this::denied) || denied(e.getOldCursor())) e.setCancelled(true);
        if (e.getWhoClicked() instanceof Player p) later(p);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void open(InventoryOpenEvent e) {
        if (e.getPlayer() instanceof Player p && plugin.isAdministrator(p)) return;
        clean(e.getInventory());
        if (e.getInventory() instanceof MerchantInventory inventory) {
            Merchant merchant = inventory.getMerchant();
            merchant.setRecipes(merchant.getRecipes().stream().filter(r -> !denied(r.getResult()) && r.getIngredients().stream().noneMatch(this::denied)).toList());
        }
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void transfer(InventoryMoveItemEvent e) {
        if (denied(e.getItem())) { e.setCancelled(true); clean(e.getSource()); }
        else e.setItem(Objects.requireNonNull(sanitize(e.getItem())));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void hopper(InventoryPickupItemEvent e) {
        if (denied(e.getItem().getItemStack())) { e.setCancelled(true); e.getItem().remove(); }
        else e.getItem().setItemStack(Objects.requireNonNull(sanitize(e.getItem().getItemStack())));
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void pickup(EntityPickupItemEvent e) {
        ItemStack item = sanitize(e.getItem().getItemStack());
        if (item == null) { e.setCancelled(true); e.getItem().remove(); }
        else e.getItem().setItemStack(item);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void spawn(ItemSpawnEvent e) {
        ItemStack item = sanitize(e.getEntity().getItemStack());
        if (item == null) e.setCancelled(true); else e.getEntity().setItemStack(item);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void loot(LootGenerateEvent e) {
        e.setLoot(e.getLoot().stream().map(this::sanitize).filter(Objects::nonNull).toList());
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void trade(VillagerAcquireTradeEvent e) {
        if (denied(e.getRecipe().getResult()) || e.getRecipe().getIngredients().stream().anyMatch(this::denied)) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void breakBlock(BlockBreakEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (banned.contains(e.getBlock().getType()) || denied(e.getPlayer().getInventory().getItemInMainHand())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void place(BlockPlaceEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (banned.contains(e.getBlock().getType()) || denied(e.getItemInHand())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void use(PlayerInteractEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (denied(e.getItem())) e.setCancelled(true);
        later(e.getPlayer());
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void consume(PlayerItemConsumeEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (denied(e.getItem())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void glide(EntityToggleGlideEvent e) {
        if(e.getEntity() instanceof Player p&&plugin.isAdministrator(p))return;
        if(e.isGliding()&&banned.contains(Material.ELYTRA))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void equip(org.bukkit.event.block.BlockDispenseArmorEvent e) {
        if(denied(e.getItem()))e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void damage(EntityDamageByEntityEvent e) {
        if (e.getDamager() instanceof Player p && !plugin.isAdministrator(p) && denied(p.getInventory().getItemInMainHand())) e.setCancelled(true);
    }
    @EventHandler(priority = EventPriority.HIGHEST) public void death(EntityDeathEvent e) {
        e.getDrops().removeIf(this::denied);
        e.getDrops().replaceAll(this::sanitize);
        e.getDrops().removeIf(Objects::isNull);
    }
    @EventHandler public void held(PlayerItemHeldEvent e) { later(e.getPlayer()); }
    @EventHandler public void swap(PlayerSwapHandItemsEvent e) {
        if (plugin.isAdministrator(e.getPlayer())) return;
        if (denied(e.getMainHandItem()) || denied(e.getOffHandItem())) e.setCancelled(true);
        later(e.getPlayer());
    }
}
