# Devicon for LaTeX submission details

| Field | Suggested value |
| --- | --- |
| Package | `devicon` |
| Version | `0.2.2` |
| Summary | Devicon for pdfLaTeX, XeLaTeX and LuaLaTeX |
| CTAN directory | `/fonts/devicon` |
| License | MIT |
| Upload archive | `dist/devicon-ctan.zip` |

**Description**

`devicon` brings Devicon v2.18.0 to pdfLaTeX, XeLaTeX and LuaLaTeX.
Use `\devicon{python-plain}` to insert an icon at the current text size and
color. A PDF catalog lists the available icon names.

**Announcement**

Version 0.2.2 adds PDF replacement text for Devicon glyphs. Use the
`actualtext` option to supply a context-specific label or `artifact` to
mark an icon as decorative in a tagged PDF. The manual and example show
both options.

Before uploading, confirm the catalog name, supply the maintainer's public
name and the uploader's contact email, and confirm the copyright credit in
`LICENSE`. Run the build with `--verify-luatex` on a TeX installation with
`luaotfload`. Add the source repository URL if one is available. The upstream
MIT notice travels alongside the original Devicon font and its sources.
Use the Upload link on <https://ctan.org/pkg/devicon> to submit an update.
