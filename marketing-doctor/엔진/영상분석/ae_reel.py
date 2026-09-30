"""After Effects 로 쇼츠 한 편을 통째로 만든다 — 대사 한 줄 = 그림 한 장, 전환·자막·그림 속 강조까지 한 프로젝트에서 (2026-09-28)

  python ae_reel.py <릴.json> <출력.mp4>      (소리는 따로 ffmpeg 로 섞는다)

왜: 운영자 09-28 레퍼런스(ref_0928) 「트렌지션효과 효과음활용 에프터이펙트 한번 정독학습해서 … 레퍼런스대로 실행」
    학습노트: 새작업/레퍼런스/학습노트.md — 정지 그림도 늘 움직임, 전환은 컷·줌 블러·휩·흰 번쩍,
    자막은 한 줄이 흐림→선명·살짝 크게 박히고 핵심 낱말만 색, 그림 속 강조(지폐 비·빛 선·빨간 원·핀)는 그림에 붙어 움직임.

릴.json: {"length":48, "fps":30,
  "shots":[{"s":0,"e":1.6,"src":"a.png|a.mp4","in":0, "from":[1.0,0,0], "to":[1.08,-20,0],   # [확대, x, y 이동 px]
            "box":[0,0,1080,960] (선택: 2단 분할 칸)}],
  "trans":[{"t":1.6, "type":"zoom|whip|flash|blur", "dur":0.22}],
  "subs":[{"s":0,"e":1.5,"runs":[["출퇴근 때문에","#ffe34d"],[" 이사를","#ffffff"]], "size":66}],
  "draw":[{"s":14,"e":17,"shot":9,"type":"ellipse|line|ring","pts":[[x,y],…] (그림 원본 px),"r":[rx,ry],"color":"#ff3b30","w":10,"glow":1}],
  "money":[{"s":8.9,"e":10.1,"img":"money.png","n":26}],
  (09-29 추가) shots[].src = "black" 이면 까만 배경 · trans type "lens"(렌즈 블러) ·
  "over":[{"s","e","src":"카드.png","keys":[[t,x,y,확대,회전,불투명],…],"shadow":1,"ease":70,"top":1(그리기보다 위),"parent":i(그 over 에 붙임·좌표는 그 그림 px),"autoOrient":1(경로 따라 회전)}]  — 떠오르는 페이지·카드·도장·X·전동차·세 칸 그림
  draw 에 "over":i(떠오른 그림 px 기준, "base":확대%) · "screen":1(화면 좌표) · "dash":[선,틈] · "op":불투명 · "closed":1(네모) · "blink":초(그린 뒤 깜빡임) · "pop":1(그리지 않고 박히듯 등장) 추가
  trans 에 "dir":-1 이면 휩이 반대 방향
  "notes":[{"s":0,"e":5,"text":"AI로 만든 연출 영상 · 가상인물"}]}
"""
import json, os, subprocess, sys, tempfile, time

AE = r"C:\Program Files\Adobe\Adobe After Effects 2026\Support Files\AfterFX.exe"
spec = json.load(open(sys.argv[1], encoding="utf-8"))
OUT = os.path.abspath(sys.argv[2])
for sh in spec["shots"]:
    if sh["src"] == "black":                      # 까만 배경(09-29 커뮤니티 세 칸)
        sh["video"] = False; continue
    sh["src"] = os.path.abspath(sh["src"]).replace("\\", "/")
    sh["video"] = sh["src"].lower().endswith((".mp4", ".mov"))
for o in spec.get("over", []):
    o["src"] = os.path.abspath(o["src"]).replace("\\", "/")
for m in spec.get("money", []):
    m["img"] = os.path.abspath(m["img"]).replace("\\", "/")


def rgb(h):
    return [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]


for sb in spec.get("subs", []):
    sb["runs"] = [[t, rgb(c)] for t, c in sb["runs"]]
for d in spec.get("draw", []):
    d["rgb"] = rgb(d.get("color", "#ff3b30"))
