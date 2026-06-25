# Centro Carvajal — Método IA

## Catálogo de tratamientos

Archivo fuente: `catalogo_tratamientos.json`
- Contiene todos los tratamientos con problemas, zonas, precios, contraindicaciones, etc.
- Se sincroniza automáticamente con Cloudinary (`carvajal/catalogo_tratamientos.json`) al arrancar y al guardar.
- La IA lo consume desde `app.py` a través de `_cargar_catalogo()` + `_catalogo_a_texto()`.

## Editor del catálogo

Ruta online: `/catalogo`
- Página: `catalogo.html`
- Permite activar/desactivar tratamientos, editar precios, problemas, zonas, contraindicaciones, etc.
- Guarda en `/api/catalogo` POST → actualiza JSON local + Cloudinary.
- Acceso: contraseña `ADMIN_PASSWORD` (Railway/Render).

## Lista de precios pública

Ruta online: `/precios`
- Definida en `app.py` línea ~4895 (`def precios()`).
- HTML estático con la tabla de precios.
- No se actualiza automáticamente desde el catálogo; hay que editarla manualmente en `app.py`.

## Planes generados

Ruta online: `/planes`
- HTML embebido en `app.py` (`PLANES_HTML`, línea ~814).
- Lista planes guardados en Cloudinary (`carvajal/planes/`).
- Acceso: contraseña `ADMIN_PASSWORD`.

## Panel principal

Ruta online: `/panel`
- Archivo: `panel-carvajal.html`
- Links a formulario demo, subir Word, ver planes y catálogo.

## Autenticación

- Variable `ADMIN_PASSWORD` (Railway/Render) sirve para `/planes`, `/catalogo` y `/reporte-llm`.
- Fallback reportes: `reportes2026` si `ADMIN_PASSWORD` no está definida.
- Usuarios con email/contraseña se guardan en `carvajal/config/usuarios.json` en Cloudinary.

## Flujo de trabajo recomendado

1. Editar catálogo en `/catalogo` → guardar.
2. La IA usará el catálogo actualizado para nuevos planes.
3. Si se cambian precios, actualizar también la página `/precios` en `app.py`.
4. Ver planes generados en `/planes`.
