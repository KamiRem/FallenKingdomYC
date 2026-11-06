package fr.fkamis;

/** Capture continue ; déconnexion, défense, pause ou mélange d'attaquants remet à zéro. */
final class CaptureClock {
    String attacker = "";
    int elapsedTicks;

    boolean advance(String candidate, boolean contested, int duration) {
        if (candidate == null || contested) { reset(); return false; }
        if (!candidate.equals(attacker)) { attacker = candidate; elapsedTicks = 0; return false; }
        return ++elapsedTicks >= duration;
    }

    void reset() { attacker = ""; elapsedTicks = 0; }
}
