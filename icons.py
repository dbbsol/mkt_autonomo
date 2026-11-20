"""Biblioteca de ícones vetoriais desenhados em código (sem arquivos externos).
Cada glifo é desenhado numa grade 100x100, em 8x e reduzido (borda lisa).
Para criar um ícone novo: escreva uma função g_nome(d, s, c, a, w) e registre em ICONS."""
import math
from functools import lru_cache
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

FD = Path(__file__).parent / "assets" / "fonts"
Q = 8  # fator de super-amostragem


def _P(s, pts):
    return [(x * s, y * s) for x, y in pts]


def _line(d, s, pts, c, w):
    p = _P(s, pts); d.line(p, fill=c, width=int(w * s), joint="curve")
    r = w * s / 2
    for x, y in (p[0], p[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=c)


def _poly(d, s, pts, c, soft=0):
    p = _P(s, pts); d.polygon(p, fill=c)
    if soft:
        d.line(p + [p[0]], fill=c, width=int(soft * s), joint="curve")


def _rr(d, s, x0, y0, x1, y1, r, c):
    d.rounded_rectangle((x0 * s, y0 * s, x1 * s, y1 * s), r * s, fill=c)


def _el(d, s, cx, cy, rx, ry=None, c=None):
    ry = rx if ry is None else ry
    d.ellipse(((cx - rx) * s, (cy - ry) * s, (cx + rx) * s, (cy + ry) * s), fill=c)


def _rot(layer, ang, s):
    return layer.rotate(ang, resample=Image.BICUBIC, center=(50 * s, 50 * s))


def _star(cx, cy, R, r, n=5, rot=-90):
    pts = []
    for i in range(n * 2):
        a = math.radians(rot + i * 180 / n); rr = R if i % 2 == 0 else r
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    return pts


def g_heart(d, s, c, a, w):
    pts = []
    for i in range(0, 360, 2):
        t = math.radians(i)
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((50 + x * 2.65, 45 + y * 2.65))
    _poly(d, s, pts, c)


def g_star(d, s, c, a, w):
    _poly(d, s, _star(50, 54, 44, 19), c, soft=7)


def g_bolt(d, s, c, a, w):
    _poly(d, s, [(60, 4), (22, 56), (46, 56), (38, 96), (78, 40), (54, 40)], c, soft=4)


def g_check(d, s, c, a, w):
    _line(d, s, [(20, 54), (42, 75), (80, 28)], c, 15)


def g_target(d, s, c, a, w):
    for r, k in ((44, 9), (29, 9)):
        d.ellipse(((50 - r) * s, (50 - r) * s, (50 + r) * s, (50 + r) * s), outline=c, width=int(k * s))
    _el(d, s, 50, 50, 11, c=c)
    _line(d, s, [(52, 48), (86, 14)], a, 6)
    _poly(d, s, [(86, 14), (80, 6), (96, 4), (94, 20), (92, 24)][:4] + [(86, 14)], a)


def g_pencil(d, s, c, a, w):
    L = Image.new("RGBA", (100 * s, 100 * s), (0, 0, 0, 0)); k = ImageDraw.Draw(L)
    _rr(k, s, 38, 18, 62, 66, 3, c)
    _poly(k, s, [(38, 68), (62, 68), (50, 94)], c, soft=2)
    _rr(k, s, 38, 8, 62, 20, 5, a)
    k.rectangle((38 * s, 22 * s, 62 * s, 25 * s), fill=(0, 0, 0, 0))
    k.polygon(_P(s, [(45, 80), (55, 80), (50, 94)]), fill=a)
    return _rot(L, 45, s), True


def g_chart(d, s, c, a, w):
    _rr(d, s, 10, 56, 30, 92, 4, c); _rr(d, s, 40, 40, 60, 92, 4, c); _rr(d, s, 70, 22, 90, 92, 4, c)
    _line(d, s, [(10, 38), (36, 22), (54, 28), (84, 4)], a, 6)
    _poly(d, s, [(90, 0), (92, 18), (74, 10)], a)


def g_chat(d, s, c, a, w):
    _rr(d, s, 8, 12, 92, 70, 18, c)
    _poly(d, s, [(26, 66), (24, 92), (52, 68)], c)
    for x in (30, 50, 70):
        _el(d, s, x, 41, 5.5, c=(0, 0, 0, 0))


def g_phone(d, s, c, a, w):
    _rr(d, s, 24, 4, 76, 96, 12, c)
    _rr(d, s, 31, 14, 69, 80, 5, a)
    _poly(d, s, [(44, 36), (44, 58), (60, 47)], (255, 255, 255, 255), soft=3)
    _el(d, s, 50, 88, 3.4, c=a)


def g_bulb(d, s, c, a, w):
    _el(d, s, 50, 38, 28, c=c)
    _poly(d, s, [(36, 56), (64, 56), (60, 78), (40, 78)], c)
    _rr(d, s, 38, 80, 62, 87, 3, c); _rr(d, s, 43, 89, 57, 95, 3, c)
    _line(d, s, [(42, 40), (50, 52), (58, 40)], a, 4.5)
    for ang in (-60, -30, 0, 30, 60):
        t = math.radians(ang - 90)
        _line(d, s, [(50 + 36 * math.cos(t), 38 + 36 * math.sin(t)), (50 + 46 * math.cos(t), 38 + 46 * math.sin(t))], a, 4.5)


def g_rocket(d, s, c, a, w):
    L = Image.new("RGBA", (100 * s, 100 * s), (0, 0, 0, 0)); k = ImageDraw.Draw(L)
    _poly(k, s, [(50, 4), (64, 22), (67, 54), (61, 74), (39, 74), (33, 54), (36, 22)], c, soft=4)
    _poly(k, s, [(34, 46), (16, 66), (16, 80), (36, 70)], a, soft=3)
    _poly(k, s, [(66, 46), (84, 66), (84, 80), (64, 70)], a, soft=3)
    _poly(k, s, [(42, 78), (58, 78), (50, 98)], a)
    _el(k, s, 50, 38, 10, c=(0, 0, 0, 0)); _el(k, s, 50, 38, 6, c=a)
    return _rot(L, 38, s), True


def g_bag(d, s, c, a, w):
    d.arc((32 * s, 6 * s, 68 * s, 48 * s), 180, 360, fill=a, width=int(8 * s))
    _poly(d, s, [(16, 32), (84, 32), (90, 92), (10, 92)], c, soft=6)
    _el(d, s, 36, 46, 4.5, c=(0, 0, 0, 0)); _el(d, s, 64, 46, 4.5, c=(0, 0, 0, 0))


def g_calendar(d, s, c, a, w):
    _rr(d, s, 8, 16, 92, 94, 13, c)
    _rr(d, s, 8, 16, 92, 40, 13, a); d.rectangle((8 * s, 30 * s, 92 * s, 40 * s), fill=a)
    _rr(d, s, 27, 5, 37, 26, 4, c); _rr(d, s, 63, 5, 73, 26, 4, c)
    for r in range(2):
        for q in range(3):
            _rr(d, s, 20 + q * 22, 50 + r * 20, 34 + q * 22, 63 + r * 20, 3, (255, 255, 255, 255))


def g_gear(d, s, c, a, w):
    for i in range(8):
        L = Image.new("RGBA", (100 * s, 100 * s), (0, 0, 0, 0)); k = ImageDraw.Draw(L)
        _rr(k, s, 42, 4, 58, 28, 3, c)
        d.bitmap((0, 0), _rot(L, i * 45, s).split()[3], fill=c)
    _el(d, s, 50, 50, 33, c=c)
    _el(d, s, 50, 50, 14, c=(0, 0, 0, 0))


def g_users(d, s, c, a, w):
    _el(d, s, 66, 32, 13, c=a); d.pieslice((46 * s, 50 * s, 92 * s, 104 * s), 180, 360, fill=a)
    _el(d, s, 36, 30, 16, c=c); d.pieslice((8 * s, 52 * s, 64 * s, 112 * s), 180, 360, fill=c)


def g_megaphone(d, s, c, a, w):
    _poly(d, s, [(10, 38), (38, 38), (74, 14), (74, 78), (38, 54), (10, 54)], c, soft=4)
    _rr(d, s, 24, 54, 42, 84, 6, a)
    d.arc((60 * s, 28 * s, 92 * s, 64 * s), -60, 60, fill=a, width=int(5 * s))
    d.arc((70 * s, 18 * s, 102 * s, 74 * s), -55, 55, fill=a, width=int(5 * s))


def g_camera(d, s, c, a, w):
    _poly(d, s, [(32, 28), (40, 14), (60, 14), (68, 28)], c, soft=4)
    _rr(d, s, 6, 26, 94, 86, 14, c)
    _el(d, s, 50, 56, 22, c=(0, 0, 0, 0)); _el(d, s, 50, 56, 14, c=a)
    _el(d, s, 80, 38, 4, c=(0, 0, 0, 0))


def g_trophy(d, s, c, a, w):
    d.arc((8 * s, 12 * s, 36 * s, 42 * s), 90, 270, fill=c, width=int(7 * s))
    d.arc((64 * s, 12 * s, 92 * s, 42 * s), -90, 90, fill=c, width=int(7 * s))
    _poly(d, s, [(24, 8), (76, 8), (73, 38), (62, 56), (38, 56), (27, 38)], c, soft=4)
    _rr(d, s, 43, 54, 57, 74, 2, c); _rr(d, s, 28, 74, 72, 92, 5, a)
    _poly(d, s, _star(50, 28, 10, 4.2), (255, 255, 255, 255))


def g_clock(d, s, c, a, w):
    _el(d, s, 50, 50, 44, c=c)
    _line(d, s, [(50, 24), (50, 50), (68, 62)], (255, 255, 255, 255), 7)
    _el(d, s, 50, 50, 5, c=a)


def g_shield(d, s, c, a, w):
    _poly(d, s, [(50, 4), (86, 18), (85, 50), (72, 76), (50, 96), (28, 76), (15, 50), (14, 18)], c, soft=6)
    _line(d, s, [(32, 50), (45, 63), (69, 36)], (255, 255, 255, 255), 9)


def g_link(d, s, c, a, w):
    L = Image.new("RGBA", (100 * s, 100 * s), (0, 0, 0, 0)); k = ImageDraw.Draw(L)
    k.rounded_rectangle((4 * s, 34 * s, 56 * s, 66 * s), 16 * s, outline=c, width=int(10 * s))
    k.rounded_rectangle((44 * s, 34 * s, 96 * s, 66 * s), 16 * s, outline=a, width=int(10 * s))
    return _rot(L, 40, s), True


def g_mail(d, s, c, a, w):
    _rr(d, s, 6, 18, 94, 82, 11, c)
    _line(d, s, [(14, 28), (50, 58), (86, 28)], (255, 255, 255, 255), 7)


def g_play(d, s, c, a, w):
    _el(d, s, 50, 50, 45, c=c)
    _poly(d, s, [(39, 28), (39, 72), (74, 50)], (255, 255, 255, 255), soft=6)


def g_search(d, s, c, a, w):
    d.ellipse((10 * s, 10 * s, 68 * s, 68 * s), outline=c, width=int(11 * s))
    _line(d, s, [(62, 62), (88, 88)], a, 13)


def g_gift(d, s, c, a, w):
    _rr(d, s, 14, 46, 86, 94, 7, c)
    _rr(d, s, 8, 32, 92, 50, 6, a)
    _rr(d, s, 44, 32, 56, 94, 2, (255, 255, 255, 255))
    d.ellipse((24 * s, 8 * s, 50 * s, 34 * s), outline=a, width=int(7 * s))
    d.ellipse((50 * s, 8 * s, 76 * s, 34 * s), outline=a, width=int(7 * s))


def g_coin(d, s, c, a, w):
    _el(d, s, 50, 50, 45, c=c)
    _el(d, s, 50, 50, 36, c=(0, 0, 0, 0)); _el(d, s, 50, 50, 33, c=c)
    f = ImageFont.truetype(str(FD / "Poppins-SemiBold.ttf"), int(50 * s))
    d.text((50 * s, 53 * s), "$", font=f, fill=(255, 255, 255, 255), anchor="mm")


def g_crown(d, s, c, a, w):
    _poly(d, s, [(8, 76), (12, 26), (34, 52), (50, 14), (66, 52), (88, 26), (92, 76)], c, soft=5)
    _rr(d, s, 8, 78, 92, 92, 5, a)
    for x, y in ((12, 24), (50, 12), (88, 24)):
        _el(d, s, x, y, 6, c=a)


def g_pin(d, s, c, a, w):
    _el(d, s, 50, 38, 32, c=c)
    _poly(d, s, [(22, 52), (78, 52), (50, 96)], c, soft=3)
    _el(d, s, 50, 38, 12, c=(0, 0, 0, 0))


def g_eye(d, s, c, a, w):
    pts = [(x, 50 - 30 * (1 - ((x - 50) / 44) ** 2) ** .8) for x in range(6, 95, 2)]
    pts += [(x, 50 + 30 * (1 - ((x - 50) / 44) ** 2) ** .8) for x in range(94, 5, -2)]
    _poly(d, s, pts, c)
    _el(d, s, 50, 50, 17, c=(255, 255, 255, 255)); _el(d, s, 50, 50, 9, c=a)


def g_book(d, s, c, a, w):
    _poly(d, s, [(47, 24), (8, 14), (8, 78), (47, 90)], c, soft=4)
    _poly(d, s, [(53, 24), (92, 14), (92, 78), (53, 90)], a, soft=4)
    for y in (34, 46, 58):
        _line(d, s, [(17, y - 2), (38, y + 4)], (255, 255, 255, 255), 3.4)
        _line(d, s, [(62, y + 4), (83, y - 2)], (255, 255, 255, 255), 3.4)


def g_sparkle(d, s, c, a, w):
    def sp(cx, cy, R, col):
        r = R * .26
        _poly(d, s, [(cx, cy - R), (cx + r, cy - r), (cx + R, cy), (cx + r, cy + r), (cx, cy + R), (cx - r, cy + r), (cx - R, cy), (cx - r, cy - r)], col, soft=2)
    sp(40, 56, 38, c); sp(76, 22, 17, a); sp(80, 76, 12, a)


def g_send(d, s, c, a, w):
    _poly(d, s, [(6, 46), (94, 6), (68, 94), (48, 62)], c, soft=4)
    _line(d, s, [(48, 62), (94, 6)], (255, 255, 255, 255), 3.5)
    _poly(d, s, [(48, 62), (50, 84), (60, 70)], a)


def g_growth(d, s, c, a, w):
    _line(d, s, [(8, 76), (34, 48), (52, 62), (84, 24)], c, 11)
    _poly(d, s, [(94, 14), (92, 46), (62, 18)], c, soft=4)
    _rr(d, s, 6, 90, 94, 96, 3, a)


def g_checklist(d, s, c, a, w):
    _rr(d, s, 14, 12, 86, 94, 11, c)
    _rr(d, s, 33, 4, 67, 22, 6, a)
    for i, y in enumerate((38, 56, 74)):
        _line(d, s, [(24, y), (28, y + 4), (35, y - 4)], (255, 255, 255, 255), 3.6)
        _rr(d, s, 44, y - 3, 76, y + 3, 3, (255, 255, 255, 255))


def g_bookmark(d, s, c, a, w):
    _poly(d, s, [(24, 6), (76, 6), (76, 94), (50, 72), (24, 94)], c, soft=5)


def g_share(d, s, c, a, w):
    _line(d, s, [(24, 50), (74, 22)], c, 6); _line(d, s, [(24, 50), (74, 78)], c, 6)
    for x, y in ((24, 50), (76, 22), (76, 78)):
        _el(d, s, x, y, 14, c=c)
    _el(d, s, 24, 50, 5, c=a)


def g_users2(d, s, c, a, w):  # alias visual: cliente/pessoa
    _el(d, s, 50, 30, 20, c=c); d.pieslice((14 * s, 56 * s, 86 * s, 130 * s), 180, 360, fill=c)


ICONS = {
    "heart": ("Coração", g_heart), "star": ("Estrela", g_star), "bolt": ("Raio / rápido", g_bolt), "check": ("Check", g_check),
    "target": ("Alvo / estratégia", g_target), "pencil": ("Lápis / criação", g_pencil), "chart": ("Gráfico", g_chart),
    "growth": ("Crescimento", g_growth), "chat": ("Conversa", g_chat), "phone": ("Celular", g_phone), "bulb": ("Ideia", g_bulb),
    "rocket": ("Foguete", g_rocket), "bag": ("Sacola / venda", g_bag), "calendar": ("Calendário", g_calendar), "gear": ("Engrenagem / processo", g_gear),
    "users": ("Pessoas / público", g_users), "person": ("Pessoa", g_users2), "megaphone": ("Megafone", g_megaphone), "camera": ("Câmera", g_camera),
    "trophy": ("Troféu / resultado", g_trophy), "clock": ("Relógio / tempo", g_clock), "shield": ("Escudo / segurança", g_shield),
    "link": ("Link", g_link), "mail": ("E-mail", g_mail), "play": ("Vídeo / play", g_play), "search": ("Busca", g_search),
    "gift": ("Presente / bônus", g_gift), "coin": ("Dinheiro", g_coin), "crown": ("Coroa / premium", g_crown), "pin": ("Local", g_pin),
    "eye": ("Visibilidade", g_eye), "book": ("Livro / educação", g_book), "sparkle": ("Brilho / IA", g_sparkle), "send": ("Enviar", g_send),
    "checklist": ("Checklist", g_checklist), "bookmark": ("Salvar", g_bookmark), "share": ("Compartilhar", g_share),
}
ICON_LABELS = {k: v[0] for k, v in ICONS.items()}
DEFAULT_ICON = "star"

# palavra-chave -> ícone (usado pelo modo local e para completar o que a IA não indicar)
KEYWORDS = [
    (("estrat", "plano", "meta", "objetiv", "foco"), "target"), (("cri", "design", "arte", "legenda", "texto", "escrev"), "pencil"),
    (("engaj", "curt", "amor", "cuidado", "relacion"), "heart"), (("venda", "compra", "loja", "produto", "oferta"), "bag"),
    (("dinheiro", "lucro", "invest", "preço", "preco", "financ", "caixa"), "coin"), (("resultado", "conquist", "premi", "vit"), "trophy"),
    (("cresc", "escal", "aument", "alcance"), "growth"), (("dado", "métrica", "metrica", "análise", "analise", "número", "numero", "relat"), "chart"),
    (("ideia", "dica", "aprend", "insight"), "bulb"), (("tempo", "rotina", "hora", "prazo", "rápid", "rapid"), "clock"),
    (("cliente", "público", "publico", "audiência", "comunidade", "pessoa", "equipe", "time"), "users"), (("conversa", "direct", "dm", "whats", "atend", "pergunt", "dúvida", "duvida"), "chat"),
    (("vídeo", "video", "reels", "stories", "story"), "play"), (("foto", "imagem", "visual", "feed", "perfil"), "camera"),
    (("process", "automa", "sistema", "ferrament", "organiz"), "gear"), (("segur", "confian", "garantia", "proteg"), "shield"),
    (("calend", "agenda", "data", "cronograma"), "calendar"), (("lançament", "lancament", "começ", "comec", "início", "inicio", "novo"), "rocket"),
    (("autoridade", "premium", "exclusiv", "líder", "lider"), "crown"), (("bônus", "bonus", "presente", "brinde"), "gift"),
    (("ia ", "inteligência", "inteligencia", "magia"), "sparkle"), (("salv", "guard"), "bookmark"), (("compartilh", "envi", "indic"), "share"),
    (("curso", "aula", "ebook", "livro", "educa", "estud"), "book"), (("visib", "ver ", "olhar", "enxerg"), "eye"), (("anúncio", "anuncio", "divulg", "campanha", "tráfego", "trafego"), "megaphone"),
    (("local", "endereço", "endereco", "região", "regiao", "cidade"), "pin"), (("checklist", "passo", "etapa", "lista"), "checklist"), (("link", "site", "acesse"), "link"),
]


def pick_icon(text, fallback=DEFAULT_ICON):
    t = (text or "").lower() + " "
    for keys, ic in KEYWORDS:
        if any(k in t for k in keys):
            return ic
    return fallback


@lru_cache(maxsize=512)
def glyph(name, size, c=(255, 255, 255, 255), a=None):
    """Retorna RGBA (size x size) com o ícone. c = cor principal, a = cor de apoio (padrão = c)."""
    fn = ICONS.get(name, ICONS[DEFAULT_ICON])[1]
    a = a or c
    s = Q
    big = Image.new("RGBA", (100 * s, 100 * s), (0, 0, 0, 0)); d = ImageDraw.Draw(big)
    r = fn(d, s, c, a, 0)
    if isinstance(r, tuple):
        big = r[0]
    return big.resize((int(size), int(size)), Image.LANCZOS)


def contact_sheet(cols=6, cell=150, fg=(232, 82, 126, 255), fg2=(217, 164, 65, 255), bg=(251, 240, 232), label_fg=(60, 40, 40)):
    names = list(ICONS); rows = (len(names) + cols - 1) // cols
    im = Image.new("RGB", (cols * cell, rows * (cell + 34)), bg); d = ImageDraw.Draw(im)
    f = ImageFont.truetype(str(FD / "Poppins-Medium.ttf"), 17)
    for i, n in enumerate(names):
        x, y = (i % cols) * cell, (i // cols) * (cell + 34)
        g = glyph(n, 84, fg, fg2); im.paste(g, (x + (cell - 84) // 2, y + 14), g)
        d.text((x + cell / 2, y + cell + 6), ICON_LABELS[n], font=f, fill=label_fg, anchor="mt")
    return im
