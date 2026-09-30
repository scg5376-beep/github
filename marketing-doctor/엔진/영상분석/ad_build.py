"""광고 시안 한 편을 끝까지 만든다 — 자막층·배경음·컷 조립·TTS 판까지 (2026-09-28)

  python ad_build.py <편.json> [--only notts|tts] [--still 3.2,10.5]

편.json: {"name":"V1", "length":38, "fps":30, "out_dir":"…/납품",
  "sets":"…/서체/세트.json", "set":"④",                         # 서체 세트(08-자막타이포 §4)
  "titles_engine":"ae",                                           # 선택: After Effects 로 자막층(키네틱·빛 스치기·글로우), 없으면 PIL
  "clips":[…blender_cut 컷 형식…], "overlays":[…],
  "titles":[{"start":0.1,"end":2,"style":"hook","text":"집이 너무 좁아!!","at":[x,y]?}],
  "styles_extra":{"end_dark":{"base":"end_name","color":"#1d1b19","shadow":0}},   # 편 전용 스타일(선택)
  "notices":[{"start":0,"end":5,"text":"…·…"}],                   # 법정 고지 — 「·」 에서 알아서 줄바꿈
  "ai":[{"start":0,"end":8,"text":"AI로 만든 연출 영상"}],          # 왼쪽 아래 작고 옅게(운영자 09-28)
  "bgm":{"f":"…mp3","in":0,"vol":0.55,"fade_in":0.2,"fade_out":1.6,"gain_db":0},   # gain_db: 작게 녹음된 곡 키우기
  "sfx_dir":"…/음원2/효과음/", "sfx":[{"t":8.0,"f":"whoosh/….mp3","vol":0.4}],
  "narration":{"dir":"…/TTS/V1","lines":[{"t":0.1,"f":"00.wav"}],"vol":1.0,"duck_db":-12}}

만드는 것: <name>_TTS없음.mp4 · <name>_TTS.mp4
- 자막·고지·AI 표기는 전부 title_render 로 그린 투명 층 한 장(blender_cut "title_layer")
- 배경음은 편 길이에 맞춰 자르고 끝을 서서히 줄인다(음악이 뚝 끊기지 않게)
- TTS 판은 TTS없음 판의 소리(배경음+효과음)를 내레이션이 나올 때만 낮춘(sidechain) 뒤 내레이션을 얹는다 — 화면은 한 번만 렌더
- 내레이션 줄이 겹치면 뒤 줄을 밀고, 편 길이를 넘으면 경고한다(글자보다 말이 길면 대본을 고친다)
"""
import json, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER = os.path.expandvars(r"%LOCALAPPDATA%\Programs\blender\blender-5.2.1-windows-x64\blender.exe")
spec = json.load(open(sys.argv[1], encoding="utf-8"))
ONLY = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else ""
NAME, LEN, FPS = spec["name"], spec["length"], spec.get("fps", 30)
OUT = spec["out_dir"]
WORK = os.path.join(OUT, "_work", NAME)
os.makedirs(WORK, exist_ok=True)


def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p],
                                capture_output=True, text=True).stdout or 0)


def wrap_notice(text, size, width_px=930):
    """고지를 「·」 조각 단위로 줄바꿈(한 줄에 대략 width_px 안)"""
    per_line = int(width_px / (size * 0.98))
    parts, lines, cur = text.split("·"), [], ""
    for p in parts:
        cand = p if not cur else cur + "·" + p
        if len(cand) <= per_line:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = p
    lines.append(cur)
    return "\n".join(lines)


# ── 1. 자막층 ──
sets = json.load(open(spec["sets"], encoding="utf-8"))[spec["set"]]
for k, v in spec.get("styles_extra", {}).items():                   # 편에서만 쓰는 스타일: {"새이름": {"base":"end_name", "color":"#1d1b19", …}}
    sets[k] = {**sets[v.get("base", k)], **{kk: vv for kk, vv in v.items() if kk != "base"}}
styles = {k: {kk: vv for kk, vv in v.items() if kk != "at"} for k, v in sets.items()}
items = []
for t in spec.get("titles", []):
    it = dict(t)
    it.setdefault("at", sets[t["style"]]["at"])
    if "lines" in it:
        it["lines"] = [[a, b] for a, b in it["lines"]]
    items.append(it)
for n in spec.get("notices", []):
    items.append({"start": n["start"], "end": n["end"], "style": "notice", "text": wrap_notice(n["text"], sets["notice"]["size"]),
                  "at": n.get("at", sets["notice"]["at"])})
