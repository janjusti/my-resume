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

To show or hide experience bullets by topic without deleting text, adjust `\readlist\renderedtags{...}` in `latex/main.tex`.

## Build

```shell
python build.py
```

PDFs are written to `output/` (`cv_eng`, `cv_ptbr`, `cv_ats_eng`, `cv_ats_ptbr`).

Optional single variant: `python build.py <altacv|altacv-ats> <0|1>` (language `0` = English, `1` = PT-BR).

## LinkedIn

Optional plain-text export for pasting sections into LinkedIn:

```shell
python scripts/cv_linkedin.py
python scripts/cv_linkedin.py --lang eng
```

## Agents

If you use Cursor or similar tools on this repo, see [AGENTS.md](AGENTS.md).
