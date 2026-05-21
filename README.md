# Auto Capture Game Script (Real Time)

Real-time game dialogue capture + translation overlay.

- Captures the screen
- Extracts text via **EasyOCR** or lets the **LLM read the image**
- Translates via **OpenRouter**
- Displays the translated text on a **PyQt6 always-on-top overlay**

## Requirements

- Python **3.10+**
- OS: tested primarily on **Windows** (uses the `keyboard` global hotkey hook)
- An **OpenRouter API key**

> Note on OCR: `ocr.py` initializes EasyOCR with `gpu=True`. If you don’t have CUDA, you may need to change it to `gpu=False`.

## Install

This repo is configured for [`uv`](https://github.com/astral-sh/uv).

```bash
uv sync
```

## Run

```bash
uv run python main.py
```

On first launch, a **Settings** dialog opens. Configure and click **Save System Settings**.

## Configuration (Settings dialog)

These values are stored via Qt `QSettings`:

- **OpenRouter API Key**
- **Model** (example suggestions)
  - `google/gemma-4-26b-a4b-it` (normally 0.00006-0.0001 usd per request)
  - `google/gemma-4-31b-it` (normally 0.00006-0.0001 usd per request but use a bit logger time)
  - `google/gemini-3.1-flash-lite` (normally 0.0003-0.0004 usd per request but more consistent and low delay)
- **Language Processing Direction**: `EN->TH`, `JP->TH`, `JP->EN`
- **Text Extraction Engine Mode**
  - `ocr`: use EasyOCR to extract text, then translate the text (use GPU, if you have no GPU It consume long time)
  - `llm`: send the cropped image to the LLM and let it read/translate directly (recommend, it have high quality)
- **Target Story Dataset (Context Tuning)**: extra prompt context from `llm_prompt.json`
- **Translation Display Box Region**
  - `ocr`: place subtitles near the detected OCR dialogue box (use GPU, if you have no GPU It consume long time)
  - `fixed`: place subtitles in a fixed region (Re commend to use this, pick/reset in settings)
- **Subtitles Display Duration (Seconds)**

## Hotkeys (defaults)

All hotkeys are configurable in Settings.

**Full Screen Translate**: capture full screen, when use in llm mode it will send full screen picture, It will see what screen is in and what character is talking(**Recommend**)
**Manual Region Translate**: drag to select a region you want to translate, use when they have many text in screen (especially in playback log or setting screen)
**Auto Segmentation Translate**: use OCR to make segmentation, use when they have high risk screen that may violate guardrail rule (use GPU if you not have one, you may use Manual Region Translate instead)
**Toggle Overlay Visibility**: toggle overlay display
**Open Settings**: Open settings
**Quit**: because it is overlay program It will run in background, this program will be close by this key

you can set at 
- one character such as `p`,`q`
- two character such as `po`,`qr` (you must push both 2 key at the same time to trigger)
- enter and space bar: `enter`,`space`

recommend for one key
- Full Screen Translate: `p` 
- Manual Region Translate: `l` (drag to select a region)
- Auto Segmentation Translate: `i`
- Toggle Overlay Visibility: `o`
- Open Settings: `s`
- Quit: `q`

recommend for two key
- Full Screen Translate: `po`
- Manual Region Translate: `pl` (drag to select a region)
- Auto Segmentation Translate: `pi`
- Toggle Overlay Visibility: `oi`
- Open Settings: `st`
- Quit: `qw` or `qr`

recommend for game automate translate almost every time
- Full Screen Translate: `enter` or `space` (depend on game you play)


## Output folders

The app writes screenshots for debugging:

- `image/raw/` – full captures
- `image/to_llm/` – cropped images sent to the LLM (or full frame for full-screen mode)

## Build an .exe (PyInstaller)

See `to_exe_guide.txt` for the full checklist. In short, you’ll typically need to:

- include the `image/` folder (and any config files you rely on)
- collect EasyOCR (and sometimes `torch` / `cv2`) submodules

## Troubleshooting

- **“No text found”**: try `Full Screen Translate`, switch extraction mode to `llm`, or use `Manual Region Translate`.
- **OpenRouter error**: verify API key and model name.
- **Windows SSL/OpenSSL issue**: `main.py` clears `SSLKEYLOGFILE` on Windows to avoid AV-related OpenSSL problems.

## License

Apache-2.0 (see `LICENSE`).
