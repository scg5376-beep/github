"""After Effects 로 짧은 교통 모식도 애니메이션 — 노선이 그려지고 그 위로 전동차가 지나간다 (2026-09-28)

  python ae_transit.py <설정.json> <출력.mp4>

왜: 운영자 09-28 「저 지하철 노선도 이어지는거 완전 짧게 넣는거아니면 별로야 그리고 노선이생기고 지하철이 그위로 지나가는
    모형이런느낌 에펙으로 구현하는거 아니면 별로일듯해」 → 3초 안팎, 모양 레이어 선이 Trim Paths 로 그려진 뒤 전동차가 그 길을 따라 달린다.

설정.json: {"length":3.5, "fps":30, "bg":["#0d1017","#1a2230"], "push":1.06,
  "river":{"pts":[[x,y],…], "width":120, "color":"#1f4f80"},
  "lines":[{"pts":[[x,y],…], "color":"#9a5cc0", "width":16, "dash":false, "draw":[0.2,0.9]},
           {"pts":…, "dash":true, "draw":[0.8,1.9], "train":[1.4,3.1]}],     # train: 전동차가 이 선을 따라 달리는 구간(초)
  "dots":[{"at":[x,y], "t":0.9, "dashed":false, "color":"#ffffff"}],
  "under":"도심.mp4", "under_in":1.0, "under_dim":30, "under_zoom":1.0,       # 선택: 밑에 깔 영상(없으면 그러데이션 배경), river 는 생략 가능
  "labels":[{"at":[x,y], "text":"마곡", "size":44, "t":0.9, "color":"#ffffff"}]}
- 좌표는 1080×1920 화면 픽셀. 역 위치가 정해지지 않은 계획선은 점선·점선 원으로(판례 2007다59066, 단지 표시 없음)
- 단계 고지 등 글자는 ad_build 의 자막층에서 얹는다(여기서는 지명만)
"""
import json, math, os, subprocess, sys, tempfile, time

AE = r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe"
spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.abspath(sys.argv[2])
WORK = tempfile.mkdtemp(prefix="aetr_")
log_path = os.path.join(WORK, "log.txt").replace("\\", "/")
render_base = os.path.join(WORK, "transit").replace("\\", "/")


def rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


# 전동차 경로: 선 길이에 비례한 시간으로 꼭짓점마다 키
for ln in spec["lines"]:
    ln["rgb"] = rgb(ln["color"])
    if ln.get("train_color"):
        ln["train_rgb"] = rgb(ln["train_color"])
    if "train" in ln:
        p = ln["pts"]
        seg = [math.dist(p[i], p[i + 1]) for i in range(len(p) - 1)]
        tot = sum(seg)
        t0, t1 = ln["train"]
        ts, acc = [t0], 0
        for s in seg:
            acc += s
            ts.append(t0 + (t1 - t0) * acc / tot)
        ln["train_keys"] = [[t, p[i][0], p[i][1], math.degrees(math.atan2(p[min(i + 1, len(p) - 1)][1] - p[max(i - 1, 0)][1] if i == len(p) - 1 else p[i + 1][1] - p[i][1],
                                                                           (p[min(i + 1, len(p) - 1)][0] - p[max(i - 1, 0)][0]) if i == len(p) - 1 else p[i + 1][0] - p[i][0]))]
                             for i, t in enumerate(ts)]
for d in spec.get("dots", []):
    d["rgb"] = rgb(d.get("color", "#ffffff"))
for l in spec.get("labels", []):
    l["rgb"] = rgb(l.get("color", "#ffffff"))
spec["river_rgb"] = rgb(spec["river"]["color"]) if spec.get("river") else None
spec["bg_rgb"] = [rgb(c) for c in spec.get("bg", ["#0d1017", "#1a2230"])]

