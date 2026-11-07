package fr.fkamis;

/** Compteur en secondes de ticks actifs, sans horloge murale ni rattrapage hors ligne. */
final class SupplyClock {
    int remaining;
    SupplyClock(int remaining) { this.remaining = remaining; }
    boolean advance(boolean started, boolean paused, boolean finished, boolean participantOnline) {
        if (!started || paused || finished || !participantOnline) return false;
        return --remaining <= 0;
    }
}
