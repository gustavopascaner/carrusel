#!/usr/bin/env python3
"""Renderiza un carrusel de Instagram desde carrusel.json con la marca de ~/.config/motion/brands/<slug>/.

Uso:  python3 render.py <carpeta-o-carrusel.json> [--solo 3,5]
Salida en la carpeta del JSON: placa_01.png … , hoja.jpg (hoja de contactos) y html/ (fuentes, fotos y HTML).
Funciona en macOS, Windows y Linux. Necesita Google Chrome (o Edge / Chromium). Pillow es opcional (hoja.jpg).
"""
import colorsys
import html
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

BRANDS = Path(os.environ.get("MOTION_BRANDS", Path.home() / ".config" / "motion" / "brands"))
W = 1080
HEIGHTS = {"4:5": 1350, "1:1": 1080}


# ───────────────────────── colores ─────────────────────────
def hex2rgb(h):
    h = h.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def rgb2hex(c):
    return "#" + "".join(f"{max(0, min(255, round(v * 255))):02X}" for v in c)


def lum(h):
    def ch(v):
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(v) for v in hex2rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def shade(h, f):
    """f<1 oscurece, f>1 aclara (en luminosidad HLS)."""
    r, g, b = hex2rgb(h)
    hh, l, s = colorsys.rgb_to_hls(r, g, b)
    return rgb2hex(colorsys.hls_to_rgb(hh, max(0, min(1, l * f)), s))


def best(bg, candidates, minimum=3.0):
    for c in candidates:
        if c and c.lower() != bg.lower() and contrast(bg, c) >= minimum:
            return c
    return max((c for c in candidates if c), key=lambda c: contrast(bg, c))


# ───────────────────────── marca ─────────────────────────
def load_brand(slug):
    d = BRANDS / slug
    f = d / "brand.json"
    if not f.exists():
        sys.exit(f"No existe la marca «{slug}» en {BRANDS}. Marcas: {', '.join(sorted(p.name for p in BRANDS.iterdir() if (p / 'brand.json').exists()))}")
    return d, json.loads(f.read_text(encoding="utf-8"))


def palette(b):
    c = b.get("colors", {})
    extra = b.get("palette_extra", {}) or {}
    dark, light = c.get("dark", "#1E1E1E"), c.get("light", "#F4F1EC")
    accent = c.get("accent", "#2F6FED")
    accent2 = c.get("accent2", c.get("accent3", accent))
    mute = c.get("mute", "#888888")
    accent_dark = extra.get("verde_oscuro") or extra.get("accent_dark") or shade(accent, 0.72)
    return {"dark": dark, "light": light, "accent": accent, "accent2": accent2, "mute": mute, "accent_dark": accent_dark}


def font_faces(brand_dir, b, out_dir):
    """Copia las fuentes a html/ y devuelve (css @font-face, familias por rol)."""
    fonts = b.get("fonts", {})
    css, fam = [], {}
    for role in ("display", "body", "accent", "mono"):
        spec = fonts.get(role)
        if not spec:
            continue
        name = f"F_{role}"
        fam[role] = name
        for fi in spec.get("files", []):
            src = brand_dir / fi["file"]
            if not src.exists():
                continue
            shutil.copy2(src, out_dir / src.name)
            weight = fi.get("weight", "400")
            style = fi.get("style", "italic" if (spec.get("italic") and role == "accent") else "normal")
            css.append(f'@font-face{{font-family:{name};src:url("{src.name}");font-weight:{weight};font-style:{style}}}')
    fam.setdefault("body", fam.get("display", "sans-serif"))
    fam.setdefault("display", fam["body"])
    fam.setdefault("mono", fam["body"])
    acc = fonts.get("accent")
    accent_italic = bool(acc and (acc.get("italic") or any(f.get("style") == "italic" for f in acc.get("files", []))))
    if "accent" not in fam:  # sin serif de acento: display en itálica sintética no queda bien; usamos body itálica
        fam["accent"] = fam["body"]
        accent_italic = True
    return "\n".join(css), fam, accent_italic


# ───────────────────────── íconos (Lucide, ISC) ─────────────────────────
_ICONS = None


def icons():
    global _ICONS
    if _ICONS is None:
        f = Path(__file__).resolve().parent.parent / "assets" / "iconos" / "lucide.json"
        _ICONS = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    return _ICONS


