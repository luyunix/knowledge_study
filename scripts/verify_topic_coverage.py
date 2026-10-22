"""Offline topic/link/locked-source integrity check. Not a semantic correctness proof."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
paths = list(ROOT.glob('实现详解_[0-9][0-9]_*.md'))
docs = {int(p.name.split('_')[1]): p for p in paths}
assert len(paths) == len(docs), 'duplicate topic ID'
assert set(docs) == set(range(74)), sorted(docs)
for n, path in docs.items():
    text = path.read_text()
    for target in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)', text):
        if target.startswith(('https://', 'http://', '#')):
            continue
        assert (path.parent / unquote(target.split('#')[0])).exists(), (path.name, target)
    if n:
        assert len(re.findall(r'!\[[^\]]+\]\(', text)) == 1, path.name
        assert '## 自测' in text, path.name
        for ext in ('svg', 'png'):
            assert (ROOT / 'assets/deep-points' / f'{n:02d}.{ext}').stat().st_size > 100
        assert not re.search(r'面试|倪裕禄|蚂蚁|得物|working/transcripts', text), path.name
index = docs[0].read_text()
assert all(p.name in index for n, p in docs.items() if n)
locked = json.loads((ROOT / 'sources/source-lock.json').read_text())
count = 0
for repo in locked:
    for source in repo['files']:
        path = ROOT / '.source-cache' / repo['id'] / repo['commit'] / source['path']
        data = path.read_bytes()
        assert hashlib.sha256(data).hexdigest() == source['sha256'], path
        assert source['status'] == 'ok', path
        lines = data.decode('utf-8').splitlines()
        for symbol, numbers in source['symbols'].items():
            assert numbers and all(symbol in lines[n - 1] for n in numbers), (path, symbol)
        count += 1
print(f'{len(docs)-1} topics + index: images, self-checks, local links and public/private boundary passed')
print(f'{len(locked)} repositories, {count} cached files: SHA-256 and symbol lines passed')
