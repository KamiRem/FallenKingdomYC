package fr.fkamis;

/** Les morts individuelles ne participent jamais au calcul du rôle ou de l'élimination. */
final class PlayerRoles {
    enum Mode { SURVIVAL, CREATIVE, SPECTATOR }
    static Mode mode(boolean administrator, boolean assigned, boolean kingdomCaptured, boolean started) {
        if (administrator) return Mode.CREATIVE;
        if (kingdomCaptured || started && !assigned) return Mode.SPECTATOR;
        return Mode.SURVIVAL;
    }
    static boolean participant(boolean administrator, boolean assigned) { return !administrator && assigned; }
}
