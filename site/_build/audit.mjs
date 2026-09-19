// 모든 페이지 × 여러 폭에서 가로 넘침·글자 잘림을 검사한다.
import { spawn } from "node:child_process";
import http from "node:http";
import fs from "node:fs";
const EDGE = "C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe";
const base = "http://127.0.0.1:8765";
const urls = JSON.parse(fs.readFileSync(process.argv[2], "utf8"));
const widths = (process.argv[3] || "360,400,768,1024,1366").split(",").map(Number);
const p = spawn(EDGE, ["--headless=new","--disable-gpu","--remote-debugging-port=9334","--user-data-dir="+process.env.TEMP+"/edge-audit","--window-size=1366,900","about:blank"],{stdio:"ignore"});
const get = (u)=>new Promise((r,rej)=>http.get(u,res=>{let d="";res.on("data",c=>d+=c);res.on("end",()=>{try{r(JSON.parse(d))}catch(e){rej(e)}})}).on("error",rej));
let tabs = null;                                                                 // 디버그 포트가 열릴 때까지 최대 30초 기다린다 (2026-09-19: 4초 고정 대기는 다른 Edge 가 많을 때 ECONNREFUSED)
for (let i = 0; i < 30 && !tabs; i++) {
  await new Promise(r=>setTimeout(r,1000));
  try { tabs = await get("http://127.0.0.1:9334/json"); } catch (e) { tabs = null; }
}
if (!tabs) { console.error("Edge 디버그 포트 9334 가 30초 안에 안 열림"); p.kill(); process.exit(2); }
let t = tabs.find(x=>x.type==="page");
const ws = new WebSocket(t.webSocketDebuggerUrl);
await new Promise(r=>ws.onopen=r);
let id=0; const send=(m,params)=>new Promise((r,rej)=>{const i=++id; const to=setTimeout(()=>{ws.removeEventListener("message",h); rej(new Error("timeout "+m));},25000); function h(e){const d=JSON.parse(e.data); if(d.id===i){clearTimeout(to); ws.removeEventListener("message",h); r(d.result);}} ws.addEventListener("message",h); ws.send(JSON.stringify({id:i,method:m,params}));});   // 응답이 25초 안 오면 넘어간다 (2026-09-19: 죽은 탭에서 영원히 기다리던 것)
await send("Page.enable",{});
const expr = `(()=>{
  const vw=document.documentElement.clientWidth; const out=[];
  const path=(el)=>{let s=el.tagName.toLowerCase(); if(el.id) s+='#'+el.id; if(el.className&&typeof el.className==='string') s+='.'+el.className.trim().split(/\\s+/).join('.'); return s;};
  for(const el of document.querySelectorAll('body *')){
    const r=el.getBoundingClientRect(); if(r.width===0) continue;
    const cs=getComputedStyle(el);
    if(r.right>vw+1 && cs.position!=='fixed' && !el.closest('figure,table') && !el.closest('nav.tabs .subs .wrap')) out.push('OVER '+path(el)+' right='+Math.round(r.right)+' vw='+vw+' text='+(el.textContent||'').trim().slice(0,30));
    if(cs.overflow==='hidden' || cs.overflowX==='hidden' || cs.textOverflow==='ellipsis'){
      if(el.scrollWidth>el.clientWidth+1 && !['TABLE','PRE','FIGURE','svg','NAV'].includes(el.tagName) && !el.closest('table,pre,figure,nav.tabs')) out.push('CLIP '+path(el)+' sw='+el.scrollWidth+' cw='+el.clientWidth+' text='+(el.textContent||'').trim().slice(0,30));
    }
  }
  // 부모 상자 밖으로 삐져나온 글자 (overflow visible 인 경우)
  for(const el of document.querySelectorAll('main *, aside *, header *, nav *, footer *')){
    if(el.closest('svg')) continue;
    const r=el.getBoundingClientRect(); if(r.width===0||r.height===0) continue;
    const pr=el.parentElement.getBoundingClientRect();
    if(r.right>pr.right+2 && getComputedStyle(el).position!=='absolute' && getComputedStyle(el.parentElement).overflow==='visible' && !['TABLE','TR','TD','TH'].includes(el.tagName) && !el.closest('table,figure'))
      out.push('SPILL '+path(el)+' right='+Math.round(r.right)+' parent='+Math.round(pr.right)+' text='+(el.textContent||'').trim().slice(0,30));
  }
  // SVG 안 글자가 그림 밖으로
  for(const s of document.querySelectorAll('svg')){
    const sr=s.getBoundingClientRect();
    for(const tx of s.querySelectorAll('text')){
      const b=tx.getBoundingClientRect();
      if(b.right>sr.right+1||b.left<sr.left-1) out.push('SVGTEXT '+(tx.textContent||'').trim().slice(0,30)+' right='+Math.round(b.right)+' svg='+Math.round(sr.right));
    }
    // 글자가 같은 svg 안의 다른 글자와 겹침
    const ts=[...s.querySelectorAll('text')].map(t=>[t,t.getBoundingClientRect()]);
    for(let i=0;i<ts.length;i++) for(let j=i+1;j<ts.length;j++){const a=ts[i][1],b=ts[j][1]; if(a.width&&b.width&&a.left<b.right-2&&b.left<a.right-2&&a.top<b.bottom-2&&b.top<a.bottom-2) out.push('SVGOVERLAP '+ts[i][0].textContent.trim().slice(0,20)+' / '+ts[j][0].textContent.trim().slice(0,20));}
  }
  const sw=document.documentElement.scrollWidth; if(sw>vw+1) out.unshift('PAGE scrollWidth '+sw+' > '+vw);
  return out.slice(0,40);
})()`;
const results = {};
for (const w of widths) {
  await send("Emulation.setDeviceMetricsOverride",{width:w,height:1200,deviceScaleFactor:1,mobile:w<800});
  for (const u of urls) {
    let v = [];
    try {
      await send("Page.navigate",{url:base+u});
      await new Promise(r=>setTimeout(r,700));
      const res = await send("Runtime.evaluate",{expression:expr,returnByValue:true});
      v = res && res.result && res.result.value || [];
    } catch (e) { v = ["ERROR " + e.message]; }
    if (v.length) { results[w] ??= {}; results[w][u] = v; }
  }
}
fs.writeFileSync(process.argv[4] || "audit.json", JSON.stringify(results,null,1));
let n=0; for (const w in results) for (const u in results[w]) { n++; console.log(w, u); for (const l of results[w][u]) console.log("   ", l); }
console.log("pages with issues:", n);
ws.close(); p.kill();
