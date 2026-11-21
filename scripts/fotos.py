#!/usr/bin/env python3
"""Busca fotos en Pixabay para ilustrar un carrusel y baja las candidatas con una hoja numerada.

Uso:  python3 fotos.py <carpeta> "<búsqueda en inglés>" [-n 8] [--horizontal] [--pagina 2]
Clave: variable PIXABAY_KEY o archivo ~/.config/pixabay/key.
Salida en <carpeta>/fotos/: c01.jpg … (candidatas), candidatas.jpg (hoja numerada para mirar) y
candidatas.json (id, autor, página, etiquetas). Las búsquedas siguientes numeran a continuación.
Licencia de Pixabay: uso comercial libre, sin atribución obligatoria.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request
from pathlib import Path


def key():
    k = os.environ.get("PIXABAY_KEY")
    f = Path.home() / ".config" / "pixabay" / "key"
    if not k and f.exists():
        k = f.read_text().strip()
    if not k:
        sys.exit("Falta la clave de Pixabay: definí PIXABAY_KEY o guardala en ~/.config/pixabay/key")
    return k


def get(url, timeout=60):
    req = urllib.request.Request(url, headers={"User-Agent": "carrusel/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def hoja(items, out):
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False
    tw, th, cols = 300, 400, 4
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * 10, rows * th + (rows + 1) * 10), "#222")
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 40)
    except Exception:
        font = ImageFont.load_default()
    for k, it in enumerate(items):
        im = Image.open(it["archivo"]).convert("RGB")
        r = max(tw / im.width, th / im.height)
        im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
        x0, y0 = (im.width - tw) // 2, (im.height - th) // 2
        im = im.crop((x0, y0, x0 + tw, y0 + th))
        x, y = 10 + (k % cols) * (tw + 10), 10 + (k // cols) * (th + 10)
        sheet.paste(im, (x, y))
        d = ImageDraw.Draw(sheet)
        d.rectangle([x, y, x + 80, y + 56], fill="#000")
        d.text((x + 10, y + 6), Path(it["archivo"]).stem, fill="#fff", font=font)
    sheet.save(out, quality=85)
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("q", help="búsqueda, mejor en inglés (ej. 'dentist smiling patient')")
    ap.add_argument("-n", type=int, default=8)
    ap.add_argument("--horizontal", action="store_true")
    ap.add_argument("--pagina", type=int, default=1)
    a = ap.parse_args()

    dest = Path(a.carpeta).expanduser() / "fotos"
    dest.mkdir(parents=True, exist_ok=True)
    meta_f = dest / "candidatas.json"
    meta = json.loads(meta_f.read_text()) if meta_f.exists() else []
    vistos = {m["id"] for m in meta}

    params = dict(key=key(), q=a.q[:100], image_type="photo", safesearch="true", per_page=max(3, min(200, a.n * 2)),
                  page=a.pagina, orientation="horizontal" if a.horizontal else "vertical", min_width=1080)
    try:
        data = json.loads(get("https://pixabay.com/api/?" + urllib.parse.urlencode(params)))
    except Exception as e:
        sys.exit(f"Pixabay no respondió: {e}")
    hits = [h for h in data.get("hits", []) if h["id"] not in vistos][: a.n]
    if not hits:
        sys.exit(f"Sin resultados nuevos para «{a.q}». Probá otras palabras (en inglés), --horizontal o --pagina 2.")

    nuevos = []
    for h in hits:
        n = len(meta) + 1
        f = dest / f"c{n:02d}.jpg"
        try:
            f.write_bytes(get(h["largeImageURL"]))
        except Exception as e:
            print(f"  no pude bajar {h['id']}: {e}")
            continue
        m = dict(archivo=str(f), id=h["id"], busqueda=a.q, autor=h.get("user"), pagina=h.get("pageURL"),
                 etiquetas=h.get("tags"), ancho=h.get("imageWidth"), alto=h.get("imageHeight"))
        meta.append(m)
        nuevos.append(m)
        print(f"  {f.name}  {h.get('tags')}")
    meta_f.write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    if hoja(meta, dest / "candidatas.jpg"):
        print(f"Hoja: {dest / 'candidatas.jpg'}")
    else:
        print("Sin Pillow: mirá las candidatas una por una.")
    print(f"{len(nuevos)} candidatas nuevas ({data.get('totalHits', 0)} resultados en total).")


if __name__ == "__main__":
    main()
