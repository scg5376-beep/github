// 묻고 답하기 게시판 — ask.sajangmarketing.com (Cloudflare Worker + D1)
// 운영자 2026-10-06: «사용자들이 궁금한걸 묻는 문의사항페이지도 두고싶은데 이거는 닉네임이랑 비밀번호 입력해서 수정 및 삭제 할수 있게끔 설계해서 만들어줘»
//
// 원칙(설계기준 D 번호는 site/docs/설계기준.md):
// - 자바스크립트 없이 돈다. 모든 화면은 서버가 그린 HTML, 입력은 평범한 form POST. 어르신 휴대폰에서도 같다.
// - 개인정보를 받지 않는다. 닉네임·비밀번호(해시만 저장)·제목·내용뿐. 글 속 전화번호·메일은 저장할 때 가린다.
// - 비밀번호: PBKDF2-SHA256 20,000회 + 글마다 다른 소금. 원문은 어디에도 남지 않는다.
// - IP 원문을 저장하지 않는다. 도배·비밀번호 맞히기 막기에만 HMAC(비밀값, IP+날짜) 앞 16글자를 2일 동안 쓴다.
// - 답변은 운영자(관리자 비밀번호 = 비밀값 ADMIN_KEY)만 단다. 비밀값은 `wrangler secret put` 으로만 넣는다(공개 레포).

const SITE = "https://sajangmarketing.com";
const PER_PAGE = 15;
const ITER = 20000; // 무료 요금제 CPU 한도(요청당 10ms) 안에서 도는 값. 이 비밀번호는 «내 글 고치기»만 지킨다
const LIM = { nick: [2, 12], pw: [4, 32], title: [2, 60], body: [5, 3000], answer: [1, 5000] };

export default {
  async fetch(req, env) {
    try {
      return await route(req, env);
    } catch (e) {
      console.error(e && e.stack || e);
      return page(env, "잠시 문제가 생겼어요", `<p class="lead">잠시 문제가 생겼어요. 조금 뒤에 다시 해 주세요.</p>${home()}`, 500);
    }
  },
};

async function route(req, env) {
  const url = new URL(req.url);
  const p = url.pathname.replace(/\/+$/, "") || "/";
  const m = req.method;
  if (p === "/robots.txt") return new Response("User-agent: *\nDisallow: /new\nDisallow: /q/*/edit\nDisallow: /q/*/delete\nDisallow: /q/*/answer\n", { headers: { "content-type": "text/plain; charset=utf-8" } });
  if (p === "/favicon.ico") return Response.redirect(SITE + "/favicon.ico", 301);
  if (p === "/" && m === "GET") return list(env, url);
  if (p === "/new") return m === "POST" ? createPost(req, env) : writeForm(env);
  const mm = p.match(/^\/q\/(\d+)(?:\/(edit|delete|answer))?$/);
  if (mm) {
    const id = Number(mm[1]), act = mm[2] || "view";
    if (act === "view" && m === "GET") return view(env, id, url);
    if (act === "edit") return m === "POST" ? doEdit(req, env, id) : editForm(env, id);
    if (act === "delete") return m === "POST" ? doDelete(req, env, id) : deleteForm(env, id);
    if (act === "answer") return m === "POST" ? doAnswer(req, env, id) : answerForm(env, id);
  }
  return page(env, "찾는 화면이 없어요", `<p class="lead">찾는 화면이 없어요.</p>${home()}`, 404);
}

// ───────────── 화면

