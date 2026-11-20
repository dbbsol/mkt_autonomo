"""Interface minimalista na paleta da DBB (CSS em assets/style.css)."""
from pathlib import Path
import streamlit as st


def inject():
    st.markdown(f"<style>{(Path(__file__).parent / 'assets' / 'style.css').read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def title(text, sub=""):
    st.markdown(f'<div class="ttl"><h1>{text}</h1>{f"<p>{sub}</p>" if sub else ""}</div>', unsafe_allow_html=True)


def gemini_panel():
    """Barra lateral: chave do Gemini (só nesta sessão), status e teste. Retorna True se há chave (a IA é usada automaticamente)."""
    import gemini
    st.markdown('<div class="side-title">GEMINI</div>', unsafe_allow_html=True)
    st.text_input("Chave", type="password", key="gemini_key_input", placeholder="Cole a chave (opcional)", label_visibility="collapsed",
                  help="Gere em https://aistudio.google.com/apikey. Para não colar toda vez: arquivo .env (GEMINI_API_KEY=...) ou Secrets do Streamlit Cloud.")
    ok = gemini.has_key()
    st.markdown(f'<div class="status {"ok" if ok else "off"}"><i></i>{("IA ativa · " + gemini.key_source()) if ok else "Sem chave: modo local"}</div>', unsafe_allow_html=True)
    if ok and st.button("Testar conexão", width="stretch", key="btn_test_gemini"):
        with st.spinner("Testando..."):
            good, msg = gemini.test_connection()
        (st.success if good else st.error)(msg)
    return ok
