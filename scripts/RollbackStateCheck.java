import java.nio.file.*;
import java.util.*;
import java.math.BigDecimal;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.constructor.SafeConstructor;

/** Compare uniquement l'état historique ; aucune construction de types Java YAML. */
class RollbackStateCheck {
    static boolean same(Object a,Object b) {
        if(a instanceof Number x && b instanceof Number y)return new BigDecimal(x.toString()).compareTo(new BigDecimal(y.toString()))==0;
        if(a instanceof Map<?,?> x && b instanceof Map<?,?> y) {
            if(!x.keySet().equals(y.keySet()))return false;
            return x.keySet().stream().allMatch(k->same(x.get(k),y.get(k)));
        }
        if(a instanceof List<?> x && b instanceof List<?> y) {
            if(x.size()!=y.size())return false;for(int i=0;i<x.size();i++)if(!same(x.get(i),y.get(i)))return false;return true;
        }
        return Objects.equals(a,b);
    }
    static Object optional(Object value){return value==null?Map.of():value;}
    public static void main(String[] args)throws Exception {
        var options=new LoaderOptions();options.setCodePointLimit(16*1024*1024);var yaml=new Yaml(new SafeConstructor(options));
        Map<?,?> a=yaml.load(Files.readString(Path.of(args[0]))),b=yaml.load(Files.readString(Path.of(args[1])));
        if(!same(a.get("schema"),1)||!same(b.get("schema"),1))throw new IllegalStateException("Schéma historique inconnu");
        for(String key:List.of("schema","day","started","end-open","winner","eliminated","validated","terrain-validated","spawns"))
            if(!same(a.get(key),b.get(key)))throw new IllegalStateException("Historique modifié : "+key);
        for(String key:List.of("roster","roster-names","objectives"))
            if(!same(optional(a.get(key)),optional(b.get(key))))throw new IllegalStateException("Historique modifié : "+key);
        Map<?,?> an=(Map<?,?>)a.get("native"),bn=(Map<?,?>)b.get("native");
        if(!same(an.get("TeamManager"),bn.get("TeamManager")))throw new IllegalStateException("Équipes ou territoires modifiés");
        System.out.println("{\"historicalStatePreserved\":true,\"nativeTeamsAndTerritoriesPreserved\":true,\"spawnsAndObjectivesPreserved\":true}");
    }
}
