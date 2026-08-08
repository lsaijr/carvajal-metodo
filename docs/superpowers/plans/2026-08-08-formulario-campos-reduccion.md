# Reducción de campos del formulario — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. No automated test suite exists in this repo — verification is manual (see each task's "Verify" step).

**Goal:** Ocultar (display:none) los 70 campos marcados "Quitar" en la revisión de campos del cliente (email 31-jul-2026, `/formulario-seleccion`) en `formulario-produccion.html`, dejar de recolectarlos/procesarlos en el pipeline (`collectData()` → `_mapear_formulario` → docx), y corregir 5 bugs preexistentes en campos que quedan "Mantener".

**Architecture:** Cambios en 2 archivos: `formulario-produccion.html` (HTML + JS inline) y `app.py` (`_mapear_formulario`, `generar_docx_cuestionario`). No se toca `_datos_paciente()` — se verificó que ningún campo que lee está marcado "Quitar" (ver spec en `FIXLOG.md`, sección "Diseño 2026-08-08"). No se toca `prompt_carvajal.txt` ni las plantillas Jinja (`plantilla_plan.html`/`plantilla_borrador.html`) — ninguno de sus placeholders `{{...}}` usa un campo "Quitar".

**Tech Stack:** Flask monolito (`app.py`), HTML/JS vanilla sin build (`formulario-produccion.html`).

## Global Constraints

- Ocultar con `display:none` en el contenedor del campo (label + input + detalle condicional), NO eliminar el markup/JS.
- No modularizar ni reorganizar `app.py` — sigue monolítico por convención del proyecto.
- No hay test suite automatizado — cada task termina con pasos de verificación manual (grep, revisión visual, o server local si aplica).
- El spec completo (mapeo campo→código, lista de 150 campos) vive en `FIXLOG.md`, sección "Diseño 2026-08-08: Reducción de campos del formulario según revisión del cliente". Consultar ahí ante cualquier duda de si un campo es Mantener/Quitar.
- Commits frecuentes, uno por task.

---

### Task 1: Ocultar Step 8 completo (Evaluación Capilar) — sección huérfana

**Files:**
- Modify: `formulario-produccion.html:698-699` (apertura del `<div class="step-panel" id="step-8">`)

Toda la sección "Evaluación Capilar" (12 preguntas, todas "Quitar": desde cuándo cae, la caída es, síntomas asociados, factores recientes, antecedentes familiares alopecia, tratamientos previos caída, deseas reducir/eliminar vello, zonas interés, métodos previos depilación, aumento reciente vello, cambios hormonales recientes, reacciones previas depilación) ya es huérfana hoy — ninguna de sus preguntas se recolecta en `collectData()`. Cero riesgo backend.

- [ ] **Step 1: Ocultar el step-panel completo**

Cambiar:
```html
<div class="step-panel" id="step-8">
```
a:
```html
<div class="step-panel" id="step-8" style="display:none">
```

- [ ] **Step 2: Verificar que el step navigation salte el step 8**

Buscar en el JS la lógica de navegación entre steps (`goToStep`, contador de steps, `nav-bar`). Si la navegación itera sobre `.step-panel` visibles o cuenta pasos por índice fijo (1-11), confirmar que ocultar el panel no rompe la barra de progreso ni dejar un paso "fantasma" en blanco al navegar. Si la navegación es por índice fijo (no por panels visibles), ajustar el contador de "paso X de 11" a "paso X de 10" y renumerar cualquier referencia visible al número de step 9/10/11 restantes.

Run: `grep -n "goToStep\|totalSteps\|step-panel" formulario-produccion.html`

Ajustar cualquier lógica que dependa de contar steps 1-11 literalmente.

- [ ] **Step 3: Commit**

```bash
git add formulario-produccion.html
git commit -m "fix: oculta step 8 (Evaluación Capilar), sección sin conexión backend"
```

---

### Task 2: Ocultar campos huérfanos individuales (Datos Personales + Condición Actual)

**Files:**
- Modify: `formulario-produccion.html` (varias líneas, sección Datos Personales y Condición Actual)

Campos "Quitar" que hoy NO se recolectan en `collectData()` (huérfanos, cero riesgo backend): "¿Trabaja actualmente?", "¿Con quién vive?", "Familiares en casa (relación)", "¿Cuenta con ayuda en casa?", "Tipo de apoyo recibido", "Nivel de actividad laboral" — **ojo, este último SÍ se recolecta (`actLaboral`), no es huérfano, va en Task 3** —, "¿A qué hora del día?" (baño), "¿Utiliza medicamento/suplemento para dormir?", "¿Trabaja en turnos nocturnos?", "Andropausia", "Otros problemas de piel no mencionados" (`#f-otros-piel`).

- [ ] **Step 1: Localizar y ocultar cada campo**

Para cada campo de la lista, buscar su bloque `<div class="field">...</div>` o `<div class="yn-row">...</div>` completo en el HTML y envolverlo o marcarlo con `style="display:none"` en el div contenedor exterior (no solo el input). Ejemplo de patrón:

```bash
grep -n "Trabaja actualmente\|Con quién vive\|Familiares en casa\|Cuenta con ayuda en casa\|Tipo de apoyo recibido\|A qué hora del día\|medicamento o suplemento para dormir\|turnos nocturnos\|Andropausia\|f-otros-piel" formulario-produccion.html
```

Añadir `style="display:none"` al `<div class="field">` o `<div class="yn-row">` que envuelve cada uno (verificar el div padre correcto leyendo 2-3 líneas de contexto antes de editar, ya que varios campos comparten patrón `.yn-row` genérico y hay que confirmar cuál es cuál por el texto del label).

- [ ] **Step 2: Verificar que ninguno de estos aparece en collectData()**

```bash
grep -n "trabaja\|conQuienVive\|familiares\|ayudaCasa\|tipoApoyo\|banioHora\|medicamentoDormir\|turnoNocturno\|andropausia\|otrosPiel" formulario-produccion.html
```

Confirmar que ninguna de estas claves aparece dentro de la función `collectData()` (líneas ~1223-1516). Si alguna sí aparece, anotarla — significa que el reporte de exploración se equivocó y ese campo requiere también Task 3/4 (tocar `app.py`).

