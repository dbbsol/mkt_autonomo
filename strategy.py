"""Estratégia de conteúdo: briefing -> plano de 10 dias (1 carrossel por dia) -> textos dos cards.
Metodologia: funil Topo/Meio/Fundo, níveis de consciência (Schwartz), PAS/AIDA nos carrosséis, pilares editoriais, 1 CTA por peça."""
import re, datetime as dt
from pydantic import BaseModel, field_validator
import gemini
import icons as IC
from ai import Slide, Item, gemini_plan, fix_plan, _clean

N = 10   # dias do plano = carrosséis (1 por dia)

NICHOS = ["Saúde e bem-estar", "Nutrição", "Fitness / personal", "Estética e beleza", "Odontologia", "Psicologia / terapia", "Advocacia / jurídico",
          "Finanças / consórcio / seguros", "Imobiliário", "Arquitetura / design", "Educação / cursos", "Tecnologia / automação", "Gastronomia",
          "Moda / varejo", "Marketing / agência", "Serviços B2B", "Outro"]
OBJ = ["Autoridade e confiança", "Engajamento e alcance", "Geração de leads / DMs", "Vendas diretas", "Lançamento", "Relacionamento / retenção"]
FUNIL = {OBJ[0]: (4, 4, 2), OBJ[1]: (5, 3, 2), OBJ[2]: (3, 3, 4), OBJ[3]: (2, 3, 5), OBJ[4]: (2, 4, 4), OBJ[5]: (3, 4, 3)}   # Topo/Meio/Fundo, soma 10
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
           proibido="", datas="", inicio=dt.date.today())


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


_STOP = {"de", "da", "do", "das", "dos", "e", "a", "o", "com", "para", "em", "no", "na", "que", "um", "uma", "por"}


def _short(t, n=3):
    w = (t or "").strip().rstrip(".!?").split()[:n]
    while len(w) > 1 and (w[-1].lower() in _STOP or w[-1].isdigit()): w.pop()
    return " ".join(w).capitalize() if w else ""


def _items(lines, p, n=3, fb=()):
    src = list(lines) or list(fb)
    out = []
    for j in range(n):
        t = src[(p.n + j) % len(src)] if src else ""
        lb = _short(t); tx = "" if (len(t.split()) <= 3 or t.lower().startswith(lb.lower())) else t[:90]
        out.append(Item(icon=IC.pick_icon(t, ["target", "chart", "bulb", "heart", "gear"][(p.n + j) % 5]), label=lb, text=tx))
    return out


