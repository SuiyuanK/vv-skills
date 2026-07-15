#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Parser - Extract text and sections from PDF files.

Features:
  - Extract text from PDF
  - Parse IMRaD sections (Introduction, Methods, Results, Discussion)
  - Extract metadata (title, authors, abstract)
  - Summarize content

Requirements:
  pip install pymupdf

Usage:
  python pdf_parser.py paper.pdf --output text.txt
  python pdf_parser.py paper.pdf --sections --json output.json
  python pdf_parser.py paper.pdf --summarize
"""

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Error: PyMuPDF required. Install with: pip install pymupdf")
    sys.exit(1)


# Section patterns for academic papers
SECTION_PATTERNS = {
    "abstract": [
        r"^abstract\s*$",
        r"^摘要\s*$",
        r"^abstract[.:]",
    ],
    "introduction": [
        r"^1\.?\s*introduction\s*$",
        r"^introduction\s*$",
        r"^一、引言\s*$",
        r"^1\s+引言\s*$",
    ],
    "methods": [
        r"^2\.?\s*methods?\s*$",
        r"^methodology\s*$",
        r"^materials\s+and\s+methods\s*$",
        r"^二、方法\s*$",
        r"^2\s+方法\s*$",
    ],
    "results": [
        r"^3\.?\s*results?\s*$",
        r"^findings\s*$",
        r"^三、结果\s*$",
        r"^3\s+结果\s*$",
    ],
    "discussion": [
        r"^4\.?\s*discussion\s*$",
        r"^conclusions?\s*$",
        r"^四、讨论\s*$",
        r"^4\s+讨论\s*$",
        r"^五、结论\s*$",
    ],
    "references": [
        r"^references?\s*$",
        r"^bibliography\s*$",
        r"^参考文献\s*$",
    ],
}


def extract_text(pdf_path: str) -> str:
    """Extract all text from PDF."""
    doc = fitz.open(pdf_path)
    text_parts = []
    for page in doc:
        text_parts.append(page.get_text())
    doc.close()
    return "\n\n".join(text_parts)


def extract_metadata(pdf_path: str) -> dict:
    """Extract metadata from PDF."""
    doc = fitz.open(pdf_path)
    meta = doc.metadata

    metadata = {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "subject": meta.get("subject", ""),
        "keywords": meta.get("keywords", ""),
        "pages": len(doc),
        "creator": meta.get("creator", ""),
        "producer": meta.get("producer", ""),
    }

    doc.close()
    return metadata


def extract_abstract(text: str) -> str:
    """Extract abstract from paper text."""
    lines = text.split("\n")
    abstract_start = None
    abstract_end = None

    for i, line in enumerate(lines):
        line_lower = line.strip().lower()

        # Find abstract start
        if abstract_start is None:
            for pattern in SECTION_PATTERNS["abstract"]:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    abstract_start = i + 1
                    break

        # Find abstract end (next section)
        elif abstract_end is None:
            for section in ["introduction", "methods"]:
                for pattern in SECTION_PATTERNS.get(section, []):
                    if re.match(pattern, line_lower, re.IGNORECASE):
                        abstract_end = i
                        break
                if abstract_end:
                    break

    if abstract_start is not None:
        if abstract_end is None:
            abstract_end = min(abstract_start + 50, len(lines))
        abstract = "\n".join(lines[abstract_start:abstract_end])
        # Clean up
        abstract = re.sub(r"\s+", " ", abstract).strip()
        return abstract[:2000]  # Limit length

    return ""


def parse_sections(text: str) -> dict:
    """Parse paper into IMRaD sections."""
    lines = text.split("\n")
    sections = {}

    current_section = "other"
    current_content = []

    for line in lines:
        line_stripped = line.strip()
        line_lower = line_stripped.lower()

        # Check if this line is a section header
        found_section = None
        for section_name, patterns in SECTION_PATTERNS.items():
            for pattern in patterns:
                if re.match(pattern, line_lower, re.IGNORECASE):
                    found_section = section_name
                    break
            if found_section:
                break

        if found_section:
            # Save previous section
            if current_content:
                sections[current_section] = "\n".join(current_content).strip()
            current_section = found_section
            current_content = []
        else:
            current_content.append(line)

    # Save last section
    if current_content:
        sections[current_section] = "\n".join(current_content).strip()

    return sections


def summarize_text(text: str, max_length: int = 500) -> str:
    """Simple extractive summarization."""
    # Split into sentences
    sentences = re.split(r'[。.!?]\s*', text)

    if len(sentences) <= 5:
        return text[:max_length]

    # Take first 3 and last 2 sentences
    selected = sentences[:3] + sentences[-2:]
    summary = ". ".join(selected)

    return summary[:max_length]


def main():
    parser = argparse.ArgumentParser(
        description="Extract text and sections from PDF files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract all text
  python pdf_parser.py paper.pdf --output text.txt

  # Extract sections as JSON
  python pdf_parser.py paper.pdf --sections --json output.json

  # Extract metadata and abstract
  python pdf_parser.py paper.pdf --metadata --abstract

  # Summarize content
  python pdf_parser.py paper.pdf --summarize
        """
    )

    parser.add_argument("pdf_path", help="Path to PDF file")
    parser.add_argument("--output", "-o", help="Output file path")
    parser.add_argument("--json", help="Output as JSON to file")
    parser.add_argument("--sections", action="store_true", help="Parse IMRaD sections")
    parser.add_argument("--metadata", action="store_true", help="Extract metadata")
    parser.add_argument("--abstract", action="store_true", help="Extract abstract")
    parser.add_argument("--summarize", action="store_true", help="Summarize content")
    parser.add_argument("--all", action="store_true", help="Extract everything")

    args = parser.parse_args()

    if not Path(args.pdf_path).exists():
        print(f"Error: File not found: {args.pdf_path}", file=sys.stderr)
        sys.exit(1)

    # Default to all extraction if no specific options
    if not any([args.sections, args.metadata, args.abstract, args.summarize, args.all]):
        args.all = True

    result = {}

    # Extract text
    print(f"Processing: {args.pdf_path}", file=sys.stderr)
    text = extract_text(args.pdf_path)

    if args.all or args.metadata:
        result["metadata"] = extract_metadata(args.pdf_path)

    if args.all or args.abstract:
        result["abstract"] = extract_abstract(text)

    if args.all or args.sections:
        result["sections"] = parse_sections(text)

    if args.all or args.summarize:
        result["summary"] = summarize_text(text)

    # Always include full text
    result["text"] = text[:10000]  # Limit for practical use
    result["text_length"] = len(text)

    # Output
    if args.json:
        with open(args.json, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print(f"Saved to {args.json}", file=sys.stderr)
    elif args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"Saved to {args.output}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
