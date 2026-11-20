"""Ponto único de renderização: escolhe o motor certo para o modelo escolhido e aplica o indicador de carrossel."""
from config import THEMES
from templates import TEMPLATES
from engine import render, LAYOUTS
from template_engine import render_tpl
from dsl import render_dsl
from studio import render_studio
from carousel_icon import add_indicator

LIVRE = "Livre (layouts criativos)"


def model_names():
    st_ = [k for k, v in TEMPLATES.items() if v.get("engine") == "studio"]
    return st_ + [k for k in TEMPLATES if k not in st_] + [LIVRE]


def is_studio(modelo): return TEMPLATES.get(modelo, {}).get("engine") == "studio"


def render_any(slides, fmt, modelo, brand="", theme="Obsidiana", layout="Editorial", ind=True, imgs=(), logo=None):
    tpl = TEMPLATES.get(modelo)
    if tpl and tpl.get("engine") == "studio": ims, w = render_studio(slides, fmt, tpl, brand, imgs, logo)
    elif tpl and tpl.get("engine") == "dsl": ims, w = render_dsl(slides, fmt, tpl, brand, list(imgs))
    elif tpl: ims, w = render_tpl(slides, fmt, tpl, brand, len(slides) >= 3)
    else: ims, w = render(slides, fmt, THEMES[theme], layout, list(imgs), brand, logo)
    if ind: ims = [add_indicator(im, k, len(ims)) for k, im in enumerate(ims)]
    return ims, w
