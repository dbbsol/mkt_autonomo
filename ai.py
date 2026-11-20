"""Schemas (Pydantic), prompt, Gemini e planejador local (modo demo).
Toda chamada ao Gemini passa por gemini.py (acha a chave, escolhe o modelo, repete em erro temporário)."""
import re
from typing import Optional
from pydantic import BaseModel, field_validator
import gemini
import icons as IC

LAYOUT_KEYS = ["capa", "capa_foto", "texto", "lista", "icones", "passos", "foto", "citacao", "cta"]


class Item(BaseModel):
    icon: str = ""
    label: str = ""
    text: str = ""

    @field_validator("icon", "label", "text", mode="before")
    @classmethod
    def _txt(cls, v):
        return "" if v is None else str(v).strip()


class Slide(BaseModel):
    label: str = ""
    headline: str = ""
    subhead: str = ""
    body: str = ""
    cta: str = ""
    highlight: str = ""
    icon: str = ""
    layout: str = ""
    items: list[Item] = []
    image: Optional[int] = None

    @field_validator("label", "headline", "subhead", "body", "cta", "highlight", "icon", "layout", mode="before")
    @classmethod
    def _txt(cls, v):  # Gemini costuma devolver null nos campos vazios
        return "" if v is None else str(v).strip()

    @field_validator("items", mode="before")
    @classmethod
    def _items(cls, v):
        out = []
        for it in (v or []):
            if isinstance(it, str): out.append({"label": it})
            elif isinstance(it, dict): out.append(it)
            elif isinstance(it, Item): out.append(it.model_dump())
        return out

    @field_validator("image", mode="before")
    @classmethod
    def _img(cls, v):
        try:
            return None if v in (None, "", "null") else int(v)
        except (TypeError, ValueError):
            return None


class Plan(BaseModel):
    slides: list[Slide]


PROMPT = """Você é social media sênior, copywriter e diretor de arte de Instagram.
Transforme o TEXTO em um carrossel de EXATAMENTE {n} slide(s) ({fmt}), pronto para virar arte.

CONTEÚDO
- Preserve as ideias e os fatos do texto; NÃO invente fatos, números, preços, prazos ou depoimentos.
- Escreva em português do Brasil, frases curtas, uma ideia por slide, tom humano (nada de "descubra o segredo").
- headline: máx 9 palavras. subhead: frase de destaque, máx 22 palavras. body: máx 38 palavras; pode usar **negrito** em 1 ou 2 trechos.
- highlight: UMA palavra do headline que recebe o pincel colorido (a mais importante). Vazio se não houver.
- label: 1 ou 2 palavras em maiúsculas (ex.: "O PROBLEMA", "O CAMINHO"). Vazio no CTA se não precisar.

ESTRUTURA E LAYOUT (campo "layout", escolha um por slide e varie; nunca repita o mesmo layout em slides seguidos)
- slide 1: "capa" (gancho forte, headline curto, subhead de apoio){capa_foto}
- meio: "texto" (headline + subhead + body), "lista" (headline + 3 itens com ícone, cada item com label curto e text de 1 frase),
  "icones" (headline + 3 itens só com ícone e label de 1-2 palavras), "citacao" (frase de impacto no headline, sem body){foto}
- último (quando houver 3 ou mais slides): "cta" (headline de convite, subhead curto, cta = texto do botão com 2 a 5 palavras)

ÍCONES (campo "icon" do slide e de cada item): use SOMENTE estes nomes: {icones}.
Escolha o ícone pelo sentido do texto. Em "items", sempre 3 itens quando o layout for "lista" ou "icones"; nos demais layouts, items = [].
{imgs}
Responda SOMENTE JSON válido, neste formato:
{{"slides":[{{"layout":"capa","label":"","headline":"","highlight":"","subhead":"","body":"","cta":"","icon":"","items":[{{"icon":"","label":"","text":""}}],"image":null}}]}}

TEXTO:
{text}"""


def _prompt(text, n, fmt, k):
    if k:
        imgs = f'Há {k} imagem(ns) enviadas pelo cliente (índices 0 a {k - 1}). Use "image" (o índice) nos slides em que a foto fizer sentido; senão null.'
        capa_foto, foto = ' ou "capa_foto" (foto em tela cheia) se houver imagem', ' e "foto" (foto + texto) quando houver imagem'
    else:
        imgs, capa_foto, foto = 'Não há imagens: use sempre "image": null.', "", ""
    return PROMPT.format(n=n, fmt=fmt, text=text, icones=", ".join(IC.ICONS), imgs=imgs, capa_foto=capa_foto, foto=foto)


def fix_plan(p, n, k):
    """Normaliza a saída da IA: n slides, ícones/layouts válidos, no máximo 4 itens, imagem existente."""
    p.slides = (p.slides + [Slide() for _ in range(n)])[:n]
    for i, s in enumerate(p.slides):
        s.label = s.label or f"{i + 1:02d}"
        s.icon = s.icon if s.icon in IC.ICONS else ""
        s.layout = s.layout if s.layout in LAYOUT_KEYS else ""
        s.items = [Item(icon=it.icon if it.icon in IC.ICONS else "", label=it.label, text=it.text) for it in s.items if it.label or it.text][:4]
        if s.layout in ("lista", "icones") and len(s.items) < 2: s.layout = ""
        if s.image is not None and not (0 <= s.image < k): s.image = None
        if s.layout in ("capa_foto", "foto") and s.image is None and k: s.image = min(i, k - 1)
    return p


def local_plan(text, n, k):
    """Modo local (sem IA): distribui as frases do texto pelos slides e escolhe ícones por palavra-chave."""
    S = [x for x in re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip()) if x] or [""]
    out = []
    for i in range(n):
        ch = S[i * len(S) // n:(i + 1) * len(S) // n] or [S[-1]]
        first, rest = ch[0], " ".join(ch[1:])
        if len(first) > 90:
            w = first.split()
            rest, first = " ".join(ch), " ".join(w[:10]) + "…"
        out.append(Slide(label=f"{i + 1:02d}", headline=first, body=rest, icon=IC.pick_icon(first + " " + rest, ""), image=i if i < k else None))
    return Plan(slides=out)


def _clean(e):
    return gemini.clean(e)


def gemini_plan(text, n, fmt, k):
    """Plano de carrossel pelo Gemini. Levanta gemini.GeminiError (mensagem em português) se falhar."""
    d = gemini.generate_json(_prompt(text, n, fmt, k))
    return fix_plan(Plan(**d), n, k)


def make_plan(text, n, fmt, k, use_ai):
    """Retorna (plano, modo, aviso). Nunca depende da IA para funcionar."""
    if use_ai and gemini.has_key():
        try:
            return gemini_plan(text, n, fmt, k), "gemini", ""
        except Exception as e:  # noqa
            return fix_plan(local_plan(text, n, k), n, k), "demo", f"Gemini falhou, usei o modo local. Motivo: {_clean(e)}"
    aviso = "" if not use_ai else "Sem chave do Gemini: usei o modo local. Cole a chave na barra lateral para ativar a IA."
    return fix_plan(local_plan(text, n, k), n, k), "demo", aviso
