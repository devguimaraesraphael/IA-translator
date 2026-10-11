---
name: export-manuscript
description: |
  Compiles the chapters of a manuscript into epub, pdf or docx using Pandoc, either
  partial (chapter range) or complete. Use when the user asks to "export the book",
  "generate epub/pdf/docx", or "compile the manuscript". Slash form:
  `/export-manuscript`.
---

# Skill: Export Manuscript

Compiles the chapters of a fiction manuscript into a distributable file via Pandoc.

## How to use

```
/export-manuscript [format=epub|pdf|docx] [chapters=<range>] [title="<title>"]
```

**Examples:**
- `/export-manuscript format=epub` — export the complete novel as epub
- `/export-manuscript format=pdf chapters=1-10` — PDF of the first 10 chapters
- `/export-manuscript format=docx chapters=1-55 title="Title — Final Edition"`

## Prerequisites

```bash
# Install pandoc if needed
sudo apt install pandoc

# For PDF:
sudo apt install texlive-xetex
```

## Process

1. Collect chapters in order from `manuscript/chapters/chapter*.md` (or the project's equivalent)
2. Concatenate with chapter separators
3. Apply metadata from `build/metadata.yaml` (including `lang: <language-tag>` for the book's language)
4. Run pandoc with the right template

## Pandoc Commands

```bash
# EPUB
pandoc $(ls manuscript/chapters/chapter*.md | sort) \
  --metadata-file=build/metadata.yaml \
  --epub-cover-image=build/cover.jpg \
  -o build/manuscript.epub

# PDF
pandoc $(ls manuscript/chapters/chapter*.md | sort) \
  --metadata-file=build/metadata.yaml \
  --pdf-engine=xelatex \
  --template=build/template.tex \
  -o build/manuscript.pdf

# DOCX
pandoc $(ls manuscript/chapters/chapter*.md | sort) \
  --metadata-file=build/metadata.yaml \
  --reference-doc=build/template.docx \
  -o build/manuscript.docx
```

## Validation Before Exporting

- [ ] Do all chapters have status: final in the frontmatter?
- [ ] Did `check-consistency` run over the full range with no high severity?
- [ ] Is the word count reasonable for the intended genre/format?

## References

- Last step of the full workflow — see the project's writing workflow, if one exists
