#!/usr/bin/env python3

import argparse
import os
import re
import shutil
from datetime import datetime
from typing import List
from PIL import Image, ImageDraw, ImageFont


class Block:
    def __init__(self, kind: str, text: str):
        self.kind = kind  # 'title', 'bullet', 'paragraph', 'spacer'
        self.text = text


def parse_markdown_lines(lines: List[str]) -> List[Block]:
    blocks: List[Block] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            blocks.append(Block('spacer', ''))
            continue
        if line.startswith('= '):
            blocks.append(Block('title', line[2:].strip()))
        elif line.lstrip().startswith('* '):
            leading = len(line) - len(line.lstrip())
            blocks.append(Block('bullet', ' ' * leading + line.lstrip()[2:].strip()))
        else:
            blocks.append(Block('paragraph', line.strip()))
    return blocks


def load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    candidates = [
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/SFNSText.ttf",
        "/Library/Fonts/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for cand in candidates:
        if os.path.exists(cand):
            try:
                return ImageFont.truetype(cand, size)
            except Exception:
                continue
    return ImageFont.load_default()


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int) -> List[str]:
    words = text.split()
    lines: List[str] = []
    current: List[str] = []

    for w in words:
        test = (" ".join(current + [w])).strip()
        if not test:
            current.append(w)
            continue
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            current.append(w)
        else:
            lines.append(" ".join(current))
            current = [w]
    if current:
        lines.append(" ".join(current))
    return lines


def draw_mixed_parentheses_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    normal_font: ImageFont.ImageFont,
    paren_font: ImageFont.ImageFont,
    fill: str,
) -> None:
    # Split text into segments inside and outside parentheses, supporting nesting
    segments: List[tuple[bool, str]] = []  # (is_parentheses, segment_text)
    buf: List[str] = []
    depth = 0
    in_paren = False
    for ch in text:
        if ch == '(': 
            if not in_paren:
                if buf:
                    segments.append((False, ''.join(buf)))
                    buf = []
                in_paren = True
            depth += 1
            buf.append(ch)
        elif ch == ')':
            if in_paren:
                buf.append(ch)
                depth = max(0, depth - 1)
                if depth == 0:
                    segments.append((True, ''.join(buf)))
                    buf = []
                    in_paren = False
            else:
                buf.append(ch)
        else:
            buf.append(ch)
    if buf:
        segments.append((in_paren, ''.join(buf)))

    cx = x
    for is_paren, seg_text in segments:
        f = paren_font if is_paren else normal_font
        cy = y + (normal_font.size - paren_font.size) if is_paren else y
        if seg_text:
            draw.text((cx, cy), seg_text, font=f, fill=fill)
            bbox = draw.textbbox((cx, cy), seg_text, font=f)
            seg_w = bbox[2] - bbox[0]
            cx += seg_w


def wrap_text_with_paren_mode(
    draw: ImageDraw.ImageDraw,
    text: str,
    normal_font: ImageFont.ImageFont,
    paren_font: ImageFont.ImageFont,
    max_width: int,
) -> List[tuple[str, bool]]:
    """Wrap text into lines while tracking parentheses depth.
    Lines that begin inside parentheses (depth > 0) are marked to render
    uniformly with the reduced parentheses font.
    Returns list of (line_text, use_paren_font).
    """
    tokens = re.findall(r"\S+|\s+", text)
    lines: List[tuple[str, bool]] = []
    current = ""
    depth = 0
    current_paren_mode = depth > 0

    def paren_delta(tok: str) -> int:
        return tok.count("(") - tok.count(")")

    for tok in tokens:
        font = paren_font if current_paren_mode else normal_font
        test = (current + tok)
        bbox = draw.textbbox((0, 0), test, font=font)
        width = bbox[2] - bbox[0]
        if width <= max_width or not current:
            current = test
            depth += paren_delta(tok)
        else:
            lines.append((current.rstrip(), current_paren_mode))
            current = tok
            # line starts with current depth
            current_paren_mode = depth > 0
            depth += paren_delta(tok)

    if current:
        lines.append((current.rstrip(), current_paren_mode))
    return lines


