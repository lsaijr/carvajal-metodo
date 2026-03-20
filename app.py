import os, json, uuid, threading, calendar
from datetime import date, datetime
from flask import Flask, request, jsonify, render_template_string, send_from_directory
import requests as req
import zipfile, re, html as htmllib

app = Flask(__name__)

# ── Config desde variables de entorno ────────────────────────
CLAUDE_KEY  = os.environ.get('CLAUDE_KEY', '')
RESEND_KEY  = os.environ.get('RESEND_KEY', '')
MAIL_TO     = os.environ.get('MAIL_TO', 'isai.josue@gmail.com')
MAIL_FROM   = os.environ.get('MAIL_FROM', 'envios@centrocarvajal.com')
PLANES_DIR  = os.path.join(os.path.dirname(__file__), 'planes_generados')
os.makedirs(PLANES_DIR, exist_ok=True)

# ── Jobs en memoria ───────────────────────────────────────────
jobs = {}  # jobId -> {'status': ..., 'msg': ..., 'html_url': ...}

# ════════════════════════════════════════════════════════════
# RUTAS
# ════════════════════════════════════════════════════════════

@app.route('/', methods=['GET'])
def index():
    with open(os.path.join(os.path.dirname(__file__), 'subir_word.html'), encoding='utf-8') as f:
        return f.read()

@app.route('/planes_generados/<path:filename>')
def serve_plan(filename):
    return send_from_directory(PLANES_DIR, filename)

@app.route('/status')
def status():
    job_id = request.args.get('job', '')
    job = jobs.get(job_id, {'status': 'working', 'msg': 'Procesando...'})
    return jsonify(job)

@app.route('/upload', methods=['POST'])
def upload():
    if 'docx' not in request.files:
        return jsonify({'error': 'No se recibio archivo'}), 400

    f = request.files['docx']
    tmp_path = f'/tmp/carvajal_{uuid.uuid4().hex}.docx'
    f.save(tmp_path)

    texto = leer_docx(tmp_path)
    os.unlink(tmp_path)

    if not texto:
        return jsonify({'error': 'No se pudo leer el archivo .docx'}), 400

    data, faltantes = parsear_cuestionario(texto)
    if not data.get('nombre'):
        return jsonify({'error': 'No se encontro nombre_completo en el documento'}), 400

    job_id = uuid.uuid4().hex[:16]
    jobs[job_id] = {'status': 'working', 'msg': 'Iniciando generacion del plan...'}

    # Lanzar en background
    t = threading.Thread(target=worker, args=(job_id, data, faltantes), daemon=True)
    t.start()

    return jsonify({'jobId': job_id, 'nombre': data['nombre']})


# ════════════════════════════════════════════════════════════
# WORKER
# ════════════════════════════════════════════════════════════

def worker(job_id, data, faltantes):
    try:
        jobs[job_id] = {'status': 'working', 'msg': 'Generando plan con IA (puede tomar 1-2 min)...'}

        plan_json = generar_plan_ia(data)
        if 'error' in plan_json:
            jobs[job_id] = {'status': 'error', 'msg': plan_json['error']}
            return

        jobs[job_id] = {'status': 'working', 'msg': 'Construyendo HTML del plan...'}
        html = render_plan(plan_json, data)

        nombre     = data.get('nombre', 'Paciente')
        html_name  = 'Plan_' + re.sub(r'[^a-zA-Z0-9]', '_', nombre) + '_' + datetime.now().strftime('%Y%m%d') + '.html'
        html_path  = os.path.join(PLANES_DIR, html_name)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)

        base_url = os.environ.get('BASE_URL', 'https://metodo.centrocarvajal.com')
        html_url = f'{base_url}/planes_generados/{html_name}'

        jobs[job_id] = {'status': 'working', 'msg': 'Enviando correos...'}
        fecha_hoy = datetime.now().strftime('%d/%m/%Y a las %H:%M')

        # Correo 1: formulario
        enviar_resend(
            f'Nuevo Cuestionario - {nombre} ({fecha_hoy})',
            email_formulario(data, faltantes),
            MAIL_TO
        )
        # Correo 2: plan
        enviar_resend(
            f'Plan IA - {nombre} ({fecha_hoy})',
            email_plan(nombre, html_url, datetime.now().strftime('%d/%m/%Y')),
            'isai.josue@gmail.com',
            adjunto_path=html_path,
            adjunto_name=html_name
        )

        jobs[job_id] = {
            'status'   : 'done',
            'nombre'   : nombre,
            'html_url' : html_url,
            'html_name': html_name,
            'faltantes': faltantes,
        }

    except Exception as e:
        jobs[job_id] = {'status': 'error', 'msg': str(e)}


# ════════════════════════════════════════════════════════════
# LEER DOCX
# ════════════════════════════════════════════════════════════

