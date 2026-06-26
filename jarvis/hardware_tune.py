# Source Generated with Decompyle++
# File: hardware_tune.cpython-312.pyc (Python 3.12)

'''One-shot GPU tuning — env, models, audio settings (8GB AMD or 12GB NVIDIA).'''
from __future__ import annotations
import re
import subprocess
from pathlib import Path
from jarvis.config import DATA_DIR, PROJECT_ROOT
OLLAMA_12GB_PULL = ('qwen2.5:14b', 'qwen2.5-coder:14b', 'deepseek-r1:14b', 'llava:13b', 'moondream:latest', 'nomic-embed-text:latest', 'dolphin-mistral:latest')
MODEL_12GB_STANDARD = {
    'general': 'qwen2.5:14b',
    'coder': 'qwen2.5-coder:14b',
    'review': 'deepseek-r1:14b',
    'vision': 'llava:13b',
    'image': 'comfyui',
    'embed': 'nomic-embed-text:latest' }
MODEL_12GB_UNCENSORED = {
    'general': 'dolphin3:latest',
    'coder': 'qwen2.5-coder:14b',
    'review': 'dolphin3:latest',
    'vision': 'llava:13b',
    'image': 'comfyui',
    'embed': 'nomic-embed-text:latest' }
OLLAMA_12GB_UNCENSORED_EXTRA = ('dolphin3:latest', 'dolphin-mistral:latest')
ENV_12GB_DEFAULTS: 'dict[str, str]' = {
    'JARVIS_GPU_PREFER': 'nvidia',
    'JARVIS_CUDA_DEVICE': '0',
    'JARVIS_TORCH_DEVICE': 'cuda',
    'JARVIS_WHISPER_DEVICE': 'cuda',
    'JARVIS_WHISPER_COMPUTE': 'float16',
    'JARVIS_WHISPER_MODEL': 'medium',
    'JARVIS_FUNCTIONGEMMA_DEVICE': 'cuda',
    'JARVIS_VRAM_GUARD': '1',
    'JARVIS_COMFYUI_CPU': '0',
    'JARVIS_COMFYUI_INPAINT_MAX_DIM': '1536',
    'JARVIS_SONG_MODE': 'max',
    'JARVIS_SONG_VOCAL_DEVICE': 'cuda',
    'JARVIS_REASONING_MODEL': 'deepseek-r1:14b',
    'OLLAMA_KEEP_ALIVE': '30m' }
OLLAMA_8GB_PULL = ('qwen2.5:7b', 'qwen2.5-coder:7b', 'moondream:latest', 'nomic-embed-text:latest', 'dolphin-mistral:latest')
ENV_8GB_DEFAULTS: 'dict[str, str]' = {
    'JARVIS_WHISPER_MODEL': 'small',
    'JARVIS_WHISPER_DEVICE': 'cpu',
    'JARVIS_WHISPER_COMPUTE': 'int8',
    'JARVIS_VRAM_GUARD': '1',
    'JARVIS_TORCH_DEVICE': 'cuda',
    'JARVIS_ROCM_GFX': '11.0.0',
    'HSA_OVERRIDE_GFX_VERSION': '11.0.0',
    'JARVIS_COMFYUI_INPAINT_MAX_DIM': '1024',
    'JARVIS_SONG_MODE': 'auto',
    'JARVIS_SONG_VOCAL_DEVICE': 'cpu',
    'OLLAMA_KEEP_ALIVE': '15m' }

def patch_env_file(env_path = None, updates = None):
    '''Set or append export KEY="value" lines; never removes unrelated keys.'''
    changed = []
    text = env_path.read_text(encoding = 'utf-8') if env_path.is_file() else ''
    for key, value in updates.items():
        pattern = re.compile(f'''^export\\s+{re.escape(key)}=.*$''', re.MULTILINE)
        line = f'''export {key}="{value}"'''
        if pattern.search(text):
            new_text = pattern.sub(line, text)
            if new_text != text:
                changed.append(key)
            text = new_text
            continue
        if not text and text.endswith('\n'):
            text += '\n'
        text += f'''\n# 8GB tune\n{line}\n'''
        changed.append(key)
    env_path.parent.mkdir(parents = True, exist_ok = True)
    env_path.write_text(text, encoding = 'utf-8')
    return changed


def apply_audio_settings(*, whisper_model):
    save_settings = save_settings
    import jarvis.audio_settings
    save_settings({
        'whisper_model': whisper_model })