def icon(name, size="1em", stroke=2, extra=""):
    nodes = icons().get(name)
    if not nodes:
        sys.exit(f"No existe el ícono «{name}». Buscalo con: python3 scripts/iconos.py <palabra en inglés>")
    inner = "".join("<" + tag + "".join(f' {k}="{html.escape(str(v))}"' for k, v in attrs.items()) + "/>" for tag, attrs in nodes)
    return (f'<svg class="icn" viewBox="0 0 24 24" width="{size}" height="{size}" fill="none" stroke="currentColor" '
            f'stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round" {extra}>{inner}</svg>')


def big_icon(p, C, size=200, key="icono"):
    if not p.get(key):
        return ""
    return f'<div style="color:{C["pop"]};margin-bottom:40px;line-height:0">{icon(p[key], f"{size}px", 1.6)}</div>'


# ───────────────────────── texto ─────────────────────────
def md(t):
    """Marcado en línea: **negrita**, _serif de acento_, ~~tachado~~, ==resaltado==, {color secundario}, salto con \\n."""
    if t is None:
        return ""
    s = html.escape(str(t), quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"~~(.+?)~~", r'<span class="tach">\1</span>', s)
    s = re.sub(r"==(.+?)==", r'<span class="hl">\1</span>', s)
    s = re.sub(r"(?<![\w])_(.+?)_(?![\w])", r'<span class="si">\1</span>', s)
    s = re.sub(r"\{(.+?)\}", r'<span class="pop">\1</span>', s)
    s = re.sub(r"\[\[([a-z0-9-]+)\]\]", lambda m: icon(m.group(1), "1em", 2.2, 'style="vertical-align:-.12em"'), s)
    return s.replace("\n", "<br>")


def fs(px):
    return f'data-fs="{px}"'


# ───────────────────────── placas ─────────────────────────
ICON_X = '<svg viewBox="0 0 38 38" width="36" height="36"><path d="M7 7L31 31M31 7L7 31" stroke="currentColor" stroke-width="7" stroke-linecap="round"/></svg>'
ICON_OK = '<svg viewBox="0 0 38 38" width="38" height="38"><path d="M6 20l9 9L32 9" fill="none" stroke="currentColor" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></svg>'


def L_portada(p, s, C):
    etiqueta = f'<span class="chip" style="background:{C["pop"]};color:{C["on_pop"]};align-self:flex-start;margin-bottom:34px" {fs(24)}>{md(p["etiqueta"])}</span>' if p.get("etiqueta") else ""
    remate = f'<div class="si" {fs(100)} style="color:{C["pop"]};line-height:1.02;margin-top:14px">{md(p["remate"])}</div>' if p.get("remate") else ""
    if p.get("foto"):
        pos = p.get("foto_pos", "50% 0%")
        ov = C["photo_bg"]
        return f"""
<img class="foto" src="{p['_foto']}" style="object-position:{pos}">
<div style="position:absolute;inset:0;background:linear-gradient(180deg,{ov}00 22%,{ov}c0 50%,{ov} 70%)"></div>
<div class="s" style="justify-content:flex-end;padding-bottom:150px">{etiqueta}
  <div class="h" {fs(p.get('tam', 112))}>{md(p['titulo'])}</div>{remate}
</div>"""
    deco = "" if p.get("icono") or p.get("sin_deco") else f'<div class="deco" style="color:{C["pop"]}"></div>'
    return f"""{deco}
<div class="s" style="justify-content:center">{big_icon(p, C, 240)}{etiqueta}
  <div class="h" {fs(p.get('tam', 140))}>{md(p['titulo'])}</div>{remate}
</div>"""


def L_lista(p, s, C):
    icon = p.get("icono", "x")
    items = []
    for i, t in enumerate(p.get("items", []), 1):
        ic = icon
        if isinstance(t, dict):
            ic, t = t.get("icono", icon), t.get("texto", "")
        mark = (ICON_X if ic == "x" else ICON_OK if ic == "check" else
                f'<span class="h" style="font-size:44px;line-height:1">{i}</span>' if ic == "num" else globals()["icon"](ic, "44px", 2.2))
        items.append(f"""
<div class="card row" style="background:{C['card']};color:{C['on_card']}">
  <div class="ico" style="background:{C['icon_bg']};color:{C['on_icon']}">{mark}</div>
  <div {fs(p.get('tam_items', 37))} style="line-height:1.22">{md(t)}</div>
</div>""")
    kick = f'<div class="kick" style="color:{C["pop"]};margin-top:20px" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    rem = f'<br><span class="si" style="color:{C["pop2"]}">{md(p["remate"])}</span>' if p.get("remate") else ""
    return f"""
<div class="s">{kick}
  <div class="h" {fs(p.get('tam', 140))} style="margin:14px 0 50px">{md(p.get('titulo', ''))}{rem}</div>
  <div style="display:flex;flex-direction:column;gap:22px">{''.join(items)}</div>
</div>"""


