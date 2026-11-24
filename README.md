# Devicon for LaTeX

Version 0.2.0 · 24 November 2026

`devicon` makes the [Devicon](https://devicon.dev/) font available in pdfLaTeX,
XeLaTeX and LuaLaTeX as `\devicon{<name>}`. The package uses the font and CSS names
from Devicon v2.18.0 at upstream revision
[`32fe1d3`](https://github.com/devicons/devicon/commit/32fe1d3b3f36ad11f90ab94f7db59738139c2bf6).
The glyphs take the current text size and color.

```latex
\documentclass{article}
\usepackage{devicon}
\begin{document}
\devicon{python-plain} Python \quad \devicon{github-original} GitHub
\end{document}
```

## Installation and use

### Start a new Overleaf project

Use **New Project → Upload Project** with the Overleaf release ZIP and compile
`example.tex` with **pdfLaTeX**. [Uploading an Overleaf project](https://docs.overleaf.com/managing-projects-and-files/uploading-a-project)

### Add Devicon to an existing Overleaf project

1. Extract the Overleaf ZIP, or open the `devicon/` folder inside the extracted
   CTAN archive.
2. Use **Upload** above Overleaf's file list. Put these files in the project
   root alongside your main `.tex` file. [Uploading files](https://docs.overleaf.com/managing-projects-and-files/adding-files-to-a-project/uploading-files-to-a-project)

   | Files | What to upload |
   | --- | --- |
   | Package | `devicon.sty` and `devicon-glyphs.def` |
   | Font | `devicon-2.18.0.ttf` |
   | pdfLaTeX map | `devicon-pdftex.map` |
   | pdfLaTeX encodings and metrics | All six `devicon-2-18-0-*.enc` and all six `devicon-2-18-0-*.tfm` files, numbered 0 to 5 |

3. Add `\usepackage{devicon}` to the preamble of your main `.tex` file.
   Put `\devicon{python-plain}` where you want the icon in the document body.
4. Click **Recompile**. If you need to select a compiler, go to
   **Settings → Compiler** and choose **pdfLaTeX**. [Overleaf compiler settings](https://docs.overleaf.com/getting-started/recompiling-your-project/selecting-a-tex-live-version-and-latex-compiler)

### When Overleaf includes Devicon

CTAN reviews and publishes new submissions. TeX Live aims to include
qualifying packages within a few days after they appear on CTAN. A project
can load `\usepackage{devicon}` directly once its selected Overleaf TeX Live
version includes the package. [CTAN review process](https://ctan.org/file/help/ctan/CTAN-upload-addendum) · [TeX Live package inclusion](https://tug.org/texlive/pkgcontrib.html)

Standard Overleaf updates TeX Live annually. The opt-in **Rolling TeX Live**
experiment can pick up new packages in a monthly build after TeX Live adds
them. For a submission in November 2026, August or September 2027 is a
planning estimate for standard Overleaf, based on the 2025 and 2026 upgrades
and subject to CTAN acceptance, TeX Live inclusion, and Overleaf's schedule.
[Overleaf TeX Live policy](https://docs.overleaf.com/troubleshooting-and-support/tex-live) · [2025 upgrade](https://www.overleaf.com/blog/tex-live-2025-is-now-available) · [2026 upgrade](https://www.overleaf.com/blog/tex-live-2026-is-now-available)

### Local installation and usage notes

- For a standalone local document, copy the same runtime files alongside
  your main `.tex` file.
- The package requires LaTeX dated 2021-06-01 or newer. XeLaTeX and LuaLaTeX
  use `fontspec`. pdfLaTeX uses its PDF output mode and the bundled metrics,
  encodings and map, which the package loads automatically.
- The manual `devicon.pdf` lists all accepted names. The command also accepts
  the full CSS class, such as `\devicon{devicon-python-plain}`.
- Use `\textcolor{blue}{\devicon{git-plain}}` with `xcolor` for a single-color
  glyph. Use the font variants listed in the manual. Keep a text label for
  meaningful icons.

For a local TEXMF installation, put the files in these directories and
refresh the filename database if your TeX distribution requires it.

| Files | TEXMF directory |
| --- | --- |
| `.sty`, `.def` | `tex/latex/devicon/` |
| `.ttf` | `fonts/truetype/public/devicon/` |
| `.tfm` | `fonts/tfm/public/devicon/` |
| `.enc` | `fonts/enc/dvips/devicon/` |
| `.map` | `fonts/map/pdftex/devicon/` |

## Build a release

The source checkout needs Python 3 with `fonttools` and a TeX installation with
`pltotf`, pdfLaTeX, XeLaTeX and the packages used by the example and manual.
Run from the source root:

```sh
python3 -m pip install fonttools
python3 scripts/release.py
```

The script uses bundled Devicon assets when run from the unpacked CTAN
archive. From the source checkout it downloads the pinned GitHub commit
archive. To specify a local ZIP or extracted repository root, run:

```sh
python3 scripts/release.py --upstream /path/to/devicon-master.zip
```

The build checks upstream file hashes and CSS mappings against the font,
generates the pdfLaTeX font files, and compiles the example and full catalog
with pdfLaTeX and XeLaTeX. Add `--verify-luatex` to repeat the compilation
with LuaLaTeX. The build writes these files to `dist/`:

| File | Purpose |
| --- | --- |
| `devicon-overleaf.zip` | Example project and runtime files |
| `devicon-ctan.zip` | CTAN archive with the package, documentation and sources |
| `devicon.pdf` | Manual and complete icon catalog |

See `CTAN.md` for submission details.

## Licensing

The LaTeX wrapper, documentation source and build script use the MIT License
in `LICENSE`. Devicon's font, CSS and IcoMoon source retain the upstream MIT
notice in `LICENSE-DEVICON` in built archives. Product names and logos belong
to their respective owners. Follow their brand policies when using the icons.
