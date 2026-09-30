"""After Effects 로 강조 그래픽 층(3D 오브제·카드·도장·글자)을 모션그래픽으로 만든다 → 투명 배경 .mov (2026-09-28)

  python ae_graphics.py <그래픽.json> <출력.mov>

왜: 운영자 09-28 「중복 이미지 … 이미지가 미리나오는것도 문제 이미지 등장도 너무 단조롭고 이미지 to 이미지 트레지션효과도 없어서 밋밋함」
    「이미지도 너무 저품질」 「에펙이나 ai이미지스킬로 좀 고급지게」 → 고품질 오브제(코덱스 3D 렌더·공급간지 고해상도)를
    AE 에서 모션 블러·빛 스치기·다양한 등장·밀어내기 전환으로 움직인다. 글자는 이미지에 굽지 않고 AE 글자 층으로(한글 깨짐 방지).

그래픽.json: {"length":54.5, "fps":30, "items":[
   {"img":"obj.png", "start":1.2, "end":2.4, "cx":0.5, "cy":0.30, "w":560,
    "in":"fly_l|fly_r|drop|slam|flip|zoom|swing", "out":"push_l|push_r|up|fade",
    "sweep":true, "xmark":false,
    "text":"6억대", "font":"Pretendard-Black", "size":120, "color":"#f3d38a", "tx":0, "ty":0, "trot":-6}]}
  - cx·cy 화면 비율, w 가로 px. text 의 tx·ty 는 이미지 가운데 기준 px(이미지와 함께 움직임)
  - 다음 그림이 0.15초 안에 이어지면 만드는 쪽(편 설정)에서 out 을 push 로 주고 end 를 다음 start+0.3 으로 겹친다
"""
import json, os, subprocess, sys, tempfile, time

AE = r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe"
spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.abspath(sys.argv[2])
W, H = 1080, 1920
FPS, LEN = spec.get("fps", 30), spec["length"]
WORK = tempfile.mkdtemp(prefix="aeg_")


def rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


items = []
for it in spec["items"]:
    d = dict(it)
    d["img"] = os.path.abspath(it["img"]).replace("\\", "/") if it.get("img") else ""
    d["color"] = rgb(it.get("color", "#ffffff"))
    d.setdefault("font", "Pretendard-Black"); d.setdefault("size", 110); d.setdefault("tx", 0); d.setdefault("ty", 0); d.setdefault("trot", 0)
    d.setdefault("in", "zoom"); d.setdefault("out", "fade")
    items.append(d)

