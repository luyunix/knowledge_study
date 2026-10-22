"""Finite local counterexamples, not Dubbo/ZooKeeper/Python SDK integration.

Directory events are already classified; real empty-protection configuration,
URL conversion, sessions, network delivery and transport sharing are not modeled.
Selection is deterministic here, not Dubbo's load-balancing implementation.
"""

from dataclasses import dataclass
import threading
import unittest


class Unavailable(Exception):
    pass


@dataclass(frozen=True)
class Release:
    environment: str
    app: str
    version: str
    artifact: str
    config: str


@dataclass(frozen=True)
class Provider:
    name: str
    release: Release
    ready: bool = True
    accepting: bool = True


class Directory:
    def __init__(self):
        self.cached = ()
        self.forbidden = False

    def refresh(self, event, providers=()):
        if event == "ordinary-empty":
            # Simplified cached-address preservation branch.
            return "retained"
        if event == "explicit-empty":
            self.forbidden = True
            self.cached = ()
            return "cleared"
        if event == "conversion-failed":
            return "retained"
        if event != "providers" or not providers:
            raise ValueError("classify the event explicitly")
        self.cached = tuple(providers)
        self.forbidden = False
        return "installed"

    def select(self, expected):
        candidates = [] if self.forbidden else [
            p for p in self.cached
            if p.release == expected and p.ready and p.accepting
        ]
        if not candidates:
            raise Unavailable("no qualified target; no cross-version fallback")
        return sorted(candidates, key=lambda p: p.name)[0]


class RouteView:
    """One scope and one sequential installer; not a global fencing protocol."""

    def __init__(self):
        self.generation = -1
        self.release = None

    def install(self, generation, release):
        if generation < self.generation:
            return "stale"
        if generation == self.generation:
            if release != self.release:
                raise ValueError("same generation, conflicting payload")
            return "duplicate"
        self.generation, self.release = generation, release
        return "installed"


class ReferenceGate:
    """Toy ownership gate, not ReferenceConfig internals or socket ownership."""

    def __init__(self):
        self.lock = threading.Lock()
        self.accepting = True
        self.closed = False
        self.leases = set()

    def acquire(self):
        with self.lock:
            if not self.accepting:
                raise Unavailable("reference retiring")
            token = object()
            self.leases.add(token)
            return token

    def retire(self):
        with self.lock:
            self.accepting = False
            self.closed = not self.leases

    def release(self, token):
        with self.lock:
            if token not in self.leases:
                return False
            self.leases.remove(token)
            if not self.accepting and not self.leases:
                self.closed = True
            return True


class LifecycleContracts(unittest.TestCase):
    def setUp(self):
        self.r1 = Release("stage", "recommend", "r1", "H1", "K1")
        self.r2 = Release("stage", "recommend", "r2", "H2", "K2")
        self.d = Provider("D", self.r2)
        self.e = Provider("E", self.r2)
        self.directory = Directory()

    def test_registered_provider_is_not_necessarily_ready(self):
        self.directory.refresh("providers", [Provider("D", self.r2, ready=False)])
        with self.assertRaises(Unavailable):
            self.directory.select(self.r2)

    def test_healthy_r1_does_not_hide_empty_r2(self):
        self.directory.refresh("providers", [Provider("A", self.r1)])
        with self.assertRaises(Unavailable):
            self.directory.select(self.r2)

    def test_same_label_with_wrong_artifact_is_not_expected_release(self):
        fake = Release("stage", "recommend", "r2", "OLD", "K2")
        self.directory.refresh("providers", [Provider("D", fake)])
        with self.assertRaises(Unavailable):
            self.directory.select(self.r2)

    def test_ordinary_empty_retains_previous_directory(self):
        self.directory.refresh("providers", [self.d])
        self.assertEqual(self.directory.refresh("ordinary-empty"), "retained")
        self.assertEqual(self.directory.select(self.r2), self.d)

    def test_explicit_empty_clears_and_forbids(self):
        self.directory.refresh("providers", [self.d])
        self.directory.refresh("explicit-empty")
        with self.assertRaises(Unavailable):
            self.directory.select(self.r2)
        self.assertEqual(self.directory.cached, ())

    def test_failed_conversion_does_not_prove_new_view_installed(self):
        self.directory.refresh("providers", [self.d])
        self.assertEqual(self.directory.refresh("conversion-failed"), "retained")
        self.assertEqual(self.directory.cached, (self.d,))

    def test_retry_rechecks_same_release_after_directory_change(self):
        self.directory.refresh("providers", [self.d, self.e])
        self.assertEqual(self.directory.select(self.r2).name, "D")
        self.directory.refresh("providers", [Provider("A", self.r1)])
        with self.assertRaises(Unavailable):
            self.directory.select(self.r2)

    def test_route_before_discovery_cannot_manufacture_provider(self):
        view = RouteView()
        view.install(101, self.r2)
        with self.assertRaises(Unavailable):
            self.directory.select(view.release)

    def test_rollback_old_release_uses_new_generation(self):
        view = RouteView()
        view.install(102, self.r2)
        view.install(103, self.r1)
        self.assertEqual(view.install(102, self.r2), "stale")
        self.assertEqual(view.release, self.r1)

    def test_equal_generation_requires_equal_payload(self):
        view = RouteView()
        view.install(101, self.r1)
        self.assertEqual(view.install(101, self.r1), "duplicate")
        with self.assertRaises(ValueError):
            view.install(101, self.r2)

    def test_local_install_does_not_update_other_proxy(self):
        first, disconnected = RouteView(), RouteView()
        first.install(101, self.r1)
        disconnected.install(101, self.r1)
        first.install(102, self.r2)
        self.assertNotEqual(first.release, disconnected.release)

    def test_retirement_rejects_new_leases_and_waits_for_existing(self):
        gate = ReferenceGate()
        token = gate.acquire()
        gate.retire()
        self.assertFalse(gate.closed)
        with self.assertRaises(Unavailable):
            gate.acquire()
        self.assertTrue(gate.release(token))
        self.assertTrue(gate.closed)
        self.assertFalse(gate.release(token))

    def test_foreign_lease_does_not_release_owned_resource(self):
        first, second = ReferenceGate(), ReferenceGate()
        a, b = first.acquire(), second.acquire()
        second.retire()
        self.assertFalse(second.release(a))
        self.assertFalse(second.closed)
        self.assertTrue(second.release(b))

    def test_one_pod_removal_does_not_destroy_version_reference(self):
        reference = ReferenceGate()
        self.directory.refresh("providers", [self.d, self.e])
        self.directory.refresh("providers", [self.d])
        token = reference.acquire()
        self.assertEqual(self.directory.select(self.r2).name, "D")
        reference.release(token)
        self.assertFalse(reference.closed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
