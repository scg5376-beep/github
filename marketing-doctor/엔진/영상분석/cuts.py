"""영상 컷 분석 — 컷 전환 시점·컷 수·평균 컷 길이·첫 3초 컷 수·컷별 대표 프레임 격자 (2026-09-25)

  python cuts.py <영상.mp4> <출력폴더> [장면 임계값 0.30]

출력: <출력폴더>/<이름>.json (컷 시각·길이), <이름>-sheet.jpg (컷마다 가운데 프레임 한 장, 5열 격자, 칸 아래 번호·시각)
ffmpeg·ffprobe 가 PATH 에 있어야 한다. 임계값을 낮추면 부드러운 전환(디졸브)까지 잡지만 카메라 움직임도 컷으로 셀 수 있다.
"""
import json, re, subprocess, sys
from pathlib import Path


def probe_duration(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(p)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def scene_cuts(p, th):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(p), "-vf", f"select='gt(scene,{th})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, encoding="utf-8", errors="ignore")
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def sheet(tmp, shots, dst, cols=5):
    from PIL import Image, ImageDraw, ImageFont
    ims = [Image.open(f) for f in sorted(tmp.glob("*.jpg"))]
    if not ims:
        return
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * (w + 4) + 4, rows * (h + 4) + 4), "white")
    try:
        font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 14)
    except OSError:
        font = ImageFont.load_default()
    for i, (im, (start, length)) in enumerate(zip(ims, shots)):
        x, y = 4 + (i % cols) * (w + 4), 4 + (i // cols) * (h + 4)
        canvas.paste(im.resize((w, h)), (x, y))
        d = ImageDraw.Draw(canvas)
        label = f"{i + 1}  {start:.1f}s ({length:.1f}s)"
        d.rectangle([x, y + h - 20, x + 8 + d.textlength(label, font=font), y + h], fill="black")
        d.text((x + 4, y + h - 19), label, fill="white", font=font)
    canvas.save(dst, quality=88)


def main():
    src, out = Path(sys.argv[1]), Path(sys.argv[2])
    th = float(sys.argv[3]) if len(sys.argv) > 3 else 0.30
    out.mkdir(parents=True, exist_ok=True)
    dur = probe_duration(src)
    cuts = [c for c in scene_cuts(src, th) if 0.15 < c < dur - 0.15]
    bounds = [0.0] + cuts + [dur]
    shots = [(round(a, 2), round(b - a, 2)) for a, b in zip(bounds, bounds[1:])]
    info = {
        "file": src.name, "duration": round(dur, 2), "threshold": th,
        "shots": len(shots), "avg_shot": round(dur / len(shots), 2),
        "median_shot": sorted(s[1] for s in shots)[len(shots) // 2],
        "cuts_first3s": sum(1 for c in cuts if c <= 3.0),
        "cuts_per_10s": round(len(cuts) / dur * 10, 2),
        "shot_list": shots,
    }
    (out / f"{src.stem}.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    tmp = out / f"{src.stem}-frames"; tmp.mkdir(exist_ok=True)
    for i, (start, length) in enumerate(shots, 1):
        t = start + length / 2
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", str(src), "-frames:v", "1", "-vf", "scale=240:-2",
                        str(tmp / f"{i:03d}.jpg")], check=False)
    sheet(tmp, shots, out / f"{src.stem}-sheet.jpg")   # ffmpeg drawtext 는 fontconfig 가 없는 PC 에서 실패해 PIL 로 번호를 쓴다
    print(json.dumps({k: v for k, v in info.items() if k != "shot_list"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
