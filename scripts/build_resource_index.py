#!/usr/bin/env python
"""Build the NHIS Assistant V2 local approved-resource index.

This script is the editable content workflow for participation/FAQ/resource
answers. It intentionally reads only:
  - resources/approved_urls.csv
  - resources/approved_documents/*

It does NOT make the app do live web search at runtime. Instead, it generates a
local searchable JSON index used by the app:
  - resources/generated/faq_index_seed.json

Run from the project root:
  python scripts/build_resource_index.py

Outputs:
  - resources/generated/faq_index_seed.json
  - resources/generated/resource_index_qc_report.csv
  - data/faq_index/faq_index_seed.json  (compatibility copy)
"""
from __future__ import annotations

from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from zipfile import ZipFile
from xml.etree import ElementTree as ET
from datetime import datetime, timezone
import csv
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
URLS_CSV = ROOT / "resources" / "approved_urls.csv"
DOCS_DIR = ROOT / "resources" / "approved_documents"
OUT_DIR = ROOT / "resources" / "generated"
OUT_INDEX = OUT_DIR / "faq_index_seed.json"
OUT_REPORT = OUT_DIR / "resource_index_qc_report.csv"
LEGACY_COPY = ROOT / "data" / "faq_index" / "faq_index_seed.json"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip_stack = []
        self.title = ""
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "noscript", "svg", "form"}:
            self.skip_stack.append(tag)
        if tag == "title":
            self.in_title = True
        if tag in {"main", "article", "section", "p", "li", "h1", "h2", "h3", "h4", "td", "th"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.skip_stack and tag == self.skip_stack[-1]:
            self.skip_stack.pop()
        if tag == "title":
            self.in_title = False
        if tag in {"main", "article", "section", "p", "li", "h1", "h2", "h3", "h4", "td", "th"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip_stack:
            return
        text = clean_text(data)
        if not text:
            return
        if self.in_title:
            self.title += " " + text
        else:
            self.parts.append(text + " ")


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text or "").strip()
    # Common CDC chrome fragments are better caught by chunk QC, but remove very short garbage here.
    return text


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")[:80] or "source"


def fetch_url(url: str, timeout: int = 8) -> tuple[str, str]:
    req = Request(url, headers={"User-Agent": "NHIS-Assistant-Approved-Resource-Indexer/0.2"})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    html = raw.decode("utf-8", errors="replace")
    parser = TextExtractor()
    parser.feed(html)
    title = clean_text(parser.title) or url
    text = clean_text(" ".join(parser.parts))
    return title, text


def read_docx(path: Path) -> str:
    texts = []
    with ZipFile(path) as z:
        names = [n for n in z.namelist() if n.startswith("word/") and n.endswith(".xml")]
        for name in names:
            if not (name.endswith("document.xml") or "header" in name or "footer" in name):
                continue
            root = ET.fromstring(z.read(name))
            for node in root.iter():
                if node.tag.endswith('}t') and node.text:
                    texts.append(node.text)
    return clean_text(" ".join(texts))


def read_pdf(path: Path) -> tuple[str, str | None]:
    try:
        from pypdf import PdfReader  # optional dependency for indexing only
    except Exception as e:
        return "", f"pypdf not installed; skipped PDF text extraction: {e!r}"
    try:
        reader = PdfReader(str(path))
        pages = []
        for page in reader.pages:
            try:
                pages.append(page.extract_text() or "")
            except Exception:
                continue
        return clean_text(" ".join(pages)), None
    except Exception as e:
        return "", repr(e)


def read_document(path: Path) -> tuple[str, str | None]:
    suffix = path.suffix.lower()
    try:
        if suffix == ".txt":
            return clean_text(path.read_text(encoding="utf-8", errors="replace")), None
        if suffix == ".docx":
            return read_docx(path), None
        if suffix == ".pdf":
            return read_pdf(path)
        return "", f"unsupported file type: {suffix}"
    except Exception as e:
        return "", repr(e)


def chunk_text(text: str, max_chars: int = 1300, max_chunks: int = 25) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    # Split on sentence-ish boundaries. This is intentionally simple and auditable.
    sentences = re.split(r"(?<=[.!?])\s+|\n+", text)
    chunks = []
    current = ""
    for sent in sentences:
        sent = clean_text(sent)
        if len(sent) < 25:
            continue
        if len(current) + len(sent) + 1 <= max_chars:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            current = sent
        if len(chunks) >= max_chunks:
            break
    if current and len(chunks) < max_chunks:
        chunks.append(current)
    return chunks


def load_urls() -> list[dict]:
    rows = []
    if not URLS_CSV.exists():
        return rows
    with URLS_CSV.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            enabled = str(row.get("enabled", "true")).strip().lower() not in {"0", "false", "no", "n"}
            if not enabled:
                continue
            url = str(row.get("url", "")).strip()
            if url.startswith("http"):
                rows.append({
                    "source_id": row.get("source_id") or slugify(url),
                    "title": row.get("title") or "",
                    "url": url,
                    "category": row.get("category") or "approved_url",
                    "enabled": True,
                })
    return rows


def add_chunks(docs: list[dict], source_id: str, title: str, url: str, category: str, text: str, source_type: str) -> int:
    chunks = chunk_text(text)
    now = datetime.now(timezone.utc).isoformat()
    for i, chunk in enumerate(chunks, 1):
        docs.append({
            "id": f"{slugify(source_id)}_{i}",
            "title": title or source_id,
            "url": url,
            "source_type": source_type,
            "source_category": category,
            "chunk_index": i,
            "text": chunk,
            "excerpt": chunk[:520],
            "retrieved_at": now,
        })
    return len(chunks)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    LEGACY_COPY.parent.mkdir(parents=True, exist_ok=True)

    docs: list[dict] = []
    report_rows: list[dict] = []

    for row in load_urls():
        try:
            title, text = fetch_url(row["url"])
            if row.get("title"):
                title = row["title"]
            chunks = add_chunks(docs, row["source_id"], title, row["url"], row["category"], text, "approved_html_url")
            status = "ok" if chunks else "no_chunks"
            report_rows.append({**row, "resolved_title": title, "status": status, "word_count": len(text.split()), "chunk_count": chunks, "error": ""})
        except (HTTPError, URLError, TimeoutError, Exception) as e:
            report_rows.append({**row, "resolved_title": "", "status": "failed", "word_count": 0, "chunk_count": 0, "error": repr(e)[:400]})

    for path in sorted(DOCS_DIR.iterdir() if DOCS_DIR.exists() else []):
        if path.name.startswith(".") or path.name.lower().startswith("readme"):
            continue
        text, err = read_document(path)
        chunks = add_chunks(docs, slugify(path.stem), path.stem, str(path.relative_to(ROOT)), "approved_document", text, "approved_document") if text else 0
        report_rows.append({
            "source_id": slugify(path.stem), "title": path.stem, "url": str(path.relative_to(ROOT)),
            "category": "approved_document", "enabled": True, "resolved_title": path.stem,
            "status": "ok" if chunks else "failed", "word_count": len(text.split()) if text else 0,
            "chunk_count": chunks, "error": err or "",
        })

    # If nothing indexed, do not destroy a working index.
    if docs:
        payload = {
            "generated_from": "NHIS Assistant V2 approved URLs and approved documents",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "document_count": len(docs),
            "source_count": len(report_rows),
            "documents": docs,
        }
        OUT_INDEX.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        shutil.copy2(OUT_INDEX, LEGACY_COPY)
        print(f"Resource index refreshed: {len(docs)} chunks from {len(report_rows)} sources")
    else:
        print("No resources were indexed. Existing index was left unchanged.")

    with OUT_REPORT.open("w", newline="", encoding="utf-8") as f:
        fieldnames = ["source_id", "title", "url", "category", "enabled", "resolved_title", "status", "word_count", "chunk_count", "error"]
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in report_rows:
            w.writerow({k: r.get(k, "") for k in fieldnames})
    print(f"QC report: {OUT_REPORT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
