---
name: carrusel
description: Convierte cualquier guion (o idea) en un carrusel de Instagram de 2 a 10 placas de 1080×1350 diseñadas con la marca de un cliente o de Gus (paleta, tipografías y estilo de ~/.config/motion/brands/<slug>/brand.json). Sintetiza el texto, define una dirección de arte, diseña las placas con tipografía, íconos, datos grandes, comparaciones, grillas y diagramas a medida, busca en Pixabay una foto que ilustre el tema (o usa las que da el usuario), las renderiza en PNG con Chrome, las revisa, escribe el texto de la publicación y, con el OK, las programa con /publicar. Usar cuando el usuario escribe /carrusel con un guion, archivo o tema, o pide "armá un carrusel con este guion", "pasá este guion a carrusel para @cuenta", "hacé un carrusel con la marca de <cliente>".
---

# /carrusel — cualquier guion → carrusel de Instagram con la marca

Hablarle al usuario (Gus o alguien de su equipo) en español rioplatense (voseo), corto.

**Principio:** cualquier guion tiene que poder terminar en un carrusel atractivo, **sin depender de fotos**. El diseño
sale de la marca (colores y tipografías) más las herramientas de esta skill: jerarquía tipográfica fuerte, íconos,
números grandes, comparaciones, grillas, pasos y placas libres en HTML/SVG para diagramas a medida. Encima de eso,
**1 o 2 fotos reales que ilustren el tema** (de Pixabay o las que dé el usuario) le dan vida: el carrusel nunca depende
de ellas, pero se buscan siempre (ver 3.6).

