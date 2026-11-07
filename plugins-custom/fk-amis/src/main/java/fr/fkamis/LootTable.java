package fr.fkamis;

import java.util.*;

/** Tirage pur, testable sans serveur. Les poids concernent chaque tirage, pas le coffre entier. */
final class LootTable {
    record Entry(String material, int min, int max, int unitCost, String enchant, int level) {}
    record Tier(String name, int weight, List<Entry> entries) {}
    record Reward(String material, int amount, String enchant, int level) {}
    final List<Tier> tiers;
    final Map<String, Integer> caps;
    final int rolls, chestBudget, eventBudget;
    LootTable(List<Tier> tiers, Map<String, Integer> caps, int rolls, int chestBudget, int eventBudget) {
        if (tiers.isEmpty() || tiers.stream().anyMatch(t -> t.weight <= 0 || t.weight > 100 || t.entries.isEmpty())
                || tiers.stream().mapToInt(Tier::weight).sum() != 100 || rolls < 1 || rolls > 6
                || chestBudget < 1 || eventBudget < chestBudget) throw new IllegalArgumentException("Table de butin invalide.");
        for (Tier tier : tiers) for (Entry e : tier.entries) {
            if (forbidden(e.material) || e.min < 1 || e.max < e.min || e.max > 64 || e.unitCost < 1
                    || !caps.containsKey(e.material) || caps.get(e.material) < 1 || caps.get(e.material) > 64
                    || e.level < 0 || e.level > 2) throw new IllegalArgumentException("Butin interdit ou sans plafond : " + e.material);
        }
        this.tiers = List.copyOf(tiers); this.caps = Map.copyOf(caps); this.rolls = rolls;
        this.chestBudget = chestBudget; this.eventBudget = eventBudget;
    }
    static boolean forbidden(String material) {
        return !Set.of("COOKED_BEEF", "BREAD", "OAK_LOG", "SPRUCE_LOG", "COBBLESTONE", "STONE_BRICKS", "ARROW",
                "COAL", "TORCH", "IRON_INGOT", "GOLD_INGOT", "COPPER_INGOT", "OBSIDIAN", "ENDER_PEARL", "BOW",
                "SHIELD", "IRON_PICKAXE", "IRON_AXE", "BOOK", "LAPIS_LAZULI", "DIAMOND", "ENCHANTED_BOOK").contains(material);
    }
    String category(Random random) {
        int ticket = random.nextInt(100);
        for (Tier tier : tiers) { if (ticket < tier.weight) return tier.name; ticket -= tier.weight; }
        throw new IllegalStateException();
    }
    List<List<Reward>> draw(int chests, Random random) {
        Map<String, Integer> totals = new HashMap<>();
        int budgetLeft = eventBudget;
        List<List<Reward>> bundles = new ArrayList<>();
        for (int chest = 0; chest < chests; chest++) {
            int chestLeft = Math.min(chestBudget, budgetLeft);
            List<Reward> bundle = new ArrayList<>();
            for (int roll = 0; roll < rolls; roll++) {
                String category = category(random);
                List<Entry> entries = tiers.stream().filter(t -> t.name.equals(category)).findFirst().orElseThrow().entries;
                Entry entry = entries.get(random.nextInt(entries.size()));
                int count = entry.min + random.nextInt(entry.max - entry.min + 1);
                count = Math.min(count, caps.get(entry.material) - totals.getOrDefault(entry.material, 0));
                count = Math.min(count, chestLeft / entry.unitCost);
                if (count < 1) continue; // Aucun nouveau tirage : les probabilités annoncées restent celles du tirage brut.
                int cost = count * entry.unitCost;
                chestLeft -= cost; budgetLeft -= cost; totals.merge(entry.material, count, Integer::sum);
                bundle.add(new Reward(entry.material, count, entry.enchant, entry.level));
            }
            bundles.add(List.copyOf(bundle));
        }
        return bundles;
    }
}
