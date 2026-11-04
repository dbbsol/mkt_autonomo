"""Estratégia de conteúdo: briefing -> linha editorial -> calendário de 30 dias (15 peças) -> textos dos cards.
Metodologia: funil Topo/Meio/Fundo, níveis de consciência (Schwartz), PAS/AIDA nos carrosséis, pilares editoriais, 1 CTA por peça."""
import json, os, re, datetime as dt
from pydantic import BaseModel, field_validator
from ai import Slide, gemini_plan, _clean

NICHOS = ["Saúde e bem-estar", "Nutrição", "Fitness / personal", "Estética e beleza", "Odontologia", "Psicologia / terapia", "Advocacia / jurídico",
          "Finanças / consórcio / seguros", "Imobiliário", "Arquitetura / design", "Educação / cursos", "Tecnologia / automação", "Gastronomia",
          "Moda / varejo", "Marketing / agência", "Serviços B2B", "Outro"]
OBJ = ["Autoridade e confiança", "Engajamento e alcance", "Geração de leads / DMs", "Vendas diretas", "Lançamento", "Relacionamento / retenção"]
FUNIL = {OBJ[0]: (6, 6, 3), OBJ[1]: (8, 5, 2), OBJ[2]: (5, 5, 5), OBJ[3]: (4, 5, 6), OBJ[4]: (4, 5, 6), OBJ[5]: (5, 6, 4)}
CONSC = ["Inconsciente (não sabe que tem o problema)", "Consciente do problema", "Consciente da solução", "Consciente do produto/serviço", "Pronto para comprar"]
TONS = ["Didático", "Acolhedor", "Direto / provocativo", "Premium / sofisticado", "Bem-humorado", "Técnico / especialista", "Inspirador"]
CTAS = ["Chamar no direct", "Link na bio", "WhatsApp", "Comentar palavra-chave", "Salvar e compartilhar", "Agendar/Reservar"]
FUN = ["Topo", "Meio", "Fundo"]
PILAR_FUNIL = {"Educação": "Topo", "Conexão e bastidores": "Topo", "Autoridade e prova": "Meio", "Quebra de objeções": "Meio", "Oferta e conversão": "Fundo"}
PILAR_DESC = {"Educação": "Ensina algo útil e gera salvamentos e alcance.", "Conexão e bastidores": "Humaniza a marca e cria vínculo.",
              "Autoridade e prova": "Mostra método, critério e resultados reais informados pelo cliente.", "Quebra de objeções": "Responde dúvidas e travas antes da decisão.",
              "Oferta e conversão": "Apresenta a solução e chama para a ação."}
AFIN = {"Educação": .9, "Autoridade e prova": .8, "Quebra de objeções": .7, "Oferta e conversão": .4, "Conexão e bastidores": .3}
DEFAULT_P = {"Topo": "Educação", "Meio": "Autoridade e prova", "Fundo": "Oferta e conversão"}
ESTR = {OBJ[0]: "priorizar conteúdo de meio de funil (método, critério e prova) para ser lembrado como referência.",
        OBJ[1]: "priorizar topo de funil, com temas amplos e formatos salváveis/compartilháveis para ampliar o alcance.",
        OBJ[2]: "equilibrar o funil e fechar cada peça com um convite claro à conversa (direct, WhatsApp ou palavra-chave).",
        OBJ[3]: "reforçar o fundo de funil (oferta, objeções e chamada direta) sustentado por conteúdo de confiança.",
        OBJ[4]: "construir expectativa no topo/meio e concentrar as chamadas de oferta na segunda metade do período.",
        OBJ[5]: "aprofundar o meio de funil com conteúdo de uso, dúvidas frequentes e bastidores para quem já conhece a marca."}
KPIS = {OBJ[0]: "salvamentos, compartilhamentos, visitas ao perfil", OBJ[1]: "alcance, compartilhamentos, novos seguidores", OBJ[2]: "mensagens no direct, cliques no link, palavras-chave comentadas",
        OBJ[3]: "mensagens com intenção de compra, cliques, vendas atribuídas", OBJ[4]: "lista de interessados, cliques, mensagens", OBJ[5]: "respostas, salvamentos, retorno de clientes"}
