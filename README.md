# Markdown to Image for cheatsheets

Generate a portrait image (phone-friendly) from simple markdown-like text.

Ideal to create your cheatsheets in a portable and user friendly way.

Designed for headings (starting with `= `), paragraphs, and bullet lists (`* `).

## Install

Requires Python 3.9+.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Guide (Recommended Flow)

1. Edit your input file: create or modify `inputTexts.md` at the project root.
2. Generate images: `./md_2_images.sh`
3. Open the output folder named after your input (e.g., `inputTexts/`).
4. Share the generated images to your laptop (e.g., AirDrop, cloud drive, or USB).

Tips
- If the output folder already exists, it is automatically archived to `<name>-yyyy-mm-dd` before new images are written.
- Default font is Arial on macOS (`/Library/Fonts/Arial.ttf`). You can override via `--font`.

## Features
- Title line starting with `= ` rendered large
- Paragraphs and bullet points with wrapping
- 9:16 portrait defaults (1080x1920), extends height if content needs it
- Customizable margins, colors, and font

## Advanced usage
You can alternatively run the scripts directly:
     - Or run the Python wrapper directly
		 ```bash
		 python scripts/md_2_images.py inputTexts.md
		 ```
	 - Or call the engine with options (positional input supported; `--outdir` defaults to the input filename stem):
		 ```bash
		 python scripts/md_sections_to_images.py inputTexts.md --width 1080 --height 1920 --margin 64 --bg "#111111" --fg "#ffffff"
		 ```

From a file:
```bash
python scripts/md_to_image.py -i sample.md -o output.png
```

From stdin:
```bash
echo "= Title\nParagraph.\n* bullet one\n* bullet two" | python scripts/md_to_image.py -o out.png
```

Options:
- `--width` / `--height`: default 1080x1920 (portrait). Height will grow if the content exceeds the initial height.
- `--margin`: padding around content (default 64px)
- `--bg` / `--fg`: background and text colors (hex)
- `--font`: path to a TTF/OTF font; otherwise tries common macOS fonts or falls back to PIL default.

## Notes
- For best typography, pass a font path, e.g., `/Library/Fonts/Arial.ttf` on macOS.
- Bullet text wraps with indentation and a small dot marker.

## Multiple Sections → Images

If your markdown file contains several sections, each starting with `= `, generate one image per section:

```bash
python scripts/md_sections_to_images.py -i sample.md -o output_images
```

Options mirror the single-image script:
- `--width` / `--height`: portrait size; height extends if needed.
- `--margin`: padding around content.
- `--bg` / `--fg`: colors.
- `--font`: font path.

Images are saved in the output directory using a filename derived from each section title (sanitized). If duplicate titles occur, numeric suffixes are appended.