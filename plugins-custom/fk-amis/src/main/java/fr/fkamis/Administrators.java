package fr.fkamis;

import org.bukkit.*;
import org.bukkit.command.*;
import org.bukkit.configuration.file.YamlConfiguration;
import org.bukkit.entity.Player;
import org.bukkit.event.*;
import org.bukkit.event.block.*;
import org.bukkit.event.player.*;
import org.bukkit.permissions.PermissionAttachment;

import java.io.IOException;
import java.nio.channels.FileChannel;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.time.Instant;
import java.util.*;

/** Autorisations UUID hors state.yml ; seul l'accès console peut les modifier. */
final class Administrators implements Listener {
    private final FKAmis plugin;
    private final Path file;
    private final Set<UUID> ids = new HashSet<>();
    private final Map<UUID, PermissionAttachment> attachments = new HashMap<>();
    private final Map<UUID, Permit> permits = new HashMap<>();
    private record Permit(Location block, long expires) {}
    Administrators(FKAmis plugin) throws Exception {
        this.plugin = plugin; file = plugin.getDataFolder().toPath().resolve("admins.yml");
        if (Files.exists(file)) {
            var yaml = new YamlConfiguration(); yaml.load(file.toFile());
            if (yaml.getInt("schema") != 1) throw new IllegalStateException("Format admins.yml invalide.");
            for (String id : yaml.getStringList("administrators")) ids.add(UUID.fromString(id));
        } else save();
    }
    boolean contains(UUID id) { return id != null && ids.contains(id); }
    boolean contains(Player player) { return contains(player.getUniqueId()); }
    Set<UUID> ids() { return Set.copyOf(ids); }
    private void save() throws Exception {
        var yaml = new YamlConfiguration(); yaml.set("schema",1);
        yaml.set("administrators",ids.stream().map(UUID::toString).sorted().toList());
        Path temporary = file.resolveSibling("admins.yml.new");
        Files.writeString(temporary,yaml.saveToString(),StandardCharsets.UTF_8);
        try (var channel=FileChannel.open(temporary,StandardOpenOption.WRITE)) { channel.force(true); }
        Files.move(temporary,file,StandardCopyOption.ATOMIC_MOVE,StandardCopyOption.REPLACE_EXISTING);
    }
    void attach(Player player) {
        detach(player);
        if (!contains(player)) return;
        var attachment = player.addAttachment(plugin);
        Bukkit.getPluginManager().getPermissions().forEach(permission -> attachment.setPermission(permission.getName(),true));
        for (String permission : List.of("fkamis.admin","fallenkingdom.admin","minecraft.command","bukkit.command")) attachment.setPermission(permission,true);
        attachments.put(player.getUniqueId(),attachment);
    }
    void detach(Player player) {
        PermissionAttachment old=attachments.remove(player.getUniqueId());
        if (old!=null) old.remove();
        permits.remove(player.getUniqueId());
    }
    void close() { for (Player player:Bukkit.getOnlinePlayers()) detach(player); permits.clear(); }
    void audit(UUID id,String action) {
        String line=Instant.now()+" | "+id+" | "+action.replace('\n',' ').replace('\r',' ');
        plugin.getLogger().info("[Arbitrage] "+line);
        try { Files.writeString(plugin.getDataFolder().toPath().resolve("admin-audit.log"),line+"\n",StandardCharsets.UTF_8,StandardOpenOption.CREATE,StandardOpenOption.APPEND); }
        catch (IOException error) { throw new IllegalStateException("Journal d'arbitrage indisponible.",error); }
    }
    boolean sensitive(Player player,Location location) {
        Permit permit=permits.get(player.getUniqueId());
        return contains(player)&&permit!=null&&System.nanoTime()<permit.expires&&FKAmis.sameBlock(permit.block,location)&&!plugin.state.running();
    }
    void command(CommandSender sender,String[] args) throws Exception {
        if (!(sender instanceof ConsoleCommandSender)) throw new IllegalArgumentException("Gestion du rôle réservée à la console du serveur.");
        if (args.length==2&&args[1].equals("list")) { sender.sendMessage("Administrateurs UUID : "+ids); return; }
        if (args.length==3&&args[1].equals("uuid")) {
            Player player=Bukkit.getPlayerExact(args[2]);
            if (player==null) throw new IllegalArgumentException("Compte officiel connecté requis.");
            sender.sendMessage(player.getName()+" : "+player.getUniqueId()); return;
        }
        if (args.length<3) throw new IllegalArgumentException("Console : fka admin <uuid pseudo|list|grant UUID [confirm]|revoke UUID [confirm]|unlock UUID x y z confirm>");
        UUID id=UUID.fromString(args[2]);
        if (args[1].equals("unlock")) {
            if (args.length!=7||!args[6].equals("confirm")||plugin.state.running()||!contains(id))
                throw new IllegalArgumentException("En pause : admin unlock UUID x y z confirm ; une action sensible, 60 secondes.");
            Player player=Objects.requireNonNull(Bukkit.getPlayer(id),"Administrateur connecté requis.");
            Location target=new Location(player.getWorld(),Integer.parseInt(args[3]),Integer.parseInt(args[4]),Integer.parseInt(args[5]));
            audit(id,"AUTORISATION SENSIBLE "+target.getWorld().getName()+" "+target.getBlockX()+" "+target.getBlockY()+" "+target.getBlockZ());
            permits.put(id,new Permit(target,System.nanoTime()+60_000_000_000L)); sender.sendMessage("Une intervention ciblée autorisée pour 60 secondes ; remettre l'objectif/site en état avant reprise."); return;
        }
        if (!Set.of("grant","revoke").contains(args[1])) throw new IllegalArgumentException("Action administrateur inconnue.");
        if (args.length==3) { sender.sendMessage("Confirmer explicitement : fka admin "+args[1]+" "+id+" confirm"); return; }
        if (args.length!=4||!args[3].equals("confirm")) throw new IllegalArgumentException("Confirmation exacte requise.");
        if (args[1].equals("grant")&&plugin.roster.containsKey(id)) throw new IllegalArgumentException("Retirer ce participant de son équipe avant de lui donner le rôle arbitre.");
        audit(id,"CONSOLE "+args[1]);
        Set<UUID> previous=new HashSet<>(ids);
        if (args[1].equals("grant")) ids.add(id); else ids.remove(id);
        try { save(); } catch (Exception error) { ids.clear(); ids.addAll(previous); throw error; }
        permits.remove(id);
        Player player=Bukkit.getPlayer(id);
        if (player!=null) { attach(player); plugin.reconcilePlayer(player); }
        sender.sendMessage("Rôle "+args[1]+" enregistré pour "+id+" ; aucune attribution d'équipe.");
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void broken(BlockBreakEvent e) { changed(e.getPlayer(),e.getBlock().getLocation(),"DESTRUCTION"); }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void placed(BlockPlaceEvent e) { changed(e.getPlayer(),e.getBlock().getLocation(),"CONSTRUCTION"); }
    private void changed(Player p,Location at,String action) {
        if (!contains(p)) return;
        if (sensitive(p,at)) permits.remove(p.getUniqueId());
        audit(p.getUniqueId(),action+" "+at.getWorld().getName()+" "+at.getBlockX()+" "+at.getBlockY()+" "+at.getBlockZ());
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void teleported(PlayerTeleportEvent e) {
        if (contains(e.getPlayer())) audit(e.getPlayer().getUniqueId(),"TELEPORTATION "+e.getCause());
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void interacted(PlayerInteractEvent e) {
        if (contains(e.getPlayer())&&e.getClickedBlock()!=null) audit(e.getPlayer().getUniqueId(),"INTERACTION "+e.getClickedBlock().getType());
    }
    @EventHandler(priority=EventPriority.HIGHEST) public void worldCommands(PlayerCommandPreprocessEvent e) {
        String root=e.getMessage().strip().split("\\s+",2)[0].toLowerCase(Locale.ROOT).replaceFirst("^/","");
        root=root.substring(root.lastIndexOf(':')+1);
        // Ces commandes ne déclenchent pas BlockBreak/Place et pourraient contourner
        // les verrous des objectifs/sites : intervention explicite par console seulement.
        if (Set.of("setblock","fill","clone","place","data","execute").contains(root)) {
            e.setCancelled(true);e.getPlayer().sendMessage("§cModification avancée du monde : utiliser explicitement la console après sauvegarde. Les objectifs/sites restent protégés en jeu.");
        }
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void commands(PlayerCommandPreprocessEvent e) {
        if (contains(e.getPlayer())) audit(e.getPlayer().getUniqueId(),"COMMANDE "+e.getMessage().strip().split("\\s+",2)[0]);
    }
    @EventHandler(priority=EventPriority.MONITOR,ignoreCancelled=true) public void consoleCommands(org.bukkit.event.server.ServerCommandEvent e) {
        String root=e.getCommand().strip().split("\\s+",2)[0].toLowerCase(Locale.ROOT);
        root=root.substring(root.lastIndexOf(':')+1);
        if (Set.of("setblock","fill","clone","place","data","execute","kill","tp","teleport","gamemode","give","gamerule","worldborder").contains(root))
            audit(new UUID(0,0),"CONSOLE commande "+root);
    }
}
