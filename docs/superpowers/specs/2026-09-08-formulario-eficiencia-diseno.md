# Rediseño de eficiencia del formulario clínico — Diseño

**Fecha:** 2026-09-08
**Archivo objetivo principal:** `formulario-produccion.html` (servido en `/formulario`)
**Commit base:** `ba1c80b`

## Objetivo

Reducir el largo visual del formulario clínico de 9 pasos sin perder información:
convertir grupos de opción única en listas desplegables, aprovechar el espacio
liberado con layout de 2 columnas, condicionar secciones por sexo, y eliminar
redundancias. "Eficiente = menos campos en pantalla, misma calidad de datos."

## Principio rector

El backend (`_mapear_formulario` en `app.py`) recibe el JSON de `collectData()`
**tal cual**, y para los campos de opción los valores llegan como **el texto
del label** (`sexo: "Femenino"`, `numHijos: "2"`, `pielTipo: "Mixta"`,
`nivelEstres: "4"`). Un `<select>` cuyas `<option>` tengan exactamente ese
mismo texto produce el mismo string. **Por eso la conversión radio→select NO
requiere cambios en `app.py`** siempre que se preserve el texto exacto de cada
opción y `collectData()` lea el `<select>` en vez del radio.

## Alcance

### 1. Convertir 14 campos de opción única a `<select>`

| # | Campo | id/name actual | Paso | Opciones (texto EXACTO a preservar) |
|---|---|---|---|---|
| 1 | Sexo | `name="sexo"` | 1 | Femenino / Masculino |
| 2 | Horario laboral | `name="horario_laboral"` | 1 | Mañana / Tarde / Noche / Variable / Otro |
| 3 | Número de hijos | `name="num_hijos"` | 1 | 0 / 1 / 2 / 3 / 4+ |
| 4 | ¿Cómo nos conociste? | `name="como_conociste"` | 1 | Internet / Google · Redes sociales · Recomendación de amigo/a · Paciente anterior · Otro |
| 5 | Si fuma, frecuencia | `name="fuma_frec"` | 2 | Diario / Ocasional |
| 6 | Si consume alcohol, frecuencia | `name="alcohol_frec"` | 2 | Diario / Semanal / Ocasional |
| 7 | Promedio de horas por noche | `name="horas_sueno"` | 2 | Menos de 5h / 5–7h / 7–9h / Más de 9h |
| 8 | Calidad del sueño | `name="calidad_sueno"` | 2 | Profundo y reparador / Interrumpido o ligero / Dificultad para conciliar / Insomnio frecuente |
| 9 | Frecuencia de consumo (dulces) | `name="dulces_frec"` | 4 | Diario / 2–3 veces/semana / 1 vez/semana / Ocasionalmente |
| 10 | ¿Cuántas comidas al día? | `name="comidas"` | 4 | 1 / 2 / 3 / 4+ |
| 11 | ¿Cómo describiría su piel? | `name="tipo_piel"` | 6 | Normal / Seca / Grasa / Mixta / Sensible / No lo sé |
| 12 | Nivel de actividad física | `name="act_fisica"` | 10 | Sedentario / Ligero (1–2/sem) / Moderado (3–4/sem) / Intenso (5+/sem) |
| 13 | Nivel de estrés diario | `scale-group#scale-estres` | 2 | 1..10 |
| 14 | Satisfacción con área a tratar | `scale-group#scale-satisfaccion` | 9 | 1..10 |

**No se convierten** (se quedan como están):
- Toggles `yn-row` Sí/No de una línea (ya son compactos: Fuma, Consume alcohol,
  cirugía, cansancio, etc.).
- Radio Sí/No "¿Algún familiar directo con enfermedades relevantes?"
  (`name="antecedentes_fam"`) — 2 opciones, 1 clic, se deja como radio-item
  (además tiene lógica de mostrar/ocultar el detalle).
- Grupos de checkboxes multi-selección (`check-grid`): áreas faciales,
  corporales, problemas de piel, etc. — un `<select>` simple no sirve.

**Nuevo componente CSS `select-field`:**
```css
.field select{
  appearance:none;-webkit-appearance:none;
  background:transparent;border:0;border-bottom:1px solid var(--border);
  padding:8px 24px 8px 0;font-family:'DM Sans',sans-serif;font-size:14px;
  font-weight:300;color:var(--text);cursor:pointer;width:100%;
  background-image:url("data:image/svg+xml,...chevron...");
  background-repeat:no-repeat;background-position:right 2px center;
}
.field select:focus{outline:none;border-bottom-color:var(--gold)}
.field select:invalid{color:var(--muted)} /* placeholder gris cuando value="" */
```
Cada `<select>` empieza con `<option value="" disabled selected>Selecciona…</option>`.