HOOKS = {"Educação": ["O que ninguém te explica sobre {tema}", "5 erros comuns em {tema}", "{tema}: por onde começar"],
         "Autoridade e prova": ["Como {cliente} trabalha {tema}", "O critério por trás de {tema}", "O que {pub} ganha com {tema}"],
         "Conexão e bastidores": ["Quem está por trás de {cliente}", "Um dia na rotina de {cliente}", "Por que {cliente} trabalha com {nicho}"],
         "Quebra de objeções": ["“{obj}”: vamos conversar?", "Mito ou verdade sobre {tema}", "A dúvida mais comum sobre {tema}"],
         "Oferta e conversão": ["{tema}: para quem é", "Como funciona {tema}", "Pronto para começar? Fale com {cliente}"]}
WD = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
DEF = dict(cliente="", insta="", nicho=NICHOS[0], nicho_outro="", desc="", ofertas="", diferenciais="", temas="", pub="", idade="25–34", regiao="",
           consc=CONSC[1], dores="", desejos="", objecoes="", obj_mes=OBJ[0], tom=[], pilares=list(PILAR_FUNIL), pilar_extra="", cta=CTAS[0], palavra="",
           proibido="", datas="", inicio=dt.date.today(), ncar=9)


class _B(BaseModel):
    @field_validator("*", mode="before")
    @classmethod
    def _n(cls, v, info):
        return "" if v is None and cls.model_fields[info.field_name].annotation is str else v


class Pillar(_B):
    nome: str = ""; descricao: str = ""; funil: str = "Topo"


class Piece(_B):
    n: int = 0; dia: int = 1; formato: str = "Carrossel"; pilar: str = ""; funil: str = "Topo"
    tema: str = ""; gancho: str = ""; cta: str = ""; legenda: str = ""; slides: list[Slide] = []


class Strategy(_B):
    diagnostico: str = ""; pilares: list[Pillar] = []; pecas: list[Piece] = []


def L(t): return [x.strip(" -•\t") for x in (t or "").splitlines() if x.strip()]


def dlabel(B, p):
    d = dt.date.fromisoformat(B["inicio"]) + dt.timedelta(days=int(p.dia) - 1); return f"{WD[d.weekday()]} {d:%d/%m}"


def cta_text(B, funil):
    kw = (B.get("palavra") or "QUERO").upper()
    m = {CTAS[0]: "Chame no direct", CTAS[1]: "Acesse o link na bio", CTAS[2]: "Fale com a gente no WhatsApp", CTAS[3]: f'Comente "{kw}" e receba',
         CTAS[4]: "Salve e compartilhe com quem precisa", CTAS[5]: "Agende seu horário"}
    soft = {"Topo": "Salve e compartilhe com quem precisa", "Meio": "Siga para ver mais conteúdos assim"}
    if funil == "Topo" or (funil == "Meio" and B["obj_mes"] in (OBJ[0], OBJ[1], OBJ[5])): return soft[funil]
    return m.get(B["cta"], B["cta"])


def local_slides(B, p):
    pub, dores, des, difs = (B.get("pub") or "").strip(), L(B.get("dores")), L(B.get("desejos")), L(B.get("diferenciais"))
    if p.formato != "Carrossel":
        return [Slide(label=p.pilar.upper(), headline=p.gancho, subhead=B["cliente"], cta=p.cta)]
    g = lambda a, i, d: a[i % len(a)] if a else d
    return [Slide(label=p.pilar.upper(), headline=p.gancho, subhead=f"para {pub}" if pub else ""),
            Slide(label="O PONTO DE PARTIDA", headline="O ponto de partida", body=g(dores, p.n, f"Entenda o cenário de {p.tema}.")),
            Slide(label="POR QUE IMPORTA", headline="Por que isso importa", body=g(dores, p.n + 1, f"{p.tema} faz diferença no dia a dia de quem busca resultado.")),
            Slide(label="O CAMINHO", headline="O caminho", body=g(difs, p.n, f"Veja como {B['cliente']} conduz {p.tema}.")),
            Slide(label="O QUE MUDA", headline="O que muda", body=g(des, p.n, "Mais clareza e segurança para decidir.")),
            Slide(label="PRÓXIMO PASSO", headline="Próximo passo", cta=p.cta)]


