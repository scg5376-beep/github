"""After Effects 로 자막·타이틀 층을 만든다 — title_render.py 와 같은 자막.json 을 받아 투명 배경 .mov 로 (2026-09-28)

  python ae_titles.py <자막.json> <출력.mov> [--keep]

왜: 운영자 09-28 「고급진 이미지 연출할때 저 두가지 프로그램이 유용할텐데」 → AE 실측(11-AE프리미어자동화 §6)에서
    스크립트 무인 실행·한글 글꼴·글자 애니메이터·CC Light Sweep·Glow 가 되는 것을 확인. PIL 로는 어려운
    한 글자씩 올라오는 키네틱·빛 스치기·은은한 글로우를 AE 에 맡긴다. 결과는 blender_cut 의 title_layer 로 얹는다.

자막.json 은 title_render.py 형식 그대로. 스타일에 아래 키를 더 쓸 수 있다
  anim: punch(박히기) | fade | rise(한 글자씩 아래에서) | track(자간이 좁혀지며) | mask(짧게 튀어 오름) | type(한 글자씩 타자)
  sweep: true  → CC Light Sweep 이 글자 위를 한 번 훑는다(끝 화면 단지명 등)
  glow: 0~1    → 은은한 Glow
  ae_font: "Pretendard-Black" 처럼 PostScript 이름을 직접 줄 때(없으면 font 파일 이름에서 추정)
- 글꼴은 사용자 글꼴로 설치된 것만 AE 가 쓴다(Pretendard 전 굵기·Playfair·Cormorant·나눔명조·고운바탕, 09-28 설치)
- 출력 템플릿은 한국어판 이름 「고품질(알파 포함)」. 영문 이름으로는 못 찾는다(실측)
"""
import json, os, re, subprocess, sys, tempfile

AE = r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe"
spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.abspath(sys.argv[2])
W, H = spec.get("size", [1080, 1920])
FPS, LEN = spec.get("fps", 30), spec["length"]
STY = spec["styles"]
WORK = tempfile.mkdtemp(prefix="aet_")


def ps_name(st):
    if st.get("ae_font"):
        return st["ae_font"]
    b = os.path.splitext(os.path.basename(st["font"]))[0]
    fixed = {"PlayfairDisplay": "PlayfairDisplay-Regular", "CormorantGaramond": "CormorantGaramond-Regular",
             "NanumMyeongjo-Bold": "NanumMyeongjoBold", "NanumMyeongjo-ExtraBold": "NanumMyeongjoExtraBold",
             "NotoSerifKR[wght]": "NanumMyeongjo"}
    return fixed.get(b, b)


def js(s):
    return json.dumps(s, ensure_ascii=False)


def rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


lines_js = []
for idx, it in enumerate(spec["items"]):
    rows = it.get("lines") or [[t, it["style"]] for t in it["text"].split("\n")]
    sts = [STY[s] for _, s in rows]
    heights = [st["size"] * st.get("lead", 1.25) for st in sts]
    total = sum(heights)
    y0 = it["at"][1] * H - total / 2
    base = STY[rows[0][1]]
    for k, ((text, sname), st) in enumerate(zip(rows, sts)):
        cy = y0 + sum(heights[:k]) + heights[k] / 2
        align = st.get("align", base.get("align", "center"))
        x = it["at"][0] * W
        y = cy + st["size"] * 0.36                                 # 글자 기준선(가운데 → 기준선 보정)
        anim = it.get("anim", st.get("anim", base.get("anim", "fade")))
        tin, tout = it.get("in", st.get("in", 0.4)), it.get("out", st.get("out", 0.3))
        lines_js.append({
            "t": text, "s": it["start"] + k * 0.08, "e": it["end"], "font": ps_name(st), "size": st["size"],
            "track": st.get("track", 0) * 1000, "color": rgb(st.get("color", "#ffffff")), "align": align,
            "x": x, "y": y, "anim": anim, "tin": tin, "tout": tout, "shadow": st.get("shadow", 0.4),
            "op": st.get("opacity", 1.0) * 100, "sweep": bool(st.get("sweep") or it.get("sweep")),
            "glow": st.get("glow", 0), "lh": st["size"]})

