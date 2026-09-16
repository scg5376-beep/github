# 캡처에 빨간 표시(네모·번호·화살표)를 그린다. shot.mjs 가 만든 png+json 을 읽는다.
# 사용: python mark.py in.png out.png [--crop x,y,w,h | --auto 여백] [--labels 1,2,...]
import json, sys, pathlib
from PIL import Image, ImageDraw, ImageFont

RED = (229, 38, 38)
FONT = pathlib.Path(__file__).resolve().parent.parent / "fonts/pretendard/Pretendard-Bold.woff2"


def font(size):
    for cand in ["C:/Windows/Fonts/malgunbd.ttf", "C:/Windows/Fonts/malgun.ttf"]:
        try:
            return ImageFont.truetype(cand, size)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    src, out = sys.argv[1], sys.argv[2]
    args = sys.argv[3:]
    crop = auto = None
    labels = None
    i = 0
    while i < len(args):
        if args[i] == "--crop":
            crop = [int(float(v)) for v in args[i + 1].split(",")]; i += 2
        elif args[i] == "--auto":
            auto = int(args[i + 1]); i += 2
        elif args[i] == "--labels":
            labels = args[i + 1].split(","); i += 2
        else:
            i += 1
    meta = json.loads(pathlib.Path(src).with_suffix(".json").read_text(encoding="utf-8"))
    boxes = [b for b in meta["boxes"] if b and b["w"] > 0 and b["h"] > 0]
    im = Image.open(src).convert("RGB")
    W, H = im.size
    if auto is not None and boxes:
        x0 = max(0, min(b["x"] for b in boxes) - auto); y0 = max(0, min(b["y"] for b in boxes) - auto)
        x1 = min(W, max(b["x"] + b["w"] for b in boxes) + auto); y1 = min(H, max(b["y"] + b["h"] for b in boxes) + auto)
        crop = [int(x0), int(y0), int(x1 - x0), int(y1 - y0)]
    if crop:
        im = im.crop((crop[0], crop[1], crop[0] + crop[2], crop[1] + crop[3]))
        for b in boxes:
            b["x"] -= crop[0]; b["y"] -= crop[1]
    d = ImageDraw.Draw(im)
    W2, H2 = im.size
    pos = []
    for b in boxes:
        pad = 6
        x, y, w, h = b["x"] - pad, b["y"] - pad, b["w"] + 2 * pad, b["h"] + 2 * pad
        d.rounded_rectangle([x, y, x + w, y + h], radius=6, outline=RED, width=4)
        pos.append({"x": round(x / W2 * 100, 2), "y": round(y / H2 * 100, 2), "w": round(w / W2 * 100, 2), "h": round(h / H2 * 100, 2)})
    # 번호는 그림에 굽지 않는다 — 글마다 순번이 달라서 HTML 이 상자 위치(%)에 배지를 얹는다 (운영자 2026-09-17)
    pathlib.Path(out).with_suffix(".boxes.json").write_text(json.dumps({"w": W2, "h": H2, "boxes": pos}, ensure_ascii=False), encoding="utf-8")
    im.save(out, optimize=True)
    print(out, im.size)


if __name__ == "__main__":
    main()
