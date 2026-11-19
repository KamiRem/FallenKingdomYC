import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import org.yaml.snakeyaml.Yaml;
import org.yaml.snakeyaml.LoaderOptions;
import org.yaml.snakeyaml.constructor.SafeConstructor;

/** Lecture seule : pas de serveur, pas de construction de types Java depuis YAML. */
class BackupYamlCheck {
    public static void main(String[] args) throws Exception {
        Path root=Path.of(args[0]);int count=0;Map<?,?> state=null;
        var options=new LoaderOptions();options.setCodePointLimit(16*1024*1024);
        var yaml=new Yaml(new SafeConstructor(options));
        try(var paths=Files.walk(root)) {
            for(Path path:paths.filter(Files::isRegularFile).toList()) {
                if(!(path.toString().endsWith(".yml")||path.toString().endsWith(".yaml")))continue;
                Object value=yaml.load(Files.readString(path,StandardCharsets.UTF_8));
                if(value!=null&&!(value instanceof Map<?,?>))throw new IllegalArgumentException("Root YAML invalide");
                if(path.equals(root.resolve("plugins/FKAmis/state.yml")))state=(Map<?,?>)value;
                count++;
            }
        }
        if(state==null||!Integer.valueOf(1).equals(state.get("schema"))||!(state.get("native") instanceof Map<?,?>)||!(state.get("spawns") instanceof Map<?,?> spawns)||spawns.size()!=4)
            throw new IllegalArgumentException("État de partie incomplet");
        System.out.println("{\"yamlFiles\":"+count+",\"gameStateSchema\":1,\"teamSpawns\":4}");
    }
}
