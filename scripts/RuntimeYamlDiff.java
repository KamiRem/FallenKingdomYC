import java.nio.file.*;
import java.util.*;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.constructor.SafeConstructor;

/** Diff des chemins uniquement : aucune valeur de configuration dans les journaux. */
class RuntimeYamlDiff {
    static void diff(String file,String path,Object before,Object after) {
        if(before instanceof Map<?,?> a && after instanceof Map<?,?> b) {
            for(Object key:a.keySet()) {
                String next=path+"/"+key;
                if(!b.containsKey(key))System.out.println(file+"\tremoved\t"+next);
                else diff(file,next,a.get(key),b.get(key));
            }
            for(Object key:b.keySet())if(!a.containsKey(key))System.out.println(file+"\tadded\t"+path+"/"+key);
        } else if(!Objects.equals(before,after))System.out.println(file+"\tchanged\t"+path);
    }
    public static void main(String[] args)throws Exception {
        Path before=Path.of(args[0]),after=Path.of(args[1]);var options=new LoaderOptions();options.setCodePointLimit(16*1024*1024);var yaml=new Yaml(new SafeConstructor(options));
        try(var paths=Files.walk(before)) {
            for(Path p:paths.filter(Files::isRegularFile).filter(p->p.toString().endsWith(".yml")).toList()) {
                Path relative=before.relativize(p),q=after.resolve(relative);
                if(!Files.exists(q))throw new IllegalStateException("Configuration YAML supprimée");
                if(!Arrays.equals(Files.readAllBytes(p),Files.readAllBytes(q)))diff(relative.toString(),"",yaml.load(Files.readString(p)),yaml.load(Files.readString(q)));
            }
        }
    }
}
