"""Studio · Vinho DBB: escuro com glow vinho/coral e dourado, na identidade do site da DBB."""
TEMPLATE = dict(
    name="Studio · Vinho DBB", engine="studio", handle="@DBB.SOL",
    style=dict(
        dark=True, bg="#09050D", bg2="#1C0911", fg="#FFFFFF", body="#D9D0E0", muted="#9A91A7",
        accent="#FF3D5A", accent2="#F2C96B", soft="#2A1220", soft2="#1A0B16", card=(255, 255, 255, 14), card_line=(255, 255, 255, 38),
        shadow="#000000", brush_text="#FFFFFF",
        disp="anton", disp_up=True, gap=.30, hl_scale=1.14, hl_font="anton",
        blobs=[(.92, .06, .60, "accent", .30), (.02, .60, .45, "accent2", .10), (.7, 1.0, .55, "accent", .22)],
        dots=True, stripe=False, grain=2.4, tagline="Soluções Empresariais",
    ),
)
