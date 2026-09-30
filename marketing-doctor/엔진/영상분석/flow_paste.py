"""로컬 이미지를 브라우저 클립보드로 옮겨 Google Flow 입력창에 붙여 넣게 해 주는 작은 서버 (2026-09-27)

  python flow_paste.py <이미지폴더> [포트=8766]

Flow 의 「미디어 업로드」는 운영체제 파일 선택 창을 띄워서 브라우저 자동화로는 못 누른다.
그래서: 이 서버를 켜고 → 새 탭에서 http://127.0.0.1:8766/copy.html?f=<파일명.png> 을 연다
→ 탭 화면을 한 번 캡처(탭이 앞으로 와야 클립보드가 열린다)하고 화면 가운데를 클릭 → window.__r 이 'COPIED …' 인지 본다
→ Flow 탭 입력창을 클릭하고 ctrl+v → 업로드가 끝나 썸네일이 보이면 프롬프트를 친다.

- Flow 페이지 안에서 127.0.0.1 로 fetch 하면 멈춘다(크롬 로컬 네트워크 접근 확인 창으로 추정, 09-27 실측). 반드시 따로 탭을 연다.
- 다 쓰면 서버를 끈다(좀비 정리 대상).
"""
import functools, http.server, sys
from pathlib import Path

PAGE = """<!doctype html><meta charset="utf-8"><title>copy</title>
<body style="margin:0"><button id="b" style="width:100vw;height:100vh;font-size:40px">COPY</button>
<script>
window.__r='none';
document.getElementById('b').onclick=async()=>{try{const f=new URLSearchParams(location.search).get('f');
const b=await fetch('/'+encodeURIComponent(f)).then(r=>r.blob());
await navigator.clipboard.write([new ClipboardItem({'image/png':b})]);
window.__r='COPIED '+f+' '+b.size;document.title='COPIED';}catch(e){window.__r='ERR '+e.message;document.title='ERR';}};
</script>"""


class H(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/copy.html"):
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()


if __name__ == "__main__":
    root = Path(sys.argv[1]).resolve()
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8766
    print(f"serving {root} on http://127.0.0.1:{port}/copy.html?f=<file>", flush=True)
    http.server.ThreadingHTTPServer(("127.0.0.1", port), functools.partial(H, directory=str(root))).serve_forever()