def L_frase(p, s, C):
    intro = f'<div {fs(40)} style="line-height:1.3;max-width:840px;opacity:.92;margin-bottom:60px">{md(p["intro"])}</div>' if p.get("intro") else ""
    rem = f'<div class="si" {fs(p.get("tam_remate", 108))} style="line-height:1.04;margin-top:40px">{md(p["remate"])}</div>' if p.get("remate") else ""
    return f"""
<div class="s" style="justify-content:center">{big_icon(p, C, 170)}{intro}
  <div class="h" {fs(p.get('tam', 118))}>{md(p['titulo'])}</div>{rem}
</div>"""


def L_pregunta(p, s, C):
    chips = "".join(f'<span class="chip" style="border:3px solid currentColor" {fs(22)}>{md(c)}</span>' for c in p.get("chips", []))
    kick = f'<div class="kick" style="margin-top:60px;color:{C["mute"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    chips = f'<div style="display:flex;gap:16px;margin-top:22px;flex-wrap:wrap">{chips}</div>' if chips else ""
    texto = f'<div {fs(38)} style="line-height:1.35;margin-top:50px;max-width:880px;opacity:.88">{md(p["texto"])}</div>' if p.get("texto") else ""
    return f"""
<div class="s" style="justify-content:center">
  <div class="si" style="font-size:300px;line-height:.6;color:{C['pop']};height:120px">“</div>
  <div class="h" {fs(p.get('tam', 124))}>{md(p['titulo'])}</div>{texto}{kick}{chips}
</div>"""


def L_metodo(p, s, C):
    cols = [C["accent"], C["accent2"], C["accent_dark"], C["dark"], C["accent"], C["accent2"], C["accent_dark"]]
    rots = [-4, 3, -2, 4, -3, 2, -4]
    letras = p.get("letras", [])
    n = max(1, len(letras))
    tw = min(190, int((W - 180 - (n - 1) * 20) / n))
    tiles = "".join(f"""
<div style="display:flex;flex-direction:column;align-items:center;gap:16px;width:{tw}px">
  <div class="card h tile" style="width:{tw}px;height:{int(tw * 1.28)}px;background:{cols[i % len(cols)]};color:{best(cols[i % len(cols)], [C['light'], C['dark']], 3)};font-size:{int(tw * 1.12)}px;transform:rotate({rots[i % len(rots)]}deg)">{html.escape(l.get('l', ''))}</div>
  <div class="kick" style="font-size:{min(20, int(tw / 8.5))}px;letter-spacing:.03em;text-align:center">{md(l.get('w', ''))}</div>
</div>""" for i, l in enumerate(letras))
    kick = f'<div class="kick" style="color:{C["pop"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    texto = f'<div {fs(38)} style="line-height:1.32;max-width:880px">{md(p["texto"])}</div>' if p.get("texto") else ""
    rem = f'<div class="si" {fs(52)} style="color:{C["pop2"]};margin-top:26px">{md(p["remate"])}</div>' if p.get("remate") else ""
    return f"""
<div class="s" style="justify-content:center">{kick}
  <div class="h" {fs(p.get('tam', 112))} style="margin-top:16px">{md(p['titulo'])}</div>
  <div style="display:flex;justify-content:space-between;margin:70px 0 64px">{tiles}</div>{texto}{rem}
</div>"""


