"""Fontes do estúdio (todas dentro de assets/fonts, funciona igual em qualquer computador)."""
from functools import lru_cache
from pathlib import Path
from PIL import ImageFont

FD = Path(__file__).parent / "assets" / "fonts"
FACES = {"os_b": ("OpenSans-VF.ttf", [700, 100]), "os_r": ("OpenSans-VF.ttf", [400, 100]),
         "pf_r": ("PlayfairDisplay-VF.ttf", [400]), "pf_b": ("PlayfairDisplay-VF.ttf", [700]),
         "pf_i": ("PlayfairDisplay-Italic-VF.ttf", [600]), "pop_r": ("Poppins-Regular.ttf", None),
         "pop_m": ("Poppins-Medium.ttf", None), "pop_s": ("Poppins-SemiBold.ttf", None),
         "chewy": ("Fredoka-VF.ttf", [700, 100]), "bebas": ("BebasNeue-Regular.ttf", None), "anton": ("Anton-Regular.ttf", None)}


@lru_cache(None)
def face(k, s):
    n, ax = FACES[k]; s = max(int(s), 8)
    try:
        f = ImageFont.truetype(str(FD / n), s)
        if ax:
            try: f.set_variation_by_axes(ax)
            except Exception: pass
        return f
    except OSError:
        for alt in ("DejaVuSans-Bold.ttf", "DejaVuSans.ttf"):
            try: return ImageFont.truetype(alt, s)
            except OSError: pass
        return ImageFont.load_default()
