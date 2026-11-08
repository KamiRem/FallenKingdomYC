package fr.fkamis;

import com.google.gson.Gson;
import org.bukkit.*;
import org.bukkit.attribute.Attribute;
import org.bukkit.entity.*;
import org.bukkit.event.*;
import org.bukkit.event.entity.*;
import org.bukkit.projectiles.ProjectileSource;
import java.util.*;

/** Observation seulement : n'annule, ne réautorise et n'inflige jamais aucun dégât. */
final class DamageDiagnostics implements Listener {
    private final FKAmis plugin;private final Gson gson=new Gson();
    private record Trace(long id,double health){}
    private final IdentityHashMap<Event,Trace> traces=new IdentityHashMap<>();
    private long serial,window,lastMobWindow;private int emitted,mobEmitted;
    DamageDiagnostics(FKAmis plugin){this.plugin=plugin;}
    private boolean enabled(){return plugin.getConfig().getBoolean("damage-debug",false);}
    private boolean budget(){long second=System.nanoTime()/1_000_000_000L;if(second!=window){window=second;emitted=0;}return emitted++<16;}
    private Trace begin(Event event,Entity victim){
        if(!enabled())return null;Trace known=traces.get(event);if(known!=null)return known;
        if(!budget())return null;Trace trace=new Trace(++serial,victim instanceof LivingEntity living?living.getHealth():-1);traces.put(event,trace);
        Bukkit.getScheduler().runTask(plugin,()->traces.remove(event));return trace;
    }
    void damage(EntityDamageEvent event,String phase) {
        if(!enabled() || !(event.getEntity() instanceof Player victim))return;
        Trace trace=traces.get(event);if(trace==null && phase.equals("LOWEST"))trace=begin(event,victim);if(trace==null)return;
        Map<String,Object> row=victim(victim);row.put("id",trace.id);row.put("phase",phase);row.put("cause",event.getCause().name());
        row.put("cancelled",event.isCancelled());row.put("initialDamage",event.getOriginalDamage(EntityDamageEvent.DamageModifier.BASE));row.put("damage",event.getDamage());row.put("finalDamage",event.getFinalDamage());
        row.put("damageType",event.getDamageSource().getDamageType().getKey().toString());row.put("direct",entity(event.getDamageSource().getDirectEntity()));row.put("causing",entity(event.getDamageSource().getCausingEntity()));
        Entity direct=event instanceof EntityDamageByEntityEvent by?by.getDamager():event.getDamageSource().getDirectEntity();
        row.put("projectile",entity(direct));row.put("shooter",direct instanceof Projectile p?source(p.getShooter()):"aucun");
        row.put("playerAttribution",Objects.toString(plugin.damageAttribution.damageOwner(event),"aucune"));log("DAMAGE",row);
    }
    private Map<String,Object> victim(Player player){
        Map<String,Object> row=new LinkedHashMap<>();row.put("victimType",player.getType().name());row.put("victimUuid",player.getUniqueId().toString());
        row.put("gamemode",player.getGameMode().name());row.put("team",Objects.toString(plugin.roster.get(player.getUniqueId()),"aucune"));
        row.put("administrator",plugin.isAdministrator(player));row.put("eliminated",plugin.eliminated(player));row.put("participant",plugin.activeParticipant(player));
        row.put("health",player.getHealth());row.put("absorption",player.getAbsorptionAmount());row.put("invulnerable",player.isInvulnerable());
        row.put("noDamageTicks",player.getNoDamageTicks());row.put("maximumNoDamageTicks",player.getMaximumNoDamageTicks());
        var max=player.getAttribute(Attribute.MAX_HEALTH);row.put("maxHealth",max==null?"inconnu":max.getValue());
        row.put("day",plugin.state.day);row.put("paused",plugin.state.paused);row.put("running",plugin.state.running());return row;
    }
    private String entity(Entity entity){return entity==null?"aucune":entity.getType()+":"+entity.getUniqueId();}
    private String source(ProjectileSource source){return source instanceof Entity entity?entity(entity):source==null?"aucune":source.getClass().getSimpleName();}
    private void log(String kind,Map<String,Object> row){plugin.getLogger().info("[FK-DIAG "+kind+"] "+gson.toJson(row));}
    @EventHandler(priority=EventPriority.LOWEST) public void before(EntityDamageEvent event){damage(event,"LOWEST");}
    @EventHandler(priority=EventPriority.MONITOR) public void after(EntityDamageEvent event){
        damage(event,"MONITOR_OBSERVED");Trace trace=traces.get(event);
        if(trace==null||!(event.getEntity() instanceof Player player))return;
        Bukkit.getScheduler().runTask(plugin,()->{
            Map<String,Object> row=new LinkedHashMap<>();row.put("id",trace.id);row.put("phase","AFTER_DISPATCH_NEXT_TICK");row.put("cancelledFinal",event.isCancelled());row.put("healthBefore",trace.health);
            row.put("healthAfter",player.isValid()||player.isDead()?player.getHealth():"indisponible");row.put("dead",player.isDead());log("HEALTH",row);
        });
    }
    private void projectile(Event event,Projectile projectile,Entity victim,String phase){
        if(!enabled())return;Trace trace=traces.get(event);if(trace==null&&phase.equals("LOWEST"))trace=begin(event,victim);
        if(trace==null)return;Map<String,Object> row=new LinkedHashMap<>();row.put("id",trace.id);row.put("phase",phase);row.put("event",event.getEventName());
        row.put("projectile",entity(projectile));row.put("shooter",source(projectile.getShooter()));row.put("cancelled",event instanceof Cancellable c&&c.isCancelled());
        if(victim instanceof Player player)row.putAll(victim(player));log("PROJECTILE",row);
    }
    @EventHandler(priority=EventPriority.LOWEST) public void launchBefore(ProjectileLaunchEvent event){projectile(event,event.getEntity(),null,"LOWEST");}
    @EventHandler(priority=EventPriority.MONITOR) public void launchAfter(ProjectileLaunchEvent event){projectile(event,event.getEntity(),null,"MONITOR_OBSERVED");}
    @EventHandler(priority=EventPriority.LOWEST) public void hitBefore(ProjectileHitEvent event){projectile(event,event.getEntity(),event.getHitEntity(),"LOWEST");}
    @EventHandler(priority=EventPriority.MONITOR) public void hitAfter(ProjectileHitEvent event){projectile(event,event.getEntity(),event.getHitEntity(),"MONITOR_OBSERVED");}
    @EventHandler(priority=EventPriority.MONITOR) public void bow(EntityShootBowEvent event){
        if(!enabled()||!budget())return;log("SHOOT",Map.of("shooter",entity(event.getEntity()),"projectile",entity(event.getProjectile()),"cancelled",event.isCancelled(),"force",event.getForce()));
    }
    @EventHandler(priority=EventPriority.MONITOR) public void target(EntityTargetLivingEntityEvent event){
        if(!enabled()||!(event.getEntity() instanceof AbstractSkeleton)||!budget())return;
        log("TARGET",Map.of("shooter",entity(event.getEntity()),"target",entity(event.getTarget()),"reason",event.getReason().name(),"cancelled",event.isCancelled()));
    }
    void equipment(LivingEntity entity,boolean changed){
        if(!enabled()||!(entity instanceof AbstractSkeleton skeleton))return;long bucket=System.nanoTime()/5_000_000_000L;
        if(bucket!=lastMobWindow){lastMobWindow=bucket;mobEmitted=0;}if(mobEmitted++>=8)return;
        log("MOB",Map.of("shooter",entity(entity),"ai",skeleton.hasAI(),"target",entity(skeleton.getTarget()),
                "hand",skeleton.getEquipment().getItemInMainHand().getType().name(),"usingItem",skeleton.hasActiveItem(),
                "useTicks",skeleton.getActiveItemUsedTime(),"equipmentChanged",changed));
    }
    void describeHandlers(){
        if(!enabled())return;
        for(HandlerList list:List.of(EntityDamageEvent.getHandlerList(),ProjectileLaunchEvent.getHandlerList(),ProjectileHitEvent.getHandlerList(),EntityShootBowEvent.getHandlerList()))
            for(var handler:list.getRegisteredListeners())plugin.getLogger().info("[FK-DIAG HANDLER] plugin="+handler.getPlugin().getName()+" version="+handler.getPlugin().getDescription().getVersion()+" listener="+handler.getListener().getClass().getName()+" priority="+handler.getPriority()+" ignoreCancelled="+handler.isIgnoringCancelled());
    }
}