jsx = os.path.join(WORK, "gfx.jsx")
render_base = os.path.join(WORK, "gfx_ae").replace("\\", "/")
log_path = os.path.join(WORK, "log.txt").replace("\\", "/")
open(jsx, "w", encoding="utf-8").write(r"""
app.preferences.savePrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY", 1);
var LOG = new File(%(log)s); LOG.encoding = "UTF-8"; LOG.open("w");
function L(s){ LOG.writeln(s); }
function K(p, t, v, inf, outf){ var i = p.addKey(t); p.setValueAtKey(i, v); return i; }
function EASE(p, outInf, inInf){ for (var i = 1; i <= p.numKeys; i++){ var n = (p.value instanceof Array) ? p.value.length : 1; var a = [], b = [];
  for (var d = 0; d < n; d++){ a.push(new KeyframeEase(0, inInf || 70)); b.push(new KeyframeEase(0, outInf || 70)); }
  try { p.setTemporalEaseAtKey(i, a, b); } catch (x) {} } }
try {
  if (!app.project) app.newProject();                      // -noui: newProject·beginSuppressDialogs 금지(09-28 실측)
  var comp = app.project.items.addComp("gfx", %(W)d, %(H)d, 1, %(LEN)f, %(FPS)d);
  comp.motionBlur = true; comp.shutterAngle = 200;
  var IT = %(items)s; L("start " + IT.length);
  for (var n = 0; n < IT.length; n++) {
    var R = IT[n], s = R.start, e = R.end; L("item " + n);
    var cx = R.cx * %(W)d, cy = R.cy * %(H)d;
    var hold = comp.layers.addNull(); hold.name = "grp" + n; hold.threeDLayer = (R["in"] == "flip");
    hold.inPoint = s; hold.outPoint = e;
    var P = hold.property("ADBE Transform Group").property("ADBE Position"), S = hold.property("ADBE Transform Group").property("ADBE Scale"),
        RT = hold.property("ADBE Transform Group").property("ADBE Rotate Z"), O = hold.property("ADBE Transform Group").property("ADBE Opacity");
    var z = hold.threeDLayer ? [cx, cy, 0] : [cx, cy];
    function PT(x, y){ return hold.threeDLayer ? [x, y, 0] : [x, y]; }
    function SC(v){ return hold.threeDLayer ? [v, v, v] : [v, v]; }
    // ── 등장 ──
    var a = R["in"];
    if (a == "fly_l" || a == "fly_r") { var sg = (a == "fly_l") ? -1 : 1;
      K(P, s, PT(cx + sg * 1300, cy + 60)); K(P, s + 0.30, PT(cx - sg * 26, cy)); K(P, s + 0.44, PT(cx, cy));
      K(RT, s, sg * 14); K(RT, s + 0.30, -sg * 3); K(RT, s + 0.44, 0); K(S, s, SC(92)); K(S, s + 0.44, SC(100)); }
    else if (a == "drop") { K(P, s, PT(cx, cy - 1150)); K(P, s + 0.30, PT(cx, cy + 34)); K(P, s + 0.40, PT(cx, cy - 12)); K(P, s + 0.50, PT(cx, cy));
      K(S, s + 0.28, SC(104)); K(S, s + 0.36, SC(96)); K(S, s + 0.50, SC(100)); }
    else if (a == "slam") { P.setValue(z); K(S, s, SC(260)); K(S, s + 0.13, SC(90)); K(S, s + 0.21, SC(105)); K(S, s + 0.30, SC(100));
      K(RT, s, -22); K(RT, s + 0.13, -7); K(RT, s + 0.30, -8);
      P.expression = "var t0=" + (s + 0.13) + "; if (time>t0 && time<t0+0.28) value + wiggle(40, 18*(1-(time-t0)/0.28)) - value; else value;"; }
    else if (a == "flip") { P.setValue(z); var YR = hold.property("ADBE Transform Group").property("ADBE Rotate Y");
      K(YR, s, -95); K(YR, s + 0.34, 9); K(YR, s + 0.48, 0); K(S, s, SC(90)); K(S, s + 0.48, SC(100)); EASE(YR, 80, 60); }
    else if (a == "swing") { hold.property("ADBE Transform Group").property("ADBE Anchor Point").setValue([0, -300]); var zz = PT(cx, cy - 300);
      K(P, s, PT(cx, cy - 1400)); K(P, s + 0.28, zz); K(RT, s, -38); K(RT, s + 0.28, 16); K(RT, s + 0.46, -7); K(RT, s + 0.62, 3); K(RT, s + 0.76, 0); }
    else { P.setValue(z); K(S, s, SC(25)); K(S, s + 0.24, SC(108)); K(S, s + 0.38, SC(100)); K(RT, s, 8); K(RT, s + 0.38, 0); }
    K(O, s, 0); K(O, s + 0.08, 100);
    // ── 퇴장 ──
    var b = R.out, e0 = e - 0.30;
    if (b == "push_l" || b == "push_r") { var so = (b == "push_l") ? -1 : 1; var cur = P.valueAtTime(e0, true);
      K(P, e0, cur); K(P, e, PT(cx + so * 1350, (cur[1]))); K(RT, e0, RT.valueAtTime(e0, true)); K(RT, e, so * 10); }
    else if (b == "up") { var cu = P.valueAtTime(e0, true); K(P, e0, cu); K(P, e, PT(cu[0], cu[1] - 1300)); }
    else { K(S, e0, S.valueAtTime(e0, true)); K(S, e, SC(88)); }
    K(O, e - 0.12, 100); K(O, e, 0);
    EASE(P, 85, 60); EASE(S, 80, 60); EASE(RT, 70, 60);
    // ── 그림 ──
    var imgL = null, iw = R.w, ih = R.w;
    if (R.img) { var ft = app.project.importFile(new ImportOptions(new File(R.img)));
      imgL = comp.layers.add(ft); imgL.inPoint = s; imgL.outPoint = e; imgL.parent = hold; imgL.threeDLayer = hold.threeDLayer;
      var sc = R.w / ft.width * 100; imgL.property("ADBE Transform Group").property("ADBE Scale").setValue(hold.threeDLayer ? [sc, sc, sc] : [sc, sc]);
      imgL.property("ADBE Transform Group").property("ADBE Position").setValue(hold.threeDLayer ? [0, 0, 0] : [0, 0]); imgL.property("ADBE Transform Group").property("ADBE Rotate Z").setValue(0); iw = R.w; ih = ft.height * R.w / ft.width;
      var fx = imgL.property("ADBE Effect Parade"); var ds = fx.addProperty("ADBE Drop Shadow");
      ds.property("ADBE Drop Shadow-0002").setValue(150); ds.property("ADBE Drop Shadow-0004").setValue(R.w * 0.03); ds.property("ADBE Drop Shadow-0005").setValue(R.w * 0.06);
      if (R.sweep) { var sw = fx.addProperty("CC Light Sweep"); var c0 = s + 0.45, c1 = Math.min(e - 0.35, c0 + 0.9);
        sw.property(1).setValueAtTime(c0, [-ft.width * 0.2, ft.height * 0.3]); sw.property(1).setValueAtTime(c1, [ft.width * 1.2, ft.height * 0.7]);
        try { sw.property(3).setValue(ft.width * 0.12); sw.property(5).setValue(55); } catch (x) {} }
      imgL.motionBlur = true; }
    // ── 빨간 X(획이 그려짐) ──
    if (R.xmark) { var X = comp.layers.addShape(); X.parent = hold; X.inPoint = s; X.outPoint = e; X.threeDLayer = hold.threeDLayer;
      var ct = X.property("ADBE Root Vectors Group"); var r2 = Math.min(iw, ih) * 0.42;
      var segs = [[[-r2, -r2], [r2, r2]], [[r2, -r2], [-r2, r2]]];
      for (var q = 0; q < 2; q++) { var g = ct.addProperty("ADBE Vector Group"); var gc = g.property("ADBE Vectors Group");
        var pth = gc.addProperty("ADBE Vector Shape - Group"); var sh = new Shape(); sh.vertices = segs[q]; sh.closed = false; pth.property("ADBE Vector Shape").setValue(sh);
        var st = gc.addProperty("ADBE Vector Graphic - Stroke"); st.property("ADBE Vector Stroke Color").setValue([0.86, 0.1, 0.12]); st.property("ADBE Vector Stroke Width").setValue(Math.max(30, iw * 0.07));
        st.property("ADBE Vector Stroke Line Cap").setValue(2);
        var tr = gc.addProperty("ADBE Vector Filter - Trim"); var en = tr.property("ADBE Vector Trim End"); var t0 = s + 0.40 + q * 0.14;
        en.setValueAtTime(t0, 0); en.setValueAtTime(t0 + 0.14, 100); }
      X.property("ADBE Transform Group").property("ADBE Position").setValue(hold.threeDLayer ? [0, 0, 0] : [0, 0]);
      X.property("ADBE Transform Group").property("ADBE Scale").setValue(hold.threeDLayer ? [100, 100, 100] : [100, 100]); X.property("ADBE Transform Group").property("ADBE Rotate Z").setValue(0);
      var xd = X.property("ADBE Effect Parade").addProperty("ADBE Drop Shadow"); xd.property("ADBE Drop Shadow-0002").setValue(140); xd.property("ADBE Drop Shadow-0005").setValue(14); X.motionBlur = true; }
    // ── 글자(그림과 함께 움직임) ──
    if (R.text) { var ts = R.text.split("\n");
      for (var li = 0; li < ts.length; li++) { var T = comp.layers.addText(ts[li]); T.parent = hold; T.inPoint = s; T.outPoint = e; T.threeDLayer = hold.threeDLayer;
        var srt = T.property("ADBE Text Properties").property("ADBE Text Document"); var td = srt.value; td.resetCharStyle(); td.font = R.font; td.fontSize = R.size; td.fillColor = R.color;
        td.applyStroke = false; td.justification = ParagraphJustification.CENTER_JUSTIFY; srt.setValue(td);
        var ty = R.ty + (li - (ts.length - 1) / 2) * R.size * 1.08 + R.size * 0.36;
        T.property("ADBE Transform Group").property("ADBE Position").setValue(T.threeDLayer ? [R.tx, ty, 0] : [R.tx, ty]);
        T.property("ADBE Transform Group").property("ADBE Scale").setValue(T.threeDLayer ? [100, 100, 100] : [100, 100]);   // parent 연결 때 0초 시점 크기로 보정된 것을 되돌림(09-28 실측: 확대 등장 글자 4배)
        T.property("ADBE Transform Group").property("ADBE Rotate Z").setValue(R.trot);
        var tf = T.property("ADBE Effect Parade"); var td2 = tf.addProperty("ADBE Drop Shadow"); td2.property("ADBE Drop Shadow-0002").setValue(170);
        td2.property("ADBE Drop Shadow-0004").setValue(R.size * 0.06); td2.property("ADBE Drop Shadow-0005").setValue(R.size * 0.12);
        if (R.glow) { var gl = tf.addProperty("ADBE Glo2"); try { gl.property("ADBE Glo2-0003").setValue(R.size * 0.4); gl.property("ADBE Glo2-0004").setValue(R.glow); } catch (x) {} }
        var to = T.property("ADBE Transform Group").property("ADBE Opacity"); to.setValueAtTime(s, 0); to.setValueAtTime(s + 0.22, 0); to.setValueAtTime(s + 0.34, 100);
        T.motionBlur = true; } }
  }
  var rq = app.project.renderQueue.items.add(comp);
  var om = rq.outputModule(1); om.applyTemplate("고품질(알파 포함)"); om.file = new File(%(out)s);
  L("items " + IT.length); app.project.renderQueue.render(); L("render done");
} catch (e) { L("ERROR " + e.toString() + " line " + e.line); }
LOG.close();
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.quit();
""" % {"log": json.dumps(log_path), "W": W, "H": H, "LEN": LEN, "FPS": FPS, "items": json.dumps(items, ensure_ascii=False), "out": json.dumps(render_base)})

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
cands = [f for f in os.listdir(WORK) if f.startswith("gfx_ae")]
if "render done" not in log or not cands:
    raise SystemExit("AE 렌더 실패: " + WORK)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, cands[0]), "-c:v", "png", "-pix_fmt", "rgba", "-r", str(FPS), OUT], check=True)
os.remove(os.path.join(WORK, cands[0]))
print("AE GFX", OUT)
