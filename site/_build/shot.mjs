// 공개 화면 캡처기 (로그인 없는 새 프로필). 사용: node shot.mjs <url> <out.png> <width> <height> [selector1|selector2|...] [pre-js]
// 결과: out.png + out.json (선택자마다 위치 상자). 빨간 표시는 mark.py 가 json 을 읽어 그린다.
import { spawn } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const [url, out, W = "1200", H = "800", sels = "", pre = ""] = process.argv.slice(2);
const w = +W, h = +H;
const prof = process.env.TEMP + "/edge-shot";
const p = spawn(EDGE, ["--headless=new", "--disable-gpu", "--remote-debugging-port=9337", "--user-data-dir=" + prof, `--window-size=${w},${h}`, "--lang=ko-KR", "--hide-scrollbars", url], { stdio: "ignore" });
const get = (u) => new Promise(r => http.get(u, res => { let d = ""; res.on("data", c => d += c); res.on("end", () => r(JSON.parse(d))) }));
await new Promise(r => setTimeout(r, 6000));
const tabs = await get("http://127.0.0.1:9337/json");
const t = tabs.find(x => x.type === "page" && !x.url.startsWith("edge://"));
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0;
const send = (m, params) => new Promise(r => { const i = ++id; ws.addEventListener("message", function hh(e) { const d = JSON.parse(e.data); if (d.id === i) { ws.removeEventListener("message", hh); r(d.result); } }); ws.send(JSON.stringify({ id: i, method: m, params })); });
await send("Emulation.setDeviceMetricsOverride", { width: w, height: h, deviceScaleFactor: 1, mobile: false });
await send("Emulation.setLocaleOverride", { locale: "ko-KR" });
if (pre) { await send("Runtime.evaluate", { expression: pre, awaitPromise: true }); await new Promise(r => setTimeout(r, 2500)); }
await new Promise(r => setTimeout(r, 1500));
const expr = `(()=>{const sels=${JSON.stringify(sels.split("|").filter(Boolean))};let noscroll=false;const find=(s)=>{let up=false;if(s.startsWith("!")){noscroll=true;s=s.slice(1);}if(s.startsWith("^")){up=true;s=s.slice(1);}const el=find0(s);return (up&&el)?(el.closest("a,button,li,label")||el):el;};const find0=(s)=>{let big=false;if(s.startsWith("big:")){big=true;s=s.slice(4);}if(s.startsWith("text=")){const q=s.slice(5);let best=null,ba=big?0:1e12;for(const e of document.querySelectorAll("a,button,span,div,h1,h2,h3,h4,p,li,label,strong,em")){const tx=(e.innerText||"").trim().replace(/\s+/g," ");if(!tx.includes(q))continue;const r=e.getBoundingClientRect();const a=r.width*r.height;if(a>0&&(big?(a>ba&&a<200000):a<ba)){ba=a;best=e;}}return best;}try{return document.querySelector(s);}catch(e){return null;}};
// 배너 제거(웨일 설치 안내 등)
for(const e of document.querySelectorAll("div,section,aside")){const tx=(e.innerText||"");if(e.children.length<8&&tx.length<200&&/웨일|브라우저를 업데이트/.test(tx)&&e.getBoundingClientRect().height<200){e.remove();}}
const first=(sels.length&&!sels[0].replace(/^!/,"").startsWith("box="))?find(sels[0]):null;if(first&&!noscroll){first.scrollIntoView({block:"center"});}
const out=[];for(let s of sels){if(s.startsWith("!")){noscroll=true;s=s.slice(1);}if(s.startsWith("box=")){const [x,y,w,h]=s.slice(4).split(",").map(Number);out.push({sel:s,x,y,w,h});continue;}const el=find(s);if(!el){out.push(null);continue;}const r=el.getBoundingClientRect();out.push({sel:s,x:r.left,y:r.top,w:r.width,h:r.height});}
return JSON.stringify({url:location.href,title:document.title,boxes:out});})()`;
await send("Runtime.evaluate", { expression: expr, returnByValue: true });
await new Promise(r => setTimeout(r, 800));
const res = await send("Runtime.evaluate", { expression: expr, returnByValue: true });
const shot = await send("Page.captureScreenshot", { format: "png" });
fs.writeFileSync(out, Buffer.from(shot.data, "base64"));
fs.writeFileSync(out.replace(/\.png$/, ".json"), res.result.value);
console.log(res.result.value);
ws.close(); p.kill();
