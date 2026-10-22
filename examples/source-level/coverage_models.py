"""Deterministic protocol models; not production distributed implementations.

Run: python3 examples/source-level/coverage_models.py
Only stdlib. SQLite cases use an in-memory DB and model ordered contenders.
"""
from collections import deque
from math import ceil, sqrt
import sqlite3


class Dag:
    def __init__(self, dependencies):
        self.deps = {n: set(parents) for n, parents in dependencies.items()}
        assert all(p in self.deps for ps in self.deps.values() for p in ps)
        left = {n: len(ps) for n, ps in self.deps.items()}
        ready = deque(n for n, count in left.items() if count == 0)
        seen = []
        while ready:
            n = ready.popleft()
            seen.append(n)
            for child, parents in self.deps.items():
                if n in parents:
                    left[child] -= 1
                    if left[child] == 0:
                        ready.append(child)
        if len(seen) != len(left):
            raise ValueError("cycle")
        self.state = {n: "PENDING" if ps else "READY" for n, ps in self.deps.items()}
        self.attempt = {n: 0 for n in self.deps}
        self.outputs = {}

    def start(self, n):
        assert self.state[n] == "READY"
        self.attempt[n] += 1
        self.state[n] = "RUNNING"
        return self.attempt[n]

    def finish(self, n, attempt, ok, output=None):
        if self.state[n] != "RUNNING" or self.attempt[n] != attempt:
            return False
        if ok:
            assert output is not None
            self.outputs[n] = output  # Output committed before dependents become READY.
        self.state[n] = "SUCCEEDED" if ok else "FAILED"
        changed = True
        while changed:
            changed = False
            for child, parents in self.deps.items():
                if self.state[child] != "PENDING":
                    continue
                states = {self.state[p] for p in parents}
                if states & {"FAILED", "SKIPPED"}:
                    self.state[child] = "SKIPPED"
                    changed = True
                elif states == {"SUCCEEDED"}:
                    assert all(p in self.outputs for p in parents)
                    self.state[child] = "READY"
                    changed = True
        return True

    def retry(self, n, attempt):
        assert self.state[n] == "RUNNING" and self.attempt[n] == attempt
        self.state[n] = "READY"  # Old worker may still run; attempt guard protects state only.


def dag_cases():
    d = Dag({"A": [], "B": ["A"], "C": ["A"], "D": ["B", "C"]})
    a = d.start("A")
    assert d.finish("A", a, True, "manifest-A")
    assert not d.finish("A", a, True, "duplicate")
    b, c = d.start("B"), d.start("C")
    d.finish("B", b, True, "B-1")
    assert d.state["D"] == "PENDING"
    d.finish("C", c, True, "C-1")
    assert d.state["D"] == "READY"
    d.start("D")
    d.retry("D", 1)
    assert d.start("D") == 2
    assert not d.finish("D", 1, True, "stale")
    assert d.finish("D", 2, True, "current")
    f = Dag({"A": [], "B": ["A"], "C": ["B"]})
    f.finish("A", f.start("A"), False)
    assert f.state == {"A": "FAILED", "B": "SKIPPED", "C": "SKIPPED"}
    try:
        Dag({"A": ["B"], "B": ["A"]})
        raise AssertionError("Cycle accepted")
    except ValueError:
        pass
    print("DAG: join, committed outputs, duplicates, stale attempt, failure propagation, cycle passed")


