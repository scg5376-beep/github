"""완성 영상 위에 강조 그림(카드·도장·아이콘)을 「톡」 튀어나오게 얹는다 (2026-09-28)

  python sticker_pop.py 입력.mp4 스티커.json 출력.mp4

스티커.json: {"items":[{"png":"…/stamp.png", "start":5.0, "end":6.9, "cx":0.5, "cy":0.30, "w":620}]}
  - cx·cy: 화면 비율(가운데 기준), w: 가로 픽셀(세로는 비율대로)
  - 등장: 0.15초에 0.7배 → 1.08배, 0.1초에 1.0배로 가라앉음(레퍼런스 쇼츠의 튀어나오는 도장·카드) + 알파 페이드
왜: 운영자 09-28 「단지내 어린이집 이런식으로 표현하지말고 … 이미지를 만들어서 띄워줘」 「자막이랑 강조글자가 같아서 중복」 →
    큰 글자 강조 대신 그림을 띄우고 글자는 자막 한 줄만 남긴다.
- 소리는 그대로 복사한다. 효과음은 편 설정의 sfx 에서 넣는다
"""
import json, subprocess, sys

src, spec_p, out = sys.argv[1:4]
items = json.load(open(spec_p, encoding="utf-8"))["items"]
W, H = 1080, 1920
args = ["ffmpeg", "-v", "error", "-y", "-i", src]
for it in items:
    args += ["-loop", "1", "-framerate", "30", "-t", f"{it['end'] - it['start'] + 0.2:.3f}", "-i", it["png"]]
f, last = [], "0:v"
for k, it in enumerate(items, 1):
    d = it["end"] - it["start"]
    w0 = int(it["w"])
    s = "if(lt(t,0.15),0.7+0.38*t/0.15,if(lt(t,0.25),1.08-0.08*(t-0.15)/0.1,1))"
    f.append(f"[{k}:v]format=rgba,scale=w='trunc({w0}*{s}/2)*2':h=-2:eval=frame,"
             f"fade=t=in:st=0:d=0.12:alpha=1,fade=t=out:st={max(0.2, d - 0.15):.3f}:d=0.15:alpha=1,"
             f"setpts=PTS-STARTPTS+{it['start']:.3f}/TB[s{k}]")
    cx, cy = it["cx"] * W, it["cy"] * H
    f.append(f"[{last}][s{k}]overlay=x='{cx:.0f}-w/2':y='{cy:.0f}-h/2':eval=frame:enable='between(t,{it['start']:.3f},{it['end']:.3f})'[v{k}]")
    last = f"v{k}"
args += ["-filter_complex", ";".join(f), "-map", f"[{last}]", "-map", "0:a?", "-c:v", "libx264", "-crf", "16", "-preset", "medium",
         "-pix_fmt", "yuv420p", "-r", "30", "-c:a", "copy", "-movflags", "+faststart", out]
subprocess.run(args, check=True)
print("STICKERS", len(items), "→", out)
