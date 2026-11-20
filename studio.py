from pathlib import Path
"""Motor de design 'Studio': carrosséis editoriais com sombras suaves, selos 3D, pincel, vidro, ícones e fotos.
Tudo é desenhado em 2x (super-amostragem) e reduzido, para bordas lisas. Um estilo = um arquivo em templates/ (engine='studio').
Layouts: capa, capa_foto, texto, lista, icones, foto, citacao, cta  (escolha automática, com opção manual por slide)."""
import io, re, math, random, hashlib
from collections import OrderedDict
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageChops
from config import FORMATS
from fonts import face
import icons as IC

SS = 2
LAYOUTS_STUDIO = {"auto": "Automático", "capa": "Capa", "capa_foto": "Capa com foto cheia", "texto": "Texto", "lista": "Lista de itens (cards)",
                  "icones": "Ícones em linha", "passos": "Passos (linha do tempo)", "foto": "Foto + texto", "citacao": "Citação / destaque", "cta": "Encerramento (CTA)"}


# ───────────────────────── utilitários de cor e imagem ─────────────────────────
def rgb(h, a=None):
    h = h.lstrip("#"); t = tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
    return t if a is None else t + (int(255 * a),)


def mix(c0, c1, t):
    return tuple(int(c0[i] + (c1[i] - c0[i]) * t) for i in range(3))


def grad(w, h, c0, c1, ang=90):
    gw, gh = max(2, min(w, 96)), max(2, min(h, 96))
    x = np.linspace(0, 1, gw)[None, :]; y = np.linspace(0, 1, gh)[:, None]; a = math.radians(ang)
    t = x * math.cos(a) + y * math.sin(a); t = (t - t.min()) / (t.max() - t.min() + 1e-9)
    arr = np.array(c0[:3], float)[None, None, :] * (1 - t[..., None]) + np.array(c1[:3], float)[None, None, :] * t[..., None]
    return Image.fromarray(arr.astype("uint8"), "RGB").resize((w, h), Image.BICUBIC)


def radial(w, h, cx, cy, r, power=1.6):
    gw, gh = max(2, w // 8), max(2, h // 8)
    ys, xs = np.mgrid[0:gh, 0:gw]; d = np.hypot(xs * 8 - cx, ys * 8 - cy) / max(r, 1)
    return Image.fromarray((np.clip(1 - d, 0, 1) ** power * 255).astype("uint8"), "L").resize((w, h), Image.BICUBIC)


def scale_mask(m, k):
    return m.point(lambda v: int(v * k))


def cover_fit(img, w, h, focus=(.5, .45)):
    r = max(w / img.width, h / img.height)
    img = img.resize((max(w, int(img.width * r + .5)), max(h, int(img.height * r + .5))), Image.LANCZOS)
    l = int((img.width - w) * focus[0]); t = int((img.height - h) * focus[1])
    return img.crop((l, t, l + w, t + h))


def initials(t):
    t = re.sub(r"[^A-Za-zÀ-ÿ0-9 ]", " ", t or "").split()
    return ("".join(w[0] for w in t[:2]) or "✦").upper()


# ───────────────────────── tela de desenho ─────────────────────────
class Cv:
    def __init__(c, fmt, st, i, n, brand, logo):
        F = FORMATS[fmt]; c.W = 1080; c.H = round(1080 * F["h"] / F["w"]); c.k = SS; c.st = st; c.i, c.n = i, n
        c.top = F["top"]; c.brand = brand or ""; c.logo = logo; c.warns = []
        c.im = Image.new("RGB", (c.W * c.k, c.H * c.k), rgb(st["bg"])); c.d = ImageDraw.Draw(c.im, "RGBA")
        c.m = 84; tall = c.H / c.W > 1.5
        c.yc = (.905 if tall else .958) * c.H                     # mesma linha do indicador de carrossel
        c.y0 = c.top + 96; c.y1 = c.yc - 78
        c.P = {k: (rgb(v) if isinstance(v, str) and v.startswith("#") else v) for k, v in st.items()}

    def px(c, v): return int(round(v * c.k))
    def col(c, name, a=1.0):
        t = tuple(c.P[name])
        return t[:3] + (int(255 * a),) if len(t) == 3 else t[:3] + (int(t[3] * a),)

    def font(c, key, size): return face(key, max(8, int(size * c.k)))

    def tw(c, text, f, sp=0): return c.d.textlength(text, font=f) + sp * c.k * max(len(text) - 1, 0)

    def text(c, x, y, t, key, size, fill, anchor="ls", sp=0, d=None):
        """x,y em unidades de design (y = linha de base para anchor 'ls')."""
        d = d or c.d; f = c.font(key, size)
        if not sp:
            d.text((x * c.k, y * c.k), t, font=f, fill=fill, anchor=anchor); return
        w = c.tw(t, f, sp); xx = x * c.k - (w / 2 if anchor[0] == "m" else (w if anchor[0] == "r" else 0))
        for ch in t:
            d.text((xx, y * c.k), ch, font=f, fill=fill, anchor="l" + anchor[1]); xx += d.textlength(ch, font=f) + sp * c.k

    def put(c, layer, x, y, shadow=None):
        """Cola camada RGBA (px) em (x,y) em unidades de design (canto sup. esq.), com sombra suave opcional."""
        X, Y = int(round(x * c.k)), int(round(y * c.k))
        if shadow:
            blur, dy, al, colr = shadow; b = blur * c.k; pad = int(b * 3) + 2
            m = Image.new("L", (layer.width + 2 * pad, layer.height + 2 * pad), 0); m.paste(layer.getchannel("A"), (pad, pad))
            m = scale_mask(m.filter(ImageFilter.GaussianBlur(b)), al)
            c.im.paste(tuple(colr[:3]), (X - pad, Y - pad + int(dy * c.k)), m)
        c.im.paste(layer.convert("RGB"), (X, Y), layer.getchannel("A"))

    def ghost(c, x, y, t, key, size, name, alpha, anchor="ls"):
        """Texto translúcido (o ImageDraw ignora alfa em texto): máscara + cor."""
        if getattr(c, "measure", False): return
        f = c.font(key, size); m = Image.new("L", c.im.size, 0); ImageDraw.Draw(m).text((x * c.k, y * c.k), t, font=f, fill=255, anchor=anchor)
        c.im.paste(tuple(c.P[name][:3]), (0, 0), scale_mask(m, alpha))

    def layer(c, w, h): return Image.new("RGBA", (int(w * c.k), int(h * c.k)), (0, 0, 0, 0))


# ───────────────────────── fundo e decoração ─────────────────────────
def draw_bg(c):
    st, w, h = c.st, c.im.width, c.im.height
    c.im.paste(grad(w, h, c.P["bg"], c.P["bg2"], 90))
    for fx, fy, fr, name, al in st.get("blobs", []):
        c.im.paste(c.P[name][:3], (0, 0, w, h), scale_mask(radial(w, h, fx * w, fy * h, fr * w), al))
    c.d = ImageDraw.Draw(c.im, "RGBA")
    if st.get("dots"):
        for (x, y, cols, rows) in ((c.W - c.m - 6 * 26, c.top + 118, 7, 5), (c.m - 6, c.H * .60, 5, 6)):
            for a in range(cols):
                for b in range(rows):
                    r = c.k * 3.2; cx, cy = (x + a * 26) * c.k, (y + b * 26) * c.k
                    c.d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=c.col("accent", .30 if not st["dark"] else .22))
    if st.get("rings"):
        for rad, al in ((520, .07), (400, .06), (290, .05)):
            cx, cy = c.W * .92 * c.k, c.H * .08 * c.k
            c.d.ellipse((cx - rad * c.k, cy - rad * c.k, cx + rad * c.k, cy + rad * c.k), outline=c.col("accent", al), width=c.k * 2)


