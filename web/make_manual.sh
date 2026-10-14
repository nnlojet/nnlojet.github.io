#!/usr/bin/env bash
# Build PDF and HTML from ../manual without changing any source files.
# GNU sed is required: on macOS use MYSED=gsed with a full TeX installation.
set -euo pipefail
root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="$root/manual"
build="$root/_build/manual"
PYTHON="${PYTHON:-python3}"
MYSED="${MYSED:-sed}"
for cmd in "$PYTHON" "$MYSED" latexmk pdflatex bibtex lwarpmk pdftocairo pdftotext; do
    command -v "$cmd" >/dev/null || { echo "Missing build tool: $cmd" >&2; exit 1; }
done
"$MYSED" --version | head -1 | grep -q 'GNU sed' || { echo 'GNU sed is required (MYSED=gsed on macOS).' >&2; exit 1; }
"$PYTHON" -c 'import lxml.html' || { echo 'Install python3-lxml (or lxml in your Python environment).' >&2; exit 1; }
for name in NNLOJET.tex NNLOJET.bib SciPost.cls SciPost_bibstyle.bst nnlogo_col.pdf dokan_monitor.png plot_ptj1.pdf; do
    test -s "$source_dir/$name" || { echo "Missing manual source: $source_dir/$name" >&2; exit 1; }
done
# Only this fixed, generated directory is ever removed. Never remove manual/.
rm -rf -- "$build"
mkdir -p "$build/pdf" "$build/html" "$build/fragments"
cp -a "$source_dir/." "$build/pdf/"
cp -a "$source_dir/." "$build/html/"
trap 'echo "Manual build failed; inspect $build/pdf/ and $build/html/ for TeX logs." >&2' ERR

# Downloadable PDF: unmodified paper, not the HTML variant.
cd "$build/pdf"
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error NNLOJET.tex
cp NNLOJET.pdf "$build/manual.pdf"

# HTML compatibility changes apply exclusively to disposable copies.
cd "$build/html"
cp NNLOJET.tex manual.tex
"$PYTHON" - <<'PREPARE'
from pathlib import Path
import re
p = Path('SciPost.cls')
s = p.read_text(encoding='utf-8')
marker = r'\LoadClass[11pt,a4paper]{article}'
if s.count(marker) != 1:
    raise SystemExit('SciPost.cls has changed; review the lwarp insertion point.')
s = s.replace(marker, marker + '\n' + r'''
\usepackage[HomeHTMLFilename=manual,HTMLFilename={manual},mathjax]{lwarp}
\setcounter{FileDepth}{1}
\boolfalse{FileSectionNames}
''')
s = s.replace(r'\let\ps@plain\ps@fancy', r'\warpprintonly{\let\ps@plain\ps@fancy}')
p.write_text(s, encoding='utf-8')
# Flatten the publisher's nested placeholder box, retaining its wording.
p = Path('manual.tex')
s = p.read_text(encoding='utf-8')
match = re.search(r'(?s)(%%%%%%%%%% BLOCK: Copyright information).*?\1', s)
if match:
    paragraphs = re.findall(
        r'(?s)\\begin\{minipage\}.*?\{\\small (.*?)\}\s*%?\s*\\end\{minipage\}',
        match.group())
    if len(paragraphs) != 2:
        raise SystemExit('Publisher notice has changed; review its HTML conversion.')
    replacement = '\\begin{quote}\n' + '\\par\n'.join(paragraphs) + '\n\\end{quote}\n'
    s = s[:match.start()] + replacement + s[match.end():]
p.write_text(s, encoding='utf-8')
PREPARE
# Insert placeholders in multirow tables
${MYSED} -i -z -E 's/\\\n( *)\&/\\\n\1\\mrowcell \&/g' manual.tex


# Remove incompatible statements
${MYSED} -i '/\\usepackage{mathtools}/d' manual.tex
${MYSED} -i '/\\urlstyle{same}/d' manual.tex

# Move references to separate section
${MYSED} -i '/\\bibliography{NNLOJET.bib}/i\\\warpHTMLonly{\\section{References}}' manual.tex

# Change format of bibliography references, so they can be turned into clickable links
${MYSED} -i '/\\begin{document}/i\\\warpHTMLonly{\\renewcommand{\\citeleft}{[[[}}\n\\warpHTMLonly{\\renewcommand{\\citeright}{]]]}}' manual.tex

# Remove some line breaks
${MYSED} -i 's:\\\\ \\lstinline:\\\warpprintonly{\\\\} \\lstinline:' manual.tex

