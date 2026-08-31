# Registro de Correcciones — Centro Carvajal

## 2026-08-31: Costo mensual estimado y prioridad a Medicina Estética

### Cambio

La sección de tratamientos del plan personalizado ahora muestra el **costo mensual estimado** como la cifra principal de inversión, en lugar de resaltar el total anual.

### Archivos modificados

- `app.py` (~línea 3447): prompt `SYS3` actualizado para pedir a la IA:
  - Campo `costo_mensual_estimado` calculado como `total_anual / 12`.
  - Campo `tipo` por tratamiento (`Medicina Estética` o `Estético`).
  - Priorizar tratamientos de la categoría **Medicina Estética** del catálogo cuando el perfil clínico lo justifique.
- `app.py` (~línea 3609): estilos CSS nuevos para el recuadro de costo mensual y el badge "Medicina Estética".
- `app.py` (~línea 3888): plantilla HTML reemplaza el recuadro "Inversión Total del Plan" por "Costo mensual estimado para tu rutina personalizada ... / mes" con el total anual como referencia secundaria.
- `app.py` (~línea 4057): `render_plan()` carga el catálogo, detecta tratamientos de Medicina Estética por nombre/categoría, agrega el badge y calcula el costo mensual como fallback si la IA no lo devuelve.

### Detalle técnico

- El catálogo `catalogo_tratamientos.json` ya contiene el campo `categoria`; no requirió cambios.
- Si la IA no devuelve `costo_mensual_estimado`, el backend lo calcula como `total_anual / 12`.
- El total anual sigue visible en letra pequeña debajo del costo mensual.

### Validación

- Generar plan de prueba (preferiblemente con `groq` por costo) y verificar que `pilar5` incluya `costo_mensual_estimado`.
- Confirmar visualmente el badge "Medicina Estética" en tratamientos correspondientes.
- Confirmar que el fallback funciona si el campo está ausente.

---

## Diseño 2026-08-08: Reducción de campos del formulario según revisión del cliente

### Contexto

El 31 de julio de 2026 se envió al cliente un email de "Revisión de campos" (`/formulario-seleccion`) listando 150 preguntas del formulario clínico de 11 pasos (`formulario-produccion.html`), cada una marcada **Mantener** (80) o **Quitar** (70). Este documento es el diseño aprobado para aplicar esa decisión al sistema completo, no solo al HTML.

### Alcance

1. **Ocultar (no eliminar) los 70 campos "Quitar"** en `formulario-produccion.html` mediante `display:none` en su contenedor (label + input + cualquier detalle condicional). El markup y JS quedan en el archivo, inertes.
2. **`collectData()` (JS)** deja de leer/enviar los campos ocultados que hoy sí viajan en el payload — evita enviar datos fantasma.
3. **`_mapear_formulario` (`app.py` ~2594)** deja de leer las claves de los campos ocultados que hoy sí se procesaban.
4. **`_datos_paciente()` (`app.py` ~3198-3232)**, el resumen que se inyecta al prompt de la IA: se eliminan las líneas del f-string correspondientes a campos "Quitar" que hoy sí llegaban al LLM. Evita `KeyError` por clave faltante en `d` y evita ruido/huecos en el prompt.
5. **`generar_docx_cuestionario` (`app.py` ~1941)**: se eliminan las llamadas `_fila(...)` de los campos "Quitar" que hoy se imprimían en el Word.
6. **Validación de envío** (`submitForm`, checks de toggles/consentimientos obligatorios, ~línea 1521): se ajustan los selectores para excluir elementos `display:none` de la validación obligatoria — un campo oculto no puede bloquear el envío pidiendo que se marque.

### Bugs preexistentes a corregir en la misma pasada (hallados durante la exploración, no relacionados con la selección de campos pero deben quedar bien porque tocan campos que permanecen "Mantener")

