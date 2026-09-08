# Rediseño de eficiencia del formulario clínico — Plan de implementación

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. No hay test suite automatizado en este repo — la verificación es manual (grep, revisión visual en server local, inspección de payload de red).

**Goal:** Reducir el largo visual del formulario clínico convirtiendo 14 campos de opción única en listas desplegables, con layout de 2 columnas, secciones condicionadas por sexo, y sin redundancias — preservando exactamente los datos que llegan al backend.

**Architecture:** Solo se toca `formulario-produccion.html` (HTML + CSS + JS inline) y, mínimamente, `app.py` (un campo nuevo: `andropausia`). El backend `_mapear_formulario` recibe el JSON de `collectData()` tal cual y para los campos de opción los valores llegan como el texto del label; un `<select>` con `<option>` de texto idéntico produce el mismo string, por eso la conversión no requiere cambios de backend. Los scripts de autofill (`autofill-cuestionario.js`, `bookmarklet-cuestionario.js`) se actualizan para seguir funcionando.

**Tech Stack:** Flask monolito (`app.py`), HTML/CSS/JS vanilla sin build (`formulario-produccion.html`). Deploy Railway (auto-deploy en push a `main`). Server local: `python3 app.py`.

**Spec:** `docs/superpowers/specs/2026-09-08-formulario-eficiencia-diseno.md`

## Global Constraints

- **Texto EXACTO de opciones:** cada `<option>` debe llevar el mismo texto (tildes, guiones `–` vs `-`, espaciado) que el label del radio original. Copiar literal del HTML actual. Un carácter distinto cambia el string que llega al backend.
- **`collectData()` produce los mismos strings que hoy** — solo cambia de dónde los lee (de `<select>.value` en vez de `.radio-item.textContent`). Verificar comparando payload con la versión `.bak`.
- **No modularizar `app.py`** — sigue monolítico por convención del proyecto.
- **Sin frameworks frontend** — HTML/CSS/JS vanilla. No introducir librerías.
- **No hay test suite** — cada task termina con verificación manual.
- **Commits frecuentes** — uno por task.
- **`.bak` y tag ya existen** (`formulario-produccion.html.bak`, tag `pre-rediseno-formulario`, commit `cb52373`). No recrearlos.
- **Preservar selector de modelo oculto** — `window._modeloSel = 'claude'` en producción, no exponer UI.
- **CSS:** paleta cream/gold/dark, fuentes Cormorant Garamond + DM Sans. Variables CSS existentes: `--gold`, `--gold-light`, `--border`, `--text`, `--muted`.

---

## Estructura de archivos

| Archivo | Responsabilidad | Cambio en este plan |
|---|---|---|
| `formulario-produccion.html` | Formulario clínico completo (HTML + CSS + JS inline) | Grueso del trabajo: CSS `.field select`, 14 campos radio/scale → `<select>`, listeners de sexo/fuma/alcohol/horario, borrar subsección "Nivel de estrés" y yn-row duplicado, layout 2 columnas |
| `app.py` | Backend Flask (`_mapear_formulario`, `generar_docx_cuestionario`) | Mínimo: agregar campo `andropausia` en el dict de retorno y una fila en el docx |
| `autofill-cuestionario.js` | Script de consola para llenar el formulario (testing) | Helper `setSelect()` + reemplazar `clickRadio`/`clickScale` de los 14 campos |
| `bookmarklet-cuestionario.js` | Versión bookmarklet minificada del autofill | Regenerar con los mismos cambios |
| `FIXLOG.md` | Registro de correcciones | Añadir entrada al terminar |

## Orden de tasks y dependencias

1. **Task 1** — CSS base del `<select>` (sin dependencias)
2. **Task 2** — Convertir los 4 campos del Paso 1 (Sexo, Horario, Nº hijos, Cómo nos conociste)
3. **Task 3** — Condicionar sección hormonal por sexo + campo `andropausia` (depende de Task 2: necesita el `<select>` de Sexo)
4. **Task 4** — Convertir campos del Paso 2 (fuma_frec, alcohol_frec, horas_sueno, calidad_sueno, nivel_estres) + fusionar toggle+frecuencia + sacar Nivel de estrés de subsección
5. **Task 5** — Convertir campos del Paso 4 (dulces_frec, comidas)
6. **Task 6** — Convertir tipo_piel (Paso 6) y act_fisica (Paso 10)
7. **Task 7** — Convertir la escala de satisfacción (Paso 9)
8. **Task 8** — Eliminar yn-row de antecedentes familiares duplicado (Paso 10)
9. **Task 9** — Layout de 2 columnas (depende de Tasks 2-7: los `<select>` ya deben existir)
10. **Task 10** — `app.py`: campo `andropausia` en `_mapear_formulario` y docx
11. **Task 11** — Actualizar scripts de autofill
12. **Task 12** — Verificación integral end-to-end en server local + FIXLOG

Tasks 2-8 son mayormente independientes entre sí (cada una toca un bloque distinto del HTML) salvo la dependencia Task 3→Task 2. Task 9 va después de todas las conversiones. Task 12 va al final.

---

### Task 1: CSS base para el componente `<select>`

**Files:**
- Modify: `formulario-produccion.html` (bloque `<style>`, cerca de la regla `.radio-group` línea ~68 y `.scale-group` línea ~95)

**Interfaces:**
- Produces: clase CSS aplicable como `<div class="field"><label class="field-label">…</label><select id="f-X">…</select></div>`. El `<select>` hereda el ancho del `.field` (flex column). Un `<option value="" disabled selected>` funciona como placeholder gris vía `:invalid`.

- [ ] **Step 1: Localizar el bloque de estilos de inputs**

Run: `grep -n "^input,select,textarea\|input:focus\|\.radio-group{" formulario-produccion.html`

Leer 5 líneas de contexto para ver el patrón de estilo de los `<input>` existentes (buscar `border-bottom`, `--border`, `--gold` en focus).

- [ ] **Step 2: Agregar la regla `.field select`**

Después de la regla `.radio-item.selected .radio-dot::after{…}` (línea ~75), insertar:

```css
.field select{
  appearance:none;-webkit-appearance:none;-moz-appearance:none;
  background-color:transparent;
  border:0;border-bottom:1px solid var(--border);
  padding:9px 26px 9px 0;margin-top:4px;
  font-family:'DM Sans',sans-serif;font-size:14px;font-weight:300;
  color:var(--text);cursor:pointer;width:100%;border-radius:0;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='8' viewBox='0 0 12 8' fill='none'><path d='M1 1.5L6 6.5L11 1.5' stroke='%23b8935a' stroke-width='1.3' stroke-linecap='round'/></svg>");
  background-repeat:no-repeat;background-position:right 2px center;
}
.field select:focus{outline:none;border-bottom-color:var(--gold)}
.field select:required:invalid{color:var(--muted)}
.field select option{color:var(--text)}
.field select option[value=""][disabled]{display:none}
```

(El color `%23b8935a` en el SVG es `--gold` en hex; si `--gold` tiene otro valor en `:root`, ajustar. Verificar con `grep -n "\-\-gold:" formulario-produccion.html`.)

- [ ] **Step 3: Verificar que `--gold` coincide con el SVG**

Run: `grep -n "\-\-gold:\|\-\-gold-light:\|\-\-border:\|\-\-muted:\|\-\-text:" formulario-produccion.html`

Si `--gold` NO es `#b8935a`, reemplazar `%23b8935a` en el `background-image` por el hex real (URL-encoded: `#` → `%23`).

- [ ] **Step 4: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: estilo CSS para campos <select> del formulario"
```

---

### Task 2: Paso 1 — convertir Sexo, Horario laboral, Número de hijos, ¿Cómo nos conociste? a `<select>`

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML campos: líneas ~179-184 (Sexo), ~195-206 (Horario laboral), ~214-222 (Número de hijos), ~254-262 (¿Cómo nos conociste?)
  - JS listener horario "Otro": líneas ~1164-1170
  - `collectData()`: líneas ~1335 (sexo), ~1339 (horarioLaboral usa var `horarioLaboral` de línea ~1233-1239), ~1340 (numHijos), ~1341 (comoConociste), ~1406 (numHijosVal)

**Interfaces:**
- Consumes: `.field select` CSS de Task 1.
- Produces: `<select id="f-sexo">` con opciones `Femenino` / `Masculino` (Task 3 le añade un listener `change`). `<select id="f-horario">`, `<select id="f-num-hijos">`, `<select id="f-como-conociste">`. `collectData()` lee `.value` de cada uno; strings de salida idénticos a hoy: `sexo` = "Femenino"|"Masculino"|"" ; `horarioLaboral` = "Mañana"|"Tarde"|"Noche"|"Variable"|<texto libre si "Otro">|"" ; `numHijos`/`numHijosVal` = "0"|"1"|"2"|"3"|"4+"|"" ; `comoConociste` = "Internet / Google"|"Redes sociales"|"Recomendación de amigo/a"|"Paciente anterior"|"Otro"|"".

- [ ] **Step 1: Reemplazar el HTML de Sexo**

Localizar (línea ~179):
```html
    <div class="field"><label class="field-label">Sexo <span class="req">*</span></label>
      <div class="radio-group">
        <label class="radio-item"><input type="radio" name="sexo"><div class="radio-dot"></div>Femenino</label>
        <label class="radio-item"><input type="radio" name="sexo"><div class="radio-dot"></div>Masculino</label>
      </div>
    </div>