def draw_stripe(c):
    if c.st.get("stripe"):
        h = 16
        c.im.paste(grad(c.im.width, h * c.k, c.P["accent2"], mix(c.P["accent2"], (255, 255, 255), .45), 0).resize((c.im.width, h * c.k)), (0, c.im.height - h * c.k))
        c.im.paste(grad(c.im.width, h * c.k, mix(c.P["accent2"], (90, 50, 10), .35), c.P["accent2"], 0), (0, c.im.height - h * c.k))
        # brilho no centro da faixa
        c.im.paste((255, 255, 255), (0, c.im.height - h * c.k, c.im.width, c.im.height), scale_mask(radial(c.im.width, h * c.k, c.im.width * .6, h * c.k / 2, c.im.width * .5, 1.2).resize((c.im.width, h * c.k)), .35))
        c.d = ImageDraw.Draw(c.im, "RGBA")


def ornament(c, cx, y, w, align="c", glyph="heart"):
    """Linha fina dourada com selo no centro (ou no início)."""
    k = c.k; a2 = c.col("accent2")
    if align == "c":
        c.d.line(((cx - w / 2) * k, y * k, (cx - 18) * k, y * k), fill=a2, width=max(2, k * 2))
        c.d.line(((cx + 18) * k, y * k, (cx + w / 2) * k, y * k), fill=a2, width=max(2, k * 2))
        g = IC.glyph(glyph, 24 * k, a2, a2); c.im.paste(g, (int((cx - 12) * k), int((y - 12) * k)), g)
    else:
        x = cx
        g = IC.glyph(glyph, 24 * k, a2, a2); c.im.paste(g, (int(x * k), int((y - 12) * k)), g)
        c.d.line(((x + 36) * k, y * k, (x + w) * k, y * k), fill=a2, width=max(2, k * 2))


# ───────────────────────── selos, cards, formas ─────────────────────────
def shape_mask(size, kind, tail=True):
    """Máscara L (size x size) para 'bubble' (balão), 'round' ou 'square'."""
    S = size * 4; m = Image.new("L", (S, S), 0); d = ImageDraw.Draw(m); pad = S * .08
    if kind == "round":
        d.ellipse((pad, pad, S - pad, S - pad), fill=255)
    else:
        d.rounded_rectangle((pad, pad, S - pad, S - pad * (1.9 if kind == "bubble" else 1)), S * .26, fill=255)
        if kind == "bubble" and tail:
            d.polygon([(S * .24, S * .80), (S * .15, S * .97), (S * .46, S * .84)], fill=255)
            d.line([(S * .24, S * .80), (S * .15, S * .97), (S * .46, S * .84)], fill=255, width=int(S * .03), joint="curve")
    return m.resize((size, size), Image.LANCZOS)


def sticker(c, name, cx, cy, size, rot=0, kind="bubble", tone="accent", shadow=True):
    """Selo 3D (gradiente + brilho + ícone branco com sombra), centrado em (cx,cy)."""
    k = c.k; S = int(size * k); pad = int(S * .35); mk = shape_mask(S, kind)
    base = c.P[tone]; hi = mix(base, (255, 255, 255), .38); lo = mix(base, (0, 0, 0), .20)
    L = Image.new("RGBA", (S + 2 * pad, S + 2 * pad), (0, 0, 0, 0))
    body = grad(S, S, hi, lo, 70).convert("RGBA"); body.putalpha(mk)
    # brilho superior
    gl = Image.new("L", (S, S), 0); ImageDraw.Draw(gl).ellipse((S * .10, S * .02, S * .82, S * .50), fill=95)
    gl = ImageChops_multiply(gl.filter(ImageFilter.GaussianBlur(S * .03)), mk)
    body.paste((255, 255, 255), (0, 0), gl)
    # aro interno
    rim = Image.new("L", (S, S), 0); rd = ImageDraw.Draw(rim)
    rim.paste(mk); inner = mk.filter(ImageFilter.MinFilter(max(3, int(S * .045) | 1)))
    rim = ImageChops_sub(rim, inner); body.paste(hi + (0,)[:0] if False else (255, 255, 255), (0, 0), scale_mask(rim, .35))
    L.paste(body, (pad, pad), body)
    g = IC.glyph(name, int(S * .52), (255, 255, 255, 255), (255, 255, 255, 235))
    gx = pad + (S - g.width) // 2; gy = pad + int(S * (.44 if kind == "bubble" else .5) - g.height / 2)
    sh = Image.new("RGBA", g.size, lo + (0,)); sh.putalpha(scale_mask(g.getchannel("A").filter(ImageFilter.GaussianBlur(S * .012)), .45))
    L.paste(sh, (gx, gy + int(S * .025)), sh); L.paste(g, (gx, gy), g)
    if rot:
        L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    c.put(L, cx - L.width / 2 / k, cy - L.height / 2 / k, (size * .07, size * .09, .38 if shadow else 0, lo) if shadow else None)


def ImageChops_multiply(a, b):
    from PIL import ImageChops
    return ImageChops.multiply(a, b)


def ImageChops_offset(a, dx, dy):
    from PIL import ImageChops
    return ImageChops.offset(a, dx, dy)


def ImageChops_sub(a, b):
    from PIL import ImageChops
    return ImageChops.subtract(a, b)


