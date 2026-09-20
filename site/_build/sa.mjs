// 서치어드바이저 수집요청 도우미 (운영자 2026-09-20 "수집요청 네가 브라우저 제어해서 해").
// 로그인은 운영자가 눈에 보이는 창에서 직접 한다. 이 스크립트는 열려 있는 창에 CDP 로 붙어 주소를 넣고 「확인」을 누른다.
//   node sa.mjs open                 → 전용 프로필(edge-sa)로 Edge 창을 열고 수집요청 화면으로 간다 (로그인은 사람이)
//   node sa.mjs dom                  → 지금 화면의 입력칸·단추·안내문을 찍어 본다
//   node sa.mjs submit urls.txt [n]  → 파일의 주소를 한 줄씩 넣고 제출, 결과 문구를 남긴다 (n 개까지)
import { spawn } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const PORT = 9444, SITE = "https://sajangmarketing.com";
const PAGE = `https://searchadvisor.naver.com/console/site/request/crawl?site=${encodeURIComponent(SITE)}`;
const cmd = process.argv[2];
const get = (u) => new Promise((r, j) => http.get(u, res => { let d = ""; res.on("data", c => d += c); res.on("end", () => { try { r(JSON.parse(d)); } catch (e) { j(e); } }); }).on("error", j));
const sleep = (ms) => new Promise(r => setTimeout(r, ms));

if (cmd === "open") {
  spawn(EDGE, ["--no-first-run", "--disable-sync", `--remote-debugging-port=${PORT}`, "--user-data-dir=" + process.env.TEMP + "/edge-sa", "--window-size=1200,900", PAGE], { detached: true, stdio: "ignore" }).unref();
  console.log("opened", PAGE);
  process.exit(0);
}

const tabs = await get(`http://127.0.0.1:${PORT}/json`);
const t = tabs.find(x => x.type === "page" && x.url.includes("searchadvisor")) || tabs.find(x => x.type === "page");
if (!t) { console.log("no tab"); process.exit(1); }
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r => ws.onopen = r);
let id = 0;
const send = (m, params) => new Promise(r => { const i = ++id; ws.addEventListener("message", function h(e) { const d = JSON.parse(e.data); if (d.id === i) { ws.removeEventListener("message", h); r(d.result); } }); ws.send(JSON.stringify({ id: i, method: m, params })); });
const ev = async (expr) => (await send("Runtime.evaluate", { expression: expr, returnByValue: true, awaitPromise: true })).result?.value;

if (cmd === "dom") {
  console.log("url:", t.url);
  const out = await ev(`(()=>{const q=s=>[...document.querySelectorAll(s)];return {inputs:q('input,textarea').map(e=>({tag:e.tagName,type:e.type,name:e.name,id:e.id,ph:e.placeholder,val:e.value.slice(0,80),vis:!!e.offsetParent})),buttons:q('button,a.btn,input[type=submit]').filter(e=>e.offsetParent).map(e=>({tag:e.tagName,text:(e.innerText||e.value||'').trim().slice(0,30),cls:e.className.slice(0,60)})),text:document.body.innerText.slice(0,1500)}})()`);
  console.log(JSON.stringify(out, null, 1));
}

if (cmd === "submit") {
  const urls = fs.readFileSync(process.argv[3], "utf8").split(/\r?\n/).map(s => s.trim()).filter(s => s.startsWith("http"));
  const n = +(process.argv[4] || urls.length);
  const log = [];
  for (const u of urls.slice(0, n)) {
    const path = u;
    await ev(`(()=>{const inp=document.querySelector('input[type="text"]');inp.focus();inp.select();})()`);
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "a", modifiers: 2, commands: ["selectAll"] });
    await send("Input.dispatchKeyEvent", { type: "keyDown", key: "Backspace", windowsVirtualKeyCode: 8 });
    await send("Input.dispatchKeyEvent", { type: "keyUp", key: "Backspace", windowsVirtualKeyCode: 8 });
    await send("Input.insertText", { text: path });
    await sleep(400);
    const r = await ev(`(async()=>{const inp=document.querySelector('input[type="text"],input:not([type]),textarea');if(!inp)return 'no-input';if(inp.value!==${JSON.stringify(path)})return 'typed:'+inp.value;const btn=[...document.querySelectorAll('button')].find(b=>b.offsetParent&&/확인|요청|제출/.test(b.innerText));if(!btn)return 'no-button';const before=document.body.innerText;btn.click();await new Promise(r=>setTimeout(r,2500));const after=document.body.innerText;const diff=after.split('\\n').filter(l=>!before.includes(l)).join(' | ');const toast=[...document.querySelectorAll('.toast,[class*=toast],[class*=alert],[class*=message],[class*=msg]')].map(e=>e.innerText.trim()).filter(Boolean).join(' | ');return (toast||diff||'?').slice(0,200)})()`);
    log.push(`${u} → ${r}`);
    console.log(log[log.length - 1]);
    if (/한도|초과|limit|더 이상/.test(String(r))) { console.log("한도에 걸린 듯 — 멈춤"); break; }
    await sleep(1500);
  }
  fs.appendFileSync(process.env.TEMP + "/sa-log.txt", new Date().toISOString() + "\n" + log.join("\n") + "\n");
}
ws.close();