jsx = os.path.join(WORK, "transit.jsx")
open(jsx, "w", encoding="utf-8").write("""
app.preferences.savePrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY", 1);
var LOG = new File(%(log)s); LOG.encoding = "UTF-8"; LOG.open("w");
var S = %(spec)s;
function ease(p){ for (var i = 1; i <= p.numKeys; i++){ var e = [new KeyframeEase(0, 70)]; if (p.value instanceof Array) { e = []; for (var d = 0; d < p.value.length; d++) e.push(new KeyframeEase(0, 70)); } try { p.setTemporalEaseAtKey(i, e, e); } catch (x) {} } }
function pathLayer(comp, name, pts, color, width, dash, draw){
  var L = comp.layers.addShape(); L.name = name;
  var g = L.property("Contents").addProperty("ADBE Vector Group");
  var sh = g.property("Contents").addProperty("ADBE Vector Shape - Group");
  var s = new Shape(); var v = []; for (var i = 0; i < pts.length; i++) v.push([pts[i][0] - 540, pts[i][1] - 960]);
  s.vertices = v; s.closed = false; sh.property("Path").setValue(s);
  var st = g.property("Contents").addProperty("ADBE Vector Graphic - Stroke");
  st.property("Color").setValue(color); st.property("Stroke Width").setValue(width);
  st.property("Line Cap").setValue(2); st.property("Line Join").setValue(2);
  if (dash) { var ds = st.property("Dashes"); ds.addProperty("ADBE Vector Stroke Dash 1").setValue(width * 1.6); ds.addProperty("ADBE Vector Stroke Gap 1").setValue(width * 1.2); }
  L.property("Transform").property("Position").setValue([540, 960]);
  if (draw) { var tr = L.property("Contents").addProperty("ADBE Vector Filter - Trim"); var e = tr.property("End");
    e.setValueAtTime(0, 0); e.setValueAtTime(draw[0], 0); e.setValueAtTime(draw[1], 100); ease(e); }
  return L;
}
try {
  if (!app.project) app.newProject();   // -noui 에서는 newProject·beginSuppressDialogs 가 AE 를 죽인다(09-28 실측)
  var comp = app.project.items.addComp("transit", 1080, 1920, 1, S.length, S.fps || 30);
  var bg = comp.layers.addSolid(S.bg_rgb[0], "bg", 1080, 1920, 1, S.length);
  var ramp = bg.property("Effects").addProperty("ADBE Ramp");
  ramp.property(1).setValue([540, 0]); ramp.property(2).setValue(S.bg_rgb[1]); ramp.property(3).setValue([540, 1920]); ramp.property(4).setValue(S.bg_rgb[0]);
  if (S.under) {                                                     // 밑에 깔 실사·AI 도심 영상(운영자 09-28 「영상ai로 아파트 근처 도심을 구현해서 거기에 지하철 노선도 선을」)
    var ft = app.project.importFile(new ImportOptions(new File(S.under)));
    var U = comp.layers.add(ft); U.startTime = -(S.under_in || 0);
    var us = Math.max(1080 / ft.width, 1920 / ft.height) * 100 * (S.under_zoom || 1.0);
    U.property("Transform").property("Scale").setValue([us, us]); U.property("Transform").property("Position").setValue([540, 960]);
    var dim = comp.layers.addSolid([0, 0, 0], "dim", 1080, 1920, 1, S.length); dim.property("Transform").property("Opacity").setValue(S.under_dim == null ? 30 : S.under_dim);
  }
  var map = comp.layers.addNull(); map.name = "map"; map.property("Transform").property("Position").setValue([540, 960]);
  var sc = map.property("Transform").property("Scale"); sc.setValueAtTime(0, [100, 100]); sc.setValueAtTime(S.length, [100 * (S.push || 1.06), 100 * (S.push || 1.06)]);
  var layers = [];
  if (S.river) { var rv = pathLayer(comp, "river", S.river.pts, S.river_rgb, S.river.width, false, null); rv.property("Transform").property("Opacity").setValue(80); layers.push(rv); }
  for (var i = 0; i < S.lines.length; i++) {
    var ln = S.lines[i];
    var L = pathLayer(comp, "line" + i, ln.pts, ln.rgb, ln.width, ln.dash, ln.draw); layers.push(L);
    var gl = L.property("Effects").addProperty("ADBE Glo2"); try { gl.property("ADBE Glo2-0003").setValue(18); gl.property("ADBE Glo2-0004").setValue(1.2); } catch (x) {}
    if (ln.train_keys) {                                            // 전동차: 둥근 사각형 + 불빛
      var T = comp.layers.addShape(); T.name = "train" + i; layers.push(T);
      var tg = T.property("Contents").addProperty("ADBE Vector Group");
      var rc = tg.property("Contents").addProperty("ADBE Vector Shape - Rect"); rc.property("Size").setValue([S.train_w || 120, S.train_h || 40]); rc.property("Roundness").setValue(16);
      var fl = tg.property("Contents").addProperty("ADBE Vector Graphic - Fill"); fl.property("Color").setValue(ln.train_rgb || ln.rgb);
      var st2 = tg.property("Contents").addProperty("ADBE Vector Graphic - Stroke"); st2.property("Color").setValue([1, 1, 1]); st2.property("Stroke Width").setValue(5);
      var tp = T.property("Transform").property("Position"), trt = T.property("Transform").property("Rotation"), top = T.property("Transform").property("Opacity");
      var K = ln.train_keys;
      for (var k = 0; k < K.length; k++) { tp.setValueAtTime(K[k][0], [K[k][1], K[k][2]]); trt.setValueAtTime(K[k][0], K[k][3]); }
      for (var k = 1; k <= tp.numKeys; k++) { tp.setInterpolationTypeAtKey(k, KeyframeInterpolationType.LINEAR); trt.setInterpolationTypeAtKey(k, KeyframeInterpolationType.HOLD); }
      top.setValueAtTime(K[0][0] - 0.15, 0); top.setValueAtTime(K[0][0], 100);
      var tgl = T.property("Effects").addProperty("ADBE Glo2"); try { tgl.property("ADBE Glo2-0003").setValue(16); tgl.property("ADBE Glo2-0004").setValue(0.9); } catch (x) {}
      var mb = T; try { mb.motionBlur = true; } catch (x) {}
    }
  }
  for (var d = 0; d < (S.dots || []).length; d++) {
    var D = S.dots[d]; var C = comp.layers.addShape(); layers.push(C);
    var cg = C.property("Contents").addProperty("ADBE Vector Group");
    var el = cg.property("Contents").addProperty("ADBE Vector Shape - Ellipse"); el.property("Size").setValue([D.r || 44, D.r || 44]);
    var cs = cg.property("Contents").addProperty("ADBE Vector Graphic - Stroke"); cs.property("Color").setValue(D.rgb); cs.property("Stroke Width").setValue(6);
    if (D.dashed) { var dd = cs.property("Dashes"); dd.addProperty("ADBE Vector Stroke Dash 1").setValue(8); dd.addProperty("ADBE Vector Stroke Gap 1").setValue(6); }
    else { var cf = cg.property("Contents").addProperty("ADBE Vector Graphic - Fill"); cf.property("Color").setValue([0.08, 0.1, 0.14]); cg.property("Contents").moveTo ? 0 : 0; }
    C.property("Transform").property("Position").setValue(D.at);
    var cs2 = C.property("Transform").property("Scale"); cs2.setValueAtTime(D.t, [0, 0]); cs2.setValueAtTime(D.t + 0.25, [115, 115]); cs2.setValueAtTime(D.t + 0.4, [100, 100]);
  }
  for (var l = 0; l < (S.labels || []).length; l++) {
    var B = S.labels[l]; var t = comp.layers.addText(B.text); layers.push(t);
    var td = t.property("Source Text").value; td.resetCharStyle(); td.font = B.font || "Pretendard-SemiBold"; td.fontSize = B.size || 44;
    td.fillColor = B.rgb; td.justification = ParagraphJustification.CENTER_JUSTIFY; t.property("Source Text").setValue(td);
    t.property("Transform").property("Position").setValue([B.at[0], B.at[1] + (B.size || 44) * 0.35]);
    if (B.rot) t.property("Transform").property("Rotation").setValue(B.rot);
    var o = t.property("Transform").property("Opacity"); o.setValueAtTime(B.t || 0, 0); o.setValueAtTime((B.t || 0) + 0.35, 100);
    var ds = t.property("Effects").addProperty("ADBE Drop Shadow"); ds.property("ADBE Drop Shadow-0002").setValue(120); ds.property("ADBE Drop Shadow-0005").setValue(12);
  }
  for (var q = 0; q < layers.length; q++) layers[q].parent = map;
  comp.motionBlur = true;
  var rq = app.project.renderQueue.items.add(comp);
  rq.outputModule(1).applyTemplate("H.264 - 렌더링 일치 설정 - 40Mbps");
  rq.outputModule(1).file = new File(%(out)s);
  LOG.writeln("layers " + layers.length);
  app.project.renderQueue.render();
  LOG.writeln("render done");
} catch (e) { LOG.writeln("ERROR " + e.toString() + " line " + e.line); }
LOG.close();
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.quit();
""" % {"log": json.dumps(log_path), "spec": json.dumps(spec, ensure_ascii=False), "out": json.dumps(render_base)})

proc = subprocess.Popen([AE, "-noui", "-r", jsx], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0, done_at = time.time(), None
while proc.poll() is None:
    time.sleep(3)
    txt = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else ""
    if ("render done" in txt or "ERROR" in txt) and done_at is None:
        done_at = time.time()
    if (done_at and time.time() - done_at > 30) or time.time() - t0 > 900:
        subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        break
subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # AE 가 남지 않게: 실행기만 끝나고 AfterFX 본체가 8GB 를 쥔 채 남던 문제(09-28)
log = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else "(로그 없음)"
print(log.strip())
cands = [f for f in os.listdir(WORK) if f.startswith("transit.") or f.startswith("transit_")]
cands = [f for f in os.listdir(WORK) if f.startswith("transit") and not f.endswith(".jsx")]
if "render done" not in log or not cands:
    raise SystemExit("AE 렌더 실패: " + WORK)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, cands[0]), "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p",
                "-r", str(spec.get("fps", 30)), "-an", OUT], check=True)
print("AE TRANSIT", OUT)