# Fix some math-related incompatibilities
${MYSED} -i '/\\DeclareRobustCommand{\\rd}{\\ensuremathrm{d}}/d                      ; s/\\rd\b/\\mathrm{d}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\GeV}{\\ensuremathrm{GeV}\\xspace}/d           ; s/\\GeV\b/\\mathrm{GeV}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\fb}{\\ensuremathrm{fb}\\xspace}/d             ; s/\\fb\b/\\mathrm{fb}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\PH}{{\\ensuremathrm{H}}\\xspace}/d            ; s/\\PH\b/{\\mathrm{H}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\PZ}{{\\ensuremathrm{Z}}\\xspace}/d            ; s/\\PZ\b/{\\mathrm{Z}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\PW}{{\\ensuremathrm{W}}\\xspace}/d            ; s/\\PW\b/{\\mathrm{W}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\PWp}{{\\ensuremathrm{W^+}}\\xspace}/d         ; s/\\PWp\b/{\\mathrm{W}^+}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\PWm}{{\\ensuremathrm{W^-}}\\xspace}/d         ; s/\\PWm\b/{\\mathrm{W}^-}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pg}{{\\ensuremathrm{g}}\\xspace}/d            ; s/\\Pg\b/{\\mathrm{g}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pgg}{{\\ensuremathrm{\\gamma}}\\xspace}/d     ; s/\\Pgg\b/{\\gamma}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pl}{{\\ensuremath{\\ell}}\\xspace}/d          ; s/\\Pl\b/{\\ell}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Plp}{{\\ensuremath{\\ell^+}}\\xspace}/d       ; s/\\Plp\b/{\\ell^+}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Plm}{{\\ensuremath{\\ell^-}}\\xspace}/d       ; s/\\Plm\b/{\\ell^-}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pgn}{{\\ensuremath{\\nu}}\\xspace}/d          ; s/\\Pgn\b/{\\nu}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pagn}{{\\ensuremath{\\bar{\\nu}}}\\xspace}/d  ; s/\\Pagn\b/\\bar{\\nu}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pe}{{\\ensuremathrm{e}}\\xspace}/d            ; s/\\Pe\b/\\mathrm{e}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pep}{{\\ensuremathrm{e^+}}\\xspace}/d         ; s/\\Pep\b/{\\mathrm{e}^+}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pem}{{\\ensuremathrm{e^-}}\\xspace}/d         ; s/\\Pem\b/{\\mathrm{e}^-}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pq}{{{q}}\\xspace}/d                          ; s/\\Pq\b/{q}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Paq}{{{\\bar{q}}}\\xspace}/d                  ; s/\\Paq\b/\\bar{q}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pp}{{\\ensuremathrm{p}}\\xspace}/d            ; s/\\Pp\b/{\\mathrm{p}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pap}{{\\ensuremathrm{\\bar{p}}}\\xspace}/d    ; s/\\Pap\b/{\\bar{\\mathrm{p}}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\Pqt}{{\\ensuremathrm{t}}\\xspace}/d           ; s/\\Pqt\b/\\mathrm{t}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\jet}{{\\mathrm{jet}}\\xspace}/d               ; s/\\jet\b/jet/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\jets}{{\\mathrm{jets}}\\xspace}/d             ; s/\\jets\b/jets/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\muF}{\\muf}/d                                 ; s/\\muF\b/{\\mu_\\mathrm{F}}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\rT}{\\ensuremathrm{T}}/d                      ; s/\\rT\b/\\mathrm{T}/g' manual.tex
${MYSED} -i '/\\DeclareRobustCommand{\\alphas}{\\ensuremath{\\alpha_\\rs}}/d         ; s/\\alphas/\\alpha_\\mathrm{s}/g' manual.tex
${MYSED} -i 's/\\mathrm{d} \\text{\\runcard{<obs>}}\$/\\mathrm{d}\$\\runcard{<obs>}/' manual.tex
${MYSED} -i 's/\\text{\\runcard{ptz_bin1}}/\\text{\\texttt{ptz\\_bin1}}/' manual.tex
${MYSED} -i -E '/DeclareRobustCommand/s/\\makebox\{(.*)\}$/\1/' manual.tex

# The full release paper also uses TeV in the worked example.
${MYSED} -i '/\\DeclareRobustCommand{\\TeV}{\\ensuremathrm{TeV}\\xspace}/d ; s/\\TeV\b/\\mathrm{TeV}/g' manual.tex

# SVG versions of PDF figures for the browser. No source PDF is modified.
for figure in ./*.pdf; do
    pdftocairo -svg "$figure" "${figure%.pdf}.svg"
done
# Initialize manual_html.tex and lwarpmk.conf, then let latexmk resolve citations.
pdflatex -interaction=nonstopmode -halt-on-error -file-line-error manual.tex
latexmk -pdf -interaction=nonstopmode -halt-on-error -file-line-error manual_html.tex
lwarpmk pdftohtml
"$PYTHON" "$root/web/manual_postprocess.py"
test -s "$build/manual.pdf"
test -s "$build/fragments/manual.html"
echo "Manual PDF and HTML generated in $build"
