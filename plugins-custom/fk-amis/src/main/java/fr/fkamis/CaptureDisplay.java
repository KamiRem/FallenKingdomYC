package fr.fkamis;

import net.kyori.adventure.bossbar.BossBar;
import net.kyori.adventure.text.Component;
import net.kyori.adventure.text.format.NamedTextColor;
import net.kyori.adventure.title.Title;
import org.bukkit.*;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.entity.PlayerDeathEvent;
import org.bukkit.event.player.*;
import java.time.Duration;
import java.util.*;

/** Vue du CaptureClock existant, sans chronomètre parallèle. */
final class CaptureDisplay implements Listener {
    private static final class Attempt {
        String attacker;BossBar bar;Map<UUID,Player> viewers=new HashMap<>();Set<UUID> contributors=new HashSet<>();
        Attempt(String attacker){this.attacker=attacker;bar=BossBar.bossBar(Component.empty(),0,BossBar.Color.RED,BossBar.Overlay.PROGRESS);}
    }
    private final FKAmis plugin;private final Map<String,Attempt> attempts=new HashMap<>();private final Map<String,Long> alerts=new HashMap<>();
    CaptureDisplay(FKAmis plugin){this.plugin=plugin;}
    void update(String defender,CaptureClock clock,Collection<? extends Player> eligible,boolean contested){
        Attempt old=attempts.get(defender);
        if(clock.attacker.isEmpty()) {
            if(old!=null&&contested)for(Player player:old.viewers.values())player.sendMessage(Component.text("Capture contestée : progression réinitialisée.",NamedTextColor.YELLOW));
            clear(defender);return;
        }
        if(old!=null&&!old.attacker.equals(clock.attacker)){clear(defender);old=null;}
        if(old==null){old=new Attempt(clock.attacker);attempts.put(defender,old);alert(defender);}
        Attempt attempt=old;int seconds=plugin.getConfig().getInt("capture-seconds");
        attempt.bar.name(Component.text("CAPTURE "+defender.toUpperCase(Locale.ROOT)+" — "+(clock.elapsedTicks/20)+" / "+seconds+" secondes",NamedTextColor.RED));
        attempt.bar.progress(Math.clamp(clock.elapsedTicks/(float)(seconds*20),0f,1f));
        Set<UUID> showing=new HashSet<>();
        for(Player player:eligible)if(clock.attacker.equals(plugin.roster.get(player.getUniqueId()))) {
            showing.add(player.getUniqueId());attempt.contributors.add(player.getUniqueId());
            if(attempt.viewers.putIfAbsent(player.getUniqueId(),player)==null)player.showBossBar(attempt.bar);
        }
        for(UUID id:new HashSet<>(attempt.viewers.keySet()))if(!showing.contains(id)){attempt.viewers.remove(id).hideBossBar(attempt.bar);}
    }
    private void alert(String defender){
        long now=System.nanoTime();if(alerts.getOrDefault(defender,0L)>now)return;alerts.put(defender,now+10_000_000_000L);
        Component message=Component.text("ALERTE — VOTRE COFFRE EST ATTAQUÉ !",NamedTextColor.RED);
        Title title=Title.title(Component.text("ALERTE",NamedTextColor.RED),Component.text("VOTRE COFFRE EST ATTAQUÉ !",NamedTextColor.GOLD),Title.Times.times(Duration.ofMillis(200),Duration.ofSeconds(3),Duration.ofMillis(500)));
        for(Player player:Bukkit.getOnlinePlayers())if(defender.equals(plugin.roster.get(player.getUniqueId()))&&!plugin.isAdministrator(player)) {
            player.sendMessage(message);player.showTitle(title);player.playSound(player.getLocation(),Sound.BLOCK_BELL_USE,SoundCategory.MASTER,.7f,.8f);
        }
    }
    Set<UUID> contributors(String defender){Attempt attempt=attempts.get(defender);return attempt==null?Set.of():Set.copyOf(attempt.contributors);}
    void clear(String defender){Attempt attempt=attempts.remove(defender);if(attempt!=null)attempt.viewers.values().forEach(player->player.hideBossBar(attempt.bar));}
    void clearAll(){for(String defender:new HashSet<>(attempts.keySet()))clear(defender);}
    void remove(UUID id){for(Attempt attempt:attempts.values()){Player player=attempt.viewers.remove(id);if(player!=null)player.hideBossBar(attempt.bar);}}
    @EventHandler public void death(PlayerDeathEvent event){remove(event.getEntity().getUniqueId());}
    @EventHandler public void quit(PlayerQuitEvent event){remove(event.getPlayer().getUniqueId());}
    @EventHandler public void world(PlayerChangedWorldEvent event){remove(event.getPlayer().getUniqueId());}
}
