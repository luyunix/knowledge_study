"""Deterministic local examples: lost responses, idempotency and eval validity.

Run with Python 3.9+. No network, LLM, API key or external database is used.
The SQLite example covers one transaction domain, not distributed effects.
"""

import hashlib
import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from typing import Tuple


class ReleaseService:
    def __init__(self):
        self.db = sqlite3.connect(":memory:")
        self.db.executescript("""
            CREATE TABLE deployments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                payload TEXT NOT NULL
            );
            CREATE TABLE operations (
                operation_id TEXT PRIMARY KEY,
                request_hash TEXT NOT NULL,
                deployment_id INTEGER NOT NULL
            );
        """)

    def release(self, operation_id, payload, lose_response=False):
        encoded = json.dumps(payload, sort_keys=True, ensure_ascii=False)
        request_hash = hashlib.sha256(encoded.encode()).hexdigest()
        with self.db:
            existing = self.db.execute(
                "SELECT request_hash, deployment_id FROM operations "
                "WHERE operation_id = ?", (operation_id,)
            ).fetchone()
            if existing:
                if existing[0] != request_hash:
                    raise ValueError("same operation_id, different request")
                return existing[1]
            cursor = self.db.execute(
                "INSERT INTO deployments(payload) VALUES (?)", (encoded,)
            )
            deployment_id = cursor.lastrowid
            self.db.execute(
                "INSERT INTO operations VALUES (?, ?, ?)",
                (operation_id, request_hash, deployment_id)
            )
        # The transaction has committed before the response is lost.
        if lose_response:
            raise TimeoutError("committed, but response lost")
        return deployment_id

    def count(self):
        return self.db.execute("SELECT COUNT(*) FROM deployments").fetchone()[0]

    def close(self):
        self.db.close()


@dataclass(frozen=True)
class Product:
    id: str
    name: str
    stock: int


@dataclass(frozen=True)
class Case:
    id: str
    kind: str
    query: str
    expected: Tuple[str, ...]


@dataclass(frozen=True)
class Result:
    case_id: str
    kind: str
    status: str
    reason: str


PRODUCTS = (
    Product("A", "红色跑鞋", 0),
    Product("B", "蓝色跑鞋", 5),
    Product("C", "红色背包", 8),
    Product("D", "绿色背包", 0),
)
CASES = (
    Case("B1", "badcase", "跑鞋", ("B",)),
    Case("B2", "badcase", "绿色背包", ()),
    Case("N1", "normal", "蓝色", ("B",)),
    Case("N2", "normal", "红色背包", ("C",)),
    Case("N3", "normal", "不存在", ()),
)


def search(release, query):
    if release not in {"r1", "r2", "r3"}:
        raise ValueError("unknown release")
    if release == "r3" and query == "蓝色":
        return []  # An introduced regression, not a valid optimization.
    return [p.id for p in PRODUCTS
            if query in p.name and (release == "r1" or p.stock > 0)]


def run_eval(target_release, served_release):
    results = []
    for case in CASES:
        if target_release != served_release:
            results.append(Result(case.id, case.kind, "INVALID", "wrong release"))
            continue
        actual = search(served_release, case.query)
        passed = sorted(actual) == sorted(case.expected)
        results.append(Result(
            case.id, case.kind, "PASS" if passed else "FAIL",
            "actual=%s expected=%s" % (actual, list(case.expected))
        ))
    return results


def ratio(passed, total):
    return "%d/%d" % (passed, total) if total else "undefined"


def summarize(results):
    counts = Counter(result.status for result in results)
    valid = counts["PASS"] + counts["FAIL"]
    report = {
        "total": len(results),
        "pass": counts["PASS"],
        "fail": counts["FAIL"],
        "invalid": counts["INVALID"],
        "pass_of_all": ratio(counts["PASS"], len(results)),
        "pass_of_valid": ratio(counts["PASS"], valid),
    }
    for kind in ("badcase", "normal"):
        group = [result for result in results if result.kind == kind]
        report[kind + "_pass_of_all"] = ratio(
            sum(result.status == "PASS" for result in group), len(group)
        )
    return report


def compare_runs(baseline, candidate):
    """Compare the same cases; invalid observations are not improvements."""
    before = {result.case_id: result for result in baseline}
    after = {result.case_id: result for result in candidate}
    if len(before) != len(baseline) or len(after) != len(candidate):
        raise ValueError("duplicate case IDs")
    if before.keys() != after.keys():
        raise ValueError("different case sets")
    changes = {"improved": [], "regressed": [], "unchanged": [], "not_comparable": []}
    for case_id in before:
        old, new = before[case_id].status, after[case_id].status
        if "INVALID" in (old, new):
            bucket = "not_comparable"
        elif old == "FAIL" and new == "PASS":
            bucket = "improved"
        elif old == "PASS" and new == "FAIL":
            bucket = "regressed"
        else:
            bucket = "unchanged"
        changes[bucket].append(case_id)
    return changes


def main():
    service = ReleaseService()
    try:
        payload = {"application": "catalog-search", "release": "r2", "env": "test"}
        try:
            service.release("op-204", payload, lose_response=True)
        except TimeoutError:
            print("Lost response: client does not know whether it committed.")
        assert service.count() == 1
        result_id = service.release("op-204", payload)
        assert result_id == 1 and service.count() == 1
        print("Same operation retried: deployment_id=1, total deployments=1")
        try:
            service.release("op-204", dict(payload, release="r3"))
        except ValueError:
            print("Same operation with changed content: rejected")
        else:
            raise AssertionError("changed content was not rejected")
        assert service.count() == 1
    finally:
        service.close()

    reports = {}
    for release, expected_passes in (("r1", 3), ("r2", 5), ("r3", 4)):
        report = summarize(run_eval(release, release))
        assert report["pass"] == expected_passes and report["invalid"] == 0
        reports[release] = report
        print(release, json.dumps(report, ensure_ascii=False))
    assert reports["r3"]["badcase_pass_of_all"] == "2/2"
    assert reports["r3"]["normal_pass_of_all"] == "2/3"
    invalid = summarize(run_eval("r2", "r1"))
    assert invalid["invalid"] == 5 and invalid["pass_of_valid"] == "undefined"
    print("Wrong release", json.dumps(invalid, ensure_ascii=False))
    changes = compare_runs(run_eval("r1", "r1"), run_eval("r3", "r3"))
    assert changes["improved"] == ["B1", "B2"]
    assert changes["regressed"] == ["N1"]
    print("r1 -> r3", json.dumps(changes, ensure_ascii=False))
    r2_to_r3 = compare_runs(run_eval("r2", "r2"), run_eval("r3", "r3"))
    assert not r2_to_r3["improved"] and r2_to_r3["regressed"] == ["N1"]
    print("r2 -> r3", json.dumps(r2_to_r3, ensure_ascii=False))
    missing_baseline = compare_runs(run_eval("r2", "r1"), run_eval("r2", "r2"))
    assert len(missing_baseline["not_comparable"]) == 5
    assert not missing_baseline["improved"]
    print("Invalid baseline is not counted as an improvement.")
    assert sorted(["B", "B"]) != sorted(["B"])
    print("All deterministic checks passed.")


if __name__ == "__main__":
    main()
