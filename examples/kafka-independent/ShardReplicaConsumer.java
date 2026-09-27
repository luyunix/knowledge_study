import org.apache.kafka.clients.consumer.*;
import org.apache.kafka.common.TopicPartition;
import org.apache.kafka.common.serialization.StringDeserializer;

import java.time.Duration;
import java.util.*;
import java.util.function.BooleanSupplier;

/** Java 17+, kafka-clients 4.1.0. Teaching skeleton, not a storage implementation. */
public final class ShardReplicaConsumer {
    public interface LocalIndex {
        // After recovering the index, return matching NEXT offsets for each partition.
        // A new replica must load a snapshot and its matching boundary first.
        Map<TopicPartition, OffsetAndMetadata> recoverNextOffsets();

        // Apply every record in partition order, idempotently. Persist a recoverable
        // index/checkpoint pair; checkpoints MUST NOT lead recoverable index state.
        // Preserve untouched partitions' checkpoints. Throw on failure; never skip.
        void applyAndCheckpoint(ConsumerRecords<String, String> records,
                                Map<TopicPartition, OffsetAndMetadata> nextOffsets);
    }

    public static Properties config(String brokers, String groupId) {
        if (groupId == null || groupId.isBlank()) {
            throw new IllegalArgumentException("A stable replica groupId is required");
        }
        Properties p = new Properties();
        p.put("bootstrap.servers", brokers);
        p.put("group.id", groupId);
        p.put("key.deserializer", StringDeserializer.class.getName());
        p.put("value.deserializer", StringDeserializer.class.getName());
        p.put("enable.auto.commit", "false");
        p.put("auto.offset.reset", "none");
        p.put("isolation.level", "read_committed");
        p.put("max.poll.records", "500");
        return p;
    }

    public static void run(String brokers, String groupId,
                           List<TopicPartition> partitions,
                           LocalIndex index, BooleanSupplier running) {
        try (KafkaConsumer<String, String> consumer =
                     new KafkaConsumer<>(config(brokers, groupId))) {
            consume(consumer, partitions, index, running);
        }
    }

    // The caller owns this consumer. This entry point also accepts MockConsumer.
    public static void consume(Consumer<String, String> consumer,
                               List<TopicPartition> partitions,
                               LocalIndex index, BooleanSupplier running) {
        if (partitions.isEmpty() || new HashSet<>(partitions).size() != partitions.size()) {
            throw new IllegalArgumentException("Use a nonempty, unique partition list");
        }
        Map<TopicPartition, OffsetAndMetadata> recovered = index.recoverNextOffsets();
        for (TopicPartition tp : partitions) {
            if (recovered.get(tp) == null || recovered.get(tp).offset() < 0) {
                throw new IllegalStateException("Missing valid index checkpoint: " + tp);
            }
        }
        consumer.assign(partitions);
        for (TopicPartition tp : partitions) {
            consumer.seek(tp, recovered.get(tp));
        }
        while (running.getAsBoolean()) {
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofSeconds(1));
            if (records.isEmpty()) continue;

            // Kafka 4.1 supplies the next position and available leader epoch.
            Map<TopicPartition, OffsetAndMetadata> next = Map.copyOf(records.nextOffsets());
            index.applyAndCheckpoint(records, next);
            // Kafka offsets are progress records; recovery above uses the index checkpoint.
            consumer.commitSync(next);
        }
    }
}
