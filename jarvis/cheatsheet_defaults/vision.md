# Vision — Quick Reference

Stored in memory namespace **`cheatsheet`** (key: `vision`). Edit in the Memory tab or say **"vision cheatsheet"**.

## Chat examples

| You say | ARIA does |
|---------|-------------|
| Attach image + "Describe this" | Image description |
| "Read all text in this image" | OCR |
| "Structured OCR" / tables in image | Structured extraction |
| "What's in the top-left?" | Region question |
| "Convert this UI to HTML" | Image-to-code |
| Attach two images + compare | Before/after compare |
| "Remember what this image says" | Vision → memory |
| Attach video + question | Frame analysis (ffmpeg) |

## Settings

- **Vision quality** in sidebar: Custom / Fast (moondream) / Quality preset.
- Default model via `JARVIS_VISION_MODEL` or GUI Model settings.

## Tips

- On 8GB GPU, prefer **llama3.2-vision** or **moondream** over heavy llava:13b.
- Use crop tool in GUI for region questions.
