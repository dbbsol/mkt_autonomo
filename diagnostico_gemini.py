"""Rode:  python diagnostico_gemini.py   -> mostra onde está o problema do Gemini (chave, biblioteca, modelos, rede)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from dotenv import load_dotenv; load_dotenv()
except Exception:
    pass
import gemini

print("1) Chave:", ("encontrada em " + gemini.key_source()) if gemini.has_key() else "NÃO encontrada -> cole em config.py (GEMINI_API_KEY)")
try:
    import google.genai as g; print("2) Biblioteca google-genai:", getattr(g, "__version__", "instalada"))
except ImportError:
    print("2) Biblioteca google-genai: NÃO instalada -> pip install -U google-genai"); sys.exit(1)
if not gemini.has_key(): sys.exit(1)
try:
    cl = gemini._client(); print("3) Modelos disponíveis p/ sua chave:", ", ".join(gemini.discover(cl)) or "(não consegui listar)")
except Exception as e:
    print("3) Falha ao listar modelos:", gemini.clean(e))
ok, msg = gemini.test_connection(); print("4) Teste de geração:", "OK" if ok else "FALHOU", "-", msg)