def leer_docx(path):
    try:
        with zipfile.ZipFile(path) as z:
            xml = z.read('word/document.xml').decode('utf-8')
        texto = re.sub(r'</w:p>', '\n', xml)
        texto = re.sub(r'</w:tc>', '\t', texto)
        texto = re.sub(r'<[^>]+>', '', texto)
        texto = htmllib.unescape(texto)
        texto = re.sub(r'[ ]+', ' ', texto)
        lineas = [l.strip() for l in texto.split('\n') if l.strip()]
        pares = []
        for i in range(0, len(lineas) - 1, 2):
            key = lineas[i].lower().strip()
            val = lineas[i + 1].strip()
            if re.match(r'^[a-z][a-z0-9_]+$', key) and val:
                pares.append(f'{key}\t{val}')
        return '\n'.join(pares)
    except Exception as e:
        print(f'leer_docx error: {e}')
        return None


# ════════════════════════════════════════════════════════════
# PARSEAR CUESTIONARIO
# ════════════════════════════════════════════════════════════

def parsear_cuestionario(texto):
    raw = {}
    for linea in texto.split('\n'):
        linea = linea.strip()
        if not linea: continue
        if '\t' in linea:
            parts = linea.split('\t', 1)
            key, val = parts[0], parts[1]
        else:
            m = re.match(r'^([a-z][a-z0-9_]+)\s+(.+)$', linea, re.I)
            if m: key, val = m.group(1), m.group(2)
            else: continue
        key, val = key.lower().strip(), val.strip()
        if key and val: raw[key] = val

    def v(k):
        val = raw.get(k)
        if not val or val == '0' or val.lower() in ['ninguna','ninguno','aun no','n/a','nada']:
            return None
        return val

    def si(k):
        return raw.get(k, 'NO').upper() in ['SI', 'SÍ', 'S', 'YES']

    faltantes = []
    for campo, label in [('peso','Peso'),('altura','Altura'),('piel_tipo','Tipo de piel'),
                          ('prioridad_principal','Prioridad principal'),('satisfaccion','Satisfaccion (1-10)'),
                          ('expectativas','Expectativas'),('exposicion_solar','Exposicion solar')]:
        if not raw.get(campo) or raw.get(campo) == '0':
            faltantes.append(label)

    historial = []
    for k, l in [('botox','Botox'),('rellenos','Rellenos'),('hilos','Hilos PDO'),('peeling','Peeling'),
                 ('laser','Laser'),('microblading','Microblading'),('radiofrecuencia','Radiofrecuencia')]:
        if si('tratamiento_' + k): historial.append(l)

    contra = {}
    for c, l in [('embarazada','Embarazo'),('lactancia','Lactancia'),('anticonceptivos','Anticonceptivos'),
                 ('sop','SOP'),('menopausia','Menopausia'),('fuma','Tabaquismo'),
                 ('alergia_lidocaina','Alergia lidocaina'),('alergia_penicilina','Alergia penicilina'),
                 ('alergia_yodo','Alergia yodo'),('alergia_aines','Alergia AINEs'),
                 ('alergia_latex','Alergia latex')]:
        contra[l] = 'Si' if si(c) else 'No'

    sintomas = []
    for c, l in [('hinchazon_abdominal','Hinchazon'),('gases_flatulencias','Gases'),
                 ('estrenimiento_diarrea','Estrenimiento'),('cansancio_comidas','Cansancio tras comer'),
                 ('digestion_lenta','Digestion lenta'),('nauseas_malestar','Nauseas')]:
        if si(c): sintomas.append(l)

    intol = []
    if si('sintomas_lacteos'):    intol.append('Lacteos')
    if si('sintomas_gluten'):     intol.append('Gluten')
    if si('sintomas_procesados'): intol.append('Procesados')

    faciales, corporales = [], []
    if raw.get('area_flacidez_facial'): faciales.append('Flacidez facial')
    if raw.get('area_grasa'):           corporales.append('Grasa localizada')
    if raw.get('area_arrugas'):         faciales.append('Arrugas')
    if raw.get('area_manchas'):         faciales.append('Manchas')
    if raw.get('area_ojeras'):          faciales.append('Ojeras')
    if raw.get('area_celulitis'):       corporales.append('Celulitis')
    prio = (v('prioridad_principal') or '').lower()
    if 'rostro' in prio or 'cara' in prio: faciales.append('Rejuvenecimiento facial')
    if 'cabello' in prio or 'pelo' in prio: faciales.append('Caida de cabello')
    if 'mancha' in prio or 'melasma' in prio: faciales.append('Manchas')
    faciales   = list(dict.fromkeys(faciales))
    corporales = list(dict.fromkeys(corporales))

    ale_list = []
    for c, l in [('alergia_lidocaina','Lidocaina'),('alergia_penicilina','Penicilina'),
                 ('alergia_yodo','Yodo'),('alergia_aines','AINEs'),('alergia_latex','Latex'),
                 ('alergia_aloe','Aloe'),('alergia_fragancias','Fragancias')]:
        if si(c): ale_list.append(l)
    if si('alergia_medicamentos'): ale_list.append(v('medicamentos_cuales') or 'Medicamentos')

    est = v('altura') or v('talla') or v('estatura')
    pes = v('peso')
    imc = 'No registrado'
    if est and pes:
        try: imc = f'{float(pes) / (float(est)/100)**2:.1f}'
        except: pass

    data = {
        'nombre':              v('nombre_completo') or '',
        'edad':                v('edad') or '',
        'sexo':                v('sexo') or '',
        'ocupacion':           v('ocupacion') or v('profesion_trabajo') or '',
        'actLaboral':          v('nivel_actividad_laboral') or '',
        'horarioLaboral':      v('horario_laboral') or '',
        'email':               v('email') or '',
        'fecha':               datetime.now().strftime('%d de %B, %Y'),
        'estatura':            est,
        'peso':                pes,
        'imc':                 imc,
        'pielTipo':            v('piel_tipo') or v('tipo_piel') or '',
        'pielProblemas':       faciales,
        'rutinaFacial':        (v('rutina_manana') or '') + ' | ' + (v('rutina_noche') or '') if si('rutina_diaria_cuidado') else 'No tiene rutina facial',
        'rutinaManana':        v('rutina_manana') or '',
        'rutinaNoche':         v('rutina_noche') or '',
        'productosFrecuentes': v('productos_cosmeticos_frecuentes') or '',
        'solar':               v('exposicion_solar') or '',
        'spf':                 (v('protector_fps') or '') + ' ' + (v('protector_marca') or ''),
        'actFisica':           v('actividad_fisica') or '',
        'sueno':               (v('horas_sueno') or '') + ' horas ' + (v('calidad_sueno') or ''),
        'horaDespierta':       v('hora_levanta') or '',
        'horaDuerme':          v('hora_acuesta') or '',
        'cansancioDia':        'Si' if si('cansancio_dia') else 'No',
        'fuma':                ('Si - ' + (v('fuma_cantidad') or '')) if si('fuma') else 'No',
        'alcohol':             'Si' if si('alcohol') else 'No',
        'condicionSistemica':  (v('enfermedad_detalle') or 'Si') if si('sufre_enfermedad') else 'Sin enfermedades',
        'condiciones':         v('otras_condiciones') or '',
        'medicamentos':        v('medicamento_cual') or '',
        'cirugias':            (v('cirugias_detalle') or 'Si') if si('cirugias') else 'Ninguna',
        'antecedentesFam':     (v('antecedentes_detalle') or 'Si') if si('antecedentes_familiares') else 'Ninguno',
        'alergias':            ', '.join(ale_list) if ale_list else 'Ninguna',
        'contraindications':   contra,
        'areasFaciales':       faciales,
        'areasCorporales':     corporales,
        'prioridad':           v('prioridad_principal') or '',
        'expectativas':        v('expectativas') or '',
        'satisfaccion':        v('satisfaccion') or '',
        'historialEstetico':   list(dict.fromkeys(historial)),
        'laserActivo':         'Si' if si('laser_actual') else 'No',
        'intolerancias':       intol,
        'sintomasDigestivos':  sintomas,
        'proteinas':           ', '.join(filter(None, [v('proteina_pollo'), v('proteinas_otras')])),
        'carbohidratos':       v('carb_arroz_blanco') or '',
        'verduras':            v('verduras_consume') or '',
        'frutas':              v('carb_frutas') or '',
        'alimentosEvitar':     ', '.join(filter(None, [v('proteinas_evitar'), v('carbohidratos_evitar'), v('verduras_evitar')])),
        'postres':             v('postres_favoritos') or '',
        'bebidas':             (v('bebidas_azucaradas_cuales') or 'Si') if si('bebidas_azucaradas') else 'No',
        'notasAlimentacion':   v('observaciones_alimentarias') or '',
        'notasStaff':          '',
    }
    return data, faltantes


