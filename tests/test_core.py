import sys, os, re, io, zipfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from PIL import Image, ImageChops
from config import FORMATS
from ai import fix_plan, Plan, Slide, Item
from templates import TEMPLATES
from renderer import render_any, MODELO
from export import to_pdf, to_zip
from carousel_icon import add_indicator

LAYOUTS = ["capa", "capa_foto", "texto", "lista", "icones", "passos", "foto", "citacao", "cta"]
ITS = [Item(icon="target", label="Estratégia", text="Pilares claros"), Item(icon="pencil", label="Criação", text="Artes com a sua cara"), Item(icon="chart", label="Análise", text="Ajuste semanal")]


def _photo():
    im = Image.new("RGB", (900, 1200), "#a06070"); b = io.BytesIO(); im.save(b, "JPEG"); return b.getvalue()


def test_only_lc_design():
    assert list(TEMPLATES) == ["LC Digital"] == [MODELO]


@pytest.mark.parametrize("lay", LAYOUTS)
@pytest.mark.parametrize("img", [None, 0])
def test_all_layouts(lay, img):
    s = Slide(layout=lay, label="TESTE", headline="Um título bem longo para testar a quebra de linhas do motor", highlight="título", subhead="Subtítulo com **destaque** aqui.",
              body="Texto de apoio com **negrito** e várias palavras para ocupar espaço no card.", cta="Quero saber mais", items=ITS, image=img)
    ims, w = render_any([s, s, s], "Instagram 4:5", "LC Digital", True, [_photo()])
    assert len(ims) == 3 and ims[0].size == (1080, 1350)


@pytest.mark.parametrize("fmt", list(FORMATS))
def test_formats_pdf_zip(fmt):
    sl = [Slide(layout="capa", headline="Conteúdo que conecta e vende", highlight="vende", subhead="Sub")] + [Slide(headline=f"Slide {i}", body="Texto " * 20) for i in range(3)] + [Slide(layout="cta", headline="Vamos conversar?", cta="Fale")]
    ims, W = render_any(sl, fmt, "LC Digital", False)
    assert all(im.size == (FORMATS[fmt]["w"], FORMATS[fmt]["h"]) for im in ims)
    pdf = to_pdf(ims); assert pdf[:5] == b"%PDF-" and len(re.findall(rb"/Type\s*/Page(?!s)", pdf)) == len(ims)
    assert len(zipfile.ZipFile(io.BytesIO(to_zip(ims))).namelist()) == len(ims)


def test_extremes():
    for s in (Slide(), Slide(headline="palavra " * 60, body="texto " * 300, subhead="x" * 400)):
        for lay in ("", "capa", "texto", "lista", "cta", "citacao"):
            ims, _ = render_any([Slide(layout=lay, **s.model_dump(exclude={"layout"}))] * 2, "Story/Reels 9:16", "", True)
            assert ims[0].size == (1080, 1920)


def test_hero_word_and_default_logo():
    ims, _ = render_any([Slide(layout="capa", headline="Conteúdo que conecta e vende", highlight="vende")], "Instagram 4:5", "LC Digital", False)
    px = ims[0].getpixel((540, 340))   # linha da palavra-herói (rosa)
    assert px[0] > px[1] + 40, px
    foot = ims[0].crop((80, 1250, 160, 1330)); assert foot.getcolors(100000) and len(foot.getcolors(100000)) > 20   # avatar com o logo desenhado


def test_indicator():
    F = FORMATS["Instagram 4:5"]
    for n in (1, 5):
        base = Image.new("RGB", (F["w"], F["h"]), "#520000"); out = add_indicator(base.copy(), 0, n)
        assert (ImageChops.difference(base, out).getbbox() is None) == (n < 2)


def test_fix_plan_sanitizes():
    p = fix_plan(Plan(slides=[Slide(icon="naoexiste", layout="xyz", items=[Item(label=x) for x in "abcde"], image=9)]), 3, 1)
    assert len(p.slides) == 3 and p.slides[0].icon == "" and p.slides[0].layout == "" and len(p.slides[0].items) == 4 and p.slides[0].image is None
