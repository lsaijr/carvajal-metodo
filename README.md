# Centro Carvajal — Método IA

## Git / Despliegue (Railway)

- Repo local real de trabajo: `github-repo/` (carpeta hermana, no la raíz del proyecto en Finder).
- Remote: `git@github.com:lsaijr/carvajal-metodo.git` (SSH, auth ya configurada — `ssh -T git@github.com` responde `Hi lsaijr!`).
- Branch: `main`. Push directo a `main` funciona sin pasos extra.
- **Despliegue: Railway** (enlazado a este repo GitHub, deploy automático en push a `main`). No hay `railway.json`/`railway.toml` en el repo — Railway detecta el stack solo (Nixpacks: Python/Flask + `requirements.txt`). `render.yaml` en el repo es config vieja de Render, ya no se usa para desplegar pero documenta las env vars requeridas.
- Variables de entorno (configuradas en Railway, no en el repo): `CLAUDE_KEY`, `GEMINI_KEY`, `GROQ_KEY`, `RESEND_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `MAIL_TO`, `MAIL_FROM`, `MAIL_CC`, `BASE_URL`, `ADMIN_PASSWORD`.
- Flujo normal: editar en `github-repo/`, commit, `git push origin main` → Railway redespliega solo.

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
- Acceso: contraseña `ADMIN_PASSWORD` (env var en Railway).

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

- Variable `ADMIN_PASSWORD` (env var en Railway) sirve para `/planes`, `/catalogo` y `/reporte-llm`.
- Fallback reportes: `reportes2026` si `ADMIN_PASSWORD` no está definida.
- Usuarios con email/contraseña se guardan en `carvajal/config/usuarios.json` en Cloudinary.

## Flujo de trabajo recomendado

1. Editar catálogo en `/catalogo` → guardar.
2. La IA usará el catálogo actualizado para nuevos planes.
3. Si se cambian precios, actualizar también la página `/precios` en `app.py`.
4. Ver planes generados en `/planes`.
