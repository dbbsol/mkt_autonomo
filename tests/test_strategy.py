import sys, os, io, re, types, zipfile
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import strategy as ST
from report import build_report
from planner_ui import pack_zip, make_renderer


def brief(**k):
    B = dict(ST.DEF)
    B.update(cliente="Studio Glau", insta="@personalglau", nicho_final="Fitness / personal", inicio="2026-11-02", pub="mães que querem voltar a treinar",
             dores="falta de tempo\ncansaço\nculpa por se priorizar", desejos="energia\nconfiança", objecoes="não tenho tempo\nacademia é cara", ofertas="Treino online\nConsultoria 1:1",
             diferenciais="Treinos de 30 minutos\nAcompanhamento semanal", temas="treino em casa\nrotina com filhos\nalimentação simples", datas="12/11 - Dia do Treino\n25/11 - Black Friday")
    B.update(k); return B


@pytest.mark.parametrize("obj", ST.OBJ)
@pytest.mark.parametrize("ncar", [5, 9, 12])
def test_local(obj, ncar):
    P = ST.build_local(brief(obj_mes=obj, ncar=ncar)).pecas
    assert len(P) == 15 and [p.n for p in P] == list(range(1, 16))
    assert sum(p.formato == "Carrossel" for p in P) == ncar
    d = [p.dia for p in P]; assert d == sorted(d) and d[0] == 1 and d[-1] == 30
    assert tuple(sum(p.funil == f for p in P) for f in ST.FUN) == ST.FUNIL[obj]
    assert all(p.slides and p.gancho and p.cta for p in P)
    assert all(len(p.slides) == (6 if p.formato == "Carrossel" else 1) for p in P)
    assert not any(P[i].pilar == P[i + 1].pilar == P[i + 2].pilar for i in range(13)), [p.pilar for p in P]


def test_dates():
    t = " ".join(p.tema for p in ST.build_local(brief()).pecas); assert "Dia do Treino" in t and "Black Friday" in t


def test_report_pdf():
    B = brief(); pdf = build_report(B, ST.build_local(B))
    assert pdf[:5] == b"%PDF-" and len(re.findall(rb"/Type\s*/Page(?!s)", pdf)) >= 4


@pytest.mark.parametrize("modelo", ["DBB Soluções", "Legado Capital", "Livre (layouts criativos)"])
def test_pack(modelo):
    B = brief(); S = ST.build_local(B); rp = make_renderer(modelo, "Instagram 4:5", "@x", "Obsidiana", "Editorial", True)
    z = zipfile.ZipFile(io.BytesIO(pack_zip(B, S, rp))); n = z.namelist()
    assert len([x for x in n if x.startswith("cards/")]) == 15 and len([x for x in n if x.startswith("legendas/")]) == 15
    assert "00_linha_editorial.pdf" in n and "00_calendario.csv" in n and all(z.read(x)[:5] == b"%PDF-" for x in n if x.endswith(".pdf"))


def test_ai_fix(monkeypatch):
    class R: text = '{"diagnostico":"ok","pilares":[],"pecas":[{"n":1,"dia":40,"formato":"carrossel","pilar":"Educação","funil":"topo","tema":"t","gancho":"g","cta":"c"}]}'
    class M: generate_content = staticmethod(lambda **k: R())
    class C:
        def __init__(self, **k): self.models = M()
    g = types.ModuleType("google"); ge = types.ModuleType("google.genai"); ge.Client = C; g.genai = ge
    monkeypatch.setitem(sys.modules, "google", g); monkeypatch.setitem(sys.modules, "google.genai", ge); monkeypatch.setenv("GEMINI_API_KEY", "x")
    S = ST.build_ai(brief())
    assert len(S.pecas) == 15 and all(1 <= p.dia <= 30 and p.formato in ("Carrossel", "Post fixo") and p.funil in ST.FUN for p in S.pecas)