jsx = os.path.join(WORK, "titles.jsx")
render_base = os.path.join(WORK, "titles_ae").replace("\\", "/")
log_path = os.path.join(WORK, "log.txt").replace("\\", "/")
open(jsx, "w", encoding="utf-8").write("""
app.preferences.savePrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY", 1);
var LOG = new File(%(log)s); LOG.encoding = "UTF-8"; LOG.open("w");
function L(s){ LOG.writeln(s); }
function ease(p){ for (var i = 1; i <= p.numKeys; i++){ var e = [new KeyframeEase(0, 75)]; if (p.value instanceof Array) { e = []; for (var d = 0; d < p.value.length; d++) e.push(new KeyframeEase(0, 75)); }
  try { p.setTemporalEaseAtKey(i, e, e); } catch (x) {} } }
try {
  if (!app.project) app.newProject();   // -noui 에서는 newProject·beginSuppressDialogs 가 AE 를 죽인다(09-28 실측)
  var comp = app.project.items.addComp("titles", %(W)d, %(H)d, 1, %(LEN)f, %(FPS)d); comp.motionBlur = true;
  var ROWS = %(rows)s;
  for (var r = 0; r < ROWS.length; r++) {
    var R = ROWS[r];
    var lay = comp.layers.addText(R.t);
    var src = lay.property("Source Text"); var td = src.value;
    td.resetCharStyle(); td.font = R.font; td.fontSize = R.size; td.fillColor = R.color; td.tracking = R.track;
    td.applyStroke = false; td.justification = (R.align == "left") ? ParagraphJustification.LEFT_JUSTIFY : ParagraphJustification.CENTER_JUSTIFY;
    src.setValue(td);
    lay.property("Transform").property("Position").setValue([R.x, R.y]);
    lay.inPoint = R.s; lay.outPoint = R.e;
    var op = lay.property("Transform").property("Opacity");
    if (R.anim == "punch") {                                           // 화면 안으로 「박히기」: 살짝 크게 → 0.12초에 제자리, 끝은 칼같이(운영자 09-28)
      op.setValueAtTime(R.s, 0); op.setValueAtTime(R.s + 0.04, R.op); op.setValueAtTime(R.e - 0.001, R.op); op.setValueAtTime(R.e, 0);
      for (var q = 1; q <= op.numKeys; q++) op.setInterpolationTypeAtKey(q, KeyframeInterpolationType.HOLD, KeyframeInterpolationType.HOLD);
      op.setInterpolationTypeAtKey(1, KeyframeInterpolationType.LINEAR, KeyframeInterpolationType.LINEAR);
      var sc = lay.property("Transform").property("Scale"); sc.setValueAtTime(R.s, [124, 124]); sc.setValueAtTime(R.s + 0.08, [97, 97]); sc.setValueAtTime(R.s + 0.14, [100, 100]); ease(sc);
      lay.motionBlur = true;
    } else {
    op.setValueAtTime(R.s, 0); op.setValueAtTime(R.s + Math.min(R.tin, 0.25), R.op);
    op.setValueAtTime(R.e - R.tout, R.op); op.setValueAtTime(R.e, 0); ease(op); }
    if (R.anim == "rise" || R.anim == "mask" || R.anim == "type" || R.anim == "track") {
      var an = lay.property("Text").property("Animators").addProperty("ADBE Text Animator");
      var sel = an.property("Selectors").addProperty("ADBE Text Selector");
      var props = an.property("Properties");
      if (R.anim == "rise") { props.addProperty("ADBE Text Position 3D").setValue([0, R.lh * 0.55, 0]); props.addProperty("ADBE Text Opacity").setValue(0); }
      if (R.anim == "mask") { props.addProperty("ADBE Text Position 3D").setValue([0, R.lh * 0.3, 0]); props.addProperty("ADBE Text Opacity").setValue(0); }
      if (R.anim == "type") { props.addProperty("ADBE Text Opacity").setValue(0); }
      if (R.anim == "track") { props.addProperty("ADBE Text Tracking Amount").setValue(260); props.addProperty("ADBE Text Opacity").setValue(0); }
      var stp = sel.property("ADBE Text Percent Start");
      stp.setValueAtTime(R.s, 0); stp.setValueAtTime(R.s + R.tin * (R.anim == "track" ? 1.6 : 1.9), 100); ease(stp);
      try { sel.property("ADBE Text Range Advanced").property("ADBE Text Levels Max Ease").setValue(R.anim == "type" ? 0 : 60); } catch (x) {}
    }
    var fx = lay.property("Effects");
    if (R.shadow > 0) { var ds = fx.addProperty("ADBE Drop Shadow");
      ds.property("ADBE Drop Shadow-0002").setValue(R.shadow * 200); ds.property("ADBE Drop Shadow-0004").setValue(R.lh * 0.05);
      ds.property("ADBE Drop Shadow-0005").setValue(R.lh * 0.35); }
    if (R.glow > 0) { var gl = fx.addProperty("ADBE Glo2"); try { gl.property("ADBE Glo2-0003").setValue(R.lh * 0.5); gl.property("ADBE Glo2-0004").setValue(R.glow * 1.2); } catch (x) {} }
    if (R.sweep) { var sw = fx.addProperty("CC Light Sweep");
      var c = sw.property(1); var t0 = R.s + R.tin + 0.2, t1 = Math.min(R.e - 0.3, t0 + 1.6);
      c.setValueAtTime(t0, [R.x - 700, R.y]); c.setValueAtTime(t1, [R.x + 700, R.y]);
      try { sw.property(3).setValue(Math.max(30, R.lh * 0.6)); sw.property(5).setValue(70); } catch (x) {} }
  }
  var rq = app.project.renderQueue.items.add(comp);
  var om = rq.outputModule(1);
  om.applyTemplate("고품질(알파 포함)");
  om.file = new File(%(out)s);
  L("rows " + ROWS.length);
  app.project.renderQueue.render();
  L("render done");
} catch (e) { L("ERROR " + e.toString() + " line " + e.line); }
LOG.close();
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.quit();
""" % {"log": js(log_path), "W": W, "H": H, "LEN": LEN, "FPS": FPS, "rows": js(lines_js), "out": js(render_base)})

