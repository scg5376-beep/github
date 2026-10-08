// 공유 그림(og) 일괄 캡처기 — Edge 를 한 번만 띄우고 작업 목록의 html 을 차례로 열어 1200×630 JPEG 로 저장한다.
// 사용: node og_shots.mjs jobs.json      jobs = [{ "file": "C:/…/slug.html", "out": "C:/…/slug.jpg" }, …]
// og_pages.py 가 부른다. 한 장에 1초 안팎.
import { spawn } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const jobs = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
if (!jobs.length) { console.log("og: 할 일 없음"); process.exit(0); }
const PORT = 9351;
const prof = process.env.TEMP + "/edge-og";
const p = spawn(EDGE, ["--headless=new", "--disable-gpu", `--remote-debugging-port=${PORT}`, "--user-data-dir=" + prof, "--window-size=1200,630", "--lang=ko-KR", "--hide-scrollbars", "--allow-file-access-from-files", "about:blank"], { stdio: "ignore" });
const get = (u) => new Promise(r => http.get(u, res => { let d = ""; res.on("data", c => d += c); res.on("end", () => r(JSON.parse(d))) }));
await new Promise(r => setTimeout(r, 5000));
const tabs = await get(`http://127.0.0.1:${PORT}/json`);
const t = tabs.find(x => x.type === "page");
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0;
const send = (m, params) => new Promise(r => { const i = ++id; ws.addEventListener("message", function hh(e) { const d = JSON.parse(e.data); if (d.id === i) { ws.removeEventListener("message", hh); r(d.result); } }); ws.send(JSON.stringify({ id: i, method: m, params })); });
await send("Page.enable", {});
await send("Emulation.setDeviceMetricsOverride", { width: 1200, height: 630, deviceScaleFactor: 1, mobile: false });
let n = 0;
for (const j of jobs) {
  const url = "file:///" + j.file.replace(/\\/g, "/");
  const loaded = new Promise(r => { const hh = (e) => { const d = JSON.parse(e.data); if (d.method === "Page.loadEventFired") { ws.removeEventListener("message", hh); r(); } }; ws.addEventListener("message", hh); setTimeout(r, 4000); });
  await send("Page.navigate", { url });
  await loaded;
  await send("Runtime.evaluate", { expression: "document.fonts ? document.fonts.ready.then(()=>1) : 1", awaitPromise: true });
  await new Promise(r => setTimeout(r, 250));
  const shot = await send("Page.captureScreenshot", { format: "jpeg", quality: 82 });
  fs.writeFileSync(j.out, Buffer.from(shot.data, "base64"));
  n++;
}
console.log(`og: ${n}장 저장`);
ws.close(); p.kill();
