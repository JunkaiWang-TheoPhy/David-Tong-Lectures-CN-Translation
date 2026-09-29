<p align="center"><a href="README.md">🇺🇸 English</a> | <a href="README.zh.md">🇨🇳 中文</a></p>

<h1 align="center">David Tong Lectures CN Translation</h1>

<p align="center"><img alt="Public" src="https://img.shields.io/badge/visibility-public-blue"> <img alt="Original tools: Apache-2.0" src="https://img.shields.io/badge/original_tools-Apache--2.0-blue"></p>

![English and Chinese physics pages in an open book](assets/banner.png)

## Introduction

This community project aims to translate David Tong's publicly available lecture notes into Chinese, preserving their physical meaning, equations, notation, and explanatory voice. It is an independent initiative.

Original sources: [David Tong's official teaching directory](https://davidtong.org/teaching/).

## Lecture Collection

The [course index](catalog/README.md) covers 23 courses. The local collection contains 24 full-course website PDFs and three version-pinned arXiv editions with their original source archives and extracted TeX.

## Workflow

Each chapter progresses through source verification, first translation, physics review, Chinese-language review, compilation checks, and release. See [translation rules](docs/translation-rules.md).

The [arXiv source catalog](catalog/arxiv-sources.json) pins lecture versions. Run `python3 tools/download_arxiv_sources.py` to save PDFs, original source archives, and extracted TeX under `downloads/arxiv/`. A local report records checksums and file counts.

Run `python3 tools/download_website_pdfs.py` to retrieve the official full-course PDFs under `downloads/website/`. The [website source catalog](catalog/website-sources.json) records URLs, retrieval time, file sizes, and checksums. Downloaded originals are kept locally; the repository provides the reproducible retrieval scripts and source indexes.

## Structure

- `catalog/`: source inventory and versions
- `glossary/`: shared and course-specific terminology
- `lectures/`: one directory per course, with chapter sources and review records
- `tools/`: build and consistency utilities
- `docs/`: workflow and permissions

## Licensing

Apache-2.0 applies to original project tools and configuration. It does not grant rights to David Tong's lecture notes, translations derived from them, or third-party figures. See [licensing scope](docs/licensing.md) and [LICENSE](LICENSE).
