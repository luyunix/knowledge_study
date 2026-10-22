"""Small deterministic protocol models. No real broker/database/cluster is used."""
import hashlib
import math


def read_view_visible(txid, active, upper, lower, creator):
    if txid < upper or txid == creator:
        return True
    if txid >= lower:
        return False
    return txid not in active


def point_in_time(rows, at):
    candidates = [row for row in rows
                  if row["event"] <= at and row["available"] <= at]
    return max(candidates, key=lambda row: (row["event"], row["available"])) if candidates else None


def recall_at_k(predicted, relevant, k):
    if k < 0:
        raise ValueError("negative k")
    if not relevant:
        return None
    return len(set(predicted[:k]) & set(relevant)) / len(set(relevant))


def ndcg(labels, k, ideal_labels=None):
    if k < 0 or any(value < 0 for value in labels):
        raise ValueError("invalid relevance or k")
    ideal_values = labels if ideal_labels is None else ideal_labels
    if any(value < 0 for value in ideal_values):
        raise ValueError("negative ideal relevance")
    def dcg(values):
        return sum((2 ** value - 1) / math.log2(i + 2)
                   for i, value in enumerate(values[:k]))
    # Supply the complete evaluation universe when relevant items may be missing.
    ideal = dcg(sorted(ideal_values, reverse=True))
    return dcg(labels) / ideal if ideal else 0.0


def rrf(rankings, constant=60):
    if constant < 0:
        raise ValueError("negative constant")
    scores = {}
    for ranking in rankings:
        for rank, item in enumerate(dict.fromkeys(ranking), 1):
            scores[item] = scores.get(item, 0) + 1 / (constant + rank)
    return sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))


def contiguous_next(start, completed):
    while start in completed:
        start += 1
    return start


def apply_versioned(state, entity, version, value):
    current = state.get(entity)
    if current and version < current[0]:
        return False
    if current and version == current[0]:
        if value != current[1]:
            raise ValueError("same version, different content")
        return False
    state[entity] = (version, value)  # None is a versioned tombstone, not absent state.
    return True


class Publisher:
    def __init__(self):
        self.epoch = 0
        self.current = None

    def acquire(self):
        self.epoch += 1
        return self.epoch

    def publish(self, token, snapshot, schema, parts, expected):
        if token != self.epoch:
            raise ValueError("stale executor")
        if set(parts) != set(expected):
            raise ValueError("incomplete manifest")
        for name, part in parts.items():
            if part["snapshot"] != snapshot or part["schema"] != schema:
                raise ValueError("incompatible reusable part")
            if hashlib.sha256(part["data"]).hexdigest() != part["checksum"]:
                raise ValueError("corrupt part: " + name)
        self.current = (snapshot, schema, tuple(sorted(parts)))


def make_part(snapshot, schema, data):
    return {"snapshot": snapshot, "schema": schema, "data": data,
            "checksum": hashlib.sha256(data).hexdigest()}


def must_fail(operation):
    try:
        operation()
    except ValueError:
        return
    raise AssertionError("expected a rejected operation")


def main():
    visibility = {i: read_view_visible(i, {40, 50}, 40, 60, 55)
                  for i in [30, 40, 45, 50, 55, 60]}
    assert visibility == {30: True, 40: False, 45: True, 50: False, 55: True, 60: False}
    print("ReadView:", visibility)

    rows = [{"event": 955, "available": 1005, "value": "late"},
            {"event": 950, "available": 952, "value": "visible"}]
    assert max(rows, key=lambda row: row["event"])["value"] == "late"
    assert point_in_time(rows, 1000)["value"] == "visible"
    print("Point-in-time join rejects a feature unavailable at the sample time")

    assert recall_at_k(["A", "C"], {"A", "B"}, 2) == 0.5
    assert recall_at_k(["A", "A"], {"A", "B"}, 2) == 0.5
    assert recall_at_k([], set(), 2) is None
    assert ndcg([3, 2, 0], 3) == 1.0 and ndcg([0, 0], 2) == 0.0
    assert ndcg([0, 3, 2], 3) < 1
    assert rrf([["A", "B"], ["B", "C"]])[0][0] == "B"
    print("Recall, duplicate handling, NDCG and rank fusion checks passed")

    assert contiguous_next(10, {11, 12}) == 10
    assert contiguous_next(10, {10, 11, 12}) == 13
    state = {}
    assert apply_versioned(state, "x", 3, "new")
    assert not apply_versioned(state, "x", 2, "old")
    assert not apply_versioned(state, "x", 3, "new")
    assert apply_versioned(state, "x", 4, None)
    assert not apply_versioned(state, "x", 3, "revive")
    must_fail(lambda: apply_versioned(state, "x", 4, "conflict"))
    print("Offsets advance only across the completed prefix; old updates cannot revive a tombstone")

    publisher = Publisher()
    old, token = publisher.acquire(), publisher.acquire()
    parts = {name: make_part("S1", "schema1", name.encode()) for name in ["P0", "P1", "P2"]}
    must_fail(lambda: publisher.publish(old, "S1", "schema1", parts, parts))
    must_fail(lambda: publisher.publish(token, "S1", "schema1", {"P0": parts["P0"]}, parts))
    must_fail(lambda: publisher.publish(token, "S2", "schema1", parts, parts))
    corrupted = dict(parts, P1=dict(parts["P1"], data=b"broken"))
    must_fail(lambda: publisher.publish(token, "S1", "schema1", corrupted, parts))
    publisher.publish(token, "S1", "schema1", parts, parts)
    assert publisher.current == ("S1", "schema1", ("P0", "P1", "P2"))
    print("Manifest rejects stale execution, missing shards, mismatched snapshots and corrupt data")
    print("All deterministic expert models passed; no real distributed system was exercised.")


if __name__ == "__main__":
    main()
