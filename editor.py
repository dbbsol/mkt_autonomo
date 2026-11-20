"""Editor de um slide (texto, ícone, imagem, layout, itens com ícone). Usado no Post avulso e no Plano de 10 dias."""
import streamlit as st
import icons as IC
from ai import Item
from studio import LAYOUTS_STUDIO

ICON_OPTS = [""] + list(IC.ICONS)
ICON_FMT = lambda k: "Automático" if k == "" else IC.ICON_LABELS.get(k, k)


@st.cache_resource(show_spinner=False)
def icon_sheet():
    return IC.contact_sheet(cols=6, cell=150, fg=(255, 61, 90, 255), fg2=(242, 201, 107, 255), bg=(20, 12, 24), label_fg=(236, 231, 241))


def slide_editor(s, kp, n_imgs, studio=True):
    if studio:
        keys = list(LAYOUTS_STUDIO); cur = s.layout if s.layout in LAYOUTS_STUDIO else "auto"
        pick = st.selectbox("Layout do slide", keys, index=keys.index(cur), format_func=lambda k: LAYOUTS_STUDIO[k], key=kp + "lay")
        s.layout = "" if pick == "auto" else pick
    s.headline = st.text_input("Título (headline)", s.headline, key=kp + "h")
    s.highlight = st.text_input("Palavra de destaque (pincel)", s.highlight, key=kp + "x", help="Uma palavra do título; ganha o pincel colorido.")
    s.subhead = st.text_area("Subtítulo", s.subhead, key=kp + "s", height=80)
    s.body = st.text_area("Texto (use **negrito** para destacar)", s.body, key=kp + "b", height=110)
    a, b = st.columns(2)
    s.cta = a.text_input("CTA (botão)", s.cta, key=kp + "c")
    s.label = b.text_input("Etiqueta", s.label, key=kp + "l")
    if studio:
        s.icon = st.selectbox("Ícone do slide", ICON_OPTS, index=ICON_OPTS.index(s.icon) if s.icon in ICON_OPTS else 0, format_func=ICON_FMT, key=kp + "ic")
    opts = ["Sem imagem"] + [f"Imagem {j + 1}" for j in range(n_imgs)]
    cur_i = s.image + 1 if s.image is not None and s.image < n_imgs else 0
    pick = st.selectbox("Imagem do slide (envie em 'Imagens')", opts, index=cur_i, key=kp + "im")
    s.image = None if pick == "Sem imagem" else opts.index(pick) - 1
    if studio:
        with st.expander("Itens com ícone (lista / ícones em linha)", expanded=bool(s.items)):
            old = list(s.items) + [Item()] * (4 - len(s.items)); new = []
            for j in range(4):
                it = old[j]; c1, c2, c3 = st.columns([1.2, 1.3, 2.4])
                ic = c1.selectbox(f"Ícone {j + 1}", ICON_OPTS, index=ICON_OPTS.index(it.icon) if it.icon in ICON_OPTS else 0, format_func=ICON_FMT, key=f"{kp}ii{j}")
                lb = c2.text_input(f"Título {j + 1}", it.label, key=f"{kp}il{j}"); tx = c3.text_input(f"Texto {j + 1}", it.text, key=f"{kp}it{j}")
                if lb.strip() or tx.strip(): new.append(Item(icon=ic, label=lb, text=tx))
            s.items = new
        with st.expander("Galeria de ícones"):
            st.image(icon_sheet(), width="stretch")
