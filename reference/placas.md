# Tipos de placa de `carrusel.json`

Campos generales del archivo:

| Campo | Qué es |
|---|---|
| `marca` | slug de `~/.config/motion/brands/<slug>/` (obligatorio) |
| `firma` | texto de arriba a la izquierda (por defecto el `name` de la marca) |
| `logo` | `true` para poner el logo de la marca arriba a la izquierda en lugar de la firma (si la marca tiene `logo`) |
| `cuenta` | `@usuario`, va abajo a la derecha en la última placa |
| `formato` | `4:5` (1080×1350, por defecto) o `1:1` (1080×1080) |
| `colores` | opcional, pisa colores de la marca: `{"accent2": "#…"}` |
| `placas` | lista de 2 a 10 placas |

Campos comunes de cada placa: `tipo` (obligatorio), `fondo` (`light`, `dark`, `accent`, `accent_dark`, `accent2`),
`tam` (tamaño base del título en px; se achica solo si no entra), `icono_fondo` (ícono gigante y tenue abajo a la
derecha, en cualquier placa).

Íconos: nombres de [Lucide](https://lucide.dev/icons) (licencia ISC). Buscar: `python3 scripts/iconos.py <palabras en inglés>`.

## Marcado en los textos
- `**negrita**`
- `_serif de acento_` (la tipografía `accent` de la marca, en itálica)
- `~~tachado~~` (raya de color: ideal para «no es X»)
- `==resaltado==` (subrayado grueso de color)
- `{texto}` en el color de acento que mejor contrasta con el fondo
- `[[nombre]]` ícono en línea, del tamaño del texto
- `\n` salto de línea

## `portada`
`titulo`, `remate` (serif, color de acento), `etiqueta` (píldora arriba), `icono` (ícono grande arriba; saca el aro
decorativo), `sin_deco` (`true` para no poner el aro). Opcional, solo si el usuario dio una foto para este carrusel:
`foto` (ruta, relativa a la carpeta del JSON) y `foto_pos` (CSS `object-position`, por defecto `50% 0%`).

## `lista`
`kicker`, `titulo`, `remate`, `icono` (`x`, `check`, `num` o un ícono de Lucide), `items` (3–4, ≤ 14 palabras; cada
uno puede ser texto o `{"icono": "zap", "texto": "…"}`), `tam_items`.

## `frase`
`icono`, `intro` (texto chico arriba), `titulo` (frase grande), `remate` (serif grande), `tam_remate`.
Ej.: `"titulo": "No tienen un problema de ~~reputación~~."`, `"remate": "Tienen un problema de ==previsibilidad.=="`.

## `pregunta`
`titulo` (la pregunta, con comilla decorativa), `texto`, `kicker`, `chips` (2–4 palabras sueltas).

## `metodo`
`kicker`, `titulo`, `letras` (`[{"l": "I", "w": "Investigación"}, …]`, hasta 7), `texto`, `remate`.

## `bloques`
`kicker`, `bloques` (1 a 3: `{"letra": "I", "titulo": "…", "texto": "…"}`; `letra` es opcional).

## `pasos`
`kicker`, `titulo`, `texto`, `pasos` (2–4 palabras cortas con flechas), `letra_fondo` (letra gigante de fondo),
`tam_pasos`.

## `cierre`
`icono`, `etiqueta` (píldora), `titulo`, `remate` (serif).

## `cta`
`intro`, `accion` (por defecto «Comentá»), `palabra` (la palabra clave en caja), `texto`, `firma` (serif chica),
`foto` (avatar redondo junto a la firma), `foto_pos`. Fondo por defecto: `accent2`.

## `dato`
`kicker`, `numero` (ej. `"80"`, `"3 de 10"`, `"$0"`), `unidad` (serif chica al lado: `%`, `días`…), `texto`, `fuente`
(obligatoria si el número viene de afuera; nunca inventar), `icono`.

## `comparacion`
`kicker`, `titulo`, `izq` y `der`: `{"titulo": "Mito", "icono": "bed", "items": ["…", "…"]}`. La izquierda va apagada
con ✕ y la derecha destacada con ✓ (mito/realidad, antes/después, lo común/lo que conviene).

## `grilla`
`kicker`, `titulo`, `celdas` (2, 3, 4 o 6: `{"icono": "…", "titulo": "…", "texto": "…"}`).

## `libre`
`html` (el contenido de la placa), `css` (opcional, reglas extra), `estilo` (CSS del contenedor, por defecto
`justify-content:center`). El contenedor `.s` es una columna flex con los márgenes de la placa (90 px a los lados).
Disponible:
- Clases: `.h` (display de la marca), `.si` (serif de acento), `.kick` (rótulo mono), `.chip` (píldora), `.card`
  (radio de la marca), `.pop` (color de acento), `.hl` (resaltado), `.tach` (tachado), `b`.
- Variables: `var(--bg)`, `--fg`, `--pop`, `--pop2`, `--card`, `--on-card`, `--mute`, `--dark`, `--light`, `--accent`,
  `--accent2`, `--accent-dark`.
- Íconos: `[[nombre]]` (tamaño del texto) o `[[nombre|120]]` (en px).
- Ajuste automático: poner `data-fs="<px>"` en cada texto (en lugar de `font-size`) para que se achique si no entra.
- SVG en línea para diagramas (usar `currentColor` y las variables para los colores).

Ideas: línea de tiempo (puntos y línea con `--pop`), barra de progreso o termómetro, escala del 1 al 10, gráfico de
barras simple con divs, «chat» de WhatsApp con burbujas `.card`, calendario semanal, ticket/receta, número tachado con
otro encima, flecha de antes → después, checklist con casillas.
