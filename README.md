# Auto Capture Game Script (Real Time)

Real-time game dialogue capture + translation overlay for PC games.

It can:
- Capture the screen (full screen or selected region)
- Extract text via **EasyOCR** (OCR mode) or let an **LLM read the image** (LLM mode)
- Translate using **OpenRouter**
- Display translations in a **PyQt6 always-on-top overlay**

---

## Requirements

- Python **3.10+**
- **Windows recommended** (uses `keyboard` for global hotkeys; other OSes may need changes)
- An **OpenRouter API key**

> OCR note: `ocr.py` initializes EasyOCR with `gpu=True`. If you don’t have CUDA, change it to `gpu=False` (OCR will be slower).

---

## Install

This repo is configured for [`uv`](https://github.com/astral-sh/uv):

```bash
uv sync
```

---

## Run

```bash
uv run python main.py
```

On first launch, the **Settings** dialog opens. Configure values and click **Save System Settings**.

---

## Settings (Configuration)

Settings are stored using Qt `QSettings`.

### OpenRouter
- **OpenRouter API Key**
- **Model** (examples)
  - `google/gemma-4-26b-a4b-it` (normally 0.00006-0.0001 usd per request)
  - `google/gemma-4-31b-it` (normally 0.00006-0.0001 usd per request but use a bit logger time and have higher quality)
  - `google/gemini-3.1-flash-lite` (normally 0.0003-0.0004 usd per request but more consistent have higher quality and low delay)

### Translation
- **Language direction**: `EN->TH`, `JP->TH`, `JP->EN`

### Text extraction mode
- **`ocr`**: EasyOCR extracts text → send extracted text to LLM for translation  
  - Faster with GPU, slower on CPU
- **`llm`**: send the cropped image to the LLM and let it read + translate directly  
  - Usually best quality, recommended

### Context tuning (optional)
- **Target Story Dataset (Context Tuning)**: adds extra prompt context from `llm_prompt.json`

### Overlay placement
- **`ocr`**: place subtitles near the detected dialogue box (OCR-based)
- **`fixed`**: place subtitles in a fixed region (recommended; set/reset in Settings)

### Other
- **Subtitles display duration (seconds)**

---

## Hotkeys

All hotkeys are configurable in Settings.

Actions:
- **Full Screen Translate**: capture full screen (recommended for LLM mode: the model can infer context/speaker)
- **Manual Region Translate**: drag-select a region (useful when the screen has multiple text blocks)
- **Auto Segmentation Translate**: OCR-based segmentation (useful when you want to avoid sending full images to the LLM)
- **Toggle Overlay Visibility**
- **Open Settings**
- **Quit**: closes the background overlay app

Hotkey format:
- Single key: `p`, `q`, ...
- Two keys pressed together: `po`, `qr`, ...
- Special keys: `enter`, `space`

Suggested bindings (single key):
- Full Screen Translate: `p`
- Manual Region Translate: `l`
- Auto Segmentation Translate: `i`
- Toggle Overlay Visibility: `o`
- Open Settings: `s`
- Quit: `q`

Suggested bindings (two keys):
- Full Screen Translate: `po`
- Manual Region Translate: `pl`
- Auto Segmentation Translate: `pi`
- Toggle Overlay Visibility: `oi`
- Open Settings: `st`
- Quit: `qw` or `qr`

For “translate every dialogue” style automation:
- Full Screen Translate: `enter` or `space` (depends on the game controls)

---

## Prompt customization (`llm_prompt.json`)

Before sending requests to the LLM, the app appends prompts from `llm_prompt.json`.

It contains two prompt groups:
- `language_prompt`: e.g. `EN->TH`, `JP->TH`, `JP->EN`
- `specific_story_prompt`: per-game/story context (recommended to write in your target language)

---

## Output folders (debug)

The app writes screenshots for debugging:
- `image/raw/` – full captures
- `image/to_llm/` – cropped images sent to the LLM (or full frame for full-screen mode)

---

## Build an .exe (PyInstaller)

See `to_exe_guide.txt`. Typically you must:
- include the `image/` folder (and any config files you rely on)
- collect EasyOCR (and sometimes `torch` / `cv2`) submodules

---

## Troubleshooting

- **No text found**: try **Full Screen Translate**, switch extraction to **LLM**, or use **Manual Region Translate**.
- **OpenRouter error**: verify API key and model name.
- **Windows SSL/OpenSSL issue**: `main.py` clears `SSLKEYLOGFILE` on Windows to avoid some AV-related OpenSSL problems.

---

## License

Apache-2.0 (see `LICENSE`).