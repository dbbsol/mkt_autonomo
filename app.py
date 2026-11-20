from pathlib import Path
import streamlit as st
from dotenv import load_dotenv
load_dotenv()
import ui
from config import FORMATS, THEMES
from ai import make_plan, _clean
from engine import LAYOUTS
from renderer import render_any, model_names, is_studio, LIVRE
from editor import slide_editor
from export import to_pdf, to_zip

st.set_page_config("DBB · Content Studio", "✦", layout="wide")
ui.inject()
S = st.session_state
for k, v in dict(plan=None, cur=0, ver=0, mode="", msg="").items():
    S.setdefault(k, v)

_modo = st.sidebar.radio("Modo", ["Plano de 10 dias", "Post avulso"], key="modo")
if _modo == "Plano de 10 dias":
    from planner_ui import run_planner
    run_planner()
    st.stop()

DEFAULT_MODEL = "Studio · Vinho DBB"
with st.sidebar:
    ui.brand("Post avulso")
    st.markdown("### ⚙️ Configuração")
    kind = st.radio("Tipo", ["Post único", "Carrossel"], horizontal=True)
    n = 1 if kind == "Post único" else st.slider("Slides", 2, 10, 6)
    fmt = st.selectbox("Formato", list(FORMATS))
    names = model_names()
    modelo = st.selectbox("Modelo visual", names, index=names.index(DEFAULT_MODEL) if DEFAULT_MODEL in names else 0)
    livre = modelo == LIVRE
    layout = st.selectbox("Layout", list(LAYOUTS), disabled=not livre)
    theme = st.selectbox("Tema", list(THEMES), disabled=not livre)
    show_ind = st.toggle("Indicador de carrossel (seta e pontos)", True)
    brand = st.text_input("Marca / @usuário", "")
    logo = st.file_uploader("Logo ou foto de perfil (opcional)", ["png", "jpg", "jpeg", "webp"])
    use_ai = ui.gemini_panel()
    dev = st.toggle("Modo desenvolvedor", False)

ui.nav("Post avulso")
ui.hero("TEXTO BRUTO → CARROSSEL", 'Do texto à arte, <span class="grad">pronto para publicar</span>.',
        "Cole o texto e envie suas imagens: a IA organiza os slides, o motor de design desenha e você baixa em PDF ou PNG.")
_cur = 3 if S.plan else (1 if st.session_state.get("txt_main", "").strip() else 0)
_names = ["Conteúdo", "Geração", "Preview", "Exportação"]
_h = ""
for _n, _t in enumerate(_names):
    _st = "active" if _n == _cur else ("done" if _n < _cur else "todo")
    _h += f'<div class="step {_st}"><div class="dot">{"✓" if _st == "done" else _n + 1}</div><div class="lbl">{_t}</div></div>'
    if _n < 3:
        _h += f'<div class="line {"full" if _n < _cur else ""}"></div>'
st.markdown(f'<div class="stepper">{_h}</div>', unsafe_allow_html=True)

ui.head("ETAPA 1", "Conteúdo", "Cole o texto e envie imagens opcionais. O sistema decide estrutura, hierarquia e composição.")
txt = st.text_area("Conteúdo", height=220, placeholder="Digite ou cole o conteúdo da publicação...", label_visibility="collapsed", key="txt_main")
st.caption(f"{len(txt)} caracteres · ~{len(txt.split())} palavras")
files = st.file_uploader("Imagens (opcional)", ["png", "jpg", "jpeg", "webp"], accept_multiple_files=True)
imgs = [f.getvalue() for f in files]


def gen():
    if not txt.strip():
        st.warning("Cole um texto para começar."); return
    try:
        with st.spinner("Planejando a publicação..."):
            S.plan, S.mode, S.msg = make_plan(txt, n, fmt, len(imgs), use_ai)
            S.cur, S.ver = 0, S.ver + 1
    except Exception as e:
        st.error("Não foi possível gerar o planejamento. Verifique sua chave Gemini e tente novamente.")
        if dev:
            st.exception(e)


b1, b2, _ = st.columns([2, 1.2, 4])
if b1.button("✦ ORGANIZAR E GERAR", type="primary", width="stretch"):
    gen()
    if S.plan:
        st.toast("Publicação planejada!", icon="✨")
if S.plan and b2.button("↻ REGENERAR", width="stretch"):
    gen()

if S.plan:
    if S.mode == "demo":
        st.markdown('<span class="badge">Modo local (sem IA)</span>', unsafe_allow_html=True)
    if S.msg:
        st.warning(S.msg)
    sl = S.plan.slides
    if len(sl) != n:
        st.info("O número de slides mudou: clique em REGENERAR para redistribuir o conteúdo.")
    S.cur = min(S.cur, len(sl) - 1)
    ui.head("ETAPA 2", "Preview e edição", "Edite texto, ícones, imagem e layout: tudo recompõe localmente, sem nova chamada à IA.")
    left, right = st.columns([3, 2])
    with right:  # edição manual: re-renderiza localmente, sem chamar o Gemini
        slide_editor(sl[S.cur], f"s{S.cur}_{S.ver}_", len(imgs), is_studio(modelo))
    ims, warns = render_any(sl, fmt, modelo, brand, theme or "Obsidiana", layout or "Editorial", show_ind, imgs, logo.getvalue() if logo else None)
    with left:
        with st.container(key="stage"):
            st.markdown(f'<div class="slide-count">SLIDE {S.cur + 1} / {len(ims)}</div>', unsafe_allow_html=True)
            st.image(ims[S.cur], width="stretch")
    for w in dict.fromkeys(warns):
        st.warning(w)
    cols = st.columns(len(ims))
    for k, cc in enumerate(cols):
        with cc.container(key=f"thumb_{'on' if k == S.cur else 'off'}_{k}"):
            st.image(ims[k], width="stretch")
            if st.button(f"{k + 1:02d}", key=f"t{k}", width="stretch"):
                S.cur = k; st.rerun()
    ui.head("ETAPA 3", "Exportação", "PDF full-bleed no tamanho exato do formato, ou PNGs em ZIP.")
    e1, e2, _ = st.columns([2, 2, 4])
    name = "instagram_post" if len(ims) == 1 else "instagram_carousel"
    e1.download_button("⬇ BAIXAR PDF", to_pdf(ims), f"{name}.pdf", "application/pdf", width="stretch")
    e2.download_button("⬇ BAIXAR IMAGENS (ZIP)", to_zip(ims), f"{name}.zip", "application/zip", width="stretch")
