"""After Effects 로 큰 그림(단면 조감·배치도) 위를 카메라가 천천히 옮겨 다니며 구역을 하나씩 밝혀 보여 준다 → 1080×1920 mp4 (2026-09-28)

  python ae_tour.py <투어.json> <출력.mp4>

왜: 운영자 09-28 「pdf파일 움직이면서 강조하는게 아니라 ai로 구현한 엄청 큰 커뮤니티 시설을 움직이면서 하나하나 강조하면서 보여주는 그런 생동감」
    → 그림을 띄우지 않고 화면 전체로 쓴다. 카메라(위치·확대)가 멈추는 곳마다 그 구역만 불이 켜지듯 밝아지고 나머지는 살짝 어두워지며,
       이름표는 그 자리에 붙어 카메라와 함께 움직인다(떠다니지 않음).

투어.json: {"img":"cutaway.png", "length":7.0, "fps":30,
  "stops":[{"t":0.0, "x":0.5, "y":0.5, "zoom":1.0},                      # x·y 그림 비율(0~1), zoom 1 = 화면 높이에 맞춤
           {"t":1.2, "x":0.30, "y":0.62, "zoom":2.2, "hi":[0.30,0.62,0.10], "tag":"실내골프"}, …]}
  - hi: [x, y, 반지름(그림 폭 비율)] 밝힐 구역. tag: 작은 이름표(선택). 다음 정지까지 유지
"""
import json, os, subprocess, sys, tempfile, time