def render_blocks_to_image(
    blocks: List[Block],
    out_path: str,
    width: int = 1080,
    height: int = 1920,
    margin: int = 64,
    bg_color: str = "#111111",
    text_color: str = "#ffffff",
    bullet_color: str = "#ffffff",
    font_path: str | None = None,
    parenthesis_font: ImageFont.ImageFont | None = None,
) -> None:
    scale = 1.2  # For future scaling support
    title_line_spacing = 40 * scale
    title_after_spacing = 100 * scale
    body_line_spacing = 30 * scale
    body_after_spacing = 50 * scale
    bullet_line_spacing = 30 * scale
    bullet_item_spacing = 100 * scale
    title_font = load_font(font_path, 100* scale)
    body_font = load_font(font_path, 40 * scale)
    bullet_font = load_font(font_path, 70 * scale)

    # Paragraph and list spacings are controlled via function parameters

    # Derive parentheses fonts per context if not provided
    title_paren_font = parenthesis_font or load_font(font_path, max(10, int(title_font.size * 0.5)))
    body_paren_font = parenthesis_font or load_font(font_path, max(10, int(body_font.size * 0.5)))
    bullet_paren_font = parenthesis_font or load_font(font_path, max(10, int(bullet_font.size * 0.5)))

    bullet_indent = 40 * scale
    bullet_radius = 10 * scale

    img = Image.new("RGB", (width, height), color=bg_color)
    draw = ImageDraw.Draw(img)

    x = margin
    y = margin
    max_text_width = width - 2 * margin - bullet_indent

    for idx, b in enumerate(blocks):
        next_kind = blocks[idx + 1].kind if (idx + 1) < len(blocks) else None
        if b.kind == 'title':
            wrapped = wrap_text_with_paren_mode(draw, b.text, title_font, title_paren_font, width - 2 * margin)
            for i, (line, use_paren) in enumerate(wrapped):
                line_font = title_paren_font if use_paren else title_font
                if use_paren:
                    draw.text((x, y), line, font=line_font, fill=text_color)
                else:
                    draw_mixed_parentheses_text(draw, x, y, line, title_font, title_paren_font, text_color)
                bbox = draw.textbbox((x, y), line, font=line_font)
                line_h = bbox[3] - bbox[1]
                if i < len(wrapped) - 1:
                    y += line_h + title_line_spacing
                else:
                    y += line_h + title_after_spacing
        elif b.kind == 'paragraph':
            wrapped = wrap_text_with_paren_mode(draw, b.text, body_font, body_paren_font, width - 2 * margin)
            for i, (line, use_paren) in enumerate(wrapped):
                line_font = body_paren_font if use_paren else body_font
                if use_paren:
                    draw.text((x, y), line, font=line_font, fill=text_color)
                else:
                    draw_mixed_parentheses_text(draw, x, y, line, body_font, body_paren_font, text_color)
                bbox = draw.textbbox((x, y), line, font=line_font)
                line_h = bbox[3] - bbox[1]
                if i < len(wrapped) - 1:
                    y += line_h + body_line_spacing
                else:
                    y += line_h + body_after_spacing
        elif b.kind == 'bullet':
            bullet_text_x = x + bullet_indent
            wrapped = wrap_text_with_paren_mode(draw, b.text, bullet_font, bullet_paren_font, max_text_width)
            for i, (line, use_paren) in enumerate(wrapped):
                line_font = bullet_paren_font if use_paren else bullet_font
                # Measure line first to align the bullet vertically at half line height
                bbox = draw.textbbox((bullet_text_x, y), line, font=line_font)
                line_h = bbox[3] - bbox[1]
                if i == 0:
                    dot_x = x
                    dot_y = y + (line_h // 2) + bullet_radius
                    draw.ellipse((dot_x - bullet_radius, dot_y - bullet_radius, dot_x + bullet_radius, dot_y + bullet_radius), fill=bullet_color)

                if use_paren:
                    draw.text((bullet_text_x, y), line, font=line_font, fill=text_color)
                else:
                    draw_mixed_parentheses_text(draw, bullet_text_x, y, line, bullet_font, bullet_paren_font, text_color)

                if i < len(wrapped) - 1:
                    y += line_h + bullet_line_spacing
                else:
                    # Between list items vs after the last list item
                    if next_kind == 'bullet':
                        y += line_h + bullet_item_spacing
                    else:
                        y += line_h + body_after_spacing
        elif b.kind == 'spacer':
            y += body_font.size // 2

        if y > img.height - margin:
            extra = max(margin + 200, y - img.height + margin)
            ext = Image.new("RGB", (img.width, img.height + extra), color=bg_color)
            ext.paste(img, (0, 0))
            img = ext
            draw = ImageDraw.Draw(img)

    img.save(out_path)


def split_into_sections(lines: List[str]) -> List[List[str]]:
    sections: List[List[str]] = []
    current: List[str] = []
    for raw in lines:
        line = raw.rstrip("\n")
        if line.startswith('= '):
            if current:
                sections.append(current)
            current = [line]
        else:
            if current:
                current.append(line)
            else:
                # Ignore leading content until first title
                continue
    if current:
        sections.append(current)
    return sections


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-zA-Z0-9]+", "_", title).strip("_")
    return slug or "section"


