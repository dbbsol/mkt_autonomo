"""Studio · Noir Dourado: preto profundo, dourado e serifa clássica (autoridade e premium)."""
TEMPLATE = dict(
    name="Studio · Noir Dourado", engine="studio", handle="",
    style=dict(
        dark=True, bg="#0B0B10", bg2="#17141A", fg="#F6F0E4", body="#CFC7B8", muted="#8D8678",
        accent="#D6B25E", accent2="#F0D79A", soft="#2A2418", soft2="#171309", card=(255, 255, 255, 12), card_line=(214, 178, 94, 70),
        shadow="#000000", brush_text="#16120A",
        disp="pf_b", disp_up=False, gap=.62, hl_scale=1.0, hl_font="pf_i", quote_font="pf_i",
        blobs=[(.9, .05, .55, "accent", .16), (.1, .95, .45, "accent", .09)],
        dots=False, rings=True, stripe=True, grain=2.6, tagline="",
    ),
)