1. `pielProblemas` en `_mapear_formulario` (línea 2883) lee `areasFaciales` en vez de los checkboxes reales del step 6 (piel). Corregir a leer el campo correcto — afecta Inflamación/Brotes, Pigmentación, Envejecimiento cutáneo (quedan "Mantener").
2. Los 5 checkboxes de consentimiento se escriben siempre como "Acepto" fijo en el docx (línea 2617-2621), sin leer el estado real. Corregir para reflejar el valor real marcado.
3. `infeccionesDet` / `dispositivosDet` se leen en el docx (líneas 2519, 2521) pero nunca se generan en `_mapear_formulario` — siempre vacíos. Conectar a los campos reales `infeccionesCutaneas` / `dispositivosMedicos`, que ya se capturan y quedan "Mantener".
4. `_fila('tratamiento_otro', 'NO')` hardcodeado (línea 2596), ignora si el paciente marcó "Otro tratamiento estético" real. Corregir para leer el dato real.
5. `_fila('entiende_sesiones', 'SÍ')` hardcodeado (línea 2613) y el campo "¿Entiende que pueden necesitarse múltiples sesiones?" no está conectado en absoluto (ni en `collectData()`). Quedó marcado "Mantener" en la revisión — conectar de cero: recolectar en JS, mapear en `_mapear_formulario`, leer valor real en docx.

### Fuera de alcance

- `parsear_cuestionario` (ruta alterna de importar cuestionario en texto) — no se toca salvo que comparta código directo con `_mapear_formulario`.
- `prompt_carvajal.txt` — confirmado que no se carga en runtime (el prompt real está hardcodeado inline en `generar_plan_ia`, `SYS1`/`SYS2`/`SYS3`). No requiere cambios.
- No se reorganiza ni modulariza `app.py` (sigue monolítico, por convención documentada en README.md raíz).

### Verificación (manual, no hay test suite automatizado en el repo)

1. Local con `GROQ_KEY` (modelo barato para pruebas, por convención del proyecto).
2. `/formulario`: confirmar visualmente que los 70 campos "Quitar" no aparecen y los 80 "Mantener" sí.
3. Autofill de consola o llenado manual → `submitForm()` sin bloqueo de validación por campos ocultos.
4. Revisar payload de red — confirmar que no viaje ningún campo oculto.
5. Revisar `.docx` generado — sin filas de campos quitados, con los 5 bugs corregidos.
6. Revisar plan HTML generado por IA — sin `KeyError`, sin referencias a campos que ya no se recolectan.

### Mapeo completo campo → código

Ver detalle exhaustivo (tabla por sección: id HTML, variable en `_mapear_formulario`, uso en docx, uso en prompt IA, uso en plantilla) generado durante la exploración previa a este diseño — referenciado en la sesión de Claude Code del 2026-08-08. Resumen de riesgo:

- **Seguros de ocultar sin tocar `app.py`** (ya huérfanos hoy — no llegan a ningún lado): toda la sección Evaluación Capilar (Step 8), "¿Trabaja actualmente?", "¿Con quién vive?", "Familiares en casa", "¿Cuenta con ayuda en casa?", "Tipo de apoyo recibido", 8 de 14 preguntas de intolerancias, "Frecuencia consumo dulces", "Cuántas comidas al día", "Grasas saludables que consume", "¿A qué hora del día?" (baño), "¿Utiliza medicamento para dormir?", "¿Trabaja turnos nocturnos?", "Andropausia", "Otros problemas piel".
- **Requieren tocar `_mapear_formulario` + docx**: prácticamente todos los campos "Quitar" de Datos Personales, Condición Actual, Alergias, Historial Estético (con fecha/zona), Objetivos, Estilo de Vida/Solar/Rutina.
- **Requieren tocar además `_datos_paciente()`** (afecta el prompt de la IA): nombre, edad, sexo, ocupación, horario laboral, act. laboral, estatura/peso, pielTipo/pielProblemas, rutina mañana/noche, productos, solar/SPF, actFisica, sueño, fuma, alcohol, condicionSistemica, condiciones, medicamentos, cirugías, alergias, contraindications, áreas faciales/corporales, prioridad, expectativas, satisfacción, historial estético, intolerancias, preferencias alimentarias, notas alimentación, número hijos, nivel estrés — de estos, revisar cuáles quedaron "Quitar" y limpiar su línea del f-string.
- **Requieren tocar `render_plan`/plantillas Jinja** solo si se elimina: nombre, edad, ocupación, fecha, estatura/peso (IMC), condicionSistemica, satisfacción — ninguno de estos está marcado "Quitar", así que las plantillas no requieren cambios.

