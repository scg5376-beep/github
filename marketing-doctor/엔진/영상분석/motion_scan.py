"""클립마다 카메라가 어느 쪽으로 얼마나 움직이는지 프레임 단위로 잰다 (2026-09-27)

  python motion_scan.py <영상> [<영상> ...]  → 각 영상 옆에 없고, 표준 출력에 요약 + <영상>.motion.csv

- 작은 흑백(가로 135)으로 줄여 이웃 프레임끼리 위상 상관(phase correlation)으로 가로·세로 이동(dx, dy, 픽셀/프레임)을 구하고,
  가운데와 가장자리의 밝기 차 변화로 앞뒤 이동(zoom 경향)을 어림한다
- 쓰는 곳: 움직임이 「붙어 있는」 구간(속도가 일정한 곳)을 고르고, 멈춰 가는 끝부분·출발 직후를 버린다
  (06-편집기술심화 §3-②: 「감속이 끝나기 전 프레임에서 자른다」)
- 메모리를 적게 쓰려고 ffmpeg 에서 한 프레임씩 받아 바로 버린다
"""
import csv, subprocess, sys
import numpy as np

W, H = 135, 240


def frames(path):
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-i", path, "-vf", f"scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                         stdout=subprocess.PIPE)
    n = W * H
    while True:
        b = p.stdout.read(n)
        if len(b) < n:
            break
        yield np.frombuffer(b, np.uint8).astype(np.float32)
    p.wait()


def shift(a, b):
    A, B = np.fft.fft2(a), np.fft.fft2(b)
    R = A * np.conj(B)
    R /= np.abs(R) + 1e-6
    r = np.fft.ifft2(R).real
    y, x = np.unravel_index(np.argmax(r), r.shape)
    if y > H // 2:
        y -= H
    if x > W // 2:
        x -= W
    return -x, -y


def scan(path):
    fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", path],
                         capture_output=True, text=True).stdout.strip()
    fps = fps.splitlines()[0].strip().rstrip(",") if fps else "30/1"      # 여러 줄·끝 쉼표가 오는 경우(09-28 서치 보고)
    a, b = (fps.split("/") + ["1"])[:2]
    fps = float(a) / float(b)
    win = np.outer(np.hanning(H), np.hanning(W)).astype(np.float32)
    rows, prev = [], None
    for i, f in enumerate(frames(path)):
        f = f.reshape(H, W)
        if prev is not None:
            dx, dy = shift(prev * win, f * win)
            rows.append((round(i / fps, 3), dx, dy))
        prev = f
    with open(path + ".motion.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["t", "dx", "dy"])
        w.writerows(rows)
    if not rows:
        return
    dx = np.array([r[1] for r in rows], float)
    k = max(1, int(fps / 4))
    sm = np.convolve(dx, np.ones(k) / k, mode="same")                    # 0.25초 평균
    mov = np.abs(sm) >= 0.4                                              # 가로로 움직이는 중(135px 기준)
    segs, s = [], None
    for i, m in enumerate(mov):
        if m and s is None:
            s = i
        if (not m or i == len(mov) - 1) and s is not None:
            e = i if not m else i + 1
            if (e - s) / fps >= 0.6:
                segs.append((round(s / fps, 2), round(e / fps, 2), "오른쪽" if sm[s:e].mean() > 0 else "왼쪽", round(float(np.abs(sm[s:e]).mean()), 2)))
            s = None
    print(f"{path}\n  fps {fps:.2f}, 길이 {len(rows) / fps:.1f}초, 가로로 움직이는 구간: " +
          ("; ".join(f"{a}~{b}s {d}(속도 {v})" for a, b, d, v in segs) if segs else "없음(고정·앞뒤 이동 위주)"))


if __name__ == "__main__":
    for p in sys.argv[1:]:
        scan(p)