# ════════════════════════════════════════════════════════════
# GENERAR PLAN CON CLAUDE API
# ════════════════════════════════════════════════════════════

def generar_plan_ia(d):
    prompt_path = os.path.join(os.path.dirname(__file__), 'prompt_carvajal.txt')
    with open(prompt_path, encoding='utf-8') as f:
        sys_prompt = f.read()

    est = d.get('estatura', '')
    pes = d.get('peso', '')
    imc = d.get('imc', 'No registrado')

    contra_activas = [k for k, v in d.get('contraindications', {}).items() if v == 'Si']
    contra_txt = 'CONTRAINDICACIONES ACTIVAS: ' + ', '.join(contra_activas) if contra_activas else 'Sin contraindicaciones activas.'

    usr = f"""DATOS DEL PACIENTE:
Nombre: {d['nombre']} | Edad: {d['edad']} | Sexo: {d['sexo']}
Ocupacion: {d['ocupacion']} | Horario: {d['horarioLaboral']} | Act.laboral: {d['actLaboral']}
Fecha evaluacion: {d['fecha']}
Estatura: {est}cm | Peso: {pes}kg | IMC: {imc}

PIEL: {d['pielTipo']} | Problemas: {', '.join(d['pielProblemas'])}
Rutina manana: {d['rutinaManana']} | Noche: {d['rutinaNoche']}
Productos: {d['productosFrecuentes']} | Solar: {d['solar']} | SPF: {d['spf']}

HABITOS: Act.fisica: {d['actFisica']} | Sueno: {d['sueno']}
Fuma: {d['fuma']} | Alcohol: {d['alcohol']}

SALUD: {contra_txt}
Condicion sistemica: {d['condicionSistemica']}
Condiciones: {d['condiciones']}
Medicamentos: {d['medicamentos']}
Cirugias: {d['cirugias']}
Alergias: {d['alergias']}

OBJETIVOS: Faciales: {', '.join(d['areasFaciales'])} | Corporales: {', '.join(d['areasCorporales'])}
Prioridad (palabras del paciente): "{d['prioridad']}"
Expectativas: {d['expectativas']} | Satisfaccion: {d['satisfaccion']}/10
Historial estetico: {', '.join(d['historialEstetico']) or 'Ninguno'}

ALIMENTACION:
Intolerancias: {', '.join(d['intolerancias']) or 'Ninguna'}
Proteinas: {d['proteinas']} | Carbos: {d['carbohidratos']}
Verduras: {d['verduras']} | Frutas: {d['frutas']}
Evitar: {d['alimentosEvitar']}
Notas: {d['notasAlimentacion']}"""

    resp = req.post(
        'https://api.anthropic.com/v1/messages',
        headers={
            'Content-Type': 'application/json',
            'x-api-key': CLAUDE_KEY,
            'anthropic-version': '2023-06-01',
        },
        json={
            'model': 'claude-opus-4-6',
            'max_tokens': 8000,
            'system': sys_prompt,
            'messages': [{'role': 'user', 'content': usr}],
        },
        timeout=180
    )

    if resp.status_code != 200:
        return {'error': f'Error API Claude ({resp.status_code}): {resp.text[:300]}'}

    txt = resp.json()['content'][0]['text']
    txt = re.sub(r'^```json\s*', '', txt.strip())
    txt = re.sub(r'^```\s*', '', txt)
    txt = re.sub(r'```\s*$', '', txt).strip()

    try:
        return json.loads(txt)
    except Exception as e:
        return {'error': f'JSON invalido de Claude: {str(e)[:200]}'}


