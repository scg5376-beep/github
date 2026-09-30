"""시안 영상용 임시 음원을 직접 합성한다 — 효과음과 배경음(저작권 없음) (2026-09-27)

  python sfx_make.py <출력폴더> [배경음 길이초=32]

만드는 것(48kHz 스테레오 wav):
  whoosh.wav  0.7초  밀어내기·휙 전환에 붙이는 바람 소리(잡음을 훑는 대역 필터 + 좌→우 이동)
  boom.wav    2.2초  장면이 크게 바뀌는 곳의 쿵(저음 하강 + 짧은 타격)
  hit.wav     1.2초  끝 화면 같은 마무리 타격(쿵 + 밝은 금속성 윗소리)
  riser.wav   2.5초  끝 화면 앞에서 차오르는 소리(잡음·음 높이가 함께 오름)
  shimmer.wav 1.6초  빛 번짐 전환에 붙이는 반짝임(높은 배음 종소리)
  bed.wav     N초    D장조 패드 화음(4초마다 D-A-Bm-G) + 잔향. 조용한 바탕
  arp.wav     12초   견본주택 구간에 겹치는 8분음 뜯는 소리(같은 화음 진행)
실제 광고에는 쓰지 않는다: 시안 표기 「임시 음원」과 함께만.
"""
import sys
from pathlib import Path
import numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
from scipy.io import wavfile

SR = 48000
rng = np.random.default_rng(7)


def t(sec):
    return np.arange(int(sec * SR)) / SR


def env(n, a, r, curve=3.0):
    """a초 올라가고 r초 동안 지수로 내려가는 모양"""
    x = np.ones(n)
    na = max(1, int(a * SR))
    x[:na] = np.linspace(0, 1, na)
    nr = min(n, int(r * SR))
    x[-nr:] *= np.exp(-curve * np.linspace(0, 1, nr))
    return x


def bp(x, lo, hi, order=2):
    return sosfilt(butter(order, [lo, hi], "bandpass", fs=SR, output="sos"), x)


def lp(x, f, order=2):
    return sosfilt(butter(order, f, "lowpass", fs=SR, output="sos"), x)


def reverb(x, sec=2.2, mix=0.35):
    n = int(sec * SR)
    ir = rng.standard_normal(n) * np.exp(-5 * np.linspace(0, 1, n))
    ir = lp(ir, 6000)
    wet = fftconvolve(x, ir)[: len(x)]
    wet /= (np.abs(wet).max() + 1e-9)
    return (1 - mix) * x / (np.abs(x).max() + 1e-9) + mix * wet


def stereo(l, r=None):
    r = l if r is None else r
    return np.stack([l, r], 1)


def save(path, x, peak=0.89):
    x = x / (np.abs(x).max() + 1e-9) * peak
    wavfile.write(str(path), SR, (x * 32767).astype(np.int16))


def whoosh():
    n = int(0.7 * SR)
    noise = rng.standard_normal(n)
    out = np.zeros(n)
    blk = 1024
    for i in range(0, n, blk):                                  # 대역을 400Hz→3kHz→800Hz 로 훑는다
        p = i / n
        c = 400 + 2600 * np.sin(np.pi * p)
        seg = noise[max(0, i - 2048): i + blk]
        out[i:i + blk] = bp(seg, c * 0.6, min(c * 1.6, 20000))[-len(out[i:i + blk]):]
    e = np.sin(np.pi * np.linspace(0, 1, n)) ** 2
    x = out * e
    pan = np.linspace(0, 1, n)
    return stereo(x * np.cos(pan * np.pi / 2), x * np.sin(pan * np.pi / 2))


def boom(sec=2.2):
    tt = t(sec)
    f = 62 * np.exp(-tt * 1.2) + 32
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * env(len(tt), 0.005, sec)
    click = lp(rng.standard_normal(len(tt)), 900) * env(len(tt), 0.001, 0.25, 8)
    return stereo(reverb(sub + 0.5 * click, 1.8, 0.25))


def hit():
    tt = t(1.2)
    b = boom(1.2)[:, 0]
    metal = sum(np.sin(2 * np.pi * f * tt) * np.exp(-tt * d) for f, d in ((1320, 5), (1980, 6), (2640, 7), (3520, 9)))
    return stereo(reverb(b + 0.18 * metal, 1.6, 0.3))


def riser(sec=2.5):
    tt = t(sec)
    p = tt / sec
    noise = bp(rng.standard_normal(len(tt)), 300, 9000) * p ** 2
    tone = np.sin(2 * np.pi * np.cumsum(180 + 700 * p ** 2) / SR) * p ** 1.5
    x = noise * 0.7 + tone * 0.35
    x[-int(0.03 * SR):] *= np.linspace(1, 0, int(0.03 * SR))
    return stereo(reverb(x, 1.2, 0.2))


def shimmer():
    tt = t(1.6)
    x = sum(np.sin(2 * np.pi * f * tt + k) * np.exp(-tt * (2 + k)) for k, f in enumerate((1760, 2217, 2637, 3520, 4435)))
    x *= env(len(tt), 0.04, 1.5)
    return stereo(reverb(x, 2.5, 0.5), reverb(np.roll(x, 480), 2.5, 0.5))


CHORDS = [(146.83, 185.00, 220.00, 293.66), (110.00, 138.59, 164.81, 220.00),   # D, A
          (123.47, 146.83, 185.00, 246.94), (98.00, 123.47, 146.83, 196.00)]    # Bm, G


def pad_voice(freqs, sec):
    tt = t(sec)
    x = np.zeros(len(tt))
    for f in freqs:
        for det in (-0.25, 0.25):                                # 살짝 어긋난 두 소리로 넓게
            ph = 2 * np.pi * (f + det) * tt
            x += np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.12 * np.sin(3 * ph)
    return lp(x, 1800) * env(len(tt), 1.2, 1.4, 2.0)


def bed(sec):
    x = np.zeros(int(sec * SR) + SR * 4)
    for k in range(int(np.ceil(sec / 4))):
        v = pad_voice(CHORDS[k % 4], 5.0)
        i = k * 4 * SR
        x[i:i + len(v)] += v
    x = x[: int(sec * SR)]
    x *= env(len(x), 1.5, 2.5, 2.0)
    l = reverb(x, 3.0, 0.45)
    return stereo(l, reverb(np.roll(x, 900), 3.0, 0.45))


def arp(sec=12.0, bpm=100):
    step = 60 / bpm / 2                                           # 8분음
    x = np.zeros(int(sec * SR) + SR)
    n = int(sec / step)
    for i in range(n):
        ch = CHORDS[int(i * step / 4) % 4]
        f = ch[[0, 2, 3, 2][i % 4]] * 2
        tt = t(0.6)
        note = (np.sin(2 * np.pi * f * tt) + 0.25 * np.sin(4 * np.pi * f * tt)) * np.exp(-tt * 7)
        s = int(i * step * SR)
        x[s:s + len(note)] += note * (0.8 if i % 2 == 0 else 0.55)
    x = x[: int(sec * SR)] * env(int(sec * SR), 0.3, 1.0, 2.0)
    return stereo(reverb(x, 1.8, 0.35), reverb(np.roll(x, 600), 1.8, 0.35))


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    L = float(sys.argv[2]) if len(sys.argv) > 2 else 32
    for name, x in (("whoosh", whoosh()), ("boom", boom()), ("hit", hit()), ("riser", riser()),
                    ("shimmer", shimmer()), ("bed", bed(L)), ("arp", arp())):
        save(out / f"{name}.wav", x)
        print(name, round(len(x) / SR, 2), "s")


if __name__ == "__main__":
    main()