def local_slides(B, p):
    """Carrossel de 6 slides sem IA (capa, problema, lista, caminho, passos/ícones, CTA), já com layout e ícones."""
    pub, dores, des, difs = (B.get("pub") or "").strip(), L(B.get("dores")), L(B.get("desejos")), L(B.get("diferenciais"))
    g = lambda a, i, d: a[i % len(a)] if a else d
    tema = p.tema
    hl = max((w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", p.gancho)), key=len, default="")
    steps = [Item(label="Entenda", text=f"Veja onde {tema} trava hoje."), Item(label="Organize", text="Defina o que importa primeiro."),
             Item(label="Aplique", text="Comece pequeno e repita toda semana."), Item(label="Meça", text="Ajuste com base no que funcionou.")]
    five = (Slide(layout="passos", label="PASSO A PASSO", headline=f"Como começar com {tema}"[:60], icon="checklist", items=steps) if p.pilar == "Educação"
            else Slide(layout="icones", label="O QUE MUDA", headline="O que muda na prática", icon="growth", items=_items(des, p, 3, ["Mais clareza", "Mais segurança", "Mais resultado"])))
    return [Slide(layout="capa", label=p.pilar.upper(), headline=p.gancho, highlight=hl, subhead=f"Para {pub}" if pub else B["cliente"], icon=IC.pick_icon(tema + " " + p.gancho, "sparkle")),
            Slide(layout="texto", label="O PONTO DE PARTIDA", headline="Você já passou por isso?", subhead=g(dores, p.n, f"Entender {tema} muda o jogo."),
                  body=f"Quase ninguém explica **{tema}** com clareza.", icon="eye"),
            Slide(layout="lista", label="POR QUE IMPORTA", headline="3 pontos que fazem diferença", icon="bulb", items=_items(dores + difs, p, 3, [f"{tema} pede método", "Constância vence pressa", "Clareza gera confiança"])),
            Slide(layout="texto", label="O CAMINHO", headline="Como "+B["cliente"]+" conduz", subhead=g(difs, p.n, f"Método simples para {tema}."), body=g(des, p.n, "Mais clareza e segurança para decidir."), icon="target"),
            five,
            Slide(layout="cta", label="PRÓXIMO PASSO", headline="Vamos conversar?", subhead=f"Com {B['cliente']} você dá o próximo passo.", cta=p.cta[:40] or "Fale com a gente", icon="send")]


def build_local(B):
    obj = B["obj_mes"]; cnt = dict(zip(FUN, FUNIL[obj]))
    sel = [p for p in B.get("pilares", []) if p in PILAR_FUNIL] or list(PILAR_FUNIL); extra = (B.get("pilar_extra") or "").strip()
    per = {f: [p for p in sel if PILAR_FUNIL[p] == f] for f in FUN}
    if extra: per["Topo"].append(extra)
    for f in FUN:
        if not per[f]: per[f] = [DEFAULT_P[f]]
    items = sorted(((k + .5) / cnt[f], FUN.index(f), f, per[f][k % len(per[f])]) for f in FUN for k in range(cnt[f]))
    temas = L(B.get("temas")) or [B["nicho_final"]]; ofertas = L(B.get("ofertas")) or [B["cliente"]]; objs = L(B.get("objecoes"))
    pub = (B.get("pub") or "seu público").strip(); ct = dict(t=0, o=0, h={}); pecas = []
    for i, (_, _, f, pil) in enumerate(items):
        if pil == "Oferta e conversão": tema = ofertas[ct["o"] % len(ofertas)]; ct["o"] += 1
        else: tema = temas[ct["t"] % len(temas)]; ct["t"] += 1
        hs = HOOKS.get(pil, HOOKS["Educação"]); hi = ct["h"].get(pil, 0); ct["h"][pil] = hi + 1
        obj_t = objs[hi % len(objs)] if objs else "isso funciona de verdade?"
        p = Piece(n=i + 1, dia=i + 1, formato="Carrossel", pilar=pil, funil=f, tema=tema,
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
            f"Objetivo do período: {obj.lower()}; a estratégia é {ESTR[obj]} Tom de voz: {', '.join(B.get('tom') or ['a definir'])}. "
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
carrosséis com PAS/AIDA, um único CTA por peça. Monte um PLANO DE 10 DIAS com EXATAMENTE 10 carrosséis: 1 carrossel por dia, do dia 1 ao dia 10, em ordem.
Responda SOMENTE JSON: {{"diagnostico":"(máx 100 palavras)","pilares":[{{"nome":"","descricao":"","funil":"Topo|Meio|Fundo"}}],
"pecas":[{{"n":1,"dia":1,"formato":"Carrossel","pilar":"","funil":"Topo|Meio|Fundo","tema":"","gancho":"(máx 10 palavras, vira o título da capa)","cta":"","legenda":"(máx 60 palavras)"}}]}}
Regras: funil Topo {a}/Meio {b}/Fundo {c}; não repetir o mesmo pilar mais de 2 vezes seguidas; a sequência deve contar uma história (atrair, educar, provar, converter);
distribuir datas relevantes; NÃO invente fatos, preços, prazos, depoimentos ou resultados (use só o briefing; se faltar dado escreva "a confirmar"); respeite o que não pode ser dito.
BRIEFING:
{brief}"""


def build_ai(B):
    a, b, cc = FUNIL[B["obj_mes"]]
    d = gemini.generate_json(PROMPT.format(a=a, b=b, c=cc, brief=brief_text(B)))
    S = Strategy(**d)
    loc = build_local(B); S.pecas = sorted(S.pecas, key=lambda p: p.dia)[:N]
    S.pecas += loc.pecas[len(S.pecas):N]
    for i, p in enumerate(S.pecas):
        p.n = i + 1; p.dia = i + 1; p.formato = "Carrossel"
        p.funil = next((f for f in FUN if f.lower() in p.funil.lower()), "Topo"); p.slides = []
        p.cta = p.cta or cta_text(B, p.funil)
    if not S.pilares: S.pilares = loc.pilares
    S.diagnostico = S.diagnostico or loc.diagnostico
    return S


def card_brief(B, p):
    return (f"Tema: {p.tema}\nGancho (headline do slide 1): {p.gancho}\nPilar: {p.pilar} | Funil: {p.funil}\nCTA do último slide: {p.cta}\n"
            f"Estrutura: capa, problema, lista de 3 pontos, caminho, passos ou ícones, CTA.\n"
            f"Contexto:\n{brief_text(B)}\nEscreva textos curtos para o público; não invente fatos.")


def write_cards(S, B, use_ai, only_missing=True, progress=None):
    """Escreve os 6 slides de cada carrossel (Gemini ou modo local). Se a IA falhar, avisa uma vez e completa o resto no modo local."""
    warns = []; ai_ok = use_ai
    for k, p in enumerate(S.pecas):
        if not (only_missing and p.slides):
            sl = None
            if ai_ok:
                try: sl = gemini_plan(card_brief(B, p), 6, "Instagram 4:5", 0).slides
                except Exception as e:
                    warns.append(f"Carrossel {p.n}: IA indisponível ({_clean(e)[:140]}); usei o texto local nos demais."); ai_ok = False
            p.slides = sl or local_slides(B, p)
            if not p.legenda: p.legenda = "\n\n".join(x for x in (p.gancho, p.cta) if x)
        if progress: progress((k + 1) / len(S.pecas))
    return warns