# ════════════════════════════════════════════════════════════
# RENDER PLAN — llenar plantilla HTML
# ════════════════════════════════════════════════════════════

def render_plan(j, d):
    tpl_path = os.path.join(os.path.dirname(__file__), 'plantilla_plan.html')
    with open(tpl_path, encoding='utf-8') as f:
        tpl = f.read()

    def esc(s): return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('"','&quot;')

    def make_quote(txt):
        return f'<div class="quote"><svg viewBox="0 0 24 24"><path d="M3 21c3 0 7-1 7-8V5c0-1.25-.756-2.017-2-2H4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2 1 0 1 0 1 1v1c0 1-1 2-2 2s-1 .008-1 1.031V20c0 1 0 1 1 1z"/><path d="M15 21c3 0 7-1 7-8V5c0-1.25-.757-2.017-2-2h-4c-1.25 0-2 .75-2 1.972V11c0 1.25.75 2 2 2h.75c0 2.25.25 4-2.75 4v3c0 1 0 1 1 1z"/></svg><p>{esc(txt)}</p></div>'

    def make_tips(tips):
        return ''.join(f'<div class="tip"><svg viewBox="0 0 24 24" style="stroke:var(--gold);fill:none;stroke-width:2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><p>{esc(t.get("texto",""))}</p></div>' for t in tips)

    def pos_q(pos, q, target): return q if pos == target else ''

    yr = date.today().year
    nombre = d.get('nombre', '')
    imc = d.get('imc', 'No registrado')

    # Portada
    pilares_html = ''.join(
        f'<div class="pilar-mini"><div class="pm-icon">{p["emoji"]}</div><div><h4><strong>Pilar {p["num"]}: {esc(p["titulo"])}</strong></h4><p>{esc(p["descripcion"])}</p></div></div>'
        for p in j.get('portada', {}).get('pilares_resumen', [])
    )

    # Diagnostico
    badge_map = {'warning':'<span class="a-badge warning">⚠ Atención</span> ','critical':'<span class="a-badge critical">✕ Crítico</span> ','normal':''}
    diag_html = ''.join(
        f'<tr><td class="diag-left">{badge_map.get(f.get("alerta","normal"),"")}{esc(f["area"])}</td><td><strong>{esc(f["estado"])}</strong><br><span style="color:#666;font-size:0.85rem">{esc(f["hallazgos"])}</span></td></tr>'
        for f in j.get('diagnostico', {}).get('filas', [])
    )

    # Rutina
    tag_map = {'Nutricion':'tag-n','Sueno':'tag-s','Actividad':'tag-a','Mental':'tag-m','Estetico':'tag-e','Salud':'tag-h','Trabajo':'tag-n'}
    rutina_html = ''.join(
        f'<tr><td style="font-weight:600;color:var(--gold)">{esc(r["hora"])}</td><td style="text-align:center"><input type="checkbox"></td><td>{esc(r["actividad"])}</td><td><span class="pilar-tag {tag_map.get(r["pilar"],"tag-n")}">{esc(r["pilar"])}</span></td></tr>'
        for r in j.get('rutina', {}).get('items', [])
    )

    # Calendario
    cal_html = generar_calendario()

    # Helper pilar
    def build_pilar(p):
        q = make_quote(p.get('frase_motivacional', ''))
        pos = p.get('frase_posicion', 'medio')
        tips = make_tips(p.get('tips', []))
        return q, pos, tips

    # Pilar 1
    p1 = j.get('pilar1', {})
    p1q, p1pos, p1tips = build_pilar(p1)
    p1_perm = ''.join(f'<li><svg viewBox="0 0 24 24" style="stroke:var(--green);fill:none;stroke-width:2.5"><polyline points="20 6 9 17 4 12"/></svg><span>{esc(i)}</span></li>' for i in p1.get('permitidos', []))
    p1_evit = ''.join(f'<li><svg viewBox="0 0 24 24" style="stroke:#b71c1c;fill:none;stroke-width:2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg><span>{esc(i)}</span></li>' for i in p1.get('evitar', []))
    p1_menu = ''.join(f'<tr><td style="font-weight:600">{esc(m["dia"])}</td><td>{esc(m["desayuno"])}</td><td>{esc(m["almuerzo"])}</td><td>{esc(m["cena"])}</td><td>{esc(m["snack"])}</td></tr>' for m in p1.get('menu', []))
    p1_compras = ''.join(f'<div class="compra-cat"><h5>{c["emoji"]} {esc(c["categoria"])}</h5><ul>{"".join(f"<li>{esc(i)}</li>" for i in c["items"])}</ul></div>' for c in p1.get('compras', []))
    p1_supl = ''
    if p1.get('suplementacion'):
        items = ''.join(f'<p style="font-size:0.83rem;color:#555;padding:4px 0;border-bottom:1px solid rgba(0,0,0,0.05)">{esc(s)}</p>' for s in p1['suplementacion'])
        p1_supl = f'<div class="suppl" style="margin-top:20px"><h4 style="font-family:Cormorant Garamond,serif;font-size:1.1rem;margin-bottom:10px">Suplementación Sugerida</h4>{items}<p style="font-size:0.75rem;color:#999;margin-top:8px">* Bajo supervisión médica.</p></div>'

    # Pilar 2
    p2 = j.get('pilar2', {})
    p2q, p2pos, p2tips = build_pilar(p2)

    # Pilar 3
    p3 = j.get('pilar3', {})
    p3q, p3pos, p3tips = build_pilar(p3)
    p3_tec = ''.join(f'<li style="display:flex;gap:10px;align-items:flex-start;padding:8px 0;border-bottom:1px solid rgba(0,0,0,0.05)"><span style="background:var(--gold-light);color:var(--gold);border-radius:50%;min-width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700">{i+1}</span><span style="font-size:0.87rem">{esc(t)}</span></li>' for i, t in enumerate(p3.get('tecnicas', [])))

    # Pilar 4
    p4 = j.get('pilar4', {})
    p4q, p4pos, p4tips = build_pilar(p4)
    p4_proto = ''.join(f'<li style="display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid rgba(0,0,0,0.05)"><span style="background:var(--gold-light);color:var(--gold);border-radius:50%;min-width:22px;height:22px;display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700">{i+1}</span><span style="font-size:0.87rem">{esc(s)}</span></li>' for i, s in enumerate(p4.get('protocolo', [])))
    p4_reglas = ''.join(f'<li style="display:flex;gap:10px;align-items:flex-start;padding:7px 0;border-bottom:1px solid rgba(0,0,0,0.05)"><svg viewBox="0 0 24 24" style="width:16px;height:16px;stroke:#b71c1c;fill:none;stroke-width:2;flex-shrink:0;margin-top:2px"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg><span style="font-size:0.87rem">{esc(r)}</span></li>' for r in p4.get('reglas', []))

    # Pilar 5
    p5 = j.get('pilar5', {})
    p5q, p5pos, p5tips = build_pilar(p5)
    p5_bim = ''
    for bim in p5.get('bimestres', []):
        rows = ''.join(f'<tr><td><strong>{esc(t["nombre"])}</strong></td><td>{esc(t["sesiones"])}</td><td><strong>{esc(t["inversion"])}</strong></td><td>{esc(t["beneficio"])}</td></tr>' for t in bim.get('tratamientos', []))
        total = bim.get('total', 0)
        p5_bim += f'<div class="bim"><div class="bim-hdr">{esc(bim["periodo"])} · {esc(bim["titulo"])}</div><div class="bim-body"><table><thead><tr><th>Tratamiento</th><th>Sesiones</th><th>Inversión</th><th>Beneficio</th></tr></thead><tbody>{rows}</tbody></table><div class="bim-total">💰 Inversión Bimestre: ${total:,}</div></div></div>'

    p5_am = ''.join(f'<div class="rstep"><div class="snum">{s["paso"]}</div><div><div class="prod">{esc(s["producto"])}</div><div class="desc">{esc(s["descripcion"])}</div></div></div>' for s in p5.get('rutina_am', []))
    p5_pm = ''.join(f'<div class="rstep"><div class="snum">{s["paso"]}</div><div><div class="prod">{esc(s["producto"])}</div><div class="desc">{esc(s["descripcion"])}</div></div></div>' for s in p5.get('rutina_pm', []))

    notas = p5.get('notas_criticas', [])
    p5_notas = ''
    if notas:
        items = ''.join(f'<p style="font-size:0.83rem;padding:3px 0;border-bottom:1px solid rgba(0,0,0,0.05)">{esc(n)}</p>' for n in notas)
        p5_notas = f'<div style="background:#fff8e8;border:1px dashed rgba(184,147,90,0.5);border-radius:var(--radius);padding:16px 20px;margin:20px 0"><strong style="color:var(--gold);font-size:0.78rem;text-transform:uppercase;letter-spacing:1px;display:block;margin-bottom:8px">Notas Críticas</strong>{items}</div>'

    total_anual = p5.get('total_anual', 0)

    # Compromiso
    comp = j.get('compromiso', {})
    comp_res = ''.join(f'<div class="result-card"><div class="icon">{esc(r["icono"])}</div><p>{esc(r["texto"])}</p></div>' for r in comp.get('resultados', []))
    comp_pasos = ''.join(f'<div class="chk-item"><svg viewBox="0 0 24 24" style="width:18px;height:18px;stroke:var(--gold);fill:none;stroke-width:2;flex-shrink:0;margin-top:2px"><polyline points="9 11 12 14 22 4"/><path d="M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"/></svg><span>{esc(p)}</span></div>' for p in comp.get('proximos_pasos', []))

    # Portada emojis
    pr = j.get('portada', {}).get('pilares_resumen', [{}]*5)
    get_emoji = lambda i: pr[i]['emoji'] if i < len(pr) else ['🥗','🏃','🧠','😴','✨'][i]

    replacements = {
        '{{NOMBRE}}': esc(nombre), '{{NOMBRE_COMPLETO}}': esc(nombre),
        '{{EDAD}}': esc(d.get('edad','')), '{{OCUPACION}}': esc(d.get('ocupacion','')),
        '{{FECHA}}': esc(d.get('fecha','')), '{{IMC}}': esc(imc), '{{YEAR}}': str(yr),
        '{{INTRO}}': esc(j.get('portada',{}).get('intro','')),
        '{{TITULO_PILARES}}': esc(j.get('portada',{}).get('titulo_pilares','')),
        '{{PILARES_RESUMEN}}': pilares_html,
        '{{NOTA_MEDICA}}': f'<strong>Nota para el equipo médico:</strong> {esc(j.get("diagnostico",{}).get("nota_medica",""))}',
        '{{DIAGNOSTICO_FILAS}}': diag_html,
        '{{RUTINA_NOTA}}': esc(j.get('rutina',{}).get('nota','')),
        '{{RUTINA_FILAS}}': rutina_html,
        '{{CALENDARIO_HTML}}': cal_html,
        '{{P1_EMOJI}}': get_emoji(0), '{{P1_TITULO}}': esc(p1.get('titulo','')),
        '{{P1_OBJETIVO}}': esc(p1.get('objetivo','')),
        '{{P1_QUOTE_TOP}}': pos_q(p1pos,p1q,'inicio'), '{{P1_QUOTE_MID}}': pos_q(p1pos,p1q,'medio'), '{{P1_QUOTE_END}}': pos_q(p1pos,p1q,'final'),
        '{{P1_PERMITIDOS}}': p1_perm, '{{P1_EVITAR}}': p1_evit,
        '{{P1_TIPS_TOP}}': p1tips if p1pos=='inicio' else '', '{{P1_TIPS_END}}': p1tips if p1pos!='inicio' else '',
        '{{P1_MENU}}': p1_menu, '{{P1_COMPRAS}}': p1_compras, '{{P1_SUPLEMENTACION}}': p1_supl,
        '{{P2_EMOJI}}': get_emoji(1), '{{P2_TITULO}}': esc(p2.get('titulo','')),
        '{{P2_OBJETIVO}}': esc(p2.get('objetivo','')),
        '{{P2_QUOTE_TOP}}': pos_q(p2pos,p2q,'inicio'), '{{P2_QUOTE_MID}}': pos_q(p2pos,p2q,'medio'), '{{P2_QUOTE_END}}': pos_q(p2pos,p2q,'final'),
        '{{P2_PLAN}}': esc(p2.get('plan_semanal','')), '{{P2_ADAPTACIONES}}': esc(p2.get('adaptaciones','')),
        '{{P2_TIPS}}': p2tips,
        '{{P3_EMOJI}}': get_emoji(2), '{{P3_TITULO}}': esc(p3.get('titulo','')),
        '{{P3_OBJETIVO}}': esc(p3.get('objetivo','')),
        '{{P3_QUOTE_TOP}}': pos_q(p3pos,p3q,'inicio'), '{{P3_QUOTE_MID}}': pos_q(p3pos,p3q,'medio'), '{{P3_QUOTE_END}}': pos_q(p3pos,p3q,'final'),
        '{{P3_TECNICAS}}': p3_tec, '{{P3_TIPS}}': p3tips,
        '{{P4_EMOJI}}': get_emoji(3), '{{P4_TITULO}}': esc(p4.get('titulo','')),
        '{{P4_OBJETIVO}}': esc(p4.get('objetivo','')),
        '{{P4_QUOTE_TOP}}': pos_q(p4pos,p4q,'inicio'), '{{P4_QUOTE_MID}}': pos_q(p4pos,p4q,'medio'), '{{P4_QUOTE_END}}': pos_q(p4pos,p4q,'final'),
        '{{P4_PROTOCOLO}}': p4_proto, '{{P4_REGLAS}}': p4_reglas, '{{P4_TIPS}}': p4tips,
        '{{P5_EMOJI}}': get_emoji(4), '{{P5_TITULO}}': esc(p5.get('titulo','')),
        '{{P5_OBJETIVO}}': esc(p5.get('objetivo','')),
        '{{P5_QUOTE_TOP}}': pos_q(p5pos,p5q,'inicio'), '{{P5_QUOTE_MID}}': pos_q(p5pos,p5q,'medio'), '{{P5_QUOTE_END}}': pos_q(p5pos,p5q,'final'),
        '{{P5_BIMESTRES}}': p5_bim, '{{P5_TOTAL_ANUAL}}': f'${total_anual:,}',
        '{{P5_RUTINA_AM}}': p5_am, '{{P5_RUTINA_PM}}': p5_pm,
        '{{P5_NOTAS_CRITICAS}}': p5_notas, '{{P5_TIPS}}': p5tips,
        '{{COMP_PARRAFO}}': esc(comp.get('parrafo','')),
        '{{COMP_RESULTADOS}}': comp_res, '{{COMP_PASOS}}': comp_pasos,
    }

    for k, v in replacements.items():
        tpl = tpl.replace(k, v)
    return tpl


