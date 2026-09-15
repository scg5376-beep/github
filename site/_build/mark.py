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
    f = font(22)
    for k, b in enumerate(boxes):
        pad = 6
        x, y, w, h = b["x"] - pad, b["y"] - pad, b["w"] + 2 * pad, b["h"] + 2 * pad
        d.rounded_rectangle([x, y, x + w, y + h], radius=6, outline=RED, width=4)
        lab = (labels[k] if labels and k < len(labels) else str(k + 1))
        # 번호 동그라미: 상자 왼쪽 위 바깥. 자리가 없으면 안쪽
        r = 17
        cx, cy = x - r - 6, y - r - 6
        if cx < r or cy < r:
            cx, cy = x + w + r + 6, y + h / 2
            if cx > im.size[0] - r:
                cx, cy = x + r + 4, y + r + 4
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=RED)
        tw = d.textlength(lab, font=f)
        d.text((cx - tw / 2, cy - 14), lab, fill="white", font=f)
    im.save(out, optimize=True)
    print(out, im.size)


if __name__ == "__main__":
    main()
