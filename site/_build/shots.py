# shots.txt 의 목록을 전부 캡처하고 표시까지 그린다. 사용: python shots.py [이름 ...]
import subprocess, sys, pathlib, os
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
OUT = ROOT / "img/shots"
OUT.mkdir(exist_ok=True)
only = set(sys.argv[1:])
rows = [l for l in (HERE / "shots.txt").read_text(encoding="utf-8").splitlines() if l.strip() and not l.startswith("#")]
subprocess.run("taskkill /F /IM msedge.exe", shell=True, capture_output=True)
for l in rows:
    parts = [x.strip() for x in l.split(" | ")]
    name, url, size, sels, crop = parts[:5]
    pre = parts[5] if len(parts) > 5 else ""
    if only and name not in only:
        continue
    w, h = size.split("x")
    raw = OUT / f"_{name}.png"
    r = subprocess.run(["node", str(HERE / "shot.mjs"), url, str(raw), w, h, sels, pre], capture_output=True, text=True, encoding="utf-8")
    print(name, (r.stdout or r.stderr).strip()[:300])
    subprocess.run("taskkill /F /IM msedge.exe", shell=True, capture_output=True)
    args = ["--auto", crop.split(":")[1]] if crop.startswith("auto") else ["--crop", crop]
    subprocess.run([sys.executable, "-X", "utf8", str(HERE / "mark.py"), str(raw), str(OUT / f"{name}.png"), *args], check=False)
