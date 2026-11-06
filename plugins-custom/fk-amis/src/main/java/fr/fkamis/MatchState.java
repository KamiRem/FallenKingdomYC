package fr.fkamis;

import java.util.*;

/** État logique indépendant du temps Minecraft et de l'horloge système. */
final class MatchState {
    int day = 0;
    boolean started = false;
    boolean paused = true;
    boolean endOpen = false;
    String winner = "";
    final Set<String> eliminated = new HashSet<>();

    boolean running() { return started && !paused && winner.isEmpty(); }
    boolean assaults(int unlockDay) { return running() && day >= unlockDay; }

    void start(Collection<Integer> sizes, boolean override) {
        if (started) throw new IllegalStateException("La partie a déjà commencé.");
        if (sizes.size() != 4 || sizes.stream().anyMatch(n -> n > 2 || n < 0))
            throw new IllegalStateException("Il faut exactement quatre équipes de deux joueurs maximum.");
        if (!override && sizes.stream().anyMatch(n -> n != 2))
            throw new IllegalStateException("Répartir huit joueurs, ou utiliser start override explicitement.");
        started = true; paused = false; day = 1;
    }

    void nextDay(int assaultDay, boolean allRoomsValid) {
        if (!started || !winner.isEmpty()) throw new IllegalStateException("Aucune partie en cours.");
        if (day + 1 >= assaultDay && !allRoomsValid)
            throw new IllegalStateException("Valider les quatre objectifs avant les assauts.");
        day++;
    }

    void eliminate(String team, Collection<String> teams) {
        if (!started || !winner.isEmpty() || !teams.contains(team))
            throw new IllegalStateException("Élimination impossible.");
        eliminated.add(team);
        List<String> remaining = teams.stream().filter(t -> !eliminated.contains(t)).toList();
        if (remaining.size() == 1) { winner = remaining.getFirst(); paused = true; }
    }
}
