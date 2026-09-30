"""편집에 넣기 전 클립 전처리 — 구간 자르기·속도(슬로모션·속도 램프)·30fps 맞춤·색·리프레임을 한 번에 (2026-09-27)

  python clip_prep.py <준비.json> <출력폴더>

준비.json: {"fps":30, "size":[1080,1920], "grade":"warm",
  "clips":[{"name":"거실", "src":"...mp4", "in":1.2, "out":3.4,          # 원본 기준 실제 초
            "speed":0.5,                                               # 한 가지 속도(0.5 = 절반 속도 슬로모션)
            "ramp":[[0,0.5],[0.7,0.5],[1.0,1.6]],                       # 또는 속도 램프: [원본 구간 비율, 속도] 점들(큐빅처럼 잘게 나눔)
            "zoom":1.08, "pan":[0,-0.03],                               # 리프레임: 확대 배율, 가로·세로 이동(화면 비율, 위가 -)
            "grade":"warm"}]}
- 59.94fps 짐벌 소스를 Blender 에 그대로 올리면 한 프레임=한 프레임으로 **의도하지 않은 절반 속도**가 된다(09-27 확인).
  그래서 여기서 속도를 정해 30fps 고정으로 **미리 변환**하고, Blender 에는 결과만 올린다(06-편집기술심화 §3-② 「먼저 컨폼」)
- 속도 램프는 원본 구간을 잘게(8~12조각) 나눠 조각마다 속도를 바꿔 이어 붙인다 → 한 컷 안에서 빨라졌다 느려짐
- 색: warm = 화이트밸런스 살짝 따뜻하게·대비 약간·채도 1.1·하이라이트 보호(06 §5, 과하지 않게)
- 30fps 맞춤은 fps(프레임 버리기·복제) 대신 framerate(이웃 프레임 섞기)로 한다. 0.65배처럼 나누어떨어지지 않는 속도에서
  프레임을 불규칙하게 버리면 7·7·12 식으로 움직임이 튀어 「끊겨」 보인다(09-27 v3 측정, 운영자 「전환전 끊기는거」)
- 원음은 버린다(운영자 09-27 「말소리들리는것도 별로」)
"""
import json, os, subprocess, sys

GRADES = {
    "warm": "eq=contrast=1.05:brightness=0.015:saturation=1.10:gamma=1.02,colorbalance=rs=0.035:gs=0.01:bs=-0.035:rh=0.01:bh=-0.02",
    "neutral": "eq=contrast=1.03:saturation=1.05",
    "none": "null",
}


def probe_fps(path):
    s = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
                       capture_output=True, text=True).stdout.strip()
    a, b = s.split("/")
    return float(a) / float(b)


def pieces(c):
    """(원본 시작, 원본 끝, 속도) 조각들"""
    a, b = c["in"], c["out"]
    if "ramp" not in c:
        return [(a, b, c.get("speed", 1.0))]
    pts = c["ramp"]
    out, n = [], 12
    for k in range(n):
        u0, u1 = k / n, (k + 1) / n
        um = (u0 + u1) / 2
        for (p0, s0), (p1, s1) in zip(pts, pts[1:]):
            if p0 <= um <= p1:
                x = (um - p0) / (p1 - p0) if p1 > p0 else 0
                x = x * x * (3 - 2 * x)                                   # 부드러운 곡선(ease)
                sp = s0 + (s1 - s0) * x
                break
        else:
            sp = pts[-1][1]
        out.append((a + (b - a) * u0, a + (b - a) * u1, sp))
    return out


def build(c, fps, size, outdir, default_grade):
    W, H = size
    z = c.get("zoom", 1.0)
    px, py = c.get("pan", [0, 0])
    grade = GRADES[c.get("grade", default_grade)]
    parts = pieces(c)
    fc = []
    for i, (a, b, sp) in enumerate(parts):
        fc.append(f"[0:v]trim=start={a:.4f}:end={b:.4f},setpts=(PTS-STARTPTS)/{sp:.4f}[p{i}]")
    fc.append("".join(f"[p{i}]" for i in range(len(parts))) + f"concat=n={len(parts)}:v=1:a=0[c]")
    cw, ch = f"iw/{z}", f"ih/{z}"
    cx, cy = f"(iw-iw/{z})/2+iw*{px}", f"(ih-ih/{z})/2+ih*{py}"
    fc.append(f"[c]framerate=fps={fps},crop={cw}:{ch}:{cx}:{cy},scale={W}:{H}:flags=lanczos,{grade},format=yuv420p[v]")
    out = os.path.join(outdir, c["name"] + ".mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c["src"], "-filter_complex", ";".join(fc), "-map", "[v]", "-an",
                    "-c:v", "libx264", "-crf", "14", "-preset", "medium", "-r", str(fps), out], check=True)
    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out], capture_output=True, text=True).stdout.strip()
    print(f"{c['name']}: 원본 {c['in']}~{c['out']}s → {float(d):.2f}s ({probe_fps(c['src']):.2f}fps 원본)")


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    outdir = sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for c in spec["clips"]:
        build(c, spec.get("fps", 30), spec.get("size", [1080, 1920]), outdir, spec.get("grade", "warm"))


if __name__ == "__main__":
    main()
