"""Tela 'Plano de 30 dias': briefing guiado -> linha editorial -> calendário (15 peças) -> cards no kit do cliente -> PDF/ZIP."""
import csv, io, json, os, re, unicodedata, zipfile, datetime as dt
import streamlit as st
import pandas as pd
from config import FORMATS, THEMES
from engine import LAYOUTS, render
from templates import TEMPLATES
from template_engine import render_tpl
from dsl import render_dsl
from carousel_icon import add_indicator
from export import to_pdf
from ai import _clean
import strategy as ST
from report import build_report


def slug(t):
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", t.lower()).strip("_")[:40] or "peca"


def make_B(S):
    B = {k: S.get("b_" + k, v) for k, v in ST.DEF.items()}
    B["inicio"] = B["inicio"].isoformat() if hasattr(B["inicio"], "isoformat") else str(B["inicio"])
    B["nicho_final"] = ((B["nicho_outro"] or "").strip() or "seu nicho") if B["nicho"] == "Outro" else B["nicho"]
    B["cliente"] = (B["cliente"] or "").strip() or "Cliente"
    return B


def cal_csv(B, S):
    o = io.StringIO(); w = csv.writer(o, delimiter=";")
    w.writerow(["Peça", "Dia", "Data", "Formato", "Pilar", "Funil", "Tema", "Gancho", "CTA"])
    for p in S.pecas: w.writerow([p.n, p.dia, ST.dlabel(B, p), p.formato, p.pilar, p.funil, p.tema, p.gancho, p.cta])
    return "\ufeff" + o.getvalue()


def make_renderer(modelo, fmt, brand, theme, layout, ind):
    tpl = TEMPLATES.get(modelo)

    def rp(slides):
        if tpl and tpl.get("engine") == "dsl": ims, w = render_dsl(slides, fmt, tpl, brand, [])
        elif tpl: ims, w = render_tpl(slides, fmt, tpl, brand, len(slides) >= 3)
        else: ims, w = render(slides, fmt, THEMES[theme], layout, [], brand, None)
        if ind: ims = [add_indicator(im, k, len(ims)) for k, im in enumerate(ims)]
        return ims, w
    return rp


def pack_zip(B, S, rp, progress=None):
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("00_linha_editorial.pdf", build_report(B, S)); zf.writestr("00_calendario.csv", cal_csv(B, S))
        for k, p in enumerate(S.pecas):
            ims, _ = rp(p.slides); nm = f"{p.n:02d}_dia{p.dia:02d}_{slug(p.formato)}_{slug(p.tema)}"
            zf.writestr(f"cards/{nm}.pdf", to_pdf(ims)); zf.writestr(f"legendas/{nm}.txt", f"{p.gancho}\n\n{p.legenda}\n")
            if progress: progress((k + 1) / len(S.pecas))
    return z.getvalue()


