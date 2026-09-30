"""한국어 내레이션 TTS — Google Cloud Text-to-Speech(Chirp3 HD) (2026-09-28)

  python tts_ko.py --voice Kore --text "문장" --out 출력.wav [--rate 1.0]
  python tts_ko.py --batch 줄.tsv            (열: 목소리 \t 속도 \t 문장 \t 출력경로)

- movie 저장소 tools/tts_google.py 와 같은 방식(운영자 2026-09-15 「일단 구글로 가자」). 인증은 gcloud ADC
- 무료 한도: 월 100만 자(미확인 부분은 movie 쪽 기록 참고). 글자 수를 같은 폴더 _tts_글자수.tsv 에 쌓는다
- 목소리: ko-KR-Chirp3-HD-<이름> (예: Kore·Aoede·Charon·Leda·Puck)
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.request, urllib.error

LOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_tts_글자수.tsv")


def token():
    return subprocess.check_output(["gcloud", "auth", "application-default", "print-access-token"], text=True, shell=True).strip()


def project():
    return subprocess.check_output(["gcloud", "config", "get-value", "project"], text=True, shell=True).strip()


def synth(text, voice, out, rate=1.0, tok=None, proj=None):
    name = voice if voice.startswith("ko-KR") else f"ko-KR-Chirp3-HD-{voice}"
    body = {"input": {"text": text}, "voice": {"languageCode": "ko-KR", "name": name},
            "audioConfig": {"audioEncoding": "LINEAR16", "sampleRateHertz": 48000, "speakingRate": rate}}
    req = urllib.request.Request("https://texttospeech.googleapis.com/v1/text:synthesize", data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {tok or token()}", "x-goog-user-project": proj or project(),
                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            d = json.load(r)
    except urllib.error.HTTPError as e:
        raise SystemExit(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:400]}")
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    open(out, "wb").write(base64.b64decode(d["audioContent"]))
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M')}\t{name}\t{len(text)}\t{out}\n")
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", out],
                               capture_output=True, text=True).stdout or 0)
    print(f"{dur:5.2f}s  {name}  {text[:30]}")
    return dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice"); ap.add_argument("--text"); ap.add_argument("--out"); ap.add_argument("--rate", type=float, default=1.0)
    ap.add_argument("--batch")
    a = ap.parse_args()
    tok, proj = token(), project()
    if a.batch:
        for line in open(a.batch, encoding="utf-8"):
            if not line.strip() or line.startswith("#"):
                continue
            v, r, t, o = line.rstrip("\n").split("\t")
            synth(t, v, o, float(r or 1), tok, proj)
    else:
        synth(a.text, a.voice, a.out, a.rate, tok, proj)


if __name__ == "__main__":
    main()
