#!/usr/bin/env python3
"""
Render CV LaTeX sources as plain text for copying into LinkedIn.

Respects \\readlist\\renderedtags and \\checktags from latex/main.tex.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SECTION_SEP = "==="
LATEX = ROOT / "latex"
SRC = LATEX / "src"

MONTHS_EN = {
    0: "present",
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}
MONTHS_PT = {
    0: "presente",
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}
MONTHS_SHORT_EN = {
    0: "present",
    1: "Jan",
    2: "Feb",
    3: "Mar",
    4: "Apr",
    5: "May",
    6: "Jun",
    7: "Jul",
    8: "Aug",
    9: "Sep",
    10: "Oct",
    11: "Nov",
    12: "Dec",
}
MONTHS_SHORT_PT = {
    0: "presente",
    1: "Jan",
    2: "Fev",
    3: "Mar",
    4: "Abr",
    5: "Mai",
    6: "Jun",
    7: "Jul",
    8: "Ago",
    9: "Set",
    10: "Out",
    11: "Nov",
    12: "Dez",
}

SKILL_LEVEL_EN = {1: "beginner", 2: "intermediate", 3: "advanced", 4: "fluent"}
SKILL_LEVEL_PT = {1: "básico", 2: "intermediário", 3: "avançado", 4: "fluente"}


class ParseError(Exception):
    pass


def read_braced(tex: str, i: int) -> tuple[str, int]:
    if i >= len(tex) or tex[i] != "{":
        raise ParseError(f"expected '{{' at {i}")
    depth = 0
    start = i + 1
    i += 1
    while i < len(tex):
        ch = tex[i]
        if ch == "{":
            depth += 1
        elif ch == "}":
            if depth == 0:
                return tex[start:i], i + 1
            depth -= 1
        elif ch == "\\" and i + 1 < len(tex):
            i += 1
        i += 1
    raise ParseError("unclosed brace")


def read_args(tex: str, i: int, n: int) -> tuple[list[str], int]:
    args: list[str] = []
    for _ in range(n):
        while i < len(tex) and tex[i].isspace():
            i += 1
        if i >= len(tex) or tex[i] != "{":
            raise ParseError(f"expected argument at {i}")
        arg, i = read_braced(tex, i)
        args.append(arg)
    return args, i


def read_command(tex: str, i: int) -> tuple[str | None, int]:
    if i >= len(tex) or tex[i] != "\\":
        return None, i
    j = i + 1
    while j < len(tex) and tex[j].isalpha():
        j += 1
    if j == i + 1:
        return None, i + 1
    return tex[i + 1 : j], j


def load_rendered_tags() -> set[str]:
    main = (LATEX / "main.tex").read_text(encoding="utf-8")
    marker = r"\readlist\renderedtags"
    pos = main.find(marker)
    if pos == -1:
        return set()
    brace = main.find("{", pos)
    if brace == -1:
        return set()
    body, _ = read_braced(main, brace)
    tags: set[str] = set()
    for line in body.splitlines():
        line = line.split("%", 1)[0].strip()
        if not line:
            continue
        for piece in line.split(","):
            name = piece.strip()
            if name:
                tags.add(name)
    return tags


class Renderer:
    def __init__(self, lang: str, rendered_tags: set[str], show_levels: bool) -> None:
        self.lang = lang
        self.rendered_tags = rendered_tags
        self.show_levels = show_levels
        self.months = MONTHS_SHORT_EN if lang == "eng" else MONTHS_SHORT_PT
        self.skill_levels = SKILL_LEVEL_EN if lang == "eng" else SKILL_LEVEL_PT

    def pick_lang(self, en: str, pt: str) -> str:
        return en if self.lang == "eng" else pt

    def tags_active(self, tag_csv: str) -> bool:
        wanted = {t.strip() for t in tag_csv.split(",") if t.strip()}
        return bool(wanted & self.rendered_tags)

    def expand(self, tex: str, structural: bool = False, _depth: int = 0) -> str:
        out: list[str] = []
        i = 0
        while i < len(tex):
            if tex[i] == "%":
                while i < len(tex) and tex[i] != "\n":
                    i += 1
                continue
            if tex[i] != "\\":
                out.append(tex[i])
                i += 1
                continue

            cmd, j = read_command(tex, i)
            if cmd is None:
                out.append(tex[i])
                i += 1
                continue
            i = j

            try:
                handled, chunk, i = self.dispatch(cmd, tex, i, structural)
            except ParseError:
                out.append("\\" + cmd)
                continue
            if handled:
                if chunk:
                    out.append(chunk)
            else:
                while i < len(tex) and tex[i].isspace():
                    i += 1
                while i < len(tex) and tex[i] == "{":
                    try:
                        _, i = read_braced(tex, i)
                    except ParseError:
                        break

        text = "".join(out)
        text = self.unescape_latex(text)
        return normalize_paste_text(text)

    def format_date_range(self, raw: str) -> str:
        text = raw.strip()
        text = re.sub(r"\s*–\s*", " – ", text)
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def unescape_latex(text: str) -> str:
        text = text.replace(r"\&", "&")
        text = text.replace(r"\#", "#")
        text = text.replace(r"\_", "_")
        text = text.replace(r"\%", "%")
        return text

    def dispatch(
        self, cmd: str, tex: str, i: int, structural: bool
    ) -> tuple[bool, str, int]:
        if cmd in ("multiLangString",):
            args, i = read_args(tex, i, 2)
            return True, self.expand(self.pick_lang(args[0], args[1]), structural), i

        if cmd == "checktags":
            args, i = read_args(tex, i, 2)
            if self.tags_active(args[0]):
                return True, self.expand(args[1], structural), i
            return True, "", i

        if cmd == "cvsearchtag":
            args, i = read_args(tex, i, 1)
            return True, self.expand(args[0], structural), i

        if cmd == "monthName":
            args, i = read_args(tex, i, 1)
            n = int(args[0].strip())
            return True, self.months.get(n, str(n)), i

        if cmd in ("betweenDates",):
            return True, "–", i

        if cmd == "cvscale":
            args, i = read_args(tex, i, 1)
            return True, f"~{args[0].strip()}×", i

        if cmd == "cvapproxpct":
            args, i = read_args(tex, i, 1)
            return True, f"~{args[0].strip()}%", i

        if cmd == "cvarrow":
            return True, " → " if self.lang == "eng" else " → ", i

        if cmd == "cvcpuSpikeRange":
            args, i = read_args(tex, i, 2)
            a, b = args[0].strip(), args[1].strip()
            if self.lang == "eng":
                return True, f"~{a}%–{b}%", i
            return True, f"~{a}%–{b}%", i

        if cmd == "smallObsv":
            args, i = read_args(tex, i, 2)
            a, b = self.expand(args[0], structural), self.expand(args[1], structural)
            return True, f"{a} ({b})", i

        if cmd == "href":
            args, i = read_args(tex, i, 2)
            link_text = self.expand(args[1], structural)
            url = args[0].strip()
            if url and not structural:
                return True, f"{link_text} ({url})", i
            return True, link_text, i

        if cmd in ("par", "newline", "linebreak"):
            return True, "\n", i

        if cmd in ("&",):
            return True, "&", i

        if cmd in (
            "medskip",
            "smallskip",
            "bigskip",
            "hspace",
            "vspace",
            "unskip",
            "justifying",
            "noindent",
            "ignorespaces",
        ):
            if cmd == "vspace":
                _, i = read_args(tex, i, 1)
            return True, "", i

        if cmd == "ifthenelse":
            args, i = read_args(tex, i, 3)
            return True, "", i

        if cmd in ("divider",):
            return True, "\n---\n", i

        if structural:
            if cmd == "cvsection":
                args, i = read_args(tex, i, 1)
                title = self.expand(args[0], structural)
                return True, f"\n{title}\n", i

            if cmd == "cvskillsubsection":
                args, i = read_args(tex, i, 1)
                title = self.expand(args[0], structural)
                return True, f"\n{title}: ", i

            if cmd == "cvevent":
                args, i = read_args(tex, i, 4)
                title = self.expand(args[0], structural)
                org = self.expand(args[1], structural)
                dates = self.format_date_range(self.expand(args[2], structural))
                loc = self.expand(args[3], structural).strip()
                meta = f"{dates} · {loc}" if loc else dates
                block = f"\n{title}\n{org}\n{meta}\n"
                return True, block, i

            if cmd == "cvsubevent":
                args, i = read_args(tex, i, 4)
                title = self.expand(args[0], structural).strip()
                d2 = self.format_date_range(self.expand(args[2], structural))
                if d2:
                    short = re.match(r"^(.*)\s+\(([A-Za-z0-9.-]{2,10})\)\s*$", title)
                    if short and len(short.group(2)) <= 8:
                        title = short.group(1).strip()
                    line = f"{title} ({d2})"
                else:
                    line = title
                return True, f"\n{line}", i

            if cmd == "cveventsummary":
                args, i = read_args(tex, i, 1)
                body = self.expand(args[0], structural).strip()
                return True, f"\n{body}\n\n", i

            if cmd == "item":
                return True, "\n• ", i

        if cmd == "cvskilltxt":
            while i < len(tex) and tex[i].isspace():
                i += 1
            if i < len(tex) and tex[i] == "[":
                j = tex.find("]", i + 1)
                i = j + 1 if j != -1 else i
            args, i = read_args(tex, i, 2)
            name = self.expand(args[0], structural)
            level = int(args[1].strip())
            if self.show_levels:
                return True, f"{name} ({self.skill_levels.get(level, level)})", i
            return True, name, i

        if cmd in ("cvproseblock",):
            args, i = read_args(tex, i, 1)
            return True, self.expand(args[0], structural).strip() + "\n", i

        if cmd in ("cvskillblock",):
            args, i = read_args(tex, i, 1)
            return True, self.expand(args[0], structural).strip() + "\n", i

        if cmd == "inlineList":
            args, i = read_args(tex, i, 1)
            inner = args[0]
            chunks = re.split(r"\\item\s+", inner)
            names: list[str] = []
            for chunk in chunks:
                chunk = chunk.strip()
                if not chunk:
                    continue
                names.append(self.expand(chunk, structural).strip())
            return True, ", ".join(names) + "\n", i

        if cmd in ("begin", "end"):
            args, i = read_args(tex, i, 1)
            return True, "", i

        if cmd in ("checktags",):
            return False, "", i

        return False, "", i


def normalize_paste_text(text: str) -> str:
    text = Renderer.unescape_latex(text)
    text = text.replace("\t", " ")
    lines = [re.sub(r" +", " ", ln).rstrip() for ln in text.splitlines()]
    out: list[str] = []
    for ln in lines:
        if ln.startswith(" •"):
            ln = "•" + ln[2:]
        if not ln and out and out[-1] == "":
            continue
        out.append(ln)
    text = "\n".join(out)
    text = re.sub(r"\n\n+(•)", r"\n\1", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def process_file(path: Path, renderer: Renderer) -> str:
    tex = path.read_text(encoding="utf-8")
    return renderer.expand(tex, structural=True)


def drop_redundant_cvsection(body: str, titles: tuple[str, ...]) -> str:
    for title in titles:
        if body.startswith(title):
            return body[len(title) :].lstrip("\n")
    return body


def section_label(lang: str, key: str) -> str:
    labels = {
        "eng": {
            "about": "About",
            "experience": "Experience",
            "education": "Education",
        },
        "ptbr": {
            "about": "Sobre",
            "experience": "Experiência profissional",
            "education": "Formação",
        },
    }
    return labels[lang][key]


def main() -> int:
    parser = argparse.ArgumentParser(description="Plain-text CV view for LinkedIn updates.")
    parser.add_argument(
        "--lang",
        choices=("eng", "ptbr"),
        default="ptbr",
        help="language to export (default: ptbr)",
    )
    args = parser.parse_args()

    tags = load_rendered_tags()
    renderer = Renderer(args.lang, tags, show_levels=False)

    about = drop_redundant_cvsection(
        process_file(SRC / "summary.tex", renderer),
        ("Summary", "Resumo Profissional"),
    )
    experience = drop_redundant_cvsection(
        process_file(SRC / "professional.tex", renderer),
        ("Work Experience", "Experiência Profissional"),
    )
    education = drop_redundant_cvsection(
        process_file(SRC / "education.tex", renderer),
        ("Education", "Experiência Acadêmica"),
    )

    parts: list[str] = []
    if about.strip():
        parts.append(section_label(args.lang, "about"))
        parts.append(about.strip())

    if experience.strip():
        if parts:
            parts.extend(["", SECTION_SEP, ""])
        parts.append(section_label(args.lang, "experience"))
        parts.append(experience.strip())

    if education.strip():
        if parts:
            parts.extend(["", SECTION_SEP, ""])
        parts.append(section_label(args.lang, "education"))
        parts.append(education.strip())

    sys.stdout.write(normalize_paste_text("\n".join(parts)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
