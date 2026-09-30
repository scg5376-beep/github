"""After Effects 로 「라인 인포그래픽」 강조 층 — 빛나는 점 하나가 영상 내내 이어지며 정보를 끌고 다닌다 → 투명 .mov (2026-09-28)

  python ae_callouts.py <콜아웃.json> <출력.mov>

왜: 운영자 09-28 시안 D(라인 인포그래픽) 선택 + 「글자가 강조되게끔 폰트나 색감을 조정」 +
    레퍼런스(youtube vR5ikhZBN28 모션그래픽) 「이런 자연스러움과 고급스러움 … 끊기는게 아니라」
    → 요소가 따로 튀어나오지 않고, 점 하나가 다음 정보 자리로 미끄러져 가며 선을 그리고 글자를 풀어 놓는다.
       등장: 선 그리기(Trim Paths) · 글자 흐림→선명·아래서 위로 · 순차. 퇴장: 선이 점으로 되감기·글자 흐려지며 위로.

콜아웃.json: {"length":54.5, "fps":30, "items":[
   {"start":1.18, "end":3.1, "ax":230, "ay":700, "side":1, "label":"PRICE", "big":"6억대", "small":"84㎡ 분양가",
    "img":"(선택) 카드 그림.png", "img_w":520}]}
  - ax·ay: 점 자리(px). side 1 = 글자가 오른쪽, -1 = 왼쪽(오른쪽 정렬)
"""
import json, os, subprocess, sys, tempfile, time

AE = r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe"
spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.abspath(sys.argv[2])
FPS, LEN = spec.get("fps", 30), spec["length"]
WORK = tempfile.mkdtemp(prefix="aec_")
items = []
for it in spec["items"]:
    d = dict(it)
    d["img"] = os.path.abspath(it["img"]).replace("\\", "/") if it.get("img") else ""
    d.setdefault("side", 1); d.setdefault("small", ""); d.setdefault("big", ""); d.setdefault("img_w", 520)
    items.append(d)
C = spec.get("colors", {"big": [0.97, 0.86, 0.63], "label": [0.56, 0.90, 0.86], "small": [1, 1, 1], "line": [1, 1, 1]})

