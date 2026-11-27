#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Generate, compile, and package Devicon for LaTeX from the pinned release."""

import argparse
import hashlib
import re
import shutil
import subprocess
import tempfile
import urllib.request
import zipfile
from pathlib import Path

from fontTools.ttLib import TTFont, TTLibError

ROOT = Path(__file__).resolve().parents[1]
VERSION = "2.18.0"
REVISION = "32fe1d3b3f36ad11f90ab94f7db59738139c2bf6"
SOURCE_URL = f"https://github.com/devicons/devicon/archive/{REVISION}.zip"
FONT_NAME = f"devicon-{VERSION}.ttf"
PDFTEX_MAP = "devicon-pdftex.map"
UPSTREAM_HASHES = {
    "devicon.min.css": "3aa2a00f8090f817721a968bd7a475ac1a3e82e06263a1e1807cf0ed6c703731",
    "fonts/devicon.ttf": "94e07032e8a5bcace228d280235e237d02d2cdd5124e2cbd128533920f7d959d",
    "icomoon.json": "aebd26972787b9c29b733c26782780bfd89c190f30e63e239fe161d72e290e0a",
    "LICENSE": "121194741d4a915b9f5890fdd6dd95121f9b1f816517c792358d72d7c838d664",
}
UPSTREAM_BUNDLED_NAMES = {"fonts/devicon.ttf": FONT_NAME, "LICENSE": "LICENSE-DEVICON"}
RUNTIME_FILES = ("devicon.sty", "devicon-glyphs.def", FONT_NAME)
CSS_RULE = re.compile(r"([^{}]+)\{([^{}]*)\}")
GLYPH_SELECTOR = re.compile(r"\.devicon-([a-z0-9_-]+)::?before")
CSS_CONTENT = re.compile(
    r"(?:^|;)\s*content\s*:\s*(['\"])(\\[0-9A-Fa-f]{1,6}\s*|[^'\"\\])\1\s*(?:;|$)"
)


def read_upstream(source):
    if source.is_dir():
        bundled = (source / "LICENSE-DEVICON").is_file()
        files = {}
        for name in UPSTREAM_HASHES:
            path = UPSTREAM_BUNDLED_NAMES.get(name, name) if bundled else name
            files[name] = (source / path).read_bytes()
    else:
        # Read only the expected members without extracting paths from the archive.
        with zipfile.ZipFile(source) as archive:
            members = set(archive.namelist())
            prefixes = ("", f"devicon-{REVISION}/", f"devicon-{VERSION}/", "devicon-master/")
            for prefix in prefixes:
                if all(prefix + name in members for name in UPSTREAM_HASHES):
                    files = {name: archive.read(prefix + name) for name in UPSTREAM_HASHES}
                    break
            else:
                raise ValueError(f"expected a Devicon ZIP containing revision {REVISION}")

    for name, expected_hash in UPSTREAM_HASHES.items():
        if hashlib.sha256(files[name]).hexdigest() != expected_hash:
            raise ValueError(f"{name} does not match Devicon revision {REVISION}")
    return files


def glyph_map(css, cmap):
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)
    glyphs = {}
    for selectors, declarations in CSS_RULE.findall(css):
        names = [GLYPH_SELECTOR.fullmatch(selector.strip()) for selector in selectors.split(",")]
        names = [match[1] for match in names if match]
        if not names:
            continue
        content = CSS_CONTENT.search(declarations)
        if content is None:
            raise ValueError(f"no Unicode code point in CSS for {', '.join(names)}")
        character = content[2]
        code_point = int(character[1:], 16) if character.startswith("\\") else ord(character)
        for name in names:
            # These selectors have equal specificity, so the last CSS rule wins.
            glyphs[name] = code_point

    if not glyphs:
        raise ValueError("no Devicon font selectors found in the CSS")
    missing = [name for name, code_point in glyphs.items() if code_point not in cmap]
    if missing:
        raise ValueError(f"CSS names missing in the font cmap: {', '.join(sorted(missing))}")
    return dict(sorted(glyphs.items()))


def write_pdftex_fonts(stage, font, cmap, points):
    """Split the native font into 8-bit encodings for the pdfTeX backend."""
    slots = {}
    map_lines = []
    units_per_em = font["head"].unitsPerEm
    postscript_name = font["name"].getDebugName(6)
    for offset in range(0, len(points), 256):
        bank_number = offset // 256
        bank = f"devicon-{VERSION.replace('.', '-')}-{bank_number}"
        metrics = ["(FAMILY DEVICON)\n(DESIGNSIZE R 10.0)\n"]
        encoding = ["/.notdef"] * 256
        for slot, point in enumerate(points[offset:offset + 256]):
            slots[point] = (bank, slot)
            # pdfTeX resolves these Unicode glyph names via the TrueType cmap.
            encoding[slot] = f"/uni{point:04X}" if point <= 0xFFFF else f"/u{point:X}"
            glyph_name = cmap[point]
            width = font["hmtx"].metrics[glyph_name][0]
            glyph = font["glyf"][glyph_name]
            height = max(0, getattr(glyph, "yMax", 0))
            depth = max(0, -getattr(glyph, "yMin", 0))
            metrics.append(
                f"(CHARACTER D {slot}\n"
                f"   (CHARWD R {width / units_per_em:.10f})\n"
                f"   (CHARHT R {height / units_per_em:.10f})\n"
                f"   (CHARDP R {depth / units_per_em:.10f})\n)\n"
            )

        rows = [" ".join(encoding[i:i + 8]) for i in range(0, 256, 8)]
        (stage / f"{bank}.enc").write_text(
            f"/DeviconEncoding{bank_number} [\n" + "\n".join(rows) + "\n] def\n",
            encoding="ascii",
        )
        pl = stage / f"{bank}.pl"
        pl.write_text("".join(metrics), encoding="ascii")
        result = subprocess.run(
            ["pltotf", pl.name, f"{bank}.tfm"], cwd=stage, capture_output=True, text=True,
            check=False,
        )
        if result.returncode:
            raise ValueError(f"pltotf failed for {bank}:\n{result.stdout}{result.stderr}")
        pl.unlink()
        map_lines.append(f"{bank} {postscript_name} <[{bank}.enc <{FONT_NAME}\n")

    (stage / PDFTEX_MAP).write_text("".join(map_lines), encoding="ascii")
    return slots


