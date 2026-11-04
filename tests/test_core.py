import sys, os, re, io, zipfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from PIL import Image, ImageChops
from config import FORMATS, THEMES
from ai import local_plan, Plan
from engine import render, LAYOUTS
from templates import TEMPLATES
from template_engine import render_tpl
from dsl import render_dsl
from export import to_pdf, to_zip
from carousel_icon import add_indicator
TXT = " ".join(f"Frase {i} sobre automação de processos e consórcio para empresas que querem crescer." for i in range(50))


def build(kind, fmt, p):
    if kind == "Livre": return render(p, fmt, THEMES["Obsidiana"], "Magazine", brand="@marca")
    t = TEMPLATES[kind]
    return render_dsl(p, fmt, t) if t.get("engine") == "dsl" else render_tpl(p, fmt, t, "", len(p) >= 3)


@pytest.mark.parametrize("kind", ["Livre"] + list(TEMPLATES))
@pytest.mark.parametrize("fmt", list(FORMATS))
@pytest.mark.parametrize("n", [1, 2, 5])
def test_pdf(kind, fmt, n):
    p = local_plan(TXT, n, 0); p.slides[0].highlight = "consórcio"
    ims, W = build(kind, fmt, p.slides)
    assert not [w for w in W if "incorreta" in w or "vazia" in w or "fora da" in w or "sobreposição" in w], W
    pdf = to_pdf(ims); assert pdf[:5] == b"%PDF-" and len(re.findall(rb"/Type\s*/Page(?!s)", pdf)) == len(ims)
    assert len(zipfile.ZipFile(io.BytesIO(to_zip(ims))).namelist()) == len(ims)


@pytest.mark.parametrize("fmt", list(FORMATS))
@pytest.mark.parametrize("n", [1, 5])
def test_indicator(fmt, n):
    F = FORMATS[fmt]
    for i in range(n):
        base = Image.new("RGB", (F["w"], F["h"]), "#520000"); out = add_indicator(base.copy(), i, n)
        assert (ImageChops.difference(base, out).getbbox() is None) == (n < 2)