def unique_outpath(out_dir: str, base: str) -> str:
    path = os.path.join(out_dir, f"{base}.png")
    if not os.path.exists(path):
        return path
    i = 2
    while True:
        candidate = os.path.join(out_dir, f"{base}_{i}.png")
        if not os.path.exists(candidate):
            return candidate
        i += 1


def main():
    parser = argparse.ArgumentParser(description="Render multiple markdown-like sections to individual images")
    # Accept positional input path or -i/--input; enforce presence after parsing
    parser.add_argument("input", nargs="?", help="Path to markdown text file with multiple sections starting with '= '")
    parser.add_argument("--input", "-i", dest="input", help="Path to markdown text file with multiple sections starting with '= '")
    parser.add_argument("--outdir", "-o", default=None, help="Directory to write images (default: input file name without extension; will be created if missing)")
    parser.add_argument("--width", type=int, default=1080, help="Image width (portrait)")
    parser.add_argument("--height", type=int, default=1920, help="Initial image height (extends if content exceeds)")
    parser.add_argument("--margin", type=int, default=64, help="Margin in pixels")
    parser.add_argument("--bg", default="#111111", help="Background color (e.g. #111111)")
    parser.add_argument("--fg", default="#ffffff", help="Text color (e.g. #ffffff)")
    parser.add_argument("--font", default="/Library/Fonts/Arial.ttf", help="Path to a TTF/OTF font file (default: /Library/Fonts/Arial.ttf)")

    args = parser.parse_args()
    if not args.input:
        parser.error("the following argument is required: input (positional) or --input/-i")
    # If outdir wasn't provided, derive from input filename (without extension)
    if args.outdir is None:
        base = os.path.splitext(os.path.basename(args.input))[0]
        args.outdir = base or "output_images"

    with open(args.input, "r", encoding="utf-8") as f:
        lines = f.readlines()

    sections = split_into_sections(lines)
    if not sections:
        raise SystemExit("No sections found. Ensure lines starting with '= ' mark each section.")

    # If output directory exists, archive it by appending date and time (yyyy-mm-dd-HH-MM)
    if os.path.isdir(args.outdir):
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        base_dir = args.outdir.rstrip("/")
        archived = f"{base_dir}-{timestamp}"
        i = 2
        while os.path.exists(archived):
            archived = f"{base_dir}-{timestamp}_{i}"
            i += 1
        shutil.move(args.outdir, archived)
        print(f"Archived existing output directory to {archived}")

    os.makedirs(args.outdir, exist_ok=True)

    for idx, sec_lines in enumerate(sections, start=1):
        blocks = parse_markdown_lines(sec_lines)
        # Find title to generate filename
        title_text = None
        for b in blocks:
            if b.kind == 'title':
                title_text = b.text
                break
        base = slugify(title_text) if title_text else f"section_{idx}"
        out_path = unique_outpath(args.outdir, base)
        render_blocks_to_image(
            blocks,
            out_path=out_path,
            width=args.width,
            height=args.height,
            margin=args.margin,
            bg_color=args.bg,
            text_color=args.fg,
            bullet_color=args.fg,
            font_path=args.font,
        )
        print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
