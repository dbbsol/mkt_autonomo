"""Interface minimalista na paleta da DBB (CSS em assets/style.css)."""
from pathlib import Path
import streamlit as st


_JS = """<script>
try{const d=window.parent.document;
if(!d.getElementById('bar')){
 const b=d.createElement('div');b.id='bar';d.body.appendChild(b);
 const g=d.createElement('div');g.className='cursor-glow';d.body.appendChild(g);
 const m=d.querySelector('[data-testid=stMain]')||d.documentElement;
 m.addEventListener('scroll',()=>{b.style.width=(m.scrollTop/Math.max(1,m.scrollHeight-m.clientHeight)*100)+'%'},{passive:true});
 if(window.parent.matchMedia('(pointer:fine)').matches)d.addEventListener('pointermove',e=>{g.style.transform='translate('+e.clientX+'px,'+e.clientY+'px)';g.classList.add('on')},{passive:true});
}}catch(e){}
</script>"""


def inject():
    """Identidade DBB: CSS + aurora/grade/grão de fundo + barra de progresso e luz do cursor."""
    st.markdown(f"<style>{(Path(__file__).parent / 'assets' / 'style.css').read_text(encoding='utf-8')}</style>"
                '<div class="bg"><div class="orb a"></div><div class="orb b"></div><div class="orb c"></div></div><div class="grain"></div>',
                unsafe_allow_html=True)
    try:
        import streamlit.components.v1 as components
        components.html(_JS, height=0)
    except Exception:
        pass


def title(text, sub=""):
    """Título no padrão da landing: chip + h1 com a última palavra em gradiente."""
    w = text.rsplit(" ", 1); text = f'{w[0]} <span class="grad">{w[1]}</span>' if len(w) == 2 else text
    st.markdown(f'<div class="ttl"><span class="chip"><span class="pulse"></span>DBB · automação e IA</span><h1>{text}</h1>{f"<p>{sub}</p>" if sub else ""}</div>', unsafe_allow_html=True)


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
