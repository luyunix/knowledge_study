import java.lang.reflect.Field;
import java.net.URL;
import java.net.URLClassLoader;
import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.locks.ReentrantLock;

/** Run with --add-opens java.base/java.util=ALL-UNNAMED. No external libraries. */
public final class ExpertMechanics {
    static void check(boolean ok, String message) {
        if (!ok) throw new AssertionError(message);
    }

    static final class Key {
        final int hash;
        Key(int hash) { this.hash = hash; }
        public int hashCode() { return hash; }
        public boolean equals(Object other) {
            return other instanceof Key && ((Key) other).hash == hash;
        }
    }

    static final class Collision {
        static int comparisons;
        final int id;
        Collision(int id) { this.id = id; }
        public int hashCode() { return 0; }
        public boolean equals(Object other) {
            comparisons++;
            return other instanceof Collision && ((Collision) other).id == id;
        }
    }

    static void hashMap() throws Exception {
        HashMap<Key, Integer> map = new HashMap<>(16);
        for (int i = 0; i < 13; i++) map.put(new Key(3 + 16 * i), i);
        Field field = HashMap.class.getDeclaredField("table");
        field.setAccessible(true);
        Object[] table = (Object[]) field.get(map);
        check(table.length == 32, "expected resize 16 -> 32");
        Field next = Class.forName("java.util.HashMap$Node").getDeclaredField("next");
        next.setAccessible(true);
        List<List<Integer>> values = new ArrayList<>();
        for (int bucket : new int[]{3, 19}) {
            List<Integer> found = new ArrayList<>();
            for (Object node = table[bucket]; node != null; node = next.get(node)) {
                Map.Entry<?, ?> entry = (Map.Entry<?, ?>) node;
                found.add((Integer) entry.getValue());
            }
            values.add(found);
        }
        check(values.get(0).equals(Arrays.asList(0, 2, 4, 6, 8, 10, 12)), "low split");
        check(values.get(1).equals(Arrays.asList(1, 3, 5, 7, 9, 11)), "high split");
        HashMap<Collision, Integer> collisions = new HashMap<>(64);
        for (int i = 0; i < 32; i++) collisions.put(new Collision(i), i);
        Object[] collisionTable = (Object[]) field.get(collisions);
        check(collisionTable[0].getClass().getName().endsWith("TreeNode"), "must treeify");
        Collision.comparisons = 0;
        check(collisions.get(new Collision(-1)) == null, "missing key");
        check(Collision.comparisons >= 32, "unordered equal-hash lookup visits many keys");
        System.out.println("HashMap split=" + values + "; missing-key equality checks=" + Collision.comparisons);
    }

    static final class Lru<K, V> {
        private final int capacity;
        private final ReentrantLock lock = new ReentrantLock();
        private final LinkedHashMap<K, V> values = new LinkedHashMap<>(16, .75f, true);
        Lru(int capacity) {
            if (capacity < 0) throw new IllegalArgumentException("negative capacity");
            this.capacity = capacity;
        }
        V get(K key) {
            lock.lock();
            try { return values.get(key); }
            finally { lock.unlock(); }
        }
        void put(K key, V value) {
            lock.lock();
            try {
                if (capacity == 0) return;
                values.put(key, value);
                if (values.size() > capacity) {
                    Iterator<K> iterator = values.keySet().iterator();
                    iterator.next();
                    iterator.remove();
                }
            } finally { lock.unlock(); }
        }
        int size() {
            lock.lock();
            try { return values.size(); }
            finally { lock.unlock(); }
        }
    }

    static void lru() throws Exception {
        Lru<Integer, Integer> cache = new Lru<>(2);
        cache.put(1, 1); cache.put(2, 2); cache.get(1); cache.put(3, 3);
        check(cache.get(2) == null && cache.get(1) == 1, "access must update LRU");
        cache.put(1, 7); cache.put(4, 4);
        check(cache.get(3) == null && cache.get(1) == 7, "update must update LRU");
        Lru<Integer, Integer> zero = new Lru<>(0);
        zero.put(1, 1); check(zero.size() == 0, "capacity zero");
        Lru<Integer, Integer> shared = new Lru<>(32);
        ExecutorService pool = Executors.newFixedThreadPool(8);
        List<Future<?>> tasks = new ArrayList<>();
        try {
            for (int t = 0; t < 8; t++) {
                final int id = t;
                tasks.add(pool.submit(() -> {
                    for (int i = 0; i < 2000; i++) {
                        shared.put((i + id) % 100, i);
                        shared.get((i * 3 + id) % 100);
                        check(shared.size() <= 32, "capacity invariant");
                    }
                }));
            }
            for (Future<?> task : tasks) task.get();
        } finally { pool.shutdownNow(); }
        System.out.println("LRU order and concurrent capacity checks passed");
    }