def partition_capacity_state():
    logical = {key: key % 64 for key in range(10000)}  # Deterministic toy hash only.
    for workers in (8, 12):
        plan = {w: [p for p in range(64) if p % workers == w] for w in range(workers)}
        assert sorted(p for ps in plan.values() for p in ps) == list(range(64))
        assert all(logical[key] in plan[logical[key] % workers] for key in logical)
    assert any(key % 8 != key % 12 for key in range(100))  # Direct worker-count routing changes.
    old = ceil(1000 * .7 * .010 / .6)
    new = ceil(1000 * .3 * .020 / .6)
    assert (old, new) == (12, 10)
    snapshot = {"id": "S7", "schema": 1, "rows": [{"key": "A", "value": "x"}]}

    def migrate(source, expected_snapshot):
        if source["id"] != expected_snapshot or source["schema"] != 1:
            raise ValueError("Incompatible source")
        return {"id": source["id"], "schema": 2,
                "rows": [dict(r, category="unknown") for r in source["rows"]]}

    target = migrate(snapshot, "S7")
    assert target["rows"][0]["category"] == "unknown"
    assert "category" not in snapshot["rows"][0]  # No mutation of old state.
    try:
        migrate(snapshot, "S8")
        raise AssertionError("Wrong snapshot accepted")
    except ValueError:
        pass
    print("Partition stability, version capacity 12/10, schema migration guards passed")


def vector_and_cost():
    q = (1., 0.)
    candidates = {"A": (2., 0.), "B": (100., 100.)}
    score = lambda a, b: sum(x*y for x, y in zip(a, b))
    normalize = lambda v: tuple(x/sqrt(sum(y*y for y in v)) for x in v)
    assert max(candidates, key=lambda k: score(q, candidates[k])) == "B"
    assert max(candidates, key=lambda k: score(normalize(q), normalize(candidates[k]))) == "A"
    query_old, a_old, b_old = (1., 0.), (1., 0.), (0., 1.)
    rotate = lambda v: (-v[1], v[0])
    dot = lambda a, b: sum(x*y for x, y in zip(a, b))
    query_new = rotate(query_old)
    assert dot(query_old, a_old) > dot(query_old, b_old)
    assert dot(query_new, b_old) > dot(query_new, a_old)  # Mixed encoders invert retrieval.
    assert dot(query_new, rotate(a_old)) > dot(query_new, rotate(b_old))
    reserved_old, reserved_new = 3000*24, 500*24 + 2500*1
    assert (reserved_old, reserved_new) == (72000, 14500)
    assert abs((1 - reserved_new/reserved_old)*100 - 79.8611111111) < 1e-6
    assert 5000*.5 == 2500*1
    print("Tower normalization, mixed embedding counterexample and explicit core-hour arithmetic passed")


def lease_case():
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE tasks (id TEXT PRIMARY KEY, plan_revision INT, state TEXT, "
               "owner TEXT, epoch INT, lease_until INT, output TEXT)")
    db.execute("INSERT INTO tasks VALUES ('s1',3,'READY',NULL,0,0,NULL)")

    def claim(owner, now, revision=3):
        cur = db.execute("UPDATE tasks SET owner=?, epoch=epoch+1, lease_until=?, state='RUNNING' "
                         "WHERE id='s1' AND plan_revision=? AND (state='READY' OR "
                         "(state='RUNNING' AND lease_until<=?)) RETURNING epoch", (owner, now+10, revision, now))
        row = cur.fetchone()  # Return the epoch from this UPDATE, not a later unguarded SELECT.
        return None if row is None else row[0]

    first = claim("w1", 0)
    assert first == 1 and claim("w2", 1) is None
    second = claim("w2", 11)
    assert second == 2
    assert claim("wrong-plan", 50, 2) is None

    def finish(owner, epoch, output, now):
        return db.execute("UPDATE tasks SET state='SUCCEEDED', output=? WHERE id='s1' "
                          "AND plan_revision=3 AND state='RUNNING' AND owner=? AND epoch=? "
                          "AND lease_until>?", (output, owner, epoch, now)).rowcount == 1

    assert not finish("w1", first, "late", 12)
    assert finish("w2", second, "current", 12)
    assert not finish("w2", second, "duplicate", 13)
    assert claim("w3", 99) is None
    assert db.execute("SELECT output FROM tasks").fetchone()[0] == "current"
    db.close()
    print("Lease CAS: sole owner, expiry reclaim, plan guard, old-epoch and duplicate rejection passed")


if __name__ == "__main__":
    dag_cases()
    partition_capacity_state()
    vector_and_cost()
    lease_case()