```
Reemplazar por:
```html
    <div class="field"><label class="field-label">Sexo <span class="req">*</span></label>
      <select id="f-sexo" required>
        <option value="" disabled selected>Selecciona…</option>
        <option value="Femenino">Femenino</option>
        <option value="Masculino">Masculino</option>
      </select>
    </div>
```

- [ ] **Step 2: Reemplazar el HTML de Horario laboral**

Localizar (línea ~195):
```html
    <div class="field full"><label class="field-label">Horario laboral <span class="req">*</span></label>
      <div class="radio-group" id="horario-options">
        <label class="radio-item"><input type="radio" name="horario_laboral" value="Mañana"><div class="radio-dot"></div>Mañana</label>
        <label class="radio-item"><input type="radio" name="horario_laboral" value="Tarde"><div class="radio-dot"></div>Tarde</label>
        <label class="radio-item"><input type="radio" name="horario_laboral" value="Noche"><div class="radio-dot"></div>Noche</label>
        <label class="radio-item"><input type="radio" name="horario_laboral" value="Variable"><div class="radio-dot"></div>Variable</label>
        <label class="radio-item" id="horario-otro-label"><input type="radio" name="horario_laboral" value="Otro"><div class="radio-dot"></div>Otro</label>
      </div>
      <div class="horario-otro" id="horario-otro-input">
        <input id="f-horario-otro" type="text" placeholder="Describe tu horario habitual..." maxlength="150">
      </div>
    </div>
```
Reemplazar por:
```html
    <div class="field"><label class="field-label">Horario laboral <span class="req">*</span></label>
      <select id="f-horario" required>
        <option value="" disabled selected>Selecciona…</option>
        <option value="Mañana">Mañana</option>
        <option value="Tarde">Tarde</option>
        <option value="Noche">Noche</option>
        <option value="Variable">Variable</option>
        <option value="Otro">Otro</option>
      </select>
      <div class="horario-otro" id="horario-otro-input" style="display:none;margin-top:8px">
        <input id="f-horario-otro" type="text" placeholder="Describe tu horario habitual..." maxlength="150">
      </div>
    </div>
```
(Nota: se quitó `class="full"` — Task 9 maneja el layout. `id="horario-otro-input"` conserva el nombre para el listener.)

- [ ] **Step 3: Reemplazar el HTML de Número de hijos**

Localizar (línea ~214):
```html
    <div class="field full"><label class="field-label">Número de hijos <span class="req">*</span></label>
      <div class="radio-group">
        <label class="radio-item"><input type="radio" name="num_hijos"><div class="radio-dot"></div>0</label>
        <label class="radio-item"><input type="radio" name="num_hijos"><div class="radio-dot"></div>1</label>
        <label class="radio-item"><input type="radio" name="num_hijos"><div class="radio-dot"></div>2</label>
        <label class="radio-item"><input type="radio" name="num_hijos"><div class="radio-dot"></div>3</label>
        <label class="radio-item"><input type="radio" name="num_hijos"><div class="radio-dot"></div>4+</label>
      </div>
    </div>
```
Reemplazar por:
```html
    <div class="field"><label class="field-label">Número de hijos <span class="req">*</span></label>
      <select id="f-num-hijos" required>
        <option value="" disabled selected>Selecciona…</option>
        <option value="0">0</option>
        <option value="1">1</option>
        <option value="2">2</option>
        <option value="3">3</option>
        <option value="4+">4+</option>
      </select>
    </div>
```

- [ ] **Step 4: Reemplazar el HTML de ¿Cómo nos conociste?**

Localizar (línea ~254):
```html
    <div class="form-grid" style="margin-top:8px">
    <div class="field full"><label class="field-label">¿Cómo nos conociste?</label>
      <div class="radio-group">
        <label class="radio-item"><input type="radio" name="como_conociste"><div class="radio-dot"></div>Internet / Google</label>
        <label class="radio-item"><input type="radio" name="como_conociste"><div class="radio-dot"></div>Redes sociales</label>
        <label class="radio-item"><input type="radio" name="como_conociste"><div class="radio-dot"></div>Recomendación de amigo/a</label>
        <label class="radio-item"><input type="radio" name="como_conociste"><div class="radio-dot"></div>Paciente anterior</label>
        <label class="radio-item"><input type="radio" name="como_conociste"><div class="radio-dot"></div>Otro</label>
      </div>
    </div>
  </div>
```
Reemplazar por:
```html
    <div class="form-grid" style="margin-top:8px">
    <div class="field"><label class="field-label">¿Cómo nos conociste?</label>
      <select id="f-como-conociste">
        <option value="" disabled selected>Selecciona…</option>
        <option value="Internet / Google">Internet / Google</option>
        <option value="Redes sociales">Redes sociales</option>
        <option value="Recomendación de amigo/a">Recomendación de amigo/a</option>
        <option value="Paciente anterior">Paciente anterior</option>
        <option value="Otro">Otro</option>
      </select>
    </div>
  </div>
```

- [ ] **Step 5: Reemplazar el listener del "Otro" de horario**

Localizar (línea ~1164):
```js
// Horario "Otro" toggle
document.querySelectorAll('input[name="horario_laboral"]').forEach(radio=>{
  radio.addEventListener('change',function(){
    const otroDiv=document.getElementById('horario-otro-input');
    otroDiv.style.display=this.value==='Otro'?'block':'none';
    otroDiv.classList.toggle('visible',this.value==='Otro');
  });
});
```
Reemplazar por:
```js
// Horario "Otro" toggle
document.getElementById('f-horario').addEventListener('change',function(){
  const otroDiv=document.getElementById('horario-otro-input');
  const isOtro=this.value==='Otro';
  otroDiv.style.display=isOtro?'block':'none';
  if(!isOtro)document.getElementById('f-horario-otro').value='';
});
```

- [ ] **Step 6: Actualizar `collectData()` — variable `horarioLaboral`**

Localizar (línea ~1232):
```js
  // Horario laboral: radio o campo libre
  const horarioRadio=document.querySelector('input[name="horario_laboral"]:checked');
  let horarioLaboral='';
  if(horarioRadio){
    horarioLaboral=horarioRadio.value==='Otro'
      ?(document.getElementById('f-horario-otro').value||'Otro')
      :horarioRadio.value;
  }
```
Reemplazar por:
```js
  // Horario laboral: select o campo libre
  const horarioSel=document.getElementById('f-horario').value||'';
  let horarioLaboral='';
  if(horarioSel){
    horarioLaboral=horarioSel==='Otro'
      ?(document.getElementById('f-horario-otro').value||'Otro')
      :horarioSel;
  }
