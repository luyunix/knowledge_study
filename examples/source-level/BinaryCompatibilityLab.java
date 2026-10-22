import java.lang.reflect.InvocationTargetException;
import java.net.URL;
import java.net.URLClassLoader;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import javax.tools.JavaCompiler;
import javax.tools.ToolProvider;

/** Real class-file linkage experiment; not a Maven integration test. */
public final class BinaryCompatibilityLab {
    private static void compile(Path dir, String name, String source, Path classpath) throws Exception {
        Files.createDirectories(dir);
        Path java = dir.resolve(name + ".java");
        Files.writeString(java, source, StandardCharsets.UTF_8);
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        if (compiler == null) throw new IllegalStateException("Requires a JDK, not just a JRE");
        int result = classpath == null
                ? compiler.run(null, null, null, "--release", "17", "-d", dir.toString(), java.toString())
                : compiler.run(null, null, null, "--release", "17", "-classpath", classpath.toString(),
                    "-d", dir.toString(), java.toString());
        if (result != 0) throw new AssertionError("Compilation failed: " + name);
    }

    private static Object call(Path plugin, Path api) throws Exception {
        try (URLClassLoader loader = new URLClassLoader(
                new URL[] { plugin.toUri().toURL(), api.toUri().toURL() }, ClassLoader.getPlatformClassLoader())) {
            Class<?> type = Class.forName("Plugin", true, loader);
            if (type.getClassLoader() != loader) throw new AssertionError("Unexpected defining loader");
            return type.getMethod("call").invoke(null);
        }
    }

    public static void main(String[] args) throws Exception {
        Path root = Files.createTempDirectory("binary-compat-lab-");
        Path oldApi = root.resolve("api-v1"), newApi = root.resolve("api-v2");
        Path compatible = root.resolve("api-v3"), plugin = root.resolve("plugin");
        compile(oldApi, "Api", "public class Api { public static String label() { return \"v1\"; } }", null);
        compile(plugin, "Plugin", "public class Plugin { public static String call() { return Api.label(); } }", oldApi);
        compile(newApi, "Api", "public class Api { public static String label(int n) { return \"v2\"; } }", null);
        compile(compatible, "Api", "public class Api { public static String label() { return \"v3\"; } "
                + "public static String label(int n) { return \"v3-new\"; } }", null);
        if (!"v1".equals(call(plugin, oldApi))) throw new AssertionError();
        try {
            call(plugin, newApi);
            throw new AssertionError("Expected linkage failure");
        } catch (InvocationTargetException expected) {
            if (!(expected.getCause() instanceof NoSuchMethodError)) throw expected;
            System.out.println("Removed ()String method: actual NoSuchMethodError observed");
        }
        if (!"v3".equals(call(plugin, compatible))) throw new AssertionError();
        System.out.println("Preserved old descriptor: same Plugin.class works without recompilation");
        System.out.println("Isolated test fixtures: " + root);
    }
}
