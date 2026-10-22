import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Set;
import java.util.concurrent.locks.ReentrantLock;

/** Strict global LRU, no LinkedHashMap. Null keys/values are rejected. */
public final class HandwrittenLru<K, V> {
    private static final class Node<K, V> {
        final K key;
        V value;
        Node<K, V> prev, next;
        Node(K key, V value) { this.key = key; this.value = value; }
    }
    private final int capacity;
    private final Map<K, Node<K, V>> index = new HashMap<>();
    private final Node<K, V> head = new Node<>(null, null);
    private final Node<K, V> tail = new Node<>(null, null);
    private final ReentrantLock lock = new ReentrantLock();

    public HandwrittenLru(int capacity) {
        if (capacity < 0) throw new IllegalArgumentException("negative capacity");
        this.capacity = capacity;
        head.next = tail; tail.prev = head;
    }

    public V get(K key) {
        Objects.requireNonNull(key);
        lock.lock();
        try {
            Node<K, V> node = index.get(key);
            if (node == null) return null;
            unlink(node); addFirst(node);
            return node.value;
        } finally { lock.unlock(); }
    }

    public void put(K key, V value) {
        Objects.requireNonNull(key); Objects.requireNonNull(value);
        lock.lock();
        try {
            Node<K, V> node = index.get(key);
            if (node != null) {
                node.value = value;
                unlink(node); addFirst(node);
                return;
            }
            if (capacity == 0) return;
            Node<K, V> created = new Node<>(key, value);
            index.put(key, created);
            addFirst(created);
            if (index.size() > capacity) {
                Node<K, V> victim = tail.prev;
                unlink(victim);
                index.remove(victim.key);
            }
        } finally { lock.unlock(); }
    }

    private void unlink(Node<K, V> node) {
        node.prev.next = node.next;
        node.next.prev = node.prev;
        node.prev = node.next = null;
    }

    private void addFirst(Node<K, V> node) {
        node.prev = head; node.next = head.next;
        head.next.prev = node; head.next = node;
    }

    public List<K> keysMostRecentFirst() {
        lock.lock();
        try {
            List<K> keys = new ArrayList<>();
            for (Node<K, V> n = head.next; n != tail; n = n.next) keys.add(n.key);
            return keys;
        } finally { lock.unlock(); }
    }

    /** Debug-only O(n) check. Never call on every operation in a throughput benchmark. */
    public void checkInvariants() {
        lock.lock();
        try {
            if (head.prev != null || tail.next != null || head.next == null || tail.prev == null)
                throw new AssertionError("sentinels");
            Set<Node<K, V>> seen = new HashSet<>();
            Node<K, V> previous = head;
            for (Node<K, V> n = head.next; n != tail; n = n.next) {
                if (n == null || !seen.add(n) || n.prev != previous || index.get(n.key) != n)
                    throw new AssertionError("broken index/list relation");
                previous = n;
            }
            if (tail.prev != previous || previous.next != tail || seen.size() != index.size()
                    || index.size() > capacity) throw new AssertionError("size/tail");
        } finally { lock.unlock(); }
    }
}
