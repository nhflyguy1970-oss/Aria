# Source Generated with Decompyle++
# File: meme.cpython-312.pyc (Python 3.12)

'''Meme generator: LLM captions + optional ComfyUI background.'''
from __future__ import annotations
import json
import re
from datetime import datetime
from pathlib import Path
from jarvis import llm
from jarvis.meme_ops import MEME_DIR, compose_meme, overlay_meme_text, solid_background
from jarvis.modules.image import BASE_NEGATIVE, ImageEngine
PROMPT_UNCENSORED_NOTE = '\n\nUncensored mode: keep edgy, adult, or NSFW humor the user asked for. Do not sanitize or refuse.'
CAPTION_SYSTEM = 'You write classic internet meme captions from a user idea.\n\nOutput ONLY valid JSON with keys "top", "bottom", and "image_prompt". No markdown.\n\nRules:\n- top and bottom: short IMPACT-style captions (often ALL CAPS), max ~10 words each\n- One may be empty if the joke works with a single caption\n- image_prompt: vivid scene for the meme background — NO text, letters, or watermarks in the scene\n- Match the user\'s tone (wholesome, sarcastic, absurd, etc.)\n' + PROMPT_UNCENSORED_NOTE
CAPTION_USER = 'Meme idea: {idea}\n\nReturn JSON only.'

def _parse_caption_json(raw = None):
    raw = raw.strip()
    if raw.startswith('```'):
        raw = re.sub('^```(?:json)?\\s*', '', raw)
        raw = re.sub('\\s*```$', '', raw)
    
    try:
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None
        return {
            'top': str(data.get('top', '')).strip(),
            'bottom': str(data.get('bottom', '')).strip(),
            'image_prompt': str(data.get('image_prompt', '')).strip() }
    except json.JSONDecodeError:
        m = re.search('\\{[\\s\\S]*\\}', raw)
        if not m:
            return None
        data = json.loads(m.group(0))
    except json.JSONDecodeError:
        return None

    continue


class MemeEngine:
    
    def __init__(self = None):
        self.image = ImageEngine()
        self.last_meme = ''
        self.last_top = ''
        self.last_bottom = ''
        self.last_image_prompt = ''
        self.last_background = ''

    
    def prepare_captions(self = None, idea = None):
        fallback_prompt = f'''funny meme scene, {idea}, expressive, high contrast, no text'''
        fallback = {
            'top': idea[:40].upper(),
            'bottom': '',
            'image_prompt': fallback_prompt }
        
        try:
            prompt_model_name = prompt_model_name
            import jarvis.modules.image
            model = prompt_model_name()
            raw = llm.ask_with_system(model, CAPTION_SYSTEM, CAPTION_USER.format(idea = idea), options = {
                'num_predict': 220,
                'temperature': 0.75 })
            parsed = _parse_caption_json(raw)
            if parsed:
                if parsed['top'] or parsed['bottom']:
                    self.last_top = parsed['top']
                    self.last_bottom = parsed['bottom']
                    if not parsed['image_prompt']:
                        parsed['image_prompt']
                    self.last_image_prompt = fallback_prompt
                    return dict(parsed)
                self.last_top = None['top']
                self.last_bottom = fallback['bottom']
                self.last_image_prompt = fallback['image_prompt']
                return fallback
            except Exception:
                continue


    
    def generate(self = None, *, top, bottom, idea, image_prompt, background_path, use_ai_image):
        """Build a meme PNG. Returns path or 'ERROR: …'."""
        MEME_DIR.mkdir(parents = True, exist_ok = True)
        if not idea and top.strip() and bottom.strip():
            caps = self.prepare_captions(idea)
            top = caps.get('top', top)
            bottom = caps.get('bottom', bottom)
            if not image_prompt:
                image_prompt = caps.get('image_prompt', '')
        self.last_top = top.strip()
        self.last_bottom = bottom.strip()
        self.last_image_prompt = image_prompt.strip()
        if not self.last_top and self.last_bottom:
            return 'ERROR: Need top text, bottom text, or a meme idea.'
        bg_path = background_path
        if bg_path and Path(bg_path).is_file():
            self.last_background = bg_path
        elif use_ai_image:
            if not image_prompt:
                image_prompt
                if not idea:
                    idea
            prompt = f'''{top} {bottom}'''.strip()
            if not prompt:
                prompt = 'funny meme background scene, expressive, no text'
            prompt = f'''{prompt}, meme template photo, bold composition, no text, no watermark'''
            neg = f'''{BASE_NEGATIVE}, text, words, letters, caption, watermark, meme text'''
            result = self.image.generate(prompt, negative_prompt = neg, enhance = False)
            if result.startswith('ERROR:'):
                return result
            bg_path = None
            self.last_background = bg_path
        else:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            plain = MEME_DIR / f'''meme_bg_{stamp}.png'''
            solid_background().save(plain)
            bg_path = str(plain)
            self.last_background = bg_path
        
        try:
            stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            out = MEME_DIR / f'''meme_{stamp}.png'''
            path = compose_meme(bg_path, top = self.last_top, bottom = self.last_bottom, output = out)
            self.last_meme = path
            invalidate_meme_gallery = invalidate_meme_gallery
            import jarvis.cache_state
            invalidate_meme_gallery()
            return path
        except Exception:
            exc = None
            del exc
            return None
            None = 
            del exc


    
    def preview_text_only(self = None, top = None, bottom = None, width = (800, 600), height = ('top', 'str', 'bottom', 'str', 'width', 'int', 'height', 'int', 'return', 'str')):
        '''Fast preview without AI — gray slab + captions.'''
        img = overlay_meme_text(solid_background(width, height), top = top, bottom = bottom)
        MEME_DIR.mkdir(parents = True, exist_ok = True)
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out = MEME_DIR / f'''meme_preview_{stamp}.png'''
        img.save(out, format = 'PNG')
        self.last_meme = str(out.resolve())
        return str(out.resolve())