WORK = tempfile.mkdtemp(prefix="aer_")
jsx = os.path.join(WORK, "reel.jsx")
render_base = os.path.join(WORK, "reel_ae").replace("\\", "/")
log_path = os.path.join(WORK, "log.txt").replace("\\", "/")
open(jsx, "w", encoding="utf-8").write(r"""
app.preferences.savePrefAsLong("Main Pref Section", "Pref_SCRIPTING_FILE_NETWORK_SECURITY", 1);
var LOG = new File(%(log)s); LOG.encoding = "UTF-8"; LOG.open("w");
function L(s){ LOG.writeln(s); }
function TR(l){ return l.property("ADBE Transform Group"); }
function EZ(p, inf){ for (var i = 1; i <= p.numKeys; i++){ var n = (p.value instanceof Array) ? p.value.length : 1; var a = [];
  for (var d = 0; d < n; d++) a.push(new KeyframeEase(0, inf || 70)); try { p.setTemporalEaseAtKey(i, a, a); } catch (x) {} } }
function HOLDK(p, t){ p.setValueAtTime(t, p.valueAtTime(t, false)); }       // 바꾸기 전에 그 시각의 원래 값을 키로 고정
function FX(l, m){ return l.property("ADBE Effect Parade").addProperty(m); }
var CACHE = {};
function IMP(p){ if (!CACHE[p]) CACHE[p] = app.project.importFile(new ImportOptions(new File(p))); return CACHE[p]; }
try {
  if (!app.project) app.newProject();
  var S = %(spec)s, W = 1080, H = 1920, FR = S.fps || 30;
  var comp = app.project.items.addComp("reel", W, H, 1, S.length, FR); comp.motionBlur = true; comp.shutterAngle = 180;
  var bg = comp.layers.addSolid([0, 0, 0], "bg", W, H, 1, S.length);
  var TRS = S.trans || [], SH = S.shots, SL = [];
  function transAt(t){ for (var i = 0; i < TRS.length; i++) if (Math.abs(TRS[i].t - t) < 0.02) return TRS[i]; return null; }
  // ── 장면 ──
  for (var k = 0; k < SH.length; k++) {
    var sh = SH[k], tin = transAt(sh.s), tout = transAt(sh.e);
    var a = sh.s - (tin && tin.type != "cut" ? tin.dur / 2 : 0), b = sh.e + (tout && tout.type != "cut" ? tout.dur / 2 : 0);
    var ft = sh.src == "black" ? null : IMP(sh.src), host = comp, bx = sh.box || [0, 0, W, H];
    if (sh.box) { var sub = app.project.items.addComp("box" + k, bx[2], bx[3], 1, S.length, FR); var bl = comp.layers.add(sub);
      TR(bl).property("ADBE Position").setValue([bx[0] + bx[2] / 2, bx[1] + bx[3] / 2]); bl.inPoint = a; bl.outPoint = b; host = sub; sh._host = bl; }
    var ly = ft ? host.layers.add(ft) : host.layers.addSolid([0, 0, 0], "black" + k, bx[2], bx[3], 1, S.length); ly.motionBlur = true;
    if (!ft) ft = {width: bx[2], height: bx[3]};
    if (sh.video) { ly.startTime = a - (sh["in"] || 0) + 0; }
    ly.inPoint = a; ly.outPoint = b;
    var base = Math.max(bx[2] / ft.width, bx[3] / ft.height) * 100;
    var f = sh.from || [1, 0, 0], g = sh.to || [1.06, 0, 0], cx = bx[2] / 2, cy = bx[3] / 2;
    var sc = TR(ly).property("ADBE Scale"), ps = TR(ly).property("ADBE Position");
    sc.setValueAtTime(a, [base * f[0], base * f[0]]); sc.setValueAtTime(b, [base * g[0], base * g[0]]);
    ps.setValueAtTime(a, [cx + f[1], cy + f[2]]); ps.setValueAtTime(b, [cx + g[1], cy + g[2]]);
    sh._layer = ly; sh._top = sh._host || ly; sh._base = base; SL.push(sh);
  }
  // ── 전환 ──
  for (var i = 0; i < TRS.length; i++) {
    var tr = TRS[i], t = tr.t, d = tr.dur || 0.22;
    if (tr.type == "cut") continue;
    var adj = comp.layers.addSolid([1, 1, 1], "tr" + i, W, H, 1, S.length); adj.adjustmentLayer = true; adj.inPoint = t - d / 2 - 0.02; adj.outPoint = t + d / 2 + 0.02;
    var nxt = null, prv = null; for (var k = 0; k < SL.length; k++) { if (Math.abs(SL[k].s - t) < 0.02) nxt = SL[k]; if (Math.abs(SL[k].e - t) < 0.02) prv = SL[k]; }
    if (tr.type == "zoom") { var rb = FX(adj, "CC Radial Fast Blur"); var amt = rb.property(2);
      amt.setValueAtTime(t - d / 2, 0); amt.setValueAtTime(t, 85); amt.setValueAtTime(t + d / 2, 0); EZ(amt, 60);
      if (nxt) { var ns = TR(nxt._top).property("ADBE Scale"); HOLDK(ns, t + d / 2); var v = ns.valueAtTime(t + d / 2, false); ns.setValueAtTime(t - d / 2, [v[0] * 1.35, v[1] * 1.35]); }
      if (prv) { var psc = TR(prv._top).property("ADBE Scale"); HOLDK(psc, t - d / 2); var v2 = psc.valueAtTime(t - d / 2, false); psc.setValueAtTime(t + d / 2, [v2[0] * 1.5, v2[1] * 1.5]); } }
    if (tr.type == "whip") { var wd = tr.dir || 1; var db = FX(adj, "ADBE Motion Blur"); db.property(1).setValue(wd > 0 ? 135 : 45); var ln = db.property(2);
      ln.setValueAtTime(t - d / 2, 0); ln.setValueAtTime(t, 260); ln.setValueAtTime(t + d / 2, 0); EZ(ln, 60);
      if (prv) { var pp = TR(prv._top).property("ADBE Position"); HOLDK(pp, t - d / 2); var q = pp.valueAtTime(t - d / 2, false); pp.setValueAtTime(t + d / 2, [q[0] - 700 * wd, q[1] - 700]); }
      if (nxt) { var np = TR(nxt._top).property("ADBE Position"); HOLDK(np, t + d / 2); var q2 = np.valueAtTime(t + d / 2, false); np.setValueAtTime(t - d / 2, [q2[0] + 700 * wd, q2[1] + 700]); } }
    if (tr.type == "blur") { var gb = FX(adj, "ADBE Gaussian Blur 2"); var bb = gb.property(1);
      bb.setValueAtTime(t - d / 2, 0); bb.setValueAtTime(t, 90); bb.setValueAtTime(t + d / 2, 0); EZ(bb, 60); }
    if (tr.type == "lens") { var lr = null; try { lr = FX(adj, "ADBE Camera Lens Blur").property(1); } catch (x) { lr = FX(adj, "ADBE Gaussian Blur 2").property(1); }
      lr.setValueAtTime(t - d / 2, 0); lr.setValueAtTime(t, 55); lr.setValueAtTime(t + d / 2, 0); EZ(lr, 55); }
    if (tr.type == "flash") { adj.remove(); var wf = comp.layers.addSolid([1, 1, 1], "flash" + i, W, H, 1, S.length); wf.inPoint = t - d; wf.outPoint = t + d;
      wf.blendingMode = BlendingMode.ADD; var wo = TR(wf).property("ADBE Opacity"); wo.setValueAtTime(t - d, 0); wo.setValueAtTime(t, 100); wo.setValueAtTime(t + d, 0); EZ(wo, 50); }
    if (prv && nxt && tr.type != "flash") { var o1 = TR(nxt._top).property("ADBE Opacity"); o1.setValueAtTime(t - d / 2, 0); o1.setValueAtTime(t, 100); }
  }
  // ── 떠오르는 그림·카드·도장·전동차(over: 키 [t,x,y,확대,회전,불투명]) ──
  var OV = S.over || [];
  for (var i = 0; i < OV.length; i++) { var ov = OV[i], ol = comp.layers.add(IMP(ov.src)); ol.inPoint = ov.s; ol.outPoint = ov.e; ol.motionBlur = true;
    if (ov.parent != null) ol.parent = OV[ov.parent]._layer;                                  // 부모(지도 카드)에 붙임 → 좌표는 부모 그림 px(09-29 전동차)
    if (ov.autoOrient) ol.autoOrient = AutoOrientType.ALONG_PATH;                             // 경로 방향으로 저절로 돌기
    var oP = TR(ol).property("ADBE Position"), oS = TR(ol).property("ADBE Scale"), oR = TR(ol).property("ADBE Rotate Z"), oO = TR(ol).property("ADBE Opacity");
    for (var q = 0; q < ov.keys.length; q++) { var kk = ov.keys[q];
      oP.setValueAtTime(kk[0], [kk[1], kk[2]]); oS.setValueAtTime(kk[0], [kk[3] * 100, kk[3] * 100]); oR.setValueAtTime(kk[0], kk[4]); oO.setValueAtTime(kk[0], kk[5]); }
    if (ov.ease !== false) { EZ(oP, ov.ease || 70); EZ(oS, ov.ease || 70); EZ(oR, ov.ease || 70); }
    if (ov.autoOrient) for (var q = 1; q <= oP.numKeys; q++) { try { oP.setSpatialAutoBezierAtKey(q, true); } catch (x) {} }   // 곡선 경로를 매끈하게
    if (ov.shadow) { var ods = FX(ol, "ADBE Drop Shadow"); ods.property("ADBE Drop Shadow-0002").setValue(140); ods.property("ADBE Drop Shadow-0005").setValue(40); ods.property("ADBE Drop Shadow-0004").setValue(18); }
    ov._layer = ol; }
  // ── 그림 속 강조(그림·떠오른 그림에 붙음, screen 이면 화면 좌표) ──
  var DR = S.draw || [];
  for (var i = 0; i < DR.length; i++) {
    var dr = DR[i], host2 = dr.over != null ? {_layer: OV[dr.over]._layer, _base: dr.base || 100} : (dr.screen ? {_layer: null, _base: 100} : SL[dr.shot]);
    var par = host2._layer, hc = par ? par.containingComp : comp;
    var sl = hc.layers.addShape(); if (par) sl.parent = par; sl.inPoint = dr.s; sl.outPoint = dr.e;
    TR(sl).property("ADBE Position").setValue([0, 0]); TR(sl).property("ADBE Scale").setValue([100, 100]); TR(sl).property("ADBE Anchor Point").setValue([0, 0]);
    var gg = sl.property("ADBE Root Vectors Group").addProperty("ADBE Vector Group").property("ADBE Vectors Group");
    var sw = (dr.w || 10) * 100 / (host2._base || 100);
    if (dr.type == "ellipse" || dr.type == "ring") { var el = gg.addProperty("ADBE Vector Shape - Ellipse");
      el.property("ADBE Vector Ellipse Size").setValue([dr.r[0] * 2, dr.r[1] * 2]); el.property("ADBE Vector Ellipse Position").setValue(dr.pts[0]); }
    else { var shp = new Shape(); shp.vertices = dr.pts; shp.closed = !!dr.closed; gg.addProperty("ADBE Vector Shape - Group").property("ADBE Vector Shape").setValue(shp); }
    var st = gg.addProperty("ADBE Vector Graphic - Stroke"); st.property("ADBE Vector Stroke Color").setValue(dr.rgb); st.property("ADBE Vector Stroke Width").setValue(sw);
    st.property("ADBE Vector Stroke Line Cap").setValue(2);
    if (dr.type == "ring") { var sz = sl.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property(1).property("ADBE Vector Ellipse Size");
      sz.expression = "var p=((time-" + dr.s + ")*1.4)%%1; value*(0.4+p*1.2);";
      sl.property("ADBE Root Vectors Group").property(1).property("ADBE Vector Transform Group").property("ADBE Vector Group Opacity").expression = "var p=((time-" + dr.s + ")*1.4)%%1; 100*(1-p);"; }
    else if (!dr.pop) { var te = sl.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").addProperty("ADBE Vector Filter - Trim").property("ADBE Vector Trim End");
      te.setValueAtTime(dr.s, 0); te.setValueAtTime(dr.s + (dr.dur || 0.45), 100); EZ(te, 80); }
    if (dr.pop) { var mnx = 1e9, mny = 1e9, mxx = -1e9, mxy = -1e9;                       // 박히듯: 크게 → 살짝 작게 → 제자리(09-29)
      for (var q = 0; q < dr.pts.length; q++) { mnx = Math.min(mnx, dr.pts[q][0]); mny = Math.min(mny, dr.pts[q][1]); mxx = Math.max(mxx, dr.pts[q][0]); mxy = Math.max(mxy, dr.pts[q][1]); }
      var pc = [(mnx + mxx) / 2, (mny + mxy) / 2]; TR(sl).property("ADBE Anchor Point").setValue(pc); TR(sl).property("ADBE Position").setValue(pc);
      var psc = TR(sl).property("ADBE Scale"); psc.setValueAtTime(dr.s, [135, 135]); psc.setValueAtTime(dr.s + 0.06, [95, 95]); psc.setValueAtTime(dr.s + 0.12, [100, 100]); EZ(psc, 60); }
    if (dr.dash) { var st2 = sl.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke");
      var dsh = st2.property("ADBE Vector Stroke Dashes"); dsh.addProperty("ADBE Vector Stroke Dash 1").setValue(dr.dash[0]);
      sl.property("ADBE Root Vectors Group").property(1).property("ADBE Vectors Group").property("ADBE Vector Graphic - Stroke").property("ADBE Vector Stroke Dashes").addProperty("ADBE Vector Stroke Gap 1").setValue(dr.dash[1]); }
    if (dr.glow) { var gw = FX(sl, "ADBE Glo2"); try { gw.property("ADBE Glo2-0003").setValue(30); gw.property("ADBE Glo2-0004").setValue(1.2); } catch (x) {} }
    var so = TR(sl).property("ADBE Opacity"), sop = dr.op || 100; so.setValueAtTime(dr.s, sop); so.setValueAtTime(dr.e - 0.15, sop); so.setValueAtTime(dr.e, 0);
    if (dr.blink) so.expression = "var u = time - " + (dr.s + (dr.dur || 0.45)) + "; (u > 0 && u < " + dr.blink + " && Math.floor(u * 7) - 2 * Math.floor(u * 3.5) == 1) ? 12 : value;";   // 깜빡깜빡(09-29)
  }
  for (var i = 0; i < OV.length; i++) if (OV[i].top) OV[i]._layer.moveToBeginning();   // 강조 선보다 위(전동차가 선에 묻히지 않게, 09-29)
  // ── 지폐 비 ──
  var MN = S.money || [];
  for (var i = 0; i < MN.length; i++) { var mn = MN[i], mf = IMP(mn.img); var seed = 7;
    function rnd(){ seed = (seed * 9301 + 49297) %% 233280; return seed / 233280; }
    for (var j = 0; j < (mn.n || 24); j++) { var m = comp.layers.add(mf); var t0 = mn.s + rnd() * 0.5, t1 = Math.min(mn.e + 0.3, t0 + 1.1 + rnd() * 0.8);
      m.inPoint = t0; m.outPoint = t1; m.motionBlur = true; var x = 80 + rnd() * 920, ms = (260 + rnd() * 240) / mf.width * 100;
      TR(m).property("ADBE Scale").setValue([ms, ms]);
      var mp = TR(m).property("ADBE Position"); mp.setValueAtTime(t0, [x, -250]); mp.setValueAtTime(t1, [x + (rnd() - 0.5) * 400, 2150]);
      var mr = TR(m).property("ADBE Rotate Z"); mr.setValueAtTime(t0, rnd() * 360); mr.setValueAtTime(t1, rnd() * 900 - 450);
      m.threeDLayer = true; var ry = TR(m).property("ADBE Rotate Y"); ry.setValueAtTime(t0, 0); ry.setValueAtTime(t1, 360 + rnd() * 360); } }
  // ── 자막(한 줄, 흐림→선명·살짝 크게 박힘, 핵심 낱말 색) ──
  var SB = S.subs || [];
  for (var i = 0; i < SB.length; i++) { var sb = SB[i], size = sb.size || 66, y = sb.y || 1330, lays = [], wsum = 0;
    var gp = comp.layers.addNull(); gp.inPoint = sb.s; gp.outPoint = sb.e; TR(gp).property("ADBE Anchor Point").setValue([0, 0]); TR(gp).property("ADBE Position").setValue([W / 2, y]);
    for (var r = 0; r < sb.runs.length; r++) { var T = comp.layers.addText(sb.runs[r][0]); var spp = T.property("ADBE Text Properties").property("ADBE Text Document"); var td = spp.value;
      td.resetCharStyle(); td.font = "Pretendard-ExtraBold"; td.fontSize = size; td.fillColor = sb.runs[r][1]; td.applyStroke = true; td.strokeColor = [0, 0, 0];
      td.strokeWidth = size * 0.13; td.strokeOverFill = false; td.justification = ParagraphJustification.LEFT_JUSTIFY; spp.setValue(td);
      T.inPoint = sb.s; T.outPoint = sb.e; var rc = T.sourceRectAtTime(sb.s, false); lays.push([T, rc]); wsum += rc.width; }
    var x0 = -wsum / 2;
    for (var r = 0; r < lays.length; r++) { var T2 = lays[r][0], rc2 = lays[r][1]; T2.parent = gp;
      TR(T2).property("ADBE Position").setValue([x0 - rc2.left, size * 0.35]); x0 += rc2.width;
      var bl2 = FX(T2, "ADBE Box Blur2").property(1); bl2.setValueAtTime(sb.s, 10); bl2.setValueAtTime(sb.s + 0.09, 0);
      var ds = FX(T2, "ADBE Drop Shadow"); ds.property("ADBE Drop Shadow-0002").setValue(160); ds.property("ADBE Drop Shadow-0005").setValue(10); ds.property("ADBE Drop Shadow-0004").setValue(3); }
    var gs = TR(gp).property("ADBE Scale"), pk = sb.pop ? 1.28 : 1.12;
    gs.setValueAtTime(sb.s, [100 * pk, 100 * pk]); gs.setValueAtTime(sb.s + 0.09, [98, 98]); gs.setValueAtTime(sb.s + 0.15, [100, 100]); EZ(gs, 60); }
  // ── 좌하단 작은 고지 ──
  var NT = S.notes || [];
  for (var i = 0; i < NT.length; i++) { var nt = NT[i], N = comp.layers.addText(nt.text); var sp2 = N.property("ADBE Text Properties").property("ADBE Text Document"); var tn = sp2.value;
    tn.resetCharStyle(); tn.font = "Pretendard-Regular"; tn.fontSize = 22; tn.fillColor = [1, 1, 1]; tn.applyStroke = false; tn.justification = ParagraphJustification.LEFT_JUSTIFY; sp2.setValue(tn);
    N.inPoint = nt.s; N.outPoint = nt.e; TR(N).property("ADBE Position").setValue([40, 1870]); TR(N).property("ADBE Opacity").setValue(55); }
  var rq = app.project.renderQueue.items.add(comp); var om = rq.outputModule(1); om.applyTemplate("H.264 - 렌더링 일치 설정 - 40Mbps"); om.file = new File(%(out)s);
  L("shots " + SH.length); app.project.renderQueue.render(); L("render done");
} catch (e) { L("ERROR " + e.toString() + " line " + e.line); }
LOG.close();
app.project.close(CloseOptions.DO_NOT_SAVE_CHANGES);
app.quit();
""" % {"log": json.dumps(log_path), "spec": json.dumps(spec, ensure_ascii=False), "out": json.dumps(render_base)})

proc = subprocess.Popen([AE, "-noui", "-r", jsx], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
t0, done_at = time.time(), None
while True:
    time.sleep(3)
    txt = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else ""
    if ("render done" in txt or "ERROR" in txt) and done_at is None:
        done_at = time.time()
    if (done_at and time.time() - done_at > 20) or time.time() - t0 > 3000 or (proc.poll() is not None and done_at):
        break
subprocess.run(["taskkill", "/IM", "AfterFX.exe", "/F"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)   # AE 가 남지 않게(09-28)
log = open(log_path, encoding="utf-8", errors="replace").read() if os.path.exists(log_path) else "(로그 없음)"
print(log.strip())
cands = [f for f in os.listdir(WORK) if f.startswith("reel_ae")]
if "render done" not in log or not cands:
    raise SystemExit("AE 렌더 실패: " + WORK)
subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", os.path.join(WORK, cands[0]), "-c:v", "libx264", "-crf", "16", "-pix_fmt", "yuv420p", "-r", str(spec.get("fps", 30)), "-an", OUT], check=True)
print("AE REEL", OUT)
