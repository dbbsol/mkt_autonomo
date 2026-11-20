"""Testa a camada do Gemini com um cliente falso (sem rede): modelos, repetição, erros em português, JSON dentro de ```."""
import sys, os, types
import pytest
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import gemini
import strategy as ST
from ai import gemini_plan, make_plan


class Resp:
    def __init__(self, t): self.text = t


def install(monkeypatch, handler, models=("models/gemini-2.5-flash", "models/gemini-2.5-flash-image")):
    calls = []

    class M:
        @staticmethod
        def generate_content(model, contents, config=None):
            calls.append(model); return handler(model, contents, config)

        @staticmethod
        def list():
            return [types.SimpleNamespace(name=n, supported_actions=["generateContent"]) for n in models]

    class C:
        def __init__(self, api_key=None): self.models = M()
    g = types.ModuleType("google"); ge = types.ModuleType("google.genai"); ge.Client = C; g.genai = ge
    monkeypatch.setitem(sys.modules, "google", g); monkeypatch.setitem(sys.modules, "google.genai", ge)
    import config
    monkeypatch.setattr(config, "GEMINI_MODELS", []); monkeypatch.setattr(config, "GEMINI_MODEL", "")
    monkeypatch.delenv("GEMINI_MODELS", raising=False); monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setenv("GEMINI_API_KEY", "chave-de-teste-123"); monkeypatch.setattr(gemini, "_MODELS", {}); monkeypatch.setattr(gemini.time, "sleep", lambda s: None)
    return calls


def test_key_lookup(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False); monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert gemini.get_key() == "" and not gemini.has_key()
    monkeypatch.setenv("GEMINI_API_KEY", '  "abc123"  '); assert gemini.get_key() == "abc123" and gemini.key_source().startswith(".env")
    monkeypatch.setenv("GEMINI_API_KEY", "sua_chave"); assert gemini.get_key() == ""
    monkeypatch.delenv("GEMINI_API_KEY"); monkeypatch.setenv("GOOGLE_API_KEY", "zzz"); assert gemini.get_key() == "zzz"


def test_json_in_fence_and_nulls(monkeypatch):
    install(monkeypatch, lambda m, c, cf: Resp('```json\n{"slides":[{"layout":"capa","headline":"Oi","highlight":null,"icon":"rocket","items":null,"image":null}]}\n```'))
    p = gemini_plan("texto", 1, "Instagram 4:5", 0)
    assert p.slides[0].headline == "Oi" and p.slides[0].icon == "rocket" and p.slides[0].layout == "capa" and p.slides[0].items == []


def test_falls_to_next_model_on_404(monkeypatch):
    def h(m, c, cf):
        if m == "gemini-2.5-flash": raise Exception("404 NOT_FOUND: model is no longer available")
        return Resp('{"ok": true}')
    calls = install(monkeypatch, h, models=("models/gemini-3-flash",))
    assert gemini.generate_json("x") == {"ok": True}
    assert calls[0] == "gemini-3-flash" or "gemini-3-flash" in calls   # modelo descoberto na chave é tentado


def test_retries_on_overload(monkeypatch):
    n = {"i": 0}
    def h(m, c, cf):
        n["i"] += 1
        if n["i"] < 3: raise Exception("503 UNAVAILABLE: overloaded")
        return Resp('{"ok": 1}')
    install(monkeypatch, h); assert gemini.generate_json("x") == {"ok": 1} and n["i"] == 3


def test_bad_key_message(monkeypatch):
    install(monkeypatch, lambda m, c, cf: (_ for _ in ()).throw(Exception("400 INVALID_ARGUMENT. API key not valid. reason: API_KEY_INVALID")))
    with pytest.raises(gemini.GeminiError) as e: gemini.generate_json("x")
    assert "recusada" in str(e.value) and "chave-de-teste-123" not in str(e.value)
    ok, msg = gemini.test_connection(); assert not ok and "recusada" in msg


def test_quota_message(monkeypatch):
    install(monkeypatch, lambda m, c, cf: (_ for _ in ()).throw(Exception("429 RESOURCE_EXHAUSTED quota")))
    with pytest.raises(gemini.GeminiError) as e: gemini.generate_json("x")
    assert "cota" in str(e.value).lower()


def test_make_plan_falls_back_to_local(monkeypatch):
    install(monkeypatch, lambda m, c, cf: (_ for _ in ()).throw(Exception("API_KEY_INVALID")))
    p, modo, aviso = make_plan("Frase um. Frase dois. Frase três.", 3, "Instagram 4:5", 0, True)
    assert modo == "demo" and len(p.slides) == 3 and "Gemini falhou" in aviso
    monkeypatch.delenv("GEMINI_API_KEY"); p, modo, aviso = make_plan("a. b. c.", 2, "Instagram 4:5", 0, True)
    assert modo == "demo" and "Sem chave" in aviso


def test_strategy_build_ai_normalizes(monkeypatch):
    j = '{"diagnostico":"ok","pilares":[],"pecas":[{"n":1,"dia":40,"formato":"post","pilar":"Educação","funil":"topo","tema":"t","gancho":"g","cta":"c"}]}'
    install(monkeypatch, lambda m, c, cf: Resp(j))
    B = dict(ST.DEF); B.update(cliente="X", nicho_final="Y", inicio="2026-11-02")
    S = ST.build_ai(B)
    assert len(S.pecas) == 10 and [p.dia for p in S.pecas] == list(range(1, 11)) and all(p.formato == "Carrossel" and p.funil in ST.FUN for p in S.pecas)


def test_write_cards_stops_ai_after_first_failure(monkeypatch):
    calls = install(monkeypatch, lambda m, c, cf: (_ for _ in ()).throw(Exception("API_KEY_INVALID")))
    B = dict(ST.DEF); B.update(cliente="X", nicho_final="Y", inicio="2026-11-02"); S = ST.build_local(B)
    for p in S.pecas: p.slides = []
    w = ST.write_cards(S, B, True, only_missing=False)
    assert len(w) == 1 and all(len(p.slides) == 6 for p in S.pecas) and len(calls) <= 2


def test_multiple_models_in_order(monkeypatch):
    """Vários modelos listados (vírgula no .env): tenta na ordem escrita; 3.5+ não recebe temperature."""
    seen = []
    def h(m, c, cf):
        seen.append((m, dict(cf or {})))
        if m == "gemini-3.9-flash": raise Exception("404 NOT_FOUND")
        return Resp('{"ok": true}')
    install(monkeypatch, h)
    monkeypatch.setenv("GEMINI_MODELS", "gemini-3.9-flash, models/gemini-3.6-flash ,gemini-3.5-flash")
    assert gemini.candidates()[:3] == ["gemini-3.9-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
    assert gemini.generate_json("x") == {"ok": True}
    assert [m for m, _ in seen] == ["gemini-3.9-flash", "gemini-3.6-flash"]
    assert all("temperature" not in cf for _, cf in seen)


def test_temperature_only_on_old_models():
    assert gemini._accepts_temperature("gemini-2.5-flash") and gemini._accepts_temperature("gemini-3.1-flash-lite")
    assert not gemini._accepts_temperature("gemini-3.5-flash") and not gemini._accepts_temperature("gemini-3.6-flash")
    assert not gemini._accepts_temperature("gemini-flash-latest")
