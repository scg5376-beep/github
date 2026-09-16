# 발전 루프 예산 — 이 프로젝트가 쓴 토큰 수로 잰다 (운영자 2026-09-17: 5시간 %는 다른 레포와 공유되니 토큰 수를 정해 두자).
# 상한 = 5시간 창의 25% 에 해당하는 환산 토큰. 앤스로픽이 창의 토큰 수를 공개하지 않아 첫 실행 때 캘리브레이션한다:
#   이 프로젝트만 돌아가는 동안 Δ토큰 / Δ(5시간 %) 를 재서 25%p 에 해당하는 토큰을 구한다 → docs/발전/예산.json 의 cap.
# 사용: python budget.py --start        「시작해」 때 기준점(토큰·5시간 %) 저장
#       python budget.py --check        매 바퀴. 기준점부터 쓴 토큰이 cap 을 넘으면 종료코드 2
#       python budget.py --calibrate    Δ5시간% 가 3 이상일 때 cap = 25 × (Δ토큰/Δ%) 로 갱신
#       python budget.py --cap N        cap 을 손으로 정한다
import json, os, sys, time, glob, datetime, pathlib

HOME = os.path.expanduser("~")
PROJ = "C--Users-USER-Desktop------"
RATE = pathlib.Path(HOME) / ".claude" / "statusline-rate.json"
STATE = pathlib.Path(__file__).resolve().parents[2] / "docs/발전/예산.json"
DEFAULT_CAP = 5_000_000                                                          # 잠정 — 캘리브레이션 전 기본값(환산 토큰)


def tokens_all():
    """이 프로젝트 모든 세션의 누적 환산 토큰(캐시 읽기 1/10). 기준점과의 차이만 쓴다."""
    tot = 0; seen = set()
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
                    msg = d.get("message") or {}; u = msg.get("usage")
                    if not u:
                        continue
                    key = msg.get("id") or d.get("uuid")
                    if key in seen:
                        continue
                    seen.add(key)
                    tot += u.get("input_tokens", 0) + u.get("output_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0) // 10
        except OSError:
            pass
    return tot


def five_pct():
    try:
        d = json.loads(RATE.read_text(encoding="utf-8"))
        return d["rate_limits"].get("five_hour", {}).get("used_percentage"), d["rate_limits"].get("five_hour", {}).get("resets_at"), d["rate_limits"].get("seven_day", {}).get("used_percentage")
    except (OSError, ValueError, KeyError):
        return None, None, None


st = json.loads(STATE.read_text(encoding="utf-8")) if STATE.exists() else {}
cap = st.get("cap", DEFAULT_CAP)
now_tok = tokens_all(); pct, reset, week = five_pct()

if "--cap" in sys.argv:
    st["cap"] = int(sys.argv[sys.argv.index("--cap") + 1]); STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    print(f"cap = {st['cap']:,}"); sys.exit(0)
if "--start" in sys.argv:
    st.update({"start_tok": now_tok, "start_pct": pct, "start_reset": reset, "started": time.time(), "cap": cap})
    STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    print(f"기준점: 토큰 {now_tok:,} · 5시간 {pct}% · 주간 {week}% · cap {cap:,}{' (잠정)' if 'calibrated' not in st else ''}"); sys.exit(0)
if "start_tok" not in st:
    print("기준점 없음 — 먼저 --start"); sys.exit(1)
used = now_tok - st["start_tok"]
dpct = (pct - st["start_pct"]) if (pct is not None and st.get("start_pct") is not None and reset == st.get("start_reset")) else None
if "--calibrate" in sys.argv:
    if dpct is None or dpct < 3:
        print(f"아직 못 잰다: Δ5시간% = {dpct} (3 이상 필요, 창이 바뀌면 다시 --start)"); sys.exit(1)
    st["cap"] = int(used / dpct * 25); st["calibrated"] = datetime.date.today().isoformat(); st["per_pct"] = int(used / dpct)
    STATE.write_text(json.dumps(st, ensure_ascii=False), encoding="utf-8")
    print(f"캘리브레이션: {used:,} 토큰 = {dpct}%p → 1%p ≈ {st['per_pct']:,} → cap(25%p) = {st['cap']:,}"); sys.exit(0)
print(f"쓴 토큰 {used:,} / cap {cap:,} ({used / cap:.0%}) · 5시간 {pct}%(Δ{dpct}) · 주간 {week}%")
if week is not None and week >= 95:
    print("주간 한도 임박 — 멈춤"); sys.exit(2)
sys.exit(2 if used >= cap else 0)