**`collectData()` — cambios por campo:**
Reemplazar cada expresión
```js
(document.querySelector('input[name="X":checked')||{closest…}).closest('.radio-item').textContent.trim()
```
por
```js
document.getElementById('f-X').value || ''
```
y para las escalas, `getScaleValue('scale-estres')` →
`document.getElementById('f-estres').value || ''` (mismo string "1".."10").

Campos de `collectData()` afectados (todos ya existen, solo cambia el modo de
lectura): `sexo`, `horarioLaboral` (mantener rama "Otro"→campo texto),
`numHijos`, `numHijosVal`, `comoConociste`, `pielTipo`, `actFisica`,
`nivelEstres`, `satisfaccion`, y las lecturas dentro de `fuma`, `alcohol`,
`sueno` (horas + calidad), `dulces_frec`, `comidas`.

**`initCheckboxes()` bloque `.radio-item`** (líneas ~1187-1196): sigue existiendo
para `antecedentes_fam`; no se toca. Los listeners de `horario_laboral`
(líneas 1164-1170, "Otro"→input) se re-implementan como `change` sobre el
`<select>`.

### 2. Sección "Condiciones hormonales" condicionada por sexo (paso 2)

Subsección líneas 292-301: envolver en `<div id="cond-hormonales">`.
- Quitar "(solo mujeres)" del título → "Condiciones hormonales".
- Fila "Andropausia" (línea 300, hoy `display:none`): quitar "(solo hombres)"
  del texto, dejar dentro de la subsección.
- Al cambiar el `<select>` de Sexo:
  - **Femenino** → mostrar embarazada, lactancia, SOP, anticonceptivos,
    menopausia, perimenopausia; ocultar Andropausia.
  - **Masculino** → ocultar las 6 anteriores; mostrar Andropausia.
  - Sin selección → estado inicial: todo oculto (o el estado actual, que es
    todas las de mujer visibles + andropausia oculta). Decisión: **todo oculto
    hasta elegir sexo**, para no mostrar campos que quizá no apliquen.
- Listener: en el `change` del `<select id="f-sexo">`, togglear `display` de
  cada `yn-row` por su texto de label.
- `collectData()`: `embarazo`, `lactancia`, `anticonceptivos`, `sop`,
  `menopausia`, `perimenopausia` ya se leen con `getYNValue(s3, ...)`. Si están
  ocultas y sin responder, `getYNValue` devuelve `'No respondido'` — igual que
  hoy si el paciente no las toca. **No requiere cambio de backend**; el prompt
  de la IA (`_datos_paciente`) ya tolera estos valores.
- **Andropausia**: hoy NO se recolecta en `collectData()`. Agregar
  `andropausia: getYNValue(s3, 'andropausia')` al objeto y
  `'andropausia': s('andropausia')` en `_mapear_formulario` (retorno del dict),
  más `_fila('andropausia', _g('andropausia'))` en `generar_docx_cuestionario`
  junto a las otras condiciones hormonales. Verificar primero si `_datos_paciente`
  arma alguna línea con andropausia (probable que no).

### 3. Layout de 2 columnas tras liberar espacio (eficiencia A)

`.form-grid` ya es `grid-template-columns:1fr 1fr` con `.full` para ancho
completo. Tras convertir a `<select>` (altura de 1 línea), quitar `.full` de
los campos que hoy lo tienen solo porque el radio-group era ancho:
- Paso 1: Horario laboral, Número de hijos, ¿Cómo nos conociste? → pasan a
  media columna, emparejados (Sexo | Fecha nac. ya están; Horario | Nº hijos;
  ¿Cómo nos conociste? | Ocupación).
- Paso 2: Promedio horas sueño | Calidad del sueño (par); Nivel de estrés entra
  como media columna al lado de otro campo (ver eficiencia E).
- Paso 4: Frecuencia dulces | ¿Cuántas comidas al día? (par).

Responsive: el `@media(max-width:520px)` ya colapsa a 1 columna. No se toca.

### 4. Fusionar toggle + frecuencia (eficiencias B y C)

