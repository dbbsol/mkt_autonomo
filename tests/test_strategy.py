import sys, os, io, re, zipfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import strategy as ST
from report import build_report
from planner_ui import pack_zip, make_renderer


def brief(**k):
    B = dict(ST.DEF)
    B.update(cliente="Studio Glau", insta="@personalglau", nicho_final="Fitness / personal", inicio="2026-11-02", pub="mães que querem voltar a treinar",
             dores="falta de tempo\ncansaço\nculpa por se priorizar", desejos="energia\nconfiança", objecoes="não tenho tempo\nacademia é cara", ofertas="Treino online\nConsultoria 1:1",
             diferenciais="Treinos de 30 minutos\nAcompanhamento semanal", temas="treino em casa\nrotina com filhos\nalimentação simples", datas="05/11 - Dia do Treino\n09/11 - Black Friday")
    B.update(k); return B


@pytest.mark.parametrize("obj", ST.OBJ)
def test_local(obj):
    P = ST.build_local(brief(obj_mes=obj)).pecas
    assert len(P) == 10 and [p.n for p in P] == list(range(1, 11))
    assert all(p.formato == "Carrossel" for p in P)
    assert [p.dia for p in P] == list(range(1, 11))
    assert tuple(sum(p.funil == f for p in P) for f in ST.FUN) == ST.FUNIL[obj]
    assert sum(ST.FUNIL[obj]) == 10
    assert all(p.slides and p.gancho and p.cta and len(p.slides) == 6 for p in P)
    assert all(p.slides[0].layout == "capa" and p.slides[-1].layout == "cta" and p.slides[-1].cta for p in P)
    assert not any(P[i].pilar == P[i + 1].pilar == P[i + 2].pilar for i in range(8)), [p.pilar for p in P]


def test_dates():
    t = " ".join(p.tema for p in ST.build_local(brief()).pecas); assert "Dia do Treino" in t and "Black Friday" in t


def test_report_pdf():
    B = brief(); pdf = build_report(B, ST.build_local(B))
    assert pdf[:5] == b"%PDF-" and len(re.findall(rb"/Type\s*/Page(?!s)", pdf)) >= 4


@pytest.mark.parametrize("modelo", ["Studio · Vinho DBB", "Studio · Rosé Creme", "DBB Soluções", "Livre (layouts criativos)"])
def test_pack(modelo):
    B = brief(); S = ST.build_local(B); rp = make_renderer(modelo, "Instagram 4:5", "@x", "Obsidiana", "Editorial", True)
    z = zipfile.ZipFile(io.BytesIO(pack_zip(B, S, rp))); n = z.namelist()
    assert len([x for x in n if x.endswith("carrossel.pdf")]) == 10 and len([x for x in n if x.endswith("legenda.txt")]) == 10
    assert len([x for x in n if x.endswith(".png")]) >= 60
    assert "00_linha_editorial.pdf" in n and "00_calendario.csv" in n and all(z.read(x)[:5] == b"%PDF-" for x in n if x.endswith(".pdf"))