def L_bloques(p, s, C):
    bl = p.get("bloques", [])
    big = {1: 400, 2: 330, 3: 230}.get(len(bl), 230)
    out = []
    for i, b in enumerate(bl):
        lc = C["fg"] if i % 2 == 0 else C["pop"]
        letra = f'<div class="h" style="flex:none;font-size:{big}px;line-height:.78;color:{lc};width:{int(big * 0.64)}px;text-align:center">{html.escape(b["letra"])}</div>' if b.get("letra") else ""
        out.append(f"""
<div style="display:flex;gap:44px;align-items:flex-start">{letra}
  <div style="padding-top:6px;min-width:0">
    <div class="h" {fs(b.get('tam', 84))}>{md(b.get('titulo', ''))}</div>
    <div {fs(35)} style="line-height:1.3;margin-top:18px;opacity:.92">{md(b.get('texto', ''))}</div>
  </div>
</div>""")
    sep = f'<div style="height:3px;background:{C["fg"]};opacity:.2"></div>'
    kick = f'<div class="kick" style="color:{C["pop"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    return f'<div class="s" style="justify-content:center;gap:60px">{kick}{sep.join(out)}</div>'


def L_pasos(p, s, C):
    cols = [(C["accent"], None), (C["light"], None), (C["accent2"], None), (C["accent_dark"], None)]
    pills = []
    arrow = f'<svg width="54" height="40" viewBox="0 0 54 40" style="flex:none"><path d="M2 20H46M32 5l16 15-16 15" fill="none" stroke="{C["pop"]}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></svg>'
    for i, t in enumerate(p.get("pasos", [])):
        bg = cols[i % len(cols)][0]
        if bg.lower() == C["bg"].lower():
            bg = C["card"]
        pills.append(f'<div class="card h" style="background:{bg};color:{best(bg, [C["light"], C["dark"]], 3)};padding:30px 14px 22px;text-align:center;flex:1" {fs(p.get("tam_pasos", 52))}>{md(t)}</div>')
    kick = f'<div class="kick" style="color:{C["pop"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    texto = f'<div {fs(40)} style="line-height:1.3;margin-top:34px;max-width:840px">{md(p["texto"])}</div>' if p.get("texto") else ""
    fondo = f'<div class="h" style="position:absolute;right:-40px;top:120px;font-size:1150px;line-height:.8;opacity:.06">{html.escape(p["letra_fondo"])}</div>' if p.get("letra_fondo") else ""
    return f"""{fondo}
<div class="s" style="justify-content:center">{kick}
  <div class="h" {fs(p.get('tam', 176))} style="margin-top:12px">{md(p['titulo'])}</div>{texto}
  <div style="display:flex;align-items:center;gap:18px;margin-top:60px">{arrow.join(pills)}</div>
</div>"""


def L_cierre(p, s, C):
    chip = f'<span class="chip" style="background:{C["fg"]};color:{C["bg"]};align-self:flex-start" {fs(22)}>{md(p["etiqueta"])}</span>' if p.get("etiqueta") else ""
    rem = f'<div class="si" {fs(60)} style="line-height:1.12;margin-top:56px;max-width:900px">{md(p["remate"])}</div>' if p.get("remate") else ""
    return f"""
<div class="s" style="justify-content:center">{big_icon(p, C, 170)}{chip}
  <div class="h" {fs(p.get('tam', 122))} style="margin-top:46px">{md(p['titulo'])}</div>{rem}
</div>"""


def L_cta(p, s, C):
    intro = f'<div {fs(40)} style="line-height:1.3;font-weight:500;max-width:900px">{md(p["intro"])}</div>' if p.get("intro") else ""
    accion = f'<div class="h" {fs(150)} style="margin-top:60px">{md(p.get("accion", "Comentá"))}</div>'
    box_bg = C["dark"] if C["bg"].lower() != C["dark"].lower() else C["accent2"]
    shadow = C["light"] if box_bg.lower() != C["light"].lower() else C["accent"]
    palabra = f'<div class="card h" {fs(250)} style="background:{box_bg};color:{best(box_bg, [C["light"], C["dark"]], 3)};padding:44px 60px 22px;align-self:flex-start;margin-top:18px;transform:rotate(-3deg);box-shadow:16px 16px 0 {shadow}">{md(p["palabra"])}</div>' if p.get("palabra") else ""
    texto = f'<div {fs(40)} style="line-height:1.3;margin-top:70px;max-width:880px">{md(p["texto"])}</div>' if p.get("texto") else ""
    foto = f'<img src="{p["_foto"]}" style="width:96px;height:96px;border-radius:50%;object-fit:cover;object-position:{p.get("foto_pos", "50% 25%")};border:4px solid currentColor">' if p.get("_foto") else ""
    firma = f'<div style="display:flex;align-items:center;gap:22px;margin-top:56px">{foto}<div class="si" {fs(44)}>{md(p["firma"])}</div></div>' if p.get("firma") else ""
    return f'<div class="s" style="justify-content:center">{intro}{accion}{palabra}{texto}{firma}</div>'


