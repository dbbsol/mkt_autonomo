"""Formatos, temas e chave do Gemini.
A chave também pode vir do campo da barra lateral, do arquivo .env (GEMINI_API_KEY=...) ou de Secrets do Streamlit Cloud.
Se preferir fixar aqui, cole entre as aspas (e NÃO publique este arquivo no GitHub com a chave dentro)."""
GEMINI_API_KEY = ""
# Modelos (opcional). Pode colocar VÁRIOS, em ordem de preferência: se o 1º falhar/estiver fora do ar, tenta o 2º, e assim por diante.
# Vazio = escolhe sozinho os que sua chave aceita (do mais novo ao mais antigo).
GEMINI_MODELS = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite"]
GEMINI_MODEL = ""   # (antigo, ainda funciona) um modelo só. Aceita também vários separados por vírgula.

FORMATS = {
    "Instagram 4:5": dict(w=1080, h=1350, margin=90, top=0),
    "Instagram 1:1": dict(w=1080, h=1080, margin=80, top=0),
    "Story/Reels 9:16": dict(w=1080, h=1920, margin=100, top=150),
}
THEMES = {
    "Obsidiana": dict(bg="#0B0B10", fg="#F4F1EA", accent="#C8A96A", muted="#8A8794", primary="#1A1A24"),
    "Marfim": dict(bg="#F4F1EA", fg="#15141A", accent="#B4452F", muted="#6E6A63", primary="#E6E1D6"),
    "Neon": dict(bg="#07070D", fg="#FFFFFF", accent="#B6FF3B", muted="#9A9AB0", primary="#16162C"),
    "Oceano": dict(bg="#0A1F2E", fg="#EAF6F6", accent="#4FD1C5", muted="#7FA3B0", primary="#10304A"),
}
