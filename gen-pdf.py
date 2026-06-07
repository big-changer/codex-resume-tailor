#!/usr/bin/env python3
"""Convert an ATS-friendly Markdown resume to a text-based PDF.

This script intentionally uses only Python's standard library. It supports the
Markdown commonly used in resumes: headings, paragraphs, bullets, bold text,
and horizontal rules.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


PAGE_SIZES = {
    "letter": (612.0, 792.0),
    "a4": (595.28, 841.89),
}


@dataclass(frozen=True)
class Style:
    font: str
    size: float
    leading: float
    before: float = 0.0
    after: float = 0.0
    color: tuple[float, float, float] = (0.12, 0.15, 0.18)


@dataclass
class Block:
    kind: str
    text: str = ""
    level: int = 0


STYLES = {
    "name": Style("bold", 20.0, 23.0, after=4.0, color=(0.05, 0.16, 0.28)),
    "subtitle": Style("regular", 11.0, 14.0, after=5.0, color=(0.22, 0.29, 0.36)),
    "h2": Style("bold", 12.0, 15.0, before=9.0, after=4.0, color=(0.05, 0.16, 0.28)),
    "h3": Style("bold", 10.5, 13.0, before=6.0, after=2.0, color=(0.08, 0.13, 0.19)),
    "body": Style("regular", 9.2, 12.0, after=3.5),
    "bullet": Style("regular", 9.2, 12.0, after=2.5),
}


def pdf_escape(text: str) -> str:
    """Encode text for a PDF literal string using the WinAnsi-compatible range."""
    cleaned = (
        text.replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2018", "'")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2022", "-")
        .replace("\u00a0", " ")
    )
    data = cleaned.encode("cp1252", errors="replace")
    return (
        data.replace(b"\\", b"\\\\")
        .replace(b"(", b"\\(")
        .replace(b")", b"\\)")
        .decode("latin-1")
    )


def strip_markdown(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    return text.replace("\\|", "|").strip()


def parse_markdown(source: str) -> list[Block]:
    blocks: list[Block] = []
    paragraph: list[str] = []

    def flush_paragraph() -> None:
        if paragraph:
            blocks.append(Block("paragraph", " ".join(paragraph)))
            paragraph.clear()

    lines = source.splitlines()
    first_content = next((i for i, line in enumerate(lines) if line.strip()), None)
    in_frontmatter = first_content is not None and lines[first_content].strip() == "---"
    frontmatter_closed = not in_frontmatter

    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not frontmatter_closed:
            if line == "---" and index != first_content:
                frontmatter_closed = True
            continue

        if not line:
            flush_paragraph()
            continue
        if line in {"---", "***", "___"}:
            flush_paragraph()
            blocks.append(Block("rule"))
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            flush_paragraph()
            blocks.append(Block("heading", heading.group(2), len(heading.group(1))))
            continue

        bullet = re.match(r"^[-*+]\s+(.+)$", line)
        if bullet:
            flush_paragraph()
            blocks.append(Block("bullet", bullet.group(1)))
            continue

        paragraph.append(line)

    flush_paragraph()
    return blocks


def inline_runs(text: str, default_font: str) -> list[tuple[str, str]]:
    """Return (font, text) runs for a small, resume-focused Markdown subset."""
    text = strip_markdown(text)
    parts = re.split(r"(\*\*.+?\*\*)", text)
    runs: list[tuple[str, str]] = []
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            runs.append(("bold", part[2:-2]))
        else:
            runs.append((default_font, part.replace("**", "")))
    return runs


def text_width(text: str, size: float, bold: bool = False) -> float:
    """Estimate Helvetica text width conservatively for dependable line wrapping."""
    narrow = "fijltI.,:;'|![]()"
    wide = "MW@%&Q"
    total = 0.0
    for char in text:
        if char == " ":
            total += 0.278
        elif char in narrow:
            total += 0.28
        elif char in wide:
            total += 0.82
        elif char.isupper():
            total += 0.66
        else:
            total += 0.50
    if bold:
        total *= 1.06
    # Leave a small safety margin so a line never reaches the page edge.
    return total * size * 1.025


def wrap_runs(
    runs: Iterable[tuple[str, str]], size: float, max_width: float
) -> list[list[tuple[str, str]]]:
    words: list[tuple[str, str]] = []
    for font, text in runs:
        for word in re.findall(r"\S+|\s+", text):
            if word.isspace():
                if words:
                    words.append((font, " "))
            else:
                words.append((font, word))

    lines: list[list[tuple[str, str]]] = []
    line: list[tuple[str, str]] = []
    width = 0.0
    for font, word in words:
        word_width = text_width(word, size, font == "bold")
        if word == " " and not line:
            continue
        if line and word != " " and width + word_width > max_width:
            while line and line[-1][1] == " ":
                line.pop()
            lines.append(line)
            line = []
            width = 0.0
        line.append((font, word))
        width += word_width
    if line:
        while line and line[-1][1] == " ":
            line.pop()
        lines.append(line)
    return lines or [[("regular", "")]]


class ResumePDF:
    def __init__(self, page_size: str = "letter") -> None:
        self.width, self.height = PAGE_SIZES[page_size]
        self.margin_x = 48.0
        self.margin_top = 42.0
        self.margin_bottom = 40.0
        self.pages: list[list[str]] = []
        self.current: list[str] = []
        self.y = self.height - self.margin_top
        self.started_content = False
        self.new_page()

    @property
    def usable_width(self) -> float:
        return self.width - 2 * self.margin_x

    def new_page(self) -> None:
        if self.current:
            self.pages.append(self.current)
        self.current = []
        self.y = self.height - self.margin_top

    def ensure_space(self, required: float) -> None:
        if self.y - required < self.margin_bottom:
            self.new_page()

    def draw_rule(self) -> None:
        self.ensure_space(9.0)
        self.current.append(
            f"0.72 0.76 0.80 RG 0.6 w {self.margin_x:.2f} {self.y:.2f} m "
            f"{self.width - self.margin_x:.2f} {self.y:.2f} l S"
        )
        self.y -= 7.0

    def draw_line(
        self,
        runs: list[tuple[str, str]],
        x: float,
        y: float,
        style: Style,
        word_spacing: float = 0.0,
    ) -> None:
        r, g, b = style.color
        commands = [
            "BT",
            f"{r:.3f} {g:.3f} {b:.3f} rg",
            f"{word_spacing:.3f} Tw",
            f"1 0 0 1 {x:.2f} {y:.2f} Tm",
        ]
        active_font = ""
        for font, text in runs:
            font_name = "F2" if font == "bold" else "F1"
            if font_name != active_font:
                commands.append(f"/{font_name} {style.size:.2f} Tf")
                active_font = font_name
            commands.append(f"({pdf_escape(text)}) Tj")
        commands.append("ET")
        self.current.append(" ".join(commands))

    @staticmethod
    def distributed_word_spacing(
        line: list[tuple[str, str]], style: Style, max_width: float
    ) -> float:
        spaces = sum(text.count(" ") for _, text in line)
        if spaces < 2:
            return 0.0

        line_width = sum(
            text_width(text, style.size, font == "bold") for font, text in line
        )
        extra_per_space = (max_width - line_width) / spaces

        # Avoid visibly stretched short lines. PDF word spacing is additive.
        if 0.0 < extra_per_space <= style.size * 0.32:
            return extra_per_space
        return 0.0

    def estimate_block_height(self, block: Block) -> float:
        if block.kind == "rule":
            return 7.0
        if block.kind == "bullet":
            style = STYLES["bullet"]
            width = self.usable_width - 13.0
        elif block.kind == "heading":
            if block.level == 1:
                style = STYLES["name"]
            elif block.level == 2:
                style = STYLES["h2"]
            else:
                style = STYLES["h3"]
            width = self.usable_width
        else:
            style = STYLES["body"]
            width = self.usable_width
        lines = wrap_runs(inline_runs(block.text, style.font), style.size, width)
        return style.before + len(lines) * style.leading + style.after

    def draw_text(self, text: str, style: Style, bullet: bool = False) -> None:
        indent = 13.0 if bullet else 0.0
        max_width = self.usable_width - indent
        runs = inline_runs(text, style.font)
        lines = wrap_runs(runs, style.size, max_width)
        required = style.before + len(lines) * style.leading + style.after
        self.ensure_space(required)
        self.y -= style.before

        for index, line in enumerate(lines):
            if bullet and index == 0:
                self.draw_line([("regular", "-")], self.margin_x, self.y, style)
            word_spacing = 0.0
            if index < len(lines) - 1:
                word_spacing = self.distributed_word_spacing(line, style, max_width)
            self.draw_line(
                line,
                self.margin_x + indent,
                self.y,
                style,
                word_spacing=word_spacing,
            )
            self.y -= style.leading
        self.y -= style.after

    def render(self, blocks: list[Block]) -> None:
        seen_name = False
        for index, block in enumerate(blocks):
            if block.kind == "rule":
                self.draw_rule()
            elif block.kind == "bullet":
                self.draw_text(block.text, STYLES["bullet"], bullet=True)
            elif block.kind == "heading":
                # Avoid leaving a heading or employer name alone at a page bottom.
                following = (
                    self.estimate_block_height(blocks[index + 1])
                    if index + 1 < len(blocks)
                    else STYLES["body"].leading
                )
                heading_height = self.estimate_block_height(block)
                self.ensure_space(heading_height + following)
                if block.level == 1 and not seen_name:
                    self.draw_text(block.text, STYLES["name"])
                    seen_name = True
                elif block.level == 2:
                    self.draw_text(block.text, STYLES["h2"])
                else:
                    self.draw_text(block.text, STYLES["h3"])
            else:
                style = STYLES["subtitle"] if index == 1 and seen_name else STYLES["body"]
                self.draw_text(block.text, style)

        if self.current:
            self.pages.append(self.current)
            self.current = []

    def write(self, destination: Path, title: str) -> None:
        objects: list[bytes] = []

        def add_object(content: str | bytes) -> int:
            raw = content.encode("latin-1") if isinstance(content, str) else content
            objects.append(raw)
            return len(objects)

        catalog_id = add_object("")
        pages_id = add_object("")
        font_regular_id = add_object(
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>"
        )
        font_bold_id = add_object(
            "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>"
        )

        page_ids: list[int] = []
        for page_commands in self.pages:
            stream = "\n".join(page_commands).encode("latin-1")
            content_id = add_object(
                b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n"
                + stream
                + b"\nendstream"
            )
            page_id = add_object(
                f"<< /Type /Page /Parent {pages_id} 0 R "
                f"/MediaBox [0 0 {self.width:.2f} {self.height:.2f}] "
                f"/Resources << /Font << /F1 {font_regular_id} 0 R "
                f"/F2 {font_bold_id} 0 R >> >> "
                f"/Contents {content_id} 0 R >>"
            )
            page_ids.append(page_id)

        objects[catalog_id - 1] = f"<< /Type /Catalog /Pages {pages_id} 0 R >>".encode()
        kids = " ".join(f"{page_id} 0 R" for page_id in page_ids)
        objects[pages_id - 1] = (
            f"<< /Type /Pages /Kids [{kids}] /Count {len(page_ids)} >>".encode()
        )

        now = datetime.now(timezone.utc).strftime("D:%Y%m%d%H%M%SZ")
        info_id = add_object(
            f"<< /Title ({pdf_escape(title)}) /Author ({pdf_escape(title.split(' - ')[0])}) "
            f"/Creator (gen-pdf.py) /Producer (gen-pdf.py) /CreationDate ({now}) >>"
        )

        pdf = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = [0]
        for number, content in enumerate(objects, start=1):
            offsets.append(len(pdf))
            pdf.extend(f"{number} 0 obj\n".encode())
            pdf.extend(content)
            pdf.extend(b"\nendobj\n")

        xref_offset = len(pdf)
        pdf.extend(f"xref\n0 {len(objects) + 1}\n".encode())
        pdf.extend(b"0000000000 65535 f \n")
        for offset in offsets[1:]:
            pdf.extend(f"{offset:010d} 00000 n \n".encode())
        pdf.extend(
            f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R "
            f"/Info {info_id} 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n".encode()
        )
        destination.write_bytes(pdf)


def default_output_path(source: Path) -> Path:
    return source.with_suffix(".pdf")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Convert an ATS-friendly Markdown resume to a selectable-text PDF."
    )
    parser.add_argument("input", type=Path, help="Markdown resume file")
    parser.add_argument("-o", "--output", type=Path, help="Output PDF path")
    parser.add_argument(
        "--page-size",
        choices=sorted(PAGE_SIZES),
        default="letter",
        help="PDF page size (default: letter)",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source: Path = args.input
    destination: Path = args.output or default_output_path(source)

    if not source.is_file():
        print(f"Error: input file does not exist: {source}", file=sys.stderr)
        return 2
    if source.suffix.lower() not in {".md", ".markdown"}:
        print("Error: input file must be Markdown (.md or .markdown)", file=sys.stderr)
        return 2
    if destination.suffix.lower() != ".pdf":
        destination = destination.with_suffix(".pdf")

    markdown = source.read_text(encoding="utf-8-sig")
    blocks = parse_markdown(markdown)
    if not blocks:
        print("Error: input Markdown contains no renderable content", file=sys.stderr)
        return 2

    title_block = next((block.text for block in blocks if block.kind == "heading"), source.stem)
    destination.parent.mkdir(parents=True, exist_ok=True)
    document = ResumePDF(args.page_size)
    document.render(blocks)
    try:
        document.write(destination, f"{strip_markdown(title_block)} - Resume")
    except PermissionError:
        print(
            f"Error: cannot write {destination}. Close the PDF if it is open, "
            "or choose another path with --output.",
            file=sys.stderr,
        )
        return 2

    print(f"Created {destination} ({len(document.pages)} page(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
