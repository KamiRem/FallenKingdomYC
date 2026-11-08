package fr.fkamis;

import java.util.Collection;

/** Capacité officielle, indépendante des connexions momentanées. */
final class TeamCapacity {
    static int validate(int capacity) {
        if (capacity < 1 || capacity > 4) throw new IllegalArgumentException("players-per-team doit être un entier entre 1 et 4.");
        return capacity;
    }
    static void existing(int configured, int saved, boolean started, Collection<Integer> sizes) {
        validate(configured); validate(saved);
        if (sizes.stream().anyMatch(n -> n > configured))
            throw new IllegalArgumentException("players-per-team=" + configured + " inférieur à un effectif enregistré ; rétablir la capacité sans supprimer state.yml.");
        if (started && saved != configured)
            throw new IllegalArgumentException("Partie déjà commencée : conserver players-per-team=" + saved + " jusqu'à une nouvelle partie.");
    }
    static int attackers(int configured, long officialMembers) {
        return (int)Math.min(configured, officialMembers);
    }
}
