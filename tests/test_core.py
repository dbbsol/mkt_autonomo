import sys, os, re, io, zipfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from PIL import Image, ImageChops
from config import FORMATS
from ai import local_plan, fix_plan, Slide, Item
from templates import TEMPLATES
from renderer import render_any, model_names, LIVRE
from export import to_pdf, to_zip
from carousel_icon import add_indicator
TXT = " ".join(f"Frase {i} sobre automação de processos e consórcio para empresas que querem crescer." for i in range(50))


def build(kind, fmt, p):
    return render_any(p, fmt, kind, "@marca", ind=False)


@pytest.mark.parametrize("kind", model_names())
@pytest.mark.parametrize("fmt", list(FORMATS))
@pytest.mark.parametrize("n", [1, 2, 5])
def test_pdf(kind, fmt, n):
    p = local_plan(TXT, n, 0); p.slides[0].highlight = "consórcio"
    ims, W = build(kind, fmt, p.slides)
    assert not [w for w in W if "incorreta" in w or "vazia" in w or "fora da" in w or "sobreposição" in w], W
    assert all(im.size[0] == FORMATS[fmt]["w"] and im.size[1] == FORMATS[fmt]["h"] for im in ims)
    pdf = to_pdf(ims); assert pdf[:5] == b"%PDF-" and len(re.findall(rb"/Type\s*/Page(?!s)", pdf)) == len(ims)
    assert len(zipfile.ZipFile(io.BytesIO(to_zip(ims))).namelist()) == len(ims)


@pytest.mark.parametrize("fmt", list(FORMATS))
@pytest.mark.parametrize("n", [1, 5])
def test_indicator(fmt, n):
    F = FORMATS[fmt]
    for i in range(n):
        base = Image.new("RGB", (F["w"], F["h"]), "#520000"); out = add_indicator(base.copy(), i, n)
        assert (ImageChops.difference(base, out).getbbox() is None) == (n < 2)


def _photo():
    im = Image.new("RGB", (900, 1200), "#a06070"); b = io.BytesIO(); im.save(b, "JPEG"); return b.getvalue()


STUDIO = [k for k, v in TEMPLATES.items() if v.get("engine") == "studio"]


@pytest.mark.parametrize("modelo", STUDIO)
def test_studio_all_layouts(modelo):
    """Todos os layouts do estúdio renderizam, com e sem foto, sem estourar o canvas."""
    its = [Item(icon="target", label="Estratégia", text="Pilares claros"), Item(icon="pencil", label="Criação", text="Artes com a sua cara"), Item(icon="chart", label="Análise", text="Ajuste semanal")]
    for lay in ["capa", "capa_foto", "texto", "lista", "icones", "passos", "foto", "citacao", "cta"]:
        for img in (None, 0):
            s = Slide(layout=lay, label="TESTE", headline="Um título bem longo para testar a quebra de linhas do motor", highlight="título", subhead="Subtítulo com **destaque** aqui.",
                      body="Texto de apoio com **negrito** e várias palavras para ocupar espaço no card.", cta="Quero saber mais", items=its, image=img)
            ims, w = render_any([s, s, s], "Instagram 4:5", modelo, "@teste", imgs=[_photo()], ind=True)
            assert len(ims) == 3 and ims[0].size == (1080, 1350)


def test_studio_without_content_and_extremes():
    empty = Slide(); huge = Slide(headline="palavra " * 60, body="texto " * 300, subhead="x" * 400)
    for s in (empty, huge):
        for lay in ("", "capa", "texto", "lista", "cta"):
            ims, _ = render_any([Slide(layout=lay, **s.model_dump(exclude={"layout"}))] * 2, "Story/Reels 9:16", STUDIO[0], "")
            assert ims[0].size == (1080, 1920)


def test_fix_plan_sanitizes():
    from ai import Plan
    p = Plan(slides=[Slide(icon="naoexiste", layout="xyz", items=[Item(label="a"), Item(label="b"), Item(label="c"), Item(label="d"), Item(label="e")], image=9)])
    p = fix_plan(p, 3, 1)
    assert len(p.slides) == 3 and p.slides[0].icon == "" and p.slides[0].layout == "" and len(p.slides[0].items) == 4 and p.slides[0].image is None