- **Fuma** (`yn-row`, línea 305) + **Si fuma, frecuencia** (`<select>`, línea 306):
  el `<select>` de frecuencia arranca oculto (`display:none` en su `.field`).
  Listener en los `.yn-btn` de la fila "Fuma": si "Sí" → mostrar el select;
  si "No" → ocultar y resetear a `value=""`.
- **Consume alcohol** (línea 307) + **frecuencia** (línea 308): igual.
- `collectData()` para `fuma`/`alcohol` ya compone `"Sí - <frec>"` leyendo el
  radio marcado; cambiar la lectura del radio por
  `document.getElementById('f-fuma-frec').value`. Sin cambio de backend
  (el string resultante es idéntico).
- Reutiliza el patrón existente `toggleSolar`/`toggleRutina` (mostrar wrap en
  "Sí"). Se puede escribir una función genérica `toggleFrec(btn,val,selectId)`.

### 5. Nivel de estrés: sacarlo de subsección propia (eficiencia E)

Paso 2, subsección "Nivel de estrés" (líneas 340-357) ocupa un bloque entero
para 1 campo. Moverlo dentro de la subsección "Hábitos de sueño" como un
`<select>` 1–10 emparejado en 2 columnas con "Calidad del sueño" o debajo de
las horas de acostarse/levantarse. Eliminar la subsección vacía.
- `collectData().nivelEstres` sigue leyendo `#f-estres`. Sin cambio de backend.

### 6. Consolidar "Antecedentes Familiares" duplicado (eficiencia H)

Paso 10 tiene DOS subsecciones casi idénticas:
- Líneas 986-992 "Antecedentes Familiares y Contraindicaciones": incluye el
  `yn-row` **"¿En su familia hay historia de alguna enfermedad relevante?"** +
  otros 3 yn-row de contraindicaciones (alergias tópicas, infecciones cutáneas
  [ya oculto], marcapasos).
- Líneas 993-1007 "Antecedentes Familiares": radio Sí/No
  **"¿Algún familiar directo con enfermedades relevantes?"** + textarea
  "¿Cuáles?" condicional.

**Acción:** eliminar el `yn-row` "¿En su familia hay historia de alguna
enfermedad relevante?" (línea 988). Conservar el radio + detalle (líneas
996-1005), que es la versión que captura el "¿cuáles?".
- **Verificado (2026-09-08):** el `yn-row` "¿En su familia hay historia de
  alguna enfermedad relevante?" (línea 988) NO se lee en `collectData()` —
  ningún `getYNValue()` lo busca. Es huérfano. `antecedentesFam` viene solo del
  radio `name="antecedentes_fam"`. Borrar el yn-row es seguro.
- Renombrar la subsección 986 a "Contraindicaciones" (ya no lleva antecedentes).
- Mantener las otras 3 filas de esa subsección intactas.
- `_mapear_formulario` línea 2864 hace `'antecedentesFam': 'Ninguno'` y luego
  línea 2874 lo sobreescribe con `s('antecedentesFam')` — dejar el segundo, el
  primero es código muerto (no tocar en este spec salvo que estorbe).

### 7. Backup y reversión

- **Antes de tocar nada:**
  1. `cp formulario-produccion.html formulario-produccion.html.bak`
  2. `git add formulario-produccion.html.bak && git commit -m "chore: backup de formulario-produccion antes de rediseño de eficiencia"`
  3. `git tag pre-rediseno-formulario`
- **Para revertir:** `cp formulario-produccion.html.bak formulario-produccion.html`
  o `git checkout pre-rediseno-formulario -- formulario-produccion.html`, commit, push.
- El `.bak` se mantiene en el repo hasta que el rediseño se valide en producción;
  luego se puede borrar en un commit aparte.

### 8. Scripts de autofill (testing) — actualizar

`autofill-cuestionario.js` y `bookmarklet-cuestionario.js` usan
`clickRadio(name, label)` (busca `.radio-item`) y `clickScale(groupId, val)`
(busca `.scale-btn`). Tras la conversión:
- `clickRadio` para los 12 campos convertidos deja de funcionar.
- `clickScale` para los 2 deja de funcionar.

**Acción:** añadir helper `setSelect(id, text)` que asigne
`document.getElementById(id).value` por texto de opción y dispare `change`, y
reemplazar las llamadas afectadas. Es testing, no bloquea producción, pero se
actualiza en el mismo trabajo para no dejar el autofill roto.

## Fuera de alcance

- **Eficiencia F** (agrupar las 6 preguntas Sí/No de Intolerancias como grid de
  checkboxes) — descartada por el usuario.
