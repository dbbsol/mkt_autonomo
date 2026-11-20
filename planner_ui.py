"""Tela 'Plano de 10 dias': briefing guiado -> estratégia -> calendário (10 carrosséis, 1 por dia) -> design dos slides -> PDF/PNG/ZIP."""
import csv, io, json, re, unicodedata, zipfile, datetime as dt
import streamlit as st
import pandas as pd
from config import FORMATS
from renderer import render_any, model_names, is_studio, LIVRE
from engine import LAYOUTS
from config import THEMES
from export import to_pdf, to_zip
from ai import Slide, gemini_plan, _clean
from editor import slide_editor
import strategy as ST
import ui
from report import build_report

DEFAULT_MODEL = "Studio · Vinho DBB"


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
    w.writerow(["Carrossel", "Dia", "Data", "Pilar", "Funil", "Tema", "Gancho", "CTA"])
    for p in S.pecas: w.writerow([p.n, p.dia, ST.dlabel(B, p), p.pilar, p.funil, p.tema, p.gancho, p.cta])
    return "﻿" + o.getvalue()


def make_renderer(modelo, fmt, brand, theme, layout, ind, logo=None, imgs_of=None):
    """Devolve rp(slides, n=None) -> (imagens, avisos). `n` = número do carrossel (para achar as imagens enviadas para ele)."""
    def rp(slides, n=None):
        imgs = list(imgs_of(n)) if (imgs_of and n is not None) else []
        return render_any(slides, fmt, modelo, brand, theme or "Obsidiana", layout or "Editorial", ind, imgs, logo)
    return rp


def pack_zip(B, S, rp, progress=None):
    z = io.BytesIO()
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("00_linha_editorial.pdf", build_report(B, S)); zf.writestr("00_calendario.csv", cal_csv(B, S))
        for k, p in enumerate(S.pecas):
            ims, _ = rp(p.slides, p.n); folder = f"carrosseis/{p.n:02d}_dia{p.dia:02d}_{slug(p.tema)}"
            zf.writestr(f"{folder}/carrossel.pdf", to_pdf(ims))
            for j, im in enumerate(ims, 1):
                b = io.BytesIO(); im.save(b, "PNG"); zf.writestr(f"{folder}/slide_{j:02d}.png", b.getvalue())
            zf.writestr(f"{folder}/legenda.txt", f"{p.gancho}\n\n{p.legenda}\n")
            if progress: progress((k + 1) / len(S.pecas))
    return z.getvalue()


