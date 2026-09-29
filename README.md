# My Resume

Bilingual CV (English / Brazilian Portuguese) built with LaTeX ([AltaCV](https://github.com/liantze/AltaCV)) and rendered via Docker.

## Prerequisites

- Docker (Compose v2)
- Python 3

## Setup

1. Copy and fill the env files:

```shell
cp env-examples/.eng.env .eng.env
cp env-examples/.ptbr.env .ptbr.env
```

Use `\&` in `CURRENT_POSITION` or `ATS_HEADLINE` when the text contains `&` (LaTeX).

- `CURRENT_POSITION`: tagline on the **visual** PDF (your current role).
- `ATS_HEADLINE`: plain keyword line under your name on **ATS** PDFs only.

2. Edit the CV under `latex/src/`.

## Build

```shell
python build.py
```

PDFs are written to `output/` (`cv_eng`, `cv_ptbr`, `cv_ats_eng`, `cv_ats_ptbr`).

Optional single variant: `python build.py <altacv|altacv-ats> <0|1>` (language `0` = English, `1` = PT-BR).

To hide experience bullets by topic without deleting text, adjust `\readlist\renderedtags{...}` in `latex/main.tex`.

### LinkedIn copy helper

Plain-text **About**, **experience**, and **education** for pasting into LinkedIn (`===` between section types, `---` between major roles/degrees). Uses the same `renderedtags` as the PDF; does not read `.env` (no personal data).

```shell
python scripts/cv_linkedin.py              # PT-BR (default)
python scripts/cv_linkedin.py --lang eng   # English
```