- **Eficiencia G** (fusionar los 3 grids de "Problemas de piel" en uno) — no
  pedida; posible segunda ronda.
- **Eficiencia I** (consolidar pasos 9→7-8 renumerando `stepIds`) — no en esta
  ronda; alto riesgo en navegación.
- Modularizar `app.py` — sigue monolítico por convención.
- Cambiar `prompt_carvajal.txt` — no se carga en runtime.
- Tocar `formulario.html`, `formulario-demo.html`, `formulario-estetica-v*.html`
  — solo se rediseña `formulario-produccion.html`.

## Archivos que se tocan

| Archivo | Qué cambia |
|---|---|
| `formulario-produccion.html` | HTML de 14 campos, CSS `.field select`, `collectData()`, listeners de sexo/fuma/alcohol/horario, borrar subsección "Nivel de estrés" y yn-row duplicado, layout 2 col |
| `app.py` | SOLO: agregar `andropausia` en `_mapear_formulario` (retorno) y `generar_docx_cuestionario` (`_fila`). Nada más — el resto de campos convertidos no requiere cambio |
| `autofill-cuestionario.js` | helper `setSelect` + reemplazar `clickRadio`/`clickScale` de los 14 campos |
| `bookmarklet-cuestionario.js` | igual (regenerar el bookmarklet minificado) |
| `formulario-produccion.html.bak` | nuevo — copia de seguridad |
| `FIXLOG.md` | registrar el rediseño al terminar |

## Verificación (manual — no hay test suite)

Servidor local con `GROQ_KEY` (modelo barato). Abrir `/formulario`.

1. Los 14 campos se ven como lista desplegable de 1 línea.
2. Cada `<select>` tiene las opciones con el texto exacto de la tabla.
3. Layout: pares de campos lado a lado en escritorio; 1 columna en móvil (<520px).
4. Sexo = Femenino → aparecen las 6 condiciones hormonales, no Andropausia.
5. Sexo = Masculino → aparece solo Andropausia, no las 6.
6. Fuma = Sí → aparece el select de frecuencia; Fuma = No → desaparece.
   Igual para Alcohol.
7. Horario laboral = Otro → aparece el campo de texto libre.
8. Subsección "Nivel de estrés" ya no existe como bloque aparte; el campo está
   dentro de "Hábitos de sueño".
9. Paso 10: una sola pregunta de antecedentes familiares (radio + ¿cuáles?).
10. Autofill de consola llena los 14 selects correctamente.
11. `submitForm()` → inspeccionar payload de red (`POST /enviar`): `sexo`,
    `numHijos`, `pielTipo`, `nivelEstres`, `satisfaccion`, `actFisica`,
    `comoConociste`, `horarioLaboral`, `fuma`, `alcohol` traen los mismos
    strings que antes del rediseño (comparar con un envío de la versión `.bak`).
12. Esperar generación del plan → sin `KeyError` en logs.
13. Abrir el `.docx`: campos de opción reflejan lo elegido; fila `andropausia`
    presente si sexo=Masculino.
14. Abrir el plan HTML: carga sin errores; edad, IMC, perfil correctos.

## Riesgos

- **Texto de opción desalineado:** si una `<option>` difiere en un carácter
  (guion `–` vs `-`, tilde, espaciado) del label del radio original, el string
  que llega al backend cambia y el prompt de la IA o el docx puede mostrar algo
  raro. Mitigación: copiar el texto literal del HTML actual, verificación #11.
- **`getYNValue` y secciones ocultas:** al ocultar condiciones hormonales por
  sexo, `getYNValue` devuelve `'No respondido'`. Confirmar que
  `_datos_paciente` y el docx toleran ese valor (hoy ya puede pasar si el
  paciente no responde). Bajo riesgo.
- **Autofill roto a mitad:** si se actualiza el HTML pero no el autofill, las
  pruebas manuales se vuelven lentas. Por eso el autofill va en el mismo trabajo.
- **Sesiones parciales:** `POST /sesion/guardar` guarda `collectData()` en
  Cloudinary, pero el formulario NO tiene código de restauración en el frontend
  (`SESSION_ID` se genera nuevo en cada carga; no lee `?session=`). La
  reanudación la maneja el backend vía `/panel/regenerar`. Como los `value` de
  `collectData()` no cambian (solo de dónde se leen), no hay riesgo. Verificado
  2026-09-08.