def generar_calendario():
    mes_names = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    dias_sem  = ['Lu','Ma','Mi','Ju','Vi','Sa','Do']
    hoy = date.today()
    yr  = hoy.year
    mi  = hoy.month
    cal_html = ''
    row_html = ''
    for m in range(12):
        mes     = ((mi - 1 + m) % 12) + 1
        anio_m  = yr + (mi - 1 + m) // 12
        dias_en = calendar.monthrange(anio_m, mes)[1]
        primer  = date(anio_m, mes, 1).isoweekday()
        grid    = '<div class="cal-grid">'
        for d in dias_sem: grid += f'<div class="cal-dh">{d}</div>'
        for _ in range(1, primer): grid += '<div class="cal-d cal-empty"></div>'
        for dia in range(1, dias_en + 1):
            grid += f'<div class="cal-d"><div class="n">{dia}</div><div class="dots"><div class="dot nu"></div><div class="dot ac"></div><div class="dot me"></div><div class="dot su"></div></div></div>'
        grid += '</div>'
        row_html += f'<div class="cal-month"><div class="cal-mhdr">{mes_names[mes-1]} {anio_m}</div>{grid}</div>'
        if (m + 1) % 3 == 0:
            cal_html += f'<div class="cal-row">{row_html}</div>'
            row_html = ''
    if row_html: cal_html += f'<div class="cal-row">{row_html}</div>'
    return cal_html


