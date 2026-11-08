package fr.fkamis;

import org.bukkit.configuration.ConfigurationSection;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.inventory.ItemStack;
import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;

/** Écritures atomiques et copies conservant les clés inconnues. */
final class AtomicData {
    static void write(Path file,String text)throws IOException {
        Files.createDirectories(file.toAbsolutePath().getParent());
        Path temporary=file.resolveSibling(file.getFileName()+".new");
        Files.writeString(temporary,text,StandardCharsets.UTF_8,StandardOpenOption.CREATE_NEW,StandardOpenOption.WRITE);
        try(FileChannel channel=FileChannel.open(temporary,StandardOpenOption.WRITE)){channel.force(true);}
        Files.move(temporary,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
    }
    static String sha(String text) {
        return shaBytes(text.getBytes(StandardCharsets.UTF_8));
    }
    static String shaBytes(byte[] bytes) {
        try{return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(java.security.NoSuchAlgorithmException error){throw new IllegalStateException(error);}
    }
    static YamlConfiguration copy(ConfigurationSection source) {var result=new YamlConfiguration();if(source!=null)overlay(result,source);return result;}
    static void overlay(ConfigurationSection destination,ConfigurationSection source) {
        for(String key:source.getKeys(false)) {
            Object value=source.get(key);
            if(value instanceof ConfigurationSection child) {
                ConfigurationSection section=destination.getConfigurationSection(key);
                if(section==null)section=destination.createSection(key);
                overlay(section,child);
            } else destination.set(key,cloneValue(value));
        }
    }
    private static Object cloneValue(Object value) {
        if(value instanceof ItemStack stack)return stack.clone();
        if(value instanceof List<?> list)return list.stream().map(AtomicData::cloneValue).toList();
        if(value instanceof Map<?,?> map){Map<Object,Object> copy=new LinkedHashMap<>();map.forEach((key,item)->copy.put(key,cloneValue(item)));return copy;}
        return value;
    }
}