for a in spec.get("ai", []):
    items.append({"start": a["start"], "end": a["end"], "style": "ai", "text": a["text"], "at": sets["ai"]["at"]})
tl_json, tl_mov = os.path.join(WORK, "titles.json"), os.path.join(WORK, "titles.mov")
json.dump({"fps": FPS, "length": LEN, "size": [1080, 1920], "styles": styles, "items": items},
          open(tl_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if ONLY != "tts":
    engine = "ae_titles.py" if spec.get("titles_engine") == "ae" else "title_render.py"   # "ae" = After Effects 로 자막층(09-28)
    subprocess.run([sys.executable, os.path.join(HERE, engine), tl_json, tl_mov], check=True)

# ── 2. 배경음(편 길이에 맞춰 자르고 끝 페이드) ──
bg = spec["bgm"]
bgm_wav = os.path.join(WORK, "bgm.wav")
fo = bg.get("fade_out", 1.6)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(bg.get("in", 0)), "-i", bg["f"], "-t", str(LEN),
                "-af", f"volume={bg.get('gain_db', 0)}dB,afade=t=in:st=0:d={bg.get('fade_in', 0.15)},afade=t=out:st={LEN - fo}:d={fo},aresample=48000",
                "-ac", "2", bgm_wav], check=True)

# ── 3. 컷 조립 → TTS없음 판 ──
cut = {"fps": FPS, "length": LEN, "clips": spec["clips"], "texts": [], "text_box": False,
       "overlays": spec.get("overlays", []), "title_layer": tl_mov,
       "sfx_dir": spec.get("sfx_dir", ""), "sfx": spec.get("sfx", []),
       "bgm": [{"t": 0, "f": bgm_wav, "vol": bg.get("vol", 0.55)}]}
cut_json = os.path.join(WORK, "cut.json")
json.dump(cut, open(cut_json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
notts = os.path.join(OUT, f"{NAME}_TTS없음.mp4")
if "--still" in sys.argv:
    subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_cut.py"), "--", cut_json, notts, "--still",
                    sys.argv[sys.argv.index("--still") + 1], os.path.join(WORK, "still")], check=True)
    sys.exit(0)
if ONLY != "tts":
    r = subprocess.run([BLENDER, "-b", "-P", os.path.join(HERE, "blender_cut.py"), "--", cut_json, notts],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode or not os.path.exists(notts):
        print(r.stdout[-3000:], r.stderr[-3000:])
        raise SystemExit("blender_cut 실패")
    print("TTS없음:", notts, f"{dur(notts):.2f}s")

# ── 4. TTS 판 ──
nar = spec.get("narration")
if nar and ONLY != "notts":
    lines, t_end, sched = nar["lines"], 0.0, []
    for ln in lines:
        p = os.path.join(nar["dir"], ln["f"])
        d = dur(p)
        t = max(ln["t"], t_end + 0.12)
        sched.append((t, p, d))
        t_end = t + d
        print(f"  말 {t:6.2f}~{t + d:6.2f}  {os.path.basename(p)}" + ("  ★밀림" if t > ln["t"] + 0.01 else ""))
    if t_end > LEN - 0.2:
        print(f"  ★경고: 마지막 말이 {t_end:.2f}s 에 끝남(편 길이 {LEN}s)")
    ins, fc = [], []
    for i, (t, p, d) in enumerate(sched):
        ins += ["-i", p]
        fc.append(f"[{i + 1}:a]aresample=48000,adelay={int(t * 1000)}|{int(t * 1000)},volume={nar.get('vol', 1.0)}[n{i}]")
    k = len(sched)
    fc.append("".join(f"[n{i}]" for i in range(k)) + f"amix=inputs={k}:normalize=0,apad,atrim=0:{LEN}[nar]")
    fc.append("[nar]asplit=2[nar1][nar2]")
    ratio = 10 ** (-nar.get("duck_db", -12) / 20)                       # -12dB ≈ 4배
    fc.append(f"[0:a]aresample=48000[bed];[bed][nar1]sidechaincompress=threshold=0.02:ratio={ratio:.1f}:attack=15:release=350:makeup=1[duck]")
    fc.append("[duck][nar2]amix=inputs=2:normalize=0,alimiter=limit=0.95[a]")
    tts = os.path.join(OUT, f"{NAME}_TTS.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", notts, *ins, "-filter_complex", ";".join(fc),
                    "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
                    "-movflags", "+faststart", "-t", str(LEN), tts], check=True)
    print("TTS:", tts, f"{dur(tts):.2f}s")