async function list(env, url) {
  const n = Math.max(1, parseInt(url.searchParams.get("page") || "1", 10) || 1);
  const { results } = await env.DB.prepare(
    "SELECT id, nick, title, created, answered FROM posts WHERE hidden = 0 ORDER BY id DESC LIMIT ? OFFSET ?"
  ).bind(PER_PAGE + 1, (n - 1) * PER_PAGE).all();
  const more = results.length > PER_PAGE;
  const rows = results.slice(0, PER_PAGE).map(r => `
    <li><a href="/q/${r.id}">
      <span class="badge ${r.answered ? "done" : "wait"}">${r.answered ? "답변 완료" : "답변 기다림"}</span>
      <strong>${esc(r.title)}</strong>
      <span class="meta">${esc(r.nick)} · ${day(r.created)}</span>
    </a></li>`).join("");
  const nav = (n > 1 ? `<a class="btn ghost" href="/?page=${n - 1}">← 앞 쪽</a>` : "") + (more ? `<a class="btn ghost" href="/?page=${n + 1}">다음 쪽 →</a>` : "");
  return page(env, "묻고 답하기", `
    <p class="lead">가게 홍보를 하다가 막힌 것을 물어보세요. 운영자가 읽고 답을 달아 드려요.</p>
    <ol class="steps">
      <li><b>1</b>아래 <em>질문 쓰기</em>를 누르세요</li>
      <li><b>2</b>닉네임과 비밀번호를 정해 적으세요</li>
      <li><b>3</b>답이 달리면 이 목록에 <em>답변 완료</em>가 떠요</li>
    </ol>
    <p><a class="btn big" href="/new">질문 쓰기</a></p>
    <h2>올라온 질문</h2>
    ${rows ? `<ul class="list">${rows}</ul>` : `<p class="empty">아직 올라온 질문이 없어요. 첫 질문을 남겨 보세요.</p>`}
    ${nav ? `<p class="pager">${nav}</p>` : ""}`, 200, { index: true });
}

function writeForm(env, v = {}, err = "") {
  return tokenized(env, async tok => page(env, "질문 쓰기", `
    ${err ? `<p class="err" role="alert">${esc(err)}</p>` : ""}
    <form method="post" action="/new" class="card">
      ${tok}
      <label>닉네임 <small>(2~12자, 다른 사람에게 보여요)</small><input name="nick" required minlength="2" maxlength="12" value="${esc(v.nick || "")}" autocomplete="nickname"></label>
      <label>비밀번호 <small>(4자 이상 — 나중에 고치거나 지울 때 써요. 꼭 기억해 두세요)</small><input name="pw" type="password" required minlength="4" maxlength="32" autocomplete="new-password"></label>
      <label>제목<input name="title" required minlength="2" maxlength="60" value="${esc(v.title || "")}"></label>
      <label>궁금한 내용<textarea name="body" required minlength="5" maxlength="3000" rows="9">${esc(v.body || "")}</textarea></label>
      <p class="note">전화번호·주소·실명은 쓰지 마세요. 적어도 저장할 때 <b>***</b> 로 가려집니다. 글은 누구나 볼 수 있어요.</p>
      ${honeypot()}
      <button class="btn big" type="submit">질문 올리기</button>
    </form>
    ${back("/", "목록으로")}`));
}

async function view(env, id, url) {
  const r = await getPost(env, id);
  if (!r) return gone(env);
  const ans = r.answered ? `
    <section class="answer"><h2>운영자 답변</h2><div class="text">${para(r.answer)}</div><p class="meta">${day(r.answered)}</p></section>`
    : `<p class="waiting">아직 답변을 기다리고 있어요. 보통 며칠 안에 답을 달아 드려요.</p>`;
  const msg = { saved: "질문이 올라갔어요.", edited: "고친 내용이 저장됐어요.", answered: "답변이 저장됐어요." }[url.searchParams.get("ok")] || "";
  return page(env, r.title, `
    ${msg ? `<p class="ok" role="status">${msg}</p>` : ""}
    <article class="q">
      <p class="meta">${esc(r.nick)} · ${day(r.created)}${r.updated ? ` · 고침 ${day(r.updated)}` : ""}</p>
      <div class="text">${para(r.body)}</div>
    </article>
    ${ans}
    <p class="row"><a class="btn ghost" href="/q/${id}/edit">글 고치기</a><a class="btn ghost" href="/q/${id}/delete">글 지우기</a></p>
    ${back("/", "목록으로")}`, 200, { index: !!r.answered });
}

