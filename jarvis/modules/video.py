# Source Generated with Decompyle++
# File: video.cpython-312.pyc (Python 3.12)

'''Video generation and prompt expansion for Jarvis Video studio.'''
from __future__ import annotations
import json
import os
import re
from jarvis import llm
from jarvis.comfyui_video import generate_motion_clip
from jarvis.video_ops import ensure_dirs
PROMPT_SYSTEM = 'You convert casual video requests into prompts for AI video generation.\n\nOutput ONLY valid JSON: {"positive": "...", "negative": "..."}\n\npositive: vivid scene with clear subject action and motion (walking, turning, wind, water, gestures), lighting, composition.\nnegative: defects to avoid; empty string if none.\n'
PROMPT_UNCENSORED = '\n\nUncensored: preserve all explicit or adult details. No refusal or sanitization.'

def prompt_model_name():
    return VideoEngine()._prompt_model()


class VideoEngine:
    
    def __init__(self = None):
        ensure_dirs()
        self.last_enhanced_prompt = ''
        self.last_negative_prompt = ''
        self.last_video = ''
        self.last_keyframe = ''
        self.last_method = 'ken_burns'
        self.last_fallback_reason = ''

    
    def _prompt_model(self = None):
        env = os.getenv('JARVIS_VIDEO_PROMPT_MODEL', '').strip()
        if env:
            return env
        
        try:
            is_uncensored = is_uncensored
            import jarvis.config
            get_models = get_models
            import jarvis.model_store
            if is_uncensored():
                return get_models().get('general', 'dolphin-mistral:latest')
            return 'qwen2.5:7b'
        except Exception:
            return 'qwen2.5:7b'


    
    def prepare_prompt(self = None, user_prompt = None):
        is_uncensored = is_uncensored
        import jarvis.config
        if not user_prompt:
            user_prompt
        user_prompt = ''.strip()
        if not user_prompt:
            return ('', '')
        system = PROMPT_SYSTEM + PROMPT_UNCENSORED if is_uncensored() else ''
        
        try:
            raw = llm.ask(self._prompt_model(), [
                {
                    'role': 'system',
                    'content': system },
                {
                    'role': 'user',
                    'content': f'''Video request: {user_prompt}\n\nReturn JSON only.''' }])
            m = re.search('\\{[\\s\\S]*\\}', raw)
            if m:
                data = json.loads(m.group(0))
                if not str(data.get('positive', '')).strip():
                    str(data.get('positive', '')).strip()
                pos = user_prompt
                neg = str(data.get('negative', '')).strip()
                self.last_enhanced_prompt = pos
                self.last_negative_prompt = neg
                return (pos, neg)
            self.last_enhanced_prompt = user_prompt
            self.last_negative_prompt = ''
            return (user_prompt, '')
        except Exception:
            continue


    
    def generate(self = None, prompt = None):
        invalidate_video_gallery = invalidate_video_gallery
        import jarvis.cache_state
        prepare_for_comfyui = prepare_for_comfyui
        import jarvis.vram_guard
        prepare_for_comfyui()
        (pos, neg) = self.prepare_prompt(prompt)
        if not pos:
            return 'ERROR: Empty video prompt'
        (result, keyframe, method) = generate_motion_clip(pos, negative_prompt = neg)
        if result.startswith('ERROR:'):
            return result
        self.last_video = None
        self.last_keyframe = keyframe
        self.last_method = method
        last_fallback_reason = last_fallback_reason
        import jarvis.comfyui_video
        self.last_fallback_reason = last_fallback_reason()
        invalidate_video_gallery()
        return result


