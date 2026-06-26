# Source Generated with Decompyle++
# File: comfyui_settings.cpython-312.pyc (Python 3.12)

'''Persisted ComfyUI device mode (GPU / CPU / auto-fallback) and checkpoint choice.'''
from __future__ import annotations
import json
import os
from pathlib import Path
from jarvis.config import DATA_DIR
SETTINGS_FILE = DATA_DIR / 'comfyui_settings.json'
VALID_MODES = ('auto', 'gpu', 'cpu')
VALID_CHECKPOINTS = ('flux', 'quality', 'fast')
UNCENSORED_CHECKPOINTS = ('RealVisXL_V5.0_fp16.safetensors', 'Realistic_Vision_V6.0_NV_B1_fp16.safetensors', 'ponyDiffusionV6XL_v6StartWithThisOne.safetensors', 'Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors', 'lustifySDXLNSFWSFW_v10.safetensors', 'leosamsHelloworldXL_helloworldXL60.safetensors', 'DreamShaperXL_Turbo_v2.safetensors', 'epicrealism_naturalSinRC1VAE.safetensors')
UNCENSORED_CHECKPOINT_LABELS = {
    'RealVisXL_V5.0_fp16.safetensors': 'RealVisXL V5 (photoreal SDXL)',
    'Realistic_Vision_V6.0_NV_B1_fp16.safetensors': 'Realistic Vision V6 (photoreal SD 1.5)',
    'ponyDiffusionV6XL_v6StartWithThisOne.safetensors': 'Pony Diffusion V6 XL (anime/illustration)',
    'Juggernaut-XL_v9_RunDiffusionPhoto_v2.safetensors': 'Juggernaut XL v9 (photoreal SDXL)',
    'lustifySDXLNSFWSFW_v10.safetensors': 'Lustify SDXL v10 (photoreal SDXL)',
    'leosamsHelloworldXL_helloworldXL60.safetensors': 'HelloWorld XL 6.0 (SDXL)',
    'DreamShaperXL_Turbo_v2.safetensors': 'DreamShaper XL Turbo v2 (fast SDXL)',
    'epicrealism_naturalSinRC1VAE.safetensors': 'epiCRealism (photoreal SD 1.5)' }
COMFYUI_PORT = int(os.getenv('JARVIS_COMFYUI_PORT', '8188'))
COMFYUI_URL = os.getenv('JARVIS_COMFYUI_URL', f'''http://127.0.0.1:{COMFYUI_PORT}''')
COMFY_ROOT = Path(os.getenv('JARVIS_COMFYUI_ROOT', Path.home() / 'ComfyUI'))
CKPT_DIR = COMFY_ROOT / 'models' / 'checkpoints'

def _defaults():
    return {
        'mode': 'auto',
        'runtime_cpu': False,
        'checkpoint': 'quality' }


def load_settings():
    data = _defaults()
    if not SETTINGS_FILE.exists():
        return data
    
    try:
        raw = json.loads(SETTINGS_FILE.read_text(encoding = 'utf-8'))
        if raw.get('mode') in VALID_MODES:
            data['mode'] = raw['mode']
        if raw.get('checkpoint') in VALID_CHECKPOINTS:
            data['checkpoint'] = raw['checkpoint']
        custom = raw.get('checkpoint_file')
        if isinstance(custom, str) and custom.strip():
            data['checkpoint_file'] = Path(custom.strip()).name
        if raw.get('uncensored_auto_applied'):
            data['uncensored_auto_applied'] = True
        wf = raw.get('workflow_file')
        if isinstance(wf, str) and wf.strip():
            data['workflow_file'] = wf.strip()
        data['runtime_cpu'] = bool(raw.get('runtime_cpu', False))
        return data
    except (json.JSONDecodeError, OSError, TypeError):
        return data