async function editForm(env, id, v = null, err = "") {
  const r = await getPost(env, id);
  if (!r) return gone(env);
  v = v || r;
  return tokenized(env, async tok => page(env, "글 고치기", `
    ${err ? `<p class="err" role="alert">${esc(err)}</p>` : ""}
    <form method="post" action="/q/${id}/edit" class="card">
      ${tok}
      <p class="note">글을 쓸 때 정한 <b>닉네임과 비밀번호</b>를 넣어야 고쳐져요.</p>
      <label>닉네임<input name="nick" required maxlength="12" value="${esc(v.nickIn || "")}"></label>
      <label>비밀번호<input name="pw" type="password" required maxlength="32" autocomplete="current-password"></label>
      <label>제목<input name="title" required minlength="2" maxlength="60" value="${esc(v.title)}"></label>
      <label>궁금한 내용<textarea name="body" required minlength="5" maxlength="3000" rows="9">${esc(v.body)}</textarea></label>
      ${honeypot()}
      <button class="btn big" type="submit">고친 내용 저장</button>
    </form>
    ${back(`/q/${id}`, "질문으로 돌아가기")}`));
}

async function deleteForm(env, id, err = "", nickIn = "") {
  const r = await getPost(env, id);
  if (!r) return gone(env);
  return tokenized(env, async tok => page(env, "글 지우기", `
    ${err ? `<p class="err" role="alert">${esc(err)}</p>` : ""}
    <p class="lead">「${esc(r.title)}」 글을 지웁니다. 지우면 되돌릴 수 없어요. 달린 답변도 함께 지워져요.</p>
    <form method="post" action="/q/${id}/delete" class="card">
      ${tok}
      <label>닉네임<input name="nick" required maxlength="12" value="${esc(nickIn)}"></label>
      <label>비밀번호<input name="pw" type="password" required maxlength="32" autocomplete="current-password"></label>
      ${honeypot()}
      <button class="btn big danger" type="submit">지우기</button>
    </form>
    ${back(`/q/${id}`, "지우지 않고 돌아가기")}`));
}

async function answerForm(env, id, err = "") {
  const r = await env.DB.prepare("SELECT * FROM posts WHERE id = ?").bind(id).first(); // 숨긴 글도 운영자는 본다
  if (!r) return gone(env);
  return tokenized(env, async tok => page(env, "답변 달기(운영자)", `
    ${err ? `<p class="err" role="alert">${esc(err)}</p>` : ""}
    <article class="q"><h2>${esc(r.title)}</h2><div class="text">${para(r.body)}</div></article>
    <form method="post" action="/q/${id}/answer" class="card">
      ${tok}
      <label>관리자 비밀번호<input name="key" type="password" required autocomplete="current-password"></label>
      <label>답변<textarea name="answer" rows="10" maxlength="5000">${esc(r.answer || "")}</textarea></label>
      <label class="chk"><input type="checkbox" name="hide" value="1"${r.hidden ? " checked" : ""}> 이 글 숨기기(광고·욕설)</label>
      <button class="btn big" type="submit">답변 저장</button>
    </form>
    ${back(`/q/${id}`, "질문으로 돌아가기")}`, 200, { index: false }));
}

// ───────────── 처리

async function createPost(req, env) {
  const f = await req.formData();
  const v = pick(f, ["nick", "pw", "title", "body"]);
  const bad = await guard(env, req, f, "post", 5, 3600);
  if (bad) return writeForm(env, v, bad);
  const e = check(v, ["nick", "pw", "title", "body"]);
  if (e) return writeForm(env, v, e);
  const salt = rand(16), hash = await pbkdf(v.pw, salt);
  const now = Date.now();
  const r = await env.DB.prepare(
    "INSERT INTO posts (nick, title, body, pw_hash, pw_salt, created) VALUES (?, ?, ?, ?, ?, ?) RETURNING id"
  ).bind(v.nick.trim(), mask(v.title.trim()), mask(v.body.trim()), hash, salt, now).first();
  return redirect(`/q/${r.id}?ok=saved`);
}

async function doEdit(req, env, id) {
  const f = await req.formData();
  const v = pick(f, ["nick", "pw", "title", "body"]);
  const bad = await guard(env, req, f, "auth", 8, 900);
  if (bad) return editForm(env, id, { ...v, nickIn: v.nick }, bad);
  const e = check(v, ["title", "body"]);
  if (e) return editForm(env, id, { ...v, nickIn: v.nick }, e);
  const r = await getPost(env, id);
  if (!r) return gone(env);
  if (!(await owner(r, v))) return editForm(env, id, { ...v, nickIn: v.nick }, "닉네임이나 비밀번호가 맞지 않아요. 글을 쓸 때 정한 것을 넣어 주세요.");
  await env.DB.prepare("UPDATE posts SET title = ?, body = ?, updated = ? WHERE id = ?")
    .bind(mask(v.title.trim()), mask(v.body.trim()), Date.now(), id).run();
  return redirect(`/q/${id}?ok=edited`);
}

