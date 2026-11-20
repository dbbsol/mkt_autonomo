"""Camada única de acesso ao Gemini: acha a chave, escolhe um modelo que existe, tenta de novo quando a API oscila
e devolve erros em português dizendo o que fazer. Nunca imprime a chave."""
import os, re, json, time

PREFERRED = ["gemini-3.6-flash", "gemini-3.5-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite",
             "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.5-flash-lite", "gemini-2.0-flash"]
PLACEHOLDERS = {"", "sua_chave", "sua_chave_aqui", "COLE_AQUI", "xxx", "x"}


class GeminiError(Exception):
    """Erro já com mensagem amigável."""


def get_key():
    cands = []
    try:  # chave colada na barra lateral do app (vale só nesta sessão)
        import streamlit as st
        cands.append(st.session_state.get("gemini_key_input", ""))
    except Exception:
        pass
    try:
        import config
        cands.append(getattr(config, "GEMINI_API_KEY", ""))
    except Exception:
        pass
    cands += [os.environ.get("GEMINI_API_KEY", ""), os.environ.get("GOOGLE_API_KEY", "")]
    try:  # Streamlit Cloud (secrets)
        import streamlit as st
        for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY"):
            cands.append(st.secrets.get(name, ""))
    except Exception:
        pass
    for k in cands:
        k = (k or "").strip().strip("\"'").strip()
        if k and k not in PLACEHOLDERS:
            return k
    return ""


def has_key(): return bool(get_key())


def key_source():
    k = get_key()
    if not k: return ""
    try:
        import streamlit as st
        if (st.session_state.get("gemini_key_input", "") or "").strip().strip("\"'") == k: return "campo da barra lateral"
    except Exception:
        pass
    try:
        import config
        if (getattr(config, "GEMINI_API_KEY", "") or "").strip().strip("\"'") == k: return "config.py"
    except Exception:
        pass
    if k in (os.environ.get("GEMINI_API_KEY", "").strip().strip("\"'"), os.environ.get("GOOGLE_API_KEY", "").strip().strip("\"'")): return ".env / variável de ambiente"
    return "st.secrets"


def clean(e):
    m = f"{type(e).__name__}: {e}"; k = get_key()
    return (m.replace(k, "***") if k else m)[:400]


def _client():
    key = get_key()
    if not key:
        raise GeminiError("Chave do Gemini não encontrada. Cole a chave no campo da barra lateral, no arquivo .env (GEMINI_API_KEY=...) ou em Secrets do Streamlit Cloud.")
    try:
        from google import genai
    except ImportError:
        raise GeminiError("Biblioteca do Gemini não instalada. Rode: pip install -U google-genai")
    return genai.Client(api_key=key)


_MODELS = {}


def discover(cl):
    """Modelos 'flash' que aceitam generateContent nesta chave (cache por sessão)."""
    if "v" in _MODELS: return _MODELS["v"]
    out = []
    try:
        for m in cl.models.list():
            acts = getattr(m, "supported_actions", None) or getattr(m, "supported_generation_methods", None) or []
            n = (getattr(m, "name", "") or "").replace("models/", "")
            if "generateContent" in acts and "flash" in n and not re.search(r"image|tts|live|embed|audio|thinking|exp|vision|robotics|computer", n):
                out.append(n)
    except Exception:
        pass
    out.sort(key=lambda n: ("lite" in n, "preview" in n, [-int(x) for x in re.findall(r"\d+", n)][:2]))
    _MODELS["v"] = out
    return out


def _split(v):
    """Aceita lista/tupla ou texto separado por vírgula, ponto e vírgula ou quebra de linha."""
    if isinstance(v, (list, tuple, set)): items = v
    else: items = re.split(r"[,;\n]+", v or "")
    return [str(m).strip().strip("\"'").replace("models/", "") for m in items if str(m).strip().strip("\"'")]


