# Source Generated with Decompyle++
# File: vision_media.cpython-312.pyc (Python 3.12)

'''Image/video/PDF helpers for the vision module.'''
from __future__ import annotations
import io
import re
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
OCR_PROMPT = 'Read and transcribe ALL visible text in this image exactly as shown. Preserve layout with line breaks where helpful. If there is no text, say so.'
OCR_STRUCTURED_PROMPT = 'Extract all visible content from this image as structured data.\n- Use markdown tables for tabular data.\n- Use bullet lists for forms and labeled fields.\n- Wrap JSON-like key-value pairs in a ```json code block when appropriate.\n- Preserve exact text for labels, values, and headings.\n- If there is no text, say so.'
IMAGE_TO_CODE_PROMPT = 'This is a UI screenshot. Recreate it as clean, semantic HTML with embedded CSS. Match layout, colors, typography, and spacing closely. Use accessible markup. Output only a single ```html code block.'
DESCRIBE_PROMPT = 'Describe this image in detail.'
IDENTIFY_PROMPT = 'You are an expert at visual identification. Study this image carefully.\nAnswer the question with the most likely identity (species, breed, model, etc.).\nFor organisms: give common name and scientific name when possible.\nExplain the key visual features that support your answer.\nIf uncertain, give your best guess, plausible alternatives, and confidence.\n\nQuestion: {question}'
_IDENTIFY_PATTERNS = ('\\b(what|which)\\s+(species|kind|type|breed|variety|sort)\\b', '\\b(identify|identification|name (this|the|it))\\b', '\\bwhat (animal|plant|bird|insect|spider|snake|fish|tree|flower|mushroom|bug|mammal|reptile|amphibian|fungus|lichen)\\b', '\\b(is this (a|an)|tell me what (this|that|it) is)\\b', '\\bwhat is (this|that|it)\\b.*\\?', '\\b(what|which)\\s+(bird|tree|flower|dog|cat|snake|spider|insect|fish)\\s+is\\b', '\\b(scientific|latin)\\s+name\\b', '\\bwhat (breed|variety) (is|of)\\b')
VIDEO_EXTENSIONS = {
    '.avi',
    '.m4v',
    '.mkv',
    '.mov',
    '.webm',
    '.mp4'}
PDF_EXTENSIONS = {
    '.pdf'}
IMAGE_EXTENSIONS = {
    '.bmp',
    '.gif',
    '.png',
    '.jpeg',
    '.webp',
    '.jpg'}
REGION_PRESETS: 'dict[str, dict[str, float]]' = {
    'top left': {
        'x': 0,
        'y': 0,
        'w': 0.5,
        'h': 0.5 },
    'top-left': {
        'x': 0,
        'y': 0,
        'w': 0.5,
        'h': 0.5 },
    'top right': {
        'x': 0.5,
        'y': 0,
        'w': 0.5,
        'h': 0.5 },
    'top-right': {
        'x': 0.5,
        'y': 0,
        'w': 0.5,
        'h': 0.5 },
    'bottom left': {
        'x': 0,
        'y': 0.5,
        'w': 0.5,
        'h': 0.5 },
    'bottom-left': {
        'x': 0,
        'y': 0.5,
        'w': 0.5,
        'h': 0.5 },
    'bottom right': {
        'x': 0.5,
        'y': 0.5,
        'w': 0.5,
        'h': 0.5 },
    'bottom-right': {
        'x': 0.5,
        'y': 0.5,
        'w': 0.5,
        'h': 0.5 },
    'center': {
        'x': 0.25,
        'y': 0.25,
        'w': 0.5,
        'h': 0.5 },
    'middle': {
        'x': 0.25,
        'y': 0.25,
        'w': 0.5,
        'h': 0.5 } }

def vision_task_for_question(question = None):
    '''Return vision task tier key: identify (heavy) or describe (light).'''
    if not question:
        question
    lower = ''.lower().strip()
    if not lower:
        return 'describe'
    for pattern in _IDENTIFY_PATTERNS:
        if not re.search(pattern, lower):
            continue
        _IDENTIFY_PATTERNS
        return 'identify'
    return 'describe'


def build_vision_prompt(question = None, task = None):
    if task == 'identify':
        return IDENTIFY_PROMPT.format(question = question.strip())


def apply_crop_bytes(content = None, crop = None):
    '''Crop image bytes. crop: {x, y, w, h} as fractions 0–1.'''
    if not crop:
        return content
    Image = Image
    import PIL
    x = float(crop.get('x', 0))
    y = float(crop.get('y', 0))
    w = float(crop.get('w', 1))
    h = float(crop.get('h', 1))
    opened = Image.open(io.BytesIO(content))
    rgb = opened.convert('RGB')
    (width, height) = rgb.size
    left = max(0, min(width - 1, int(x * width)))
    top = max(0, min(height - 1, int(y * height)))
    right = max(left + 1, min(width, int((x + w) * width)))
    bottom = max(top + 1, min(height, int((y + h) * height)))
    cropped = rgb.crop((left, top, right, bottom))
    out = io.BytesIO()
    cropped.save(out, format = 'JPEG', quality = 90, optimize = True)
    None(None, None)
    return 
    with None:
        if not None, out.getvalue():
            pass


