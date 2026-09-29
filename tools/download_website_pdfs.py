#!/usr/bin/env python3
"""Discover full lecture PDFs from Tong's official teaching index."""

import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse

ROOT = Path(__file__).resolve().parents[1]
BASE = "https://davidtong.org"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current = None

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.current = dict(attrs)
            self.current["text"] = ""

    def handle_data(self, data):
        if self.current is not None:
            self.current["text"] += data

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            self.current["text"] = " ".join(self.current["text"].split())
            self.links.append(self.current)
            self.current = None


def get(url, destination):
    if not destination.exists():
        part = destination.with_suffix(destination.suffix + ".part")
        subprocess.run(["curl", "-L", "--fail", "-sS", "--connect-timeout", "15",
                        "--max-time", "60", "--retry", "1", url, "-o", str(part)], check=True)
        part.replace(destination)
    return destination.read_bytes()


def parse(content):
    parser = Links()
    parser.feed(content.decode("utf-8"))
    return parser.links


def course(link):
    url = urljoin(BASE, link["href"])
    slug = urlparse(url).path.strip("/").split("/")[-1]
    directory = ROOT / "downloads/website" / slug
    directory.mkdir(parents=True, exist_ok=True)
    record = {"slug": slug, "title": link["text"], "course_url": url, "pdfs": []}
    try:
        links = parse(get(url, directory / "course.html"))
        full = [item for item in links if "pill-link" in item.get("class", "").split()
                and urlparse(item.get("href", "")).path.lower().endswith(".pdf")]
        if not full:
            raise ValueError("Course page has no full-lecture PDF action")
        for item in full:
            pdf_url = urljoin(url, item["href"])
            path = directory / Path(urlparse(pdf_url).path).name
            data = get(pdf_url, path)
            if not data.startswith(b"%PDF-"):
                raise ValueError(f"Invalid PDF: {pdf_url}")
            record["pdfs"].append({"url": pdf_url, "label": item["text"],
                                   "path": str(path.relative_to(ROOT)), "bytes": len(data),
                                   "sha256": hashlib.sha256(data).hexdigest()})
        record["status"] = "complete"
        print(f'{slug}: {len(full)} full PDFs downloaded', flush=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        record.update(status="failed", error=str(error))
        print(f'{slug}: {error}', flush=True)
    return record


def main():
    directory = ROOT / "downloads/website"
    directory.mkdir(parents=True, exist_ok=True)
    links = parse(get(BASE + "/teaching/", directory / "teaching.html"))
    courses = {item["href"]: item for item in links
               if "course-nav-link" in item.get("class", "").split()}
    if not courses:
        raise ValueError("No courses found in the official index")
    print(f"Official teaching index: {len(courses)} courses", flush=True)
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(course, courses.values()))
    report = {"retrieved_at": datetime.now(timezone.utc).isoformat(),
              "index_url": BASE + "/teaching/", "courses": records}
    (directory / "download-report.json").write_text(json.dumps(report, indent=2) + "\n")
    (ROOT / "catalog/website-sources.json").write_text(json.dumps(report, indent=2) + "\n")
    return 1 if any(item["status"] != "complete" for item in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
