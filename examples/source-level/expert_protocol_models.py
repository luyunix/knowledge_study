"""Executable teaching models, not a distributed-system correctness proof.

Uses real SQLite transactions/concurrent connections for a bounded local domain.
Does not validate MySQL lock behavior, Kafka, Codex, Eino, Kubernetes or networks.
"""

import math
import sqlite3
import tempfile
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


class ClosingConnection(sqlite3.Connection):
    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.close()


class ProtocolModels(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="expert-protocol-")
        self.db = str(Path(self.temp.name) / "model.sqlite")
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE operations (
                  tenant TEXT, action TEXT, op TEXT, payload_hash TEXT,
                  task_id TEXT, PRIMARY KEY (tenant, action, op));
                CREATE TABLE tasks (id TEXT PRIMARY KEY, attempt INTEGER,
                                    state TEXT, manifest TEXT);
                CREATE TABLE releases (id TEXT PRIMARY KEY, state TEXT,
                                       revision INTEGER);
                CREATE TABLE outbox (release_id TEXT, revision INTEGER,
                                     desired TEXT,
                                     PRIMARY KEY (release_id, revision));
                CREATE TABLE route (id TEXT PRIMARY KEY, revision INTEGER,
                                    desired TEXT);
                CREATE TABLE dependencies (
                  run TEXT, node TEXT, dependency TEXT, expected TEXT,
                  satisfied INTEGER DEFAULT 0,
                  PRIMARY KEY (run, node, dependency));
                CREATE TABLE nodes (run TEXT, node TEXT, state TEXT,
                                    ready_transitions INTEGER DEFAULT 0,
                                    PRIMARY KEY (run, node));
            """)

    def tearDown(self):
        self.temp.cleanup()

    def connect(self):
        return sqlite3.connect(self.db, timeout=10, isolation_level=None,
                               factory=ClosingConnection)

    def submit(self, digest, barrier=None, fail_before_commit=False):
        if barrier:
            barrier.wait(timeout=10)
        db = self.connect()
        try:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT payload_hash,task_id FROM operations "
                "WHERE tenant=? AND action=? AND op=?", ("T", "deploy", "O1")
            ).fetchone()
            if row:
                if row[0] != digest:
                    raise ValueError("same key, different intent")
                db.commit()
                return row[1]
            db.execute("INSERT INTO tasks VALUES ('D1',1,'ACCEPTED',NULL)")
            db.execute("INSERT INTO operations VALUES (?,?,?,?,?)",
                       ("T", "deploy", "O1", digest, "D1"))
            if fail_before_commit:
                raise RuntimeError("injected before local commit")
            db.commit()
            return "D1"
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def seed_release(self):
        with self.connect() as db:
            db.execute("INSERT INTO releases VALUES ('R','CANARY',7)")
            db.execute("INSERT INTO route VALUES ('R',6,'CANARY')")

    def promote(self, expected):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute(
                "UPDATE releases SET state='PROMOTED',revision=revision+1 "
                "WHERE id='R' AND state='CANARY' AND revision=?", (expected,)
            ).rowcount
            if changed:
                db.execute("INSERT INTO outbox VALUES ('R',?,'PROMOTED')",
                           (expected + 1,))
            db.commit()
            return changed

    def cancel(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            revision, state = db.execute(
                "SELECT revision,state FROM releases WHERE id='R'"
            ).fetchone()
            if state not in ("CANARY", "PROMOTED"):
                db.commit()
                return revision
            db.execute("UPDATE releases SET state='CANCELLED',revision=? "
                       "WHERE id='R'", (revision + 1,))
            db.execute("INSERT INTO outbox VALUES ('R',?,'CANCELLED')",
                       (revision + 1,))
            db.commit()
            return revision + 1

    def apply_route(self, revision, desired):
        with self.connect() as db:
            return db.execute(
                "UPDATE route SET revision=?,desired=? "
                "WHERE id='R' AND revision<?", (revision, desired, revision)
            ).rowcount

    def complete_dependency(self, dependency, revision, barrier=None):
        if barrier:
            barrier.wait(timeout=10)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            changed = db.execute(
                "UPDATE dependencies SET satisfied=1 WHERE run='G1' "
                "AND node='D' AND dependency=? AND expected=? AND satisfied=0",
                (dependency, revision)
            ).rowcount
            if changed:
                missing = db.execute(
                    "SELECT COUNT(*) FROM dependencies WHERE run='G1' "
                    "AND node='D' AND satisfied=0"
                ).fetchone()[0]
                if not missing:
                    db.execute("UPDATE nodes SET state='READY',"
                               "ready_transitions=ready_transitions+1 "
                               "WHERE run='G1' AND node='D' AND state='PENDING'")
            db.commit()
            return changed

    def test_concurrent_same_intent_creates_one_local_task(self):
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(self.submit, "H1", barrier) for _ in range(2)]
            self.assertEqual([f.result(timeout=15) for f in futures], ["D1", "D1"])
        with self.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 1)

    def test_payload_change_is_not_a_retry(self):
        self.submit("H1")
        with self.assertRaises(ValueError):
            self.submit("H2")
        self.assertEqual(self.submit("H1"), "D1")

    def test_precommit_failure_rolls_back_both_records(self):
        with self.assertRaises(RuntimeError):
            self.submit("H1", fail_before_commit=True)
        with self.connect() as db:
            self.assertEqual(db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0], 0)
            self.assertEqual(db.execute("SELECT COUNT(*) FROM operations").fetchone()[0], 0)
        self.submit("H1")  # Pretend the committed response is lost.
        self.assertEqual(self.submit("H1"), "D1")

    def test_cancel_rejects_stale_observation(self):
        self.seed_release()
        self.assertEqual(self.cancel(), 8)
        self.assertEqual(self.promote(7), 0)
        with self.connect() as db:
            self.assertEqual(db.execute("SELECT state FROM releases").fetchone()[0], "CANCELLED")
            self.assertEqual(db.execute("SELECT COUNT(*) FROM outbox").fetchone()[0], 1)

    def test_route_converges_but_control_commit_is_not_remote_barrier(self):
        self.seed_release()
        self.assertEqual(self.promote(7), 1)  # Produces revision 8.
        self.assertEqual(self.cancel(), 9)   # Produces revision 9.
        # Cancellation is committed locally, but not yet observed by this receiver.
        self.assertEqual(self.apply_route(8, "PROMOTED"), 1)
        self.assertEqual(self.apply_route(9, "CANCELLED"), 1)
        self.assertEqual(self.apply_route(8, "PROMOTED"), 0)

    def test_join_deduplicates_logical_edge_and_pins_revision(self):
        with self.connect() as db:
            db.execute("INSERT INTO nodes VALUES ('G1','D','PENDING',0)")
            db.executemany("INSERT INTO dependencies VALUES ('G1','D',?,?,0)",
                           [("B", "B1"), ("C", "C1")])
        barrier = threading.Barrier(2)
        with ThreadPoolExecutor(max_workers=2) as pool:
            fs = [pool.submit(self.complete_dependency, "B", "B1", barrier) for _ in range(2)]
            self.assertEqual(sorted(f.result(timeout=15) for f in fs), [0, 1])
        self.assertEqual(self.complete_dependency("B", "B2"), 0)
        with self.connect() as db:
            self.assertEqual(db.execute("SELECT state FROM nodes").fetchone()[0], "PENDING")
        self.assertEqual(self.complete_dependency("C", "C1"), 1)
        self.assertEqual(self.complete_dependency("C", "C1"), 0)
        with self.connect() as db:
            self.assertEqual(db.execute("SELECT state,ready_transitions FROM nodes").fetchone(), ("READY", 1))

    def test_old_attempt_cannot_publish_manifest(self):
        with self.connect() as db:
            db.execute("INSERT INTO tasks VALUES ('B',2,'RUNNING',NULL)")
            old = db.execute("UPDATE tasks SET manifest='old',state='SUCCEEDED' "
                             "WHERE id='B' AND attempt=1 AND state='RUNNING'").rowcount
            new = db.execute("UPDATE tasks SET manifest='new',state='SUCCEEDED' "
                             "WHERE id='B' AND attempt=2 AND state='RUNNING'").rowcount
            self.assertEqual((old, new), (0, 1))

    def test_fence_values_are_only_ordered_within_their_scope(self):
        accepted = {"application-A": 8, "application-B": 2}
        def accept(resource, epoch):
            if epoch < accepted[resource]:
                return False
            accepted[resource] = epoch
            return True
        self.assertFalse(accept("application-A", 7))
        self.assertTrue(accept("application-B", 3))
        self.assertTrue(accept("application-A", 8))  # Fence alone allows duplicates.

    def test_paired_exact_binomial_calculation(self):
        both_pass, improved, regressed, both_fail = 65, 15, 5, 15
        self.assertEqual(both_pass + improved + regressed + both_fail, 100)
        self.assertEqual((both_pass + regressed, both_pass + improved), (70, 80))
        p = 2 * sum(math.comb(20, k) for k in range(6)) / 2**20
        self.assertAlmostEqual(p, 0.04138946533203125)

    def test_zero_failures_still_has_nonzero_upper_bound(self):
        upper = 1 - 0.05 ** (1 / 300)
        self.assertAlmostEqual(upper, 0.00993608194445771)
        # Repeating ten correlated samples 30 times does not establish n=300 IID.
        self.assertGreater(1 - 0.05 ** (1 / 10), upper)

    def test_isolation_memory_and_error_budget_have_units(self):
        shared_mib = 2 * (300 + 20 * 100)
        separate_mib = 20 * 2 * (200 + 100)
        self.assertEqual((shared_mib, separate_mib, separate_mib - shared_mib), (4600, 12000, 7400))
        errors_per_sec = 1000 * 0.05 * 0.10
        allowed_per_sec = 1000 * (1 - 0.999)
        self.assertAlmostEqual(errors_per_sec / allowed_per_sec, 5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
