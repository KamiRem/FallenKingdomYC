package fr.fkamis;

import org.bukkit.*;
import org.bukkit.entity.Player;
import java.lang.reflect.*;
import java.net.InetSocketAddress;
import java.util.*;

/** Corps NMS et liste serveur réels, sans canal réseau ni authentification. Test uniquement. */
final class SyntheticPlayer {
    static Object field(Object object,String name)throws Exception{for(Class<?> c=object.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);return f.get(object);}catch(NoSuchFieldException ignored){}throw new NoSuchFieldException(name);}
    static void set(Object object,String name,Object value)throws Exception{for(Class<?> c=object.getClass();c!=null;c=c.getSuperclass())try{Field f=c.getDeclaredField(name);f.setAccessible(true);f.set(object,value);return;}catch(NoSuchFieldException ignored){}throw new NoSuchFieldException(name);}
    static Class<?> type(String name)throws Exception{return Class.forName(name);}
    @SuppressWarnings("unchecked") static Player create(String name,Location at)throws Exception{
        Object server=Bukkit.getServer().getClass().getMethod("getServer").invoke(Bukkit.getServer()),level=at.getWorld().getClass().getMethod("getHandle").invoke(at.getWorld());
        UUID id=UUID.nameUUIDFromBytes(("VNext1Probe:"+name).getBytes(java.nio.charset.StandardCharsets.UTF_8));Object profile=type("com.mojang.authlib.GameProfile").getConstructor(UUID.class,String.class).newInstance(id,name);
        Object info=type("net.minecraft.server.level.ClientInformation").getMethod("createDefault").invoke(null);
        Object body=type("net.minecraft.server.level.ServerPlayer").getConstructor(type("net.minecraft.server.MinecraftServer"),type("net.minecraft.server.level.ServerLevel"),type("com.mojang.authlib.GameProfile"),type("net.minecraft.server.level.ClientInformation")).newInstance(server,level,profile,info);
        Object flow=Enum.valueOf((Class<Enum>)type("net.minecraft.network.protocol.PacketFlow"),"SERVERBOUND"),connection=type("net.minecraft.network.Connection").getConstructor(type("net.minecraft.network.protocol.PacketFlow")).newInstance(flow);
        set(connection,"address",new InetSocketAddress("127.0.0.1",1));Object cookie=type("net.minecraft.server.network.CommonListenerCookie").getMethod("createInitial",type("com.mojang.authlib.GameProfile"),boolean.class).invoke(null,profile,false);
        Object listener=type("net.minecraft.server.network.ServerGamePacketListenerImpl").getConstructor(type("net.minecraft.server.MinecraftServer"),type("net.minecraft.network.Connection"),type("net.minecraft.server.level.ServerPlayer"),type("net.minecraft.server.network.CommonListenerCookie")).newInstance(server,connection,body,cookie);
        set(body,"connection",listener);set(listener,"clientLoadedTimeoutTimer",0);set(listener,"waitingForRespawn",false);
        body.getClass().getMethod("snapTo",double.class,double.class,double.class).invoke(body,at.getX(),at.getY(),at.getZ());level.getClass().getMethod("addNewPlayer",type("net.minecraft.server.level.ServerPlayer")).invoke(level,body);
        Object list=server.getClass().getMethod("getPlayerList").invoke(server);((List<Object>)field(list,"players")).add(body);((Map<UUID,Object>)field(list,"playersByUUID")).put(id,body);((Map<String,Object>)field(list,"playersByName")).put(name.toLowerCase(Locale.ROOT),body);
        Player player=(Player)body.getClass().getMethod("getBukkitEntity").invoke(body);player.setInvulnerable(false);player.setNoDamageTicks(0);return player;
    }
    @SuppressWarnings("unchecked") static void remove(Player player)throws Exception{
        Object server=Bukkit.getServer().getClass().getMethod("getServer").invoke(Bukkit.getServer()),list=server.getClass().getMethod("getPlayerList").invoke(server),body=player.getClass().getMethod("getHandle").invoke(player),level=player.getWorld().getClass().getMethod("getHandle").invoke(player.getWorld());
        ((List<Object>)field(list,"players")).remove(body);((Map<UUID,Object>)field(list,"playersByUUID")).remove(player.getUniqueId());((Map<String,Object>)field(list,"playersByName")).remove(player.getName().toLowerCase(Locale.ROOT));
        Object reason=Enum.valueOf((Class<Enum>)type("net.minecraft.world.entity.Entity$RemovalReason"),"DISCARDED");level.getClass().getMethod("removePlayerImmediately",type("net.minecraft.server.level.ServerPlayer"),type("net.minecraft.world.entity.Entity$RemovalReason")).invoke(level,body,reason);
    }
    @SuppressWarnings({"unchecked","rawtypes"}) static void useOn(Player player,org.bukkit.block.Block block)throws Exception{
        Object body=player.getClass().getMethod("getHandle").invoke(player);
        Object vector=type("net.minecraft.world.phys.Vec3").getConstructor(double.class,double.class,double.class).newInstance(block.getX()+.5,block.getY()+1d,block.getZ()+.5);
        Object direction=Enum.valueOf((Class<Enum>)type("net.minecraft.core.Direction"),"UP"),position=type("net.minecraft.core.BlockPos").getConstructor(int.class,int.class,int.class).newInstance(block.getX(),block.getY(),block.getZ());
        Object hit=type("net.minecraft.world.phys.BlockHitResult").getConstructor(type("net.minecraft.world.phys.Vec3"),type("net.minecraft.core.Direction"),type("net.minecraft.core.BlockPos"),boolean.class).newInstance(vector,direction,position,false);
        Object hand=Enum.valueOf((Class<Enum>)type("net.minecraft.world.InteractionHand"),"MAIN_HAND");Object context=type("net.minecraft.world.item.context.UseOnContext").getConstructor(type("net.minecraft.world.entity.player.Player"),type("net.minecraft.world.InteractionHand"),type("net.minecraft.world.phys.BlockHitResult")).newInstance(body,hand,hit);
        Object item=body.getClass().getMethod("getMainHandItem").invoke(body);item.getClass().getMethod("useOn",type("net.minecraft.world.item.context.UseOnContext")).invoke(item,context);
    }
    static String lastActionBar(Player player)throws Exception{
        Object body=player.getClass().getMethod("getHandle").invoke(player),listener=field(body,"connection"),connection=field(listener,"connection");String text=null;
        for(Object queued:(Iterable<?>)field(connection,"pendingActions")){String found=actionBar(queued,0);if(found!=null)text=found;}return text;
    }
    private static String actionBar(Object object,int depth)throws Exception{
        if(object==null||depth>3)return null;
        if(object.getClass().getSimpleName().equals("ClientboundSetActionBarTextPacket")){Object component=object.getClass().getMethod("text").invoke(object);return (String)type("net.minecraft.network.chat.Component").getMethod("getString").invoke(component);}
        if(!object.getClass().getName().startsWith("net.minecraft.network.Connection"))return null;
        for(Field field:object.getClass().getDeclaredFields()){if(java.lang.reflect.Modifier.isStatic(field.getModifiers()))continue;field.setAccessible(true);String text=actionBar(field.get(object),depth+1);if(text!=null)return text;}return null;
    }
}
