"""LC Digital: único visual do sistema. Creme-pêssego, título condensado, palavra-herói rosa, pincel rosa com letra branca,
selos 3D, celular rosa, ornamento e barra dourados. O slide de citação usa a variante terracota com serifa (como no feed)."""
TEMPLATE = dict(
    name="LC Digital", engine="studio", handle="LC Digital", logo="assets/lc_logo.png",
    style=dict(
        dark=False, bg="#FFF6EE", bg2="#FBE6DC", fg="#1E1416", body="#4A3A3E", muted="#8E7479",
        accent="#DB4F7F", accent2="#D9A441", soft="#FFE3E4", soft2="#FAC9D2", card=(255, 255, 255, 205), card_line=(219, 79, 127, 44),
        shadow="#B8506A", brush_text="#FFFFFF",
        disp="anton", disp_up=True, gap=.30, hl_scale=1.08, hl_font="anton", hero=True, hero_scale=1.3,
        blobs=[(.98, .04, .50, "accent", .22), (.04, .96, .46, "accent", .13), (.97, .72, .36, "soft2", .55), (.5, .5, .8, "soft", .30)],
        dots=True, stripe=True, grain=1.6, tagline="GESTÃO DE REDES SOCIAIS", header_left="@lcdigital.mkt", phone_light=True,
        alt=dict(citacao=dict(
            dark=True, bg="#9A512F", bg2="#52271A", fg="#FBEBD6", body="#F1D9BE", muted="#D9B896", accent="#F3C98F", accent2="#FFE3B8",
            soft="#A8603C", soft2="#7A3C22", card=(255, 240, 220, 26), card_line=(255, 226, 190, 70), shadow="#1E0B04", brush_text="#52271A",
            disp="pf_r", disp_up=False, gap=.62, hl_scale=1.0, hl_font="pf_i", quote_font="pf_i", hero=False,
            blobs=[(.9, .08, .6, "accent", .17), (.05, .95, .5, "accent2", .10)], dots=False, rings=True, stripe=False, grain=3.0, phone_light=False)),
    ),
)