async function doDelete(req, env, id) {
  const f = await req.formData();
  const v = pick(f, ["nick", "pw"]);
  const bad = await guard(env, req, f, "auth", 8, 900);
  if (bad) return deleteForm(env, id, bad, v.nick);
  const r = await getPost(env, id);
  if (!r) return gone(env);
  if (!(await owner(r, v))) return deleteForm(env, id, "닉네임이나 비밀번호가 맞지 않아요. 글을 쓸 때 정한 것을 넣어 주세요.", v.nick);
  await env.DB.prepare("DELETE FROM posts WHERE id = ?").bind(id).run();
  return page(env, "글을 지웠어요", `<p class="ok" role="status">글을 지웠어요.</p>${back("/", "목록으로")}`);
}

async function doAnswer(req, env, id) {
  const f = await req.formData();
  const bad = await guard(env, req, f, "admin", 5, 900, false);
  if (bad) return answerForm(env, id, bad);
  if (!env.ADMIN_KEY || !(await same(String(f.get("key") || ""), env.ADMIN_KEY))) return answerForm(env, id, "관리자 비밀번호가 맞지 않아요.");
  const a = String(f.get("answer") || "").trim();
  if (a.length > LIM.answer[1]) return answerForm(env, id, "답변이 너무 길어요.");
  await env.DB.prepare("UPDATE posts SET answer = ?, answered = ?, hidden = ? WHERE id = ?")
    .bind(a || null, a ? Date.now() : null, f.get("hide") ? 1 : 0, id).run();
  return redirect(`/q/${id}?ok=answered`);
}

// ───────────── 검사

function check(v, keys) {
  const name = { nick: "닉네임", pw: "비밀번호", title: "제목", body: "내용" };
  for (const k of keys) {
    const s = (v[k] || "").trim(), [a, b] = LIM[k];
    if (s.length < a) return `${name[k]}을(를) ${a}자 이상 적어 주세요.`;
    if (s.length > b) return `${name[k]}은(는) ${b}자까지 쓸 수 있어요.`;
  }
  if (keys.includes("nick") && /운영자|관리자|admin/i.test(v.nick)) return "그 닉네임은 쓸 수 없어요. 다른 닉네임을 정해 주세요.";
  const links = ((v.title || "") + (v.body || "")).match(/https?:\/\/|www\./gi) || [];
  if (links.length > 2) return "인터넷 주소는 2개까지만 넣을 수 있어요.";
  return "";
}

// 폼 토큰(위조·자동 등록 막기) + 숨은 칸 + 횟수 제한. 문제가 있으면 안내 문장을, 없으면 "" 를 돌려준다.
async function guard(env, req, f, kind, max, win, honey = true) {
  if (honey && String(f.get("website") || "")) return "올리지 못했어요. 다시 해 주세요.";
  const t = String(f.get("t") || ""), [ts, sig] = t.split(".");
  const age = Date.now() - Number(ts);
  if (!ts || !sig || !(await same(sig, await hmac(env, "form:" + ts))) || age > 6 * 3600e3)
    return "화면을 너무 오래 열어 두었어요. 다시 해 주세요.";
  if (age < 3000) return "조금 천천히 다시 눌러 주세요.";
  const ip = req.headers.get("cf-connecting-ip") || "0";
  const k = kind + ":" + (await hmac(env, "ip:" + ip + ":" + new Date().toISOString().slice(0, 10))).slice(0, 16);
  const now = Date.now();
  await env.DB.prepare("DELETE FROM hits WHERE ts < ?").bind(now - 2 * 86400e3).run();
  const c = await env.DB.prepare("SELECT COUNT(*) AS n FROM hits WHERE k = ? AND ts > ?").bind(k, now - win * 1000).first();
  if (c.n >= max) return "짧은 시간에 너무 많이 눌렀어요. 잠시 뒤에 다시 해 주세요.";
  await env.DB.prepare("INSERT INTO hits (k, ts) VALUES (?, ?)").bind(k, now).run();
  return "";
}

