# /carrusel — skill de Claude Code

Le das **cualquier guion** (o una idea) y una **marca**, y arma un carrusel de Instagram de 2 a 10 placas de 1080×1350
con la paleta, las tipografías y el estilo de esa marca. Sintetiza el texto, define una dirección de arte y diseña cada
placa con tipografía, íconos (Lucide), números grandes, comparaciones, grillas, pasos y diagramas a medida: **no hacen
falta fotos**. Renderiza en PNG, revisa, escribe el texto de la publicación y, con tu OK, programa con
[/publicar](https://github.com/gustavopascaner/publicar).

```
/carrusel con este guion para gus-pascaner: <pegás el guion>
/carrusel ~/Desktop/guion.txt con la marca de <cliente>, para @cuenta el martes a las 18
```

## Antes de instalar

- [Claude Code](https://claude.com/claude-code), [Git](https://git-scm.com), Python 3 y Google Chrome.
  En Windows: `winget install Git.Git`, `winget install Python.Python.3.12` y `winget install Google.Chrome`.
- Opcional: Pillow (`python3 -m pip install pillow`) para la hoja de contactos.
- Las **marcas** en `~/.config/motion/brands/` (en Windows `%USERPROFILE%\.config\motion\brands\`). Si ya usás
  `/motion`, `/edicion` o `/marca`, ya están.
- Para programar: la skill `/publicar` instalada y conectada.

## Instalación

### macOS

```bash
git clone https://github.com/gustavopascaner/carrusel.git ~/.claude/skills/carrusel
```

### Windows (PowerShell)

```powershell
git clone https://github.com/gustavopascaner/carrusel.git $HOME\.claude\skills\carrusel
```

Abrí una sesión nueva de Claude Code y escribí `/carrusel`.

**Actualizar:** `git -C ~/.claude/skills/carrusel pull` (Windows: `git -C $HOME\.claude\skills\carrusel pull`).

## Probarlo a mano

```bash
cp -r ~/.claude/skills/carrusel/ejemplos/metodo-ideas /tmp/prueba-carrusel
python3 ~/.claude/skills/carrusel/scripts/render.py /tmp/prueba-carrusel
```

Genera `placa_01.png` … `placa_10.png` y `hoja.jpg` en esa carpeta.

## Archivos

| Archivo | Qué es |
|---|---|
| `SKILL.md` | Instrucciones para Claude: cómo sintetizar, diseñar, revisar y programar |
| `scripts/render.py` | Renderizador: `carrusel.json` + marca → PNG (Chrome sin ventana). Mac, Windows y Linux |
| `scripts/iconos.py` | Buscador de íconos por palabra (en inglés) |
| `reference/placas.md` | 13 tipos de placa (incluida una libre en HTML/SVG), campos, marcado y clases |
| `assets/iconos/` | Íconos de [Lucide](https://lucide.dev) (licencia ISC) |
| `ejemplos/metodo-ideas/` | Método con siglas, marca `gus-pascaner` |
| `ejemplos/dolor-lumbar/` | Dato, comparación, grilla, lista con íconos y placa libre (contenido de ejemplo) |