def build_local(B):
    obj = B["obj_mes"]; cnt = dict(zip(FUN, FUNIL[obj]))
    sel = [p for p in B.get("pilares", []) if p in PILAR_FUNIL] or list(PILAR_FUNIL); extra = (B.get("pilar_extra") or "").strip()
    per = {f: [p for p in sel if PILAR_FUNIL[p] == f] for f in FUN}
    if extra: per["Topo"].append(extra)
    for f in FUN:
        if not per[f]: per[f] = [DEFAULT_P[f]]
    items = sorted(((k + .5) / cnt[f], FUN.index(f), f, per[f][k % len(per[f])]) for f in FUN for k in range(cnt[f]))
    car = set(sorted(range(15), key=lambda i: (-AFIN.get(items[i][3], .5), i))[:int(B.get("ncar", 9))])
    temas = L(B.get("temas")) or [B["nicho_final"]]; ofertas = L(B.get("ofertas")) or [B["cliente"]]; objs = L(B.get("objecoes"))
    pub = (B.get("pub") or "seu público").strip(); ct = dict(t=0, o=0, h={}); pecas = []
    for i, (_, _, f, pil) in enumerate(items):
        if pil == "Oferta e conversão": tema = ofertas[ct["o"] % len(ofertas)]; ct["o"] += 1
        else: tema = temas[ct["t"] % len(temas)]; ct["t"] += 1
        hs = HOOKS.get(pil, HOOKS["Educação"]); hi = ct["h"].get(pil, 0); ct["h"][pil] = hi + 1
        obj_t = objs[hi % len(objs)] if objs else "isso funciona de verdade?"
        p = Piece(n=i + 1, dia=round(1 + i * 29 / 14), formato="Carrossel" if i in car else "Post fixo", pilar=pil, funil=f, tema=tema,
                  gancho=hs[hi % len(hs)].format(tema=tema, pub=pub, cliente=B["cliente"], nicho=B["nicho_final"], obj=obj_t), cta=cta_text(B, f))
        p.slides = local_slides(B, p); p.legenda = "\n\n".join(x for x in (p.gancho, f"Conteúdo para {pub}." if B.get("pub") else "", p.cta) if x)
        pecas.append(p)
    start = dt.date.fromisoformat(B["inicio"])
    for ln in L(B.get("datas")):  # "dd/mm - evento": encaixa na peça mais próxima
        m = re.match(r"(\d{1,2})/(\d{1,2})\s*[-–:]\s*(.+)", ln)
        if m:
            try:
                d = dt.date(start.year, int(m[2]), int(m[1])); q = min(pecas, key=lambda x: abs((start + dt.timedelta(days=x.dia - 1) - d).days))
                if "data:" not in q.tema: q.tema += f" (data: {m[3]})"
            except ValueError: pass
    pil = [Pillar(nome=p, descricao=PILAR_DESC.get(p, "Pilar personalizado do cliente."), funil=PILAR_FUNIL.get(p, "Topo")) for f in FUN for p in per[f]]
    pub_s = pub + (f", região: {B['regiao']}" if B.get("regiao") else "")
    diag = (f"{B['cliente']} ({B.get('insta') or 'sem @ informado'}) atua em {B['nicho_final']}. Público: {pub_s}, nível de consciência “{B['consc']}”. "
            f"Objetivo do mês: {obj.lower()}; a estratégia é {ESTR[obj]} Tom de voz: {', '.join(B.get('tom') or ['a definir'])}. "
            f"Indicadores para acompanhar: {KPIS[obj]}.")
    return Strategy(diagnostico=diag, pilares=pil, pecas=pecas)


def brief_text(B):
    return "\n".join(f"{k}: {v}" for k, v in [("Cliente", B["cliente"]), ("Instagram", B.get("insta")), ("Nicho", B["nicho_final"]), ("Descrição/bio/site", B.get("desc")),
        ("Ofertas", "; ".join(L(B.get("ofertas")))), ("Diferenciais e provas reais", "; ".join(L(B.get("diferenciais")))), ("Temas que domina", "; ".join(L(B.get("temas")))),
        ("Público", B.get("pub")), ("Faixa etária", B.get("idade")), ("Região", B.get("regiao")), ("Nível de consciência", B["consc"]), ("Dores", "; ".join(L(B.get("dores")))),
        ("Desejos", "; ".join(L(B.get("desejos")))), ("Objeções", "; ".join(L(B.get("objecoes")))), ("Objetivo do mês", B["obj_mes"]), ("Tom de voz", ", ".join(B.get("tom") or [])),
        ("Pilares escolhidos", ", ".join(B.get("pilares") or [])), ("CTA preferido", B["cta"]), ("Palavra-chave", B.get("palavra")), ("NÃO pode ser dito", B.get("proibido")),
        ("Datas relevantes", "; ".join(L(B.get("datas")))), ("Início", B["inicio"])] if v)


