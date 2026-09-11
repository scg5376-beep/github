(()=>{
  for (const b of document.querySelectorAll('details:not([open])')) { try { b.open=true; } catch(e){} }
  const m = document.querySelector('main, article, [role=main]') || document.body;
  let t = m.innerText || "";
  if (t.length < 1500) t = document.body.innerText || "";
  if (t.length < 1500) {
    const c = document.body.cloneNode(true);
    c.querySelectorAll('script, style, noscript, template, svg').forEach(e=>e.remove());
    t = (c.textContent||"").replace(/[ \t]+/g," ").replace(/\s*\n\s*/g,"\n").replace(/\n{3,}/g,"\n\n");
  }
  return JSON.stringify({title: document.title, url: location.href, text: t});
})()
