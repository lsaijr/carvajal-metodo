# Registro de Correcciones — Centro Carvajal

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