def badge(c, name, cx, cy, r, variant=None):
    """Círculo-ícone: 'soft' (claro, como nos exemplos) ou 'glass' (escuro)."""
    k = c.k; st = c.st; variant = variant or ("glass" if st["dark"] else "soft"); S = int(2 * r * k); pad = int(S * .3)
    L = Image.new("RGBA", (S + 2 * pad, S + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    mk = shape_mask(S, "round")
    if variant == "soft":
        body = grad(S, S, mix(c.P["soft"], (255, 255, 255), .6), c.P["soft2"], 80).convert("RGBA"); body.putalpha(mk); L.paste(body, (pad, pad), body)
        d.ellipse((pad + 2 * k, pad + 2 * k, pad + S - 2 * k, pad + S - 2 * k), outline=c.col("accent", .22), width=max(2, k * 2))
        g = IC.glyph(name, int(S * .52), c.col("accent"), c.col("accent2"))
    else:
        body = grad(S, S, mix(c.P["bg"], (255, 255, 255), .16), mix(c.P["bg"], (255, 255, 255), .05), 80).convert("RGBA"); body.putalpha(mk); L.paste(body, (pad, pad), body)
        d.ellipse((pad + 2 * k, pad + 2 * k, pad + S - 2 * k, pad + S - 2 * k), outline=c.col("accent2", .45), width=max(2, k * 2))
        g = IC.glyph(name, int(S * .52), c.col("accent"), c.col("accent2"))
    L.paste(g, (pad + (S - g.width) // 2, pad + (S - g.height) // 2), g)
    c.put(L, cx - L.width / 2 / k, cy - L.height / 2 / k, (r * .22, r * .16, .20, c.P["shadow"]))


def card(c, x, y, w, h, r=36, fill=None, line=None, bar=False, shadow=True):
    k = c.k; st = c.st; L = c.layer(w, h); d = ImageDraw.Draw(L)
    f = fill or c.col("card"); ln = line or c.col("card_line")
    d.rounded_rectangle((0, 0, L.width - 1, L.height - 1), r * k, fill=f)
    d.rounded_rectangle((0, 0, L.width - 1, L.height - 1), r * k, outline=ln, width=max(2, k * 2))
    # filete de luz no topo
    d.line((r * k, k * 2, L.width - r * k, k * 2), fill=(255, 255, 255, 120 if not st["dark"] else 50), width=k * 2)
    if bar:
        bm = Image.new("L", L.size, 0); ImageDraw.Draw(bm).rounded_rectangle((0, 0, L.width - 1, L.height - 1), r * k, fill=255)
        stripe = grad(10 * k, L.height, c.P["accent"], c.P["accent2"], 90); sm = Image.new("L", L.size, 0); sm.paste(255, (0, 0, 10 * k, L.height))
        from PIL import ImageChops
        sm = ImageChops.multiply(sm, bm); full = Image.new("RGB", L.size); full.paste(stripe, (0, 0)); L.paste(full, (0, 0), sm)
    c.put(L, x, y, (30, 18, .16 if not st["dark"] else .45, c.P["shadow"]) if shadow else None)


def pill(c, x, y, w, h, fill, outline=None):
    L = c.layer(w, h); d = ImageDraw.Draw(L); k = c.k
    d.rounded_rectangle((0, 0, L.width - 1, L.height - 1), h * k / 2, fill=fill, outline=outline, width=max(2, k * 2) if outline else 0)
    c.put(L, x, y)


# ───────────────────────── texto ─────────────────────────
def norm(w): return re.sub(r"[^\wÀ-ÿ]", "", w).lower()


def rich_tokens(t):
    out = []
    for i, part in enumerate(re.split(r"\*\*(.+?)\*\*", t or "", flags=re.S)):
        for line_i, line in enumerate(part.split("\n")):
            if line_i: out.append(("\n", False))
            out += [(w, i % 2 == 1) for w in line.split()]
    return out


def wrap_rich(c, toks, reg, bold, maxw):
    lines, cur, cw = [], [], 0; sp = c.d.textlength(" ", font=reg)
    for wd, b in toks:
        if wd == "\n":
            lines.append(cur); cur, cw = [], 0; continue
        f = bold if b else reg; w = c.d.textlength(wd, font=f)
        if cur and cw + sp + w > maxw: lines.append(cur); cur, cw = [], 0
        cur.append((wd, b, w)); cw += w + (sp if len(cur) > 1 else 0)
    lines.append(cur)
    return [l for l in lines if l] or [[]]


def paragraph(c, t, x, y, w, size, color, boldc=None, reg="pop_r", bold="pop_s", align="l", lh=1.45, maxh=None, minsize=22, tag=""):
    """Texto com **destaque**; reduz a fonte até caber em maxh. Retorna (y_final, tamanho_usado)."""
    if not (t or "").strip(): return y, size
    toks = rich_tokens(t); s = float(size); k = c.k
    while True:
        fr, fb = c.font(reg, s), c.font(bold, s); L = wrap_rich(c, toks, fr, fb, w * k); H = len(L) * s * lh
        if maxh is None or H <= maxh or s <= minsize: break
        s -= max(1, s * .05)
    if maxh is not None and H > maxh:
        c.warns.append(f"{tag or 'Slide'}: texto longo; reduzido ao mínimo (sugestão: encurtar).")
    sp = c.d.textlength(" ", font=fr)
    for li, line in enumerate(L):
        lw = sum(t_[2] for t_ in line) + sp * (len(line) - 1); by = (y + s * (lh * .5 + .32) + li * s * lh) * k
        xx = x * k if align == "l" else (x * k + (w * k - lw) / 2 if align == "c" else x * k + w * k - lw)
        for wd, b, ww in line:
            c.d.text((xx, by), wd, font=fb if b else fr, fill=(boldc or color) if b else color, anchor="ls"); xx += ww + sp
    return y + len(L) * s * lh, s


def cap_h(c, key, size):
    f = c.font(key, size); b = f.getbbox("H", anchor="ls"); return -b[1] / c.k


def brush_mask(w, h, seed):
    """Máscara de pincel (L) w x h px: bordas irregulares e fibras secas nas pontas."""
    rnd = random.Random(seed); n = 28; ext = int(h * .10)
    m = Image.new("L", (w + 2 * ext, h), 0); d = ImageDraw.Draw(m)
    top = [(ext + i * w / n, rnd.uniform(0, .07 * h)) for i in range(n + 1)]
    bot = [(ext + i * w / n, h - rnd.uniform(0, .07 * h)) for i in range(n + 1)]
    lft = [(rnd.uniform(0, ext * .9) + rnd.uniform(0, ext * .3), h * (j + .5) / 6 + rnd.uniform(-.03, .03) * h) for j in range(6)]
    rgt = [(w + 2 * ext - rnd.uniform(0, ext * .9) - rnd.uniform(0, ext * .3), h * (j + .5) / 6 + rnd.uniform(-.03, .03) * h) for j in range(6)]
    d.polygon(top + rgt + bot[::-1] + lft[::-1], fill=255)
    for _ in range(26):  # fibras
        y = rnd.uniform(.06 * h, .94 * h); left = rnd.random() < .5
        x0 = rnd.uniform(0, ext + w * .10) if left else m.width - rnd.uniform(0, ext + w * .10)
        ln = rnd.uniform(.05, .16) * w; d.line((x0, y, x0 + (ln if left else -ln), y + rnd.uniform(-2, 2)), fill=0, width=max(1, int(h * rnd.uniform(.006, .018))))
    return m.filter(ImageFilter.GaussianBlur(max(.6, h * .004)))


def headline(c, text, hl, x, y, w, size, minsize, maxh, align="c", brush=True, key=None, color=None, tag=""):
    """Título em fonte display. Com brush=True a palavra de destaque ganha pincel + texto claro, em linha própria e maior.
    Retorna (y_final, brush_info)."""
    st = c.st; key = key or st["disp"]; up = st["disp_up"]; k = c.k; gapf = st["gap"]; hs = st["hl_scale"]
    up = up and key == st["disp"]
    t = (text or "").strip(); t = t.upper() if up else t
    if not t: return y, None
    words = t.split(); hset = {norm(h) for h in re.split(r"\s+", (hl or "").strip()) if norm(h)}
    flags = [norm(wd) in hset for wd in words]
    if brush and not any(flags) and len(words) >= 2:   # destaque automático: palavra mais longa entre as 2 últimas
        j = max(range(len(words) - 2, len(words)), key=lambda q: len(norm(words[q]))); flags[j] = True
    # só o 1º grupo destacado vira pincel; depois escolhe-se a palavra-herói entre as restantes
    kinds = []; seen = False; prev = False
    for fl in flags:
        if fl and brush and (not seen or prev): kinds.append("hl"); seen = True
        else: kinds.append("txt")
        prev = fl and kinds[-1] == "hl"
    if brush and st.get("hero") and len(words) >= 3:
        cand = [j for j, wd in enumerate(words) if kinds[j] == "txt" and len(norm(wd)) >= 5 and not (j == 0 and len(words) >= 4)]
        if cand: kinds[max(cand, key=lambda j: (len(norm(words[j])), -j))] = "hero"
    if not brush: kinds = ["hl" if fl else "txt" for fl in flags]
    groups = []
    for wd, kd in zip(words, kinds):
        if groups and groups[-1][1] == kd and kd != "hero": groups[-1][0].append(wd)
        else: groups.append([[wd], kd])
    col_fg = color or c.col("fg"); s = float(size); wpx = w * k
    while True:
        blocks = []; Hh = 0
        for gi, (gw, kd) in enumerate(groups):
            txt = " ".join(gw)
            if kd == "hero":
                sh = s * st.get("hero_scale", 1.2); f = c.font(key, sh)
                while c.d.textlength(txt, font=f) > wpx and sh > s * .6: sh *= .96; f = c.font(key, sh)
                blocks.append(("hero", [txt], sh))
            elif brush and kd == "hl":
                sh = s * hs; f = c.font(key, sh)
                while c.d.textlength(txt, font=f) + sh * k * .5 > wpx and sh > s * .6: sh *= .96; f = c.font(key, sh)
                blocks.append(("hl", [txt], sh))
            else:
                f = c.font(key, s)
                # quebra gulosa com balanceamento simples
                lines, cur = [], ""
                for wd in gw:
                    tt = (cur + " " + wd).strip()
                    if c.d.textlength(tt, font=f) <= wpx or not cur: cur = tt
                    else: lines.append(cur); cur = wd
                lines.append(cur)
                if len(lines) > 1:  # equilibra a última linha
                    lo, hi = wpx * .5, wpx
                    for _ in range(12):
                        mid = (lo + hi) / 2; L2, cu = [], ""
                        for wd in gw:
                            tt = (cu + " " + wd).strip()
                            if c.d.textlength(tt, font=f) <= mid or not cu: cu = tt
                            else: L2.append(cu); cu = wd
                        L2.append(cu)
                        if len(L2) <= len(lines): hi = mid; best = L2
                        else: lo = mid
                    lines = best
                blocks.append(("txt", lines, s))
        # altura
        hh = 0
        for bi, (kind, ls, sz) in enumerate(blocks):
            cp = cap_h(c, key, sz)
            if kind == "hl": hh += cp * 1.62
            else: hh += len(ls) * cp + (len(ls) - 1) * cp * gapf
            if bi < len(blocks) - 1: hh += cp * (gapf + (.22 if kind == "hl" or blocks[bi + 1][0] == "hl" else 0) + (.10 if "hero" in (kind, blocks[bi + 1][0]) else 0))
        if hh <= maxh or s <= minsize: break
        s *= .95
    if hh > maxh: c.warns.append(f"{tag or 'Slide'}: título longo; reduzido ao mínimo (sugestão: encurtar).")
    cy = y; info = None
    for bi, (kind, ls, sz) in enumerate(blocks):
        cp = cap_h(c, key, sz); f = c.font(key, sz)
        if kind == "hl":
            txt = ls[0]; tw_ = c.d.textlength(txt, font=f) / k; padx = sz * .34; bh = cp * 1.62; bw = tw_ + 2 * padx
            bx = x + (w - bw) / 2 if align == "c" else x
            lay = Image.new("RGBA", (int((bw + sz * .6) * k), int(bh * k)), (0, 0, 0, 0))
            bm = brush_mask(int(bw * k), int(bh * k), hash(txt) & 0xffff)
            fillb = grad(bm.width, bm.height, mix(c.P["accent"], (255, 255, 255), .12), mix(c.P["accent"], (0, 0, 0), .16), 0)
            lay.paste(fillb, (0, 0), bm.crop((0, 0, lay.width, bm.height)) if bm.width >= lay.width else bm)
            ld = ImageDraw.Draw(lay); ld.text(((bm.width) / 2, bh * k / 2 + cp * k / 2 - 1), txt, font=f, fill=c.col("brush_text"), anchor="ms")
            lay = lay.rotate(-1.6 if align == "c" else -1.2, resample=Image.BICUBIC, expand=True)
            c.put(lay, bx - sz * .30 - (lay.width / k - (bw + sz * .6)) / 2, cy - (lay.height / k - bh) / 2 + cp * .04, (cp * .10, cp * .12, .30, mix(c.P["accent"], (0, 0, 0), .55)))
            info = (bx, cy, bw, bh); cy += bh
        elif kind == "hero":
            txt = ls[0]; base = cy + cp; lw = c.d.textlength(txt, font=f) / k; xx = x if align == "l" else x + (w - lw) / 2
            pad = int(sz * .2 * k); bx0, by0 = int(xx * k) - pad, int((base - cp) * k) - pad; bw_, bh_ = int(lw * k) + 2 * pad, int(cp * k) + 2 * pad
            tm = Image.new("L", (bw_, bh_), 0); ImageDraw.Draw(tm).text((pad, pad + int(cp * k)), txt, font=f, fill=255, anchor="ls")
            sm = ImageChops_offset(tm.filter(ImageFilter.GaussianBlur(sz * k * .035)), 0, int(sz * k * .05))
            c.im.paste(mix(c.P["accent"], (60, 10, 30), .55), (bx0, by0), scale_mask(sm, .34))
            c.im.paste(grad(bw_, bh_, mix(c.P["accent"], (255, 255, 255), .14), mix(c.P["accent"], (0, 0, 0), .12), 90), (bx0, by0), tm)
            c.d = ImageDraw.Draw(c.im, "RGBA"); cy = base + (cp * gapf if bi < len(blocks) - 1 else 0)
        else:
            for li, ln in enumerate(ls):
                base = cy + cp; lw = c.d.textlength(ln, font=f) / k
                xx = x if align == "l" else (x + (w - lw) / 2 if align == "c" else x + w - lw)
                # em modo 'cor', palavras destacadas ganham a cor de destaque
                if not brush and any(flags):
                    cx_ = xx; sp_ = c.d.textlength(" ", font=f) / k
                    for wd in ln.split():
                        isH = norm(wd) in hset; fk = st.get("hl_font", key) if isH else key; ff = c.font(fk, sz)
                        c.d.text((cx_ * k, base * k), wd, font=ff, fill=c.col("accent") if isH else col_fg, anchor="ls"); cx_ += c.d.textlength(wd, font=ff) / k + sp_
                else:
                    c.d.text((xx * k, base * k), ln, font=f, fill=col_fg, anchor="ls")
                cy = base + (cp * gapf if li < len(ls) - 1 or bi < len(blocks) - 1 else 0)
        if bi < len(blocks) - 1: cy += (cp * (gapf + (.22 if kind == "hl" or blocks[bi + 1][0] == "hl" else 0)) if kind == "hl" else cp * (.22 if blocks[bi + 1][0] == "hl" else 0)) + (cp * .10 if "hero" in (kind, blocks[bi + 1][0]) else 0)
    return cy, info


# ───────────────────────── rodapé e peças comuns ─────────────────────────
def avatar_layer(c, d_px):
    k = c.k; L = Image.new("RGBA", (d_px, d_px), (0, 0, 0, 0)); mk = Image.new("L", (d_px * 3, d_px * 3), 0); ImageDraw.Draw(mk).ellipse((0, 0, d_px * 3 - 1, d_px * 3 - 1), fill=255)
    mk = mk.resize((d_px, d_px), Image.LANCZOS)
    if c.logo is not None:
        im = cover_fit(c.logo.convert("RGB"), d_px, d_px, (.5, .35)); L.paste(im, (0, 0), mk)
    else:
        g = grad(d_px, d_px, mix(c.P["accent"], (255, 255, 255), .2), mix(c.P["accent"], (0, 0, 0), .2), 60); L.paste(g, (0, 0), mk)
        d = ImageDraw.Draw(L); f = c.font("bebas", d_px / k * .56); d.text((d_px / 2, d_px / 2 + d_px * .03), initials(c.brand), font=f, fill=(255, 255, 255, 255), anchor="mm")
    ring = Image.new("RGBA", (d_px, d_px), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse((1, 1, d_px - 2, d_px - 2), outline=c.col("accent2"), width=max(3, int(d_px * .05)))
    L.alpha_composite(ring); return L


def footer(c):
    if not c.brand and c.logo is None: return
    k = c.k; r = 34; L = avatar_layer(c, int(2 * r * k)); x = c.m; yc = c.yc
    c.put(L, x, yc - r, (8, 5, .25, c.P["shadow"]))
    name = c.brand.upper() if c.brand else ""
    tx = x + 2 * r + 20
    sub = c.st.get("tagline", "")
    if name:
        c.text(tx, yc + (-3 if sub else 10), name, "pop_s", 25, c.col("fg", .92), sp=3.2)
    if sub:
        c.text(tx, yc + 26, sub.upper(), "pop_r", 15.5, c.col("muted"), sp=2.4)


def ghost_number(c, n, x, y, align="r"):
    c.ghost(x, y, f"{n:02d}", "bebas", 520, "accent", .085 if not c.st["dark"] else .10, "rs" if align == "r" else "ls")


def label_pill(c, text, cx, y, align="c", icon=None):
    t = (text or "").strip().upper()
    if not t or t.isdigit(): return None
    k = c.k; f = c.font("pop_s", 23); sp = 3.6; w = c.tw(t, f, sp) / k + 56 + (34 if icon else 0); h = 54
    x = cx - w / 2 if align == "c" else cx
    pill(c, x, y, w, h, c.col("accent", .12), c.col("accent", .55))
    tx = x + 28
    if icon:
        g = IC.glyph(icon, int(26 * k), c.col("accent"), c.col("accent2")); c.im.paste(g, (int((x + 24) * k), int((y + 14) * k)), g); tx = x + 24 + 34
    c.text(tx, y + 34, t, "pop_s", 23, c.col("accent"), sp=sp)
    return x, y, w, h


def stage(c, i, n):
    """Linha do topo (pequeno): marca d'água do número e pontos decorativos."""
    pass


def photo_frame(c, img, x, y, w, h, r=44, arch=False, ring=True):
    k = c.k; W_, H_ = int(w * k), int(h * k); pic = cover_fit(img.convert("RGB"), W_, H_)
    m = Image.new("L", (W_ * 2, H_ * 2), 0); md = ImageDraw.Draw(m)
    if arch: md.rounded_rectangle((0, 0, W_ * 2 - 1, H_ * 2 - 1), W_ * .5 * 2 * (1 if W_ < H_ else .3), fill=255); md.rectangle((0, H_ * 2 * .55, W_ * 2, H_ * 2), fill=0); md.rounded_rectangle((0, H_ * 2 * .45, W_ * 2 - 1, H_ * 2 - 1), r * 2 * k, fill=255)
    else: md.rounded_rectangle((0, 0, W_ * 2 - 1, H_ * 2 - 1), r * k * 2, fill=255)
    m = m.resize((W_, H_), Image.LANCZOS)
    L = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); L.paste(pic, (0, 0), m)
    if ring:
        ov = Image.new("RGBA", (W_, H_), (0, 0, 0, 0)); ImageDraw.Draw(ov).rounded_rectangle((k * 2, k * 2, W_ - k * 2, H_ - k * 2), r * k, outline=(255, 255, 255, 130), width=k * 3)
        ov.putalpha(ImageChops_multiply(ov.getchannel("A"), m)); L.alpha_composite(ov)
    c.put(L, x, y, (34, 24, .34 if not c.st["dark"] else .6, c.P["shadow"]))


def orbit(c, cx, cy, r, n=3):
    k = c.k
    for i in range(n):
        rr = r * (1 + i * .38)
        c.d.ellipse(((cx - rr) * k, (cy - rr) * k, (cx + rr) * k, (cy + rr) * k), outline=c.col("accent", .20 - i * .05), width=k * 2)


def phone(c, cx, top, w, rot=-6, icon="heart", clip_y=None):
    """Mockup de celular (corpo escuro, tela clara com um post de Instagram desenhado). Pode ser cortado por clip_y com esmaecimento."""
    k = c.k; h = w * 1.92; Wp, Hp = int(w * k), int(h * k); pad = int(w * .22 * k)
    L = Image.new("RGBA", (Wp + 2 * pad, Hp + 2 * pad), (0, 0, 0, 0)); d = ImageDraw.Draw(L)
    r = int(w * .15 * k); mk = Image.new("L", (Wp, Hp), 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, Wp - 1, Hp - 1), r, fill=255)
    light = c.st.get("phone_light")
    body = (grad(Wp, Hp, mix(c.P["accent"], (255, 255, 255), .58), mix(c.P["accent"], (255, 255, 255), .08), 62) if light else grad(Wp, Hp, (62, 58, 72), (12, 11, 17), 62)); L.paste(body, (pad, pad), mk)
    rim = Image.new("RGBA", (Wp, Hp), (0, 0, 0, 0)); ImageDraw.Draw(rim).rounded_rectangle((k, k, Wp - k - 1, Hp - k - 1), r, outline=(255, 255, 255, 150 if light else 70), width=max(2, k * 2)); L.alpha_composite(rim, (pad, pad))
    b = int(w * .034 * k); sw, sh = Wp - 2 * b, Hp - 2 * b; sr = max(4, r - b)
    scr = Image.new("RGB", (sw, sh), (251, 249, 249)); sd = ImageDraw.Draw(scr, "RGBA"); u = sw / 100.0
    a0 = c.P["accent"]
    av = int(11 * u); sd.ellipse((7 * u, 15 * u, 7 * u + av, 15 * u + av), fill=mix(a0, (255, 255, 255), .1))
    sd.rounded_rectangle((7 * u + av + 3 * u, 17.2 * u, 7 * u + av + 33 * u, 20.4 * u), 2 * u, fill=(40, 38, 46, 255)); sd.rounded_rectangle((7 * u + av + 3 * u, 22.6 * u, 7 * u + av + 21 * u, 24.8 * u), 2 * u, fill=(190, 186, 194, 255))
    my0, my1 = 30 * u, 30 * u + 86 * u
    med = grad(int(86 * u), int(86 * u), mix(a0, (255, 255, 255), .22), mix(a0, (0, 0, 0), .12), 60)
    mm = Image.new("L", med.size, 0); ImageDraw.Draw(mm).rounded_rectangle((0, 0, med.width - 1, med.height - 1), int(6 * u), fill=255); scr.paste(med, (int(7 * u), int(my0)), mm)
    g = IC.glyph(icon, int(46 * u), (255, 255, 255, 255), (255, 255, 255, 235)); scr.paste(g, (int(7 * u + (86 * u - g.width) / 2), int(my0 + (86 * u - g.height) / 2)), g)
    sp1 = IC.glyph("sparkle", int(14 * u), (255, 255, 255, 190), (255, 255, 255, 190)); scr.paste(sp1, (int(7 * u + 62 * u), int(my0 + 10 * u)), sp1)
    ay = my1 + 7 * u
    for q, nm in enumerate(("heart", "chat", "send")):
        col_ = (tuple(a0) + (255,)) if q == 0 else (46, 42, 52, 255)
        gi = IC.glyph(nm, int(9.5 * u), col_, col_); scr.paste(gi, (int(7 * u + q * 12.5 * u), int(ay)), gi)
    for q, wd in enumerate((78, 56, 68)):
        sd.rounded_rectangle((7 * u, ay + 17 * u + q * 6.2 * u, 7 * u + wd * u * .9, ay + 17 * u + q * 6.2 * u + 3 * u), 1.6 * u, fill=(206, 202, 210, 255) if q else (70, 66, 76, 255))
    sm = Image.new("L", (sw, sh), 0); ImageDraw.Draw(sm).rounded_rectangle((0, 0, sw - 1, sh - 1), sr, fill=255)
    gl = Image.new("L", (sw, sh), 0); ImageDraw.Draw(gl).polygon([(0, 0), (sw * .62, 0), (sw * .18, sh * .62), (0, sh * .62)], fill=34)
    scr.paste((255, 255, 255), (0, 0), ImageChops_multiply(gl.filter(ImageFilter.GaussianBlur(sw * .02)), sm))
    L.paste(scr, (pad + b, pad + b), sm)
    d.rounded_rectangle((pad + Wp * .5 - w * k * .13, pad + b * 1.9, pad + Wp * .5 + w * k * .13, pad + b * 1.9 + w * k * .05), w * k * .03, fill=(tuple(mix(c.P["accent"], (0, 0, 0), .45)) + (255,)) if light else (8, 8, 12, 255))
    if rot: L = L.rotate(rot, resample=Image.BICUBIC, expand=True)
    X, Y = cx - L.width / 2 / k, top - (L.height - Hp - 2 * pad) / 2 / k - pad / k
    if clip_y is not None:
        vh = int((clip_y - Y) * k)
        if vh < L.height:
            L = L.crop((0, 0, L.width, max(2, vh))); a = np.asarray(L.getchannel("A"), dtype=np.float32)
            fh = min(L.height, int(w * k * .55)); ramp = np.ones(L.height, dtype=np.float32); ramp[-fh:] = np.linspace(1, 0, fh) ** 1.4
            L.putalpha(Image.fromarray((a * ramp[:, None]).astype("uint8"), "L"))
    c.put(L, X, Y, (w * .10, w * .07, .42 if c.st["dark"] else .30, c.P["shadow"]))
    return X, Y, L.width / k, L.height / k


def header(c):
    """Linha discreta no topo: marca à esquerda, contador à direita."""
    if c.n < 2: return
    y = c.top + 58; m = c.m
    name = (c.st.get("header_left") or c.brand or c.st.get("tagline", "")).upper()
    on_photo = getattr(c, "full_photo", False); tc = (255, 255, 255, 235) if on_photo else c.col("muted")
    if on_photo: c.d.rectangle((0, 0, c.im.width, int((y + 40) * c.k)), fill=(0, 0, 0, 70))
    if name: c.text(m, y, name, "pop_m", 19, tc, sp=3.4)
    c.text(c.W - m, y, f"{c.i + 1:02d} / {c.n:02d}", "pop_m", 19, tc, anchor="rs", sp=3.4)
    c.d.line((m * c.k, (y + 18) * c.k, (c.W - m) * c.k, (y + 18) * c.k), fill=(255, 255, 255, 80) if on_photo else c.col("muted", .22), width=max(2, c.k))


def L_passos(c, s, img):
    m, W, k = c.m, c.W, c.k; cw = W - 2 * m; y = c.y0
    label_pill(c, s.label, m, y, "l", s.icon or None); y += 92
    yh, _ = headline(c, s.headline, s.highlight, m, y, cw, 112, 64, (c.y1 - y) * .30, "l", False, tag=f"Slide {c.i + 1}")
    y = yh + 36
    items = [it for it in s.items if it.label or it.text][:4]
    if not items: return L_texto(c, s, img)
    n = len(items); zone = c.y1 - y; step = min(250, zone / n); r = 44; x0 = m + r
    c.d.line((x0 * k, (y + r) * k, x0 * k, (y + (n - 1) * step + r) * k), fill=c.col("accent", .55), width=k * 5)
    for q, it in enumerate(items):
        cy = y + q * step + r
        halo = c.layer(r * 4, r * 4); ImageDraw.Draw(halo).ellipse((r * k, r * k, 3 * r * k, 3 * r * k), fill=c.col("accent", .30)); c.put(halo.filter(ImageFilter.GaussianBlur(r * k * .45)), x0 - 2 * r, cy - 2 * r)
        L = c.layer(2 * r, 2 * r); mk = shape_mask(int(2 * r * k), "round"); L.paste(grad(L.width, L.height, mix(c.P["accent"], (255, 255, 255), .30), mix(c.P["accent"], (0, 0, 0), .18), 70), (0, 0), mk)
        ImageDraw.Draw(L).ellipse((k * 2, k * 2, L.width - k * 2, L.height - k * 2), outline=(255, 255, 255, 120), width=k * 2); c.put(L, x0 - r, cy - r, (r * .25, r * .18, .45, mix(c.P["accent"], (0, 0, 0), .55)))
        c.text(x0, cy + cap_h(c, "bebas", 58) / 2, f"{q + 1}", "bebas", 58, (255, 255, 255, 255), anchor="ms")
        tx = x0 + r + 38; tw_ = W - m - tx
        yy, _ = paragraph(c, it.label, tx, cy - r + 2, tw_, 38, c.col("fg"), c.col("accent"), reg="pop_s", bold="pop_s", lh=1.2, maxh=56, minsize=26, tag=f"Slide {c.i + 1}")
        if it.text: paragraph(c, it.text, tx, yy + 4, tw_, 30, c.col("muted"), c.col("accent"), lh=1.38, maxh=step - 70, minsize=21, tag=f"Slide {c.i + 1}")


# ───────────────────────── layouts ─────────────────────────
def L_capa(c, s, img):
    st, m, W, k = c.st, c.m, c.W, c.k; cw = W - 2 * m; y = c.y0
    label_pill(c, s.label, W / 2, y + 4, icon=s.icon or None)
    y += 96
    avail = c.y1 - y
    yh, info = headline(c, s.headline, s.highlight, m, y, cw, 190 if img is not None else 150, 96 if img is not None else 84, avail * (.44 if img is not None else .47), "c", True, tag=f"Slide {c.i + 1}")
    y = yh + 30
    ornament(c, W / 2, y, 300); y += 34
    if s.subhead.strip():
        y, _ = paragraph(c, s.subhead, m + 20, y, cw - 40, 36, c.col("body"), c.col("accent"), align="c", lh=1.4, maxh=150, tag=f"Slide {c.i + 1}")
        y += 6
    zone0, zone1 = y + 20, c.y1 + 34; zh = zone1 - zone0
    items = [it for it in s.items if it.label or it.text][:4]
    if zh < 150: return
    if img is not None:
        pw = min(560, cw - 120); ph = min(zh, 520)
        px = (W - pw) / 2; py = zone1 - ph
        photo_frame(c, img, px, py, pw, ph, 44, arch=True)
        sticker(c, s.icon or "heart", px - 10, py + ph * .30, 150, -9, "bubble")
        sticker(c, IC.pick_icon(s.headline, "sparkle") if not s.icon else "sparkle", px + pw + 6, py + ph * .70, 126, 10, "round", "accent2")
    elif items:
        n = len(items); by = zone0 + min(zh * .42, 130)
        for q, it in enumerate(items):
            cx = m + cw * (q + .5) / n; badge(c, it.icon or IC.pick_icon(it.label), cx, by, 78)
            if it.label: c.text(cx, by + 128, it.label, "pop_m", 29, c.col("fg"), anchor="ms")
    else:
        cx = W / 2; pw = min(400, max(250, zh * .78)); main = s.icon or IC.pick_icon(s.headline + " " + s.subhead, "sparkle")
        orbit(c, cx, zone0 + zh * .55, pw * .58, 3)
        X, Y, lw, lh_ = phone(c, cx, zone0 + 6, pw, -6, main, clip_y=zone1)
        vis = min(lh_ + Y, zone1) - Y
        sticker(c, "heart", cx - pw * .62, Y + vis * .34, min(150, pw * .40), -12, "bubble")
        sticker(c, "chat", cx + pw * .64, Y + vis * .62, min(132, pw * .36), 11, "bubble", "accent2")
        sticker(c, IC.pick_icon(s.headline, "growth") if main != "growth" else "star", cx + pw * .56, Y + vis * .20, min(96, pw * .26), 8, "round")


def L_capa_foto(c, s, img):
    m, W, H, k = c.m, c.W, c.H, c.k
    if img is not None:
        pic = cover_fit(img.convert("RGB"), c.im.width, c.im.height, (.5, .35)); c.im.paste(pic, (0, 0))
    ov = Image.new("L", (1, c.im.height), 0)
    a = np.clip((np.linspace(0, 1, c.im.height) - .28) / .55, 0, 1) ** 1.25 * 245 + np.clip(1 - np.linspace(0, 1, c.im.height) / .2, 0, 1) * 70
    ov = Image.fromarray(a.astype("uint8").reshape(-1, 1), "L").resize((c.im.width, c.im.height))
    c.im.paste(c.P["bg"], (0, 0, c.im.width, c.im.height), ov); c.d = ImageDraw.Draw(c.im, "RGBA")
    label_pill(c, s.label, m, c.y0 + 4, "l", s.icon or None)
    yb = c.y1 + 10
    ytop = c.H * .50
    yh, info = headline(c, s.headline, s.highlight, m, ytop, W - 2 * m, 170, 90, (yb - ytop) * .66, "l", True, tag=f"Slide {c.i + 1}")
    ornament(c, m, yh + 30, 240, "l"); y = yh + 60
    if s.subhead.strip():
        paragraph(c, s.subhead, m, y, W - 2 * m - 60, 36, c.col("fg", .95), c.col("accent2"), align="l", lh=1.42, maxh=max(80, yb - y), tag=f"Slide {c.i + 1}")


def L_texto(c, s, img):
    st, m, W, k = c.st, c.m, c.W, c.k; cw = W - 2 * m
    ghost_number(c, c.i + 1, W - m + 20, c.y0 + 400)
    y = c.y0
    label_pill(c, s.label, m, y, "l", s.icon or None)
    y += 92
    hmax = (c.y1 - y) * .40
    yh, _ = headline(c, s.headline, s.highlight, m, y, cw - 40, 122, 70, hmax, "l", False, tag=f"Slide {c.i + 1}")
    ornament(c, m, yh + 38, 200, "l"); yh += 70
    body_h = 0
    text_top = yh + 10; avail = c.y1 - text_top - 20
    sub, body = s.subhead.strip(), s.body.strip()
    if sub or body:
        pad = 46
        # mede
        ys = text_top + pad; yb_ = ys
        sizes = (44, 38)
        # simula para saber a altura: desenha em canvas temporário? usa estimativa via wrap
        def est(tx, size, w, lh):
            fr, fb = c.font("pop_r", size), c.font("pop_s", size); return len(wrap_rich(c, rich_tokens(tx), fr, fb, w * k)) * size * lh
        iw = cw - 2 * pad - 12
        hs_ = est(sub, 44, iw, 1.34) + (22 if sub and body else 0) if sub else 0
        hb_ = est(body, 38, iw, 1.5) if body else 0
        ch = min(avail, hs_ + hb_ + 2 * pad); ch = max(ch, 220)
        # centraliza verticalmente o conjunto (título + card) quando sobra espaço
        extra = max(0, avail - ch) * .35
        if extra > 8:
            pass
        cy0 = text_top + extra * .6
        card(c, m, cy0, cw, ch, 38, bar=True)
        yy = cy0 + pad
        if sub:
            yy, _ = paragraph(c, sub, m + pad + 12, yy, iw, 44, c.col("fg"), c.col("accent"), reg="pop_m", bold="pop_s", lh=1.34, maxh=ch - 2 * pad, tag=f"Slide {c.i + 1}"); yy += 22
        if body:
            paragraph(c, body, m + pad + 12, yy, iw, 38, c.col("body"), c.col("accent"), lh=1.5, maxh=cy0 + ch - pad - yy, tag=f"Slide {c.i + 1}")
        ic = s.icon or IC.pick_icon(s.headline + " " + s.body, "star")
        sticker(c, ic, W - m - 70, cy0 + ch - 8, 150, -8, "bubble")
        # espaço restante: faixa de ícones secundários
        rest = c.y1 - (cy0 + ch)
        if rest > 230 and img is None:
            by = cy0 + ch + rest * .52
            orbit(c, m + 170, by, 80, 2)
            badge(c, IC.pick_icon(s.label + s.headline, "sparkle"), m + 170, by, 80)
            sticker(c, "heart", W - m - 190, by + 10, 120, 10, "round", "accent2")
    else:
        sticker(c, s.icon or "sparkle", W / 2, (yh + c.y1) / 2, 300, 0, "round")


def L_lista(c, s, img):
    m, W, k = c.m, c.W, c.k; cw = W - 2 * m; y = c.y0
    label_pill(c, s.label, m, y, "l", s.icon or None); y += 92
    yh, _ = headline(c, s.headline, s.highlight, m, y, cw, 112, 64, (c.y1 - y) * .30, "l", False, tag=f"Slide {c.i + 1}")
    y = yh + 24
    if s.subhead.strip():
        y, _ = paragraph(c, s.subhead, m, y, cw, 34, c.col("body"), c.col("accent"), lh=1.4, maxh=130, tag=f"Slide {c.i + 1}"); y += 10
    items = [it for it in s.items if it.label or it.text][:4] or []
    if not items:
        return L_texto(c, s, img)
    n = len(items); gap = 22; hh = min(285, (c.y1 - y - gap * (n - 1) + 10) / n)
    for q, it in enumerate(items):
        cy0 = y + q * (hh + gap)
        card(c, m, cy0, cw, hh, 34)
        r = min(66, hh * .30); bx = m + 36 + r
        badge(c, it.icon or IC.pick_icon(it.label + " " + it.text), bx, cy0 + hh / 2, r)
        c.ghost(m + cw - 30, cy0 + hh / 2 + 36, f"{q + 1:02d}", "bebas", 100, "accent", .16, "rs")
        tx = bx + r + 30; tw_ = cw - (tx - m) - 120
        yy = cy0 + (hh - (40 + (62 if it.text else 0))) / 2 if it.text else cy0 + hh / 2 - 20
        yy2, _ = paragraph(c, it.label, tx, yy, tw_, 36, c.col("fg"), c.col("accent"), reg="pop_s", bold="pop_s", lh=1.2, maxh=50, minsize=24, tag=f"Slide {c.i + 1}")
        if it.text: paragraph(c, it.text, tx, yy2 + 4, tw_, 29, c.col("muted"), c.col("accent"), lh=1.38, maxh=hh - (yy2 - cy0) - 22, minsize=20, tag=f"Slide {c.i + 1}")


def L_icones(c, s, img):
    m, W, k = c.m, c.W, c.k; cw = W - 2 * m; y = c.y0
    label_pill(c, s.label, W / 2, y + 4, icon=s.icon or None); y += 100
    yh, _ = headline(c, s.headline, s.highlight, m, y, cw, 130, 70, (c.y1 - y) * .32, "c", False, tag=f"Slide {c.i + 1}")
    y = yh + 42; ornament(c, W / 2, y, 280); y += 36
    if s.body.strip() or s.subhead.strip():
        y, _ = paragraph(c, s.body.strip() or s.subhead.strip(), m + 30, y, cw - 60, 36, c.col("body"), c.col("accent"), align="c", lh=1.45, maxh=260, tag=f"Slide {c.i + 1}"); y += 20
    items = [it for it in s.items if it.label or it.text][:4]
    if not items:
        sticker(c, s.icon or "sparkle", W / 2, (y + c.y1) / 2, 260, 0, "round"); return
    n = len(items); zone = c.y1 - y; by = y + zone * .40
    for q, it in enumerate(items):
        cx = m + cw * (q + .5) / n; r = min(106, cw / n * .40)
        orbit(c, cx, by, r * 1.12, 2) if n <= 3 else None
        badge(c, it.icon or IC.pick_icon(it.label), cx, by, r)
        yy, _ = paragraph(c, it.label, cx - cw / n / 2 + 6, by + r + 30, cw / n - 12, 34, c.col("fg"), c.col("accent"), reg="pop_s", bold="pop_s", align="c", lh=1.15, maxh=92, minsize=22, tag=f"Slide {c.i + 1}")
        if it.text: paragraph(c, it.text, cx - cw / n / 2 + 14, yy + 8, cw / n - 28, 27, c.col("muted"), align="c", lh=1.35, maxh=120, minsize=18, tag=f"Slide {c.i + 1}")


def L_foto(c, s, img):
    m, W, k = c.m, c.W, c.k; cw = W - 2 * m; y = c.y0
    ph = (c.y1 - y) * .47
    if img is not None:
        photo_frame(c, img, m, y, cw, ph, 46)
    else:
        L = c.layer(cw, ph); d = ImageDraw.Draw(L); mk = Image.new("L", L.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, L.width - 1, L.height - 1), 46 * k, fill=255)
        L.paste(grad(L.width, L.height, mix(c.P["accent"], (255, 255, 255), .25), mix(c.P["accent"], (0, 0, 0), .25), 60), (0, 0), mk)
        c.put(L, m, y, (30, 22, .3, c.P["shadow"]))
        g = IC.glyph(s.icon or IC.pick_icon(s.headline, "camera"), int(ph * .42 * k), (255, 255, 255, 235), (255, 255, 255, 235)); c.im.paste(g, (int((W / 2) * k - g.width / 2), int((y + ph / 2) * k - g.height / 2)), g)
    sticker(c, s.icon or IC.pick_icon(s.headline + s.body, "heart"), W - m - 30, y + ph, 150, 9, "bubble")
    ny = y + ph + 52
    label_pill(c, s.label, m, ny - 6, "l"); ny += 70
    yh, _ = headline(c, s.headline, s.highlight, m, ny, cw - 60, 100, 60, (c.y1 - ny) * .42, "l", False, tag=f"Slide {c.i + 1}")
    y2 = yh + 38
    ornament(c, m, y2, 180, "l"); y2 += 34
    t = (s.body.strip() or s.subhead.strip())
    if t: paragraph(c, t, m, y2, cw, 34, c.col("body"), c.col("accent"), lh=1.45, maxh=max(90, c.y1 - y2), tag=f"Slide {c.i + 1}")


def L_citacao(c, s, img):
    m, W, H, k = c.m, c.W, c.H, c.k; cw = W - 2 * m
    c.ghost(W / 2, c.y0 + 560, "“", "pf_b", 620, "accent", .16, "ms")
    label_pill(c, s.label, W / 2, c.y0 + 4, icon=s.icon or None)
    y = c.y0 + 190
    key = c.st.get("quote_font", "pf_i")
    c.st["_q"] = True
    yh, _ = headline(c, s.headline, s.highlight, m + 10, y, cw - 20, 112, 56, (c.y1 - y) * .60, "c", False, key=key, tag=f"Slide {c.i + 1}")
    y = yh + 36; ornament(c, W / 2, y, 260); y += 40
    t = s.subhead.strip() or s.body.strip()
    if t: y, _ = paragraph(c, t, m + 40, y, cw - 80, 36, c.col("body"), c.col("accent"), align="c", lh=1.45, maxh=(c.y1 - y), tag=f"Slide {c.i + 1}")
    sticker(c, s.icon or "heart", W / 2, min(c.y1 - 70, y + 120), 140, 0, "round")


def L_cta(c, s, img):
    m, W, k = c.m, c.W, c.k; cw = W - 2 * m; y = c.y0
    label_pill(c, s.label or "PRÓXIMO PASSO", W / 2, y + 4, icon=s.icon or "send"); y += 100
    yh, info = headline(c, s.headline, s.highlight, m, y, cw, 160, 72, (c.y1 - y) * .52, "c", True, tag=f"Slide {c.i + 1}")
    y = yh + 40; ornament(c, W / 2, y, 300); y += 38
    t = s.subhead.strip() or s.body.strip()
    if t: y, _ = paragraph(c, t, m + 30, y, cw - 60, 36, c.col("body"), c.col("accent"), align="c", lh=1.42, maxh=190, tag=f"Slide {c.i + 1}"); y += 24
    # botão
    cta = s.cta.strip() or "Fale com a gente"
    bh = 104; f = c.font("pop_s", 36); tw_ = c.tw(cta, f) / k; bw = min(cw, tw_ + 150 + 70)
    zone = c.y1 - y
    by = y + max(10, min(40, zone * .12)); bx = (W - bw) / 2
    L = c.layer(bw, bh); d = ImageDraw.Draw(L); mk = Image.new("L", L.size, 0); ImageDraw.Draw(mk).rounded_rectangle((0, 0, L.width - 1, L.height - 1), bh * k / 2, fill=255)
    L.paste(grad(L.width, L.height, mix(c.P["accent"], (255, 255, 255), .15), mix(c.P["accent"], (0, 0, 0), .15), 0), (0, 0), mk)
    d.rounded_rectangle((k * 2, k * 2, L.width - k * 2, L.height * .5), bh * k / 2, outline=None, fill=None)
    # círculo com seta
    cr = bh * .34; ccx, ccy = (bw - bh * .5) * k, bh * k / 2
    d.ellipse((ccx - cr * k, ccy - cr * k, ccx + cr * k, ccy + cr * k), fill=(255, 255, 255, 255))
    ar = [(ccx - cr * k * .42, ccy), (ccx + cr * k * .38, ccy)]
    d.line(ar, fill=c.col("accent"), width=int(k * 5)); d.line([(ccx + cr * k * .02, ccy - cr * k * .36), (ccx + cr * k * .40, ccy), (ccx + cr * k * .02, ccy + cr * k * .36)], fill=c.col("accent"), width=int(k * 5), joint="curve")
    d.text((bh * k * .50 + 8, bh * k / 2 + 1), cta, font=f, fill=c.col("brush_text"), anchor="lm")
    c.put(L, bx, by, (26, 18, .42, mix(c.P["accent"], (0, 0, 0), .5)))
    # linha de ações de engajamento
    ey = by + bh + (c.y1 - (by + bh)) * .55
    if c.y1 - (by + bh) > 190:
        acts = [("heart", "Curta"), ("chat", "Comente"), ("send", "Envie"), ("bookmark", "Salve")]
        for q, (ic, lb) in enumerate(acts):
            cx = m + cw * (q + .5) / 4; badge(c, ic, cx, ey - 14, 46)
            c.text(cx, ey + 64, lb, "pop_m", 25, c.col("muted"), anchor="ms")


LAY = {"capa": L_capa, "capa_foto": L_capa_foto, "texto": L_texto, "lista": L_lista, "icones": L_icones, "passos": L_passos, "foto": L_foto, "citacao": L_citacao, "cta": L_cta}
BALANCE = {"icones", "citacao", "cta", "passos", "lista", "texto"}


def auto_layout(i, n, s, has_img):
    if i == 0: return "capa"
    if i == n - 1 and n > 2: return "cta"
    items = [it for it in s.items if it.label or it.text]
    if len(items) >= 2: return "lista" if any(it.text for it in items) else "icones"
    if has_img: return "foto"
    if not s.body.strip() and s.subhead.strip() and len(s.headline.split()) >= 4: return "citacao"
    return "texto"


# ───────────────────────── renderização ─────────────────────────
_CACHE = OrderedDict()


def _h(b): return hashlib.md5(b).hexdigest() if b else ""


def render_slide(i, n, s, fmt, st, brand, imgs, logo):
    img_b = imgs[s.image] if s.image is not None and 0 <= s.image < len(imgs) else None
    key = (i, n, s.model_dump_json(), fmt, st["name"], brand, _h(img_b), _h(logo))
    if key in _CACHE:
        _CACHE.move_to_end(key); im, w = _CACHE[key]; return im.copy(), list(w)
    img = Image.open(io.BytesIO(img_b)).convert("RGB") if img_b else None
    lay = s.layout if s.layout in LAY else auto_layout(i, n, s, img is not None)
    if lay == "capa_foto" and img is None: lay = "capa"
    st = {**st, **st.get("alt", {}).get(lay, {})}   # ex.: slide de citação com fundo terracota e serifa
    c = Cv(fmt, st, i, n, brand, Image.open(io.BytesIO(logo)).convert("RGB") if logo else None)
    draw_bg(c); bg = c.im.copy(); dy = 0
    if lay in BALANCE:   # 1ª passada só mede onde termina o conteúdo; depois o bloco é centralizado na área útil
        c.measure = True; LAY[lay](c, s, img); c.measure = False; c.warns.clear()
        diff = ImageChops.difference(c.im, bg).convert("L").point(lambda v: 255 if v > 14 else 0).getbbox()
        if diff:
            top_, bot_ = diff[1] / c.k, diff[3] / c.k; free = (c.y1 - bot_) - (top_ - c.y0)
            dy = max(0, min(free * .46, (c.y1 - bot_) * .9)) if (c.y1 - bot_) > 70 else 0
        c.im = bg.copy(); c.d = ImageDraw.Draw(c.im, "RGBA")
    LAY[lay](c, s, img)
    if dy > 4:
        Y = int(round(dy * c.k)); m_ = ImageChops.difference(c.im, bg).convert("L").point(lambda v: min(255, v * 48)).filter(ImageFilter.GaussianBlur(c.k))
        moved = bg.copy(); moved.paste(c.im, (0, Y), m_); c.im = moved; c.d = ImageDraw.Draw(c.im, "RGBA")
    c.full_photo = (lay == "capa_foto" and img is not None); header(c); footer(c); draw_stripe(c)
    out = c.im.resize((c.W, c.H), Image.LANCZOS)
    g = st.get("grain", 2.2)
    if g:
        a = np.asarray(out, dtype=np.float32); rng = np.random.default_rng(7); a += rng.normal(0, g, a.shape[:2])[..., None]
        out = Image.fromarray(np.clip(a, 0, 255).astype("uint8"), "RGB")
    _CACHE[key] = (out, c.warns)
    while len(_CACHE) > 300: _CACHE.popitem(last=False)
    return out.copy(), list(c.warns)


def render_studio(slides, fmt, tpl, brand, imgs=(), logo=None):
    st = dict(tpl["style"]); st["name"] = tpl["name"]; n = len(slides); ims, W = [], []
    if logo is None and tpl.get("logo"):
        p = Path(__file__).parent / tpl["logo"]
        if p.exists(): logo = p.read_bytes()
    for i, s in enumerate(slides):
        im, w = render_slide(i, n, s, fmt, st, brand or tpl.get("handle", ""), list(imgs), logo)
        ims.append(im); W += w
    return ims, W
