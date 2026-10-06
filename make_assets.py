"""Generates the background artwork used by the dashboard (run once; output goes to assets/)."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

rng = np.random.default_rng(7)


def gradient(w, h, top, bottom):
    t = np.linspace(0, 1, h)[:, None, None]
    top, bottom = np.array(top)[None, None, :], np.array(bottom)[None, None, :]
    return np.repeat((top * (1 - t) + bottom * t), w, axis=1).astype("uint8")


def glow(img, cx, cy, r, color, alpha=150):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(layer).ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*color, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(r * 0.55))
    return Image.alpha_composite(img, layer)


def rings(img, cx, cy, radii, color, alpha=40, width=2):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for r in radii:
        d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(*color, alpha), width=width)
    return Image.alpha_composite(img, layer)


def bars(img, base_y, n, color_a, color_b, max_h, alpha=120):
    w, _ = img.size
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    bw = w / n
    for i in range(n):
        env = 0.35 + 0.65 * abs(np.sin(i / n * np.pi * 3.2 + 0.6))
        h = max_h * env * rng.uniform(0.55, 1.0)
        t = i / n
        col = tuple(int(a * (1 - t) + b * t) for a, b in zip(color_a, color_b))
        d.rounded_rectangle([i * bw + bw * 0.18, base_y - h, (i + 1) * bw - bw * 0.18, base_y],
                            radius=int(bw * 0.3), fill=(*col, alpha))
    return Image.alpha_composite(img, layer.filter(ImageFilter.GaussianBlur(1.2)))


# ---- page background (deep ocean teal -> midnight, with glow + vinyl rings) ----
W, H = 1920, 1080
bg = Image.fromarray(gradient(W, H, (6, 24, 38), (8, 12, 28))).convert("RGBA")
bg = glow(bg, 320, 220, 380, (20, 184, 166), 120)
bg = glow(bg, 1620, 300, 340, (56, 189, 248), 90)
bg = glow(bg, 1100, 980, 460, (251, 113, 133), 70)
bg = glow(bg, 200, 900, 300, (163, 230, 53), 55)
bg = rings(bg, 1500, 760, range(120, 760, 46), (94, 234, 212), 26)
bg = rings(bg, 260, 300, range(80, 420, 40), (125, 211, 252), 22)
bg = bars(bg, H, 64, (45, 212, 191), (56, 189, 248), 300, 70)
bg.convert("RGB").save("assets/bg_main.jpg", quality=82, optimize=True)

# ---- hero banner ----
W, H = 1800, 460
hero = Image.fromarray(gradient(W, H, (10, 52, 66), (9, 20, 40))).convert("RGBA")
hero = glow(hero, 300, 120, 340, (45, 212, 191), 170)
hero = glow(hero, 1450, 80, 320, (56, 189, 248), 140)
hero = glow(hero, 980, 460, 380, (251, 113, 133), 110)
hero = rings(hero, 1500, 230, range(60, 520, 36), (153, 246, 228), 45)
hero = bars(hero, H, 90, (45, 212, 191), (251, 113, 133), 230, 130)
hero.convert("RGB").save("assets/bg_hero.jpg", quality=85, optimize=True)
print("assets written")