def candidates(cl=None):
    """Ordem de tentativa: modelos que VOCÊ listou (.env, depois config.py, na ordem escrita) -> descobertos na chave -> padrão."""
    listed = _split(os.getenv("GEMINI_MODELS", "")) + _split(os.getenv("GEMINI_MODEL", ""))   # .env tem prioridade
    try:
        import config
        listed += _split(getattr(config, "GEMINI_MODELS", "")) + _split(getattr(config, "GEMINI_MODEL", ""))
    except Exception:
        pass
    rest = (discover(cl) if cl else []) + PREFERRED
    return list(dict.fromkeys(listed + rest))


def _accepts_temperature(model):
    """Gemini 3.5+ (ex.: 3.6-flash, 3.5-flash-lite) recusa temperature/top_p/top_k; versões antigas aceitam."""
    m = re.search(r"gemini-(\d+)(?:\.(\d+))?", model)
    if not m: return False   # aliases (gemini-flash-latest): na dúvida, não envia temperature
    ver = (int(m.group(1)), int(m.group(2) or 0))
    return ver < (3, 5)


def _json(raw):
    raw = (raw or "").strip()
    raw = re.sub(r"^```(?:json)?|```$", "", raw, flags=re.M).strip()
    a, b = raw.find("{"), raw.rfind("}")
    if a < 0 or b < a: raise ValueError("A resposta não veio em JSON.")
    return json.loads(raw[a:b + 1])


def _explain(e):
    s = str(e); u = s.upper()
    if any(x in u for x in ("API_KEY_INVALID", "API KEY NOT VALID", "API KEY EXPIRED", "UNAUTHENTICATED", "PERMISSION_DENIED", "403", "401")):
        return "A chave do Gemini foi recusada (inválida, expirada, sem permissão ou restrita). Gere outra em https://aistudio.google.com/apikey e cole no campo da barra lateral ou no .env."
    if "RESOURCE_EXHAUSTED" in u or "429" in u or "QUOTA" in u:
        return "Limite/cota do Gemini atingido. Espere um minuto ou ative o faturamento no Google AI Studio."
    if "FAILED_PRECONDITION" in u and "LOCATION" in u:
        return "O Gemini não está liberado na sua região para esta chave."
    if any(x in u for x in ("CONNECT", "TIMEOUT", "TIMED OUT", "NAME RESOLUTION", "SSL", "PROXY")):
        return "Sem conexão com a API do Gemini (internet, proxy ou antivírus bloqueando)."
    return clean(e)


def generate_json(prompt, retries=2):
    """Chama o Gemini pedindo JSON. Tenta os modelos disponíveis; repete em erro temporário; falha com GeminiError claro."""
    cl = _client(); last = None; tried = []
    for model in candidates(cl):
        for att in range(retries + 1):
            try:
                cfg = {"response_mime_type": "application/json"}
                if _accepts_temperature(model): cfg["temperature"] = 0.7
                r = cl.models.generate_content(model=model, contents=prompt, config=cfg)
                return _json(getattr(r, "text", "") or "")
            except GeminiError:
                raise
            except Exception as e:
                last = e; u = str(e).upper(); tried.append(model)
                if any(x in u for x in ("API_KEY_INVALID", "API KEY NOT VALID", "API KEY EXPIRED", "UNAUTHENTICATED", "PERMISSION_DENIED")):
                    raise GeminiError(_explain(e))
                if any(x in u for x in ("503", "UNAVAILABLE", "OVERLOADED", "500", "INTERNAL", "DEADLINE")) and att < retries:
                    time.sleep(1.5 * (att + 1)); continue
                if ("429" in u or "RESOURCE_EXHAUSTED" in u) and att < retries:
                    time.sleep(3 * (att + 1)); continue
                if isinstance(e, ValueError) and att < retries:   # JSON ruim: repete
                    continue
                break   # 404/modelo aposentado/etc.: próximo modelo
    raise GeminiError(f"{_explain(last)} (modelos tentados: {', '.join(dict.fromkeys(tried)) or 'nenhum'})")


def test_connection():
    """Retorna (ok, mensagem) para o botão 'Testar Gemini' e para o diagnóstico."""
    try:
        d = generate_json('Responda somente este JSON: {"ok": true}')
        return bool(d.get("ok", True)), "Gemini respondeu corretamente."
    except GeminiError as e:
        return False, str(e)
    except Exception as e:
        return False, clean(e)
