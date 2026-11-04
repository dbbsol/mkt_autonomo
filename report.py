"""Linha editorial em PDF (A4, reportlab): diagnóstico, público, pilares, funil, calendário, roteiro de cada peça e rotina de execução."""
import io, datetime as dt
from collections import Counter
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
import strategy as ST

FD = Path(__file__).parent / "assets" / "fonts"
try:
    pdfmetrics.registerFont(TTFont("PR", str(FD / "Poppins-Regular.ttf"))); pdfmetrics.registerFont(TTFont("PB", str(FD / "Poppins-SemiBold.ttf"))); R, BD = "PR", "PB"
except Exception:
    R, BD = "Helvetica", "Helvetica-Bold"
INK, ACC, SOFT, GREY = colors.HexColor("#1B1F3B"), colors.HexColor("#6D4AFF"), colors.HexColor("#F3F1FF"), colors.HexColor("#6B7090")
ST_ = dict(h1=ParagraphStyle("h1", fontName=BD, fontSize=26, leading=31, textColor=INK, spaceAfter=4),
           h2=ParagraphStyle("h2", fontName=BD, fontSize=14, leading=18, textColor=ACC, spaceBefore=14, spaceAfter=6),
           h3=ParagraphStyle("h3", fontName=BD, fontSize=10.5, leading=14, textColor=INK, spaceBefore=8),
           b=ParagraphStyle("b", fontName=R, fontSize=9.5, leading=14, textColor=INK), s=ParagraphStyle("s", fontName=R, fontSize=8.5, leading=12, textColor=GREY),
           c=ParagraphStyle("c", fontName=R, fontSize=8, leading=10.5, textColor=INK), ch=ParagraphStyle("ch", fontName=BD, fontSize=8, leading=10.5, textColor=colors.white))


def P(t, k="b"): return Paragraph(escape(str(t or "")).replace("\n", "<br/>"), ST_[k])
def bullets(items): return [P("• " + x) for x in items] or [P("—", "s")]


def tbl(rows, widths):
    t = Table([[P(c, "ch") for c in rows[0]]] + [[P(c, "c") for c in r] for r in rows[1:]], colWidths=[w * mm for w in widths], repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), ACC), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SOFT]),
                           ("GRID", (0, 0), (-1, -1), .25, colors.HexColor("#D9D6F0")), ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                           ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    return t


def build_report(B, S):
    buf = io.BytesIO(); L = ST.L
    doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm, title=f"Linha editorial - {B['cliente']}")
    ini = dt.date.fromisoformat(B["inicio"]); fim = ini + dt.timedelta(days=29)
    E = [P("Linha editorial estratégica", "h1"), P(f"{B['cliente']} · {B.get('insta') or ''}", "h3"), P(f"Período: {ini:%d/%m/%Y} a {fim:%d/%m/%Y} · 15 peças · {B['obj_mes']}", "s"), Spacer(1, 6)]
    E += [P("1. Diagnóstico e posicionamento", "h2"), P(S.diagnostico)]
    if B.get("desc"): E += [P("Descrição do negócio", "h3"), P(B["desc"])]
    E += [P("Ofertas", "h3")] + bullets(L(B.get("ofertas"))) + [P("Diferenciais e provas (informados pelo cliente)", "h3")] + bullets(L(B.get("diferenciais")))
    if B.get("proibido"): E += [P("O que não pode ser dito", "h3"), P(B["proibido"])]
    E += [P("2. Público", "h2"), P(f"{B.get('pub') or 'a definir'} · faixa etária: {B.get('idade')} · região: {B.get('regiao') or 'a definir'}"), P(f"Nível de consciência: {B['consc']}", "s"),
          P("Dores", "h3")] + bullets(L(B.get("dores"))) + [P("Desejos", "h3")] + bullets(L(B.get("desejos"))) + [P("Objeções", "h3")] + bullets(L(B.get("objecoes")))
    E += [P("3. Pilares editoriais", "h2"), tbl([["Pilar", "Funil", "Função"]] + [[p.nome, p.funil, p.descricao] for p in S.pilares], [48, 18, 108])]
    fc, fm = Counter(p.funil for p in S.pecas), Counter(p.formato for p in S.pecas)
    E += [P("4. Funil e ritmo", "h2"), tbl([["Topo (atrair)", "Meio (educar)", "Fundo (converter)", "Carrosséis", "Posts fixos"],
                                         [fc["Topo"], fc["Meio"], fc["Fundo"], fm["Carrossel"], fm["Post fixo"]]], [35, 35, 38, 34, 34]),
          P("Regras: não repetir o mesmo pilar ou formato mais de 2 vezes seguidas; um único CTA por peça; conteúdo de topo pede ação leve (salvar/compartilhar), conteúdo de fundo pede a ação principal.", "s")]
    E += [PageBreak(), P("5. Calendário de 30 dias", "h2"), tbl([["Dia", "Data", "Formato", "Pilar / funil", "Tema, gancho e CTA"]] +
          [[p.dia, ST.dlabel(B, p), p.formato, f"{p.pilar} ({p.funil})", f"{p.tema}\nGancho: {p.gancho}\nCTA: {p.cta}"] for p in S.pecas], [10, 20, 22, 36, 88])]
    E += [PageBreak(), P("6. Roteiro de cada peça", "h2")]
    for p in S.pecas:
        blk = [P(f"Peça {p.n:02d} · dia {p.dia} ({ST.dlabel(B, p)}) · {p.formato} · {p.pilar}", "h3"), P(f"Tema: {p.tema} | Funil: {p.funil}", "s")]
        for k, s in enumerate(p.slides, 1):
            txt = " | ".join(x for x in (s.headline, s.subhead, s.body, f"CTA: {s.cta}" if s.cta else "") if x)
            blk.append(P(f"Slide {k}: {txt}", "c"))
        blk += [P("Legenda sugerida:", "s"), P(p.legenda, "c"), Spacer(1, 4)]
        E.append(KeepTogether(blk))
    E += [P("7. Rotina de execução e métricas", "h2"), P(f"Indicadores principais: {ST.KPIS[B['obj_mes']]}.")] + bullets([
        "Semanal: revisar alcance, salvamentos, compartilhamentos e mensagens recebidas; manter o que performou e ajustar o gancho do que não performou.",
        "Antes de publicar: conferir fatos, preços e prazos marcados como “a confirmar” e o que não pode ser dito.",
        "Responder comentários e mensagens em até 24 h para sustentar o engajamento.",
        "Ao fim dos 30 dias: comparar com o período anterior e definir os pilares do próximo ciclo."])

    def foot(c, d):
        c.setFont(R, 8); c.setFillColor(GREY); c.drawString(18 * mm, 10 * mm, f"{B['cliente']} · Linha editorial de 30 dias"); c.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Página {d.page}")
    doc.build(E, onFirstPage=foot, onLaterPages=foot)
    return buf.getvalue()
