# DBB · Plano de 10 dias

Um único fluxo: **Cliente → Plano (estratégia + calendário) → 10 carrosséis**, sempre no visual **LC Digital** (creme/rosé, título condensado com palavra-herói rosa e pincel, celular 3D, selos, logo LC).
Não existe mais post avulso nem outros modelos visuais.

## Rodar
    pip install -r requirements.txt
    streamlit run app.py        (ou iniciar.bat no Windows)

## Gemini (IA)
Cole a chave em UM destes lugares:
1. Campo "GEMINI" na barra lateral do app (só vale na sessão)
2. `.env` (copie `.env.example`): `GEMINI_API_KEY=...`
3. `config.py`: `GEMINI_API_KEY = "..."`
4. Streamlit Cloud → Settings → Secrets: `GEMINI_API_KEY = "..."`

Vários modelos (se o 1º falhar, tenta o 2º...): `GEMINI_MODELS=modelo1,modelo2,modelo3` no `.env`, ou `GEMINI_MODELS = [...]` no `config.py`.
Sem chave, o plano e os textos saem no modo local (mais simples). Botão "Testar conexão" mostra o erro real.

## Testes
    python -m pytest -q tests