```

- [ ] **Step 7: Actualizar `collectData()` — sexo, numHijos, comoConociste, numHijosVal**

Localizar (línea ~1335):
```js
    sexo:           (document.querySelector('input[name="sexo"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
Reemplazar por:
```js
    sexo:           document.getElementById('f-sexo').value||'',
```

Localizar (línea ~1340):
```js
    numHijos:       (document.querySelector('input[name="num_hijos"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
    comoConociste:  (document.querySelector('input[name="como_conociste"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
Reemplazar por:
```js
    numHijos:       document.getElementById('f-num-hijos').value||'',
    comoConociste:  document.getElementById('f-como-conociste').value||'',
```

Localizar (línea ~1406):
```js
    numHijosVal:        (document.querySelector('input[name="num_hijos"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
Reemplazar por:
```js
    numHijosVal:        document.getElementById('f-num-hijos').value||'',
```

- [ ] **Step 8: Verificar que no quedan referencias a los radios eliminados**

Run: `grep -n 'name="sexo"\|name="horario_laboral"\|name="num_hijos"\|name="como_conociste"\|horario-options\|horario-otro-label' formulario-produccion.html`

Esperado: 0 resultados (o solo dentro de comentarios). Si aparece alguno en `initCheckboxes()` (línea ~1187, el bloque `.radio-item`), NO tocar ese bloque — sigue sirviendo a otros radios (`antecedentes_fam`, escalas ya no, etc.). El `querySelectorAll('.radio-item')` genérico no rompe nada aunque haya menos radios.

- [ ] **Step 9: Verificar sintaxis JS**

Run: `node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>$/,''));}catch(e){ok=false;console.log('script',i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"`

Esperado: `JS OK`

- [ ] **Step 10: Verificación visual en server local**

Levantar server (ver Task 12 Step 1 para env vars):
```bash
python3 app.py
```
Abrir `http://localhost:5000/formulario`. En el Paso 1:
- Sexo, Horario laboral, Número de hijos, ¿Cómo nos conociste? se ven como listas desplegables.
- Cada lista abre con las opciones correctas.
- Seleccionar "Otro" en Horario laboral → aparece el campo de texto libre debajo.
- Cambiar a otra opción → el campo de texto libre desaparece.

- [ ] **Step 11: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: Paso 1 — Sexo, Horario, Nº hijos y Cómo nos conociste como <select>"
```

---

### Task 3: Condicionar sección "Condiciones hormonales" por sexo + campo `andropausia`

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML subsección: líneas ~292-301
  - `collectData()`: añadir `andropausia` cerca de línea ~1414 (junto a `perimenopausia`)
  - JS: nuevo listener `change` en `#f-sexo`

**Interfaces:**
- Consumes: `<select id="f-sexo">` de Task 2.
- Produces: `collectData().andropausia` = "Sí"|"No"|"No respondido" (mismo formato que las otras condiciones hormonales vía `getYNValue`). Task 10 lo consume en `_mapear_formulario`.

- [ ] **Step 1: Envolver la subsección y ajustar títulos/textos**

Localizar (línea ~292):
```html
  <div class="subsection" style="margin-top:24px">
    <div class="subsection-title">Condiciones hormonales (solo mujeres)</div>
    <div class="yn-row"><span class="yn-label">Actualmente embarazada</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">Periodo de lactancia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">Síndrome de ovario poliquístico (SOP)</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">Uso de anticonceptivos hormonales</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">Menopausia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">Perimenopausia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" style="display:none"><span class="yn-label">Andropausia (solo hombres)</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
  </div>
```
Reemplazar por:
```html
  <div class="subsection" id="cond-hormonales" style="margin-top:24px;display:none">
    <div class="subsection-title">Condiciones hormonales</div>
    <div class="yn-row" data-sexo="Femenino"><span class="yn-label">Actualmente embarazada</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" data-sexo="Femenino"><span class="yn-label">Periodo de lactancia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" data-sexo="Femenino"><span class="yn-label">Síndrome de ovario poliquístico (SOP)</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" data-sexo="Femenino"><span class="yn-label">Uso de anticonceptivos hormonales</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" data-sexo="Femenino"><span class="yn-label">Menopausia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" data-sexo="Femenino"><span class="yn-label">Perimenopausia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" data-sexo="Masculino" style="display:none"><span class="yn-label">Andropausia</span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
  </div>
```

- [ ] **Step 2: Agregar el listener de sexo**

En el bloque JS, después del listener de horario de Task 2 Step 5 (o cerca, dentro del `<script>` principal), agregar:

```js
// Condiciones hormonales según sexo
document.getElementById('f-sexo').addEventListener('change',function(){
  const sexo=this.value;
  const cont=document.getElementById('cond-hormonales');
  cont.style.display=sexo?'block':'none';
  cont.querySelectorAll('.yn-row').forEach(row=>{
    row.style.display=(row.dataset.sexo===sexo)?'flex':'none';
  });
});
```

(Nota: `.yn-row` usa `display:flex` en su CSS — verificar con `grep -n "\.yn-row{" formulario-produccion.html`. Si usa otro display, ajustar el `'flex'` de arriba.)

- [ ] **Step 3: Agregar `andropausia` a `collectData()`**

Localizar (línea ~1414):
```js
    perimenopausia:     getYNValue(s3,'perimenopausia'),
```
Añadir justo debajo:
```js
    andropausia:        getYNValue(s3,'andropausia'),
```

- [ ] **Step 4: Verificar el display de `.yn-row`**

Run: `grep -n "\.yn-row{" formulario-produccion.html`

Confirmar el valor de `display`. Si es `flex`, el Step 2 está bien. Si es `block` o `grid`, cambiar `'flex'` por ese valor en el listener.

- [ ] **Step 5: Verificar sintaxis JS**

Run: `node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"`

Esperado: `JS OK`

- [ ] **Step 6: Verificación visual en server local**

`python3 app.py` → `http://localhost:5000/formulario`. Ir al Paso 2 (Condición Actual):
- Antes de tocar Sexo (Paso 1): la subsección "Condiciones hormonales" NO se ve.
- Volver al Paso 1, elegir Sexo = Femenino, avanzar al Paso 2: se ven las 6 preguntas (embarazada, lactancia, SOP, anticonceptivos, menopausia, perimenopausia), NO Andropausia.
- Volver al Paso 1, cambiar Sexo = Masculino, avanzar: se ve SOLO Andropausia, NO las 6.
- El título dice "Condiciones hormonales" (sin "(solo mujeres)").

- [ ] **Step 7: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: sección de condiciones hormonales condicionada por sexo + campo andropausia"
```

---

### Task 4: Paso 2 — convertir fuma_frec, alcohol_frec, horas_sueno, calidad_sueno, nivel_estres; fusionar toggle+frecuencia; mover Nivel de estrés

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML: línea ~306 (fuma_frec), ~308 (alcohol_frec), ~330 (horas_sueno), ~331 (calidad_sueno), ~340-357 (subsección Nivel de estrés — se elimina como bloque, el campo se mueve)
  - `collectData()`: `fuma` línea ~1372, `alcohol` línea ~1373, `sueno` líneas ~1308-1311, `nivelEstres` línea ~1405
  - JS: nueva función `toggleFrec`

**Interfaces:**
- Consumes: `.field select` CSS de Task 1.
- Produces: `<select id="f-fuma-frec">`, `<select id="f-alcohol-frec">`, `<select id="f-horas-sueno">`, `<select id="f-calidad-sueno">`, `<select id="f-estres">`. Strings de salida idénticos: `fuma` = "No" | "Sí" | "Sí - Diario" | "Sí - Ocasional" ; `alcohol` análogo con Diario/Semanal/Ocasional ; `sueno` = "<horas> <calidad>" (mismo formato concatenado que hoy) ; `nivelEstres` = "1".."10"|"".

- [ ] **Step 1: Confirmar el CSS de `.yn-row` y `toggleYN`/`toggleSolar`**

Run: `grep -n "function toggleYN\|function toggleSolar\|\.yn-row{\|\.yn-btn\b" formulario-produccion.html`

Leer `toggleSolar` (línea ~1484) como patrón de referencia — muestra/oculta un wrap al pulsar Sí/No.

- [ ] **Step 2: Agregar la función `toggleFrec`**

Después de `toggleSolar` (línea ~1490) o junto a las otras funciones toggle, agregar:

```js
// Toggle select de frecuencia (fuma / alcohol)
function toggleFrec(btn, val, selectId) {
  const row = btn.closest('.yn-btns');
  row.querySelectorAll('.yn-btn').forEach(b => b.classList.remove('active-yes','active-no'));
  btn.classList.add(val === 'yes' ? 'active-yes' : 'active-no');
  const wrap = document.getElementById(selectId + '-wrap');
  if (wrap) {
    wrap.style.display = val === 'yes' ? 'block' : 'none';
    if (val !== 'yes') document.getElementById(selectId).value = '';
  }
}
```

- [ ] **Step 3: Reemplazar el yn-row de "Fuma" + su frecuencia**

Localizar (línea ~305):
```html
    <div class="yn-row"><span class="yn-label">Fuma <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="form-grid" style="margin:10px 0 16px"><div class="field full"><label class="field-label">Si fuma, frecuencia</label><div class="radio-group"><label class="radio-item"><input type="radio" name="fuma_frec"><div class="radio-dot"></div>Diario</label><label class="radio-item"><input type="radio" name="fuma_frec"><div class="radio-dot"></div>Ocasional</label></div></div></div>
```
Reemplazar por:
```html
    <div class="yn-row"><span class="yn-label">Fuma <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleFrec(this,'yes','f-fuma-frec')">Sí</button><button class="yn-btn" onclick="toggleFrec(this,'no','f-fuma-frec')">No</button></div></div>
    <div id="f-fuma-frec-wrap" style="display:none;margin:10px 0 16px">
      <div class="field"><label class="field-label">Frecuencia</label>
        <select id="f-fuma-frec">
          <option value="" disabled selected>Selecciona…</option>
          <option value="Diario">Diario</option>
          <option value="Ocasional">Ocasional</option>
        </select>
      </div>
    </div>
```

- [ ] **Step 4: Reemplazar el yn-row de "Consume alcohol" + su frecuencia**

Localizar (línea ~307):
```html
    <div class="yn-row"><span class="yn-label">Consume alcohol <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="form-grid" style="margin:10px 0 16px"><div class="field full"><label class="field-label">Si consume alcohol, frecuencia</label><div class="radio-group"><label class="radio-item"><input type="radio" name="alcohol_frec"><div class="radio-dot"></div>Diario</label><label class="radio-item"><input type="radio" name="alcohol_frec"><div class="radio-dot"></div>Semanal</label><label class="radio-item"><input type="radio" name="alcohol_frec"><div class="radio-dot"></div>Ocasional</label></div></div></div>
```
Reemplazar por:
```html
    <div class="yn-row"><span class="yn-label">Consume alcohol <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleFrec(this,'yes','f-alcohol-frec')">Sí</button><button class="yn-btn" onclick="toggleFrec(this,'no','f-alcohol-frec')">No</button></div></div>
    <div id="f-alcohol-frec-wrap" style="display:none;margin:10px 0 16px">
      <div class="field"><label class="field-label">Frecuencia</label>
        <select id="f-alcohol-frec">
          <option value="" disabled selected>Selecciona…</option>
          <option value="Diario">Diario</option>
          <option value="Semanal">Semanal</option>
          <option value="Ocasional">Ocasional</option>
        </select>
      </div>
    </div>
```

- [ ] **Step 5: Reemplazar horas_sueno y calidad_sueno**

Localizar (línea ~330):
```html
      <div class="field full"><label class="field-label">Promedio de horas por noche <span class="req">*</span></label><div class="radio-group"><label class="radio-item"><input type="radio" name="horas_sueno"><div class="radio-dot"></div>Menos de 5h</label><label class="radio-item"><input type="radio" name="horas_sueno"><div class="radio-dot"></div>5–7h</label><label class="radio-item"><input type="radio" name="horas_sueno"><div class="radio-dot"></div>7–9h</label><label class="radio-item"><input type="radio" name="horas_sueno"><div class="radio-dot"></div>Más de 9h</label></div></div>
      <div class="field full"><label class="field-label">Calidad del sueño <span class="req">*</span></label><div class="radio-group"><label class="radio-item"><input type="radio" name="calidad_sueno"><div class="radio-dot"></div>Profundo y reparador</label><label class="radio-item"><input type="radio" name="calidad_sueno"><div class="radio-dot"></div>Interrumpido o ligero</label><label class="radio-item"><input type="radio" name="calidad_sueno"><div class="radio-dot"></div>Dificultad para conciliar</label><label class="radio-item"><input type="radio" name="calidad_sueno"><div class="radio-dot"></div>Insomnio frecuente</label></div></div>
```
Reemplazar por:
```html
      <div class="field"><label class="field-label">Promedio de horas por noche <span class="req">*</span></label>
        <select id="f-horas-sueno" required>
          <option value="" disabled selected>Selecciona…</option>
          <option value="Menos de 5h">Menos de 5h</option>
          <option value="5–7h">5–7h</option>
          <option value="7–9h">7–9h</option>
          <option value="Más de 9h">Más de 9h</option>
        </select>
      </div>
      <div class="field"><label class="field-label">Calidad del sueño <span class="req">*</span></label>
        <select id="f-calidad-sueno" required>
          <option value="" disabled selected>Selecciona…</option>
          <option value="Profundo y reparador">Profundo y reparador</option>
          <option value="Interrumpido o ligero">Interrumpido o ligero</option>
          <option value="Dificultad para conciliar">Dificultad para conciliar</option>
          <option value="Insomnio frecuente">Insomnio frecuente</option>
        </select>
      </div>
```
**IMPORTANTE:** el texto `5–7h` y `7–9h` usa guion largo `–` (U+2013), no `-`. Copiar literal del HTML original.

- [ ] **Step 6: Eliminar la subsección "Nivel de estrés" y reinsertar el campo dentro de "Hábitos de sueño"**

Localizar la subsección completa (líneas ~340-357):
```html
  <div class="subsection">
    <div class="subsection-title">Nivel de estrés</div>
    <div class="field">
      <label class="field-label">¿Cómo calificarías tu nivel de estrés diario? <span class="req">*</span> <span style="font-size:10px;color:var(--muted)">(1 = Muy bajo · 10 = Muy alto)</span></label>
      <div class="scale-group" id="scale-estres">
        <button class="scale-btn" onclick="toggleScale(this,1)">1</button>
        ... (botones 2-10) ...
      </div>
    </div>
  </div>
```
Eliminarla por completo.

Luego, dentro de la subsección "Hábitos de sueño", después del bloque `<div class="form-grid">` que contiene horas/calidad/hora-acuesta/hora-levanta y antes del `<div class="yn-row" ...>¿Siente cansancio...` (línea ~335), insertar:
```html
    <div class="form-grid" style="margin-top:12px">
      <div class="field"><label class="field-label">Nivel de estrés diario <span class="req">*</span> <span style="font-size:10px;color:var(--muted)">(1 = Muy bajo · 10 = Muy alto)</span></label>
        <select id="f-estres" required>
          <option value="" disabled selected>Selecciona…</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5</option>
          <option value="6">6</option>
          <option value="7">7</option>
          <option value="8">8</option>
          <option value="9">9</option>
          <option value="10">10</option>
        </select>
      </div>
    </div>
```

- [ ] **Step 7: Actualizar `collectData()` — `sueno`**

Localizar (línea ~1308):
```js
  // Sueño
  const horasSueno=document.querySelector('input[name="horas_sueno"]:checked');
  const calidadSueno=document.querySelector('input[name="calidad_sueno"]:checked');
  const sueno=(horasSueno?horasSueno.closest('.radio-item').textContent.trim():'')
    +' '+(calidadSueno?calidadSueno.closest('.radio-item').textContent.trim():'');
```
Reemplazar por:
```js
  // Sueño
  const horasSueno=document.getElementById('f-horas-sueno').value||'';
  const calidadSueno=document.getElementById('f-calidad-sueno').value||'';
  const sueno=(horasSueno+' '+calidadSueno).trim();
```

- [ ] **Step 8: Actualizar `collectData()` — `fuma` y `alcohol`**

Localizar (línea ~1372):
```js
    fuma:    (()=>{ const f=getYNValue(s3,'fuma'); const frec=document.querySelector('input[name="fuma_frec"]:checked'); return f==='Sí'?('Sí'+(frec?' - '+frec.closest('.radio-item').textContent.trim():'')):'No'; })(),
    alcohol: (()=>{ const a=getYNValue(document.getElementById('step-4'),'alcohol'); const afrec=document.querySelector('input[name="alcohol_frec"]:checked'); return a==='Sí'?('Sí'+(afrec?' - '+afrec.closest('.radio-item').textContent.trim():'')):'No'; })(),
```
Reemplazar por:
```js
    fuma:    (()=>{ const f=getYNValue(s3,'fuma'); const frec=document.getElementById('f-fuma-frec').value||''; return f==='Sí'?('Sí'+(frec?' - '+frec:'')):'No'; })(),
    alcohol: (()=>{ const a=getYNValue(s3,'alcohol'); const afrec=document.getElementById('f-alcohol-frec').value||''; return a==='Sí'?('Sí'+(afrec?' - '+afrec:'')):'No'; })(),
```
**Nota:** el `alcohol` original leía `getYNValue(document.getElementById('step-4'),'alcohol')` — `step-4` es Preferencias Alimentarias, ahí NO está la pregunta "Consume alcohol" (está en `step-2` = "Condición Actual", que es la var `s3`). Esto parece un bug preexistente: la pregunta "Consume alcohol" del step-2 no se estaba leyendo. Al cambiar a `s3` se corrige. **Verificar en Step 11** que `alcohol` ahora refleje lo elegido. Si el cliente prefiere no cambiar comportamiento, dejar `document.getElementById('step-2')` explícito. Confirmar cuál es el id real del panel "Condición Actual" con `grep -n 'step-panel" id=' formulario-produccion.html` (por el mapeo del spec, "Condición Actual" = `id="step-2"`, y `s3` se define como `document.getElementById('step-2')`).

- [ ] **Step 9: Actualizar `collectData()` — `nivelEstres`**

Localizar (línea ~1405):
```js
    nivelEstres:        getScaleValue('scale-estres'),
```
Reemplazar por:
```js
    nivelEstres:        document.getElementById('f-estres').value||'',
```

- [ ] **Step 10: Verificar sintaxis JS y referencias muertas**

Run: `grep -n 'name="fuma_frec"\|name="alcohol_frec"\|name="horas_sueno"\|name="calidad_sueno"\|scale-estres\|"Nivel de estrés"' formulario-produccion.html`

Esperado: 0 resultados (o solo en el autofill, que se arregla en Task 11).

Run: `node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"`

Esperado: `JS OK`

- [ ] **Step 11: Verificación visual en server local**

`python3 app.py` → Paso 2:
- Fuma, Consume alcohol: al pulsar "Sí" aparece un `<select>` de frecuencia; al pulsar "No" desaparece.
- Promedio de horas por noche, Calidad del sueño: listas desplegables, 2 columnas.
- Nivel de estrés: lista desplegable 1–10, dentro de la subsección "Hábitos de sueño" (ya NO hay una subsección aparte llamada "Nivel de estrés").
- Llenar todo el formulario (o usar autofill tras Task 11), enviar, e inspeccionar el payload de `POST /enviar` en DevTools → Network: `fuma`, `alcohol`, `sueno`, `nivelEstres` traen los strings esperados.

- [ ] **Step 12: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: Paso 2 — selects de frecuencia/sueño/estrés, fusión toggle+frecuencia, estrés sin subsección propia"
```

---

### Task 5: Paso 4 — convertir dulces_frec y comidas a `<select>`

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML: línea ~482 (dulces_frec), ~489 (comidas)
  - `collectData()`: no hay lectura directa de `dulces_frec` ni `comidas` en el objeto retornado — **verificar** (grep). Si `comidas` no se recolecta hoy, sigue sin recolectarse (campo huérfano, no romper). Si `dulces_frec` tampoco, igual.

**Interfaces:**
- Consumes: `.field select` CSS de Task 1.
- Produces: `<select id="f-dulces-frec">`, `<select id="f-comidas">`. Si hoy no se recolectan, no se añade recolección (fuera de alcance del spec — solo conversión visual).

- [ ] **Step 1: Verificar si dulces_frec / comidas se recolectan**

Run: `grep -n 'dulces_frec\|name="comidas"\|comidas:' formulario-produccion.html`

Anotar si aparecen dentro de `collectData()` (líneas ~1319-1434). Del análisis previo NO aparecen en el objeto retornado — son huérfanos hoy. Confirmar.

- [ ] **Step 2: Reemplazar dulces_frec**

Localizar (línea ~482):
```html
      <div class="field full"><label class="field-label">Frecuencia de consumo <span class="req">*</span></label><div class="radio-group"><label class="radio-item"><input type="radio" name="dulces_frec"><div class="radio-dot"></div>Diario</label><label class="radio-item"><input type="radio" name="dulces_frec"><div class="radio-dot"></div>2–3 veces/semana</label><label class="radio-item"><input type="radio" name="dulces_frec"><div class="radio-dot"></div>1 vez/semana</label><label class="radio-item"><input type="radio" name="dulces_frec"><div class="radio-dot"></div>Ocasionalmente</label></div></div>
```
Reemplazar por:
```html
      <div class="field"><label class="field-label">Frecuencia de consumo <span class="req">*</span></label>
        <select id="f-dulces-frec" required>
          <option value="" disabled selected>Selecciona…</option>
          <option value="Diario">Diario</option>
          <option value="2–3 veces/semana">2–3 veces/semana</option>
          <option value="1 vez/semana">1 vez/semana</option>
          <option value="Ocasionalmente">Ocasionalmente</option>
        </select>
      </div>
```
(Guion largo `–` en "2–3 veces/semana" — copiar literal.)

- [ ] **Step 3: Reemplazar comidas**

Localizar (línea ~489):
```html
      <div class="field"><label class="field-label">¿Cuántas comidas al día? <span class="req">*</span></label><div class="radio-group"><label class="radio-item"><input type="radio" name="comidas"><div class="radio-dot"></div>1</label><label class="radio-item"><input type="radio" name="comidas"><div class="radio-dot"></div>2</label><label class="radio-item"><input type="radio" name="comidas"><div class="radio-dot"></div>3</label><label class="radio-item"><input type="radio" name="comidas"><div class="radio-dot"></div>4+</label></div></div>
```
Reemplazar por:
```html
      <div class="field"><label class="field-label">¿Cuántas comidas al día? <span class="req">*</span></label>
        <select id="f-comidas" required>
          <option value="" disabled selected>Selecciona…</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4+">4+</option>
        </select>
      </div>
```

- [ ] **Step 4: Verificar sintaxis y referencias**

Run: `grep -n 'name="dulces_frec"\|name="comidas"' formulario-produccion.html`
Esperado: 0 (o solo autofill).

Run: `node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"`
Esperado: `JS OK`

- [ ] **Step 5: Verificación visual**

`python3 app.py` → Paso 4 (Preferencias Alimentarias): "Frecuencia de consumo" y "¿Cuántas comidas al día?" se ven como listas desplegables.

- [ ] **Step 6: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: Paso 4 — frecuencia de dulces y comidas al día como <select>"
```

---

### Task 6: Convertir tipo_piel (Paso 6) y act_fisica (Paso 10) a `<select>`

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML: líneas ~661-670 (tipo_piel), ~976-983 (act_fisica)
  - `collectData()`: `pielTipo` línea ~1382, `actFisica` línea ~1389

**Interfaces:**
- Consumes: `.field select` CSS de Task 1.
- Produces: `<select id="f-tipo-piel">` opciones Normal/Seca/Grasa/Mixta/Sensible/No lo sé. `<select id="f-act-fisica">` opciones Sedentario/Ligero (1–2/sem)/Moderado (3–4/sem)/Intenso (5+/sem). `collectData()` lee `.value`; strings idénticos a hoy.

- [ ] **Step 1: Reemplazar tipo_piel**

Localizar (línea ~661):
```html
    <div class="field"><label class="field-label">¿Cómo describiría su piel? <span class="req">*</span></label>
      <div class="radio-group">
        <label class="radio-item"><input type="radio" name="tipo_piel"><div class="radio-dot"></div>Normal</label>
        <label class="radio-item"><input type="radio" name="tipo_piel"><div class="radio-dot"></div>Seca</label>
        <label class="radio-item"><input type="radio" name="tipo_piel"><div class="radio-dot"></div>Grasa</label>
        <label class="radio-item"><input type="radio" name="tipo_piel"><div class="radio-dot"></div>Mixta</label>
        <label class="radio-item"><input type="radio" name="tipo_piel"><div class="radio-dot"></div>Sensible</label>
        <label class="radio-item"><input type="radio" name="tipo_piel"><div class="radio-dot"></div>No lo sé</label>
      </div>
    </div>
```
Reemplazar por:
```html
    <div class="field"><label class="field-label">¿Cómo describiría su piel? <span class="req">*</span></label>
      <select id="f-tipo-piel" required>
        <option value="" disabled selected>Selecciona…</option>
        <option value="Normal">Normal</option>
        <option value="Seca">Seca</option>
        <option value="Grasa">Grasa</option>
        <option value="Mixta">Mixta</option>
        <option value="Sensible">Sensible</option>
        <option value="No lo sé">No lo sé</option>
      </select>
    </div>
```

- [ ] **Step 2: Reemplazar act_fisica**

Localizar (línea ~976):
```html
    <div class="field"><label class="field-label">Nivel de actividad física <span class="req">*</span></label>
      <div class="radio-group">
        <label class="radio-item"><input type="radio" name="act_fisica"><div class="radio-dot"></div>Sedentario</label>
        <label class="radio-item"><input type="radio" name="act_fisica"><div class="radio-dot"></div>Ligero (1–2/sem)</label>
        <label class="radio-item"><input type="radio" name="act_fisica"><div class="radio-dot"></div>Moderado (3–4/sem)</label>
        <label class="radio-item"><input type="radio" name="act_fisica"><div class="radio-dot"></div>Intenso (5+/sem)</label>
      </div>
    </div>
```
Reemplazar por:
```html
    <div class="field"><label class="field-label">Nivel de actividad física <span class="req">*</span></label>
      <select id="f-act-fisica" required>
        <option value="" disabled selected>Selecciona…</option>
        <option value="Sedentario">Sedentario</option>
        <option value="Ligero (1–2/sem)">Ligero (1–2/sem)</option>
        <option value="Moderado (3–4/sem)">Moderado (3–4/sem)</option>
        <option value="Intenso (5+/sem)">Intenso (5+/sem)</option>
      </select>
    </div>
```
(Guion largo `–` en "1–2/sem" y "3–4/sem" — copiar literal.)

- [ ] **Step 3: Actualizar `collectData()`**

Localizar (línea ~1382):
```js
    pielTipo:            (document.querySelector('input[name="tipo_piel"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
Reemplazar por:
```js
    pielTipo:            document.getElementById('f-tipo-piel').value||'',
```

Localizar (línea ~1389):
```js
    actFisica: (document.querySelector('input[name="act_fisica"]:checked')||{closest:()=>({textContent:''})}).closest('.radio-item').textContent.trim(),
```
Reemplazar por:
```js
    actFisica: document.getElementById('f-act-fisica').value||'',
```

- [ ] **Step 4: Verificar sintaxis y referencias**

Run: `grep -n 'name="tipo_piel"\|name="act_fisica"' formulario-produccion.html`
Esperado: 0 (o solo autofill).

Run: `node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"`
Esperado: `JS OK`

- [ ] **Step 5: Verificación visual**

`python3 app.py` → Paso 6 (Historial Quirúrgico y Piel): "¿Cómo describiría su piel?" es lista. Paso 8 real (Estilo de Vida, panel `id="step-10"`): "Nivel de actividad física" es lista.

- [ ] **Step 6: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: tipo de piel y nivel de actividad física como <select>"
```

---

### Task 7: Convertir la escala de satisfacción (Paso 9) a `<select>` 1–10

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML: líneas ~909-923 (bloque `scale-group#scale-satisfaccion`)
  - `collectData()`: `satisfaccion` línea ~1395

**Interfaces:**
- Consumes: `.field select` CSS de Task 1.
- Produces: `<select id="f-satisfaccion">` opciones 1..10. `collectData().satisfaccion` = "1".."10"|"" (mismo string que `getScaleValue` hoy).

- [ ] **Step 1: Reemplazar el bloque de la escala**

Localizar (línea ~909):
```html
      <div class="field full">
        <label class="field-label">Satisfacción actual con el área a tratar <span class="req">*</span> <span style="font-size:10px;color:var(--muted)">(1 = Muy insatisfecho · 10 = Muy satisfecho)</span></label>
        <div class="scale-group" id="scale-satisfaccion">
          <button class="scale-btn" onclick="toggleScale(this,1)">1</button>
          <button class="scale-btn" onclick="toggleScale(this,2)">2</button>
          <button class="scale-btn" onclick="toggleScale(this,3)">3</button>
          <button class="scale-btn" onclick="toggleScale(this,4)">4</button>
          <button class="scale-btn" onclick="toggleScale(this,5)">5</button>
          <button class="scale-btn" onclick="toggleScale(this,6)">6</button>
          <button class="scale-btn" onclick="toggleScale(this,7)">7</button>
          <button class="scale-btn" onclick="toggleScale(this,8)">8</button>
          <button class="scale-btn" onclick="toggleScale(this,9)">9</button>
          <button class="scale-btn" onclick="toggleScale(this,10)">10</button>
        </div>
      </div>
```
Reemplazar por:
```html
      <div class="field full">
        <label class="field-label">Satisfacción actual con el área a tratar <span class="req">*</span> <span style="font-size:10px;color:var(--muted)">(1 = Muy insatisfecho · 10 = Muy satisfecho)</span></label>
        <select id="f-satisfaccion" required>
          <option value="" disabled selected>Selecciona…</option>
          <option value="1">1</option>
          <option value="2">2</option>
          <option value="3">3</option>
          <option value="4">4</option>
          <option value="5">5</option>
          <option value="6">6</option>
          <option value="7">7</option>
          <option value="8">8</option>
          <option value="9">9</option>
          <option value="10">10</option>
        </select>
      </div>
```

- [ ] **Step 2: Actualizar `collectData()`**

Localizar (línea ~1395):
```js
    satisfaccion:     getScaleValue('scale-satisfaccion'),
```
Reemplazar por:
```js
    satisfaccion:     document.getElementById('f-satisfaccion').value||'',
```

- [ ] **Step 3: Verificar si `toggleScale`/`getScaleValue` siguen usándose**

Run: `grep -n 'scale-group\|scale-btn\|toggleScale\|getScaleValue\|scale-estres\|scale-satisfaccion' formulario-produccion.html`

Tras Task 4 (estrés) y Task 7 (satisfacción), NO deberían quedar `scale-group` en el HTML. Las funciones `toggleScale` y `getScaleValue` (líneas ~1151-1161) quedan sin uso — **dejarlas** (código inerte, no estorban; quitarlas es limpieza opcional fuera de alcance). El CSS `.scale-group`/`.scale-btn` (líneas ~95-98) igual — dejarlo.

- [ ] **Step 4: Verificar sintaxis JS**

Run: `node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"`
Esperado: `JS OK`

- [ ] **Step 5: Verificación visual**

`python3 app.py` → Paso 7 real (Objetivos y Estética Previa, panel `id="step-9"`): "Satisfacción actual con el área a tratar" es una lista desplegable 1–10.

- [ ] **Step 6: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: escala de satisfacción como <select> 1–10"
```

---

### Task 8: Eliminar el yn-row de antecedentes familiares duplicado (Paso 10)

**Files:**
- Modify: `formulario-produccion.html`:
  - HTML: línea ~988 (yn-row "¿En su familia hay historia de alguna enfermedad relevante?") y el título de la subsección línea ~987

**Interfaces:**
- No produce ni consume nada nuevo. Verificado en el spec: este yn-row NO se lee en `collectData()`. Borrarlo no afecta el pipeline.

- [ ] **Step 1: Confirmar (otra vez) que el yn-row está huérfano**

Run: `grep -n "familia hay historia\|En su familia\|historia de alguna enfermedad" formulario-produccion.html`

Debe aparecer SOLO en la línea ~988 (el yn-row) y en ningún `getYNValue(...)`. Si aparece un `getYNValue(s10,'familia hay historia')` o similar dentro de `collectData()`, **DETENER** y reportar — el spec asumió huérfano.

- [ ] **Step 2: Eliminar el yn-row y renombrar la subsección**

Localizar (líneas ~986-992):
```html
  <div class="subsection">
    <div class="subsection-title">Antecedentes Familiares y Contraindicaciones</div>
    <div class="yn-row"><span class="yn-label">¿En su familia hay historia de alguna enfermedad relevante? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">¿Tienes alergias a medicamentos o productos tópicos? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" style="display:none"><span class="yn-label">¿Has tenido infecciones cutáneas en zonas a tratar? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">¿Tienes marcapasos, implantes metálicos o dispositivos médicos? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
  </div>
```
Reemplazar por (quitar el primer yn-row, renombrar título):
```html
  <div class="subsection">
    <div class="subsection-title">Contraindicaciones</div>
    <div class="yn-row"><span class="yn-label">¿Tienes alergias a medicamentos o productos tópicos? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row" style="display:none"><span class="yn-label">¿Has tenido infecciones cutáneas en zonas a tratar? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
    <div class="yn-row"><span class="yn-label">¿Tienes marcapasos, implantes metálicos o dispositivos médicos? <span style="color:var(--gold)">*</span></span><div class="yn-btns"><button class="yn-btn" onclick="toggleYN(this,'yes')">Sí</button><button class="yn-btn" onclick="toggleYN(this,'no')">No</button></div></div>
  </div>
```

- [ ] **Step 3: Verificación visual**

`python3 app.py` → Paso 8 real (Estilo de Vida, panel `id="step-10"`): solo hay UNA pregunta sobre antecedentes familiares — el radio "¿Algún familiar directo con enfermedades relevantes?" con su campo "¿Cuáles?". La subsección de contraindicaciones ya no menciona antecedentes.

- [ ] **Step 4: Commit**

```bash
git add formulario-produccion.html
git commit -m "fix: elimina pregunta de antecedentes familiares duplicada en Paso 10"
```

---

### Task 9: Layout de 2 columnas aprovechando el espacio liberado

**Files:**
- Modify: `formulario-produccion.html`:
  - Paso 1 (`id="step-1"`): agrupar campos en `.form-grid`, quitar `.full` de los `<select>` que ya no lo necesitan, emparejar
  - Paso 2 (`id="step-2"`): emparejar horas/calidad de sueño (ya hecho en Task 4 Step 5), estrés (Task 4 Step 6)
  - Paso 4 (`id="step-3"`): emparejar frecuencia dulces / comidas

**Interfaces:**
- Consumes: todos los `<select>` de Tasks 2-7.
- No cambia `collectData()` ni backend. Solo estructura de `<div class="form-grid">` y clases `.full`.

- [ ] **Step 1: Revisar el estado actual del Paso 1**

Run: `grep -n 'id="step-1"' formulario-produccion.html`

Leer desde ahí hasta el cierre del panel (`<!-- STEP 3` o el próximo `step-panel`). Mapear qué campos hay y cuáles tienen `class="field full"` vs `class="field"`.

- [ ] **Step 2: Reorganizar el Paso 1 en pares**

Objetivo de emparejamiento (2 columnas en escritorio, 1 en móvil por el `@media` existente):
- Fila: Nombre completo (`full`)
- Fila: Cédula (oculto) — no cuenta / Dirección (oculto) — no cuenta
- Fila: Sexo | Fecha de nacimiento
- Fila: Celular | Correo electrónico
- Fila: Ocupación | Horario laboral
- Fila: Número de hijos | ¿Cómo nos conociste?

Asegurar que:
- El `<div class="form-grid">` del Paso 1 envuelve estos campos.
- `Sexo`, `Horario laboral`, `Número de hijos`, `¿Cómo nos conociste?` tienen `class="field"` (NO `full`).
- El campo "Otro" de horario (`#horario-otro-input`) queda debajo del `<select>` dentro del mismo `.field` (no rompe el grid porque está dentro de la celda).
- `¿Cómo nos conociste?` estaba en un `.form-grid` separado (línea ~253) — moverlo al `.form-grid` principal del paso o dejar su propio grid pero con `.field` (media columna) y añadir un segundo campo o dejar que ocupe media fila. **Decisión:** dejarlo en el grid principal, emparejado con "Número de hijos".

Editar el HTML del Paso 1 para lograr esa estructura. Como es reordenamiento, hacerlo con cuidado leyendo el bloque completo primero.

- [ ] **Step 3: Emparejar en el Paso 4**

En `id="step-3"` (Preferencias Alimentarias), subsección "Otros hábitos alimentarios" y "Postres y dulces": poner "Frecuencia de consumo" (dulces) y "¿Cuántas comidas al día?" en el mismo `<div class="form-grid">` para que queden lado a lado. Verificar que "Postres preferidos" (texto libre) siga arriba en su fila (`full` o solo).

- [ ] **Step 4: Verificar el Paso 2**

Confirmar que Task 4 dejó horas/calidad de sueño emparejados y el estrés en un `.form-grid`. Si el estrés quedó solo en una fila de 2 columnas con una celda vacía, emparejarlo con las horas de acostarse/levantarse o dejarlo `full` si se ve mejor. Decisión visual — ver en el navegador.

- [ ] **Step 5: Verificación visual responsive**

`python3 app.py`. En escritorio (ventana ancha):
- Paso 1: Sexo|Fecha nac., Celular|Correo, Ocupación|Horario, Nº hijos|Cómo conociste — lado a lado.
- Paso 2: Horas sueño|Calidad sueño lado a lado.
- Paso 4: Frecuencia dulces|Comidas lado a lado.

Achicar la ventana a <520px (DevTools responsive, iPhone): todo colapsa a 1 columna, sin desbordes horizontales.

- [ ] **Step 6: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: layout de 2 columnas en Pasos 1, 2 y 4 tras liberar espacio con selects"
```

---

### Task 10: `app.py` — campo `andropausia` en `_mapear_formulario` y docx

**Files:**
- Modify: `app.py`:
  - `_mapear_formulario` retorno del dict (línea ~2873, junto a `perimenopausia`)
  - `generar_docx_cuestionario` (buscar dónde se imprimen embarazo/lactancia/etc.)
  - `_datos_paciente` — verificar si arma línea con condiciones hormonales

**Interfaces:**
- Consumes: `collectData().andropausia` de Task 3 ("Sí"|"No"|"No respondido").
- Produces: `d['andropausia']` disponible para el docx.

- [ ] **Step 1: Localizar dónde se procesan las condiciones hormonales en `_mapear_formulario`**

Run: `grep -n "'perimenopausia'\|'menopausia'\|'embarazo'\|'lactancia'" app.py`

- [ ] **Step 2: Agregar `andropausia` al dict de retorno**

En `app.py`, localizar (línea ~2873):
```python
        'perimenopausia':      s('perimenopausia'),
```
Añadir justo debajo:
```python
        'andropausia':         s('andropausia'),
```

- [ ] **Step 3: Localizar el docx de condiciones hormonales**

Run: `grep -n "perimenopausia\|menopausia\|embarazo\|lactancia\|_fila('emergencia\|condiciones hormonales\|Condiciones hormonales" app.py`

Encontrar el bloque en `generar_docx_cuestionario` donde se hace `_fila('embarazo', ...)` o similar.

- [ ] **Step 4: Agregar la fila `andropausia` al docx**

Junto a las otras filas de condiciones hormonales en `generar_docx_cuestionario`, agregar (adaptando al patrón exacto que uses `_fila`/`_g`):
```python
    _fila('andropausia',              _g('andropausia'))
```
Colocarla después de la fila de `perimenopausia` (o de la última condición hormonal femenina).

- [ ] **Step 5: Verificar `_datos_paciente`**

Run: `grep -n "def _datos_paciente" app.py` y leer la función completa.

Buscar si arma alguna línea con `d['embarazo']`, `d['menopausia']`, etc. Si SÍ y quieres incluir andropausia ahí, agregar `d['andropausia']` a esa línea. Si NO arma ninguna línea con condiciones hormonales individuales (solo usa `contraindications`), no tocar `_datos_paciente`.

Del análisis previo: `_datos_paciente` usa `d.get('contraindications', {})` y no las claves individuales — probablemente no requiere cambio. Confirmar.

- [ ] **Step 6: Verificar sintaxis Python**

Run: `python3 -c "import ast; ast.parse(open('app.py').read()); print('OK')"`
Esperado: `OK`

- [ ] **Step 7: Verificación en server local**

`python3 app.py` → llenar formulario con Sexo = Masculino, responder Andropausia = Sí, enviar. Esperar generación del plan. Abrir el `.docx` generado (link en el email o en Cloudinary): confirmar que aparece una fila "andropausia" con valor "Sí". Sin `KeyError` en los logs.

- [ ] **Step 8: Commit**

```bash
git add app.py
git commit -m "feat: campo andropausia en mapeo de formulario y docx"
```

---

### Task 11: Actualizar scripts de autofill

**Files:**
- Modify: `autofill-cuestionario.js`
- Modify: `bookmarklet-cuestionario.js` (regenerar minificado)

**Interfaces:**
- Consumes: los `id` de los `<select>` de Tasks 2-7: `f-sexo`, `f-horario`, `f-num-hijos`, `f-como-conociste`, `f-fuma-frec`, `f-alcohol-frec`, `f-horas-sueno`, `f-calidad-sueno`, `f-estres`, `f-dulces-frec`, `f-comidas`, `f-tipo-piel`, `f-act-fisica`, `f-satisfaccion`.
- Produces: autofill funcional para pruebas manuales.

- [ ] **Step 1: Leer `autofill-cuestionario.js` completo**

Run: `cat autofill-cuestionario.js` (o Read). Ubicar la función `clickRadio`, `clickScale`, y todas sus invocaciones.

- [ ] **Step 2: Agregar helper `setSelect`**

En `autofill-cuestionario.js`, junto a `clickRadio`:
```js
function setSelect(id, text) {
  const el = document.getElementById(id);
  if (!el) { console.warn('[autofill] select no encontrado:', id); return; }
  const opt = [...el.options].find(o => o.value === text || o.textContent.trim() === text);
  if (opt) { el.value = opt.value; el.dispatchEvent(new Event('change', {bubbles:true})); }
  else console.warn('[autofill] opción no encontrada:', id, text);
}
```

- [ ] **Step 3: Reemplazar las invocaciones de radios/escalas convertidos**

Cambiar (los valores de ejemplo son los del script actual — mantenerlos):
```js
clickRadio('sexo', 'Femenino');           → setSelect('f-sexo', 'Femenino');
clickRadio('horario_laboral', 'Mañana');  → setSelect('f-horario', 'Mañana');
clickRadio('num_hijos', '1');             → setSelect('f-num-hijos', '1');
clickRadio('como_conociste', 'Internet'); → setSelect('f-como-conociste', 'Internet / Google');
clickRadio('horas_sueno', '7–9h');        → setSelect('f-horas-sueno', '7–9h');
clickRadio('calidad_sueno', 'Profundo');  → setSelect('f-calidad-sueno', 'Profundo y reparador');
clickRadio('dulces_frec', 'Ocasionalmente'); → setSelect('f-dulces-frec', 'Ocasionalmente');
clickRadio('comidas', '3');               → setSelect('f-comidas', '3');
clickRadio('tipo_piel', 'Mixta');         → setSelect('f-tipo-piel', 'Mixta');
clickRadio('act_fisica', 'Ligero');       → setSelect('f-act-fisica', 'Ligero (1–2/sem)');
clickScale('scale-estres', 4);            → setSelect('f-estres', '4');
clickScale('scale-satisfaccion', 5);      → setSelect('f-satisfaccion', '5');
```
(`setSelect` acepta match por `value` o por texto, así que `'Internet'` no basta para "Internet / Google" — usar el texto completo. Ajustado arriba.)

Para fuma/alcohol frecuencia: el script actual hace `clickYN('Fuma', 'No')` y `clickYN('Consume alcohol', 'Ocasionalmente')`. Ese segundo está mal (Ocasionalmente no es Sí/No). Cambiar a:
```js
clickYN('Fuma', 'No');
// (no se toca frecuencia porque Fuma=No)
clickYN('Consume alcohol', 'Sí');
setSelect('f-alcohol-frec', 'Ocasional');
```

- [ ] **Step 4: Reemplazar `clickRadio('trabaja'...)` y `clickRadio('act_laboral'...)` si aún existen**

Esos campos ya están ocultos (`display:none`) desde trabajo previo. Si el autofill los llama, dejarlos (no rompen — `clickRadio` no encuentra el radio visible y no hace nada) o quitarlos para limpieza. Quitarlos:
```js
// clickRadio('trabaja', 'Sí');      ← eliminar
// clickRadio('act_laboral', ...);   ← eliminar
```

- [ ] **Step 5: Verificar sintaxis del autofill**

Run: `node -c autofill-cuestionario.js && echo "autofill OK"`
Esperado: `autofill OK`

- [ ] **Step 6: Regenerar `bookmarklet-cuestionario.js`**

El bookmarklet es la versión de una línea del autofill. Aplicar los mismos cambios (helper `setSelect`, reemplazo de invocaciones) al contenido minificado. Como es una sola línea `javascript:(function(){...})()`, editar con cuidado:
- Añadir la función `setSelect` junto a `clickRadio`.
- Reemplazar las llamadas igual que en Step 3.

Run: `node -e "eval(require('fs').readFileSync('bookmarklet-cuestionario.js','utf8').replace(/^javascript:/,''))" 2>&1 | head -3` — esto lo ejecutaría sin DOM y fallará en `document`, pero un error de sintaxis (`SyntaxError`) vs un error de runtime (`ReferenceError: document`) distingue si el JS es válido. Esperado: `ReferenceError` (no `SyntaxError`).

- [ ] **Step 7: Probar el autofill en server local**

`python3 app.py` → `http://localhost:5000/formulario` → abrir DevTools consola → pegar el contenido de `autofill-cuestionario.js` → Enter.
- Recorrer los 9 pasos: todos los `<select>` quedan con un valor seleccionado.
- Los `<select>` de frecuencia de fuma/alcohol: alcohol con "Ocasional", fuma sin frecuencia (Fuma=No).
- Sin warnings `[autofill] opción no encontrada` en consola.

- [ ] **Step 8: Commit**

```bash
git add autofill-cuestionario.js bookmarklet-cuestionario.js
git commit -m "chore: actualiza scripts de autofill para los campos <select>"
```

---

### Task 12: Verificación integral end-to-end + FIXLOG

**Files:**
- Modify: `FIXLOG.md`

- [ ] **Step 1: Levantar server local con env vars**

```bash
cd "/Users/master/Sitios Web/Metodo Carvajal/github-repo"
export CLAUDE_KEY=<key>
export GROQ_KEY=<key>
export RESEND_KEY=<key>
export CLOUDINARY_CLOUD_NAME=<val>
export CLOUDINARY_API_KEY=<val>
export CLOUDINARY_API_SECRET=<val>
export MAIL_TO=<tu-email-de-prueba>
python3 app.py
```
(Si no tienes las keys a mano, pedirlas al usuario o usar las de Railway. Para probar solo la UI sin generar plan, basta con que el server arranque — el `/formulario` es HTML estático servido por Flask.)

- [ ] **Step 2: Checklist visual completo**

Abrir `http://localhost:5000/formulario`. Recorrer los 9 pasos:

- [ ] Los 14 campos convertidos se ven como listas desplegables de 1 línea:
  Sexo, Horario laboral, Nº hijos, ¿Cómo nos conociste? (Paso 1);
  Frecuencia fuma, Frecuencia alcohol, Horas sueño, Calidad sueño, Nivel de estrés (Paso 2);
  Frecuencia dulces, Comidas/día (Paso 4);
  Tipo de piel (Paso 6); Satisfacción (Paso 7 real); Actividad física (Paso 8 real).
- [ ] Cada `<select>` abre con las opciones correctas y el texto exacto.
- [ ] Layout: pares de campos lado a lado en escritorio; 1 columna en móvil (<520px), sin scroll horizontal.
- [ ] Sexo = Femenino → Paso 2 muestra las 6 condiciones hormonales, no Andropausia.
- [ ] Sexo = Masculino → Paso 2 muestra solo Andropausia.
- [ ] Sexo sin elegir → sección hormonal oculta.
- [ ] Fuma = Sí → aparece `<select>` de frecuencia; Fuma = No → desaparece. Igual Alcohol.
- [ ] Horario laboral = Otro → aparece campo de texto libre; otra opción → desaparece.
- [ ] No existe subsección "Nivel de estrés" aparte; el campo está en "Hábitos de sueño".
- [ ] Paso 8 real: una sola pregunta de antecedentes familiares.

- [ ] **Step 3: Comparar payload con la versión `.bak`**

1. Guardar la versión actual del formulario, servir `formulario-produccion.html.bak` temporalmente (copiar sobre el original en otra carpeta, o abrir el `.bak` como archivo local).
2. Llenar ambas versiones con los MISMOS datos (usar el autofill).
3. En cada una, `submitForm()` y capturar el JSON de `POST /enviar` (DevTools → Network → payload → `data`).
4. Diff de los dos JSON. Los únicos campos que pueden diferir: `andropausia` (nuevo). Todo lo demás (`sexo`, `numHijos`, `pielTipo`, `nivelEstres`, `satisfaccion`, `actFisica`, `comoConociste`, `horarioLaboral`, `fuma`, `alcohol`, `sueno`) debe ser idéntico.
5. Si `alcohol` difiere: es por el fix del bug `step-4`→`s3` en Task 4 Step 8 — comportamiento intencional, documentarlo.

- [ ] **Step 4: Generar un plan completo de prueba**

Con el server corriendo y las keys reales (usar `GROQ_KEY` para abaratar — el selector está hardcodeado a `claude` en `submitForm`, así que temporalmente en consola: `window._modeloSel='groq'` ANTES de enviar, o editar la línea `window._modeloSel = 'claude'` de `submitForm` localmente sin commitear).

Enviar el formulario. Esperar a que el worker termine. Verificar:
- [ ] Sin `KeyError` ni excepción en los logs del servidor.
- [ ] El `.docx` generado: campos de opción reflejan lo elegido; fila `andropausia` presente si sexo=Masculino.
- [ ] El plan HTML generado carga sin errores; edad, IMC, sexo, perfil correctos.

- [ ] **Step 5: Revertir cualquier cambio local temporal**

Si editaste `window._modeloSel` en `submitForm` para probar con Groq, revertirlo:
Run: `git diff formulario-produccion.html` — debe estar limpio (sin el cambio de modelo). Si aparece, `git checkout formulario-produccion.html` NO (perderías todo) — editar manualmente para dejar `window._modeloSel = 'claude'`.

- [ ] **Step 6: Actualizar FIXLOG.md**

Añadir al inicio de `FIXLOG.md` (después del título) una sección:
```markdown
## 2026-09-08: Rediseño de eficiencia del formulario clínico

### Cambio

14 campos de opción única convertidos de grupos de botones/escalas a listas
desplegables `<select>`: Sexo, Horario laboral, Nº de hijos, ¿Cómo nos
conociste? (Paso 1); frecuencia de fuma/alcohol, horas y calidad de sueño,
nivel de estrés (Paso 2); frecuencia de dulces, comidas/día (Paso 4); tipo de
piel (Paso 6); satisfacción (Paso 9); actividad física (Paso 10).

- Sección "Condiciones hormonales" ahora se muestra según el sexo elegido
  (Femenino → 6 preguntas; Masculino → solo Andropausia). Campo `andropausia`
  conectado de cero (collectData → _mapear_formulario → docx).
- Frecuencia de fuma/alcohol: el `<select>` aparece solo si se responde "Sí".
- "Nivel de estrés" dejó de tener subsección propia; el campo vive dentro de
  "Hábitos de sueño".
- Eliminada la pregunta duplicada "¿En su familia hay historia de alguna
  enfermedad relevante?" (Paso 10) — estaba huérfana (no se recolectaba).
- Layout de 2 columnas en Pasos 1, 2 y 4 aprovechando el espacio liberado.

### Archivos modificados

- `formulario-produccion.html`: CSS `.field select`, HTML de los 14 campos,
  `collectData()`, listeners de sexo/fuma/alcohol/horario, función `toggleFrec`.
- `app.py`: campo `andropausia` en `_mapear_formulario` (~línea 2873) y en
  `generar_docx_cuestionario`.
- `autofill-cuestionario.js` / `bookmarklet-cuestionario.js`: helper
  `setSelect()` + reemplazo de invocaciones.

### Reversión

- Backup: `formulario-produccion.html.bak` (commit `cb52373`).
- Tag: `pre-rediseno-formulario`.
- Revertir: `git checkout pre-rediseno-formulario -- formulario-produccion.html`
  (nota: el `.bak` incluye los 5 campos ya ocultos de la ronda anterior; para
  restaurar `app.py` revertir manualmente el campo andropausia).

### Detalle técnico

- El backend `_mapear_formulario` recibe los mismos strings que antes: un
  `<select>` con `<option>` de texto idéntico al label del radio produce el
  mismo valor. Solo `andropausia` es nuevo.
- Bug preexistente corregido de paso: `collectData().alcohol` leía la pregunta
  "Consume alcohol" del panel `step-4` (Preferencias Alimentarias), donde no
  existe; ahora la lee de `step-2` (Condición Actual) — su ubicación real.
- Funciones `toggleScale`/`getScaleValue` y CSS `.scale-*` quedan inertes (sin
  uso) pero no se eliminan.

### Validación

- Comparación de payload `POST /enviar` contra la versión `.bak` con los mismos
  datos: idéntico salvo `andropausia` (y `alcohol` por el fix).
- Plan de prueba generado con Groq: sin `KeyError`, docx y HTML correctos.
```

- [ ] **Step 7: Commit final**

```bash
git add FIXLOG.md
git commit -m "docs: registra el rediseño de eficiencia del formulario en FIXLOG"
```

- [ ] **Step 8: NO hacer push automático**

Dejar todos los commits locales. Informar al usuario: "Rediseño completo, N commits locales, server local corriendo para revisión. Push a `main` (auto-deploy Railway) solo cuando confirmes."

---

## Self-Review — cobertura del spec

| Requisito del spec | Task que lo implementa |
|---|---|
| 14 campos → `<select>` (tabla del spec §1) | Tasks 2, 4, 5, 6, 7 |
| CSS `.field select` con placeholder `:invalid` | Task 1 |
| `collectData()` lee `.value`, mismos strings | Tasks 2, 4, 5, 6, 7 (Steps de `collectData`) |
| `initCheckboxes()` bloque `.radio-item` intacto | Task 2 Step 8 (nota explícita) |
| Listener horario "Otro" re-implementado | Task 2 Step 5 |
| Sección hormonal condicionada por sexo | Task 3 |
| "(solo mujeres)" quitado del título | Task 3 Step 1 |
| Andropausia visible si Masculino | Task 3 Step 1-2 |
| Estado inicial: sección hormonal oculta | Task 3 Step 1 (`display:none` + listener) |
| `andropausia` en collectData | Task 3 Step 3 |
| `andropausia` en `_mapear_formulario` + docx | Task 10 |
| Verificar `_datos_paciente` con andropausia | Task 10 Step 5 |
| Layout 2 columnas Pasos 1, 2, 4 | Task 9 |
| Responsive <520px sin tocar | Task 9 Step 5 (verificación) |
| Fusionar Fuma + frecuencia | Task 4 Steps 2-3 |
| Fusionar Alcohol + frecuencia | Task 4 Steps 2, 4 |
| `toggleFrec` genérica | Task 4 Step 2 |
| Nivel de estrés fuera de subsección propia | Task 4 Step 6 |
| Eliminar yn-row antecedentes duplicado | Task 8 |
| Verificar huérfano antes de borrar | Task 8 Step 1 |
| Renombrar subsección a "Contraindicaciones" | Task 8 Step 2 |
| Backup `.bak` + tag | Ya hecho (commit `cb52373`) — mencionado en header |
| Autofill `setSelect` + reemplazos | Task 11 |
| Regenerar bookmarklet | Task 11 Step 6 |
| Verificación: 14 selects visibles | Task 12 Step 2 |
| Verificación: opciones con texto exacto | Task 12 Step 2 |
| Verificación: sexo condiciona hormonal | Task 12 Step 2 |
| Verificación: fuma/alcohol muestran frecuencia | Task 12 Step 2 |
| Verificación: payload idéntico a `.bak` | Task 12 Step 3 |
| Verificación: plan generado sin KeyError | Task 12 Step 4 |
| Verificación: docx con andropausia | Task 12 Step 4 |
| FIXLOG actualizado | Task 12 Step 6 |
| Riesgo: texto de opción desalineado | Global Constraints + Tasks (copiar literal) + Task 12 Step 3 |
| Riesgo: `getYNValue` en secciones ocultas | Task 3 (getYNValue devuelve "No respondido", tolerado) |
| Riesgo: autofill roto a mitad | Task 11 (mismo trabajo) |
| Riesgo: sesiones parciales | Spec — verificado, no hay restauración frontend |

**Fuera de alcance (confirmado en spec):** eficiencia F (descartada), G, I; modularizar `app.py`; `prompt_carvajal.txt`; otros formularios.

## Notas para quien ejecute este plan

- El repo NO tiene test suite. Cada "verificación" es grep + revisión visual en `python3 app.py` + inspección de payload de red. No inventar tests unitarios.
- El mapeo de números de línea es del estado en commit `cb52373`. Si un número no cuadra, buscar por el texto del bloque (los steps incluyen el HTML/JS literal a buscar).
- Los `id` de panel NO coinciden con el número de paso visible: `stepIds = ['step-1','step-2','step-3','step-4','step-5','step-6','step-9','step-10','step-11']` — "Paso 7" visible = panel `id="step-9"`, "Paso 8" visible = `id="step-10"`. El step-7 y step-8 de HTML están saltados/ocultos.
- Si en cualquier task un campo NO está donde el plan dice, o su comportamiento difiere, **detener y reportar** — no improvisar. El mapeo campo→string alimenta el prompt de la IA y un error se propaga.
- Guion largo `–` (U+2013) aparece en: "5–7h", "7–9h", "2–3 veces/semana", "1–2/sem", "3–4/sem". Copiar literal, no sustituir por `-`.
- `python3 app.py` sirve el formulario como HTML; para probar solo la UI no hacen falta las API keys, solo que Flask arranque (puede quejarse de keys faltantes pero el `/formulario` responde).
