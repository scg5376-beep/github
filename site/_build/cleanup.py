# 작업 뒤 사후 정리: 이 저장소의 도구가 띄운 프로세스만 찾아 끝낸다 (docs/규칙/공통_마무리.md).
# 대상: 헤드리스 Edge(edge-shot·edge-ovf·edge-audit 프로필), 캡처·검사용 node(shot.mjs·scroll.mjs·audit.mjs·diag_shot.mjs), 8765 로컬 서버(--server 줄 때만).
# 다른 프로젝트의 node·python·코덱스는 건드리지 않는다. 사용: python cleanup.py [--server] [--dry]
import subprocess, sys, json

MINE = ["edge-shot", "edge-ovf", "edge-audit", "shot.mjs", "scroll.mjs", "scroll_open.mjs", "diag_shot.mjs", "audit.mjs", "shot_dbg.mjs"]
if "--server" in sys.argv:
    MINE.append("http.server 8765")
PS = r'''[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(msedge|node|python)\.exe$' } | Select-Object ProcessId, Name, CommandLine | ConvertTo-Json -Compress'''
raw = subprocess.run(["powershell", "-NoProfile", "-Command", PS], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
procs = json.loads(raw) if raw else []
if isinstance(procs, dict):
    procs = [procs]
hits = [p for p in procs if p.get("CommandLine") and any(k in p["CommandLine"] for k in MINE)]
for p in hits:
    print(f'{p["ProcessId"]:>6} {p["Name"]:<11} {p["CommandLine"][:110]}')
    if "--dry" not in sys.argv:
        subprocess.run(["taskkill", "/F", "/PID", str(p["ProcessId"])], capture_output=True)
print(f"정리 {len(hits)}개" + (" (미리 보기)" if "--dry" in sys.argv else ""))
others = [p for p in procs if p not in hits and p.get("CommandLine")]
if others:
    print(f"남은 다른 프로세스 {len(others)}개 (이 저장소 것 아님 — 손대지 않음)")