- [ ] **Step 3: Commit**

```bash
git add formulario-produccion.html
git commit -m "fix: oculta campos huérfanos de Datos Personales y Condición Actual marcados Quitar"
```

---

### Task 3: Ocultar campos conectados de Datos Personales + Condición Actual, y actualizar `collectData()` + `_mapear_formulario`

**Files:**
- Modify: `formulario-produccion.html` (HTML de los campos + función `collectData()` líneas 1223-1516)
- Modify: `app.py` (`_mapear_formulario`, retorno del dict líneas ~2865-2940)
- Modify: `app.py` (`generar_docx_cuestionario`, líneas ~2419-2469)

Campos "Quitar" que SÍ fluyen hoy al backend:

- **Nivel de actividad laboral** (`actLaboral`) — HTML: radio `name="act_laboral"`. JS: línea 1384. Backend: `_mapear_formulario` línea 2873 (`'actLaboral': s('actLaboral')`), usado en `_datos_paciente()` línea 3200 y docx línea 2430.

  **Este campo SÍ es usado por `_datos_paciente()` (prompt IA)** — la exploración previa lo listó como "Quitar" pero también como usado en el prompt. Antes de tocar nada, confirmar con el usuario si de verdad quiere quitar "Nivel de actividad laboral" del prompt de la IA (afecta cómo la IA arma el plan de actividad física). Si confirma, seguir estos pasos; si no, dejar este campo como "Mantener" y saltar su tratamiento en este task.

- **¿Cómo es tu evacuación?** (`evacuacion`) — HTML: radio `name="evacuacion"`. JS: línea 1486. Backend: `_mapear_formulario` línea 2918, docx línea 2464.

- [ ] **Step 1: Confirmar con el usuario el caso "Nivel de actividad laboral"**

Antes de modificar código, preguntar explícitamente: el campo está marcado "Quitar" en la revisión pero alimenta el prompt de la IA (`d['actLaboral']` en `_datos_paciente()` línea 3200) y el docx. Confirmar si se quita de todos lados o se deja.

- [ ] **Step 2: Ocultar en HTML**

Para `actLaboral` (si se confirma quitar) y `evacuacion`: envolver su `<div class="field">` o grupo de radios en `style="display:none"`.

- [ ] **Step 3: Quitar de `collectData()`**

