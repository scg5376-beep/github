# 오늘 이 프로젝트가 쓴 토큰을 센다 (~/.claude/projects/<이 프로젝트>/*.jsonl 의 usage). 발전 루프의 예산 확인용 (docs/규칙/발전.md).
# 사용: python usage.py [--cap N] — cap 을 주면 초과 시 종료코드 2.
import json, glob, os, sys, datetime, pathlib

HOME = os.path.expanduser("~")
PROJ = "C--Users-USER-Desktop------"                                                # 이 프로젝트의 세션 폴더 이름(경로대장)
today = datetime.date.today().isoformat()
tot = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0}
seen = set()
for f in glob.glob(os.path.join(HOME, ".claude", "projects", PROJ, "*.jsonl")):
    try:
        with open(f, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if '"usage"' not in line:
                    continue
                try:
                    d = json.loads(line)
                except ValueError:
                    continue
                msg = d.get("message") or {}
                u = msg.get("usage")
                ts = str(d.get("timestamp", ""))
                try:                                                             # 기록은 UTC. 오늘은 이 컴퓨터 시각 기준
                    local = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone().date().isoformat()
                except ValueError:
                    continue
                if not u or local != today:
                    continue
                key = msg.get("id") or d.get("uuid")
                if key in seen:
                    continue
                seen.add(key)
                tot["input"] += u.get("input_tokens", 0); tot["output"] += u.get("output_tokens", 0)
                tot["cache_read"] += u.get("cache_read_input_tokens", 0); tot["cache_write"] += u.get("cache_creation_input_tokens", 0)
    except OSError:
        pass
billable = tot["input"] + tot["output"] + tot["cache_write"] + tot["cache_read"] // 10   # 캐시 읽기는 1/10 로 셈(요금 비례)
print(f"{today} 입력 {tot['input']:,} · 출력 {tot['output']:,} · 캐시쓰기 {tot['cache_write']:,} · 캐시읽기 {tot['cache_read']:,} → 환산 {billable:,}")
if "--cap" in sys.argv:
    cap = int(sys.argv[sys.argv.index("--cap") + 1])
    print(f"예산 {cap:,} 의 {billable / cap:.0%}")
    sys.exit(2 if billable > cap else 0)
