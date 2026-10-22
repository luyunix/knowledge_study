"""Executable explanatory models; not binary-compatible upstream implementations."""
from bisect import bisect_left
import math
from expert_models import ndcg, read_view_visible, point_in_time, rrf


class DeliveredFrontier:
    """One partition: offsets actually delivered, not all consecutive integers."""
    def __init__(self, start):
        self.scanned_next = start
        self.pending = []
        self.done = set()

    def delivered(self, offsets, scanned_next):
        if offsets != sorted(set(offsets)) or scanned_next < self.scanned_next:
            raise ValueError("invalid delivery order")
        if any(o < self.scanned_next or o >= scanned_next for o in offsets):
            raise ValueError("offset outside scanned range")
        self.pending.extend(offsets)
        self.scanned_next = scanned_next

    def complete(self, offset):
        if offset not in self.pending:
            raise ValueError("not an in-flight delivered record")
        self.done.add(offset)
        while self.pending and self.pending[0] in self.done:
            self.done.remove(self.pending.pop(0))

    @property
    def next_offset(self):
        return self.pending[0] if self.pending else self.scanned_next


class VersionFence:
    def __init__(self):
        self.floor = 0
        self.value = None

    def invalidate(self, version):
        self.floor = max(self.floor, version)
        if self.value and self.value[0] < self.floor:
            self.value = None

    def fill(self, version, value):
        if version < self.floor or self.value and version < self.value[0]:
            return False
        if self.value and version == self.value[0] and value != self.value[1]:
            raise ValueError("same version with conflicting content")
        self.value = (version, value)
        return True


def reinsert_probe_cluster(table, stale):
    """Teaching open-addressing table. Entries are (name, home), not real ThreadLocals."""
    size = len(table)
    table[stale] = None
    cursor = (stale + 1) % size
    while table[cursor] is not None:
        entry = table[cursor]
        table[cursor] = None
        target = entry[1]
        while table[target] is not None:
            target = (target + 1) % size
        table[target] = entry
        cursor = (cursor + 1) % size


def intersection(a, b):
    i = j = 0
    result, trace = [], []
    while i < len(a) and j < len(b):
        if a[i] < b[j]:
            i = bisect_left(a, b[j], i + 1)
        elif b[j] < a[i]:
            j = bisect_left(b, a[i], j + 1)
        else:
            result.append(a[i]); i += 1; j += 1
        trace.append((i, j))
    return result, trace


def pfor_fixture(values, bits=2):
    """Patch semantics only; body byte layout is deliberately not Lucene ForUtil."""
    mask = (1 << bits) - 1
    patches = [(i, value >> bits) for i, value in enumerate(values) if value > mask]
    if len(values) != 128 or len(patches) > 7 or any(v > 255 for _, v in patches):
        raise ValueError("fixture outside header/patch range")
    packed = sum((v & mask) << (i * bits) for i, v in enumerate(values))
    body = packed.to_bytes(128 * bits // 8, "little")
    token = len(patches) << 5 | bits
    raw = bytes([token]) + body + bytes(x for pair in patches for x in pair)
    integer = int.from_bytes(body, "little")
    decoded = [(integer >> (i * bits)) & mask for i in range(128)]
    for i, high in patches:
        decoded[i] |= high << bits
    return raw, decoded


def accepted_evaluation(events, release):
    ready, verified = False, False
    for event, actual in events:
        if event == "ready":
            ready = actual == release
            verified = False
        elif event == "verify":
            verified = ready and actual == release
        elif event == "evaluate":
            return verified and actual == release
    return False


def main():
    table = [None] * 8
    table[6], table[7], table[0] = ("A", 6), ("B", 6), ("C", 7)
    reinsert_probe_cluster(table, 6)
    assert table[6:8] == [("B", 6), ("C", 7)] and table[0] is None
    print("Open-addressed stale removal preserves the probe cluster")

    old_span, rank0, rank_i = 2, 2, 1
    new_right = old_span - (rank0 - rank_i)
    new_left = rank0 - rank_i + 1
    assert (new_left, new_right) == (2, 1)
    assert new_left + new_right == old_span + 1
    print("Skip-list span split: A->X=2, X->C=1; split spans sum to old span + 1")

    fence = VersionFence()
    fence.invalidate(2)
    assert not fence.fill(1, "stale") and fence.fill(2, "current")
    fence.invalidate(3); fence.invalidate(2)
    assert fence.floor == 3 and not fence.fill(2, "late")
    print("A persistent version floor rejects stale fill and out-of-order invalidation")

    versions = [(65, "C"), (50, "B"), (30, "A")]
    visible = next(value for tx, value in versions
                   if read_view_visible(tx, {40, 50}, 40, 60, 55))
    assert visible == "A"
    print("ReadView walks C -> B -> A and selects A")

    frontier = DeliveredFrontier(10)
    frontier.delivered([10, 12, 15], 16)
    frontier.complete(12); frontier.complete(15)
    assert frontier.next_offset == 10
    frontier.complete(10)
    assert frontier.next_offset == 16
    print("Delivered offsets 10,12,15: out-of-order completion waits for 10, not missing 11")

    snapshot, replay = set(range(100)), set(range(100, 150))
    assert snapshot | replay == set(range(150))
    assert (snapshot - {90}) | replay != set(range(150))
    print("Snapshot/stream boundary covers every event; a missing snapshot event is detected")

    outputs = {prefix + suffix: base + tail
               for prefix, base in [("a", 5), ("d", 9)]
               for suffix, tail in [("b", 0), ("c", 2)]}
    assert outputs == {"ab": 5, "ac": 7, "db": 9, "dc": 11}
    found, trace = intersection([3, 7, 18, 30], [7, 20, 30])
    assert found == [7, 30]
    values = [1] * 128; values[42] = 1000
    raw, decoded = pfor_fixture(values)
    assert raw[0] == 34 and len(raw) == 35 and decoded == values
    print("FST residual outputs, monotonic intersection and 35-byte patch fixture verified")

    idf = math.log(1 + (1000 - 10 + .5) / (10 + .5))
    score = lambda tf, dl: idf * tf / (tf + 1.2 * (.25 + .75 * dl / 100))
    assert 3.25 < score(3, 100) < 3.26 and 2.68 < score(3, 200) < 2.69
    assert score(2, 100) - score(1, 100) > score(11, 100) - score(10, 100)
    print("BM25 explanatory scores:", score(3, 100), score(3, 200))

    rows = [{"event": 955, "available": 1005}, {"event": 950, "available": 952}]
    assert point_in_time(rows, 1000)["event"] == 950
    assert len({"A", "B", "C"} & {"A", "C", "D", "E"}) / 3 == 2 / 3
    assert ndcg([2, 0], 2) == 1
    assert ndcg([2, 0], 2, ideal_labels=[3, 2, 0]) < .34
    assert .73 < ndcg([2, 0, 3], 3, ideal_labels=[3, 2, 0]) < .732
    assert rrf([["A", "B"], ["B", "C"]])[0][0] == "B"
    print("Point-in-time, retention and complete-universe NDCG checks passed")

    assert not accepted_evaluation([("ready", "r1"), ("verify", "r2"), ("evaluate", "r2")], "r2")
    assert not accepted_evaluation([("ready", "r2"), ("evaluate", "r2")], "r2")
    assert accepted_evaluation([("ready", "r2"), ("verify", "r2"), ("evaluate", "r2")], "r2")
    print("Outcome acceptance requires ready -> verified release -> evaluation")
    print("All explanatory models passed; no distributed server was exercised")


if __name__ == "__main__":
    main()