jsx = os.path.join(WORK, "callouts.jsx")
render_base = os.path.join(WORK, "cal_ae").replace("\\", "/")
log_path = os.path.join(WORK, "log.txt").replace("\\", "/")
open(jsx, "w", encoding="utf-8").write(r"""
app.preferences.savePrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY", 1);
var LOG = new File(%(log)s); LOG.encoding = "UTF-8"; LOG.open("w");
function L(s){ LOG.writeln(s); }
function TR(l){ return l.property("ADBE Transform Group"); }
function EZ(p, inf){ for (var i = 1; i <= p.numKeys; i++){ var n = (p.value instanceof Array) ? p.value.length : 1; var a = [];
  for (var d = 0; d < n; d++) a.push(new KeyframeEase(0, inf || 80)); try { p.setTemporalEaseAtKey(i, a, a); } catch (x) {} } }
function glow(l, r, k){ var g = l.property("ADBE Effect Parade").addProperty("ADBE Glo2"); try { g.property("ADBE Glo2-0003").setValue(r); g.property("ADBE Glo2-0004").setValue(k); } catch (x) {} }
function shadow(l, soft, op){ var s = l.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow"); s.property("ADBE Drop Shadow-0002").setValue(op || 160);
  s.property("ADBE Drop Shadow-0004").setValue(4); s.property("ADBE Drop Shadow-0005").setValue(soft); }
function textL(comp, t, font, size, col, just){ var T = comp.layers.addText(t); var sp = T.property("ADBE Text Properties").property("ADBE Text Document");
  var td = sp.value; td.resetCharStyle(); td.font = font; td.fontSize = size; td.fillColor = col; td.applyStroke = false; td.tracking = (size < 50) ? 120 : -10;
  td.justification = (just < 0) ? ParagraphJustification.RIGHT_JUSTIFY : ParagraphJustification.LEFT_JUSTIFY; sp.setValue(td); T.motionBlur = true; return T; }
function reveal(l, s, e, x, y, dly){ var p = TR(l).property("ADBE Position"), o = TR(l).property("ADBE Opacity");
  var b = l.property("ADBE Effect Parade").addProperty("ADBE Box Blur2"); var br = b.property(1);
  var a = s + dly; p.setValueAtTime(a, [x, y + 46]); p.setValueAtTime(a + 0.62, [x, y]); p.setValueAtTime(e - 0.42, [x, y]); p.setValueAtTime(e, [x, y - 26]);
  o.setValueAtTime(a, 0); o.setValueAtTime(a + 0.45, 100); o.setValueAtTime(e - 0.30, 100); o.setValueAtTime(e, 0);
  br.setValueAtTime(a, 22); br.setValueAtTime(a + 0.55, 0); br.setValueAtTime(e - 0.38, 0); br.setValueAtTime(e, 14);
  EZ(p, 88); EZ(o, 70); EZ(br, 80); }
try {
  if (!app.project) app.newProject();
  var comp = app.project.items.addComp("callouts", 1080, 1920, 1, %(LEN)f, %(FPS)d);
  comp.motionBlur = true; comp.shutterAngle = 180;
  var IT = %(items)s, CL = %(C)s;
  // ── 영상 내내 이어지는 점 ──
  var dot = comp.layers.addShape(); dot.name = "dot"; var dg = dot.property("ADBE Root Vectors Group");
  var e1 = dg.addProperty("ADBE Vector Group").property("ADBE Vectors Group"); e1.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([26, 26]);
  e1.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue(CL.line);
  var e2 = dg.addProperty("ADBE Vector Group").property("ADBE Vectors Group"); e2.addProperty("ADBE Vector Shape - Ellipse");
  var st2 = e2.addProperty("ADBE Vector Graphic - Stroke"); st2.property("ADBE Vector Stroke Color").setValue(CL.line); st2.property("ADBE Vector Stroke Width").setValue(2);
  var g2 = dot.property("ADBE Root Vectors Group").property(2);           // 속성을 더하면 앞서 잡은 참조가 무효 → 다시 찾기(09-28 실측)
  g2.property("ADBE Vectors Group").property(1).property("ADBE Vector Ellipse Size").expression = "var p = (time*0.9)%%1; [36+44*p, 36+44*p];";   // 숨 쉬듯 퍼지는 고리
  g2.property("ADBE Vector Transform Group").property("ADBE Vector Group Opacity").expression = "var p=(time*0.9)%%1; 80*(1-p);";
  glow(dot, 30, 1.4); dot.motionBlur = true;
  var DP = TR(dot).property("ADBE Position"), DO = TR(dot).property("ADBE Opacity"), DS = TR(dot).property("ADBE Scale");
  for (var n = 0; n < IT.length; n++) {
    var R = IT[n], s = R.start, e = R.end, prev = (n > 0) ? IT[n - 1] : null;
    if (!prev || s - prev.end > 2.5) { DP.setValueAtTime(s - 0.25, [R.ax, R.ay]); DO.setValueAtTime(s - 0.30, 0); DO.setValueAtTime(s - 0.02, 100);
      DS.setValueAtTime(s - 0.30, [40, 40]); DS.setValueAtTime(s, [100, 100]); }
    else { DP.setValueAtTime(Math.max(prev.end - 0.25, prev.start + 0.4), [prev.ax, prev.ay]); DP.setValueAtTime(s, [R.ax, R.ay]); }
    DP.setValueAtTime(e - 0.05, [R.ax, R.ay]);
    var nx = (n + 1 < IT.length) ? IT[n + 1] : null;
    if (!nx || nx.start - e > 2.5) { DO.setValueAtTime(e, 100); DO.setValueAtTime(e + 0.35, 0); DS.setValueAtTime(e, [100, 100]); DS.setValueAtTime(e + 0.35, [30, 30]); }
    var sd = R.side, ax = R.ax, ay = R.ay, xe = (sd > 0) ? 1080 - 90 : 90, ky = ay - 120;
    // 글자 뒤 부드러운 어둠
    var sc = comp.layers.addShape(); sc.inPoint = s - 0.1; sc.outPoint = e + 0.1;
    var sg = sc.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
    sg.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([900, 520]);
    sg.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue([0, 0, 0]);
    TR(sc).property("ADBE Position").setValue([ax + sd * 330, ay - 90]);
    sc.property("ADBE Effect Parade").addProperty("ADBE Box Blur2").property(1).setValue(140);
    var so = TR(sc).property("ADBE Opacity"); so.setValueAtTime(s, 0); so.setValueAtTime(s + 0.5, 42); so.setValueAtTime(e - 0.3, 42); so.setValueAtTime(e + 0.1, 0); EZ(so, 70);
    // 선: 점 → 사선 → 가로
    var ln = comp.layers.addShape(); ln.inPoint = s; ln.outPoint = e + 0.05; TR(ln).property("ADBE Position").setValue([0, 0]);   // 경로 좌표 = 화면 좌표
    var lg = ln.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
    var sh = new Shape(); sh.vertices = [[ax, ay], [ax + sd * 120, ky], [xe, ky]]; sh.closed = false;
    lg.addProperty("ADBE Vector Shape - Group").property("ADBE Vector Shape").setValue(sh);
    var ls = lg.addProperty("ADBE Vector Graphic - Stroke"); ls.property("ADBE Vector Stroke Color").setValue(CL.line); ls.property("ADBE Vector Stroke Width").setValue(3);
    ls.property("ADBE Vector Stroke Line Cap").setValue(2);
    var tm = lg.addProperty("ADBE Vector Filter - Trim"); var te = tm.property("ADBE Vector Trim End");
    te.setValueAtTime(s, 0); te.setValueAtTime(s + 0.55, 100); te.setValueAtTime(e - 0.45, 100); te.setValueAtTime(e, 0); EZ(te, 85);
    glow(ln, 16, 0.9);
    // 글자(라벨) + 선 아이콘 배지 또는 큰 글자
    var tx = ax + sd * 140;
    var lb = textL(comp, R.label, "Pretendard-Bold", 40, CL.label, sd); lb.inPoint = s; lb.outPoint = e; reveal(lb, s, e, tx, ky - 44, 0.18);
    if (R.icon) {                                                   // 운영자 09-28 「글자보단 좀더 시각적인 요소로 강조」 → 선이 그려지는 아이콘
      var bx = ax + sd * 330, by = ky + 150, K2 = 1.55;
      var ic = comp.layers.addShape(); ic.inPoint = s; ic.outPoint = e + 0.05; TR(ic).property("ADBE Position").setValue([bx, by]);
      var root = ic.property("ADBE Root Vectors Group");
      var strokes = [{"circle": [0, 0, 74]}].concat(R.icon);
      for (var q = 0; q < strokes.length; q++) {
        var gg = root.addProperty("ADBE Vector Group").property("ADBE Vectors Group"), sk = strokes[q];
        if (sk.circle) { var el = gg.addProperty("ADBE Vector Shape - Ellipse"); el.property("ADBE Vector Ellipse Size").setValue([sk.circle[2] * 2 * (q ? K2 : 1.6), sk.circle[2] * 2 * (q ? K2 : 1.6)]);
          el.property("ADBE Vector Ellipse Position").setValue([sk.circle[0] * K2, sk.circle[1] * K2]); }
        else { var ps = new Shape(), vv = []; for (var v = 0; v < sk.pts.length; v++) vv.push([sk.pts[v][0] * K2, sk.pts[v][1] * K2]);
          ps.vertices = vv; ps.closed = !!sk.closed; gg.addProperty("ADBE Vector Shape - Group").property("ADBE Vector Shape").setValue(ps); }
        var ss = gg.addProperty("ADBE Vector Graphic - Stroke"); ss.property("ADBE Vector Stroke Color").setValue(q ? CL.big : CL.line);
        ss.property("ADBE Vector Stroke Width").setValue(q ? 6 : 2.5); ss.property("ADBE Vector Stroke Line Cap").setValue(2); ss.property("ADBE Vector Stroke Line Join").setValue(2);
        var tt = gg.addProperty("ADBE Vector Filter - Trim").property("ADBE Vector Trim End");
        var d0 = s + 0.35 + (q ? 0.25 + q * 0.09 : 0); tt.setValueAtTime(d0, 0); tt.setValueAtTime(d0 + (q ? 0.5 : 0.7), 100);
        tt.setValueAtTime(e - 0.40, 100); tt.setValueAtTime(e - 0.05, 0); EZ(tt, 85);
      }
      glow(ic, 22, 0.8); ic.motionBlur = true;
      var isc = TR(ic).property("ADBE Scale"); isc.setValueAtTime(s + 0.3, [86, 86]); isc.setValueAtTime(s + 1.1, [100, 100]); isc.setValueAtTime(e, [104, 104]); EZ(isc, 80);
      var ib = comp.layers.addShape(); ib.inPoint = s; ib.outPoint = e; ib.moveAfter(ic);          // 배지 안 은은한 어둠
      var ibg = ib.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
      ibg.addProperty("ADBE Vector Shape - Ellipse").property("ADBE Vector Ellipse Size").setValue([236, 236]);
      ibg.addProperty("ADBE Vector Graphic - Fill").property("ADBE Vector Fill Color").setValue([0.03, 0.05, 0.08]);
      TR(ib).property("ADBE Position").setValue([bx, by]);
      var io = TR(ib).property("ADBE Opacity"); io.setValueAtTime(s + 0.3, 0); io.setValueAtTime(s + 0.9, 55); io.setValueAtTime(e - 0.3, 55); io.setValueAtTime(e, 0); EZ(io, 70);
    }
    if (R.big) {
    var bg = textL(comp, R.big, "Pretendard-Black", R.big.length > 7 ? 92 : 124, CL.big, sd); bg.inPoint = s; bg.outPoint = e;
    reveal(bg, s, e, tx, ky + (R.big.length > 7 ? 104 : 128), 0.28); glow(bg, 26, 0.35); shadow(bg, 22, 170);
    if (R.small) { var sm = textL(comp, R.small, "Pretendard-SemiBold", 44, CL.small, sd); sm.inPoint = s; sm.outPoint = e;
      reveal(sm, s, e, tx, ky + (R.big.length > 7 ? 180 : 212), 0.40); shadow(sm, 14, 150); }
    }
    // 사진 카드(운영자 09-28 「아이콘배지같이 짜치는거말고 시각이미지」) — 선 끝 자리에, 둥근 모서리·얇은 금테·천천히 다가감
    if (R.img) { var ft = app.project.importFile(new ImportOptions(new File(R.img))); var cw = R.img_w || 440;
      var cx2 = ax + sd * (150 + cw / 2), cy2 = ky + 60 + cw * ft.height / ft.width / 2, chh = cw * ft.height / ft.width;
      var im = comp.layers.add(ft); im.inPoint = s; im.outPoint = e; var k = cw / ft.width * 100; TR(im).property("ADBE Scale").setValue([k, k]);
      var mk = im.property("ADBE Mask Parade").addProperty("ADBE Mask Atom"); var rr = 26 * ft.width / cw, w2 = ft.width, h2 = ft.height;
      var rs = new Shape(); rs.vertices = [[rr, 0], [w2 - rr, 0], [w2, rr], [w2, h2 - rr], [w2 - rr, h2], [rr, h2], [0, h2 - rr], [0, rr]];
      var c0 = rr * 0.55; rs.inTangents = [[-c0, 0], [0, 0], [0, -c0], [0, 0], [c0, 0], [0, 0], [0, c0], [0, 0]];
      rs.outTangents = [[0, 0], [c0, 0], [0, 0], [0, c0], [0, 0], [-c0, 0], [0, 0], [0, -c0]]; rs.closed = true; mk.property("ADBE Mask Shape").setValue(rs);
      reveal(im, s, e, cx2, cy2, 0.30); shadow(im, 40, 170); im.motionBlur = true;
      var isc = TR(im).property("ADBE Scale"); isc.setValueAtTime(s + 0.3, [k * 0.96, k * 0.96]); isc.setValueAtTime(e, [k * 1.05, k * 1.05]);
      var fr = comp.layers.addShape(); fr.inPoint = s; fr.outPoint = e; var fg = fr.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
      var rct = fg.addProperty("ADBE Vector Shape - Rect"); rct.property("ADBE Vector Rect Size").setValue([cw + 14, chh + 14]); rct.property("ADBE Vector Rect Roundness").setValue(30);
      var fs = fg.addProperty("ADBE Vector Graphic - Stroke"); fs.property("ADBE Vector Stroke Color").setValue(CL.big); fs.property("ADBE Vector Stroke Width").setValue(2.5);
      var ftr = fg.addProperty("ADBE Vector Filter - Trim").property("ADBE Vector Trim End"); ftr.setValueAtTime(s + 0.35, 0); ftr.setValueAtTime(s + 0.95, 100); EZ(ftr, 85);
      reveal(fr, s, e, cx2, cy2, 0.30); }
  }
  EZ(DP, 75); EZ(DO, 70); EZ(DS, 70);
  dot.moveToBeginning();
  var rq = app.project.renderQueue.items.add(comp); var om = rq.outputModule(1); om.applyTemplate("고품질(알파 포함)"); om.file = new File(%(out)s);
  L("items " + IT.length); app.project.renderQueue.render(); L("render done");
} catch (e) { L("ERROR " + e.toString() + " line " + e.line); }
LOG.close();
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.quit();
""" % {"log": json.dumps(log_path), "LEN": LEN, "FPS": FPS, "items": json.dumps(items, ensure_ascii=False), "C": json.dumps(C), "out": json.dumps(render_base)})

proc = subprocess.Popen([AE, "-noui", "-r", jsx], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0, done_at = time.time(), None
while proc.poll() is None:
    time.sleep(3)
    txt = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else ""
    if ("render done" in txt or "ERROR" in txt) and done_at is None:
        done_at = time.time()
    if (done_at and time.time() - done_at > 30) or time.time() - t0 > 2400:
        subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        break
subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # AE 가 남지 않게: 실행기만 끝나고 AfterFX 본체가 8GB 를 쥔 채 남던 문제(09-28)
log = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else "(로그 없음)"
print(log.strip())
cands = [f for f in os.listdir(WORK) if f.startswith("cal_ae")]
if "render done" not in log or not cands:
    raise SystemExit("AE 렌더 실패: " + WORK)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, cands[0]), "-c:v", "png", "-pix_fmt", "rgba", "-r", str(FPS), OUT], check=True)
os.remove(os.path.join(WORK, cands[0]))
print("AE CALLOUTS", OUT)