def compile_tex(engine, document, tex_dir, output_dir):
    output_dir.mkdir(exist_ok=True)
    log = output_dir / Path(document).with_suffix(".log")
    for _ in range(2):
        result = subprocess.run(
            [engine, "-no-shell-escape", "-interaction=nonstopmode", "-halt-on-error",
             "-file-line-error", f"-output-directory={output_dir}", document],
            cwd=tex_dir, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
            encoding="utf-8", errors="replace", check=False,
        )
        if result.returncode:
            raise ValueError(f"{engine} failed to render {document}:\n{result.stdout}")
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.startswith("Missing character:"):
                raise ValueError(f"{engine} reported a missing glyph in {document}: {line}")


def write_zip(path, directory, files, prefix=""):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(files):
            archive.write(directory / name, prefix + name)


def build(upstream, stage):
    for name in ("devicon.sty", "devicon.tex", "example.tex", "README.md", "LICENSE", "CTAN.md"):
        shutil.copyfile(ROOT / name, stage / name)
    (stage / "scripts").mkdir()
    shutil.copyfile(Path(__file__), stage / "scripts/release.py")
    for original, contents in upstream.items():
        destination = UPSTREAM_BUNDLED_NAMES.get(original, original)
        (stage / destination).write_bytes(contents)

    with TTFont(stage / FONT_NAME) as font:
        cmap = font.getBestCmap() or {}
        glyphs = glyph_map(upstream["devicon.min.css"].decode("utf-8-sig"), cmap)
        points = sorted(set(glyphs.values()))
        slots = write_pdftex_fonts(stage, font, cmap, points)

    header = f"% Generated from Devicon v{VERSION} by scripts/release.py.\n"
    banks = sorted({bank for bank, _ in slots.values()})
    declarations = [f"\\__devicon_declare_bank:n {{{bank}}}\n" for bank in banks]
    for name, point in glyphs.items():
        bank, slot = slots[point]
        declarations.append(f"\\__devicon_declare:nnnn {{{name}}} {{{point:X}}} {{{bank}}} {{{slot}}}\n")
    (stage / "devicon-glyphs.def").write_text(
        header + "".join(declarations), encoding="utf-8",
    )
    (stage / "devicon-catalog.tex").write_text(
        header + "".join(f"\\DeviconCatalogEntry{{{name}}}\n" for name in glyphs),
        encoding="utf-8",
    )
    return len(glyphs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upstream", type=Path, help="Devicon source ZIP or extracted root")
    parser.add_argument("--out-dir", type=Path, default=ROOT / "dist")
    parser.add_argument("--verify-luatex", action="store_true",
                        help="also compile the example and manual with LuaLaTeX")
    args = parser.parse_args()
    destination = args.out_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)

    try:
        with tempfile.TemporaryDirectory(prefix="devicon-build-", dir=destination) as tmp:
            work = Path(tmp)
            source = args.upstream
            if source is None and (ROOT / "LICENSE-DEVICON").is_file():
                source = ROOT
            if source is None:
                source = work / "upstream.zip"
                with urllib.request.urlopen(SOURCE_URL, timeout=60) as response, source.open("wb") as output:
                    shutil.copyfileobj(response, output)
            stage = work / "devicon"
            stage.mkdir()
            count = build(read_upstream(source), stage)

            engines = ["pdflatex", "xelatex"]
            if args.verify_luatex:
                engines.append("lualatex")
            for engine in engines:
                compile_tex(engine, "example.tex", stage, work / engine)
                compile_tex(engine, "devicon.tex", stage, work / engine)
            shutil.copyfile(work / "pdflatex/devicon.pdf", stage / "devicon.pdf")

            release_files = [str(path.relative_to(stage)) for path in stage.rglob("*") if path.is_file()]
            write_zip(work / "devicon-ctan.zip", stage, release_files, prefix="devicon/")
            pdftex_files = [path.name for pattern in ("*.enc", "*.tfm") for path in stage.glob(pattern)]
            project_files = (
                *RUNTIME_FILES, PDFTEX_MAP, *pdftex_files,
                "example.tex", "README.md", "devicon.pdf", "LICENSE", "LICENSE-DEVICON",
            )
            write_zip(work / "devicon-overleaf.zip", stage, project_files)
            for name in ("devicon-ctan.zip", "devicon-overleaf.zip"):
                (work / name).replace(destination / name)
            (stage / "devicon.pdf").replace(destination / "devicon.pdf")
    except (OSError, ValueError, zipfile.BadZipFile, TTLibError) as error:
        parser.exit(1, f"Build failed: {error}\n")

    print(f"Built both archives and the manual in {destination} ({count} font names).")


if __name__ == "__main__":
    main()
