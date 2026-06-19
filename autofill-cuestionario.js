// ════════════════════════════════════════════════════════════
//  AUTOFILL — Cuestionario Carvajal (consola del navegador)
//  Copia todo este bloque, ábrelo en la consola (F12 → Consola)
//  con el formulario abierto, y pégalo. Presiona Enter.
// ════════════════════════════════════════════════════════════

(function() {
  'use strict';

  // ── 1. Helpers ────────────────────────────────────────────
  const $  = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));
  const sleep = (ms) => new Promise(r => setTimeout(r, ms));

  function setVal(id, val) {
    const el = document.getElementById(id);
    if (el) { el.value = val; el.dispatchEvent(new Event('input', {bubbles:true})); }
  }
  function clickRadio(name, labelText) {
    const items = $$(`input[name="${name}"]`);
    for (const item of items) {
      const lbl = item.closest('.radio-item');
      if (lbl && lbl.textContent.trim().toLowerCase().includes(labelText.toLowerCase())) {
        item.checked = true;
        lbl.classList.add('selected');
        item.dispatchEvent(new Event('change', {bubbles:true}));
        return;
      }
    }
  }
  function clickCheckbox(text) {
    for (const item of $$('.check-item')) {
      if (item.textContent.trim().toLowerCase().includes(text.toLowerCase())) {
        const cb = item.querySelector('input[type="checkbox"]');
        if (cb && !cb.checked) {
          cb.checked = true;
          item.classList.add('checked');
          cb.dispatchEvent(new Event('change', {bubbles:true}));
        }
      }
    }
  }
  function clickYN(rowText, answer) {
    for (const row of $$('.yn-row')) {
      if (row.querySelector('.yn-label')?.textContent.trim().toLowerCase().includes(rowText.toLowerCase())) {
        const btns = row.querySelectorAll('.yn-btn');
        const target = Array.from(btns).find(b => b.textContent.trim().toLowerCase() === answer.toLowerCase());
        if (target) target.click();
      }
    }
  }
  function clickScale(groupId, val) {
    const group = document.getElementById(groupId);
    if (!group) return;
    for (const btn of group.querySelectorAll('.scale-btn')) {
      if (btn.textContent.trim() === String(val)) { btn.click(); return; }
    }
  }
  function clickAlergia(idPrefix, answer) {
    const row = document.getElementById('arow-' + idPrefix);
    if (!row) return;
    const btns = row.querySelectorAll('.yn-btn');
    const target = Array.from(btns).find(b => b.textContent.trim().toLowerCase() === answer.toLowerCase());
    if (target) target.click();
  }
  function clickTratamiento(id, answer) {
    const row = document.getElementById('trat-row-' + id);
    if (!row) return;
    const btns = row.querySelectorAll('.yn-btn');
    const target = Array.from(btns).find(b => b.textContent.trim().toLowerCase() === answer.toLowerCase());
    if (target) target.click();
  }
  function clickConsent() {
    for (const item of $$('.consent-item')) {
      const cb = item.querySelector('input[type="checkbox"]');
      if (cb && !cb.checked) {
        cb.checked = true;
        item.classList.add('checked');
        cb.dispatchEvent(new Event('change', {bubbles:true}));
      }
    }
  }

  // ── 2. Datos de prueba ────────────────────────────────────
  const hoy = new Date().toISOString().split('T')[0];
  const data = {
    // Paso 1
    nombre: 'María Elena Torres',
    cedula: '8-987-654',
    direccion: 'Calle 50, Bella Vista, Panamá',
    edad: 34,
    fechanac: '1991-05-14',
    celular: '+507 6123 4567',
    email: 'maria.torres.ejemplo@gmail.com',
    ocupacion: 'Diseñadora gráfica',
    contNombre: 'Carlos Torres',
    contRelacion: 'Esposo',
    contTel: '+507 6123 9999',
    horarioOtro: '',
    familiares: 'Esposo y 1 hija de 6 años',

    // Paso 2
    estatura: 165,
    peso: 62,
    enfermedadDet: 'Hipotiroidismo diagnosticado en 2019, controlado con levotiroxina 75mcg.',
    medicamentos: 'Levotiroxina 75 mcg cada mañana en ayunas. Vitamina D3 2000 UI.',
    otrasCondiciones: 'Ninguna adicional.',
    horaDuerme: '22:30',
    horaDespierta: '06:30',

    // Paso 4
    fProteinasEvitar: 'Mariscos',
    fCarbosEvitar: '',
    fVerduras: 'Espinaca, brócoli, zanahoria, coliflor, lechuga, pepino, tomate, cebolla.',
    fVerdurasEvitar: 'Ninguna en particular.',
    fFrutas: 'Fresa, piña, banano, manzana, sandía, mango.',
    fGrasasEvitarPorque: 'Digestión lenta y sensación de pesadez.',
    fPostres: 'Chocolate oscuro, helado de vainilla ocasional.',
    fBebidasCuales: 'Coca-cola light 2-3 veces por semana.',
    fNotaAlim: 'Intento comer saludable pero a veces caigo en comida rápida por falta de tiempo.',

    // Paso 6
    fCirugiasDet: 'Cesárea en 2019 sin complicaciones.',
    fOtrosPiel: 'Rosácea leve en mejillas que se activa con el calor.',

    // Paso 9
    fPrioridad: 'Eliminar manchas solares en pómulos y frente, y mejorar la flacidez leve de la papada.',
    fExpectativas: 'Espero ver una piel más uniforme y luminosa en 3-4 meses. No busco perfección, solo mejorar lo que me incomoda al verme en el espejo.',

    // Paso 10
    fProtectorMarca: 'La Roche-Posay Anthelios',
    fSpf: 'SPF 50+',
    fProtectorHora: '7:15 am, antes de salir de casa',
    fRutinaManana: '1. Limpiador en gel La Roche-Posay, 2. Sérum vitamina C Vichy, 3. Hidratante CeraVe, 4. Protector solar La Roche-Posay.',
    fRutinaNoche: '1. Leche limpiadora Bioderma, 2. Tónico suave, 3. Retinol 0.3% La Roche-Posay (3 veces/semana), 4. Hidratante reparadora.',
    fProductos: 'Base maquillaje MAC Studio Fix, corrector NARS, rubor Benefit.',
    fAntecedentesDet: 'Padre con diabetes tipo 2 diagnosticada a los 55 años. Madre con hipotiroidismo.',
    fLaserDet: '',
    fComplicDet: '',
  };

  // ── 3. Función principal ──────────────────────────────────
  async function fillAll() {
    console.log('[autofill] Iniciando...');

    // === PASO 1 ===
    setVal('f-nombre', data.nombre);
    setVal('f-cedula', data.cedula);
    setVal('f-direccion', data.direccion);
    setVal('f-edad', data.edad);
    setVal('f-fechanac', data.fechanac);
    setVal('f-celular', data.celular);
    setVal('f-email', data.email);
    setVal('f-ocupacion', data.ocupacion);
    setVal('f-cont-nombre', data.contNombre);
    setVal('f-cont-relacion', data.contRelacion);
    setVal('f-cont-tel', data.contTel);
    setVal('f-familiares', data.familiares);
    setVal('f-horario-otro', data.horarioOtro);

    clickRadio('sexo', 'Femenino');
    clickRadio('trabaja', 'Sí');
    clickRadio('horario_laboral', 'Mañana');
    clickRadio('act_laboral', 'Sedentario');
    clickRadio('num_hijos', '1');
    clickCheckbox('Con pareja');
    clickCheckbox('Con hijos');
    clickCheckbox('Solo/a');          // marca también para que no quede vacío
    clickYN('Cuenta con ayuda en casa', 'No');
    clickCheckbox('Limpieza del hogar');
    clickRadio('como_conociste', 'Internet');

    // === PASO 2 ===
    setVal('f-estatura', data.estatura);
    setVal('f-peso', data.peso);
    clickRadio('enfermedad', 'Sí');
    setVal('f-enfermedad-det', data.enfermedadDet);

    // Hormonales (Sí/No)
    clickYN('Actualmente embarazada', 'No');
    clickYN('Periodo de lactancia', 'No');
    clickYN('Síndrome de ovario poliquístico', 'No');
    clickYN('Uso de anticonceptivos hormonales', 'Sí');
    clickYN('Menopausia', 'No');
    clickYN('Perimenopausia', 'No');
    clickYN('Andropausia', 'No');

    // Hábitos
    clickYN('Fuma', 'No');
    clickYN('Consume alcohol', 'Ocasionalmente');
    clickYN('Toma medicamentos', 'Sí');
    setVal('f-medicamentos', data.medicamentos);
    setVal('f-otras-condiciones', data.otrasCondiciones);

    // Intestinal
    clickYN('Vas al baño todos los días', 'Sí');
    clickRadio('banio_hora', 'Mañana');
    clickRadio('evacuacion', 'Normal');

    // Sueño
    clickRadio('horas_sueno', '7–9h');
    clickRadio('calidad_sueno', 'Profundo');
    setVal('f-hora-duerme', data.horaDuerme);
    setVal('f-hora-despierta', data.horaDespierta);
    clickYN('cansancio o somnolencia durante', 'No');
    clickYN('Utiliza medicamento o suplemento para dormir', 'No');
    clickYN('Trabaja en turnos nocturnos', 'No');

    // Estrés
    clickScale('scale-estres', 4);

    // === PASO 3 (Intolerancias) ===
    clickYN('hinchazón abdominal', 'Sí');
    clickYN('gases o flatulencias', 'Sí');
    clickYN('estreñimiento o diarrea', 'No');
    clickYN('cansancio o somnolencia después', 'Sí');
    clickYN('dolor de cabeza o migrañas', 'No');
    clickYN('Picazón, enrojecimiento o urticaria', 'No');
    clickYN('Congestión nasal o estornudos', 'No');
    clickYN('Inflamación en articulaciones', 'No');
    clickYN('Cambios de humor, ansiedad', 'No');
    clickYN('digestión es lenta o pesada', 'Sí');
    clickYN('Dificultad para bajar de peso', 'No');
    clickYN('Náuseas o malestar general', 'No');
    clickYN('Antecedentes familiares de intolerancias', 'No');
    clickYN('Síntomas al consumir lácteos', 'No');
    clickYN('Síntomas al consumir gluten', 'No');
    clickYN('Síntomas con alimentos procesados', 'No');

    // === PASO 4 (Alimentación) ===
    clickCheckbox('Pollo');
    clickCheckbox('Pescado');
    clickCheckbox('Huevos');
    clickCheckbox('Legumbres');
    setVal('f-proteinas-evitar', data.fProteinasEvitar);

    clickCheckbox('Arroz blanco');
    clickCheckbox('Avena');
    clickCheckbox('Pan');
    clickCheckbox('Papa');
    setVal('f-carbos-evitar', data.fCarbosEvitar);

    setVal('f-verduras', data.fVerduras);
    setVal('f-verduras-evitar', data.fVerdurasEvitar);
    setVal('f-frutas', data.fFrutas);

    clickCheckbox('Aguacate');
    clickCheckbox('Aceite de oliva');
    clickCheckbox('Nueces / Almendras');
    clickCheckbox('Semillas');

    clickCheckbox('Alimentos fritos');
    clickCheckbox('Aceites vegetales procesados');
    clickCheckbox('Grasas trans');
    setVal('f-grasas-evitar-porque', data.fGrasasEvitarPorque);

    setVal('f-postres', data.fPostres);
    clickRadio('dulces_frec', 'Ocasionalmente');
    clickRadio('comidas', '3');
    clickYN('Consume bebidas azucaradas', 'Sí');
    setVal('f-bebidas-cuales', data.fBebidasCuales);
    setVal('f-nota-alim', data.fNotaAlim);

    // === PASO 5 (Alergias) ===
    clickAlergia('alg_medicamentos', 'No');
    clickAlergia('alg_lidocaina', 'No');
    clickAlergia('alg_penicilina', 'No');
    clickAlergia('alg_yodo', 'No');
    clickAlergia('alg_aines', 'No');
    clickAlergia('alg_alimentos', 'No');
    clickAlergia('alg_mariscos', 'Sí');
    setVal('asint-alg_mariscos', 'Urticaria leve y comezón en brazos.');
    clickAlergia('alg_latex', 'No');
    clickAlergia('alg_aloe', 'No');
    clickAlergia('alg_fragancias', 'No');
    clickAlergia('alg_otro', 'No');

    // === PASO 6 (Piel) ===
    clickYN('Se ha realizado alguna cirugía', 'Sí');
    setVal('f-cirugias-det', data.fCirugiasDet);
    clickRadio('tipo_piel', 'Mixta');
    clickCheckbox('Poros dilatados');
    clickCheckbox('Brillo excesivo');
    clickCheckbox('Manchas solares');
    clickCheckbox('Melasma');
    clickCheckbox('Marcas post-acné');
    clickCheckbox('Pérdida de luminosidad');
    clickCheckbox('Líneas finas');
    clickCheckbox('Ardor');         // sensibilidad
    setVal('f-otros-piel', data.fOtrosPiel);

    // === PASO 8 (Capilar) ===
    clickRadio('caida_tiempo', 'No tengo caída');
    clickRadio('caida_tipo', 'No aplica');
    clickCheckbox('Ninguno');       // síntomas capilares
    clickCheckbox('Ninguno');       // factores recientes (puede marcar varios)
    clickYN('Antecedentes familiares de alopecia', 'No');
    clickYN('Has usado tratamientos para la caída', 'No');
    clickYN('Deseas reducir o eliminar vello', 'Sí');
    clickCheckbox('Axilas');
    clickCheckbox('Piernas');
    clickCheckbox('Facial');
    clickCheckbox('Cera');
    clickCheckbox('Afeitado');
    clickYN('Has notado aumento reciente de vello', 'No');
    clickYN('Cambios hormonales recientes', 'No');
    clickCheckbox('Ninguna');       // reacciones depilación

    // === PASO 9 (Objetivos) ===
    clickYN('Ha recibido tratamientos estéticos anteriormente', 'No');
    clickTratamiento('botox', 'No');
    clickTratamiento('rellenos', 'No');
    clickTratamiento('hilos', 'No');
    clickTratamiento('peeling', 'No');
    clickTratamiento('laser', 'No');
    clickTratamiento('microblading', 'No');
    clickTratamiento('mesoterapia', 'No');
    clickTratamiento('radiofrecuencia', 'No');
    clickTratamiento('criolipolisis', 'No');
    clickTratamiento('otro_estetico', 'No');
    clickYN('Actualmente está en tratamiento con láser', 'No');
    clickYN('Ha tenido complicaciones con algún tratamiento', 'No');

    clickCheckbox('Manchas');
    clickCheckbox('Flacidez facial');
    clickCheckbox('Textura de la piel');
    clickCheckbox('Grasa localizada');
    clickCheckbox('Celulitis');
    setVal('f-prioridad', data.fPrioridad);
    setVal('f-expectativas', data.fExpectativas);
    clickScale('scale-satisfaccion', 5);
    clickYN('Entiende que pueden necesitarse múltiples sesiones', 'Sí');

    // === PASO 10 (Estilo de vida) ===
    clickRadio('sol', 'Moderada');
    clickYN('Usa protector solar diariamente', 'Sí');
    setVal('f-protector-marca', data.fProtectorMarca);
    setVal('f-spf', data.fSpf);
    setVal('f-protector-hora', data.fProtectorHora);
    clickRadio('reaplica_solar', 'No');
    clickYN('Realiza rutina diaria de cuidado facial', 'Sí');
    setVal('f-rutina-manana', data.fRutinaManana);
    setVal('f-rutina-noche', data.fRutinaNoche);
    clickCheckbox('Limpieza facial diaria');
    clickCheckbox('Hidratación');
    clickCheckbox('Retinol o ácidos');
    setVal('f-productos', data.fProductos);
    clickRadio('act_fisica', 'Ligero');
    clickYN('En su familia hay historia de alguna enfermedad', 'No');
    clickYN('Tienes alergias a medicamentos o productos tópicos', 'No');
    clickYN('Has tenido infecciones cutáneas', 'No');
    clickYN('Tienes marcapasos, implantes', 'No');
    clickRadio('antecedentes_fam', 'Sí');
    setVal('f-antecedentes-det', data.fAntecedentesDet);

    // === PASO 11 (Consentimiento + fecha) ===
    clickConsent();
    setVal('fecha-envio', hoy);

    console.log('[autofill] ✅ Formulario llenado. Revisa cada paso antes de enviar.');
    console.log('[autofill] Puedes avanzar paso a paso con el botón Continuar, o ir al paso 11 y presionar Enviar.');
  }

  fillAll();
})();