PROMPT = """Você é estrategista sênior de social media (Instagram). Metodologia: funil Topo/Meio/Fundo, níveis de consciência (Schwartz), pilares editoriais,
carrosséis com PAS/AIDA, um único CTA por peça. Monte a linha editorial de 30 dias com EXATAMENTE 15 peças.
Responda SOMENTE JSON: {{"diagnostico":"(máx 120 palavras)","pilares":[{{"nome":"","descricao":"","funil":"Topo|Meio|Fundo"}}],
"pecas":[{{"n":1,"dia":1,"formato":"Carrossel|Post fixo","pilar":"","funil":"Topo|Meio|Fundo","tema":"","gancho":"(máx 12 palavras)","cta":"","legenda":"(máx 60 palavras)"}}]}}
Regras: {car} carrosséis e {fix} posts fixos; funil Topo {a}/Meio {b}/Fundo {c}; dias de 1 a 30 em ordem crescente; não repetir pilar nem formato mais de 2 vezes seguidas;
distribuir datas relevantes; NÃO invente fatos, preços, prazos, depoimentos ou resultados (use só o briefing; se faltar dado escreva "a confirmar"); respeite o que não pode ser dito.
BRIEFING:
{brief}"""


def build_ai(B):
    from google import genai
    c = genai.Client(api_key=os.environ["GEMINI_API_KEY"].strip().strip("\"'")); a, b, cc = FUNIL[B["obj_mes"]]; car = int(B.get("ncar", 9)); last = None
    prompt = PROMPT.format(car=car, fix=15 - car, a=a, b=b, c=cc, brief=brief_text(B))
    for m in dict.fromkeys([os.getenv("GEMINI_MODEL", "").strip(), "gemini-2.5-flash", "gemini-flash-latest", "gemini-2.0-flash"]):
        if not m: continue
        try:
            r = c.models.generate_content(model=m, contents=prompt, config={"response_mime_type": "application/json"})
            raw = r.text or ""; S = Strategy(**json.loads(raw[raw.index("{"):raw.rindex("}") + 1])); break
        except Exception as e: last = e
    else: raise last
    loc = build_local(B); S.pecas = sorted(S.pecas, key=lambda p: p.dia)[:15]
    S.pecas += loc.pecas[len(S.pecas):15]
    for i, p in enumerate(S.pecas):
        p.n = i + 1; p.dia = min(max(int(p.dia), 1), 30); p.formato = "Carrossel" if "carro" in p.formato.lower() else "Post fixo"
        p.funil = next((f for f in FUN if f.lower() in p.funil.lower()), "Topo"); p.slides = []
    if not S.pilares: S.pilares = loc.pilares
    S.diagnostico = S.diagnostico or loc.diagnostico
    return S


def card_brief(B, p):
    return (f"Tema: {p.tema}\nGancho (título do slide 1): {p.gancho}\nPilar: {p.pilar} | Funil: {p.funil}\nCTA final: {p.cta}\n"
            f"Contexto:\n{brief_text(B)}\nEscreva textos curtos para o público; não invente fatos.")


def write_cards(S, B, use_ai, only_missing=True, progress=None):
    warns = []
    for k, p in enumerate(S.pecas):
        if not (only_missing and p.slides):
            ns, sl = (6 if p.formato == "Carrossel" else 1), None
            if use_ai:
                try: sl = gemini_plan(card_brief(B, p), ns, "Instagram 4:5", 0).slides
                except Exception as e: warns.append(f"Peça {p.n}: IA indisponível ({_clean(e)[:90]}); usei o texto base.")
            p.slides = sl or local_slides(B, p)
            if not p.legenda: p.legenda = "\n\n".join(x for x in (p.gancho, p.cta) if x)
        if progress: progress((k + 1) / len(S.pecas))
    return warns
