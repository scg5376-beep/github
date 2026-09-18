// GA4 가 실제로 요청을 보내는지 + CSP 오류가 없는지 (D65). 사용: node _build/ga_probe.mjs https://sajangmarketing.com/
import { spawn } from "node:child_process"; import http from "node:http";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const url = process.argv[2] || "https://sajangmarketing.com/";
const p = spawn(EDGE, ["--headless=new","--disable-gpu","--no-first-run","--disable-sync","--remote-debugging-port=9334","--user-data-dir="+process.env.TEMP+"/edge-ovf","about:blank"],{stdio:"ignore"});
const get = (u)=>new Promise(r=>http.get(u,res=>{let d="";res.on("data",c=>d+=c);res.on("end",()=>r(JSON.parse(d)))}));
await new Promise(r=>setTimeout(r,4000));
const tabs = await get("http://127.0.0.1:9334/json"); const t = tabs.find(x=>x.type==="page");
const ws = new WebSocket(t.webSocketDebuggerUrl); await new Promise(r=>ws.onopen=r);
let id=0; const hits=[], errs=[];
const send=(m,params)=>new Promise(r=>{const i=++id; ws.addEventListener("message",function h(e){const d=JSON.parse(e.data); if(d.id===i){ws.removeEventListener("message",h); r(d.result);}}); ws.send(JSON.stringify({id:i,method:m,params}));});
ws.addEventListener("message",e=>{const d=JSON.parse(e.data);
  if(d.method==="Network.requestWillBeSent"){const u=d.params.request.url; if(/google-analytics|googletagmanager|analytics\.google/.test(u)) hits.push(u.slice(0,100));}
  if(d.method==="Log.entryAdded" && d.params.entry.level==="error") errs.push(d.params.entry.text.slice(0,200));
  if(d.method==="Runtime.exceptionThrown") errs.push("EXC "+(d.params.exceptionDetails.text||"").slice(0,200));});
await send("Network.enable",{}); await send("Log.enable",{}); await send("Runtime.enable",{});
await send("Page.navigate",{url}); await new Promise(r=>setTimeout(r,8000));
console.log("GA requests:",hits.length); hits.forEach(h=>console.log(" ",h)); console.log("errors:",errs.length); errs.forEach(x=>console.log(" ",x));
ws.close(); spawn("taskkill",["/PID",String(p.pid),"/T","/F"],{stdio:"ignore"});
