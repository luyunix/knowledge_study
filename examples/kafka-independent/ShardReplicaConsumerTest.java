import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.TopicPartition;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** In-memory API contract checks only: no broker, disk, replication or crash test. */
public final class ShardReplicaConsumerTest {
    static final TopicPartition P0 = new TopicPartition("product-change", 0);
    static final TopicPartition P2 = new TopicPartition("product-change", 2);

    static final class MemoryIndex implements ShardReplicaConsumer.LocalIndex {
        final Map<TopicPartition, OffsetAndMetadata> checkpoints = new HashMap<>();
        final List<Long> applied = new ArrayList<>();
        final AtomicBoolean running;
        boolean fail;
        MemoryIndex(long next, AtomicBoolean running) {
            checkpoints.put(P0, new OffsetAndMetadata(next));
            this.running = running;
        }
        public Map<TopicPartition, OffsetAndMetadata> recoverNextOffsets() {
            return Map.copyOf(checkpoints);
        }
        public void applyAndCheckpoint(ConsumerRecords<String, String> records,
                                       Map<TopicPartition, OffsetAndMetadata> next) {
            if (fail) throw new IllegalStateException("injected index failure");
            for (var r : records) applied.add(r.offset());
            checkpoints.putAll(next);
            running.set(false);
        }
    }

    static MockConsumer<String, String> mock() {
        var c = new MockConsumer<String, String>("none");
        c.updateBeginningOffsets(Map.of(P0, 0L, P2, 0L));
        c.updateEndOffsets(Map.of(P0, 101L, P2, 51L));
        return c;
    }

    static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }

    static void replica(String id) {
        var running = new AtomicBoolean(true);
        var index = new MemoryIndex(100, running);
        try (var c = mock()) {
            c.schedulePollTask(() -> {
                check(c.assignment().equals(Set.of(P0)), "wrong assigned partitions");
                check(c.position(P0) == 100, "not restored from local checkpoint");
                c.addRecord(new ConsumerRecord<>(P0.topic(), 0, 100, "2", "price=80,version=9"));
            });
            ShardReplicaConsumer.consume(c, List.of(P0), index, running::get);
            check(index.applied.equals(List.of(100L)), "record not applied");
            check(index.checkpoints.get(P0).offset() == 101, "wrong local checkpoint");
            check(c.committed(Set.of(P0)).get(P0).offset() == 101, "wrong Kafka commit");
        }
        check(ShardReplicaConsumer.config("unused:9092", id).get("group.id").equals(id), "group config");
    }

    public static void main(String[] args) {
        replica("product-s0-a");
        replica("product-s0-b");
        var running = new AtomicBoolean(true);
        var index = new MemoryIndex(100, running);
        index.fail = true;
        try (var c = mock()) {
            c.schedulePollTask(() -> c.addRecord(new ConsumerRecord<>(P0.topic(), 0, 100, "2", "v9")));
            try {
                ShardReplicaConsumer.consume(c, List.of(P0), index, running::get);
                throw new AssertionError("failure was swallowed");
            } catch (IllegalStateException expected) {
                check(expected.getMessage().equals("injected index failure"), "unexpected exception");
            }
            check(c.committed(Set.of(P0)).get(P0) == null, "committed after failed write");
        }
        try (var c = mock()) {
            try {
                ShardReplicaConsumer.consume(c, List.of(P2), index, running::get);
                throw new AssertionError("missing checkpoint accepted");
            } catch (IllegalStateException expected) {
                check(expected.getMessage().contains("Missing valid"), "unexpected exception");
            }
        }
        // Even if Kafka's recorded progress leads the recovered index, local state wins.
        try (var c = mock()) {
            c.assign(List.of(P0));
            c.commitSync(Map.of(P0, new OffsetAndMetadata(101)));
            var behind = new MemoryIndex(99, new AtomicBoolean(false));
            ShardReplicaConsumer.consume(c, List.of(P0), behind, () -> false);
            check(c.position(P0) == 99, "Kafka commit incorrectly overrides recovered index");
        }
        System.out.println("PASS: two independent replicas, assigned partition, local seek, next offset, failed write, missing checkpoint, local recovery authority.");
        System.out.println("MockConsumer only; no real Kafka or durable index verification.");
    }
}