def run_planner():
    S = st.session_state
    for k, v in dict(strat=None, cver=0, pack=None, pmsg="", imgs={}, cursl={}).items(): S.setdefault(k, v)
    for k, v in ST.DEF.items(): S.setdefault("b_" + k, v)
    with st.sidebar:
        ui.brand("Plano de 10 dias")
        use_ai = ui.gemini_panel()
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
        st.caption("O servidor não guarda dados entre sessões: salve o projeto para continuar depois. As imagens enviadas não entram no arquivo.")

    ui.nav("Plano de 10 dias")
    ui.hero("10 DIAS · 10 CARROSSÉIS", 'Um carrossel por dia, <span class="grad">prontos para postar</span>.',
            "Conte sobre o cliente e o público: o sistema monta a estratégia, o calendário de 10 dias e desenha cada carrossel no visual escolhido, com suas fotos e ícones.")
    t1, t2, t3, t4, t5 = st.tabs(["① Cliente", "② Público", "③ Estratégia", "④ Calendário", "⑤ Carrosséis"])
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
        a.selectbox("Objetivo do período", ST.OBJ, key="b_obj_mes"); b.multiselect("Tom de voz", ST.TONS, key="b_tom")
        st.multiselect("Pilares de conteúdo", list(ST.PILAR_FUNIL), key="b_pilares"); a.text_input("Pilar extra (opcional)", key="b_pilar_extra")
        b.selectbox("CTA preferido", ST.CTAS, key="b_cta")
        if S.b_cta == "Comentar palavra-chave": a.text_input("Palavra-chave do CTA", key="b_palavra", placeholder="ex.: QUERO")
        b.date_input("Início do plano (dia 1)", key="b_inicio", format="DD/MM/YYYY")
        st.text_area("O que NÃO pode ser dito (regras, promessas proibidas)", key="b_proibido", height=80)
        st.text_area("Datas relevantes (1 por linha, formato dd/mm - evento)", key="b_datas", height=80)
        if st.button("✦ GERAR PLANO DE 10 DIAS", type="primary", key="btn_plan"):
            B = make_B(S)
            if not (S.b_cliente or "").strip(): st.warning("Informe o nome do cliente na etapa ①.")
            else:
                S.pmsg = ""
                try:
                    with st.spinner("Montando a estratégia..."):
                        S.strat = ST.build_ai(B) if use_ai else ST.build_local(B)
                except Exception as e:
                    S.strat, S.pmsg = ST.build_local(B), f"Gemini falhou; usei o planejador local. Motivo: {_clean(e)}"
                S.cver += 1; S.pack = None
        if S.pmsg: st.warning(S.pmsg)
        if S.strat:
            st.markdown("**Diagnóstico**"); st.write(S.strat.diagnostico)
            fc = {f: sum(p.funil == f for p in S.strat.pecas) for f in ST.FUN}; m = st.columns(4)
            for c, (k, v) in zip(m, [("Carrosséis", len(S.strat.pecas)), ("Topo", fc["Topo"]), ("Meio", fc["Meio"]), ("Fundo", fc["Fundo"])]): c.metric(k, v)
            st.dataframe(pd.DataFrame([p.model_dump() for p in S.strat.pilares]), hide_index=True, width="stretch")
    B = make_B(S)
    with t4:
        if not S.strat: st.info("Gere o plano na etapa ③.")
        else:
            pcs = S.strat.pecas
            df = pd.DataFrame([dict(dia=p.dia, data=ST.dlabel(B, p), pilar=p.pilar, funil=p.funil, tema=p.tema, gancho=p.gancho, cta=p.cta) for p in pcs])
            ed = st.data_editor(df, hide_index=True, width="stretch", key=f"ed_cal_{S.cver}", num_rows="fixed", disabled=["dia", "data"],
                                column_config={"funil": st.column_config.SelectboxColumn(options=ST.FUN), "dia": st.column_config.NumberColumn("dia", width="small")})
            for p, r in zip(pcs, ed.to_dict("records")):
                if (p.tema, p.gancho, p.cta) != (r["tema"], r["gancho"], r["cta"]): p.slides = []  # texto desatualizado: será regerado
                p.pilar, p.funil, p.tema, p.gancho, p.cta = r["pilar"], r["funil"], r["tema"], r["gancho"], r["cta"]
            st.caption("Edite a tabela à vontade. Carrosséis alterados terão os textos regerados na etapa ⑤.")
    with t5:
        if not S.strat: st.info("Gere o plano na etapa ③.")
        else: design_tab(S, B, use_ai)


