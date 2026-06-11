#!/usr/bin/env python
"""Refresh the local NHIS FAQ index from an approved CDC/NCHS allowlist.

This script intentionally fetches only URLs listed in config/faq_sources.json.
It uses only the Python standard library so it can run in restricted environments.

Run:
  python scripts/build_faq_index.py

Output:
  data/faq_index/faq_index_seed.json
  tests/qc_reports/faq_index_build_report.csv

If internet access is unavailable, the script leaves the existing index in place and
writes a report explaining which source fetches failed.
"""
from __future__ import annotations
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import csv
import json
import re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "faq_sources.json"
OUT = ROOT / "data" / "faq_index" / "faq_index_seed.json"
REPORT = ROOT / "tests" / "qc_reports" / "faq_index_build_report.csv"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = False
        self.title = ""
        self.in_title = False
        self.parts: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip = True
        if tag == "title":
            self.in_title = True
        if tag in {"p", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript", "svg"}:
            self.skip = False
        if tag == "title":
            self.in_title = False
        if tag in {"p", "li", "h1", "h2", "h3", "h4"}:
            self.parts.append("\n")

    def handle_data(self, data):
        if self.skip:
            return
        text = re.sub(r"\s+", " ", data).strip()
        if not text:
            return
        if self.in_title:
            self.title += (" " + text)
        else:
            self.parts.append(text + " ")


def fetch_url(url: str, timeout: int = 20) -> tuple[str, str]:
    req = Request(url, headers={"User-Agent": "NHIS-FAQ-Indexer/0.1"})
    with urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    # CDC pages are UTF-8; replace keeps the script robust if encoding metadata varies.
    html = raw.decode("utf-8", errors="replace")
    parser = TextExtractor()
    parser.feed(html)
    title = re.sub(r"\s+", " ", parser.title).strip() or url
    text = re.sub(r"\s+", " ", " ".join(parser.parts)).strip()
    return title, text


def chunk_text(text: str, max_chars: int = 1100) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks, current = [], ""
    for sent in sentences:
        if len(sent) < 35:
            continue
        if len(current) + len(sent) + 1 <= max_chars:
            current = (current + " " + sent).strip()
        else:
            if current:
                chunks.append(current)
            current = sent
    if current:
        chunks.append(current)
    return chunks[:8]  # avoid over-indexing boilerplate from any one page


def main():
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    urls = cfg.get("allowed_sources", [])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)

    docs = []
    report_rows = []
    for url in urls:
        try:
            title, text = fetch_url(url)
            chunks = chunk_text(text)
            status = "ok" if chunks else "no_chunks"
            for i, chunk in enumerate(chunks, 1):
                docs.append({
                    "id": f"{re.sub(r'[^a-z0-9]+', '_', url.lower()).strip('_')}_{i}",
                    "title": title,
                    "url": url,
                    "source_type": "cdc_nhis_webpage",
                    "source_category": "approved_cdc_nchis_nhis_source",
                    "chunk_index": i,
                    "text": chunk,
                    "excerpt": chunk[:520],
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
                })
            report_rows.append({"url": url, "status": status, "title": title, "chunks": len(chunks), "error": ""})
        except (HTTPError, URLError, TimeoutError, Exception) as e:
            report_rows.append({"url": url, "status": "failed", "title": "", "chunks": 0, "error": repr(e)[:300]})

    with REPORT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["url", "status", "title", "chunks", "error"])
        writer.writeheader(); writer.writerows(report_rows)

    if docs:
        payload = {
            "generated_from": "approved CDC/NCHS NHIS source allowlist",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "document_count": len(docs),
            "source_count": len(urls),
            "documents": docs,
        }
        OUT.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"FAQ index refreshed: {len(docs)} chunks from {len(urls)} approved sources")
    else:
        print("No FAQ documents were refreshed. Existing index was left unchanged.")
    print(f"Report: {REPORT}")


if __name__ == "__main__":
    main()