def L_dato(p, s, C):
    kick = f'<div class="kick" style="color:{C["pop"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    uni = f'<span class="si" style="font-size:.38em;margin-left:.12em">{md(p["unidad"])}</span>' if p.get("unidad") else ""
    texto = f'<div {fs(46)} style="line-height:1.25;max-width:880px;margin-top:30px">{md(p["texto"])}</div>' if p.get("texto") else ""
    fuente = f'<div class="kick" style="color:{C["mute"]};margin-top:50px;letter-spacing:.06em" {fs(20)}>{md(p["fuente"])}</div>' if p.get("fuente") else ""
    return f"""
<div class="s" style="justify-content:center">{big_icon(p, C, 150)}{kick}
  <div class="h" {fs(p.get('tam', 380))} style="color:{C['pop']};line-height:.85;margin-top:20px;white-space:nowrap">{md(p['numero'])}{uni}</div>{texto}{fuente}
</div>"""


def L_comparacion(p, s, C):
    def col(d, good):
        bg = C["card"] if not good else C["pop"]
        fg = C["on_card"] if not good else C["on_pop"]
        mk = ICON_OK if good else ICON_X
        items = "".join(f'<div style="display:flex;gap:18px;align-items:flex-start;margin-top:26px"><span style="flex:none;opacity:{1 if good else .6};margin-top:4px">{mk}</span><span {fs(32)} style="line-height:1.25">{md(t)}</span></div>' for t in d.get("items", []))
        ic = f'<div style="line-height:0;margin-bottom:22px">{icon(d["icono"], "64px", 2)}</div>' if d.get("icono") else ""
        return f'<div class="card" style="flex:1;min-width:0;background:{bg};color:{fg};padding:44px 38px;{"" if good else "opacity:.92"}">{ic}<div class="h" {fs(64)}>{md(d.get("titulo", ""))}</div>{items}</div>'
    kick = f'<div class="kick" style="color:{C["pop"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    titulo = f'<div class="h" {fs(p.get("tam", 104))} style="margin:14px 0 50px">{md(p["titulo"])}</div>' if p.get("titulo") else ""
    return f"""
<div class="s" style="justify-content:center">{kick}{titulo}
  <div style="display:flex;gap:24px;align-items:stretch">{col(p.get('izq', {}), False)}{col(p.get('der', {}), True)}</div>
</div>"""


def L_grilla(p, s, C):
    cel = p.get("celdas", [])
    cols = 2 if len(cel) in (2, 4) else 3 if len(cel) in (3, 6) else 2
    cards = "".join(f"""
<div class="card" style="background:{C['card']};color:{C['on_card']};padding:40px 34px">
  <div style="width:96px;height:96px;border-radius:24px;background:{C['icon_bg']};color:{C['on_icon']};display:flex;align-items:center;justify-content:center">{icon(c.get('icono', 'sparkles'), '54px', 2)}</div>
  <div class="h" {fs(54)} style="margin-top:28px">{md(c.get('titulo', ''))}</div>
  <div {fs(28)} style="line-height:1.3;margin-top:12px;opacity:.85">{md(c.get('texto', ''))}</div>
</div>""" for c in cel)
    kick = f'<div class="kick" style="color:{C["pop"]}" {fs(24)}>{md(p["kicker"])}</div>' if p.get("kicker") else ""
    titulo = f'<div class="h" {fs(p.get("tam", 110))} style="margin:14px 0 50px">{md(p["titulo"])}</div>' if p.get("titulo") else ""
    return f"""
<div class="s" style="justify-content:center">{kick}{titulo}
  <div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:22px">{cards}</div>
</div>"""


def L_libre(p, s, C):
    """HTML a medida. Puede usar las clases .h .si .kick .chip .card .pop .hl .tach, var(--bg/--fg/--pop/...),
    [[ícono]] y data-fs="px" en los textos para el ajuste automático."""
    body = p.get("html", "")
    body = re.sub(r"\[\[([a-z0-9-]+)(?:\|(\d+))?\]\]", lambda m: icon(m.group(1), (m.group(2) + "px") if m.group(2) else "1em", 2), body)
    css = f"<style>{p['css']}</style>" if p.get("css") else ""
    return f'{css}<div class="s" style="{p.get("estilo", "justify-content:center")}">{body}</div>'


