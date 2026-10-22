"""Deterministic project mechanisms. No real platform, model, ODPS/OSS or K8s."""
import importlib
import json
import hashlib
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path


def reject(fn):
    try:
        fn()
    except (ValueError, KeyError):
        return
    raise AssertionError("expected rejection")


def import_lab():
    name = "project_lab_" + uuid.uuid4().hex
    old_flag = sys.dont_write_bytecode
    with tempfile.TemporaryDirectory(prefix="python-import-lab-") as folder:
        module_file = Path(folder) / (name + ".py")
        sys.dont_write_bytecode = True
        sys.path.insert(0, folder)
        try:
            module_file.write_text("LEGACY = 1\n\ndef run():\n    return 'v1'\n")
            module = importlib.import_module(name)
            old_run = module.run
            assert importlib.import_module(name) is module
            module_file.write_text("def run():\n    return 'version-two'\n")
            importlib.invalidate_caches()
            assert importlib.reload(module) is module
            assert module.run() == "version-two" and old_run() == "v1"
            assert module.LEGACY == 1
            # Start two fresh interpreters. No shared sys.modules.
            script = "import sys,types;m=types.ModuleType('strategy');m.value=sys.argv[1];sys.modules['strategy']=m;print(m.value)"
            outputs = [
                subprocess.check_output([sys.executable, "-c", script, value], text=True).strip()
                for value in ("v1", "v2")
            ]
            assert outputs == ["v1", "v2"]
        finally:
            sys.path.remove(folder)
            sys.modules.pop(name, None)
            sys.dont_write_bytecode = old_flag
    print("67: actual import cache/reload keeps external binding and legacy name; fresh processes isolated")