async function owner(r, v) {
  if ((v.nick || "").trim() !== r.nick) { await pbkdf(v.pw || "", r.pw_salt); return false; } // 시간 차로 닉네임을 알아내지 못하게 똑같이 계산
  return same(await pbkdf(v.pw || "", r.pw_salt), r.pw_hash);
}

// 전화번호·메일·주민번호 모양을 가린다(개인정보를 받지 않는다).
function mask(s) {
  return s
    .replace(/\b\d{6}\s*-\s*[1-4]\d{6}\b/g, "******-*******")
    .replace(/\b(0\d{1,2})[\s.-]?\d{3,4}[\s.-]?\d{4}\b/g, "$1-****-****")
    .replace(/[\w.+-]+@[\w-]+\.[\w.-]+/g, "***@***");
}

// ───────────── 암호

async function pbkdf(pw, saltHex) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveBits"]);
  const bits = await crypto.subtle.deriveBits({ name: "PBKDF2", hash: "SHA-256", salt: hex2buf(saltHex), iterations: ITER }, key, 256);
  return buf2hex(bits);
}
async function hmac(env, msg) {
  const key = await crypto.subtle.importKey("raw", new TextEncoder().encode(env.TOKEN_SECRET || "dev-only"), { name: "HMAC", hash: "SHA-256" }, false, ["sign"]);
  return buf2hex(await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(msg)));
}
async function same(a, b) { // 길이·내용을 시간 차 없이 비교
  const [x, y] = await Promise.all([a, b].map(s => crypto.subtle.digest("SHA-256", new TextEncoder().encode(String(s)))));
  const u = new Uint8Array(x), w = new Uint8Array(y);
  let d = 0; for (let i = 0; i < u.length; i++) d |= u[i] ^ w[i];
  return d === 0;
}
const rand = n => buf2hex(crypto.getRandomValues(new Uint8Array(n)));
const buf2hex = b => [...new Uint8Array(b)].map(x => x.toString(16).padStart(2, "0")).join("");
const hex2buf = h => new Uint8Array(h.match(/../g).map(x => parseInt(x, 16)));

// ───────────── 조각

async function tokenized(env, fn) {
  const ts = String(Date.now());
  return fn(`<input type="hidden" name="t" value="${ts}.${await hmac(env, "form:" + ts)}">`);
}
const honeypot = () => `<div class="hp" aria-hidden="true"><label>비워 두세요<input name="website" tabindex="-1" autocomplete="off"></label></div>`;
const pick = (f, ks) => Object.fromEntries(ks.map(k => [k, String(f.get(k) || "")]));
const getPost = (env, id) => env.DB.prepare("SELECT * FROM posts WHERE id = ? AND hidden = 0").bind(id).first();
const gone = env => page(env, "없는 글이에요", `<p class="lead">지워졌거나 없는 글이에요.</p>${back("/", "목록으로")}`, 404);
const back = (href, t) => `<p class="back"><a href="${href}">← ${t}</a></p>`;
const home = () => back("/", "묻고 답하기 처음으로");
const redirect = loc => new Response(null, { status: 303, headers: { location: loc } });
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const para = s => esc(s).split(/\n{2,}/).map(x => `<p>${x.replace(/\n/g, "<br>")}</p>`).join("");
const day = ms => new Date(ms + 9 * 3600e3).toISOString().slice(0, 10).replace(/-/g, ". ") + ".";

function page(env, title, body, status = 200, o = {}) {
  const html = `<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)} · 사장님 마케팅 교실</title>
<meta name="robots" content="${o.index ? "index, follow" : "noindex, nofollow"}">
<link rel="icon" href="${SITE}/favicon.ico">
<style>${CSS}</style></head>
<body>
<header class="top"><a class="brand" href="${SITE}/">사장님 마케팅 교실</a><a class="home" href="/">묻고 답하기</a></header>
<main><h1>${esc(title)}</h1>${body}</main>
<footer><a href="${SITE}/">길라잡이로 가기</a> · <a href="${SITE}/privacy.html">개인정보 처리방침</a></footer>
</body></html>`;
  return new Response(html, {
    status,
    headers: {
      "content-type": "text/html; charset=utf-8",
      "cache-control": "no-store",
      "content-security-policy": "default-src 'none'; style-src 'unsafe-inline'; img-src 'self' " + SITE + "; form-action 'self'; base-uri 'none'; frame-ancestors 'none'",
      "x-content-type-options": "nosniff",
      "referrer-policy": "same-origin",
    },
  });
}

