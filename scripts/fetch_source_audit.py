"""Fetch exact upstream sources and record immutable commits, hashes and symbols.

Only public GET requests are used. Downloaded source stays in .source-cache/;
the reproducible lock/report is sources/source-lock.json. Python 3.9+.
"""
import concurrent.futures
import hashlib
import json
import pathlib
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
CACHE = ROOT / ".source-cache"


def fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": "source-study/1"})
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.read()


def resolve(spec):
    ref_url = "https://api.github.com/repos/%s/git/ref/tags/%s" % (
        spec["repo"], urllib.parse.quote(spec["ref"], safe=""))
    obj = json.loads(fetch(ref_url))["object"]
    for _ in range(4):
        if obj["type"] == "commit":
            return obj["sha"]
        obj = json.loads(fetch(obj["url"]))["object"]
    raise ValueError("unresolved tag: " + spec["ref"])


def get_file(spec, commit, item):
    relative = item["path"]
    url = "https://raw.githubusercontent.com/%s/%s/%s" % (
        spec["repo"], commit, relative)
    destination = CACHE / spec["id"] / commit / relative
    try:
        data = destination.read_bytes() if destination.exists() else fetch(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not destination.exists():
            destination.write_bytes(data)
        lines = data.decode("utf-8").splitlines()
        symbols = {symbol: [i + 1 for i, line in enumerate(lines) if symbol in line]
                   for symbol in item["symbols"]}
        return {"path": relative, "sha256": hashlib.sha256(data).hexdigest(),
                "lines": len(lines), "symbols": symbols,
                "url": "https://github.com/%s/blob/%s/%s" % (
                    spec["repo"], commit, relative),
                "status": "ok" if all(symbols.values()) else "missing-symbol"}
    except Exception as error:
        return {"path": relative, "status": "error", "error": str(error)}


def main():
    specs = json.loads((ROOT / "sources/source-spec.json").read_text())
    lock_path = ROOT / "sources/source-lock.json"
    previous = json.loads(lock_path.read_text()) if lock_path.exists() else []
    known = {(entry["repo"], entry["ref"]): entry["commit"]
             for entry in previous if entry.get("commit")}
    result = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for spec in specs:
            try:
                commit = known.get((spec["repo"], spec["ref"])) or resolve(spec)
            except Exception as error:
                result.append({"id": spec["id"], "repo": spec["repo"],
                               "ref": spec["ref"], "commit": None,
                               "error": str(error), "files": []})
                print("UNRESOLVED", spec["id"], error, flush=True)
                lock_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
                continue
            files = list(pool.map(lambda item: get_file(spec, commit, item), spec["files"]))
            result.append({"id": spec["id"], "repo": spec["repo"],
                           "ref": spec["ref"], "commit": commit, "files": files})
            lock_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            print(spec["id"], spec["ref"], commit, flush=True)
            for item in files:
                if item["status"] != "ok":
                    print("  NEEDS REVIEW:", item, flush=True)
    lock_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    index = ["# 固定上游源码索引", "",
             "由 fetch_source_audit.py 从公开仓库生成。commit 为 tag 解析结果，文件哈希校验下载内容。",
             "符号行号为子串命中位置，用于定位，不保证每个命中都是方法定义。", ""]
    for spec in result:
        index.extend(["## %s · %s" % (spec["id"], spec["ref"]), "",
                      "commit: `%s`" % spec.get("commit"), "",
                      "| 文件 | 入口符号 | 校验 |", "|---|---|---|"])
        for item in spec["files"]:
            label = item["path"].replace("|", "\\|")
            if item.get("url"):
                label = "[%s](%s)" % (label, item["url"])
            entries = []
            for symbol, lines in item.get("symbols", {}).items():
                entries.append("%s: %s" % (symbol, ", ".join(map(str, lines[:8]))))
            index.append("| %s | %s | %s |" % (label, "; ".join(entries), item["status"]))
        index.append("")
    (ROOT / "sources/README.md").write_text("\n".join(index) + "\n")
    failures = sum(not spec.get("commit") for spec in result)
    failures += sum(item["status"] != "ok" for spec in result for item in spec["files"])
    print("FILES:", sum(len(spec["files"]) for spec in result), "REVIEW:", failures)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
