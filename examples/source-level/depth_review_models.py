"""Reproducible arithmetic/state models for the depth review.

Not Lucene-compatible bytes, HNSW implementation, Eino execution, or a service test.
The PFor model checks the documented branch's size/reconstruction arithmetic only.
"""
import heapq
import math
import unittest


def pfor_accounting(values, bits):
    if len(values) != 128 or bits < 1 or any(x < 0 for x in values):
        raise ValueError("128 nonnegative values and a positive width required")
    mask = (1 << bits) - 1
    low = [x & mask for x in values]
    exceptions = [(i, x >> bits) for i, x in enumerate(values) if x >> bits]
    max_bits = max(values).bit_length()
    # Matches the studied source branch's prerequisites, not all encoder choices.
    all_equal_branch = len(set(low)) == 1 and max_bits <= 8
    vlong_bytes = max(1, (low[0].bit_length() + 6) // 7)
    base_bytes = vlong_bytes if all_equal_branch else 128 * bits // 8
    restored = low[:]
    for i, high in exceptions:
        restored[i] |= high << bits
    # The two examples have one-byte index + one-byte high part per exception.
    if any(high > 255 for _, high in exceptions):
        raise ValueError("model only accounts one-byte exception high parts")
    return restored, 1 + base_bytes + 2 * len(exceptions), all_equal_branch


def graph_search_model(graph, distances, start="A", ef=2):
    """Toy distance-ascending traversal; Lucene's score comparator differs."""
    candidates = [(distances[start], start)]
    results = [(-distances[start], start)]
    visited, expanded = {start}, []
    while candidates:
        distance, node = heapq.heappop(candidates)
        if len(results) == ef and distance > -results[0][0]:
            break
        expanded.append(node)
        for neighbor in graph.get(node, []):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            d = distances[neighbor]
            if len(results) < ef or d < -results[0][0]:
                heapq.heappush(candidates, (d, neighbor))
                heapq.heappush(results, (-d, neighbor))
                if len(results) > ef:
                    heapq.heappop(results)
    return sorted((-d, node) for d, node in results), expanded


def chunks(total, size, overlap):
    if total < 0 or not 0 <= overlap < size:
        raise ValueError("invalid token dimensions")
    output, start = [], 0
    while start < total:
        end = min(start + size, total)
        output.append((start, end))
        if end == total:
            break
        start += size - overlap
    return output


class DepthReviewModels(unittest.TestCase):
    def test_pfor_special_and_normal_accounting(self):
        special = [1] * 128
        special[42] = 129
        restored, size, branch = pfor_accounting(special, 1)
        self.assertEqual(restored, special)
        self.assertEqual((size, branch), (4, True))
        normal = [1] * 128
        normal[42] = 1000
        restored, size, branch = pfor_accounting(normal, 2)
        self.assertEqual(restored, normal)
        self.assertEqual((size, branch), (35, False))

    def test_graph_queue_pruning_can_hide_better_neighbor(self):
        graph = {"A": ["B", "C"], "C": ["D"], "B": ["E"]}
        distances = {"A": 9, "B": 6, "C": 2, "D": 1, "E": 0.5}
        results, expanded = graph_search_model(graph, distances)
        self.assertEqual(results, [(1, "D"), (2, "C")])
        self.assertNotIn("B", expanded)
        self.assertNotIn("E", expanded)
        self.assertLess(distances["E"], results[0][0])

    def test_overlap_and_storage(self):
        windows = chunks(1000, 200, 50)
        self.assertEqual(windows, [(0, 200), (150, 350), (300, 500),
                                   (450, 650), (600, 800), (750, 950), (900, 1000)])
        self.assertEqual(sum(b - a for a, b in windows), 1300)
        self.assertEqual(10000 * len(windows) * 768 * 4, 215040000)
        self.assertEqual(chunks(200, 200, 50), [(0, 200)])
        self.assertEqual(chunks(0, 200, 50), [])
        with self.assertRaises(ValueError):
            chunks(100, 200, 200)

    def test_rrf_judge_and_denominators(self):
        a, b = 1 / 61 + 1 / 70, 1 / 62 + 1 / 61
        self.assertGreater(b, a)
        tp, fn, fp, tn = 72, 8, 6, 14
        self.assertAlmostEqual((tp + tn) / (tp + fn + fp + tn), .86)
        self.assertAlmostEqual(fp / (fp + tn), .30)
        self.assertAlmostEqual(tp / (tp + fp), 72 / 78)
        self.assertEqual((72 / 100, 72 / 80, 80 / 100), (.72, .9, .8))

    def test_queue_catchup_memory_and_peak(self):
        self.assertEqual(10 / .04, 250)
        self.assertEqual(500 * .04, 20)
        self.assertAlmostEqual(50000 * 20 * 1024 / 1024 ** 2, 976.5625)
        backlog = 8 * 3600 * 10000
        self.assertEqual(backlog, 288000000)
        self.assertEqual(backlog / (30000 - 10000), 4 * 3600)
        self.assertEqual(100000000 / 8 * 1000, 12500000000)
        self.assertEqual(200 + 200 + 150, 550)
        self.assertEqual((10 + 10 + 40) / 10, 6)

    def test_control_generation_and_dependency_dedup(self):
        current_generation, business_version = 9, "v2"
        def install(generation, version):
            nonlocal current_generation, business_version
            if generation <= current_generation:
                return False
            current_generation, business_version = generation, version
            return True
        self.assertFalse(install(8, "v1"))
        self.assertTrue(install(10, "v1"))
        self.assertEqual((current_generation, business_version), (10, "v1"))
        dependencies, completed = {"B", "C"}, set()
        for event in ["B", "B"]:
            completed.add(event)
        self.assertEqual(dependencies - completed, {"C"})
        completed.add("C")
        self.assertFalse(dependencies - completed)

    def test_mixed_direction_cursor(self):
        rows = [(4, 3, 1), (4, 3, 2), (4, 7, 3), (3, 1, 4)]
        ordered = sorted(rows, key=lambda r: (-r[0], r[1], r[2]))
        cursor = ordered[1]
        p, t, i = cursor
        after = [r for r in ordered if r[0] < p or
                 (r[0] == p and r[1] > t) or
                 (r[0] == p and r[1] == t and r[2] > i)]
        self.assertEqual(after, ordered[2:])

    def test_srm_and_lfu_arithmetic(self):
        self.assertEqual(sum((observed - 1000) ** 2 / 1000
                             for observed in [900, 1100]), 20)
        self.assertEqual(1 / (max(5 - 5, 0) * 10 + 1), 1)
        self.assertEqual(1 / (max(15 - 5, 0) * 10 + 1), 1 / 101)
        self.assertEqual(20 - math.floor(15 / 5), 17)


if __name__ == "__main__":
    unittest.main(verbosity=2)