def design_tab(S, B, use_ai):
    pcs = S.strat.pecas
    with st.container(key="panel"):
        names = model_names(); a, b, c = st.columns(3)
        modelo = a.selectbox("Modelo visual", names, index=names.index(DEFAULT_MODEL) if DEFAULT_MODEL in names else 0, key="p_modelo")
        fmt = b.selectbox("Formato", list(FORMATS), key="p_fmt")
        brand = c.text_input("@ / marca nos slides", value=B.get("insta") or "", key="p_brand")
        a, b, c = st.columns(3)
        logo_f = a.file_uploader("Logo ou foto de perfil (opcional)", ["png", "jpg", "jpeg", "webp"], key="p_logo")
        ind = b.toggle("Indicador de carrossel (pontos e seta)", True, key="p_ind")
        theme = layout = None
        if modelo == LIVRE:
            theme = b.selectbox("Tema", list(THEMES), key="p_theme"); layout = c.selectbox("Layout", list(LAYOUTS), key="p_layout")
    logo = logo_f.getvalue() if logo_f else None
    rp = make_renderer(modelo, fmt, brand, theme, layout, ind, logo, lambda n: S.imgs.get(n, []))
    miss = sum(not p.slides for p in pcs)
    g1, g2, _ = st.columns([2, 2, 3])
    if g1.button(f"✦ GERAR TEXTOS DOS CARROSSÉIS ({miss} pendentes)" if miss else "↻ REGERAR TODOS OS TEXTOS", type="primary", width="stretch", key="btn_cards"):
        bar = st.progress(0.0)
        with st.spinner("Escrevendo os carrosséis..."):
            w = ST.write_cards(S.strat, B, use_ai, only_missing=bool(miss), progress=bar.progress)
        S.cver += 1; S.pack = None
        for x in w: st.warning(x)
        if not w: st.rerun()
    if any(not p.slides for p in pcs): ST.write_cards(S.strat, B, False, only_missing=True)  # garante texto base para o preview

    st.markdown('<div class="gl"></div>', unsafe_allow_html=True)
    opts = {p.n: f"{p.n:02d}" for p in pcs}
    n_sel = st.radio("Carrossel (um por dia)", list(opts), format_func=lambda n: f"Dia {pcs[n - 1].dia}", horizontal=True, key="p_sel")
    p = pcs[n_sel - 1]
    st.markdown(f'<span class="daychip">DIA {p.dia} · {ST.dlabel(B, p)}</span><span class="daychip">{p.pilar} · {p.funil}</span> **{p.gancho}**', unsafe_allow_html=True)
    ups = st.file_uploader("Imagens deste carrossel (opcional): fotos do cliente, produto, equipe…", ["png", "jpg", "jpeg", "webp"], accept_multiple_files=True, key=f"up_{p.n}")
    S.imgs[p.n] = [f.getvalue() for f in ups]; n_img = len(S.imgs[p.n])

    cur = min(S.cursl.get(p.n, 0), len(p.slides) - 1); S.cursl[p.n] = cur
    left, right = st.columns([3, 2])
    with right:
        st.markdown(f'<div class="page-eyebrow">EDITAR SLIDE {cur + 1}</div>', unsafe_allow_html=True)
        slide_editor(p.slides[cur], f"pe{p.n}_{cur}_{S.cver}_", n_img, is_studio(modelo))
        c1, c2, c3 = st.columns(3)
        if c1.button("＋ Slide", key=f"add{p.n}", width="stretch") and len(p.slides) < 10:
            p.slides.insert(cur + 1, Slide(label="", headline="Novo slide")); S.cursl[p.n] = cur + 1; S.cver += 1; st.rerun()
        if c2.button("－ Slide", key=f"del{p.n}", width="stretch") and len(p.slides) > 2:
            p.slides.pop(cur); S.cursl[p.n] = max(0, cur - 1); S.cver += 1; st.rerun()
        if c3.button("↻ IA", key=f"ai{p.n}", width="stretch", help="Reescreve todos os slides deste carrossel"):
            try:
                if not use_ai: raise ValueError("Ative o Gemini na barra lateral.")
                p.slides = gemini_plan(ST.card_brief(B, p), len(p.slides), "Instagram 4:5", n_img).slides
            except Exception as e:
                st.warning(f"Não deu para usar a IA: {_clean(e)[:160]}"); p.slides = ST.local_slides(B, p)
            S.cver += 1; st.rerun()
    ims, warns = rp(p.slides, p.n)
    with left:
        with st.container(key="stage"):
            st.markdown(f'<div class="slide-count">SLIDE {cur + 1} / {len(ims)}</div>', unsafe_allow_html=True)
            st.image(ims[cur], width="stretch")
    for w in dict.fromkeys(warns): st.warning(w)
    cols = st.columns(len(ims))
    for k, cc in enumerate(cols):
        with cc.container(key=f"thumb_{'on' if k == cur else 'off'}_{p.n}_{k}"):
            st.image(ims[k], width="stretch")
            if st.button(f"{k + 1:02d}", key=f"t{p.n}_{k}", width="stretch"):
                S.cursl[p.n] = k; st.rerun()

    st.markdown("**Legenda sugerida**"); p.legenda = st.text_area("Legenda", p.legenda, key=f"lg_{p.n}_{S.cver}", label_visibility="collapsed", height=130)
    st.markdown('<div class="gl"></div>', unsafe_allow_html=True); d1, d2, d3 = st.columns(3)
    d1.download_button("⬇ LINHA EDITORIAL (PDF)", build_report(B, S.strat), f"plano_10_dias_{slug(B['cliente'])}.pdf", "application/pdf", width="stretch")
    d2.download_button("⬇ ESTE CARROSSEL (PDF)", to_pdf(ims), f"carrossel_{p.n:02d}_{slug(p.tema)}.pdf", "application/pdf", width="stretch")
    d2.download_button("⬇ ESTE CARROSSEL (PNG, ZIP)", to_zip(ims), f"carrossel_{p.n:02d}_{slug(p.tema)}.zip", "application/zip", width="stretch")
    if d3.button("📦 MONTAR PACOTE DOS 10 CARROSSÉIS", width="stretch", key="btn_pack"):
        bar = st.progress(0.0)
        with st.spinner("Renderizando os 10 carrosséis..."): S.pack = pack_zip(B, S.strat, rp, bar.progress)
    if S.pack: d3.download_button("⬇ BAIXAR PACOTE (ZIP)", S.pack, f"pacote_10_dias_{slug(B['cliente'])}.zip", "application/zip", type="primary", width="stretch")
