"""Deterministic teaching checks. Python 3.9+, standard library only.

No external services, Java runtime, distributed locks or performance benchmarks.
"""
from collections import OrderedDict
from dataclasses import dataclass
from itertools import product
from math import isclose, log2
from random import Random
from threading import Lock


@dataclass(eq=False)
class Node:
    key: object = None
    value: object = None
    prev: object = None
    next: object = None


class LockedLRU:
    """Map + explicit doubly linked list; left is most recently used.

    One lock protects all structure operations. Values may not be None, making
    a missing get unambiguous. No expiration, remote loading or byte budget.
    """
    def __init__(self, capacity):
        if capacity < 0:
            raise ValueError("negative capacity")
        self.capacity = capacity
        self.nodes = {}
        self.head, self.tail = Node(), Node()
        self.head.next, self.tail.prev = self.tail, self.head
        self.lock = Lock()

    def _detach(self, node):
        node.prev.next = node.next
        node.next.prev = node.prev

    def _front(self, node):
        first = self.head.next
        node.prev, node.next = self.head, first
        self.head.next, first.prev = node, node

    def get(self, key):
        with self.lock:
            node = self.nodes.get(key)
            if node is None:
                return None
            self._detach(node)
            self._front(node)
            return node.value

    def put(self, key, value):
        if value is None:
            raise ValueError("None is reserved for a cache miss")
        with self.lock:
            if self.capacity == 0:
                return
            node = self.nodes.get(key)
            if node is not None:
                node.value = value
                self._detach(node)
            else:
                node = Node(key, value)
                self.nodes[key] = node
            self._front(node)
            if len(self.nodes) > self.capacity:
                victim = self.tail.prev
                self._detach(victim)
                del self.nodes[victim.key]

    def snapshot(self):
        """Teaching diagnostic: check map/list invariants under the same lock."""
        with self.lock:
            result, seen = [], set()
            previous, node = self.head, self.head.next
            while node is not self.tail:
                assert node.prev is previous
                assert node.key not in seen
                assert self.nodes[node.key] is node
                seen.add(node.key)
                result.append((node.key, node.value))
                previous, node = node, node.next
            assert self.tail.prev is previous
            assert len(result) == len(self.nodes) <= self.capacity
            assert seen == set(self.nodes)
            return result


def max_subarray(values):
    """Maximum sum over NONEMPTY continuous slices; reject empty input."""
    if not values:
        raise ValueError("nonempty array required")
    end_here = best = values[0]
    for value in values[1:]:
        end_here = max(value, end_here + value)
        best = max(best, end_here)
    return best


def brute_subarray(values):
    best = values[0]
    for left in range(len(values)):
        total = 0
        for right in range(left, len(values)):
            total += values[right]
            best = max(best, total)
    return best


def hash_split_demo():
    hashes = [3, 11, 19]  # Already-spread hashes, NOT a Java hashCode implementation.
    assert [h & 7 for h in hashes] == [3, 3, 3]
    assert [h & 15 for h in hashes] == [3, 11, 3]
    low = [h for h in hashes if h & 8 == 0]
    high = [h for h in hashes if h & 8 != 0]
    assert low == [3, 19] and high == [11]
    print("Hash 拆桶：容量 8 的桶 3 → 容量 16 的桶 3:[3,19]、桶 11:[11]")


def lru_demo():
    cache = LockedLRU(2)
    states = []
    cache.put("A", 1)
    states.append(cache.snapshot())
    cache.put("B", 2)
    states.append(cache.snapshot())
    assert cache.get("A") == 1
    states.append(cache.snapshot())
    cache.put("C", 3)
    states.append(cache.snapshot())
    assert states == [[("A", 1)], [("B", 2), ("A", 1)],
                      [("A", 1), ("B", 2)], [("C", 3), ("A", 1)]]
    assert cache.get("B") is None
    cache.put("A", 10)
    assert cache.snapshot() == [("A", 10), ("C", 3)]
    print("LRU 状态：", states)
    rng = Random(7)
    for capacity in (0, 1, 2, 4):
        actual, reference = LockedLRU(capacity), OrderedDict()
        for _ in range(500):
            key = rng.randrange(6)
            if rng.randrange(2):
                value = rng.randrange(100)
                actual.put(key, value)
                if capacity:
                    reference[key] = value
                    reference.move_to_end(key)
                    if len(reference) > capacity:
                        reference.popitem(last=False)
            else:
                expected = reference.get(key)
                if key in reference:
                    reference.move_to_end(key)
                assert actual.get(key) == expected
            assert actual.snapshot() == list(reversed(reference.items()))
    print("LRU：2,000 次固定种子操作与参考实现一致；非并发压测。")


def subarray_demo():
    assert max_subarray([1, 2, -5, 4, 3]) == 7
    assert max_subarray([-4, -2, -7]) == -2
    assert max_subarray([0]) == 0
    try:
        max_subarray([])
    except ValueError:
        pass
    else:
        raise AssertionError("empty input must be rejected")
    cases = 0
    for length in range(1, 6):
        for values in product(range(-2, 3), repeat=length):
            assert max_subarray(values) == brute_subarray(values), values
            cases += 1
    assert cases == 3905
    print("最大子数组：示例 7，全负例 -2；3,905 组数组与暴力法一致。")


def ranking_demo():
    ranked, relevant = ["A", "B", "C"], {"A", "C"}
    grades = {"A": 3, "B": 0, "C": 2}
    hits = len(set(ranked) & relevant)
    precision, recall = hits / len(ranked), hits / len(relevant)
    def dcg(items):
        return sum((2 ** grades[item] - 1) / log2(rank + 2)
                   for rank, item in enumerate(items))
    ndcg = dcg(ranked) / dcg(["A", "C", "B"])
    coarse_preservation = len({"A", "B"} & {"A", "C"}) / 2
    assert precision == 2 / 3 and recall == 1
    assert dcg(ranked) == 8.5
    assert isclose(ndcg, 0.95583058934618)
    assert coarse_preservation == 0.5
    print(f"评估：Precision={precision:.4f} Recall={recall:.4f} "
          f"NDCG={ndcg:.4f} 粗排保留率={coarse_preservation:.2f}")


if __name__ == "__main__":
    hash_split_demo()
    lru_demo()
    subarray_demo()
    ranking_demo()
    print("全部检查通过；只验证教学数据与状态，不代表真实系统验收。")
