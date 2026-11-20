"""Ponto único de renderização: só existe o visual LC Digital."""
from templates import TEMPLATES
from studio import render_studio
from carousel_icon import add_indicator

MODELO = "LC Digital"


def render_any(slides, fmt, brand="", ind=True, imgs=(), logo=None):
    ims, w = render_studio(slides, fmt, TEMPLATES[MODELO], brand, imgs, logo)
    if ind: ims = [add_indicator(im, k, len(ims)) for k, im in enumerate(ims)]
    return ims, w