// 큰 글씨·큰 단추(어르신 기준): 본문 20px, 단추 높이 60px, 대비 4.5:1 이상. 색은 sajangmarketing.com style.css 와 같다.
const CSS = `
:root{--paper:#f8f6f1;--card:#fff;--ink:#1b1e22;--soft:#585e66;--line:#e4e0d7;--accent:#164a9a;--accent-soft:#e9f0fb;--warm:#c6521c;--ok:#0b6b34;--ok-soft:#e8f6ea;--err:#a51b1b;--err-soft:#fdeaea}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font:400 20px/1.7 system-ui,-apple-system,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;word-break:keep-all;overflow-wrap:anywhere}
a{color:var(--accent)}
header.top{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 16px;background:var(--card);border-bottom:1px solid var(--line)}
header .brand{font-weight:700;text-decoration:none;color:var(--ink)}header .home{font-weight:700}
main{max-width:760px;margin:0 auto;padding:20px 16px 40px}
h1{font-size:30px;line-height:1.35;margin:8px 0 16px}h2{font-size:24px;margin:32px 0 12px}
.lead{font-size:21px}
.steps{list-style:none;padding:0;margin:16px 0;display:grid;gap:10px}
.steps li{display:flex;gap:14px;align-items:center;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.steps b{flex:none;width:44px;height:44px;border-radius:50%;background:var(--accent);color:#fff;display:grid;place-items:center;font-size:22px}
.steps em,.lead em{font-style:normal;font-weight:700}
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:60px;padding:0 26px;border-radius:14px;background:var(--accent);color:#fff;font:700 22px/1 inherit;font-family:inherit;text-decoration:none;border:0;cursor:pointer}
.btn.big{width:100%;font-size:24px;min-height:68px}
.btn.ghost{background:var(--card);color:var(--accent);border:2px solid var(--accent);font-size:20px;min-height:56px}
.btn.danger{background:var(--err)}
.row,.pager{display:flex;gap:12px;flex-wrap:wrap}.row .btn,.pager .btn{flex:1}
.list{list-style:none;padding:0;margin:0;display:grid;gap:10px}
.list a{display:grid;gap:4px;padding:16px;background:var(--card);border:1px solid var(--line);border-radius:14px;text-decoration:none;color:var(--ink)}
.list strong{font-size:21px}
.badge{justify-self:start;font-size:16px;font-weight:700;padding:2px 10px;border-radius:999px}
.badge.done{background:var(--ok-soft);color:var(--ok)}.badge.wait{background:#f1f3f5;color:#4b5563}
.meta{color:var(--soft);font-size:17px;margin:0}
.card{display:grid;gap:18px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:20px 16px}
label{display:grid;gap:6px;font-weight:700}label small{font-weight:400;color:var(--soft);font-size:17px}
input,textarea{font:inherit;font-weight:400;width:100%;padding:14px;border:2px solid #9aa1a9;border-radius:12px;background:#fff;color:var(--ink)}
input:focus,textarea:focus,.btn:focus-visible,a:focus-visible{outline:3px solid var(--warm);outline-offset:2px}
label.chk{display:flex;align-items:center;gap:10px;font-weight:400}label.chk input{width:28px;height:28px}
.note{background:var(--accent-soft);border-radius:12px;padding:12px 14px;margin:0;font-size:18px}
.ok{background:var(--ok-soft);color:var(--ok);font-weight:700;border-radius:12px;padding:14px 16px}
.err{background:var(--err-soft);color:var(--err);font-weight:700;border-radius:12px;padding:14px 16px}
.q,.answer{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:18px 16px;margin:0 0 16px}
.answer{border:2px solid var(--ok);background:#fbfefb}.answer h2{margin-top:0;color:var(--ok)}
.waiting{background:#f1f3f5;border-radius:12px;padding:14px 16px}
.text p{margin:0 0 12px}
.empty{color:var(--soft)}
.back{margin-top:28px;font-size:19px}
.hp{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}
footer{max-width:760px;margin:0 auto;padding:20px 16px 40px;color:var(--soft);font-size:17px}
`;