def parse_video_second(message = None, explicit = None):
    pass
# WARNING: Decompyle incomplete


def extract_video_frame(content = None, filename = None, second = None):
    '''Extract one JPEG frame from video bytes (requires ffmpeg).'''
    if not Path(filename).suffix.lower():
        Path(filename).suffix.lower()
    ext = '.mp4'
    if ext not in VIDEO_EXTENSIONS:
        ext = '.mp4'
    td = tempfile.TemporaryDirectory()
    inp = Path(td) / f'''input{ext}'''
    out = Path(td) / 'frame.jpg'
    inp.write_bytes(content)
    cmd = [
        'ffmpeg',
        '-y',
        '-loglevel',
        'error',
        '-ss',
        str(max(0, second)),
        '-i',
        str(inp),
        '-vframes',
        '1',
        str(out)]
    proc = subprocess.run(cmd, capture_output = True, timeout = 120)
    if not proc.returncode != 0 or out.exists():
        if not proc.stderr:
            proc.stderr
        err = b''.decode(errors = 'ignore').strip()
        if not err:
            err
        raise ValueError('Could not extract video frame — is ffmpeg installed?')
    None(None, None)
    return 
    with None:
        if not None, (out.read_bytes(), f'''frame_{int(second)}s.jpg'''):
            pass


def extract_pdf_page(content = None, filename = None, page = None):
    '''Render a PDF page to JPEG bytes.'''
    page = max(1, int(page))
    if not Path(filename).stem:
        Path(filename).stem
    stem = 'document'
    
    try:
        import fitz
        doc = fitz.open(stream = content, filetype = 'pdf')
        
        try:
            if page > doc.page_count:
                raise ValueError(f'''PDF has {doc.page_count} page(s); page {page} not found.''')
            pix = doc.load_page(page - 1).get_pixmap(matrix = fitz.Matrix(2, 2))
            
            try:
                doc.close()
                return (pix.tobytes('jpeg'), f'''{stem}_p{page}.jpg''')
                doc.close()
                
                try:
                    pass
                except ImportError:
                    pass

                td = tempfile.TemporaryDirectory()
                pdf_path = Path(td) / 'input.pdf'
                pdf_path.write_bytes(content)
                out_prefix = Path(td) / 'page'
                cmd = [
                    'pdftoppm',
                    '-jpeg',
                    '-f',
                    str(page),
                    '-l',
                    str(page),
                    '-r',
                    '150',
                    str(pdf_path),
                    str(out_prefix)]
                proc = subprocess.run(cmd, capture_output = True, timeout = 120)
                out_file = Path(td) / f'''page-{page:02d}.jpg'''
                if not proc.returncode != 0 or out_file.exists():
                    candidates = list(Path(td).glob('page*.jpg'))
                    if not candidates:
                        if not proc.stderr:
                            proc.stderr
                        err = b''.decode(errors = 'ignore').strip()
                        if not err:
                            err
                        raise ValueError('PDF render failed — install pymupdf (`pip install pymupdf`) or poppler-utils')
                    out_file = candidates[0]



    None(None, None)
    return 
    with None:
        if not None, (out_file.read_bytes(), f'''{stem}_p{page}.jpg'''):
            pass


def parse_region(message = None, crop = None):
    if crop:
        return crop
    if not None:
        pass
    lower = ''.lower()
    for key, region in REGION_PRESETS.items():
        if not key in lower:
            continue
        
        return REGION_PRESETS.items(), region.copy()
# WARNING: Decompyle incomplete


def build_visual_diff(path1 = None, path2 = None, out_dir = None):
    '''Pixel-diff highlight image saved under out_dir (uploads).'''
    
    try:
        Image = Image
        ImageChops = ImageChops
        ImageEnhance = ImageEnhance
        import PIL
        out_dir.mkdir(parents = True, exist_ok = True)
        raw1 = Image.open(path1)
        raw2 = Image.open(path2)
        w = min(raw1.width, raw2.width)
        h = min(raw1.height, raw2.height)
        if w < 2 or h < 2:
            None(None, None)
            None(None, None)
            return None
        a = raw1.convert('RGB').resize((w, h))
        b = raw2.convert('RGB').resize((w, h))
        diff = ImageChops.difference(a, b)
        diff = ImageEnhance.Brightness(diff).enhance(3)
        gap = 6
        canvas = Image.new('RGB', (w * 3 + gap * 2, h), (24, 24, 24))
        canvas.paste(a, (0, 0))
        canvas.paste(b, (w + gap, 0))
        canvas.paste(diff, (w * 2 + gap * 2, 0))
        stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        out = out_dir / f'''compare_diff_{stamp}.jpg'''
        canvas.save(out, format = 'JPEG', quality = 88, optimize = True)
        None(None, None)
        None(None, None)
        return 
    except ImportError:
        return None
        with None:
            if not None:
                pass

    None(None, None)
    return None
    with None:
        if not None:
            pass

