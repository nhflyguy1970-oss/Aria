# Source Generated with Decompyle++
# File: model_store.cpython-312.pyc (Python 3.12)

'''Persistent model configuration — optimized defaults + user overrides.'''
import json
from jarvis.config import DATA_DIR, is_uncensored
from jarvis.ollama_health import check_ollama
SETTINGS_FILE = DATA_DIR / 'model_settings.json'
ROLES = ('general', 'coder', 'review', 'vision', 'image', 'embed')
NON_OLLAMA_BACKENDS = frozenset({
    'a1111',
    'comfyui',
    'automatic1111'})
ROLE_LABELS = {
    'general': 'Chat',
    'coder': 'Code',
    'review': 'Review',
    'vision': 'Vision',
    'image': 'Image',
    'embed': 'Memory embeddings' }
OPTIMIZED_STANDARD = {
    'general': 'qwen2.5:7b',
    'coder': 'qwen2.5-coder:7b',
    'review': 'qwen2.5:7b',
    'vision': 'moondream:latest',
    'image': 'comfyui',
    'embed': 'nomic-embed-text' }
OPTIMIZED_UNCENSORED = {
    'general': 'dolphin3:latest',
    'coder': 'qwen2.5-coder:7b',
    'review': 'dolphin3:latest',
    'vision': 'llava:13b',
    'image': 'comfyui',
    'embed': 'nomic-embed-text' }
FAST_STANDARD = {
    'general': 'qwen2.5:7b',
    'coder': 'qwen2.5-coder:7b',
    'review': 'qwen2.5:7b',
    'vision': 'moondream:latest',
    'image': 'comfyui',
    'embed': 'nomic-embed-text' }
FAST_UNCENSORED = {
    'general': 'dolphin3:latest',
    'coder': 'qwen2.5-coder:7b',
    'review': 'dolphin3:latest',
    'vision': 'llava:13b',
    'image': 'comfyui',
    'embed': 'nomic-embed-text' }
PRESETS = {
    'quality': {
        'standard': OPTIMIZED_STANDARD,
        'uncensored': OPTIMIZED_UNCENSORED },
    'fast': {
        'standard': FAST_STANDARD,
        'uncensored': FAST_UNCENSORED } }
FALLBACK_PRIORITY = {
    'general': [
        'qwen2.5:14b',
        'qwen2.5:7b',
        'llama3.1:8b',
        'gemma3:12b',
        'dolphin3:latest',
        'dolphin-mistral:latest',
        'mistral-nemo:latest',
        'qwen3:14b'],
    'coder': [
        'qwen2.5-coder:14b',
        'deepseek-coder-v2:16b',
        'deepseek-coder-v2:latest',
        'coder-stable:latest',
        'devstral:latest',
        'qwen2.5-coder:7b'],
    'review': [
        'deepseek-r1:14b',
        'qwen2.5:14b',
        'gemma3:12b',
        'dolphin3:latest'],
    'vision': [
        'llava:13b',
        'moondream:latest',
        'moondream',
        'llama3.2-vision:11b'],
    'image': [
        'comfyui'],
    'embed': [
        'nomic-embed-text:latest',
        'nomic-embed-text'] }

def is_ollama_pullable(model = None):
    if not model:
        model
    name = ''.strip().lower()
    if bool(name):
        bool(name)
    return name not in NON_OLLAMA_BACKENDS


def _installed():
    ollama = check_ollama()
    if ollama.get('running'):
        return ollama.get('models', [])


def _match_installed(preferred = None, installed = None):
    if not preferred or installed:
        return None
    pref_lower = preferred.lower()
    for name in installed:
        if not name.lower() == pref_lower:
            continue
        
        return installed, name
    for None in installed:
        if not name.lower().startswith(pref_base):
            continue
        
        return pref_lower.split(':')[0], name


def _hardware_blurb():
    detect_gpu = detect_gpu
    is_low_vram = is_low_vram
    import jarvis.gpu
    gpu = detect_gpu()
    if not gpu.get('name'):
        gpu.get('name')
    name = 'Unknown GPU'
    if not gpu.get('vram_mb'):
        gpu.get('vram_mb')
    vram = 0
    if gpu.get('nvidia_available') and vram >= 11000:
        gpu_label = f'''{name} ({vram // 1024}GB VRAM)'''
        note = '14B models + ComfyUI fit on 12GB NVIDIA. Use dolphin3 for uncensored chat.'
    elif is_low_vram(10240):
        gpu_label = f'''{name} (8GB VRAM)''' if vram else 'AMD RX 7600 (8GB VRAM)'
        note = '14B models use GPU + RAM offload. Use 7B variants for faster replies.'
    elif vram:
        pass
    
    gpu_label = name
    note = 'Tune models to your VRAM — say **what models** for recommendations.'
    return {
        'gpu': gpu_label,
        'ram': '62GB',
        'cpu': 'Ryzen 5 5600X',
        'note': note }


def _pick_for_role(role = None, defaults = None, installed = None):
    preferred = defaults.get(role, '')
    match = _match_installed(preferred, installed)
    if match:
        return match
    for candidate in None.get(role, []):
        match = _match_installed(candidate, installed)
        if not match:
            continue
        
        return None.get(role, []), match
    if not preferred:
        preferred
    return 'qwen2.5:7b'


