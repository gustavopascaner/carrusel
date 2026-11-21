#!/usr/bin/env python3
"""Busca íconos de Lucide por nombre o etiqueta (en inglés).

Uso:  python3 iconos.py doctor heart calendar      → hasta 12 nombres por palabra
"""
import json
import sys
from pathlib import Path

A = Path(__file__).resolve().parent.parent / "assets" / "iconos"
nodes = json.loads((A / "lucide.json").read_text(encoding="utf-8"))
tags = json.loads((A / "tags.json").read_text(encoding="utf-8"))

args = sys.argv[1:]
if not args:
    sys.exit(__doc__)
for q in args:
    q = q.lower()
    exact = [n for n in nodes if n == q]
    by_name = [n for n in nodes if q in n and n not in exact]
    by_tag = [n for n in nodes if n not in exact and n not in by_name and any(q in t for t in tags.get(n, []))]
    hits = (exact + by_name + by_tag)[:12]
    print(f"{q}: {', '.join(hits) if hits else '(nada)'}")
