# Autofill Cuestionario Carvajal

## Uso rápido (modo consola)

1. Abre el cuestionario en el navegador: `https://metodo.centrocarvajal.com`
2. Abre la consola del desarrollador: **F12** → pestaña **Consola**
3. Copia TODO el contenido de `autofill-cuestionario.js` y pégalo en la consola
4. Presiona **Enter**
5. El formulario se llenará automáticamente con datos de prueba
6. Revisa cada paso y presiona **Continuar** hasta llegar al paso 11 → **Enviar**

## Datos de prueba incluidos
- Paciente ficticia: María Elena Torres, 34 años, diseñadora gráfica
- Condiciones: hipotiroidismo controlado, hipersensibilidad al marisco
- Piel mixta con manchas solares y melasma
- Objetivo: eliminar manchas y mejorar flacidez leve de papada
- Historial estético previo: ninguno

## Personalizar
Edita el objeto `data` dentro del script para cambiar nombres, valores numéricos o textos libres.

## Modo bookmarklet (barra de favoritos)
Si prefieres un botón en la barra de favoritos:
1. Copia el contenido de `bookmarklet-cuestionario.js`
2. Crea un nuevo favorito en el navegador
3. En la URL del favorito pega el código que empieza con `javascript:(function(){...`
4. Cuando estés en el formulario, haz clic en el favorito y se autollenará
