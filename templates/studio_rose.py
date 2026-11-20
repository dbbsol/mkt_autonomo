"""Studio · Rosé Creme: claro, rosé + dourado, título condensado com pincel (estilo editorial de social media)."""
TEMPLATE = dict(
    name="Studio · Rosé Creme", engine="studio", handle="",
    style=dict(
        dark=False, bg="#FCF3EC", bg2="#F9E3D9", fg="#2A1914", body="#5B4640", muted="#8C746C",
        accent="#E8507C", accent2="#D9A441", soft="#FFE0DE", soft2="#FBC9CE", card=(255, 255, 255, 190), card_line=(232, 80, 124, 38),
        shadow="#B04A5C", brush_text="#FFFFFF",
        disp="bebas", disp_up=True, gap=.34, hl_scale=1.16, hl_font="bebas",
        blobs=[(.95, .05, .55, "accent", .20), (.02, .92, .50, "accent2", .16), (.5, .5, .75, "soft", .35)],
        dots=True, stripe=True, grain=2.0, tagline="",
    ),
)
