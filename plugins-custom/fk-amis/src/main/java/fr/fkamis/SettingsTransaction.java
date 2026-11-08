package fr.fkamis;

import com.google.gson.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;

/** Journal de configuration : reprise déterministe si l'arrêt intervient entre deux fichiers. */
final class SettingsTransaction {
    private static final Set<String> ALLOWED=Set.of("config.yml","supplies.yml");
    static void commit(Path folder,Map<String,String> updates)throws Exception {
        Path journal=folder.resolve("settings-transaction.json");if(Files.exists(journal))throw new IllegalStateException("Transaction de configuration en attente ; redémarrer proprement pour reprise.");
        JsonObject root=new JsonObject();root.addProperty("schema",1);JsonObject files=new JsonObject();root.add("files",files);
        for(var entry:updates.entrySet()) {
            if(!ALLOWED.contains(entry.getKey()))throw new IllegalArgumentException("Fichier de configuration non autorisé.");
            var value=new JsonObject();value.addProperty("before",AtomicData.sha(Files.readString(folder.resolve(entry.getKey()),StandardCharsets.UTF_8)));value.addProperty("text",entry.getValue());files.add(entry.getKey(),value);
        }
        AtomicData.write(journal,new Gson().toJson(root));recover(folder);
    }
    static void recover(Path folder)throws Exception {
        Path journal=folder.resolve("settings-transaction.json");if(!Files.exists(journal))return;
        JsonObject root=JsonParser.parseString(Files.readString(journal,StandardCharsets.UTF_8)).getAsJsonObject();
        if(root.get("schema").getAsInt()!=1)throw new IllegalStateException("Version future de transaction de configuration.");
        JsonObject files=root.getAsJsonObject("files");
        for(var entry:files.entrySet()) {
            if(!ALLOWED.contains(entry.getKey()))throw new IllegalArgumentException("Chemin de configuration inattendu.");
            String current=AtomicData.sha(Files.readString(folder.resolve(entry.getKey()),StandardCharsets.UTF_8)),next=entry.getValue().getAsJsonObject().get("text").getAsString();
            if(!current.equals(entry.getValue().getAsJsonObject().get("before").getAsString())&&!current.equals(AtomicData.sha(next)))throw new IllegalStateException("Configuration modifiée pendant une transaction ; conserver les fichiers.");
        }
        for(var entry:files.entrySet()) {
            Path target=folder.resolve(entry.getKey());String next=entry.getValue().getAsJsonObject().get("text").getAsString();
            if(!Files.readString(target,StandardCharsets.UTF_8).equals(next))AtomicData.write(target,next);
        }
        Files.delete(journal);
    }
}