proc = subprocess.Popen([AE, "-noui", "-r", jsx], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0, done_at = __import__("time").time(), None                     # 렌더가 끝났는데 AE 가 종료에서 멈추면(09-28 실측) 30초 뒤 강제 종료
while proc.poll() is None:
    __import__("time").sleep(3)
    txt = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else ""
    if ("render done" in txt or "ERROR" in txt) and done_at is None:
        done_at = __import__("time").time()
    if (done_at and __import__("time").time() - done_at > 30) or __import__("time").time() - t0 > 1800:
        subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        break
subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # AE 가 남지 않게: 실행기만 끝나고 AfterFX 본체가 8GB 를 쥔 채 남던 문제(09-28)
log = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else "(로그 없음)"
print(log.strip())
cands = [f for f in os.listdir(WORK) if f.startswith("titles_ae")]
if "render done" not in log or not cands:
    raise SystemExit("AE 렌더 실패: " + WORK)
src = os.path.join(WORK, cands[0])
# blender_cut 이 읽는 PNG 코덱 .mov(알파 유지)로 바꾼다
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "png", "-pix_fmt", "rgba", "-r", str(FPS), OUT], check=True)
print("AE TITLES", OUT, "←", cands[0])
if "--keep" not in sys.argv:
    try:
        os.remove(src)
    except OSError:
        pass