# ════════════════════════════════════════════════════════════
# EMAILS con Resend
# ════════════════════════════════════════════════════════════

def enviar_resend(asunto, cuerpo, to, adjunto_path=None, adjunto_name=None):
    if not RESEND_KEY:
        print('RESEND_KEY no configurado')
        return
    payload = {
        'from': f'Centro Carvajal <{MAIL_FROM}>',
        'to': [to],
        'subject': asunto,
        'html': cuerpo,
    }
    if adjunto_path and adjunto_name and os.path.exists(adjunto_path):
        import base64
        with open(adjunto_path, 'rb') as f:
            payload['attachments'] = [{
                'filename': adjunto_name,
                'content': base64.b64encode(f.read()).decode(),
            }]
    try:
        r = req.post('https://api.resend.com/emails',
            headers={'Authorization': f'Bearer {RESEND_KEY}', 'Content-Type': 'application/json'},
            json=payload, timeout=30)
        print(f'Resend {to}: {r.status_code}')
    except Exception as e:
        print(f'Resend error: {e}')


def email_formulario(d, faltantes):
    nombre = d.get('nombre', '')
    rows = ''.join(f'<tr><td style="color:#b8935a;font-weight:600;padding:8px 16px;font-size:12px;text-transform:uppercase;letter-spacing:1px;width:140px">{k}</td><td style="padding:8px 16px;font-size:13px">{v}</td></tr>'
        for k, v in [('Nombre', nombre), ('Edad', d.get('edad','')), ('Ocupacion', d.get('ocupacion','')),
                     ('Medicamentos', d.get('medicamentos','')), ('Cirugias', d.get('cirugias','')),
                     ('Prioridad', d.get('prioridad','')), ('Satisfaccion', d.get('satisfaccion','') + '/10'),
                     ('Expectativas', d.get('expectativas',''))])
    faltantes_html = ''
    if faltantes:
        items = ''.join(f'<li style="font-size:12px;color:#6a5a20;padding:2px 0">{f}</li>' for f in faltantes)
        faltantes_html = f'<div style="background:#fffbf0;border:1px solid #e8d89a;border-radius:4px;padding:14px 18px;margin:16px 24px"><div style="font-size:11px;font-weight:700;color:#8a7030;margin-bottom:8px;text-transform:uppercase;letter-spacing:1px">Campos sin datos</div><ul style="padding-left:16px;margin:0">{items}</ul></div>'
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="background:#f0e8de;padding:20px;font-family:sans-serif"><div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #ddd"><div style="background:#1a1410;padding:20px 24px"><div style="color:#b8935a;font-size:11px;letter-spacing:3px;text-transform:uppercase">Centro Carvajal · Nuevo Cuestionario</div><div style="color:#fff;font-size:18px;margin-top:4px">{nombre}</div></div><table style="width:100%;border-collapse:collapse">{rows}</table>{faltantes_html}<div style="background:#1a1410;padding:12px 24px;text-align:center;font-size:10px;color:rgba(255,255,255,0.3)">Centro Carvajal · centrocarvajal.com</div></div></body></html>'