## 0 · Qué hace falta
- **Guion**: texto pegado, archivo (`.txt`, `.md`, `.docx`) o una idea para desarrollar.
- **Marca**: slug de `~/.config/motion/brands/<slug>/` (en Windows `%USERPROFILE%\.config\motion\brands\`). Si no la
  dicen, deducirla de la cuenta o del cliente nombrado (`ls` de la carpeta). Si hay dudas, preguntar con 2–5 opciones.
  Si no existe: se crea con `/marca`.
- **Fotos**: si el usuario pasa fotos, van esas. Si no, buscarlas en Pixabay (paso 3.6), salvo que diga «sin foto».
- Requisitos: Python 3 (`python3` en Mac, `py -3` en Windows), Google Chrome (o Edge / Chromium); Pillow opcional.

## 1 · Leer la marca y el contexto
- `brand.json`: colores (`dark`, `light`, `accent`, `accent2`, `mute`), tipografías y `notes`. Si hay `IDENTIDAD.md`
  al lado, leerlo para el tono.
- Si la carpeta de trabajo tiene un `CLAUDE.md` con reglas del negocio (cifras aprobadas, palabras a evitar), seguirlas.
  **No inventar cifras, datos, fuentes, resultados ni testimonios.** Un `dato` solo con un número que esté en el guion
  o en una fuente que el usuario aprobó. Si el guion trae una cifra que contradice una aprobada, usar la aprobada y
  avisarlo en una línea.

## 2 · Sintetizar el guion
Un carrusel no es el guion completo: es el guion **sintetizado**. 6 a 10 placas, una idea por placa, cada una se lee en
3 segundos. Mantener las palabras clave del guion y la acción del CTA tal cual. No agregar promesas que el guion no
hace. Voseo, frases cortas, sin relleno. Evitar palabras en inglés si hay una clara en castellano.

Arco base (adaptarlo; no todos los guiones lo tienen entero):
**gancho → problema o tensión → giro / idea central → desarrollo (2–5 placas) → cierre → CTA.**
Si el guion no trae CTA, cerrar con uno suave coherente con la cuenta (guardar, compartir, escribir) y avisarlo.

## 3 · Dirección de arte (antes de escribir el JSON)
Decidir en 2–3 líneas (para vos, y contarlo en una línea al mostrar el resultado):
1. **Concepto visual**: una metáfora o recurso que atraviese el carrusel (ej.: «checklist de consultorio», «antes y
   después», «mapa de pasos», «el número que asusta»). Elegir un ícono protagonista para la portada.
2. **Ritmo**: alternar fondos (`light`, `dark`, `accent`, `accent_dark`, `accent2`), nunca dos iguales seguidos, y
   alternar placas densas con placas de impacto (una frase o un número solo).
3. **Tipo de placa por contenido** — mirar qué ES cada idea del guion:

| Si la idea es… | Placa |
|---|---|
| gancho / promesa | `portada` (con foto si hay una buena; si no, `icono` o el aro decorativo) |
| una escena o situación que se ve (el paciente, el síntoma, el lugar) | `foto` |
| una cifra, porcentaje, tiempo, plata | `dato` |
| errores, señales, beneficios, requisitos | `lista` (íconos por ítem, `x` o `check`) |
| mito vs. realidad, antes/después, lo que hacen vs. lo que conviene | `comparacion` |
| 3–6 conceptos paralelos, servicios, pilares | `grilla` |
| una frase que da vuelta todo | `frase` (con `~~tachado~~` y `==resaltado==`) |
| una pregunta que duele | `pregunta` |
| un método con siglas | `metodo` + `bloques` (2 letras por placa) |
| un proceso o ciclo | `pasos` |
| la transformación / objetivo | `cierre` |
| la acción final | `cta` |
| nada de lo anterior encaja, o hace falta un diagrama, línea de tiempo, gráfico, escala, mapa | `libre` |

4. **Íconos**: usar íconos (Lucide, 2000+) para que cada placa tenga un ancla visual. Buscarlos con
   `python3 ~/.claude/skills/carrusel/scripts/iconos.py <palabras en inglés>` (ej. `tooth heart calendar money`).
   Usarlos en `icono` (portada, frase, cierre, dato), en ítems de `lista`, en `grilla`, en `comparacion`, como
   `icono_fondo` (gigante y tenue, en cualquier placa) o en línea con `[[nombre]]`.
5. **Placa `libre`**: diseñar HTML/CSS/SVG a medida cuando el contenido lo pide (línea de tiempo, barra de progreso,
   escala de dolor, gráfico simple, diagrama de flujo, «calendario» de la semana, un número tachado y otro encima…).
   Usar las variables y clases de la marca (ver `reference/placas.md`) para que no se salga del sistema. Al menos una
   placa `libre` o un recurso a medida por carrusel cuando el guion no tiene estructura obvia.
6. **Foto que ilustra el tema** (por defecto 1, máximo 2 por carrusel). Buscar en Pixabay, en inglés y con 2–4
   palabras concretas de lo que se VE (no del concepto): `lower back pain`, `dentist patient smiling`,
   `woman checking phone night`.
   ```bash
   python3 ~/.claude/skills/carrusel/scripts/fotos.py "<carpeta>" "<búsqueda>" [-n 8] [--horizontal] [--pagina 2]
   ```
   Baja `fotos/c01.jpg…` y la hoja `fotos/candidatas.jpg`. **Mirar la hoja con Read y elegir con criterio de
   director de arte**; si ninguna sirve, otra búsqueda (hasta 3) y si sigue sin haber, seguir sin foto y avisarlo.
   Sirve una foto que:
   - se entiende de un vistazo y muestra el tema (el cuerpo, la situación, el objeto), no algo genérico;
   - parece real y actual: luz natural, nada de sonrisas forzadas, poses de banco de imágenes ni montajes;
   - deja lugar para el texto (zona lisa o que tolere el degradé) y no trae texto, logos ni marcas de agua;
   - no muestra sangre, heridas, agujas en primer plano ni cuerpos expuestos de más;
   - **no se confunde con el profesional de la cuenta**: evitar un médico de frente como protagonista (parecería que es
     el cliente); mejor manos, pacientes, objetos, espacios o planos de espalda.
   Dónde va: en la `portada` (`foto`, si hay una muy buena: es la que más suma) o en una placa `foto` en el medio del
   desarrollo (`modo: "sangre"` a pantalla completa o `modo: "marco"` enmarcada con texto abajo). Ajustar el encuadre
   con `foto_pos`. Pixabay permite uso comercial sin atribución; los datos quedan en `fotos/candidatas.json`.
   Imágenes generadas con IA: solo si el usuario lo pide (gastan créditos).

## 4 · Escribir `carrusel.json`
Carpeta de salida: `Contenido/Carruseles/AAAA-MM-DD <tema corto>/` si existe `Contenido/` en la carpeta de trabajo; si
no, `Carruseles/AAAA-MM-DD <tema corto>/`. Ahí va `carrusel.json`.

Referencias: `reference/placas.md` (todos los tipos, campos, marcado y clases para `libre`) y los ejemplos
`ejemplos/metodo-ideas/` (método con siglas, marca `gus-pascaner`) y `ejemplos/dolor-lumbar/` (dato, comparación,
grilla, lista con íconos y placa libre).

```json
{ "marca": "<slug>", "firma": "Nombre · Marca", "cuenta": "@usuario", "formato": "4:5",
  "placas": [ { "tipo": "portada", "icono": "activity", "etiqueta": "…", "titulo": "…", "remate": "…" }, … ] }
```

## 5 · Renderizar y revisar
```bash
python3 ~/.claude/skills/carrusel/scripts/render.py "<carpeta>"
```
(Windows: `py -3 -X utf8 "%USERPROFILE%\.claude\skills\carrusel\scripts\render.py" "<carpeta>"`.)
Genera `placa_01.png` … y `hoja.jpg`. Los textos se achican solos si no entran.

**Mirar `hoja.jpg` con Read** (y las placas dudosas en grande) y corregir antes de mostrar — esto es dirección de arte,
no un trámite:
- nada cortado, encimado ni pegado al pie; ningún texto chico por exceso (si quedó chico, sintetizar más);
- cortes de línea feos (una palabra sola al final del título: reescribir o forzar `\n`);
- cada placa tiene un ancla visual (título grande, número, ícono o diagrama); si una se ve vacía o igual a la anterior,
  cambiarle el tipo, el fondo o sumarle un recurso;
- contraste suficiente y fondos alternados;
- la foto se ve nítida, el encuadre no corta lo importante (ajustar `foto_pos`) y el texto encima se lee bien.
Rehacer solo algunas: `--solo 3,5`.

## 6 · Texto de la publicación
Escribir `texto.txt` en la misma carpeta: primera línea = gancho, 2–4 párrafos cortos que resuman el carrusel, el CTA
del guion tal cual y, si suma, una línea final para guardar o compartir. ≤ 2200 caracteres; hashtags solo si los piden.

## 7 · Mostrar y programar
- Mandar las placas con SendUserFile (si existe) o listar las rutas, más el texto, y resumir en pocas líneas cómo se
  sintetizó y la dirección de arte.
- Preguntar si lo programa y cuándo. Con el OK, **seguir la skill `/publicar`** (invocarla con la carpeta, la cuenta,
  el texto de `texto.txt` y la fecha): ella sube, valida, confirma, programa y marca los archivos. La portada es la
  placa 1. Antes de proponer horario, mirar con `/publicar` qué hay programado ese día en la cuenta para no pisarlo.

## Si algo falla
- «No encontré Google Chrome»: instalarlo o definir la variable `CHROME` con la ruta del navegador.
- «No existe la marca»: el error lista las disponibles; si falta, crearla con `/marca` o sincronizar las marcas
  (repo `marcas-clientes` en `~/.config/motion/brands`).
- «No existe el ícono»: buscar el nombre con `scripts/iconos.py`.
- «Falta la clave de Pixabay»: va en `~/.config/pixabay/key` (o variable `PIXABAY_KEY`). Sin clave, seguir sin foto.
- Tipografía genérica en el render: revisar que existan los archivos de `fonts` que nombra `brand.json`.