## Fix 2026-06-19: Precio EXILIS Abdomen + Totales de planes en $\$0$

### 1. Precio EXILIS Abdomen

**Problema reportado:** El precio del tratamiento **EXILIS Abdomen** era incorrecto tanto en la lista pública como en el catálogo que consume la IA para generar planes.

| Ubicacion | Anterior | Corregido |
|-----------|----------|-----------|
| Pagina publica `/precios` | `$2,000.00` | `$1,000.00` |
| Catalogo del LLM (`SYS3` en `app.py:3279`) | `$2000` | `$1000` |

**Commits:**
- `a6a06d7` — Fix: precio EXILIS Abdomen 2000→1000 (pagina publica)
- `3f892e6` — Fix: precio EXILIS en catalogo LLM 2000→1000

**Despliegue:** Auto-deploy via Railway al hacer push a `main`.

---

### 2. Planes generados con inversion total `$0`

**Problema reportado:** Los planes personalizados generados por IA mostraban **$0** en el recuadro "Inversión Total del Plan" y solo traían **3 bimestres** en vez de **6**.

**Caso de ejemplo:** Plan de Ubaldo Joel Henriquez Rios (19-jun-2026) mostro:
- Bimestres 1, 2, 3 con inversiones correctas
- Pagina 7: bimestres 5-6 vacios
- Total anual: `$0`

**Causa raiz (3 problemas):**

1. **Campo `total_anual` ausente del ejemplo JSON del prompt.**
   El prompt de la fase 3/3 (`SYS3` en `app.py:~3354`) instruia al LLM: *"total bimestre = suma real inversiones. total_anual = suma bimestres"*, pero el **ejemplo JSON** que sirve de plantilla no incluia la clave `"total_anual"`. La IA (Claude) sigue el formato del ejemplo literalmente, por lo que omitia ese campo. En el renderer (`app.py:3981`) al hacer `p5.get('total_anual', 0)` obtenia `0`.

2. **Ejemplo JSON solo mostraba 3 bimestres.**
   La plantilla del prompt definia `bimestres` como un arreglo de 3 elementos. La IA copiaba ese patron y generaba solo 3 bimestres, no los 6 que corresponden a un plan de 12 meses.

3. **Logica `half` forzaba 4 bimestres en la pagina 6.**
   En `render_plan()` (`app.py:3963`):
   ```python
   half = max(4, len(bimestres) // 2 + len(bimestres) % 2)
   ```
   Con 3 bimestres generados, `max(4, 2)` = `4`. Esto colocaba los 3 bimestres en la pagina 6 (`bimestres[:4]`) y dejaba la pagina 7 (`bimestres[4:]`) **vacía**. El usuario veia el titulo "Bimestres 5-6" sin contenido.

**Correcciones aplicadas:**

| Archivo | Linea | Cambio |
|---------|-------|--------|
| `app.py` | `~3354` | Ejemplo JSON de `SYS3` ahora incluye **6 bimestres** y `"total_anual": 0000` |
| `app.py` | `3963` | `half` cambiado a `(len(bimestres) + 1) // 2` para dividir equitativamente sin forzar 4 |

**Commit:** `5d0f54d` — Fix: prompt pilar5 ahora incluye 6 bimestres + total_anual; half render sin forzar 4

**Validacion:** Proximo plan generado deberia mostrar:
- 6 bimestres consecutivos
- Totales por bimestre reales
- Total anual = suma real de los 6 bimestres (no $0)

---

## Estado general

- **Commit actual:** `26bbe55` (incluye autofill script adicional)
- **Deploy:** Railway, auto-deploy en push a `main`
- **URL produccion:** https://metodo.centrocarvajal.com
- **Repo:** `git@github.com:lsaijr/carvajal-metodo.git`

---

*Documento generado el 19 de junio de 2026.*
