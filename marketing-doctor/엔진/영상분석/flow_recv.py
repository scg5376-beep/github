"""Flow 등 브라우저 안의 영상을 크롬 다운로드 없이 받는 로컬 수신기 (2026-09-28)

  python flow_recv.py <저장폴더> [포트=8767]

왜: 크롬이 연속 다운로드를 막아(09-28 g1a 못 받음) 「미디어 다운로드」가 멈춘다.
    페이지 JS 에서 영상을 fetch 한 뒤 http://127.0.0.1:<포트>/save?name=파일.mp4 로 POST 하면 이 서버가 파일로 쓴다.
- 받는 것은 이 PC 안(127.0.0.1)뿐. 저장 폴더 밖으로는 쓰지 않는다(이름의 경로 문자는 지운다)
- 페이지 쪽 예:
    const b = await (await fetch(url)).blob();
    await fetch('http://127.0.0.1:8767/save?name=f1.mp4', {method:'POST', body:b});
"""
import http.server, os, re, sys, urllib.parse

DIR = os.path.abspath(sys.argv[1])
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 8767
os.makedirs(DIR, exist_ok=True)


class H(http.server.BaseHTTPRequestHandler):
    def cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(204); self.cors(); self.end_headers()

    def do_POST(self):
        q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        name = re.sub(r"[\\/:*?\"<>|]", "_", q.get("name", ["file.bin"])[0])
        n = int(self.headers.get("Content-Length", 0))
        data = self.rfile.read(n)
        with open(os.path.join(DIR, name), "wb") as f:
            f.write(data)
        print("SAVED", name, len(data), flush=True)
        self.send_response(200); self.cors(); self.end_headers(); self.wfile.write(b"ok")

    def log_message(self, *a):
        pass


print("RECV", DIR, PORT, flush=True)
http.server.ThreadingHTTPServer(("127.0.0.1", PORT), H).serve_forever()
