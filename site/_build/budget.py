# 발전 루프 예산 — 클로드 Max 5시간 창 사용률의 25%p (운영자 2026-09-17 "5시간 한도 기준으로 25%만").
# 상태줄(~/.claude/statusline.py)이 ~/.claude/statusline-rate.json 에 남기는 five_hour.used_percentage 를 읽는다.
# 사용: python budget.py --start   (「시작해」 때 기준점 저장)
#       python budget.py --check   (매 바퀴. 25%p 넘으면 종료코드 2, 주간 95% 넘어도 2)
import json, os, sys, time, datetime, pathlib

RATE = pathlib.Path(os.path.expanduser("~/.claude/statusline-rate.json"))
STATE = pathlib.Path(__file__).resolve().parents[2] / "docs/발전/예산.json"
CAP = 25.0


def read():
    d = json.loads(RATE.read_text(encoding="utf-8"))
    age = time.time() - d["at"]
    rl = d["rate_limits"]
    return rl.get("five_hour", {}), rl.get("seven_day", {}), age


def fmt(ts):
    return datetime.datetime.fromtimestamp(ts).strftime("%m-%d %H:%M") if ts else "?"


five, week, age = read()
if age > 600:
    print(f"주의: 상태줄 기록이 {age / 60:.0f}분 전 것 (상태줄이 갱신돼야 정확)")
if five.get("used_percentage") is None:
    print("5시간 값이 아직 없음 — 상태줄이 한 번 갱신된 뒤 다시"); sys.exit(1)
if "--start" in sys.argv:
    STATE.write_text(json.dumps({"start_pct": five.get("used_percentage"), "start_reset": five.get("resets_at"), "started": time.time()}, ensure_ascii=False), encoding="utf-8")
    print(f"기준점 저장: 5시간 {five.get('used_percentage')}% (창 초기화 {fmt(five.get('resets_at'))}) · 주간 {week.get('used_percentage')}% (초기화 {fmt(week.get('resets_at'))})")
    sys.exit(0)
st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else None
if not st:
    print("기준점 없음 — 먼저 --start"); sys.exit(1)
now = five.get("used_percentage") or 0
if five.get("resets_at") != st["start_reset"]:                                    # 창이 바뀌었으면 0부터 다시 센다
    used = now
else:
    used = now - (st["start_pct"] or 0)
print(f"5시간 창 사용 {used:.0f}%p / 상한 {CAP:.0f}%p (지금 {now}%, 창 초기화 {fmt(five.get('resets_at'))}) · 주간 {week.get('used_percentage')}%")
if week.get("used_percentage", 0) >= 95:
    print("주간 한도 임박 — 멈춤"); sys.exit(2)
sys.exit(2 if used >= CAP else 0)