LAYOUTS = {"portada": L_portada, "lista": L_lista, "frase": L_frase, "pregunta": L_pregunta, "metodo": L_metodo,
           "bloques": L_bloques, "pasos": L_pasos, "cierre": L_cierre, "cta": L_cta,
           "dato": L_dato, "comparacion": L_comparacion, "grilla": L_grilla, "libre": L_libre}
ROTA = ["light", "accent", "dark", "light", "accent_dark", "dark", "accent", "light"]


def theme_colors(P, fondo):
    bg = P.get(fondo, P["light"]) if fondo != "foto" else shade(P["dark"], 0.8)
    fg = best(bg, [P["light"], P["dark"]], 4.5)
    pop = best(bg, [P["accent2"], P["accent"], fg], 3)
    pop2 = best(bg, [P["accent"], P["accent2"], fg], 3)
    is_light = lum(bg) > 0.4
    if is_light:
        card = "#FFFFFF" if lum(bg) > 0.75 else shade(bg, 1.06)
    elif lum(bg) > 0.06:
        card = shade(bg, 0.72)
    else:
        card = shade(bg, 1.45)
    icon_bg = P["accent2"] if contrast(card, P["accent2"]) >= 2 else P["accent"]
    return dict(P, bg=bg, fg=fg, pop=pop, pop2=pop2, on_pop=best(pop, [P["dark"], P["light"]], 3),
                card=card, on_card=best(card, [fg, P["dark"], P["light"]], 4.5),
                icon_bg=icon_bg, on_icon=best(icon_bg, [P["light"], P["dark"]], 3),
                gl=("rgba(0,0,0,.07)" if is_light else "rgba(255,255,255,.07)"), photo_bg=bg)


FIT_JS = """
<script>
document.fonts.ready.then(function(){
  const box=document.querySelector('.s'); if(!box) return;
  const els=[...document.querySelectorAll('[data-fs]')];
  function over(){
    if(box.scrollHeight>box.clientHeight+2) return true;
    const W=document.body.clientWidth, H=document.body.clientHeight;
    for(const e of els){
      if(e.scrollWidth>e.clientWidth+2) return true;
      const r=e.getBoundingClientRect(); if(r.right>W-75||r.bottom>H-95) return true;
    }
    return false;
  }
  let k=1;
  els.forEach(e=>e.style.fontSize=e.dataset.fs+'px');
  while(over() && k>0.55){ k-=0.03; els.forEach(e=>e.style.fontSize=(e.dataset.fs*k)+'px'); }
  document.body.dataset.k=k.toFixed(2);
});
</script>"""


