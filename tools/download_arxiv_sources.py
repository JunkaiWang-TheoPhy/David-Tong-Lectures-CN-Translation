#!/usr/bin/env python3
"""Fetch version-pinned arXiv PDFs and original sources for local translation."""

import gzip
import hashlib
import json
import shutil
import subprocess
import tarfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath


ROOT = Path(__file__).resolve().parents[1]


def fetch(url, target):
    if target.is_file() and target.stat().st_size:
        return
    temporary = target.with_suffix(target.suffix + ".part")
    subprocess.run(
        ["curl", "--location", "--fail", "--silent", "--show-error",
         "--connect-timeout", "15", "--max-time", "90", "--retry", "1",
         url, "--output", str(temporary)],
        check=True,
    )
    temporary.replace(target)


def unpack(source, destination):
    destination.mkdir(exist_ok=True)
    if tarfile.is_tarfile(source):
        with tarfile.open(source, "r:*") as archive:
            for member in archive.getmembers():
                relative = PurePosixPath(member.name)
                if relative.is_absolute() or ".." in relative.parts:
                    raise ValueError(f"Unsafe archive path: {member.name}")
                target = destination.joinpath(*relative.parts)
                if member.isdir():
                    target.mkdir(parents=True, exist_ok=True)
                elif member.isfile():
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with archive.extractfile(member) as reader, target.open("wb") as writer:
                        shutil.copyfileobj(reader, writer)
                else:
                    raise ValueError(f"Unsupported archive member: {member.name}")
        return "tar"
    with gzip.open(source, "rb") as reader:
        content = reader.read()
    if b"\\documentclass" not in content and b"\\documentstyle" not in content:
        raise ValueError("Source is not a recognized tar archive or gzip TeX file")
    (destination / "main.tex").write_bytes(content)
    return "gzip-tex"


def artifact(path):
    return {"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def main():
    catalog = json.loads((ROOT / "catalog/arxiv-sources.json").read_text())
    output = ROOT / "downloads/arxiv"
    output.mkdir(parents=True, exist_ok=True)
    report = {"retrieved_at": datetime.now(timezone.utc).isoformat(), "sources": []}
    failures = 0
    for item in catalog["sources"]:
        record = dict(item)
        directory = output / item["slug"]
        directory.mkdir(exist_ok=True)
        try:
            pdf = directory / "lecture.pdf"
            source = directory / "source.tar.gz"
            fetch(f'https://arxiv.org/pdf/{item["arxiv_id"]}', pdf)
            if not pdf.read_bytes().startswith(b"%PDF-"):
                raise ValueError("PDF response has an invalid file signature")
            print(f'{item["slug"]}: PDF downloaded', flush=True)
            fetch(f'https://arxiv.org/src/{item["arxiv_id"]}', source)
            source_format = unpack(source, directory / "tex")
            tex_files = list((directory / "tex").rglob("*.tex"))
            if not tex_files:
                raise ValueError("No TeX files found in source")
            record.update(status="complete", source_format=source_format,
                          tex_count=len(tex_files), pdf=artifact(pdf), source=artifact(source))
            print(f'{item["slug"]}: source extracted, {len(tex_files)} TeX files', flush=True)
        except (OSError, ValueError, tarfile.TarError, subprocess.CalledProcessError) as error:
            failures += 1
            record.update(status="failed", error=str(error))
            print(f'{item["slug"]}: {error}', flush=True)
        report["sources"].append(record)
        (output / "download-report.json").write_text(json.dumps(report, indent=2) + "\n")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
