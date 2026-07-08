#!/usr/bin/env python3
"""Preview boikisser frames as PNGs — same logic as gen_boikisser.py.

Usage:
    python3 preview_boikisser.py --text "mrow"
    python3 preview_boikisser.py --text ">w<" --font-size 12 --text-height 6
    python3 preview_boikisser.py --text "uwu" --font-size 8 --text-height 4
"""

import argparse, math, os, sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
GK_DIR = os.path.join(HERE, "zmk-nice-oled", "boards", "shields", "nice_oled", "assets")
sys.path.insert(0, GK_DIR)
import importlib.util
spec = importlib.util.spec_from_file_location("gk", os.path.join(GK_DIR, "gen_boikisser.py"))
gk = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gk)

_FRAMES, _W, _H = gk._FRAMES, gk._W, gk._H
_CAT_X, _CAT_W = 12, 31
GAP = 1
FONT_PATH = os.path.join(GK_DIR, "..", "src", "fonts", "Tiny5-Regular.ttf")


def decode(data, w, h):
    img = Image.new("RGBA", (w, h), (255, 255, 255, 0))
    px, rb = img.load(), math.ceil(w / 8)
    for y in range(h):
        for x in range(w):
            b = data[8 + y * rb + x // 8]
            px[x, y] = (0, 0, 0, 255) if (b >> (7 - (x % 8))) & 1 else (255, 255, 255, 0)
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", default="")
    ap.add_argument("--frames", default="3,4,5,6")
    ap.add_argument("-o", "--outdir", default="boikisser_preview")
    ap.add_argument("-s", "--scale", type=int, default=8)
    ap.add_argument("--font-size", type=int, default=8, help="Tiny5 font size (default: 8)")
    ap.add_argument("--text-height", type=int, default=4, help="text area height in px (default: 4)")
    ap.add_argument("--y-offset", type=int, default=-20, help="font Y offset (default: -20)")
    ap.add_argument("--flip", choices=["none", "lr", "tb"], default="none",
                    help="flip text after transpose: none, lr (left-right), tb (top-bottom)")
    args = ap.parse_args()

    tf = set()
    if args.text:
        for p in args.frames.split(","):
            try: tf.add(int(p.strip()) - 1)
            except ValueError: pass

    TEXT_H = args.text_height
    font = ImageFont.truetype(FONT_PATH, size=args.font_size) if args.text else None
    text_w = _CAT_W + GAP + TEXT_H if args.text else _CAT_W
    os.makedirs(args.outdir, exist_ok=True)

    print(f"'{args.text}': font_size={args.font_size}, text_h={TEXT_H}, "
          f"y_off={args.y_offset}, flip={args.flip}, frames={sorted(f+1 for f in tf)}")

    for idx, fd in enumerate(_FRAMES):
        img = decode(fd, _W, _H)
        cat = img.crop((_CAT_X, 0, _CAT_X + _CAT_W, _H))

        if idx in tf and args.text:
            tmp = Image.new("RGBA", (1, 1))
            dr = ImageDraw.Draw(tmp)
            bb = dr.textbbox((0, args.y_offset), args.text, font=font)
            tw, th = bb[2] - bb[0], bb[3] - bb[1]
            tt = Image.new("RGBA", (tw, th), (255, 255, 255, 0))
            dr = ImageDraw.Draw(tt)
            dr.text((0, args.y_offset - bb[1]), args.text, fill=(0, 0, 0, 255), font=font)
            tr = tt.transpose(Image.Transpose.TRANSPOSE)
            if args.flip == "tb":
                tr = tr.transpose(Image.FLIP_TOP_BOTTOM)
            elif args.flip == "lr":
                tr = tr.transpose(Image.FLIP_LEFT_RIGHT)
            text_img = Image.new("RGBA", (TEXT_H, _H), (255, 255, 255, 0))
            ox = max(0, (TEXT_H - th) // 2)
            oy = max(0, (_H - tw) // 2)
            text_img.paste(tr, (ox, oy))
            frame = Image.new("RGBA", (text_w, _H), (255, 255, 255, 0))
            frame.paste(cat, (0, 0))
            frame.paste(text_img, (_CAT_W + GAP, 0))
            label = "TEXT"
        else:
            frame = Image.new("RGBA", (text_w, _H), (255, 255, 255, 0))
            frame.paste(cat, (0, 0))
            label = "notext"

        out = frame.convert("RGB").resize((text_w * args.scale, _H * args.scale), Image.NEAREST)
        out.save(os.path.join(args.outdir, f"frame_{idx:02d}_{label}.png"))

    print(f"Wrote {len(_FRAMES)} PNGs → {args.outdir}/  ({text_w}×{_H} px, {args.scale}×)")


if __name__ == "__main__":
    main()