# Source Generated with Decompyle++
# File: handlers.cpython-312.pyc (Python 3.12)

'''Engineering CAD and print handlers.'''
from __future__ import annotations
import re
from jarvis.handlers.registry import register_action
from jarvis.p3_flags import cad_enabled, printer_enabled
from jarvis.response import err, ok
from jarvis.tool_permissions import create_pending, needs_confirmation
cad_status_action = (lambda assistant = None, params = None, message = register_action('cad_status', info = True, module = 'engineering', extension = 'engineering', description = 'CAD toolchain status'): cad_status = cad_statusimport jarvis.engineering.cad_depsslicer_status = slicer_statusimport jarvis.engineering.slicerst = cad_status()lines = [
f'''**CAD:** {'ready' if st.get('ready') else 'not ready'}''',
f'''- OpenSCAD: {'yes' if st.get('openscad') else 'no'}''',
f'''- build123d: {'yes' if st.get('build123d') else 'no'}''',
f'''- Meshy: {'yes' if st.get('meshy') else 'no'}''']sl = slicer_status()if sl.get('slicers'):
None(f'''{(lambda .0: pass# WARNING: Decompyle incomplete
)(sl['slicers']())}''')
# WARNING: Decompyle incomplete
)()
generate_cad = (lambda assistant = None, params = None, message = register_action('generate_cad', module = 'engineering', description = 'Generate STL from prompt'): if not cad_enabled():
err('CAD disabled (JARVIS_CAD=0).', module = 'engineering')if not None.get('prompt'):
None.get('prompt')if not params.get('description'):
params.get('description')prompt = ''.strip()if not prompt:
prompt = re.sub('^(design|generate|create|make)\\s+(a\\s+)?(cad|part|model|stl)\\s*', '', message, flags = re.I).strip()if not prompt:
prompt = message.strip()# WARNING: Decompyle incomplete
)()
iterate_cad = (lambda assistant = None, params = None, message = register_action('iterate_cad', module = 'engineering', description = 'Modify existing CAD design (Ada v2 parity)'): params = dict(params)params['edit'] = Trueif not params.get('prompt'):
if not re.sub('^(iterate|edit|modify|change|update)\\s+(the\\s+)?(cad|design|model|part)\\s*', '', message, flags = re.I).strip():
re.sub('^(iterate|edit|modify|change|update)\\s+(the\\s+)?(cad|design|model|part)\\s*', '', message, flags = re.I).strip()params['prompt'] = message.strip()generate_cad(assistant, params, message))()
engineering_design = (lambda assistant = None, params = None, message = register_action('engineering_design', module = 'engineering', description = 'Design a 3D part (alias)'): generate_cad(assistant, params, message))()
slice_stl_action = (lambda assistant = None, params = None, message = register_action('slice_stl', module = 'engineering', description = 'Slice STL to G-code'): if not printer_enabled():
err('Printer pipeline disabled.', module = 'engineering')get_model = get_modelimport jarvis.engineering.cad_storeslice_stl = slice_stlimport jarvis.engineering.slicerif not params.get('stl_path'):
params.get('stl_path')stl = ''.strip()if not params.get('model_id'):
params.get('model_id')mid = ''.strip()if not mid and stl:
m = get_model(mid)if not m:
mif not { }.get('stl_path'):
{ }.get('stl_path')stl = ''if not stl:
err('model_id or stl_path required.', module = 'engineering')if not params.get('slicer'):
params.get('slicer')if not params.get('printer_model'):
params.get('printer_model')if not params.get('model'):
params.get('model')result = slice_stl(stl, slicer_id = '', printer_model = '')if not result.get('ok'):
err(result.get('error', 'Slice failed'), module = 'engineering')# WARNING: Decompyle incomplete
)()
printer_status_action = (lambda assistant = None, params = None, message = register_action('printer_status', info = True, module = 'engineering', description = '3D printer status'): printer_status = printer_statusimport jarvis.engineering.printer_clientget_printer = get_printerimport jarvis.engineering.printer_storeif not params.get('printer_id'):
params.get('printer_id')p = get_printer(''.strip())if not p:
ok('No printer configured — add one in Maker lab panel.', module = 'engineering')st = printer_status(p)# WARNING: Decompyle incomplete
)()
start_print_action = (lambda assistant = None, params = None, message = register_action('start_print', module = 'engineering', description = 'Upload G-code and start print'): if not printer_enabled():
err('Printer disabled.', module = 'engineering')enqueue_print = enqueue_printimport jarvis.engineering.print_jobsif not params.get('gcode_path'):
params.get('gcode_path')gcode = ''.strip()if not gcode:
err('gcode_path required.', module = 'engineering')if not None('cad') and params.get('_confirmed'):
cid = create_pending('cad', 'start_print', dict(params), message)ok('Confirm start print?', module = 'engineering', type = 'confirm_required', confirm_id = cid, tool = 'cad')if not params.get('printer_id'):
params.get('printer_id')result = enqueue_print(gcode, printer_id = '', bed_confirmed = bool(params.get('bed_confirmed')), filament_confirmed = bool(params.get('filament_confirmed')))# WARNING: Decompyle incomplete
)()
teach_cad_action = (lambda assistant = None, params = None, message = register_action('teach_cad', module = 'engineering', extension = 'engineering', description = 'Teach parametric CAD pattern'): list_patterns = list_patternsparse_teach_cad = parse_teach_cadrecord_pattern = record_patternimport jarvis.engineering.cad_teachingparsed = parse_teach_cad(message)if not params.get('text'):
params.get('text')if not params.get('pattern'):
params.get('pattern')text = ''.strip()if not params.get('kind'):
params.get('kind')kind = 'pattern'.strip()if parsed:
text = parsed['text']if not parsed.get('kind'):
parsed.get('kind')kind = kindif not text:
err('Say **teach cad:** hose adapters use 25.4mm NPS threads, or **teach cad rule:** add 0.2mm FDM clearance.', module = 'engineering')result = record_pattern(text, kind = kind)if not result.get('ok'):
err(result.get('error', 'Could not save pattern'), module = 'engineering')total = None(list_patterns())ok(f'''Saved CAD **{kind}** ({total} patterns stored).\n\n_{text[:200]}_''', module = 'engineering', type = 'teach_cad', pattern = result.get('pattern')))()
cad_patterns_list = (lambda assistant = None, params = None, message = register_action('cad_patterns_list', info = True, module = 'engineering', extension = 'engineering', description = 'List taught CAD patterns'): list_patterns = list_patternsimport jarvis.engineering.cad_teachingif not params.get('query'):
params.get('query')rows = list_patterns(query = ''.strip(), limit = 20)if not rows:
ok('No CAD patterns yet — **teach cad:** …', module = 'engineering')# WARNING: Decompyle incomplete
)()