def build_optimized_defaults(installed = None):
    pass
# WARNING: Decompyle incomplete


def _load_raw():
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    if SETTINGS_FILE.exists():
        
        try:
            return json.loads(SETTINGS_FILE.read_text(encoding = 'utf-8'))
            return { }
        except (json.JSONDecodeError, OSError):
            return { }



def _save_raw(data = None):
    DATA_DIR.mkdir(parents = True, exist_ok = True)
    SETTINGS_FILE.write_text(json.dumps(data, indent = 2), encoding = 'utf-8')


def _saved_vision_model(data = None, mode = None, installed = None):
    '''Return vision model from model_settings (matched to an installed tag if possible).'''
    if not data:
        return None
    if not data.get(mode):
        data.get(mode)
    saved = { }.get('vision', '').strip()
    if not saved:
        return None
    matched = _match_installed(saved, installed)
    if not matched:
        matched
    return saved


def _vision_fallback_for_ollama(model = None, installed = None):
    '''Use moondream/llava when Ollama is too old for llama3.2-vision (mllama).'''
    requires_mllama = requires_mllama
    supports_mllama = supports_mllama
    import jarvis.ollama_health
    if requires_mllama(model) or supports_mllama():
        return model
    for candidate in None:
        match = _match_installed(candidate, installed)
        if not match:
            continue
        
        return None, match
    return model


def get_models():
    '''Active models for current mode (standard or uncensored).'''
    load_vision_quality = load_vision_quality
    import jarvis.config
    is_low_vram = is_low_vram
    import jarvis.gpu
    data = _load_raw()
    mode = 'uncensored' if is_uncensored() else 'standard'
    optimized = build_optimized_defaults()
    installed = _installed()
    if not data:
        result = optimized[mode].copy()
    else:
        saved = data.get(mode, { })
        result = optimized[mode].copy()
        for role in ROLES:
            if not role in saved:
                continue
            if not saved[role]:
                continue
            result[role] = saved[role]
    quality = load_vision_quality()
    if quality == 'custom':
        user_vision = _saved_vision_model(data, mode, installed) if data else None
        if user_vision:
            result['vision'] = user_vision
    if quality == 'quality':
        if is_low_vram():
            if not _match_installed('llama3.2-vision:11b', installed):
                _match_installed('llama3.2-vision:11b', installed)
                if not _match_installed('llama3.2-vision', installed):
                    _match_installed('llama3.2-vision', installed)
            heavy = _match_installed('llava:13b', installed)
        elif not _match_installed('llava:13b', installed):
            _match_installed('llava:13b', installed)
            if not _match_installed('llama3.2-vision:11b', installed):
                _match_installed('llama3.2-vision:11b', installed)
        heavy = _match_installed('llama3.2-vision', installed)
        if heavy:
            result['vision'] = heavy
        elif quality == 'fast':
            if not _match_installed('moondream:latest', installed):
                _match_installed('moondream:latest', installed)
            light = _match_installed('moondream', installed)
            if light:
                result['vision'] = light
            elif is_low_vram() and 'llava' in result.get('vision', '').lower():
                fallback = _match_installed('moondream:latest', installed)
                if fallback:
                    result['vision'] = fallback
    result['vision'] = _vision_fallback_for_ollama(result.get('vision', ''), installed)
    return result


def get_all_settings():
    data = _load_raw()
    optimized = build_optimized_defaults()
    installed = _installed()
    if not data:
        data = {
            'standard': optimized['standard'],
            'uncensored': optimized['uncensored'],
            'customized': False }
        _save_raw(data)
# WARNING: Decompyle incomplete


def update_models(mode = None, models = None):
    data = _load_raw()
    if not data:
        data = build_optimized_defaults()
        data['customized'] = False
    mode_key = 'uncensored' if mode == 'uncensored' else 'standard'
    current = data.get(mode_key, build_optimized_defaults()[mode_key])
    for role in ROLES:
        if not role in models:
            continue
        if not models[role]:
            continue
        current[role] = models[role].strip()
    data[mode_key] = current
    data['customized'] = True
    _save_raw(data)
    return get_all_settings()


def apply_preset(preset = None, mode = None):
    '''Apply fast or quality preset for current or given mode.'''
    if preset not in PRESETS:
        raise ValueError(f'''Unknown preset: {preset}''')
    if not mode:
        mode
    mode_key = 'uncensored' if is_uncensored() else 'standard'
    if mode_key not in ('standard', 'uncensored'):
        mode_key = 'standard'
    raw_preset = PRESETS[preset][mode_key]
    installed = _installed()
# WARNING: Decompyle incomplete


def get_missing_models():
    active = get_models()
    installed = _installed()
    models_missing = models_missing
    import jarvis.ollama_health
# WARNING: Decompyle incomplete


def reset_to_optimized(mode = None):
    optimized = build_optimized_defaults()
    if not _load_raw():
        _load_raw()
    data = { }
    if mode in ('standard', 'uncensored'):
        data[mode] = optimized[mode]
    else:
        data['standard'] = optimized['standard']
        data['uncensored'] = optimized['uncensored']
        data['customized'] = False
    _save_raw(data)
    return get_all_settings()


def model_for(role = None):
    return get_models().get(role, OPTIMIZED_STANDARD.get(role, 'qwen2.5:7b'))

