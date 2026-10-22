"""Fetch the supplemental immutable source lock without rewriting old indexes."""

import concurrent.futures
import json
from pathlib import Path

from fetch_source_audit import get_file


ROOT = Path(__file__).resolve().parents[1]


def main():
    lock = json.loads((ROOT / "sources/dubbo-lifecycle-lock.json").read_text())
    assert lock["repo"] == "apache/dubbo"
    assert lock["commit"] == "1dd6a4aaa8816cf3f1585769dfff4f325e4ecd15"
    spec = {"id": "dubbo", "repo": lock["repo"], "ref": lock["ref"]}

    def check(expected):
        actual = get_file(spec, lock["commit"], {
            "path": expected["path"], "symbols": list(expected["symbols"])
        })
        if actual["status"] != "ok" or actual["sha256"] != expected["sha256"]:
            raise RuntimeError("Supplemental source check failed: " + expected["path"])
        if actual["symbols"] != expected["symbols"]:
            raise RuntimeError("Symbol locations changed: " + expected["path"])
        return actual["path"]

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        paths = list(pool.map(check, lock["files"]))
    print(f"{len(paths)} locked Dubbo source files available; hashes and symbols match.")
    print("Original source-lock.json and source indexes were not rewritten.")


if __name__ == "__main__":
    main()
