"""Studio · Terra Editorial: terracota quente, creme e serifa itálica."""
TEMPLATE = dict(
    name="Studio · Terra Editorial", engine="studio", handle="",
    style=dict(
        dark=True, bg="#8E4D2D", bg2="#4F2616", fg="#FBEBD6", body="#F1D9BE", muted="#D9B896",
        accent="#F3C98F", accent2="#FFE3B8", soft="#A8603C", soft2="#7A3C22", card=(255, 240, 220, 26), card_line=(255, 226, 190, 70),
        shadow="#1E0B04", brush_text="#4F2616",
        disp="pf_r", disp_up=False, gap=.62, hl_scale=1.0, hl_font="pf_i", quote_font="pf_i",
        blobs=[(.9, .08, .6, "accent", .17), (.05, .95, .5, "accent2", .10)],
        dots=False, rings=True, stripe=False, grain=3.0, tagline="",
    ),
)
