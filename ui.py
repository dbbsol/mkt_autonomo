"""Peças de interface na identidade visual da DBB (CSS em assets/style.css)."""
from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

_GLOW = """<script>try{const p=window.parent.document;if(!p.getElementById('cg')){
const o=p.createElement('div');o.className='dbb-orbs';o.innerHTML='<i></i><i></i><i></i>';p.body.appendChild(o);
const d=p.createElement('div');d.id='cg';d.className='cursor-glow';p.body.appendChild(d);
p.addEventListener('pointermove',e=>{d.style.transform='translate('+e.clientX+'px,'+e.clientY+'px)';d.classList.add('on')},{passive:true});}}catch(e){}</script>"""


def inject():
    css = (Path(__file__).parent / "assets" / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
    components.html(_GLOW, height=0)


def nav(right="Content Studio"):
    st.markdown(f'<div class="dbb-nav"><div class="dbb-logo"><i></i>DBB Soluções Empresariais</div><span class="dbb-pill">{right}</span></div>', unsafe_allow_html=True)


def brand(sub):
    st.markdown(f'<div class="brand"><div class="brand-mark">✦</div><div><div class="brand-name">DBB · Content Studio</div><div class="brand-sub">{sub}</div></div></div>', unsafe_allow_html=True)


def hero(chip, title_html, desc):
    st.markdown(f'<div class="hero"><span class="chip"><span class="pulse"></span>{chip}</span><h1>{title_html}</h1><p>{desc}</p></div>', unsafe_allow_html=True)


def head(e, t, d):
    st.markdown(f'<div class="page-head"><div class="page-eyebrow">{e}</div><h3>{t}</h3><p>{d}</p></div>', unsafe_allow_html=True)


def gemini_status(ok, src=""):
    st.markdown(f'<div class="status {"ok" if ok else "off"}"><i></i>{("Gemini ativo · " + src) if ok else "Gemini sem chave (modo local)"}</div>', unsafe_allow_html=True)


def gemini_panel():
    """Bloco da barra lateral: campo da chave, status, teste de conexão e chave liga/desliga. Retorna True se a IA deve ser usada."""
    import gemini
    st.markdown('<div class="side-title">INTELIGÊNCIA ARTIFICIAL</div>', unsafe_allow_html=True)
    st.text_input("Chave do Gemini (vale só nesta sessão)", type="password", key="gemini_key_input", placeholder="Cole a chave aqui",
                  help="Gere em https://aistudio.google.com/apikey. Para não colar toda vez: arquivo .env (GEMINI_API_KEY=...) ou Secrets do Streamlit Cloud.")
    ok = gemini.has_key()
    gemini_status(ok, gemini.key_source())
    if ok and st.button("Testar Gemini", width="stretch", key="btn_test_gemini"):
        with st.spinner("Testando..."):
            good, msg = gemini.test_connection()
        (st.success if good else st.error)(msg)
    use = st.toggle("Usar Gemini (textos e estratégia)", True, disabled=not ok, key="use_ai_toggle")
    return bool(ok and use)