def email_plan(nombre, html_url, fecha):
    return f'<!DOCTYPE html><html><head><meta charset="UTF-8"></head><body style="background:#f0e8de;padding:20px;font-family:sans-serif"><div style="max-width:600px;margin:0 auto;background:#fff;border:1px solid #ddd"><div style="background:#1a1410;padding:20px 24px"><div style="color:#b8935a;font-size:11px;letter-spacing:3px;text-transform:uppercase">Centro Carvajal · Plan Generado</div><div style="color:#fff;font-size:18px;margin-top:4px">{nombre}</div><div style="color:rgba(255,255,255,0.4);font-size:11px;margin-top:2px">{fecha}</div></div><div style="padding:24px"><p style="font-size:13px;color:#3d2e20;margin-bottom:16px">El plan personalizado de <strong>{nombre}</strong> ha sido generado exitosamente.</p><div style="text-align:center;margin:20px 0"><a href="{html_url}" style="background:#b8935a;color:#fff;padding:14px 32px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:500">Ver Plan Completo</a></div><p style="font-size:11px;color:#999;text-align:center">O copia este link: {html_url}</p></div><div style="background:#1a1410;padding:12px 24px;text-align:center;font-size:10px;color:rgba(255,255,255,0.3)">Centro Carvajal · centrocarvajal.com</div></div></body></html>'


if __name__ == '__main__':
    app.run(debug=True, port=5000)
