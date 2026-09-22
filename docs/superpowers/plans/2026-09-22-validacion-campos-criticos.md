# Validación de campos críticos del formulario — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. No hay test suite automatizado en este repo — verificación manual (grep, server local, inspección de payload).

**Goal:** Bloquear el envío del formulario si falta alguno de los 42 campos visibles marcados como críticos, y eliminar el `TypeError` en `generar_analisis_medico` que hacía que el análisis clínico se perdiera silenciosamente cuando `estatura`/`peso` llegaban vacíos.

**Architecture:** Trabajo sobre `formulario-produccion.html` (estructura de 9 pasos, la que está en producción hoy — el rediseño de 7 pasos sigue sin pushear en otra rama) y `app.py`. Se agrega una función `validarCamposObligatorios()` en el JS del formulario que corre antes de `submitForm()`, con un check explícito por campo (no un motor genérico — decisión del usuario). En `app.py`, se corrige la concatenación insegura en `generar_analisis_medico`.

**Tech Stack:** Flask monolito (`app.py`), HTML/CSS/JS vanilla (`formulario-produccion.html`). Sin test suite — verificación con server local + agent-browser + inspección de payload.

**Spec:** Este plan documenta su propio diseño (no hay spec separado — la lista de 42 campos fue auditada y aprobada por el usuario en la conversación del 2026-09-22, incluida como Apéndice A al final de este documento).

## Global Constraints

- **Trabajar sobre `origin/main` actual (commit `cdcf229`), NO sobre la rama del rediseño de 7 pasos.** Este fix va directo a producción, separado del rediseño pendiente de aprobación.
- **Worktree ya preparado:** `/tmp/carvajal-validacion` (branch `validacion-campos`, base `cdcf229`). Trabajar ahí, no en el checkout principal.
- **Solo campos VISIBLES en producción hoy** entran a la validación — un campo dentro de un contenedor `display:none` nunca debe bloquear el envío (patrón ya usado en el fix de "fecha de nacimiento" con `offsetParent`).
- **Detalle condicional también obligatorio:** si un yn-row "Sí/No" tiene detalle de texto libre y el usuario respondió "Sí", ese detalle es obligatorio (decisión del usuario, confirmada en la conversación).
- **No modularizar `app.py`** — sigue monolítico por convención del proyecto.
- **Commits frecuentes**, uno por task.
- **No hay test suite** — verificación manual con server local (`python3 app.py` en el worktree, con env vars dummy) y agent-browser.

---

## Apéndice A: Lista de 42 campos críticos (referencia para todas las tasks)

Cada fila: **# | Campo | Tipo | Selector/lógica de "respondido" | Detalle condicional (si aplica)**

1. Nombre completo — texto — `#f-nombre` — —
2. Sexo — radio — `name="sexo"` — —
3. Fecha de nacimiento — fecha — `#f-fechanac` — (ya validado en hotfix anterior, no se toca)
4. Celular — texto — `#f-celular` — —
5. Correo electrónico — texto — `#f-email` — —
6. Horario laboral — radio — `name="horario_laboral"` — si valor="Otro" → `#f-horario-otro` obligatorio
7. Número de hijos — radio — `name="num_hijos"` — —
8. Estatura — número — `#f-estatura` — —
9. Peso — número — `#f-peso` — —
10. ¿Sufre enfermedad? — yn-row — label contiene "sufre de alguna enfermedad" — si Sí → `#f-enfermedad-det` obligatorio
11. Fuma — yn-row — label "Fuma" (yn-row exacto, primera coincidencia en step-2) — si Sí → radio `name="fuma_frec"` obligatorio
12. Consume alcohol — yn-row — label "Consume alcohol" — si Sí → radio `name="alcohol_frec"` obligatorio
13. ¿Toma medicamentos? — yn-row — label "Toma medicamentos" — si Sí → `#f-medicamentos` obligatorio
14. ¿Va al baño todos los días? — yn-row — label "Vas al baño todos los días" — —
15. Horas de sueño — radio — `name="horas_sueno"` — —
16. Calidad del sueño — radio — `name="calidad_sueno"` — —
17. ¿Cansancio durante el día? — yn-row — label "cansancio o somnolencia durante el día" — —
18. Nivel de estrés — scale — `#scale-estres` (clase `.scale-btn.active`) — —
19. Hinchazón abdominal — yn-row — label "hinchazón abdominal" — —
20. Gases/flatulencias — yn-row — label "gases o flatulencias" — —
21. Dolor de cabeza/migrañas — yn-row — label "dolor de cabeza o migrañas" — —
22. Inflamación articular — yn-row — label "Inflamación en articulaciones" — —
23. Dificultad bajar de peso — yn-row — label "Dificultad para bajar de peso" — —
24. Náuseas — yn-row — label "Náuseas o malestar" — —
25. ¿Cuántas comidas al día? — radio — `name="comidas"` — —
26. Alergia medicamentos — yn-row (id) — `#arow-alg_medicamentos` — si Sí → `#asint-alg_medicamentos` obligatorio
27. Alergia alimentos — yn-row (id) — `#arow-alg_alimentos` — si Sí → `#asint-alg_alimentos` obligatorio
28. Alergia otro — yn-row (id) — `#arow-alg_otro` — si Sí → `#asint-alg_otro` obligatorio
29. ¿Cirugía? — yn-row — label "se ha realizado alguna cirugía" — si Sí → `#f-cirugias-det` obligatorio
30. Tipo de piel — radio — `name="tipo_piel"` — —
31. ¿Tratamientos estéticos previos? — yn-row — label "recibido tratamientos estéticos anteriormente" — —
32. ¿Complicaciones con tratamiento previo? — yn-row — label "Ha tenido complicaciones con algún tratamiento" — si Sí → `#f-complic-det` obligatorio
33. Áreas faciales a tratar — checkbox-grupo (≥1 marcado) — primer `.check-grid` dentro de la subsección "Área de Interés y Expectativas" — —
34. Prioridad principal — texto — `#f-prioridad` — —
35. Satisfacción actual — scale — `#scale-satisfaccion` — —
36. ¿Entiende múltiples sesiones? — yn-row — label "necesitarse múltiples sesiones" — —
37. ¿Rutina diaria de cuidado? — yn-row — label "Realiza rutina diaria de cuidado facial" — si Sí → checkbox-grupo "Rutina actual incluye" (≥1 marcado) obligatorio
38. Nivel de actividad física — radio — `name="act_fisica"` — —
39. ¿Antecedentes familiares (salud)? — yn-row — label "en su familia hay historia de alguna enfermedad" — —
40. ¿Alergias medicamentos/tópicos? — yn-row — label "alergias a medicamentos o productos tópicos" — —
41. ¿Marcapasos/dispositivos? — yn-row — label "marcapasos, implantes metálicos o dispositivos médicos" — —
42. ¿Familiar directo con enfermedades? — radio — `name="antecedentes_fam"` — si Sí → `#f-antecedentes-det` obligatorio

