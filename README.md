# MKT Autônomo (Instagram Content Studio)

Dois modos, no seletor **Modo** da barra lateral:
- **Post avulso:** texto bruto -> posts/carrosséis em PDF, PNG e ZIP, com modelos prontos (DBB, Legado Capital, Glau Personal, Rosé Gestão) e layouts livres.
- **Plano de 30 dias:** briefing do cliente e do público -> linha editorial (15 peças) -> calendário -> cards no modelo do cliente -> PDF e pacote ZIP.

## Início rápido (Windows)
Dê dois cliques em `iniciar.bat` (cria o ambiente, instala e abre o app em http://localhost:8501).
Ou, no terminal do VS Code:

    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    python -m streamlit run app.py

## Gemini (opcional)
Abra o `.env` e preencha `GEMINI_API_KEY=sua_chave` (https://aistudio.google.com/apikey). Sem a chave tudo funciona em modo local.
No Streamlit Cloud: Settings -> Secrets -> `GEMINI_API_KEY = "sua_chave"`.

## Estrutura
app.py · planner_ui.py (plano 30 dias) · strategy.py (metodologia) · report.py (PDF da linha editorial) · ai.py · engine.py (layouts livres) ·
template_engine.py (modelo DBB) · dsl.py (motor dos demais modelos) · templates/ (um arquivo por cliente) · carousel_icon.py (pontos e seta) · export.py · assets/ (css e fontes OFL).

Novo cliente/modelo: copie um arquivo de `templates/`, ajuste cores, fontes e posições; ele aparece no seletor.
Testes: `python -m pytest -q`.