def apply_model_preset_fast():
    '''Apply 8GB-safe models for both standard and uncensored modes.'''
    apply_preset = apply_preset
    import jarvis.model_store
    apply_preset('quality', 'standard')
    apply_preset('quality', 'uncensored')


def apply_model_preset_12gb():
    '''Apply 12GB NVIDIA model roles (installed models resolved via model_store).'''
    update_models = update_models
    import jarvis.model_store
    for mode, preset in (('standard', MODEL_12GB_STANDARD), ('uncensored', MODEL_12GB_UNCENSORED)):
        update_models(mode, preset.copy())


def apply_vision_quality():
    save_vision_quality = save_vision_quality
    import jarvis.config
    save_vision_quality('quality')


def apply_work_profile():
    apply_profile = apply_profile
    import jarvis.profiles
    apply_profile('work')


def apply_uncensored_profile_tune(*, pull_models):
    '''GPU + NSFW checkpoints + 12GB uncensored Ollama roles when uncensored mode is on.'''
    apply_uncensored_defaults = apply_uncensored_defaults
    save_mode = save_mode
    import jarvis.comfyui_settings
    save_vision_quality = save_vision_quality
    import jarvis.config
    update_models = update_models
    import jarvis.model_store
    video_uncensored = apply_uncensored_defaults
    import jarvis.video_settings
    installed = pull_ollama_models(OLLAMA_12GB_UNCENSORED_EXTRA) if pull_models else []
    apply_model_preset_12gb()
    update_models('uncensored', MODEL_12GB_UNCENSORED.copy())
    save_vision_quality('quality')
    save_mode('gpu')
    comfy = apply_uncensored_defaults()
    video = video_uncensored()
    return {
        'ok': True,
        'ollama_pulled': installed,
        'comfyui': comfy,
        'video': video,
        'models': MODEL_12GB_UNCENSORED }


def prefetch_whisper(model = None, *, device, compute_type):
    '''Download faster-whisper weights into cache.'''
    
    try:
        WhisperModel = WhisperModel
        import faster_whisper
        WhisperModel(model, device = device, compute_type = compute_type)
        return f'''Whisper \'{model}\' cached ({device})'''
    except ImportError:
        return 'faster-whisper not installed — using CLI whisper if available'
        except Exception:
            e = None
            del e
            return None
            None = 
            del e



def pull_ollama_models(models = None):
    pulled = []
    for name in models:
        proc = subprocess.run([
            'ollama',
            'pull',
            name], capture_output = True, text = True, timeout = 3600)
        if proc.returncode == 0:
            pulled.append(name)
    continue
    return pulled
    except Exception:
        continue


def run_optimizations_12gb(*, env_path, pull_models, prefetch_whisper_model):
    if not env_path:
        env_path
    env_path = DATA_DIR / 'jarvis.env'
    env_changed = patch_env_file(env_path, ENV_12GB_DEFAULTS)
    apply_audio_settings(whisper_model = 'medium')
    apply_model_preset_12gb()
    apply_vision_quality()
    whisper_msg = prefetch_whisper('medium', device = 'cuda', compute_type = 'float16') if prefetch_whisper_model else 'skipped'
    pulled = pull_ollama_models(OLLAMA_12GB_PULL) if pull_models else []
    return {
        'ok': True,
        'env_path': str(env_path),
        'env_keys_updated': env_changed,
        'model_preset': '12gb',
        'whisper_model': 'medium',
        'whisper_prefetch': whisper_msg,
        'ollama_pulled': pulled,
        'vision_quality': 'quality' }


def run_optimizations(*, env_path, pull_models, prefetch_whisper_model):
    if not env_path:
        env_path
    env_path = DATA_DIR / 'jarvis.env'
    env_changed = patch_env_file(env_path, ENV_8GB_DEFAULTS)
    apply_audio_settings(whisper_model = 'small')
    apply_model_preset_fast()
    whisper_msg = prefetch_whisper('small') if prefetch_whisper_model else 'skipped'
    pulled = pull_ollama_models() if pull_models else []
    return {
        'ok': True,
        'env_path': str(env_path),
        'env_keys_updated': env_changed,
        'model_preset': 'fast',
        'whisper_model': 'small',
        'whisper_prefetch': whisper_msg,
        'ollama_pulled': pulled }