def build_css(face_css, fam, accent_italic, b, H):
    d = b.get("fonts", {}).get("display", {})
    upper = d.get("upper", False)
    leading = d.get("leading", 0.95)
    dw = d.get("weight", 700)
    track = d.get("tracking", "-0.005em")
    st = b.get("style", {}) or {}
    radius = st.get("radius", 28)
    return f"""{face_css}
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{W}px;height:{H}px;overflow:hidden}}
body{{font-family:{fam['body']},sans-serif;position:relative;-webkit-font-smoothing:antialiased;background:var(--bg);color:var(--fg)}}
b{{font-weight:700}}
.s{{position:absolute;inset:0;padding:110px 90px 120px;display:flex;flex-direction:column;overflow:hidden}}
.s>*{{flex-shrink:0}}
.grid{{position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(var(--gl) 1px,transparent 1px),linear-gradient(90deg,var(--gl) 1px,transparent 1px);background-size:90px 90px;background-position:-1px -1px;display:{'block' if st.get('grid', True) else 'none'}}}
.grain{{position:absolute;inset:0;pointer-events:none;opacity:.22;mix-blend-mode:overlay;display:{'block' if st.get('grain', True) else 'none'};
 background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='300' height='300'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 .5 0 0 0 0 .5 0 0 0 0 .5 0 0 0 1 0'/></filter><rect width='300' height='300' filter='url(%23n)'/></svg>")}}
.top{{position:absolute;top:48px;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;font-family:{fam['mono']},monospace;font-size:22px;letter-spacing:.08em;text-transform:uppercase;z-index:5}}
.top img{{height:44px}}
.bot{{position:absolute;bottom:52px;left:90px;right:90px;display:flex;justify-content:space-between;align-items:center;font-family:{fam['mono']},monospace;font-size:22px;letter-spacing:.06em;z-index:5}}
.swipe{{display:flex;align-items:center;gap:14px;font-weight:700;text-transform:uppercase}}
.swipe i{{display:inline-block;width:70px;height:3px;background:currentColor;position:relative}}
.swipe i:after{{content:"";position:absolute;right:-2px;top:-8px;border:9px solid transparent;border-left:14px solid currentColor;border-right:0}}
.dots{{display:flex;gap:8px}}.dots b{{width:10px;height:10px;border-radius:50%;background:currentColor;opacity:.25}}.dots b.on{{opacity:1;width:34px;border-radius:6px}}
.h{{font-family:{fam['display']},sans-serif;font-weight:{dw};text-transform:{'uppercase' if upper else 'none'};line-height:{leading};letter-spacing:{track};overflow-wrap:normal}}
.h b{{font-weight:{dw}}}
.si{{font-family:{fam['accent']},serif;font-style:{'italic' if accent_italic else 'normal'};font-weight:400;text-transform:none;letter-spacing:0}}
.pop{{color:var(--pop)}}
.tach{{text-decoration:line-through;text-decoration-color:var(--strike);text-decoration-thickness:.07em}}
.hl{{background:linear-gradient(transparent 62%,var(--strike) 62%,var(--strike) 92%,transparent 92%);padding:0 .08em}}
.kick{{font-family:{fam['mono']},monospace;font-weight:700;font-size:24px;letter-spacing:.14em;text-transform:uppercase}}
.chip{{display:inline-block;padding:12px 26px;border-radius:999px;font-family:{fam['mono']},monospace;font-weight:700;font-size:22px;letter-spacing:.1em;text-transform:uppercase}}
.card{{border-radius:{radius}px}}
.row{{display:flex;align-items:center;gap:34px;padding:34px 40px;box-shadow:0 10px 0 rgba(0,0,0,.08)}}
.ico{{flex:none;width:86px;height:86px;border-radius:50%;display:flex;align-items:center;justify-content:center}}
.tile{{display:flex;align-items:center;justify-content:center;padding-top:.06em;line-height:1}}
.foto{{position:absolute;left:0;top:0;width:{W}px;height:{H}px;object-fit:cover}}
.deco{{position:absolute;right:-250px;bottom:-250px;width:540px;height:540px;border-radius:50%;border:90px solid currentColor;opacity:.9}}
"""


def render_slide(i, total, p, cfg, P, css, out_html, H, brand_dir):
    fondo = p.get("fondo") or ("foto" if p.get("tipo") == "portada" and p.get("foto") else ROTA[(i - 1) % len(ROTA)])
    if p.get("tipo") == "cta" and not p.get("fondo"):
        fondo = "accent2"
    C = theme_colors(P, fondo)
    for key in ("foto",):
        if p.get(key):
            src = Path(p[key]).expanduser()
            if not src.is_absolute():
                src = (cfg["_dir"] / src).resolve()
            if not src.exists():
                sys.exit(f"Placa {i}: no existe la foto {src}")
            dst = out_html / f"foto_{i:02d}{src.suffix.lower()}"
            shutil.copy2(src, dst)
            p["_foto"] = dst.name
    body = LAYOUTS[p["tipo"]](p, cfg, C)
    if p.get("icono_fondo"):
        body = (f'<div style="position:absolute;right:-120px;bottom:-60px;color:{C["pop"]};opacity:.13;line-height:0">'
                f'{icon(p["icono_fondo"], "760px", 1.4)}</div>') + body
    firma = cfg.get("firma") or ""
    logo = ""
    if cfg.get("logo") and cfg.get("_logo"):
        logo = f'<img src="{cfg["_logo"]}">'
    left = logo or html.escape(firma)
    dots = "".join(f'<b class="{"on" if k == i else ""}"></b>' for k in range(1, total + 1))
    right = '<span class="swipe">Deslizá <i></i></span>' if i < total else f'<span>{html.escape(cfg.get("cuenta", ""))}</span>'
    strike = next((c for c in (P["accent2"], P["accent"], C["fg"]) if c.lower() != C["bg"].lower()), C["fg"])
    doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>{css}