AE = r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe"
spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.abspath(sys.argv[2])
spec["img"] = os.path.abspath(spec["img"]).replace("\\", "/")
WORK = tempfile.mkdtemp(prefix="aet_")
jsx = os.path.join(WORK, "tour.jsx")
render_base = os.path.join(WORK, "tour_ae").replace("\\", "/")
log_path = os.path.join(WORK, "log.txt").replace("\\", "/")
open(jsx, "w", encoding="utf-8").write(r"""
app.preferences.savePrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY", 1);
var LOG = new File(%(log)s); LOG.encoding = "UTF-8"; LOG.open("w");
function L(s){ LOG.writeln(s); }
function TR(l){ return l.property("ADBE Transform Group"); }
function EZ(p, inf){ for (var i = 1; i <= p.numKeys; i++){ var n = (p.value instanceof Array) ? p.value.length : 1; var a = [];
  for (var d = 0; d < n; d++) a.push(new KeyframeEase(0, inf || 85)); try { p.setTemporalEaseAtKey(i, a, a); } catch (x) {} } }
try {
  if (!app.project) app.newProject();
  var S = %(spec)s, W = 1080, H = 1920;
  var comp = app.project.items.addComp("tour", W, H, 1, S.length, S.fps || 30); comp.motionBlur = true; comp.shutterAngle = 90;
  var ft = app.project.importFile(new ImportOptions(new File(S.img)));
  var iw = ft.width, ih = ft.height, base = H / ih;                  // zoom 1 = 그림 높이를 화면에 맞춤
  var world = comp.layers.addNull(); world.name = "world"; TR(world).property("ADBE Anchor Point").setValue([0, 0]);   // 널 기준점을 원점으로(그림 어긋남·검은 띠 방지)
  var im = comp.layers.add(ft); im.parent = world; TR(im).property("ADBE Position").setValue([0, 0]);
  var dim = comp.layers.addSolid([0, 0, 0], "dim", W, H, 1, S.length);   // 강조 밖을 살짝 어둡게(구멍 난 마스크)
  var pos = TR(world).property("ADBE Position"), sc = TR(world).property("ADBE Scale");
  var ST = S.stops, dimOp = TR(dim).property("ADBE Opacity");
  for (var k = 0; k < ST.length; k++) {
    var st = ST[k], z = base * st.zoom * 100, t = st.t;
    var px = (st.x - 0.5) * iw * base * st.zoom, py = (st.y - 0.5) * ih * base * st.zoom;
    var mx = Math.max(0, (iw * base * st.zoom - W) / 2), my = Math.max(0, (ih * base * st.zoom - H) / 2);   // 그림이 늘 화면을 덮게(검은 띠 방지)
    px = Math.max(-mx, Math.min(mx, px)); py = Math.max(-my, Math.min(my, py));
    pos.setValueAtTime(t, [W / 2 - px, H / 2 - py]); sc.setValueAtTime(t, [z, z]);
    var tn = (k + 1 < ST.length) ? ST[k + 1].t : S.length;
    var mv = Math.min(0.35, (tn - t) * 0.35);                         // 확대해서 멈춰 보여 주고, 다음 곳으로는 짧게 이동(운영자 09-28 「하나씩 확대후 멈춤으로」)
    if (tn - t > 0.3 && k + 1 < ST.length) { var drift = 1.015;
      pos.setValueAtTime(tn - mv, [W / 2 - px * drift, H / 2 - py * drift]); sc.setValueAtTime(tn - mv, [z * drift, z * drift]); }
    if (st.hi) {
      var tin = Math.min(0.35, (tn - t) * 0.4), he = Math.max(t + tin + 0.05, tn - 0.12), ho = he + 0.18;   // 짧은 정지도 겹치지 않게(09-28 실측: 이름표가 남음)
      var r = st.hi[2] * iw, cx = (st.hi[0] - 0.5) * iw, cy = (st.hi[1] - 0.5) * ih, D = 6000, kk = 0.5523;
      var FOL = "var w=thisComp.layer('world'); var s=w.transform.scale[0]/100; var p=w.transform.position; [p[0]+(" + cx + ")*s, p[1]+(" + cy + ")*s];";
      var SCL = "var s=thisComp.layer('world').transform.scale[0]; [s, s];";
      var sh = new Shape(); sh.vertices = [[D / 2, D / 2 - r], [D / 2 + r, D / 2], [D / 2, D / 2 + r], [D / 2 - r, D / 2]];
      sh.inTangents = [[-r * kk, 0], [0, -r * kk], [r * kk, 0], [0, r * kk]]; sh.outTangents = [[r * kk, 0], [0, r * kk], [-r * kk, 0], [0, -r * kk]]; sh.closed = true;
      // 어둠(가운데 구멍) — 구멍이 구역을 따라 움직임
      var dk = comp.layers.addSolid([0, 0, 0], "dim" + k, D, D, 1, S.length);
      var m = dk.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"); m.maskMode = MaskMode.SUBTRACT; m.property("ADBE Mask Shape").setValue(sh);
      m.property("ADBE Mask Feather").setValue([r * 0.8, r * 0.8]);
      dk.parent = im; TR(dk).property("ADBE Position").setValue([cx + iw / 2, cy + ih / 2]); TR(dk).property("ADBE Scale").setValue([100, 100]);   // 그림에 붙임(식 대신 부모 연결, 09-28)
      var dko = TR(dk).property("ADBE Opacity"); dko.setValueAtTime(0, 0); dko.setValueAtTime(Math.max(0, t - 0.05), 0); dko.setValueAtTime(t + tin, 48);
      dko.setValueAtTime(he, 48); dko.setValueAtTime(ho, 0); EZ(dko, 70);
      // 구역 은은한 빛
      var gl = comp.layers.addSolid([1, 0.86, 0.62], "glow" + k, D, D, 1, S.length); gl.blendingMode = BlendingMode.SOFT_LIGHT;
      var gm = gl.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"); gm.property("ADBE Mask Shape").setValue(sh); gm.property("ADBE Mask Feather").setValue([r, r]);
      gl.parent = im; TR(gl).property("ADBE Position").setValue([cx + iw / 2, cy + ih / 2]); TR(gl).property("ADBE Scale").setValue([100, 100]);
      var go = TR(gl).property("ADBE Opacity"); go.setValueAtTime(0, 0); go.setValueAtTime(Math.max(0, t - 0.05), 0); go.setValueAtTime(t + tin, 60);
      go.setValueAtTime(he, 60); go.setValueAtTime(ho, 0); EZ(go, 70);
      if (st.tag) {                                                   // 이름표: 구역 위쪽에 붙어 카메라와 함께 움직임
        var T = comp.layers.addText(st.tag); var sp = T.property("ADBE Text Properties").property("ADBE Text Document"); var td = sp.value;
        td.resetCharStyle(); td.font = "Pretendard-SemiBold"; td.fontSize = 60; td.fillColor = [1, 0.93, 0.78]; td.tracking = 30;
        td.justification = ParagraphJustification.CENTER_JUSTIFY; sp.setValue(td);
        T.parent = im; TR(T).property("ADBE Position").setValue([cx + iw / 2, cy + ih / 2 + r * 0.45]); TR(T).property("ADBE Scale").setValue([100 / (base * st.zoom), 100 / (base * st.zoom)]);

        var ds = T.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow"); ds.property("ADBE Drop Shadow-0002").setValue(230); ds.property("ADBE Drop Shadow-0005").setValue(26); ds.property("ADBE Drop Shadow-0004").setValue(2);
        var to = TR(T).property("ADBE Opacity"); to.setValueAtTime(0, 0); to.setValueAtTime(t + 0.05, 0); to.setValueAtTime(t + tin, 100);
        to.setValueAtTime(he, 100); to.setValueAtTime(ho - 0.05, 0); EZ(to, 70);
        var tb = T.property("ADBE Effect Parade").addProperty("ADBE Box Blur2").property(1); tb.setValueAtTime(t + 0.05, 12); tb.setValueAtTime(t + tin, 0);
      }
    }
  }
  EZ(pos, 88); EZ(sc, 88); dim.remove();
  im.motionBlur = true; world.moveToEnd(); im.moveToEnd();
  var bk = comp.layers.add(ft); var bs = Math.max(W / iw, H / ih) * 130; TR(bk).property("ADBE Scale").setValue([bs, bs]);   // 가장자리 틈 메우기: 흐린 같은 그림
  TR(bk).property("ADBE Position").setValue([W / 2, H / 2]); bk.property("ADBE Effect Parade").addProperty("ADBE Box Blur2").property(1).setValue(60);
  var bd = bk.property("ADBE Effect Parade").addProperty("ADBE Brightness & Contrast 2"); bd.property(1).setValue(-40); bk.moveToEnd();
  var rq = app.project.renderQueue.items.add(comp); var om = rq.outputModule(1); om.applyTemplate("H.264 - 렌더링 일치 설정 - 40Mbps"); om.file = new File(%(out)s);
  L("stops " + ST.length); app.project.renderQueue.render(); L("render done");
} catch (e) { L("ERROR " + e.toString() + " line " + e.line); }
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
    if (done_at and time.time() - done_at > 30) or time.time() - t0 > 1800:
        subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        break
subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # AE 가 남지 않게: 실행기만 끝나고 AfterFX 본체가 8GB 를 쥔 채 남던 문제(09-28)
log = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else "(로그 없음)"
print(log.strip())
cands = [f for f in os.listdir(WORK) if f.startswith("tour_ae")]
if "render done" not in log or not cands:
    raise SystemExit("AE 렌더 실패: " + WORK)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, cands[0]), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(spec.get("fps", 30)), "-an", OUT], check=True)
print("AE TOUR", OUT)
