# 방법 글 33편을 다시 만든다(문안 = ht_*.py, 이유 = reasons.py, 캡처 = shots_map.py). 사용: python _build/howto/regen.py
import subprocess, sys, pathlib
HERE = pathlib.Path(__file__).resolve().parent
for f in ["ht_local2.py", "ht_local.py", "ht_online.py", "ht_service.py", "ht_foreign.py"]:
    r = subprocess.run([sys.executable, "-X", "utf8", str(HERE / f)], capture_output=True, text=True, encoding="utf-8")
    print(f, "ok" if r.returncode == 0 else r.stderr[-300:])