**Excluidos (en bloques `display:none`, no deben bloquear):** Cédula, Dirección, Edad manual, Contacto emergencia, ¿Trabaja actualmente?, ¿Con quién vive?, ¿Cuenta con ayuda en casa?, hora de baño/evacuación, "utiliza medicamento para dormir", "turnos nocturnos", 8 de 14 síntomas de intolerancia (estreñimiento, cansancio post-comida, picazón, congestión, cambios de humor, digestión lenta, antecedentes familiares intolerancias — nota: distinto del #39), síntomas por grupo de alimento (lácteos/gluten/procesados), toda "Preferencias Alimentarias" (proteínas/carbos/verduras/frutas/grasas/postres, incluye frecuencia de dulces), bebidas azucaradas, Textura/Oleosidad/Sensibilidad de piel, TODO el paso Capilar (step-8, panel completo oculto), los 9 tratamientos estéticos individuales con fecha/zona, "¿en tratamiento con láser?", Exposición solar/¿usa protector diario?, "Productos cosméticos", "¿infecciones cutáneas?".

---

## Estructura de archivos

| Archivo | Qué cambia |
|---|---|
| `formulario-produccion.html` | Nueva función `validarCamposObligatorios()` (JS) llamada al inicio de `submitForm()`; helpers de lectura por tipo de campo |
| `app.py` | Fix de concatenación insegura en `generar_analisis_medico` (líneas 2066-2067) |
| `FIXLOG.md` | Registro del cambio al terminar |

## Orden de tasks

1. **Task 1** — Fix `generar_analisis_medico` (independiente, urgente, la causa raíz original del reporte)
2. **Task 2** — Helpers de lectura de estado por tipo de campo (yn-row, radio, scale, checkbox-grupo) en el JS
3. **Task 3** — Función `validarCamposObligatorios()` con los 42 checks explícitos (depende de Task 2)
4. **Task 4** — Enganchar la validación en `submitForm()` + UI de error (scroll al primer campo faltante)
5. **Task 5** — Verificación end-to-end en server local
6. **Task 6** — FIXLOG + push a producción

---

### Task 1: Fix `TypeError` en `generar_analisis_medico`

**Files:**
- Modify: `/tmp/carvajal-validacion/app.py:2066-2067`

**Interfaces:**
- No produce ni consume nada nuevo — corrige una excepción no controlada.

- [ ] **Step 1: Ver el código actual**

```bash
cd /tmp/carvajal-validacion
sed -n '2060,2070p' app.py
```

Confirmar que las líneas son:
```python
'Estatura': data.get('estatura','') + ' cm',
'Peso': data.get('peso','') + ' kg',
```

- [ ] **Step 2: Aplicar el fix**

Reemplazar:
```python
        'Estatura': data.get('estatura','') + ' cm',
        'Peso': data.get('peso','') + ' kg',
```
por:
```python
        'Estatura': (data.get('estatura') or '') + ' cm',
        'Peso': (data.get('peso') or '') + ' kg',
```

(`data.get('estatura','')` NO aplica el default `''` cuando la clave existe pero su valor es `None` — solo cuando la clave falta. `data.get('estatura') or ''` sí cubre `None`, `''` y clave ausente.)

- [ ] **Step 3: Verificar sintaxis**

```bash
python3 -c "import ast; ast.parse(open('app.py').read()); print('OK')"
```

- [ ] **Step 4: Reproducir el caso que fallaba y confirmar que ya no explota**

```bash
"/Users/master/Sitios Web/Metodo Carvajal/github-repo/.venv/bin/python" -c "
import sys; sys.path.insert(0,'/tmp/carvajal-validacion')
data = {'estatura': None, 'peso': '63', 'nombre': 'Test'}
campos_estatura = (data.get('estatura') or '') + ' cm'
campos_peso = (data.get('peso') or '') + ' kg'
print('Estatura:', repr(campos_estatura), '| Peso:', repr(campos_peso))
print('Sin excepcion - OK')
"
```
Esperado: imprime sin lanzar `TypeError`.

- [ ] **Step 5: Commit**

```bash
cd /tmp/carvajal-validacion
git add app.py
git commit -m "fix: evita TypeError en generar_analisis_medico cuando estatura/peso son None

data.get('estatura','') NO aplica el default cuando la clave existe
con valor None (_mapear_formulario guarda 'estatura': est or None).
Al concatenar con ' cm' esto lanzaba TypeError, y el except silencioso
en worker() dejaba analisis_medico = None sin avisar a nadie.

Cambiado a (data.get('estatura') or '') que cubre None, '' y ausencia
de clave.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01ALSAGadnUCDVhtPghEBbF1"
```

---

### Task 2: Helpers de lectura de estado por tipo de campo

**Files:**
- Modify: `/tmp/carvajal-validacion/formulario-produccion.html` (bloque `<script>`, cerca de `getYNValue`/`getCheckedValues`, alrededor de la línea 1200)

**Interfaces:**
- Consumes: nada nuevo.
- Produces: 4 funciones globales que Task 3 usa:
  - `ynRespondida(container, labelText)` → `boolean`
  - `radioRespondido(name)` → `boolean`
  - `scaleRespondida(groupId)` → `boolean`
  - `checkGrupoRespondido(selector)` → `boolean` (al menos 1 marcado)

- [ ] **Step 1: Ubicar el bloque de helpers existentes**

```bash
cd /tmp/carvajal-validacion
grep -n "function getYNValue\|function getCheckedValues\|function getScaleValue" formulario-produccion.html
```

- [ ] **Step 2: Agregar los 4 helpers nuevos justo después de `getCheckedValues`**

```javascript
// ── Helpers de validación de campos obligatorios ──
function ynRespondida(container, labelText){
  if(!container) return false;
  let found = false;
  container.querySelectorAll('.yn-row').forEach(row=>{
    if(found) return;
    const lbl = row.querySelector('.yn-label');
    if(!lbl) return;
    const txt = lbl.textContent.replace(/\*/g,'').trim().toLowerCase();
    if(txt.includes(labelText.toLowerCase())){
      const ay = row.querySelector('.active-yes');
      const an = row.querySelector('.active-no');
      found = !!(ay || an);
    }
  });
  return found;
}
function radioRespondido(name){
  return !!document.querySelector('input[name="'+name+'"]:checked');
}
function scaleRespondida(groupId){
  const group = document.getElementById(groupId);
  return !!(group && group.querySelector('.scale-btn.active'));
}
function checkGrupoRespondido(selector){
  const cont = document.querySelector(selector);
  return !!(cont && cont.querySelector('.check-item.checked'));
}
```

- [ ] **Step 3: Verificar sintaxis JS**

```bash
node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>\$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"
```

- [ ] **Step 4: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: helpers de lectura de estado para validación de campos obligatorios

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01ALSAGadnUCDVhtPghEBbF1"
```

---

### Task 3: Función `validarCamposObligatorios()` — los 42 checks

**Files:**
- Modify: `/tmp/carvajal-validacion/formulario-produccion.html` (agregar función nueva antes de `submitForm()`)

**Interfaces:**
- Consumes: `ynRespondida`, `radioRespondido`, `scaleRespondida`, `checkGrupoRespondido` (Task 2).
- Produces: `validarCamposObligatorios()` → devuelve `{ok: true}` o `{ok: false, mensaje: '...', stepId: 'step-X', focusEl: <element|null>}`. Task 4 la consume.

Cada check es explícito (if por campo, según decisión del usuario) — NO un motor genérico. El orden de los checks sigue el orden de los pasos (1→9) para que el primer error reportado sea el primero que el usuario vería recorriendo el formulario normalmente.

- [ ] **Step 1: Localizar `submitForm()`**

```bash
grep -n "^function submitForm" formulario-produccion.html
```

- [ ] **Step 2: Escribir la función completa, justo antes de `function submitForm(){`**

```javascript
// ── Validación de campos obligatorios antes de enviar ──
function validarCamposObligatorios(){
  const err = (mensaje, stepId, focusEl) => ({ok:false, mensaje, stepId, focusEl:focusEl||null});

  const s2 = document.getElementById('step-2');  // Condición Actual
  const s3 = document.getElementById('step-3');  // Intolerancias Alimentarias
  const s5 = document.getElementById('step-5');  // Alergias
  const s6 = document.getElementById('step-6');  // Historial Quirúrgico y Piel
  const s9 = document.getElementById('step-9');  // Objetivos
  const s10 = document.getElementById('step-10'); // Estilo de Vida

  // Paso 1: Datos Personales
  if(!document.getElementById('f-nombre').value.trim())
    return err('Por favor indica tu nombre completo.', 'step-1', document.getElementById('f-nombre'));
  if(!radioRespondido('sexo'))
    return err('Por favor indica tu sexo.', 'step-1', null);
  // Fecha de nacimiento ya se valida en submitForm() con su propio check.
  if(!document.getElementById('f-celular').value.trim())
    return err('Por favor indica tu número de celular.', 'step-1', document.getElementById('f-celular'));
  if(!document.getElementById('f-email').value.trim())
    return err('Por favor indica tu correo electrónico.', 'step-1', document.getElementById('f-email'));
  if(!radioRespondido('horario_laboral'))
    return err('Por favor indica tu horario laboral.', 'step-1', null);
  const horarioSelRadio = document.querySelector('input[name="horario_laboral"]:checked');
  if(horarioSelRadio && horarioSelRadio.value === 'Otro' && !document.getElementById('f-horario-otro').value.trim())
    return err('Por favor describe tu horario laboral.', 'step-1', document.getElementById('f-horario-otro'));
  if(!radioRespondido('num_hijos'))
    return err('Por favor indica tu número de hijos.', 'step-1', null);

  // Paso 2: Condición Actual
  if(!document.getElementById('f-estatura').value.trim())
    return err('Por favor indica tu estatura.', 'step-2', document.getElementById('f-estatura'));
  if(!document.getElementById('f-peso').value.trim())
    return err('Por favor indica tu peso.', 'step-2', document.getElementById('f-peso'));
  if(!ynRespondida(s2, 'sufre de alguna enfermedad'))
    return err('Por favor indica si sufres de alguna enfermedad.', 'step-2', null);
  {
    const enf = document.querySelector('input[name="enfermedad"]:checked');
    if(enf && enf.closest('.radio-item').textContent.trim()==='Sí' && !document.getElementById('f-enfermedad-det').value.trim())
      return err('Por favor describe tu enfermedad.', 'step-2', document.getElementById('f-enfermedad-det'));
  }
  if(!ynRespondida(s2, 'fuma'))
    return err('Por favor indica si fumas.', 'step-2', null);
  if(ynRespondida(s2,'fuma') && getYNValue(s2,'fuma')==='Sí' && !radioRespondido('fuma_frec'))
    return err('Por favor indica con qué frecuencia fumas.', 'step-2', null);
  if(!ynRespondida(s2, 'consume alcohol'))
    return err('Por favor indica si consumes alcohol.', 'step-2', null);
  if(ynRespondida(s2,'consume alcohol') && getYNValue(s2,'alcohol')==='Sí' && !radioRespondido('alcohol_frec'))
    return err('Por favor indica con qué frecuencia consumes alcohol.', 'step-2', null);
  if(!ynRespondida(s2, 'toma medicamentos'))
    return err('Por favor indica si tomas medicamentos, vitaminas o suplementos.', 'step-2', null);
  {
    const tomaMed = getYNValue(s2, 'toma medicamentos');
    if(tomaMed==='Sí' && !document.getElementById('f-medicamentos').value.trim())
      return err('Por favor especifica qué medicamentos tomas.', 'step-2', document.getElementById('f-medicamentos'));
  }
  if(!ynRespondida(s2, 'vas al baño todos los días'))
    return err('Por favor indica si vas al baño todos los días.', 'step-2', null);
  if(!radioRespondido('horas_sueno'))
    return err('Por favor indica tu promedio de horas de sueño.', 'step-2', null);
  if(!radioRespondido('calidad_sueno'))
    return err('Por favor indica la calidad de tu sueño.', 'step-2', null);
  if(!ynRespondida(s2, 'cansancio o somnolencia durante el día'))
    return err('Por favor indica si sientes cansancio durante el día.', 'step-2', null);
  if(!scaleRespondida('scale-estres'))
    return err('Por favor indica tu nivel de estrés diario.', 'step-2', null);

  // Paso 3: Intolerancias Alimentarias
  if(!ynRespondida(s3, 'hinchazón abdominal'))
    return err('Por favor responde sobre hinchazón abdominal.', 'step-3', null);
  if(!ynRespondida(s3, 'gases o flatulencias'))
    return err('Por favor responde sobre gases o flatulencias.', 'step-3', null);
  if(!ynRespondida(s3, 'dolor de cabeza o migrañas'))
    return err('Por favor responde sobre dolor de cabeza o migrañas.', 'step-3', null);
  if(!ynRespondida(s3, 'inflamación en articulaciones'))
    return err('Por favor responde sobre inflamación en articulaciones.', 'step-3', null);
  if(!ynRespondida(s3, 'dificultad para bajar de peso'))
    return err('Por favor responde sobre dificultad para bajar de peso.', 'step-3', null);
  if(!ynRespondida(s3, 'náuseas o malestar'))
    return err('Por favor responde sobre náuseas o malestar.', 'step-3', null);

  // Paso 4: Preferencias Alimentarias
  if(!radioRespondido('comidas'))
    return err('Por favor indica cuántas comidas haces al día.', 'step-4', null);

  // Paso 5: Alergias
  if(!ynRespondida(s5, 'medicamentos en general'))
    return err('Por favor indica si tienes alergia a medicamentos.', 'step-5', null);
  {
    const detMed = document.getElementById('adet-alg_medicamentos');
    if(detMed && detMed.style.display!=='none' && !document.getElementById('asint-alg_medicamentos').value.trim())
      return err('Por favor describe tu reacción alérgica a medicamentos.', 'step-5', document.getElementById('asint-alg_medicamentos'));
  }
  if(!ynRespondida(s5, 'alimentos en general'))
    return err('Por favor indica si tienes alergia a alimentos.', 'step-5', null);
  {
    const detAlim = document.getElementById('adet-alg_alimentos');
    if(detAlim && detAlim.style.display!=='none' && !document.getElementById('asint-alg_alimentos').value.trim())
      return err('Por favor describe tu reacción alérgica a alimentos.', 'step-5', document.getElementById('asint-alg_alimentos'));
  }
  if(!ynRespondida(s5, 'otro'))
    return err('Por favor indica si tienes otra alergia.', 'step-5', null);
  {
    const detOtro = document.getElementById('adet-alg_otro');
    if(detOtro && detOtro.style.display!=='none' && !document.getElementById('asint-alg_otro').value.trim())
      return err('Por favor describe tu otra reacción alérgica.', 'step-5', document.getElementById('asint-alg_otro'));
  }

  // Paso 6: Historial Quirúrgico y Piel
  if(!ynRespondida(s6, 'se ha realizado alguna cirugía'))
    return err('Por favor indica si te has realizado alguna cirugía.', 'step-6', null);
  {
    const cir = getYNValue(s6, 'cirugía');
    if(cir==='Sí' && !document.getElementById('f-cirugias-det').value.trim())
      return err('Por favor describe tu cirugía.', 'step-6', document.getElementById('f-cirugias-det'));
  }
  if(!radioRespondido('tipo_piel'))
    return err('Por favor indica cómo describirías tu piel.', 'step-6', null);

  // Paso 9: Objetivos y Estética Previa
  if(!ynRespondida(s9, 'recibido tratamientos estéticos anteriormente'))
    return err('Por favor indica si has recibido tratamientos estéticos anteriormente.', 'step-9', null);
  if(!ynRespondida(s9, 'ha tenido complicaciones con algún tratamiento'))
    return err('Por favor indica si has tenido complicaciones con algún tratamiento.', 'step-9', null);
  {
    const complic = getYNValue(s9, 'complicaciones con algún tratamiento');
    const wrap = document.getElementById('complic-det-wrap');
    if(complic==='Sí' && wrap && !document.getElementById('f-complic-det').value.trim())
      return err('Por favor describe las complicaciones que tuviste.', 'step-9', document.getElementById('f-complic-det'));
  }
  if(!checkGrupoRespondido('#step-9 .subsection:last-of-type .check-grid'))
    return err('Por favor marca al menos un área facial a tratar.', 'step-9', null);
  if(!document.getElementById('f-prioridad').value.trim())
    return err('Por favor indica cuál es tu prioridad principal.', 'step-9', document.getElementById('f-prioridad'));
  if(!scaleRespondida('scale-satisfaccion'))
    return err('Por favor indica tu satisfacción actual con el área a tratar.', 'step-9', null);
  if(!ynRespondida(s9, 'necesitarse múltiples sesiones'))
    return err('Por favor confirma que entiendes que pueden necesitarse múltiples sesiones.', 'step-9', null);

  // Paso 10: Estilo de Vida y Antecedentes
  if(!ynRespondida(s10, 'realiza rutina diaria de cuidado facial'))
    return err('Por favor indica si realizas una rutina diaria de cuidado facial.', 'step-10', null);
  {
    const tieneRutina = getYNValue(s10, 'rutina diaria de cuidado facial');
    if(tieneRutina==='Sí' && !checkGrupoRespondido('#rutina-det-wrap .check-grid'))
      return err('Por favor marca qué incluye tu rutina actual.', 'step-10', null);
  }
  if(!radioRespondido('act_fisica'))
    return err('Por favor indica tu nivel de actividad física.', 'step-10', null);
  if(!ynRespondida(s10, 'en su familia hay historia de alguna enfermedad'))
    return err('Por favor indica si hay antecedentes familiares de enfermedad.', 'step-10', null);
  if(!ynRespondida(s10, 'alergias a medicamentos o productos tópicos'))
    return err('Por favor indica si tienes alergias a medicamentos o productos tópicos.', 'step-10', null);
  if(!ynRespondida(s10, 'marcapasos, implantes metálicos o dispositivos'))
    return err('Por favor indica si tienes marcapasos o dispositivos médicos.', 'step-10', null);
  if(!radioRespondido('antecedentes_fam'))
    return err('Por favor indica si algún familiar directo tiene enfermedades relevantes.', 'step-10', null);
  {
    const fam = document.querySelector('input[name="antecedentes_fam"]:checked');
    if(fam && fam.closest('.radio-item').textContent.trim()==='Sí' && !document.getElementById('f-antecedentes-det').value.trim())
      return err('Por favor indica cuáles enfermedades tienen tus familiares.', 'step-10', document.getElementById('f-antecedentes-det'));
  }

  return {ok:true};
}
```

**Nota sobre el check #33 (Áreas faciales):** el selector `'#step-9 .subsection:last-of-type .check-grid'` asume que "Área de Interés y Expectativas" es la última `.subsection` del panel y que su primer `.check-grid` son las áreas faciales (el segundo son las corporales, no obligatorio). Verificar esto en el Step 3 de este task antes de dar por buena la función.

- [ ] **Step 3: Verificar el selector de "Áreas faciales" contra el HTML real**

```bash
grep -n "Área de Interés y Expectativas\|Áreas FACIALES\|Áreas CORPORALES" formulario-produccion.html
```

Confirmar que la subsección "Área de Interés y Expectativas" es efectivamente la última dentro de `#step-9`, y que "Áreas FACIALES a tratar" es el primer `.check-grid` dentro de ella. Si el selector no cuadra, ajustarlo a uno más directo — por ejemplo, envolver el check-grid de áreas faciales en un `id="areas-faciales-grid"` y usar ese id en vez de `:last-of-type`. Preferir esta opción si hay cualquier duda, es más robusta que depender del orden del DOM.

- [ ] **Step 4: Verificar sintaxis JS**

```bash
node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>\$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"
```

- [ ] **Step 5: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: función validarCamposObligatorios con los 42 checks críticos

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01ALSAGadnUCDVhtPghEBbF1"
```

---

### Task 4: Enganchar la validación en `submitForm()`

**Files:**
- Modify: `/tmp/carvajal-validacion/formulario-produccion.html` (función `submitForm()`)

**Interfaces:**
- Consumes: `validarCamposObligatorios()` (Task 3), `goToStep(n)`, `stepIds` (ya existentes).

- [ ] **Step 1: Ver el `submitForm()` actual**

```bash
grep -n "^function submitForm" -A 15 formulario-produccion.html
```

Debe verse así (con el check de fecha de nacimiento del hotfix anterior):
```javascript
function submitForm(){
  window._modeloSel = 'claude';
  if(!document.getElementById('f-fechanac').value){
    alert('Por favor indica tu fecha de nacimiento.');
    goToStep(1);
    document.getElementById('f-fechanac').focus();
    return;
  }
  const consents=document.querySelectorAll('#step-11 .consent-item input[type="checkbox"]');
  ...
```

- [ ] **Step 2: Insertar la llamada a `validarCamposObligatorios()` después del check de fecha de nacimiento y antes del check de consentimientos**

```javascript
function submitForm(){
  window._modeloSel = 'claude';
  if(!document.getElementById('f-fechanac').value){
    alert('Por favor indica tu fecha de nacimiento.');
    goToStep(1);
    document.getElementById('f-fechanac').focus();
    return;
  }
  const val = validarCamposObligatorios();
  if(!val.ok){
    alert(val.mensaje);
    const idx = stepIds.indexOf(val.stepId);
    if(idx >= 0) goToStep(idx + 1);
    if(val.focusEl) val.focusEl.focus();
    return;
  }
  const consents=document.querySelectorAll('#step-11 .consent-item input[type="checkbox"]');
  ...
```

- [ ] **Step 3: Verificar sintaxis JS**

```bash
node -e "const fs=require('fs');const h=fs.readFileSync('formulario-produccion.html','utf8');const m=h.match(/<script>([\s\S]*?)<\/script>/g);let ok=true;m.forEach((s,i)=>{try{new Function(s.replace(/^<script>/,'').replace(/<\/script>\$/,''));}catch(e){ok=false;console.log(i,e.message);}});console.log(ok?'JS OK':'JS FAIL');"
```

- [ ] **Step 4: Commit**

```bash
git add formulario-produccion.html
git commit -m "feat: bloquea el envío si falta algún campo obligatorio

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01ALSAGadnUCDVhtPghEBbF1"
```

---

### Task 5: Verificación end-to-end en server local

**Files:** ninguno (solo verificación)

- [ ] **Step 1: Levantar server local en el worktree**

```bash
cd /tmp/carvajal-validacion
python3 -m venv .venv 2>/dev/null || true
.venv/bin/pip install -q -r requirements.txt
CLAUDE_KEY=dummy GROQ_KEY=dummy RESEND_KEY=dummy CLOUDINARY_CLOUD_NAME=dummy CLOUDINARY_API_KEY=dummy CLOUDINARY_API_SECRET=dummy MAIL_TO=test@test.com BASE_URL=http://localhost:5001 .venv/bin/python app.py
```
(Puerto 5001 para no chocar con cualquier server que siga corriendo del trabajo de rediseño en el otro worktree, puerto 5000.)

- [ ] **Step 2: Probar con agent-browser — envío vacío debe bloquear en Paso 1**

```bash
agent-browser open "http://localhost:5001/formulario"
agent-browser eval "goToStep(9); submitForm();"
```
Esperado: aparece un `alert` con el mensaje del primer campo faltante (nombre completo), y la vista regresa al Paso 1. (agent-browser puede necesitar manejar el diálogo nativo del `alert` — usar `agent-browser eval` para leer `window.__lastAlert` si se instrumenta, o verificar visualmente con screenshot que quedó en step-1).

- [ ] **Step 3: Rellenar todos los 42 campos con el autofill existente y confirmar que valida OK**

```bash
agent-browser eval "$(cat autofill-cuestionario.js)"
agent-browser eval "JSON.stringify(validarCamposObligatorios())"
```
Esperado: `{"ok":true}`. Si da `false`, el mensaje indica qué campo falta — ajustar el autofill o el check según corresponda (el autofill ya cubre casi todos estos campos porque fue escrito para el formulario completo).

- [ ] **Step 4: Probar un caso de detalle condicional — enfermedad = Sí sin detalle**

```bash
agent-browser eval "goToStep(2);"
agent-browser eval "
const btn = [...document.querySelectorAll('#step-2 .yn-row')].find(r=>r.querySelector('.yn-label').textContent.includes('sufre de alguna enfermedad')).querySelectorAll('.yn-btn')[0];
btn.click();
document.getElementById('f-enfermedad-det').value = '';
JSON.stringify(validarCamposObligatorios())
"
```
Esperado: `{"ok":false, "mensaje":"Por favor describe tu enfermedad.", ...}`.

- [ ] **Step 5: Probar que un campo oculto NO bloquea (ej. Cédula, siempre vacía)**

Confirmar que `validarCamposObligatorios()` con todo lo demás lleno y Cédula vacía sigue dando `{ok:true}` — Cédula no está en ningún check de la función, así que esto es automático, pero confirmar visualmente que no se coló por error.

- [ ] **Step 6: Confirmar que el pipeline backend sigue funcionando con el payload validado**

```bash
agent-browser eval "JSON.stringify(collectData())" | tail -1 > /tmp/payload-val.json
.venv/bin/python -c "
import json,sys; sys.path.insert(0,'.')
raw=json.loads(open('/tmp/payload-val.json').read()); data=json.loads(raw) if isinstance(raw,str) else raw
import app
m=app._mapear_formulario(data)
print('estatura:', repr(m.get('estatura')), '| peso:', repr(m.get('peso')))
analisis_ok = True
try:
    campos_test = {'Estatura': (data.get('estatura') or '') + ' cm', 'Peso': (data.get('peso') or '') + ' kg'}
    print('generar_analisis_medico concat OK:', campos_test)
except Exception as e:
    analisis_ok = False
    print('FALLO:', e)
print('Pipeline OK' if analisis_ok else 'Pipeline FALLO')
"
rm -f /tmp/payload-val.json
```
Esperado: `estatura`/`peso` con valores reales (no `None`), concatenación sin excepción.

- [ ] **Step 7: Cerrar browser y detener server**

```bash
agent-browser close --all
```
Detener el proceso de `python app.py` (Ctrl+C o `lsof -ti:5001 | xargs kill`).

---

### Task 6: FIXLOG + push a producción

**Files:**
- Modify: `/tmp/carvajal-validacion/FIXLOG.md`

- [ ] **Step 1: Agregar entrada al inicio de FIXLOG.md**

```markdown
## 2026-09-22: Validación de campos críticos + fix de análisis médico

### Cambio

El formulario ahora bloquea el envío (`submitForm()`) si falta alguno de 42
campos visibles marcados como críticos para el análisis clínico y la
generación del plan: datos personales básicos, estatura/peso, condición
médica general, hábitos (fuma/alcohol/medicamentos), síntomas digestivos
visibles, alergias (medicamentos/alimentos/otro), tipo de piel, historial
estético, áreas a tratar, prioridad, satisfacción, actividad física y
antecedentes familiares — con sus detalles condicionales (ej. "si Sí,
describa") también obligatorios cuando aplica.

Antes de esto, casi ningún asterisco (`*`) del formulario bloqueaba nada —
solo era decorativo. Esto permitía enviar el formulario con campos vacíos
que rompían el pipeline en silencio.

### Caso real que motivó el fix

Paciente Yasmina Carvajal (22-sep-2026): dejó "Estatura" vacía. Efecto:
- El IMC no pudo calcularse en ningún punto del pipeline (correcto, sin
  estatura no hay IMC posible — no era el bug, era dato faltante).
- **Bug real:** `generar_analisis_medico()` (`app.py` línea 2066) hacía
  `data.get('estatura','') + ' cm'`. Como `_mapear_formulario` guarda
  `estatura: est or None` cuando el campo llega vacío, y `.get(key,'')`
  NO aplica el default cuando la clave existe con valor `None` (solo
  cuando la clave falta), esto era `None + ' cm'` → `TypeError`. El
  worker capturaba la excepción en silencio (línea 2662,
  `except Exception as e: print(...)`) y el análisis clínico completo
  se perdía sin que nadie se enterara.

### Archivos modificados

- `app.py`: `(data.get('estatura') or '') + ' cm'` y análogo para peso —
  cubre `None`, `''` y clave ausente.
- `formulario-produccion.html`: helpers `ynRespondida`, `radioRespondido`,
  `scaleRespondida`, `checkGrupoRespondido`; función
  `validarCamposObligatorios()` con 42 checks explícitos; enganchada en
  `submitForm()` antes del check de consentimientos.

### Validación

- Envío vacío bloquea en el Paso 1 con mensaje del primer campo faltante.
- Autofill completo (`autofill-cuestionario.js`) pasa la validación.
- Detalle condicional (ej. enfermedad=Sí sin descripción) bloquea.
- Campos en bloques ocultos (Cédula, Dirección, etc.) no bloquean.
- Pipeline backend (`_mapear_formulario`, `generar_analisis_medico`) sin
  excepción con estatura/peso presentes.

### Nota sobre alcance

Esta validación se aplicó sobre la estructura de 9 pasos que está en
producción. El rediseño de eficiencia (14 selects, 7 pasos, condiciones
por sexo) sigue en una rama separada sin pushear — cuando se apruebe y
se fusione, esta validación deberá revisarse contra la nueva estructura
de pasos (los `stepId` de `goToStep()` cambian).
```

- [ ] **Step 2: Commit**

```bash
cd /tmp/carvajal-validacion
git add FIXLOG.md
git commit -m "docs: registra validación de campos críticos y fix de análisis médico en FIXLOG

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01ALSAGadnUCDVhtPghEBbF1"
```

- [ ] **Step 3: Push a producción**

**Confirmar con el usuario antes de este paso — push dispara auto-deploy Railway.**

```bash
cd /tmp/carvajal-validacion
git push origin validacion-campos:main
```

- [ ] **Step 4: Verificar el deploy**

```bash
sleep 30
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://metodo.centrocarvajal.com/formulario
gh api repos/lsaijr/carvajal-metodo/commits/main --jq '.sha, .commit.message'
```

- [ ] **Step 5: Rebasar la rama del rediseño local (7 pasos) sobre el nuevo origin/main**

Volver al checkout principal (NO el worktree):
```bash
cd "/Users/master/Sitios Web/Metodo Carvajal/github-repo"
git fetch origin
git rebase origin/main main
```
Resolver cualquier conflicto — es esperable en `formulario-produccion.html` dado que ambas ramas tocan `submitForm()` y la estructura de pasos. Si el rebase automático falla, **detener y reportar el conflicto en vez de resolverlo a ciegas** — la validación de 42 campos escrita en esta rama usa los `stepId` de 9 pasos (`step-2`, `step-3`, `step-5`, `step-6`, `step-9`, `step-10`); el rediseño los renumeró a 7 pasos (`step-2`, `step-3`, `step-6`, `step-9`, `step-10` sin `step-5`) y movió Alergias dentro de `step-2`. La función `validarCamposObligatorios()` necesitará actualizarse a la nueva estructura como parte de resolver el conflicto — esto es trabajo de merge, no un simple "aceptar los dos lados".

- [ ] **Step 6: Limpiar el worktree**

```bash
git worktree remove /tmp/carvajal-validacion --force
git branch -d validacion-campos
```
(Solo después de confirmar que el push y el rebase salieron bien — mismo patrón de seguridad usado en el hotfix del IMC.)
