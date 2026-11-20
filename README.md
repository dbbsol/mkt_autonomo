# DBB · Content Studio (mkt autônomo)

Streamlit app com a identidade visual da DBB. Dois modos (barra lateral):

- **Plano de 10 dias**: briefing → estratégia → calendário de 10 dias (1 carrossel por dia) → design dos slides → PDF/PNG/ZIP.
- **Post avulso**: cole um texto e gere post ou carrossel.

## Rodar
    pip install -r requirements.txt
    streamlit run app.py        (ou iniciar.bat no Windows)

## Gemini (IA)
Qualquer um destes serve (nesta ordem de prioridade):
1. Campo "Chave do Gemini" na barra lateral (vale só na sessão)
2. `config.py` → `GEMINI_API_KEY = "..."`
3. Arquivo `.env` → `GEMINI_API_KEY=...` (copie `.env.example`)
4. Streamlit Cloud → Settings → Secrets → `GEMINI_API_KEY = "..."`

Botão **Testar Gemini** na barra lateral mostra o erro real. Rode também `python diagnostico_gemini.py`.
Modelos: pode listar **vários**, em ordem de preferência; se o 1º falhar, tenta o próximo.
- `.env`: `GEMINI_MODELS=gemini-3.6-flash,gemini-3.5-flash,gemini-3.5-flash-lite` (tem prioridade)
- `config.py`: `GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", ...]`
Depois dos que você listou, o app ainda tenta os que a sua chave aceita e uma lista padrão. Se deixar vazio, tudo é automático.
Sem chave, tudo funciona no modo local (textos simples, sem IA).

## Design
Modelos "Studio ·" (Vinho DBB, Rosé Creme, Noir Dourado, Terra Editorial): celular 3D na capa, selos 3D, pincel no destaque,
linha do tempo, ícones, fotos em arco/tela cheia, cabeçalho com contador e balanceamento vertical automático.
Envie imagens por carrossel e escolha ícones/layout slide a slide no editor.

## Testes
    pip install pytest && python -m pytest -q tests