    static void threadLocal() throws Exception {
        ExecutorService pool = Executors.newSingleThreadExecutor();
        ThreadLocal<String> local = new ThreadLocal<>();
        try {
            pool.submit(() -> local.set("tenant-A")).get();
            check("tenant-A".equals(pool.submit(local::get).get()), "reused thread retains context");
            pool.submit(() -> {
                try { local.set("tenant-B"); }
                finally { local.remove(); }
            }).get();
            check(pool.submit(local::get).get() == null, "remove clears the entry");
        } finally { pool.shutdownNow(); }
        System.out.println("ThreadLocal cross-task contamination and cleanup reproduced");
    }

    static void threadPool() throws Exception {
        CountDownLatch running = new CountDownLatch(2), finish = new CountDownLatch(1);
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
            1, 2, 30, TimeUnit.SECONDS, new ArrayBlockingQueue<>(1));
        Runnable blocked = () -> {
            running.countDown();
            try { finish.await(); }
            catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        };
        try {
            pool.execute(blocked);       // core worker
            pool.execute(() -> { });     // queue before maximum worker count
            pool.execute(blocked);       // second worker when queue is full
            check(running.await(5, TimeUnit.SECONDS), "workers started");
            boolean rejected = false;
            try { pool.execute(() -> { }); }
            catch (RejectedExecutionException expected) { rejected = true; }
            check(rejected && pool.getPoolSize() == 2 && pool.getQueue().size() == 1,
                  "core -> queue -> maximum -> reject");
        } finally {
            finish.countDown(); pool.shutdown();
            check(pool.awaitTermination(5, TimeUnit.SECONDS), "pool terminates");
        }
        System.out.println("ThreadPoolExecutor admission sequence reproduced");
    }

    static void classIdentity() throws Exception {
        URL root = ExpertMechanics.class.getProtectionDomain().getCodeSource().getLocation();
        ClassLoader parent = ClassLoader.getPlatformClassLoader();
        try (URLClassLoader a = new URLClassLoader(new URL[]{root}, parent);
             URLClassLoader b = new URLClassLoader(new URL[]{root}, parent)) {
            Class<?> left = Class.forName("ExpertPayload", true, a);
            Class<?> right = Class.forName("ExpertPayload", true, b);
            Object instance = right.getDeclaredConstructor().newInstance();
            check(left != right && !left.isInstance(instance), "same name, different identity");
            check(instance instanceof Runnable, "shared parent type remains compatible");
            System.out.println("Class identities differ; shared Runnable contract is compatible");
        }
    }

    static long maxSubarray(int[] values) {
        if (values.length == 0) throw new IllegalArgumentException("nonempty input required");
        long ending = values[0], best = ending;
        for (int i = 1; i < values.length; i++) {
            ending = Math.max(values[i], ending + values[i]);
            best = Math.max(best, ending);
        }
        return best;
    }
    static long brute(int[] values) {
        long best = Long.MIN_VALUE;
        for (int i = 0; i < values.length; i++) {
            long sum = 0;
            for (int j = i; j < values.length; j++) best = Math.max(best, sum += values[j]);
        }
        return best;
    }
    static void arrays(int[] values, int at) {
        if (at == values.length) {
            check(maxSubarray(values) == brute(values), "DP versus enumeration"); return;
        }
        for (int x = -2; x <= 2; x++) { values[at] = x; arrays(values, at + 1); }
    }
    public static void main(String[] args) throws Exception {
        System.out.println("Runtime: " + System.getProperty("java.runtime.version"));
        hashMap(); lru(); threadLocal(); threadPool(); classIdentity();
        for (int n = 1; n <= 7; n++) arrays(new int[n], 0);
        check(maxSubarray(new int[]{Integer.MAX_VALUE, Integer.MAX_VALUE}) == 4294967294L,
              "long accumulation avoids int overflow");
        System.out.println("Kadane exhaustive comparison and overflow checks passed");
    }
}