def run_planner():
    S = st.session_state
    for k, v in dict(strat=None, cver=0, pack=None, pmsg="").items(): S.setdefault(k, v)
    for k, v in ST.DEF.items(): S.setdefault("b_" + k, v)
    ok = bool(os.getenv("GEMINI_API_KEY"))
    with st.sidebar:
        st.markdown('<div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">CONTENT STUDIO</div><div class="brand-sub">Plano de 30 dias</div></div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status {"ok" if ok else "off"}"><i></i>{"Gemini configurado" if ok else "Gemini não configurado (modo local)"}</div>', unsafe_allow_html=True)
        use_ai = st.toggle("Usar Gemini (estratégia e textos)", ok, disabled=not ok)
        st.markdown('<div class="side-title">PROJETO DO CLIENTE</div>', unsafe_allow_html=True)
        up = st.file_uploader("Abrir projeto (.json)", ["json"], key="proj_up")
        if up is not None and S.get("proj_id") != f"{up.name}-{up.size}":
            S.proj_id = f"{up.name}-{up.size}"
            try:
                d = json.loads(up.getvalue())
                for k, v in d["brief"].items():
                    if k in ST.DEF: S["b_" + k] = dt.date.fromisoformat(v) if k == "inicio" else v
                S.strat = ST.Strategy(**d["strategy"]) if d.get("strategy") else None; S.cver += 1; S.pack = None
                st.rerun()
            except st.errors.StreamlitAPIException: raise
            except Exception:
                st.error("Arquivo de projeto inválido.")
        B0 = make_B(S)
        st.download_button("⬇ Salvar projeto (.json)", json.dumps({"brief": B0, "strategy": S.strat.model_dump() if S.strat else None}, ensure_ascii=False, default=str),
                           f"projeto_{slug(B0['cliente'])}.json", "application/json", width="stretch")
        st.caption("O servidor não guarda dados entre sessões: salve o projeto para continuar depois.")

    st.markdown('<div class="hero"><div class="hero-eyebrow">✦ ESTRATÉGIA · CALENDÁRIO · PRODUÇÃO</div><h1>Plano de 30 dias</h1><p>Conte sobre o cliente e o público: o sistema monta a linha editorial (15 peças), o calendário e os cards no kit visual do cliente.</p></div>', unsafe_allow_html=True)
    t1, t2, t3, t4, t5 = st.tabs(["① Cliente", "② Público", "③ Estratégia", "④ Calendário", "⑤ Cards e exportação"])
    with t1:
        a, b = st.columns(2)
        a.text_input("Nome do cliente / marca", key="b_cliente"); b.text_input("@ do Instagram", key="b_insta", placeholder="@cliente")
        a.selectbox("Nicho", ST.NICHOS, key="b_nicho")
        if S.b_nicho == "Outro": b.text_input("Qual nicho?", key="b_nicho_outro")
        st.text_area("Descrição do negócio, bio ou texto do site", key="b_desc", height=120, placeholder="Cole a bio, o texto do site ou descreva o que o cliente faz e como atende.")
        a.text_area("Ofertas / serviços (1 por linha)", key="b_ofertas", height=120); b.text_area("Diferenciais e provas reais (1 por linha)", key="b_diferenciais", height=120)
        st.text_area("Temas que o cliente domina (1 por linha)", key="b_temas", height=110, placeholder="ex.: alimentação na gravidez\nerros de treino\nrotina com filhos")
    with t2:
        st.text_input("Quem é o público?", key="b_pub", placeholder="ex.: mulheres de 30 a 45 anos que querem voltar a treinar com pouco tempo")
        a, b, c = st.columns(3)
        a.selectbox("Faixa etária", ["Até 24", "25–34", "35–44", "45–54", "55+", "Misto"], key="b_idade"); b.text_input("Região", key="b_regiao"); c.selectbox("Nível de consciência", ST.CONSC, key="b_consc")
        a, b, c = st.columns(3)
        a.text_area("Dores (1 por linha)", key="b_dores", height=150); b.text_area("Desejos (1 por linha)", key="b_desejos", height=150); c.text_area("Objeções (1 por linha)", key="b_objecoes", height=150)
    with t3:
        a, b = st.columns(2)
        a.selectbox("Objetivo do mês", ST.OBJ, key="b_obj_mes"); b.multiselect("Tom de voz", ST.TONS, key="b_tom")
        st.multiselect("Pilares de conteúdo", list(ST.PILAR_FUNIL), key="b_pilares"); a.text_input("Pilar extra (opcional)", key="b_pilar_extra")
        b.selectbox("CTA preferido", ST.CTAS, key="b_cta")
        if S.b_cta == "Comentar palavra-chave": a.text_input("Palavra-chave do CTA", key="b_palavra", placeholder="ex.: QUERO")
        a.slider("Carrosséis (o restante vira posts fixos)", 5, 12, key="b_ncar"); b.date_input("Início do período", key="b_inicio")
        st.text_area("O que NÃO pode ser dito (regras, promessas proibidas)", key="b_proibido", height=80)
        st.text_area("Datas relevantes (1 por linha, formato dd/mm - evento)", key="b_datas", height=80)
        if st.button("✦ GERAR LINHA EDITORIAL (30 DIAS)", type="primary"):
            B = make_B(S)
            if not (S.b_cliente or "").strip(): st.warning("Informe o nome do cliente na etapa ①.")
            else:
                try:
                    with st.spinner("Montando a estratégia..."):
                        S.strat, S.pmsg = (ST.build_ai(B) if use_ai else ST.build_local(B)), ""
                except Exception as e:
                    S.strat, S.pmsg = ST.build_local(B), f"Gemini falhou; usei o planejador local. Motivo: {_clean(e)}"
                S.cver += 1; S.pack = None
        if S.pmsg: st.warning(S.pmsg)
        if S.strat:
            st.markdown("**Diagnóstico**"); st.write(S.strat.diagnostico)
            fc = {f: sum(p.funil == f for p in S.strat.pecas) for f in ST.FUN}; m = st.columns(5)
            for c, (k, v) in zip(m, [("Peças", len(S.strat.pecas)), ("Topo", fc["Topo"]), ("Meio", fc["Meio"]), ("Fundo", fc["Fundo"]), ("Carrosséis", sum(p.formato == "Carrossel" for p in S.strat.pecas))]): c.metric(k, v)
            st.dataframe(pd.DataFrame([p.model_dump() for p in S.strat.pilares]), hide_index=True, width="stretch")
    B = make_B(S)
    with t4:
        if not S.strat: st.info("Gere a linha editorial na etapa ③.")
        else:
            pcs = S.strat.pecas
            df = pd.DataFrame([dict(dia=p.dia, data=ST.dlabel(B, p), formato=p.formato, pilar=p.pilar, funil=p.funil, tema=p.tema, gancho=p.gancho, cta=p.cta) for p in pcs])
            ed = st.data_editor(df, hide_index=True, width="stretch", key=f"ed_cal_{S.cver}", num_rows="fixed", disabled=["data"], column_config={
                "formato": st.column_config.SelectboxColumn(options=["Carrossel", "Post fixo"]), "funil": st.column_config.SelectboxColumn(options=ST.FUN),
                "dia": st.column_config.NumberColumn(min_value=1, max_value=30, step=1)})
            for p, r in zip(pcs, ed.to_dict("records")):
                if (p.formato, p.tema, p.gancho, p.cta) != (r["formato"], r["tema"], r["gancho"], r["cta"]): p.slides = []  # texto desatualizado: será regerado
                p.dia, p.formato, p.pilar, p.funil, p.tema, p.gancho, p.cta = int(r["dia"]), r["formato"], r["pilar"], r["funil"], r["tema"], r["gancho"], r["cta"]
            st.caption("Edite a tabela à vontade. Peças alteradas terão os textos dos cards regerados na etapa ⑤.")
    with t5:
        if not S.strat: st.info("Gere a linha editorial na etapa ③.")
        else:
            a, b, c = st.columns(3)
            modelo = a.selectbox("Modelo visual do cliente", list(TEMPLATES) + ["Livre (layouts criativos)"], key="p_modelo"); fmt = b.selectbox("Formato", list(FORMATS), key="p_fmt")
            brand = c.text_input("@ / marca nos cards", value=B.get("insta") or "", key="p_brand")
            theme = layout = None
            if modelo not in TEMPLATES:
                theme = a.selectbox("Tema", list(THEMES), key="p_theme"); layout = b.selectbox("Layout", list(LAYOUTS), key="p_layout")
            ind = c.toggle("Indicador de carrossel", True, key="p_ind")
            rp = make_renderer(modelo, fmt, brand, theme, layout, ind)
            miss = sum(not p.slides for p in S.strat.pecas)
            g1, g2, _ = st.columns([2, 2, 3])
            if g1.button(f"✦ GERAR TEXTOS DOS CARDS ({miss} pendentes)" if miss else "↻ REGERAR TODOS OS TEXTOS", type="primary", width="stretch"):
                bar = st.progress(0.0)
                w = ST.write_cards(S.strat, B, use_ai, only_missing=bool(miss), progress=bar.progress)
                S.cver += 1; S.pack = None
                for x in w: st.warning(x)
                st.rerun() if not w else None
            if any(not p.slides for p in S.strat.pecas): ST.write_cards(S.strat, B, False, only_missing=True)  # garante texto base para preview/export
            opts = [f"{p.n:02d} · dia {p.dia} · {p.formato} · {p.gancho[:45]}" for p in S.strat.pecas]
            sel = st.selectbox("Peça", opts, key="p_sel"); p = S.strat.pecas[opts.index(sel)]
            df = pd.DataFrame([s.model_dump(include={"label", "headline", "subhead", "body", "cta", "highlight"}) for s in p.slides])
            ed = st.data_editor(df, hide_index=True, width="stretch", num_rows="fixed", key=f"sl_{p.n}_{S.cver}")
            for s, r in zip(p.slides, ed.to_dict("records")):
                for k, v in r.items(): setattr(s, k, v or "")
            ims, warns = rp(p.slides); cols = st.columns(min(len(ims), 6))
            for c_, im in zip(cols, ims[:6]): c_.image(im, width="stretch")
            for w in dict.fromkeys(warns): st.warning(w)
            st.markdown("**Legenda sugerida**"); p.legenda = st.text_area("Legenda", p.legenda, key=f"lg_{p.n}_{S.cver}", label_visibility="collapsed", height=120)
            st.markdown("---"); d1, d2, d3 = st.columns(3)
            d1.download_button("⬇ LINHA EDITORIAL (PDF)", build_report(B, S.strat), f"linha_editorial_{slug(B['cliente'])}.pdf", "application/pdf", width="stretch")
            ims_p, _ = rp(p.slides)
            d2.download_button("⬇ CARD DESTA PEÇA (PDF)", to_pdf(ims_p), f"peca_{p.n:02d}_{slug(p.tema)}.pdf", "application/pdf", width="stretch")
            if d3.button("📦 MONTAR PACOTE COMPLETO (ZIP)", width="stretch"):
                bar = st.progress(0.0)
                with st.spinner("Renderizando as 15 peças..."): S.pack = pack_zip(B, S.strat, rp, bar.progress)
            if S.pack: st.download_button("⬇ BAIXAR PACOTE (linha editorial + cards + legendas + calendário)", S.pack, f"pacote_{slug(B['cliente'])}.zip", "application/zip", type="primary")
