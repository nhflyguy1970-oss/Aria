# Gallery Implementation

**Product:** Aria Gallery — local AI image generation & stills library  
**Shortcut:** `Ctrl+Shift+G` → Gallery Home  
**Status:** Production-oriented local image product (fail-closed jobs)

## Philosophy

Gallery is Aria’s **local AI image product**. Operators generate, browse, organize, and edit stills without being forced into Chat.

| Gallery owns | Does not own |
|--------------|--------------|
| Generated stills library | Image Generation engine (prompt→PNG pipeline) |
| Editing (upscale / inpaint / img2img) | Video Studio (motion) |
| Prompt history, search, collections | Meme Studio |
| Optional Vision metadata | Documents / Memory / Chat |
| Stay-in-Gallery generate *UI* (calls shared engine) | Mission Control (health) |
| Soft delete / restricted visibility | Cloud sync / Google Photos |

Generation itself is owned by **Image Generation** (`jarvis/image_generation/`) —
Gallery is the primary surface that enqueues the shared `generate_image` job.

## Architecture

```
UI: Gallery Home (gallery_view.js)
  Generation · Library · Image Engine · Editing · Prompt history
        ↓
API: /api/gallery*  + /api/image/*  + /api/media/job/*
        ↓
jarvis/gallery_product/
  library.py inventory.py soft_delete.py metadata.py
  search.py collections.py visibility.py generate.py
  home.py activity_bridge.py similarity.py storyboard.py
  voice_bridge.py vision_to_coding.py api.py
        ↓
media_jobs → MediaHandler → ImageEngine / ComfyUI → data/generated/
```

## Generation workflow

1. Enter prompt in Gallery  
2. `POST /api/gallery/generate` enqueues `generate_image` (same queue as Chat)  
3. UI polls `/api/media/job/{id}` until **done**  
4. Grid refreshes — Gallery stays open  

Never report completion until the job finishes.

## Library

- Pagination (`offset` / `limit`) — no hard 50 cliff  
- Default inventory excludes artifacts (keyframes, meme backgrounds, temps)  
- Search: filename + prompt + tags + optional vision captions  
- Soft delete → trash → undo → purge  
- Per-project optional `data/projects/{slug}/images/`

## Metadata (opt-in)

Never auto-index everything. Operators can:

- Generate Vision metadata per image  
- Edit / delete / export metadata  
- Search without requiring metadata  

## Censored / uncensored

Images created while Aria is uncensored are tagged. In **censored** profile:

- Thumbs show a restricted placeholder  
- Captions / prompts / vision text are not exposed  
- Original files are not moved or deleted  

## Integrations

| Product | Integration |
|---------|-------------|
| Job Center | Shared media job queue |
| Activity | Gallery events (video uses `video` category) |
| Models | Image Engine / vision roles |
| Projects | Optional `images/` subdir |
| Video | Storyboard path suggestion (never auto-creates video) |
| Documents | Save caption (Documents owns storage) |
| Coding | Vision→Coding proposal only |
| Mission Control | ComfyUI health via Image Engine link |

## Accessibility

- Arrow keys, Enter, Delete, Escape on library grid  
- Multi-select (Ctrl/Cmd, Shift)  
- ARIA listbox / labels / live regions  
- Restricted images announced without content leak  

## Testing

```bash
.venv/bin/python -m pytest tests/test_gallery_product.py -q
```

## Roadmap

- Richer outpaint / mask canvas  
- Embedding similarity (optional model)  
- Stronger multimodal caption path  
- Session restore of selection / filters  

## Do not build

Google Photos clone · cloud sync · silent metadata · silent Memory ingest · second generation stack · absorbing Video/Meme.