En `formulario-produccion.html`, dentro del objeto retornado por `collectData()` (línea 1372+), eliminar las líneas:
```js
actLaboral:     (document.querySelector('input[name="act_laboral"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
y
```js
evacuacion:         (document.querySelector('input[name="evacuacion"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
(solo si se confirmó quitar `actLaboral` en Step 1; `evacuacion` se quita siempre).

- [ ] **Step 4: Quitar de `_mapear_formulario` en `app.py`**

Eliminar las líneas correspondientes del dict de retorno:
```python
'actLaboral':          s('actLaboral'),
```
```python
'evacuacion':          s('evacuacion'),
```

- [ ] **Step 5: Actualizar `_datos_paciente()` si se quitó `actLaboral`**

Si `actLaboral` se eliminó, en `app.py` función `_datos_paciente` (línea ~3200):
```python
Ocupacion: {d['ocupacion']} | Horario: {d['horarioLaboral']} | Act.laboral: {d['actLaboral']}
```
cambiar a:
```python
Ocupacion: {d['ocupacion']} | Horario: {d['horarioLaboral']}
```
(quitar la referencia a `d['actLaboral']` para no causar `KeyError`).

- [ ] **Step 6: Quitar filas del docx en `generar_docx_cuestionario`**

En `app.py`, eliminar (si aplica `actLaboral`):
```python
_fila('nivel_actividad_laboral',  _g('actLaboral'))
```
y siempre:
```python
_fila('evacuacion',        _g('evacuacion'))
```

- [ ] **Step 7: Verificar no quedan referencias colgantes**

```bash
grep -n "actLaboral\|evacuacion" app.py formulario-produccion.html
```
Confirmar que las únicas coincidencias restantes son comentarios o casos ya intencionalmente conservados (ej. `actividad_fisica`/`actFisica` es un campo DISTINTO que se mantiene — no confundir).

- [ ] **Step 8: Commit**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: oculta y desconecta campos Quitar de Datos Personales/Condición Actual (actLaboral, evacuacion)"
```

---

### Task 4: Ocultar 8 de 14 preguntas de Intolerancias Alimentarias (huérfanas)

**Files:**
- Modify: `formulario-produccion.html`

Solo 6 de las 14 preguntas de "Intolerancias Alimentarias" están conectadas (`hinchazon_abdominal`, `gases`, `estrenimiento`, `cansancio_comidas`, `digestion_lenta`, `nauseas` — vía `sintomasMap` línea 1265-1272). Las otras 8 (Migrañas recurrentes, Picazón/urticaria, Congestión nasal, Inflamación articular, Cambios de humor, Dificultad bajar peso, Antecedentes familiares intolerancias, y una octava — verificar contra FIXLOG.md tabla 3 cuál es la última) ya son huérfanas hoy. Según la revisión del cliente, de estas 14: "Hinchazón abdominal" (Mantener), "Gases" (Mantener), "Estreñimiento/diarrea" (Quitar), "Cansancio tras comidas" (Quitar), "Dolor de cabeza/migrañas" (Mantener — **ojo, migrañas es huérfana pero está marcada Mantener**), "Picazón/urticaria" (Quitar), "Congestión nasal" (Quitar), "Inflamación articular" (Mantener — **huérfana pero Mantener**), "Cambios de humor" (Quitar), "Digestión lenta" (Quitar), "Dificultad bajar peso" (Mantener — huérfana pero Mantener), "Náuseas" (Mantener), "Antecedentes familiares" (Quitar).

- [ ] **Step 1: Releer la tabla exacta antes de tocar nada**

Abrir `FIXLOG.md`, sección "Diseño 2026-08-08", Tabla 3 (Intolerancias Alimentarias) para confirmar exactamente qué 8 de las 14 preguntas están marcadas "Quitar" — esta lista de arriba es una reconstrucción aproximada de la conversación, no copiar sin verificar contra la imagen original del email si hay duda.

- [ ] **Step 2: Ocultar únicamente las marcadas "Quitar"**

Para cada una: localizar su `.yn-row` en `formulario-produccion.html` (sección step-4, "Intolerancias Alimentarias") por el texto del label, envolver en `style="display:none"`. Dejar visibles las marcadas "Mantener" aunque sean huérfanas hoy (no se tocan en este task — quedan como están, el usuario las quiere seguir viendo aunque no se procesen; si se quiere conectarlas al backend, eso es trabajo nuevo fuera de este spec).

- [ ] **Step 3: Verificar que las 6 conectadas quitadas (si alguna lo está) se limpien del `sintomasMap`**

```bash
grep -n "sintomasMap" formulario-produccion.html
```
Si alguna de las 6 preguntas conectadas (`hinchazon_abdominal`, `gases`, `estrenimiento`, `cansancio_comidas`, `digestion_lenta`, `nauseas`) está marcada "Quitar" en la tabla real, eliminar su entrada del objeto `sintomasMap` (línea 1265-1272) y de `sintomas_map` en `app.py` `_mapear_formulario` (línea ~2850-2857), y de la sección docx correspondiente (líneas 2473-2478).

- [ ] **Step 4: Commit**

```bash
git add formulario-produccion.html
git commit -m "fix: oculta preguntas Quitar de Intolerancias Alimentarias"
```

---

### Task 5: Ocultar casi toda la sección Preferencias Alimentarias (14 de 16 campos)

**Files:**
- Modify: `formulario-produccion.html` (HTML + `collectData()`)
- Modify: `app.py` (`_mapear_formulario` + `generar_docx_cuestionario` + posiblemente `_datos_paciente`)

De 16 campos en "Preferencias Alimentarias", solo "¿Cuántas comidas al día?" y "Observaciones adicionales" quedan "Mantener". Todo lo demás (proteínas favoritas/evitar, carbohidratos favoritos/evitar, verduras consume/no tolera, frutas, grasas saludables/evitar, por qué evitarlas, postres, frecuencia consumo, bebidas azucaradas) se oculta.

**Importante:** `proteinas`, `carbohidratos`, `verduras`, `frutas`, `alimentosEvitar`, `postres`, `bebidas` SÍ se usan en `_datos_paciente()` (línea 3225-3227) y en el docx. "¿Cuántas comidas al día?" y "Observaciones adicionales" (`notasAlimentacion`) son los ÚNICOS que quedan — y "¿Cuántas comidas al día?" hoy es huérfano (no está en `collectData()`).

- [ ] **Step 1: Ocultar en HTML todos los campos "Quitar" de esta sección**

Localizar en `formulario-produccion.html` la sección "Preferencias Alimentarias" (dentro de step-4, después de intolerancias) y ocultar: proteínas favoritas (`chk-proteinas`), proteínas evitar (`f-proteinas-evitar`), carbohidratos favoritos (`chk-carbos`), carbohidratos evitar (`f-carbos-evitar`), verduras consume (`f-verduras`), verduras no tolera (`f-verduras-evitar`), frutas (`f-frutas`), grasas saludables (checkboxes sin id, sección grasas), grasas evitar (`step-4` grasas checkboxes), por qué evitarlas (`f-grasas-evitar-porque`), postres (`f-postres`), frecuencia consumo (radio, huérfano), bebidas azucaradas (yn-row + `f-bebidas-cuales`).

- [ ] **Step 2: Actualizar `collectData()`**

En `formulario-produccion.html`, quitar del objeto retornado por `collectData()`:
```js
proteinas:           proteinasSelec,
carbohidratos:       carbosSelec,
verduras:            verduras,
frutas:              frutas,
alimentosEvitar:     alimentosEvitar,
postres:             document.getElementById('f-postres').value||'',
bebidas:             bebidas,
grasasEvitar:       getCheckedValues('step-4').filter(v=>['Alimentos fritos','Manteca / Margarina','Aceites vegetales procesados','Grasas trans'].includes(v)),
grasasEvitarPorque: document.getElementById('f-grasas-evitar-porque')?document.getElementById('f-grasas-evitar-porque').value||'':'',
```
y las variables intermedias que ya no se usan (`proteinasSelec`, `proteinasEvitar`, `carbosSelec`, `carbosEvitar`, `verduras`, `verdurasEvitar`, `frutas`, `alimentosEvitar`, `bebidasYN`, `bebidasCuales`, `bebidas`) definidas más arriba en la función (líneas 1240-1253, 1355-1358). Dejar `notasAlimentacion` (Observaciones adicionales, se mantiene).

- [ ] **Step 3: Actualizar `_mapear_formulario` en `app.py`**

Eliminar del dict de retorno (líneas ~2932-2938):
```python
'proteinas':           s('proteinas'),
'carbohidratos':       s('carbohidratos'),
'verduras':            s('verduras'),
'frutas':              s('frutas'),
'alimentosEvitar':     s('alimentosEvitar'),
'postres':             s('postres'),
'bebidas':             s('bebidas'),
```

- [ ] **Step 4: Actualizar `_datos_paciente()` en `app.py`**

En el f-string (líneas 3223-3228), cambiar:
```python
ALIMENTACION:
Intolerancias: {', '.join(d['intolerancias']) or 'Ninguna'}
Proteinas: {d['proteinas']} | Carbos: {d['carbohidratos']}
Verduras: {d['verduras']} | Frutas: {d['frutas']}
Evitar: {d['alimentosEvitar']}
Notas: {d['notasAlimentacion']}
```
a:
```python
ALIMENTACION:
Intolerancias: {', '.join(d['intolerancias']) or 'Ninguna'}
Notas: {d['notasAlimentacion']}
```

- [ ] **Step 5: Actualizar `generar_docx_cuestionario` en `app.py`**

Eliminar las filas correspondientes (líneas ~2525-2544), dejando solo lo que aplica a campos que quedan Mantener (ninguna fila directa de esta subsección sobrevive salvo si se decide agregar "cuántas comidas al día" — ver Task 9 sobre campos huérfanos "Mantener" nuevos, fuera de alcance salvo pedido explícito). Eliminar bloque completo de `_fila('proteina_*', ...)`, `_fila('evitar_*', ...)`, `_fila('carb_*', ...)`, `_fila('verduras_*', ...)`, `_fila('postres_favoritos', ...)`, `_fila('bebidas_azucaradas', ...)`. Conservar `_fila('observaciones_alimentarias', _g('notasAlimentacion'))`.

- [ ] **Step 6: Verificar variables huérfanas removidas no dejan referencias sueltas**

```bash
grep -n "prot_str\|carb_str\|gras_str" app.py
```
Estas variables (usadas para las heurísticas `'pollo' in prot_str`, etc.) probablemente se calculan a partir de `_g('proteinas')` etc. más arriba en `generar_docx_cuestionario` — si ya no hay `_fila` que las use, eliminar también su cálculo previo (buscar `prot_str =`, `carb_str =`, `gras_str =`).

- [ ] **Step 7: Commit**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: oculta y desconecta Preferencias Alimentarias, deja solo notas y comidas/día"
```

---

### Task 6: Alergias y Sensibilidades — ocultar 8 de 11, actualizar collectData/mapeo/docx/prompt

**Files:**
- Modify: `formulario-produccion.html`
- Modify: `app.py`

Quedan "Mantener": Medicamentos en general, Alimentos en general, Otro. Se ocultan: Lidocaína, Penicilina, Yodopovidona, Antiinflamatorios, Mariscos/algas, Látex, Aloe vera, Fragancias/perfumes.

- [ ] **Step 1: Ocultar en HTML**

En `formulario-produccion.html`, para cada key `alg_lidocaina`, `alg_penicilina`, `alg_yodo`, `alg_aines`, `alg_mariscos`, `alg_latex`, `alg_aloe`, `alg_fragancias`: ocultar el `.yn-row` correspondiente `id="arow-alg_X"` con `style="display:none"`.

- [ ] **Step 2: Actualizar `alergiaKeys` en `collectData()`**

En `formulario-produccion.html` línea 1281-1293, quitar del array `alergiaKeys` las entradas de los 8 campos ocultados, dejando solo:
```js
const alergiaKeys=[
  ['alg_medicamentos','Medicamentos'],
  ['alg_alimentos','Alimentos'],
  ['alg_otro','Otro'],
];
```

- [ ] **Step 3: Actualizar objeto `contra` (contraindications) en `collectData()`**

Línea 1304-1316: quitar las entradas que referencian los campos ocultados:
```js
'Alergia lidocaina':  getYNValue(document.getElementById('step-5'),'lidocaína'),
'Alergia penicilina': getYNValue(document.getElementById('step-5'),'penicilina'),
'Alergia yodo':       getYNValue(document.getElementById('step-5'),'yodopovidona'),
'Alergia AINEs':      getYNValue(document.getElementById('step-5'),'antiinflamatorios'),
'Alergia latex':      getYNValue(document.getElementById('step-5'),'látex'),
```
Dejar solo `Embarazo`, `Lactancia`, `Anticonceptivos`, `SOP`, `Menopausia`, `Tabaquismo`.

- [ ] **Step 4: Quitar campos individuales `alergia_*` del retorno de `collectData()`**

Líneas 1477-1483: quitar
```js
alergia_lidocaina:  getYNValue(document.getElementById('step-5'),'lidocaína'),
alergia_penicilina: getYNValue(document.getElementById('step-5'),'penicilina'),
alergia_yodo:       getYNValue(document.getElementById('step-5'),'yodopovidona'),
alergia_aines:      getYNValue(document.getElementById('step-5'),'antiinflamatorios'),
alergia_latex:      getYNValue(document.getElementById('step-5'),'látex'),
alergia_aloe:       getYNValue(document.getElementById('step-5'),'aloe'),
alergia_fragancias: getYNValue(document.getElementById('step-5'),'fragancias'),
```

- [ ] **Step 5: Actualizar `_mapear_formulario` en `app.py`**

Quitar del dict de retorno (líneas 2911-2917):
```python
'alergia_lidocaina':   s('alergia_lidocaina'),
'alergia_penicilina':  s('alergia_penicilina'),
'alergia_yodo':        s('alergia_yodo'),
'alergia_aines':       s('alergia_aines'),
'alergia_latex':       s('alergia_latex'),
'alergia_aloe':        s('alergia_aloe'),
'alergia_fragancias':  s('alergia_fragancias'),
```

- [ ] **Step 6: Actualizar `generar_docx_cuestionario` en `app.py`**

Quitar filas (líneas 2496-2502):
```python
_fila('alergia_lidocaina',    _g('alergia_lidocaina'))
_fila('alergia_penicilina',   _g('alergia_penicilina'))
_fila('alergia_yodo',         _g('alergia_yodo'))
_fila('alergia_aines',        _g('alergia_aines'))
_fila('alergia_latex',        _g('alergia_latex'))
_fila('alergia_aloe',         _g('alergia_aloe'))
_fila('alergia_fragancias',   _g('alergia_fragancias'))
```
Dejar `_fila('alergia_medicamentos', ...)`.

- [ ] **Step 7: Verificar `_datos_paciente()` no rompe**

`_datos_paciente()` solo usa `d['alergias']` (string agregado general, línea 3216) — no referencia las claves individuales `alergia_lidocaina` etc. directamente. Confirmar con:
```bash
grep -n "d\['alergia" app.py
```
Si no hay coincidencias fuera de `_mapear_formulario`/docx ya tratados, no requiere cambio adicional.

- [ ] **Step 8: Commit**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: oculta y desconecta 8 alergias específicas marcadas Quitar"
```

---

### Task 7: Historial Quirúrgico y Piel — ocultar Textura/superficie y Oleosidad, arreglar bug `pielProblemas`

**Files:**
- Modify: `formulario-produccion.html`
- Modify: `app.py`

Se ocultan: "Textura y superficie", "Oleosidad", "Sensibilidades". Quedan "Mantener": ¿Cirugía?, ¿Cómo describiría su piel?, Inflamación/Brotes, Pigmentación, Envejecimiento cutáneo, Otros problemas no mencionados.

**Bug a arreglar (Task del spec, punto 1):** `_mapear_formulario` línea 2883 asigna `'pielProblemas': faciales` (usa `areasFaciales`, variable equivocada) en vez de los checkboxes reales del step-6. Esto significa que HOY los checkboxes de piel (incluidos los que quedan Mantener: Inflamación/Brotes, Pigmentación, Envejecimiento cutáneo) no llegan ni al docx ni al prompt IA correctamente.

- [ ] **Step 1: Ocultar en HTML los 3 subgrupos "Quitar"**

En `formulario-produccion.html` líneas 675-680 (Textura y superficie, Oleosidad) y línea 690-692 (Sensibilidades): añadir `style="display:none"` a cada `<div class="field" style="margin-top:12px">` correspondiente.

- [ ] **Step 2: Arreglar el bug de `pielProblemas` en `_mapear_formulario`**

En `app.py`, el JS ya envía correctamente `pielProblemas: problemasPiel` (línea 1428, `formulario-produccion.html`, donde `problemasPiel=getCheckedValues('step-6')`). El problema es solo en el backend. En `app.py`, cambiar línea 2883:
```python
'pielProblemas':       faciales,
```
a:
```python
'pielProblemas':       lst('pielProblemas'),
```
(usando la misma función helper `lst()` que ya se usa para `areasFaciales`/`areasCorporales` en el mismo bloque — verificar su firma exacta antes, buscar `def lst(` en `_mapear_formulario`).

Repetir el mismo cambio en la segunda ocurrencia de `'pielProblemas': faciales,` en línea 3110 (otra función que arma un dict similar — verificar de qué función es antes de tocar, con `sed -n '3090,3115p' app.py` o Read).

- [ ] **Step 3: Verificar que `getCheckedValues('step-6')` en el JS ahora solo captura los 3 subgrupos que quedan visibles**

Como Textura/Oleosidad/Sensibilidades quedaron con `display:none`, sus checkboxes ya no estarán "checked"-eables por el usuario, pero si `getCheckedValues` itera todo `#step-6` sin filtrar por visibilidad, technically el array `pielProblemas` solo contendrá lo que el usuario pudo marcar (los visibles), así que no requiere cambio adicional en `getCheckedValues`.

- [ ] **Step 4: Verificar docx (`_yn_p`) sigue funcionando con el `pielProblemas` corregido**

`_yn_p` (línea 2408) hace keyword-match sobre `piel_raw = data.get('pielProblemas', []) or []` (línea 2385). Con el bug arreglado, ahora buscará dentro de los checkboxes reales de piel en vez de las áreas faciales — esto es el comportamiento correcto/esperado. Confirmar visualmente en la prueba manual (Task 10) que "prob_manchas_solares", "prob_flacidez", etc. del docx reflejan lo marcado en el step-6 real, no en "áreas a tratar".

- [ ] **Step 5: Ocultar "Textura y superficie" y "Oleosidad" y "Sensibilidades" no deben afectar el `_yn_p` de los que quedan (manchas, pecas, líneas finas, flacidez, luminosidad, ardor)**

Revisar que las keywords que sí se mantienen visibles (Pigmentación: "manchas", "pecas"; Envejecimiento: "líneas", "arrugas", "flacidez", "luminosidad") sigan existiendo como checkboxes visibles — sí, porque esos subgrupos NO se ocultan. Solo "ardor"/"sensibil" (de Sensibilidades) se pierde — confirmar que `_fila('prob_ardor', ...)` en docx (línea 2556) ahora siempre dará 'NO' porque su checkbox está oculto; esto es esperado (campo Quitar) — no requiere quitar la fila del docx porque simplemente reportará NO consistentemente, pero para limpieza, considerar quitar `_fila('prob_ardor', ...)` también ya que su fuente desapareció. Quitarla:
```python
_fila('prob_ardor',               'SÍ' if _yn_p(['ardor','sensibil']) == 'SÍ' else 'NO')
```

- [ ] **Step 6: Commit**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: oculta Textura/Oleosidad/Sensibilidades de piel y corrige bug pielProblemas usando areasFaciales por error"
```

---

### Task 8: Objetivos y Estética Previa — ocultar 12 tratamientos, conectar "¿Entiende múltiples sesiones?"

**Files:**
- Modify: `formulario-produccion.html`
- Modify: `app.py`

Se ocultan: Botox, Rellenos dérmicos, Hilos tensores, Peeling químico, Láser facial/corporal, Microblading, Mesoterapia, Radiofrecuencia, Criolipólisis, ¿En tratamiento con láser actualmente?, ¿Qué expectativas tiene?. Quedan "Mantener": ¿Tratamientos estéticos anteriormente?, Otro tratamiento estético, ¿Complicaciones con tratamiento previo?, Áreas FACIALES/CORPORALES, ¿Cuál es su PRIORIDAD?, Satisfacción actual, ¿Entiende múltiples sesiones?.

**Bug a arreglar (spec punto 4 y 5):** `_fila('tratamiento_otro', 'NO')` hardcodeado (línea 2596) ignora si el paciente marcó "Otro tratamiento estético" real. `_fila('entiende_sesiones', 'SÍ')` hardcodeado (línea 2613) y el campo no está conectado en absoluto — hay que conectarlo de cero.

- [ ] **Step 1: Ocultar en HTML los 9 tratamientos específicos + los 2 campos sueltos**

En `formulario-produccion.html`, ocultar los bloques `#trat-row-botax`, `#trat-row-rellenos`, `#trat-row-hilos`, `#trat-row-peeling`, `#trat-row-laser`, `#trat-row-microblading`, `#trat-row-mesoterapia`, `#trat-row-radiofrecuencia`, `#trat-row-criolipolisis` (y sus `-det`/`-fecha`/`-zona` asociados si son contenedores separados — verificar estructura exacta con `grep -n "trat-row-botax" formulario-produccion.html` primero). Dejar visible `#trat-row-otro_estetico`. Ocultar el yn-row de "¿Actualmente está en tratamiento con láser?" y su detalle `#f-laser-det`. Ocultar `#f-expectativas`.

- [ ] **Step 2: Actualizar `tratKeys` en `collectData()`**

En `formulario-produccion.html` línea 1319-1330, reducir el array a solo:
```js
const tratKeys=[
  ['otro_estetico','Otro tratamiento estético','Otro'],
];
```

- [ ] **Step 3: Quitar `laserActivo` y `expectativas` del retorno de `collectData()`**

Líneas 1447 y 1443:
```js
laserActivo:      getYNValue(s9,'actualmente está en tratamiento con láser'),
```
```js
expectativas:     document.getElementById('f-expectativas').value||'',
```
Eliminar ambas.

- [ ] **Step 4: Conectar "¿Entiende que pueden necesitarse múltiples sesiones?" en `collectData()`**

Este campo (yn-row, línea 923 del HTML, sin id propio) hoy NO se recolecta. Agregar al objeto retornado por `collectData()`:
```js
entiendeSesiones: getYNValue(s9, 'necesitarse múltiples sesiones'),
```
(usando `s9` que ya está definido como `document.getElementById('step-9')` al inicio de la función, línea 1227 — verificar que el yn-row de este campo efectivamente está dentro de `#step-9` antes de asumir, con `grep -n "step-9\|múltiples sesiones" formulario-produccion.html`).

- [ ] **Step 5: Actualizar `_mapear_formulario` en `app.py`**

Quitar:
```python
'laserActivo':         'Si' if s('laserActivo').lower() in ['si','sí','yes'] else 'No',
```
```python
'expectativas':        s('expectativas'),
```
Agregar:
```python
'entiendeSesiones':    'Si' if s('entiendeSesiones').lower() in ['si','sí','yes'] else 'No',
```

- [ ] **Step 6: Arreglar `tratamiento_otro` en `generar_docx_cuestionario`**

Cambiar línea 2596:
```python
_fila('tratamiento_otro',         'NO')
```
a leer el dato real — el patrón existente usa `_yn_h(key)` para los demás tratamientos (ej. `_yn_h('botox')`), buscar la definición de `_yn_h` (probablemente busca `key in hist_lst` o similar) y aplicar igual para `'otro'`:
```python
_fila('tratamiento_otro',         _yn_h('otro'))
```
(confirmar el nombre exacto de la clave usada en `historialEstetico` para "Otro" — según `tratKeys` del JS es `'Otro'` con mayúscula, verificar consistencia con `_yn_h` antes de aplicar).

- [ ] **Step 7: Arreglar `entiende_sesiones` en `generar_docx_cuestionario`**

Cambiar línea 2613:
```python
_fila('entiende_sesiones',    'SÍ')
```
a:
```python
_fila('entiende_sesiones',    _g('entiendeSesiones'))
```

- [ ] **Step 8: Quitar filas docx de los 9 tratamientos ocultados y `laser_actual`/`expectativas`**

Eliminar de `generar_docx_cuestionario` (líneas 2578-2595, 2597-2598, 2611):
```python
_fila('tratamiento_rellenos', ...) / rellenos_fecha / rellenos_zonas
_fila('tratamiento_hilos', ...) / hilos_fecha
_fila('tratamiento_peeling', ...) / peeling_fecha
_fila('tratamiento_laser', ...) / laser_tipo / laser_fecha
_fila('tratamiento_microblading', ...) / microblading_fecha
_fila('tratamiento_mesoterapia', ...) / mesoterapia_fecha
_fila('tratamiento_radiofrecuencia', ...) / radiofrecuencia_fecha
_fila('tratamiento_criolipolisis', ...) / criolipolisis_fecha
_fila('tratamiento_botox', ...) / botox_fecha
_fila('laser_actual', _g('laserActivo'))
_fila('laser_actual_detalle', _g('laserActualDet'))
_fila('expectativas', _g('expectativas'))
```
Dejar `tratamiento_otro` (ya arreglado), `complicaciones_esteticas`/`complicaciones_esteticas_desc`, `prioridad_principal`, `satisfaccion`, `entiende_sesiones`.

- [ ] **Step 9: Verificar `_datos_paciente()` no referencia `expectativas`**

Línea 3220 del f-string:
```python
Expectativas: {d['expectativas']} | Satisfaccion: {d['satisfaccion']}/10
```
cambiar a:
```python
Satisfaccion: {d['satisfaccion']}/10
```

- [ ] **Step 10: Verificar `historialEstetico` en `_datos_paciente()` sigue funcionando con lista reducida**

Línea 3221: `Historial estetico: {', '.join(d['historialEstetico']) or 'Ninguno'}` — sigue funcionando igual, solo que ahora la lista casi siempre estará vacía salvo "Otro" — comportamiento esperado, no requiere cambio.

- [ ] **Step 11: Commit**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: oculta 9 tratamientos estéticos y expectativas, conecta entiende_sesiones, corrige tratamiento_otro hardcodeado"
```

---

### Task 9: Estilo de Vida y Antecedentes — ocultar Exposición solar/¿Usa protector diario?/Productos cosméticos/Infecciones cutáneas

**Files:**
- Modify: `formulario-produccion.html`
- Modify: `app.py`

Se ocultan: Exposición solar, ¿Usa protector solar diariamente?, Productos cosméticos de uso frecuente, ¿Has tenido infecciones cutáneas en zonas a tratar?. Quedan "Mantener" el resto (rutina diaria, rutina mañana/noche, rutina actual incluye, nivel actividad física, historia familiar, alergias medicamentos/tópicos, marcapasos/dispositivos, familiar directo enfermedades, cuáles).

**Bug a arreglar (spec punto 3):** `infeccionesDet`/`dispositivosDet` se leen en docx (líneas 2519, 2521) pero nunca se generan en `_mapear_formulario` — siempre vacíos. Como "¿Has tenido infecciones cutáneas...?" se oculta (Quitar), ya no aplica arreglar `infeccionesDet`. Pero `dispositivosDet` sigue siendo relevante porque "Marcapasos/implantes/dispositivos médicos" queda "Mantener" — sin embargo, revisando la tabla del spec, ese campo (`dispositivosMedicos`) es un yn-row simple, no tiene campo de detalle libre en el HTML actual. Verificar si existe un `#f-dispositivos-det` o similar antes de intentar conectarlo — si no existe, el bug es solo que se lee una clave (`dispositivosDet`) que nunca existió por diseño (el campo es solo Sí/No, no tiene detalle), y la línea del docx simplemente puede quedar vacía sin ser un bug real. Confirmar antes de "arreglar" algo que no está roto.

- [ ] **Step 1: Investigar si existe detalle libre para infecciones/dispositivos**

```bash
grep -n "infecciones\|dispositivos" formulario-produccion.html
```
Si NO hay ningún `<textarea>` o `<input>` de detalle asociado a estos yn-rows, entonces `infeccionesDet`/`dispositivosDet` en el docx son artefactos de un campo que nunca tuvo detalle — no hay nada que conectar, simplemente eliminar esas 2 filas del docx (`_fila('infecciones_cutaneas_detalle', ...)`, `_fila('dispositivos_medicos_detalle', ...)`) ya que `infecciones_cutaneas` se oculta de todos modos (Quitar) y `dispositivos_medicos_detalle` nunca tuvo fuente real.

- [ ] **Step 2: Ocultar "Exposición solar" en HTML**

Localizar el radio `name="sol"` (grupo "Exposición solar") y ocultar su `<div class="field">`.

- [ ] **Step 3: Ocultar "¿Usa protector solar diariamente?" y su bloque de detalle**

El toggle `toggleSolar` controla mostrar/ocultar `#solar-det-wrap` (marca, FPS, hora, reaplica). Como "¿Usa protector solar diariamente?" se oculta, decidir: ¿se ocultan también Marca protector/FPS/Hora/Reaplica (que no aparecen en la lista de 150 campos explícitamente, probablemente agrupados bajo el yn-row padre)? Revisar `FIXLOG.md` tabla 9 — "Factor de protección (FPS)" no aparece en la lista de 150 preguntas del email como ítem separado, así que probablemente está agrupado visualmente bajo el yn-row. Ocultar el yn-row principal Y su `#solar-det-wrap` completo para evitar un formulario con un campo de detalle huérfano visible sin su pregunta padre.

- [ ] **Step 4: Ocultar "Productos cosméticos de uso frecuente"**

`#f-productos` — ocultar su `<div class="field">`.

- [ ] **Step 5: Ocultar "¿Has tenido infecciones cutáneas en zonas a tratar?"**

Yn-row correspondiente en step-10 — ocultar.

- [ ] **Step 6: Actualizar `collectData()`**

Quitar del retorno:
```js
solar:               (document.querySelector('input[name="sol"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
spf:                 document.getElementById('f-spf').value||'',
productosFrecuentes: document.getElementById('f-productos').value||'',
usaProtectorSolar:  document.getElementById('solar-det-wrap')&&document.getElementById('solar-det-wrap').style.display!=='none' ? 'Sí' : 'No',
marcaSpf:           document.getElementById('f-spf')?document.getElementById('f-spf').value||'':'',
protectorMarca:     document.getElementById('f-protector-marca')?document.getElementById('f-protector-marca').value||'':'',
protectorHora:      document.getElementById('f-protector-hora')?document.getElementById('f-protector-hora').value||'':'',
reaplicaSolar:      (document.querySelector('input[name="reaplica_solar"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
infeccionesCutaneas: getYNValue(document.getElementById('step-10'), 'infecciones cutáneas'),
```
Dejar `dispositivosMedicos` (Mantener).

- [ ] **Step 7: Actualizar `_mapear_formulario` en `app.py`**

Quitar del dict:
```python
'solar':               s('solar'),
'spf':                 s('spf'),
'productosFrecuentes': s('productosFrecuentes'),
```
Buscar y quitar también (si existen en el dict, verificar con grep ya que no aparecieron en el extracto leído — pueden estar en otra parte del dict no mostrada): `usaProtectorSolar`, `protectorMarca`, `protectorHora`, `reaplicaSolar`, `infeccionesCutaneas`.

```bash
grep -n "'usaProtectorSolar'\|'protectorMarca'\|'protectorHora'\|'reaplicaSolar'\|'infeccionesCutaneas'" app.py
```

- [ ] **Step 8: Actualizar `_datos_paciente()` en `app.py`**

Línea 3206:
```python
Productos: {d['productosFrecuentes']} | Solar: {d['solar']} | SPF: {d['spf']}
```
Esta línea completa debe eliminarse (los 3 campos que usa se quitan). Cambiar el bloque PIEL (líneas 3204-3206):
```python
PIEL: {d['pielTipo']} | Problemas: {', '.join(d['pielProblemas'])}
Rutina manana: {d['rutinaManana']} | Noche: {d['rutinaNoche']}
Productos: {d['productosFrecuentes']} | Solar: {d['solar']} | SPF: {d['spf']}
```
a:
```python
PIEL: {d['pielTipo']} | Problemas: {', '.join(d['pielProblemas'])}
Rutina manana: {d['rutinaManana']} | Noche: {d['rutinaNoche']}
```

- [ ] **Step 9: Actualizar `generar_docx_cuestionario` en `app.py`**

Quitar filas:
```python
_fila('exposicion_solar',         _g('solar'))
_fila('protector_solar',          _g('usaProtectorSolar'))
_fila('protector_marca',          _g('protectorMarca'))
_fila('protector_fps',            _g('spf').split()[0] if _g('spf') else '')
_fila('protector_hora',           _g('protectorHora'))
_fila('protector_reaplica',       _g('reaplicaSolar'))
_fila('productos_cosmeticos_frecuentes', _g('productosFrecuentes'))
_fila('infecciones_cutaneas',          _yn_norm('infeccionesCutaneas'))
_fila('infecciones_cutaneas_detalle',  _g('infeccionesDet'))
_fila('dispositivos_medicos_detalle',  _g('dispositivosDet'))
```
Dejar `_fila('dispositivos_medicos', _yn_norm('dispositivosMedicos'))`.

- [ ] **Step 10: Commit**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: oculta y desconecta exposición solar, protector diario, productos cosméticos e infecciones cutáneas"
```

---

### Task 10: Consentimientos reales (bug), validación de campos ocultos, y verificación final end-to-end

**Files:**
- Modify: `formulario-produccion.html` (submitForm, validación de toggles obligatorios)
- Modify: `app.py` (`generar_docx_cuestionario`, sección Declaraciones)

**Bug a arreglar (spec punto 2):** consentimientos se escriben siempre "Acepto" fijo en docx (líneas 2617-2621), no reflejan estado real. Como los 5 quedan "Mantener" y ya se validan obligatorios client-side (todos deben estar `checked` para poder enviar), en la práctica siempre serán `true` al llegar aquí — pero el docx debe leer el valor real, no asumirlo, por corrección y para que futuros cambios de validación no dejen esto silenciosamente mal.

- [ ] **Step 1: Enviar el estado real de los consentimientos en `collectData()`**

En `formulario-produccion.html`, agregar al objeto retornado por `collectData()` (o justo antes del return):
```js
const consentLabels=['veracidad','riesgo','cambios','resultados','contacto'];
const consentEls=[...document.querySelectorAll('#step-11 .consent-item input[type="checkbox"]')];
```
y en el return:
```js
declaraciones: consentEls.map(c=>c.checked),
```

- [ ] **Step 2: Recibir y usar en `_mapear_formulario`**

En `app.py`, agregar al dict de retorno:
```python
'declaraciones': f.get('declaraciones', []),
```

- [ ] **Step 3: Usar el valor real en `generar_docx_cuestionario`**

Cambiar líneas 2617-2621:
```python
_fila('declara_veracidad',  'Acepto')
_fila('declara_riesgo',     'Acepto')
_fila('declara_cambios',    'Acepto')
_fila('declara_resultados', 'Acepto')
_fila('autoriza_contacto',  'Acepto')
```
a:
```python
decl = data.get('declaraciones', [])
_fila('declara_veracidad',  'Acepto' if len(decl) > 0 and decl[0] else 'No indicado')
_fila('declara_riesgo',     'Acepto' if len(decl) > 1 and decl[1] else 'No indicado')
_fila('declara_cambios',    'Acepto' if len(decl) > 2 and decl[2] else 'No indicado')
_fila('declara_resultados', 'Acepto' if len(decl) > 3 and decl[3] else 'No indicado')
_fila('autoriza_contacto',  'Acepto' if len(decl) > 4 and decl[4] else 'No indicado')
```

- [ ] **Step 4: Ajustar validación de envío para ignorar campos ocultos**

En `formulario-produccion.html`, revisar cualquier validación de yn-rows obligatorios (`*` en el label) que recorra el formulario completo antes de `submitForm()` o al avanzar de step. Buscar:
```bash
grep -n "yn-btn\|req\b\|obligatorio\|querySelectorAll.*yn-row" formulario-produccion.html
```
Para cualquier bucle que valide "todos los campos con `*` deben tener respuesta", agregar filtro de visibilidad, por ejemplo cambiar:
```js
document.querySelectorAll('.yn-row')
```
a:
```js
[...document.querySelectorAll('.yn-row')].filter(el => el.offsetParent !== null)
```
(`offsetParent === null` detecta elementos con `display:none` o ancestro oculto — patrón estándar, no requiere librería).

Aplicar el mismo filtro a cualquier validación de checkboxes/radios obligatorios que recorra por sección/step.

- [ ] **Step 5: Verificación manual end-to-end**

Levantar servidor local:
```bash
cd "/Users/master/Sitios Web/Metodo Carvajal/github-repo"
export CLAUDE_KEY=... GROQ_KEY=... RESEND_KEY=... CLOUDINARY_CLOUD_NAME=... CLOUDINARY_API_KEY=... CLOUDINARY_API_SECRET=...
python app.py
```
Abrir `http://localhost:5000/formulario` (o el puerto que use Flask por defecto) en navegador.

Checklist visual:
- [ ] Confirmar que Step 8 (Evaluación Capilar) no aparece en la navegación.
- [ ] Recorrer los 10 steps restantes, confirmar que los campos "Quitar" listados en `FIXLOG.md` no son visibles.
- [ ] Confirmar que los campos "Mantener" siguen visibles y funcionando (toggles, checkboxes, radios).
- [ ] Usar el autofill de consola (mencionado en README.md raíz, sección "Autofill del formulario") con `window._modeloSel` forzado a `'groq'` para pruebas baratas, o llenar manualmente los campos visibles.
- [ ] Ejecutar `submitForm()` — confirmar que NO se bloquea pidiendo llenar un campo oculto.
- [ ] Abrir DevTools → Network → inspeccionar el payload de `POST /enviar` — confirmar que ninguna clave de campo "Quitar" aparece en el JSON enviado.
- [ ] Esperar a que el worker genere el plan — confirmar que no hay `KeyError` en los logs del servidor (revisar consola donde corre `python app.py`).
- [ ] Abrir el `.docx` generado — confirmar: sin filas de campos "Quitar", consentimientos reflejan "Acepto" real, "tratamiento_otro" y "entiende_sesiones" ya no están hardcodeados, sección piel (Inflamación/Pigmentación/Envejecimiento) refleja los checkboxes reales marcados (no áreas faciales).
- [ ] Abrir el plan HTML generado — confirmar que carga sin errores.

- [ ] **Step 6: Commit final**

```bash
git add formulario-produccion.html app.py
git commit -m "fix: consentimientos reales en docx y excluye campos ocultos de validación obligatoria"
```

- [ ] **Step 7: Actualizar FIXLOG.md con resultado**

Agregar al final de la sección "Diseño 2026-08-08" en `FIXLOG.md` un subtítulo "### Implementación completada" con fecha real de ejecución, lista de commits generados, y cualquier desviación del plan encontrada durante la ejecución (ej. si algún campo resultó estar mapeado distinto a lo documentado).

---

## Notas para quien ejecute este plan

- Varios steps piden "verificar antes de asumir" (ej. Task 3 Step 1, Task 9 Step 1) — esto es intencional. La exploración previa que generó el mapeo campo→código fue hecha por un subagente de lectura rápida sobre un archivo de 5078 líneas; algunos detalles (nombres exactos de variables auxiliares, si un bug es real o un campo simplemente nunca tuvo detalle) requieren doble chequeo con `grep`/lectura directa antes de tocar código, no copiar el plan a ciegas.
- Si en cualquier task un campo resulta NO estar donde el plan dice, o su comportamiento real difiere de lo documentado, **detener y reportar la discrepancia** en vez de improvisar una solución — el mapeo alimenta decisiones downstream (qué se puede quitar sin romper el prompt de la IA) y un error de lectura se propaga.
- El orden de tasks sigue las secciones del email de revisión (Datos Personales → Declaración), pero son mayormente independientes entre sí — se pueden ejecutar en cualquier orden salvo Task 10 (debe ir al final, es la verificación integral).