def _save(data = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    SETTINGS_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')
    return data


def save_mode(mode = None):
    if mode not in VALID_MODES:
        raise ValueError(f'''mode must be one of {VALID_MODES}''')
    if mode in ('gpu', 'auto'):
        clear_runtime_cpu_fallback()
    data = load_settings()
    data['mode'] = mode
    data['runtime_cpu'] = False
    return _save(data)


def save_checkpoint(checkpoint = None):
    if checkpoint not in VALID_CHECKPOINTS:
        raise ValueError(f'''checkpoint must be one of {VALID_CHECKPOINTS}''')
    data = load_settings()
    data['checkpoint'] = checkpoint
    data.pop('checkpoint_file', None)
    return _save(data)


def recommended_uncensored_checkpoint():
    '''Best installed NSFW-friendly checkpoint, or None.'''
    for name in UNCENSORED_CHECKPOINTS:
        if not (CKPT_DIR / name).is_file():
            continue
        
        return UNCENSORED_CHECKPOINTS, name


def apply_uncensored_defaults():
    '''Pick an NSFW-friendly checkpoint and GPU mode when uncensored mode is enabled.'''
    data = load_settings()
    ckpt = recommended_uncensored_checkpoint()
    env_cpu = os.getenv('JARVIS_COMFYUI_CPU', '').strip().lower()
    if env_cpu not in ('1', 'true', 'yes', 'on'):
        data['mode'] = 'gpu'
        data['runtime_cpu'] = False
    if not ckpt:
        data.pop('uncensored_auto_applied', None)
        return _save(data)
    if None.get('checkpoint_file'):
        None.get('checkpoint_file')
    manual = not data.get('uncensored_auto_applied')
    if data.get('checkpoint') == 'flux':
        data.get('checkpoint') == 'flux'
    flux_only = not data.get('checkpoint_file')
    if not manual and flux_only:
        return data
    if None.get('uncensored_auto_applied') and data.get('checkpoint_file') == ckpt:
        return _save(data)
    data['checkpoint_file'] = None
    data['checkpoint'] = 'quality'
    data['uncensored_auto_applied'] = True
    return _save(data)


def clear_uncensored_auto_checkpoint():
    '''Revert auto-selected NSFW checkpoint when leaving uncensored mode.'''
    data = load_settings()
    if not data.pop('uncensored_auto_applied', False):
        return data
    auto_ckpt = None.get('checkpoint_file', '')
    if auto_ckpt in UNCENSORED_CHECKPOINTS:
        data.pop('checkpoint_file', None)
    return _save(data)


def mark_checkpoint_manual():
    """User picked a checkpoint — don't revert on uncensored toggle off."""
    data = load_settings()
    data['uncensored_auto_applied'] = False
    return _save(data)


def save_checkpoint_file(filename = None):
    '''Use a specific .safetensors from the checkpoints folder.'''
    name = Path(filename).name
    if name != filename or '..' in filename:
        raise ValueError('Invalid checkpoint filename')
    path = CKPT_DIR / name
    if not path.is_file():
        raise ValueError(f'''Checkpoint not found: {name}''')
    data = load_settings()
    data['checkpoint_file'] = name
    data['uncensored_auto_applied'] = False
    return _save(data)


def clear_checkpoint_file():
    data = load_settings()
    data.pop('checkpoint_file', None)
    return _save(data)


def save_workflow_file(path = None):
    '''Optional custom ComfyUI workflow JSON (absolute path or under ComfyUI).'''
    if not path:
        path
    path = ''.strip()
    data = load_settings()
    if not path:
        data.pop('workflow_file', None)
        return _save(data)
    candidate = None(path).expanduser()
    if not candidate.is_file():
        raise ValueError(f'''Workflow file not found: {path}''')
    data['workflow_file'] = str(candidate.resolve())
    return _save(data)


def effective_workflow_path():
    data = load_settings()
    if not data.get('workflow_file'):
        data.get('workflow_file')
    wf = ''.strip()
    if wf and Path(wf).is_file():
        return wf
    env = None.getenv('JARVIS_COMFYUI_WORKFLOW', '').strip()
    if env and Path(env).is_file():
        return env


def mark_runtime_cpu_fallback():
    data = load_settings()
    data['runtime_cpu'] = True
    return _save(data)


def clear_runtime_cpu_fallback():
    data = load_settings()
    data['runtime_cpu'] = False
    return _save(data)


def effective_cpu_mode():
    env = os.getenv('JARVIS_COMFYUI_CPU', '').strip().lower()
    if env in ('1', 'true', 'yes', 'on'):
        return True
    if env in ('0', 'false', 'no', 'off'):
        return False
    data = load_settings()
    if data.get('runtime_cpu'):
        return True
    mode = data.get('mode', 'auto')
    return mode == 'cpu'


def auto_fallback_enabled():
    return load_settings().get('mode') == 'auto'


def mode_label():
    data = load_settings()
    cpu = effective_cpu_mode()
    if cpu and data.get('runtime_cpu'):
        return 'CPU (auto fallback)'
    if cpu:
        return 'CPU'
    return 'GPU'


def _glob_ckpt(pattern = None):
    if not CKPT_DIR.exists():
        return None
    for path in sorted(CKPT_DIR.glob(pattern)):
        if not path.is_file():
            continue
        if path.name.startswith('put_'):
            continue
        
        return sorted(CKPT_DIR.glob(pattern)), path.name


def list_all_checkpoint_files():
    '''All .safetensors in ComfyUI checkpoints (for picker UI).'''
    if not CKPT_DIR.exists():
        return []
    out = None
    for path in sorted(CKPT_DIR.glob('*.safetensors')):
        if path.is_file() or path.name.startswith('put_'):
            continue
        lower = path.name.lower()
        if 'flux' in lower:
            family = 'Flux'
        elif 'turbo' in lower:
            family = 'SDXL Turbo'
        elif 'realvis' in lower and 'realistic_vision' in lower and 'juggernaut' in lower or 'lustify' in lower:
            family = 'RealVis'
        elif 'helloworld' in lower or 'leosams' in lower:
            family = 'HelloWorld XL'
        elif 'dreamshaper' in lower:
            family = 'DreamShaper'
        elif 'epicrealism' in lower or 'epic realism' in lower:
            family = 'epiCRealism'
        elif 'pony' in lower:
            family = 'Pony XL'
        elif 'xl' in lower or 'sd_xl' in lower:
            family = 'SDXL'
        elif 'sd1' in lower and 'v1-5' in lower or 'dreamshaper' in lower:
            family = 'SD 1.5'
        else:
            family = 'Other'
        out.append({
            'name': path.name,
            'family': family,
            'size_mb': round(path.stat().st_size / 1048576) })
    return out


def list_installed_checkpoints():
    if not _glob_ckpt('*flux*schnell*fp8*'):
        _glob_ckpt('*flux*schnell*fp8*')
    if not _glob_ckpt('sd_xl_base_1.0.safetensors'):
        _glob_ckpt('sd_xl_base_1.0.safetensors')
    return {
        'flux': _glob_ckpt('*flux*schnell*'),
        'quality': _glob_ckpt('*base*.safetensors'),
        'fast': _glob_ckpt('*turbo*.safetensors') }


def _installed_ckpt(name = None):
    if not name:
        return None
    path = CKPT_DIR / Path(name).name
    if path.is_file():
        return path.name


def resolve_checkpoint_name():
    env = os.getenv('JARVIS_COMFYUI_CKPT', '').strip()
    if env:
        resolved = _installed_ckpt(env)
        if resolved:
            return resolved
        data = None()
        if not data.get('checkpoint_file'):
            data.get('checkpoint_file')
    custom = ''.strip()
    if custom:
        resolved = _installed_ckpt(custom)
        if resolved:
            return resolved
        installed = None()
        choice = data.get('checkpoint', 'quality')
        if choice == 'fast':
            candidates = [
                installed['fast'],
                installed['quality'],
                installed['flux']]
        elif choice == 'flux':
            candidates = [
                installed['flux'],
                installed['quality'],
                installed['fast']]
        else:
            candidates = [
                installed['quality'],
                installed['flux'],
                installed['fast']]
    for candidate in candidates:
        resolved = _installed_ckpt(candidate)
        if not resolved:
            continue
        
        return candidates, resolved
    if any_ckpt:
        return any_ckpt
    raise _glob_ckpt('*.safetensors')(f'''No checkpoint .safetensors found in {CKPT_DIR}. Run ./scripts/install-sdxl-base.sh or pick a model in Gallery → Image engine.''')


def comfyui_start_hint():
    return f'''~/ComfyUI/venv/bin/python ~/ComfyUI/main.py --listen 127.0.0.1 --port {COMFYUI_PORT}'''


def checkpoint_label():
    
    try:
        name = resolve_checkpoint_name()
        lower = name.lower()
        if 'flux' in lower and 'schnell' in lower:
            return 'Flux Schnell'
        if 'flux' in lower:
            return 'Flux'
        if 'turbo' in lower:
            return 'SDXL Turbo'
        if 'base' in lower:
            return 'SDXL 1.0'
        return Path(name).stem
    except FileNotFoundError:
        return 'No checkpoint installed'



def checkpoint_family():
    
    try:
        name = resolve_checkpoint_name().lower()
        if 'flux' in name:
            return 'flux'
        if 'turbo' in name:
            return 'sdxl_turbo'
        return 'sdxl'
    except FileNotFoundError:
        return 'sdxl'



def get_settings_dict():
    is_uncensored = is_uncensored
    import jarvis.config
    prompt_model_name = prompt_model_name
    import jarvis.modules.image
    data = load_settings()
    cpu = effective_cpu_mode()
    installed = list_installed_checkpoints()
    all_files = list_all_checkpoint_files()
    rec_ckpt = recommended_uncensored_checkpoint()
    uncensored = is_uncensored()
# WARNING: Decompyle incomplete

