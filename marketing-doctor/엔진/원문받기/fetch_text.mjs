// 헤들리스 Edge 로 페이지를 열어 본문 텍스트를 저장한다. usage: node fetch_text.mjs URL OUT.txt [waitMs]
import { spawn } from "node:child_process";
import http from "node:http"; import fs from "node:fs";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const [url, out, waitMs] = [process.argv[2], process.argv[3], +(process.argv[4]||7000)];
const port = 9400 + Math.floor(Math.random()*90);
const p = spawn(EDGE, ["--headless=new","--disable-gpu","--remote-debugging-port="+port,"--user-data-dir="+process.env.TEMP+"/edge-ft"+port,"--window-size=1280,900","--lang=ko-KR","--no-first-run","--disable-sync",url],{stdio:"ignore"});
const get = (u)=>new Promise(r=>http.get(u,res=>{let d="";res.on("data",c=>d+=c);res.on("end",()=>r(JSON.parse(d)))}));
await new Promise(r=>setTimeout(r,waitMs));
try{
 const tabs = await get(`http://127.0.0.1:${port}/json`);
 const t = tabs.find(x=>x.type==="page" && !x.url.startsWith("edge://")) || tabs[0];
 const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
 let id=0; const send=(m,params)=>new Promise(r=>{const i=++id; ws.addEventListener("message",function h(e){const d=JSON.parse(e.data); if(d.id===i){ws.removeEventListener("message",h); r(d.result);}}); ws.send(JSON.stringify({id:i,method:m,params}));});
 const expr = fs.readFileSync(new URL("./fetch_expr.js", import.meta.url), "utf8");
 let res = await send("Runtime.evaluate",{expression:expr,returnByValue:true}); await new Promise(r=>setTimeout(r,800)); res = await send("Runtime.evaluate",{expression:expr,returnByValue:true});
 const v = JSON.parse(res.result.value);
 fs.writeFileSync(out, `# ${v.title}\n# ${v.url}\n\n${v.text}`);
 console.log(`${v.title} | ${v.url} | ${v.text.length} chars`);
 ws.close();
}catch(e){console.log("ERR",e.message);} p.kill();