def identity(definition):
    return hashlib.sha256(json.dumps(
        definition, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode()).hexdigest()


def require_count(value):
    if type(value) is not int or not 1 <= value <= 100:
        raise ValueError("count must be an integer in [1,100]")


def validate_stream(events, expected_release):
    if not events or events[0].get("type") != "START":
        raise ValueError("missing START")
    next_seq, ended = 0, False
    for position, event in enumerate(events):
        if ended or event.get("release") != expected_release:
            raise ValueError("late event or wrong release")
        kind = event["type"]
        if kind == "START":
            if position != 0:
                raise ValueError("duplicate START")
        elif kind == "CHUNK":
            if type(event.get("seq")) is not int or event["seq"] != next_seq:
                raise ValueError("gap or duplicate")
            next_seq += 1
        elif kind == "END":
            ended = True
        else:
            raise ValueError("unsupported event")
    if not ended:
        raise ValueError("not terminal")
    return next_seq


def cli_state(exit_code, stdout):
    if exit_code is None:  # local timeout/response unavailable, not remote failure proof
        return "UNKNOWN"
    if exit_code != 0:
        return "CHECK_ERROR"
    result = json.loads(stdout)
    if not isinstance(result, dict):
        raise ValueError("CLI result must be an object")
    status = result.get("status")
    if type(result.get("schema")) is not int or result["schema"] != 1 or status not in {"SUBMITTED", "RUNNING", "SUCCEEDED", "FAILED"}:
        raise ValueError("invalid CLI response")
    return {"SUBMITTED": "WAIT", "RUNNING": "WAIT", "SUCCEEDED": "VERIFY", "FAILED": "DIAGNOSE"}[status]


class FixtureProvider:
    def __init__(self, fixtures):
        self.fixtures = fixtures

    def call(self, tenant, action, entity):
        if action != "get_stock":
            raise ValueError("write/network fallback prohibited")
        return self.fixtures[(tenant, action, entity)]


class JobLedger:
    """Single-run sequential ledger; not an API server or a durable transaction."""
    def __init__(self):
        self.jobs, self.current, self.complete = {}, {}, set()

    def submit(self, name, request_hash):
        if name in self.jobs and self.jobs[name] != request_hash:
            raise ValueError("same name, different input")
        self.jobs[name] = request_hash

    def accept(self, shard, attempt, pod_succeeded, manifest_committed):
        if self.current.get(shard) != attempt or not pod_succeeded or not manifest_committed:
            raise ValueError("stale attempt or incomplete artifact")
        if shard in self.complete:
            return False
        self.complete.add(shard)
        return True


def ranges(total, pieces):
    if total < 0 or pieces <= 0:
        raise ValueError("invalid dimensions")
    q, r = divmod(total, pieces)
    start, output = 0, []
    for part in range(pieces):
        count = q + (part < r)
        if count:
            output.append((start, start + count))
        start += count
    return output


def require_manifest(expected_source, expected_shards, parts):
    if set(parts) != set(expected_shards):
        raise ValueError("missing/extra shards")
    for part in parts.values():
        if part["source"] != expected_source or not part["object_complete"]:
            raise ValueError("mixed source or unfinished object")
    return True


def main():
    import_lab()
    a = {"commit": "C7", "sdk": "2", "lock": "L1", "runtime": "R1"}
    assert identity(a) == identity(dict(reversed(list(a.items()))))
    assert identity(a) != identity(dict(a, sdk="3"))
    assert identity(a) != identity(dict(a, runtime="R2"))
    print("68: normalized identity stable by key order; SDK/runtime changes invalidate identity")

    require_count(20)
    reject(lambda: require_count(True))
    stream = [
        {"type": "START", "release": "r2"},
        {"type": "CHUNK", "release": "r2", "seq": 0},
        {"type": "END", "release": "r2"},
    ]
    assert validate_stream(stream, "r2") == 1
    reject(lambda: validate_stream(stream[:-1], "r2"))
    reject(lambda: validate_stream(stream, "r1"))
    reject(lambda: validate_stream(stream + [stream[1]], "r2"))
    reject(lambda: validate_stream([stream[0], dict(stream[1], seq=2), stream[2]], "r2"))
    reject(lambda: validate_stream([stream[0], dict(stream[1], seq=False), stream[2]], "r2"))
    print("69: type, target version, sequence, missing terminal and post-terminal events checked")

    user_value = "demo; should-remain-one-argument"
    process = subprocess.run(
        [sys.executable, "-c", "import json,sys;print(json.dumps({'argv':sys.argv[1:]}))", user_value],
        shell=False, capture_output=True, text=True, check=True,
    )
    assert json.loads(process.stdout)["argv"] == [user_value]
    assert cli_state(0, '{"schema":1,"status":"SUBMITTED"}') == "WAIT"
    assert cli_state(0, '{"schema":1,"status":"SUCCEEDED"}') == "VERIFY"
    assert cli_state(None, "") == "UNKNOWN"
    reject(lambda: cli_state(0, '{"schema":2,"status":"SUCCEEDED"}'))
    reject(lambda: cli_state(0, '{"schema":true,"status":"SUCCEEDED"}'))
    reject(lambda: cli_state(0, '[]'))
    reject(lambda: cli_state(0, 'not JSON'))
    print("70: argv is not shell code; CLI submit/success/unknown differ; schema guarded")

    fixed = FixtureProvider({("tenant-1", "get_stock", "A"): 0})
    assert fixed.call("tenant-1", "get_stock", "A") == 0
    latest_stock = 5
    assert latest_stock > 0 and not fixed.call("tenant-1", "get_stock", "A") > 0
    reject(lambda: fixed.call("tenant-2", "get_stock", "A"))
    reject(lambda: fixed.call("tenant-1", "deploy", "A"))
    mapping = {"shopA": "tenant-1", "shopB": "tenant-2"}
    assert mapping["shopA"] != mapping["shopB"] and mapping["shopA"] == mapping["shopA"]
    print("71: frozen fixture differs from changed live data; tenant mismatch/write/no-fixture rejected")

    ledger = JobLedger()
    ledger.submit("job-r7-s2-a3", "H1")
    ledger.submit("job-r7-s2-a3", "H1")
    reject(lambda: ledger.submit("job-r7-s2-a3", "H2"))
    ledger.current[2] = 3
    reject(lambda: ledger.accept(2, 2, True, True))
    reject(lambda: ledger.accept(2, 3, True, False))
    assert ledger.accept(2, 3, True, True)
    assert not ledger.accept(2, 3, True, True)
    print("72: idempotent create, input conflict, stale attempt, missing manifest and duplicate completion checked")

    for total in range(101):
        for pieces in range(1, 21):
            plan = ranges(total, pieces)
            seen = [row for lo, hi in plan for row in range(lo, hi)]
            assert seen == list(range(total))
            assert all(lo < hi for lo, hi in plan)
    parts = {0: {"source": "S1/session7", "object_complete": True}}
    reject(lambda: require_manifest("S1/session7", [0, 1], parts))
    reject(lambda: require_manifest("S2/session8", [0], parts))
    assert require_manifest("S1/session7", [0], parts)
    print("73: 2020 range plans cover once; mixed session/missing shard rejected")
    print("All local project checks passed; no production integration or security certification.")


if __name__ == "__main__":
    main()