body{{--bg:{C['bg']};--fg:{C['fg']};--pop:{C['pop']};--pop2:{C['pop2']};--card:{C['card']};--on-card:{C['on_card']};--mute:{C['mute']};--dark:{C['dark']};--light:{C['light']};--accent:{C['accent']};--accent2:{C['accent2']};--accent-dark:{C['accent_dark']};--gl:{C['gl']};--strike:{strike}}}</style></head><body>
<div class="grid"></div>
{body}
<div class="top"><span>{left}</span><span>{i:02d} / {total:02d}</span></div>
<div class="bot"><span class="dots">{dots}</span>{right}</div>
<div class="grain"></div>
{FIT_JS}
</body></html>"""
    f = out_html / f"placa_{i:02d}.html"
    f.write_text(doc, encoding="utf-8")
    return f


def find_chrome():
    env = os.environ.get("CHROME")
    if env and Path(env).exists():
        return env
    cands = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ]
    for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
        if base:
            cands += [os.path.join(base, "Google", "Chrome", "Application", "chrome.exe"),
                      os.path.join(base, "Microsoft", "Edge", "Application", "msedge.exe")]
    for c in cands:
        if Path(c).exists():
            return c
    for n in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "msedge"):
        w = shutil.which(n)
        if w:
            return w
    sys.exit("No encontré Google Chrome. Instalalo (o definí la variable CHROME con la ruta del navegador).")


def screenshot(chrome, html_file, png, H):
    cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--allow-file-access-from-files",
           "--force-device-scale-factor=1", f"--window-size={W},{H}", "--virtual-time-budget=3000",
           "--default-background-color=00000000", f"--screenshot={png}", html_file.resolve().as_uri()]
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    if not Path(png).exists():
        sys.exit(f"Chrome no generó {png}")


def contact_sheet(pngs, out, H):
    try:
        from PIL import Image
    except ImportError:
        print("(sin Pillow: no armo hoja.jpg; mirá las placas una por una)")
        return
    tw, th = 400, int(400 * H / W)
    cols = 5
    rows = (len(pngs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 12) - 12, rows * (th + 12) - 12), "white")
    for k, p in enumerate(pngs):
        im = Image.open(p).convert("RGB").resize((tw, th))
        sheet.paste(im, ((k % cols) * (tw + 12), (k // cols) * (th + 12)))
    sheet.save(out, quality=86)


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    arg = Path(sys.argv[1]).expanduser()
    jf = arg / "carrusel.json" if arg.is_dir() else arg
    cfg = json.loads(jf.read_text(encoding="utf-8"))
    cfg["_dir"] = jf.parent
    solo = None
    if "--solo" in sys.argv:
        solo = {int(x) for x in sys.argv[sys.argv.index("--solo") + 1].split(",")}
    brand_dir, b = load_brand(cfg["marca"])
    P = palette(b)
    for k, v in (cfg.get("colores") or {}).items():
        P[k] = v
    H = HEIGHTS.get(cfg.get("formato", "4:5"), 1350)
    out = jf.parent
    out_html = out / "html"
    out_html.mkdir(exist_ok=True)
    face_css, fam, acc_it = font_faces(brand_dir, b, out_html)
    if b.get("logo") and (brand_dir / b["logo"]).exists():
        shutil.copy2(brand_dir / b["logo"], out_html / Path(b["logo"]).name)
        cfg["_logo"] = Path(b["logo"]).name
    cfg.setdefault("firma", b.get("name", cfg["marca"]))
    css = build_css(face_css, fam, acc_it, b, H)
    placas = cfg["placas"]
    if not 2 <= len(placas) <= 10:
        sys.exit(f"Un carrusel lleva de 2 a 10 placas (hay {len(placas)}).")
    for p in placas:
        if p.get("tipo") not in LAYOUTS:
            sys.exit(f"Tipo de placa desconocido: {p.get('tipo')}. Tipos: {', '.join(LAYOUTS)}")
    chrome = find_chrome()
    pngs = []
    for i, p in enumerate(placas, 1):
        png = out / f"placa_{i:02d}.png"
        pngs.append(png)
        if solo and i not in solo:
            continue
        f = render_slide(i, len(placas), p, cfg, P, css, out_html, H, brand_dir)
        if png.exists():
            png.unlink()
        screenshot(chrome, f, png, H)
        print(f"✓ placa {i:02d} ({p['tipo']})")
    contact_sheet([p for p in pngs if p.exists()], out / "hoja.jpg", H)
    print(f"Listo: {len(pngs)} placas en {out}")


if __name__ == "__main__":
    main()
