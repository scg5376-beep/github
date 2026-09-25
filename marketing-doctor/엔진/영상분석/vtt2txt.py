"""유튜브 자막(vtt)을 「시각 · 문장」 줄로 — 자동 자막의 겹치는 줄을 지운다 (2026-09-25)

  python vtt2txt.py <자막.vtt>
"""
import re, sys

lines, seen = [], set()
t = None
for raw in open(sys.argv[1], encoding="utf-8"):
    raw = raw.strip()
    m = re.match(r"(\d+):(\d+):(\d+)\.\d+ -->", raw) or re.match(r"(\d+):(\d+)\.\d+ -->", raw)
    if m:
        g = [int(x) for x in m.groups()]
        t = g[0] * 3600 + g[1] * 60 + g[2] if len(g) == 3 else g[0] * 60 + g[1]
        continue
    if not raw or raw.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or t is None:
        continue
    txt = re.sub(r"<[^>]+>", "", raw).strip()
    if txt and txt not in seen:
        seen.add(txt)
        lines.append(f"{t:>4}s  {txt}")
print("\n".join(lines))
