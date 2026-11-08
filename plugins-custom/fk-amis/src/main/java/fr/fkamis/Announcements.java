package fr.fkamis;

import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.title.Title;
import org.bukkit.*;
import org.bukkit.command.CommandSender;
import org.bukkit.entity.Player;
import java.time.Duration;
import java.util.*;

/** Texte littéral : aucun parseur de balises ou de codes de couleur. */
final class Announcements {
    private final FKAmis plugin;
    Announcements(FKAmis plugin) { this.plugin=plugin; }
    static String validate(String message) {
        String text=message.strip();
        int length=text.codePointCount(0,text.length());
        if(length<1 || length>240) throw new IllegalArgumentException("Annonce : entre 1 et 240 caractères.");
        if(text.codePoints().anyMatch(c->Character.isISOControl(c) || Character.getType(c)==Character.FORMAT || c=='§')
                || text.matches("(?s).*&[0-9a-fk-orxA-FK-ORX].*"))
            throw new IllegalArgumentException("Annonce : texte simple requis, sans codes de formatage ni caractères de contrôle.");
        return text;
    }
    static String subtitle(String text) {
        return text.codePointCount(0,text.length())<=80 ? text : text.substring(0,text.offsetByCodePoints(0,79))+"…";
    }
    void command(CommandSender sender,String[] args) {
        if(!plugin.mayAdmin(sender)) throw new IllegalArgumentException("Annonce réservée à l'arbitre UUID et à la console.");
        send(sender,String.join(" ",Arrays.copyOfRange(args,1,args.length)),Bukkit.getOnlinePlayers());
    }
    void send(CommandSender sender,String message,Collection<? extends Player> players) {
        if(!plugin.mayAdmin(sender)) throw new IllegalArgumentException("Annonce réservée à l'arbitre UUID et à la console.");
        String text=validate(message);
        Component chat=Component.text("[FALLEN KINGDOM] ",NamedTextColor.GOLD).append(Component.text(text,NamedTextColor.YELLOW));
        Title title=Title.title(Component.text("ANNONCE IMPORTANTE",NamedTextColor.GOLD),Component.text(subtitle(text),NamedTextColor.YELLOW),
                Title.Times.times(Duration.ofMillis(400),Duration.ofSeconds(5),Duration.ofMillis(800)));
        for(Player player:players) { player.sendMessage(chat); player.showTitle(title); player.playSound(player.getLocation(),Sound.BLOCK_NOTE_BLOCK_BELL,SoundCategory.MASTER,.65f,1f); }
        plugin.administrators.audit(sender instanceof Player p?p.getUniqueId():new UUID(0,0),"ANNONCE "+text);
        sender.sendMessage("§aAnnonce envoyée ("+players.size()+" destinataire(s)).");
    }
}
