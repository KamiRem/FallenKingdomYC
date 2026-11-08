package fr.fkamis;

import java.util.*;

/** Règles exposées par les commandes ; aucune valeur numérique permissive. */
final class GameSettings {
    static final Map<String,Number> DEFAULTS=Collections.unmodifiableMap(new LinkedHashMap<>(Map.of(
        "players-per-team",2,"capture-seconds",60,"capture-players",2,"capture-radius",2.5,
        "pvp-day",2,"assault-day",3,"nether-day",2,"respawn-protection-seconds",5,"supply-interval-seconds",1800)));
    static Number parse(String key,String input) {
        if(!DEFAULTS.containsKey(key))throw new IllegalArgumentException("Paramètre inconnu : "+key);
        try {
            if(key.equals("capture-radius")){double value=Double.parseDouble(input);if(!Double.isFinite(value))throw new NumberFormatException();return value;}
            if(!input.matches("[0-9]{1,8}"))throw new NumberFormatException();return Integer.parseInt(input);
        }catch(NumberFormatException error){throw new IllegalArgumentException("Valeur numérique invalide pour "+key+".");}
    }
    static void validate(Map<String,Number> values,Collection<Integer> rosterSizes) {
        int capacity=values.get("players-per-team").intValue();TeamCapacity.validate(capacity);
        TeamCapacity.existing(capacity,capacity,false,rosterSizes);
        range(values,"capture-seconds",1,3600);range(values,"capture-players",1,4);
        double radius=values.get("capture-radius").doubleValue();
        if(!Double.isFinite(radius)||radius<1.5||radius>8)throw new IllegalArgumentException("capture-radius : 1.5..8 blocs, pour conserver des places de capture accessibles.");
        range(values,"pvp-day",1,1000);range(values,"assault-day",1,1000);range(values,"nether-day",1,1000);
        if(values.get("pvp-day").intValue()>values.get("assault-day").intValue() || values.get("nether-day").intValue()>values.get("assault-day").intValue())
            throw new IllegalArgumentException("PvP et Nether doivent s'ouvrir au plus tard le jour des assauts.");
        range(values,"respawn-protection-seconds",0,30);range(values,"supply-interval-seconds",60,86400);
    }
    private static void range(Map<String,Number> values,String key,int min,int max) {
        Number value=values.get(key);
        if(value==null||value.doubleValue()!=value.intValue()||value.intValue()<min||value.intValue()>max)
            throw new IllegalArgumentException(key+" : entier entre "+min+" et "+max+" requis.");
    }
}
