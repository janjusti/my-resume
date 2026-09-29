# Guidance for coding agents

Public bilingual LaTeX CV. Personal data lives in local `.env` files and generated PDFs — both are listed in `.gitignore` (`*.env`, `output/`). Do not `git add -f` those paths or ask the user to commit them.

## Do not

- Run `git commit` / `git push` unless the user explicitly asks (see workspace rules).
- Re-introduce automated “headline generator” scripts that infer a fixed keyword line from the CV (manual `ATS_HEADLINE` in `.env` is preferred).

## Commits

When the user asks for a **commit message** (or uses a commit-message skill), write it in **English**, Conventional Commits style, matching existing history on `main`. Do not commit for them unless they explicitly request it.

## Build and verify

```shell
python build.py
python build.py altacv 0          # visual EN
python build.py altacv-ats 1      # ATS PT-BR
```

Requires Docker Compose and Python 3.

`build.py` injects `latex/temp_*.tex` from `.eng.env` / `.ptbr.env` (`KEY=value` → `\envKeyCamelCase` in LaTeX). Keys include `FULL_NAME`, `PHONE_NUMBER`, `EMAIL`, `LOCATION`, `CURRENT_POSITION`, `ATS_HEADLINE`.

## Layout

| Path | Role |
|------|------|
| `latex/main.tex` | Document shell, fonts, `\readlist\renderedtags`, includes `latex/src/*` |
| `latex/src/*.tex` | CV content (summary, skills, professional, education) |
| `latex/mymacros.sty` | `\multiLangString`, `\checktags`, metrics (`\cvscale`, …), `\cvskillblock`, pagination hooks |
| `latex/altacv.cls` | Visual PDF |
| `latex/altacv-ats.cls` | ATS-oriented PDF (plain header, `\href` → text, role before company in `\cvevent`) |
| `scripts/cv_linkedin.py` | Plain-text About / experience / education for LinkedIn paste (`===` / `---`); respects `renderedtags`; does **not** read `.env` |

## Content toggles

- **`renderedtags`** in `latex/main.tex`: which `\checktags{…}{…}` blocks appear (e.g. `data`, `infra`, `backend`, `impact`, `show-levels`, `acad-projs`).
- **`CURRENT_POSITION`**: visual tagline only.
- **`ATS_HEADLINE`**: plain line under the name on ATS PDFs only (no label). User writes it in `.env`; `env-examples` use generic placeholders.

Escape `&` in env values as `\&` for LaTeX.

## ATS vs visual

When changing spacing or macros, check **both** modes and **both** languages. Portuguese ATS skills spacing may differ from English ATS (see `\cvskillsubsection` in `mymacros.sty`).

## LinkedIn helper

`python scripts/cv_linkedin.py [--lang eng|ptbr]` — output only; no personal data from env.

## ATS / LinkedIn headline (`ATS_HEADLINE`)

The user may ask you to **propose or refine** a pipe-separated headline (LinkedIn / ATS) from `latex/src/` and their goals.

- **Do**: suggest a concise line (roles + stack); EN/PT variants if useful; update local `.env` only when asked.
- **Do not**: add a repo script that auto-generates headlines; do not treat drafts as final without user review.
- Prefer `ATS_HEADLINE` over repeating the same keywords in the summary.

## LaTeX edits

- Keep `\multiLangString{EN}{PT}` pairs in sync when changing copy.
- Use `\cvsearchtag{…}` for technologies in body text (visual links; ATS plain text).
- Impact bullets use `\cvscale`, `\cvapproxpct`, `\cvarrow`, `\cvcpuSpikeRange` in `mymacros.sty` (ATS plain wording vs visual symbols).
