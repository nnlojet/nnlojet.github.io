#!/usr/bin/env python3
"""Generate web/examples.html from the example runcards in web/runcards/.

The runcards are stored as web/runcards/<PROCESS>/<name>.run, where <PROCESS>
is a process name as listed by `NNLOJET --listprocs`.  Naming conventions:
  nnlojet-<arXiv>-<...>.run : setup of an NNLOJET publication
  <experiment>-<arXiv>.run  : fiducial setup of an experimental measurement
  anything else             : illustrative setup, described in the header
                              comment of the runcard
Run from any directory:  python3 web/prepare_examples.py
"""

import html
import re
from pathlib import Path

WEB = Path(__file__).resolve().parent
RUNCARDS = WEB / "runcards"
OUTPUT = WEB / "examples.html"

# > process names and descriptions in the order of `NNLOJET --listprocs` (v1.0.3)
PROCESSES = [
    ("Z", "production of a Z boson (decaying to leptons)"),
    ("ZJ", "production of a Z boson plus a jet"),
    ("WP", "production of a positively charged W boson"),
    ("WPJ", "production of a positively charged W boson plus a jet"),
    ("WM", "production of a negatively charged W boson"),
    ("WMJ", "production of a negatively charged W boson plus a jet"),
    ("H", "production of a Higgs boson"),
    ("HJ", "production of a Higgs boson plus a jet"),
    ("HTO2P", "production of a Higgs boson decaying to two photons"),
    ("HTO2PJ", "production of a Higgs boson plus a jet, decaying to two photons"),
    ("HTO2L1P", "production of a Higgs boson with Dalitz decay to l+l- and a photon"),
    ("HTO2L1PJ", "production of a Higgs boson plus a jet, with Dalitz decay to l+l- and a photon"),
    ("HTO4E", "production of a Higgs boson decaying to (l+l-)(l+l-)"),
    ("HTO2E2MU", "production of a Higgs boson decaying to (l1+l1-)(l2+l2-)"),
    ("HTO2L2N", "production of a Higgs boson decaying to (l1 nu1)(l2 nu2)"),
    ("HTO4EJ", "production of a Higgs boson plus a jet, decaying to (l+l-)(l+l-)"),
    ("HTO2E2MUJ", "production of a Higgs boson plus a jet, decaying to (l1+l1-)(l2+l2-)"),
    ("HTO2L2NJ", "production of a Higgs boson plus a jet, decaying to (l1 nu1)(l2 nu2)"),
    ("GJ", "production of a photon plus a jet"),
    ("GJ_frag", "production of a photon plus a jet, including photon fragmentation"),
    ("GG", "production of two photons"),
    ("JJ", "production of two jets"),
    ("eeJJ", "production of two jets in electron-positron collisions"),
    ("eeJJJ", "production of three jets in electron-positron collisions"),
    ("epLJ", "production of a jet in neutral-current DIS"),
    ("epLJJ", "production of two jets in neutral-current DIS"),
    ("epNJ", "production of a jet in charged-current DIS (electron beam)"),
    ("epNJJ", "production of two jets in charged-current DIS (electron beam)"),
    ("epNbJ", "production of a jet in charged-current DIS (positron beam)"),
    ("epNbJJ", "production of two jets in charged-current DIS (positron beam)"),
]

# > runcard features: (description in HTML, regular expression on the runcard without comments)
FEATURES = [
    ("Proton-antiproton collisions (<code>collider = PAP</code>)", r"collider\s*=\s*PAP\b"),
    ("Lepton-proton collisions with beam energies (<code>collider = PE</code>, <code>Ebeam1</code>, <code>Ebeam2</code>)", r"\bEbeam1\s*="),
    ("Polarised lepton beam and Z-boson exchange (<code>pol</code>, <code>V_NC</code>)", r"^\s*pol\s*="),
    ("Z boson decaying to neutrinos (<code>L_NC = NU</code>)", r"\bL_NC\s*=\s*NU\b"),
    ("Exclusive jet multiplicity (<code>jet_exclusive = .true.</code>)", r"jet_exclusive\s*=\s*\.true\."),
    ("Durham and JADE jet algorithms for electron-positron collisions", r"jet\s*=\s*(durham|jade)\["),
    ("Photon isolation (<code>photon_isolation</code>)", r"photon_isolation\s*="),
    ("Photon fragmentation (<code>photon_fragmentation</code>)", r"photon_fragmentation\s*="),
    ("Automatic warmup schedule (<code>warmup = &lt;ncall&gt;[auto]</code>)", r"warmup\s*=\s*\d+\s*\[\s*auto\s*\]"),
    ("Multi-channel sampling and other optimisation settings (<code>multi_channel</code>)", r"multi_channel\s*="),
    ("Scale coefficients and histogram scale overrides (<code>scale_coefficients</code>, <code>mu0</code>)", r"\bmu0\s*="),
    ("Complex-mass scheme for the W and Z bosons (<code>SCHEME[GV] = CMS</code>)", r"SCHEME\[GV\]\s*=\s*CMS"),
    ("Fixed electroweak coupling (<code>SCHEME[ALPHA] = FIX</code>)", r"SCHEME\[ALPHA\]\s*=\s*FIX\b"),
    ("Electroweak coupling at the Z pole (<code>SCHEME[ALPHA] = ALPHAMZ</code>)", r"SCHEME\[ALPHA\]\s*=\s*ALPHAMZ\b"),
    ("Full CKM matrix (<code>CKM = FULL</code>)", r"\bCKM\s*=\s*FULL\b"),
    ("Vetoes with <code>reject</code> selectors", r"^\s*reject\s"),
    ("Selector groups (<code>OR</code> ... <code>END_OR</code>)", r"^\s*OR\s*$"),
    ("Selectors applied only to valid observables (<code>select_if_valid</code>)", r"^\s*(select|reject)_if_valid\s"),
    ("Histogram selectors (<code>HISTOGRAM_SELECTORS</code>)", r"^\s*HISTOGRAM_SELECTORS\s*$"),
    ("Composite histograms (<code>COMPOSITE</code>)", r"^\s*COMPOSITE\b"),
    ("Fiducial cross sections (<code>cross &gt; &lt;name&gt;</code>)", r"^\s*cross\s*>"),
    ("Cumulant distributions (<code>cumulant</code>)", r"\bcumulant\s*="),
    ("Logarithmic binning (<code>binning = LOG</code>)", r"\bbinning\s*=\s*LOG\b"),
    ("Breakdown into partonic luminosities (<code>output_type = 1</code>)", r"\boutput_type\s*=\s*1\b"),
    ("Rescaling a histogram (<code>fac</code>)", r"\bfac\s*="),
    ("Biasing the phase-space sampling (<code>REWEIGHT</code>)", r"^\s*REWEIGHT\b"),
    ("PDF interpolation (<code>PDF_INTERPOLATION</code>)", r"^\s*PDF_INTERPOLATION\b"),
]

ARXIV_RE = re.compile(r"(\d{4}\.\d{4,5}|\d{7})")


def strip_comments(text: str) -> str:
    return "\n".join(line.split("!")[0] for line in text.splitlines())


def header_description(text: str) -> str:
    """First sentence of the comment block that follows the NNLOJET banner."""
    words = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("!##") or re.fullmatch(r"!#+!", stripped):
            continue  # banner
        if stripped.startswith("!"):
            words.append(stripped.lstrip("!").strip())
            continue
        if stripped or words:
            break
    desc = " ".join(w for w in words if w)
    match = re.match(r"(.+?\.)(\s|$)", desc)
    return match.group(1) if match else desc


def collider_energy(text: str) -> str:
    body = strip_comments(text)
    if match := re.search(r"sqrts\s*=\s*([0-9.]+)", body, re.I):
        sqrts = float(match.group(1))
        return f"{sqrts / 1000:g} TeV" if sqrts >= 1000 else f"{sqrts:g} GeV"
    return ""


def describe(card: Path, text: str) -> str:
    if desc := header_description(text):
        return html.escape(desc)
    energy = collider_energy(text)
    energy = f" at {energy}" if energy else ""
    name = card.stem
    if name.lower().startswith("nnlojet-"):
        return f"Setup of an NNLOJET publication{energy}"
    if ARXIV_RE.search(name):
        experiment = name.split("-")[0].upper()
        return f"Fiducial setup of the {html.escape(experiment)} measurement{energy}"
    return f"Example setup{energy}"


def arxiv_link(name: str) -> str:
    if match := ARXIV_RE.search(name):
        number = match.group(1)
        return f' [<a href="https://arxiv.org/abs/{number}" target="_blank" rel="noopener">arXiv:{number}</a>]'
    return ""


def main() -> None:
    known = {proc for proc, _ in PROCESSES}
    for folder in RUNCARDS.iterdir():
        if folder.is_dir() and folder.name not in known:
            raise SystemExit(f"prepare_examples: unknown process folder {folder}")
    cards = {
        proc: sorted((RUNCARDS / proc).glob("*.run"), key=lambda p: p.name.lower())
        for proc, _ in PROCESSES
    }
    texts = {card: card.read_text(encoding="utf-8") for proc_cards in cards.values() for card in proc_cards}

    out = [
        "<h2>Examples</h2>",
        "<p>Example runcards for all processes available in NNLOJET v1.0.3. "
        "Runcards named <code>nnlojet-&lt;arXiv&gt;-...</code> use the setup of an NNLOJET publication, "
        "runcards named <code>&lt;experiment&gt;-&lt;arXiv&gt;</code> the fiducial setup of a measurement; "
        "the other runcards are illustrative setups, described in their header comments.</p>",
        "<p>Every runcard can be run directly, e.g. <kbd>NNLOJET --run Z/atlas-1109.5141.run</kbd>, "
        "which computes the leading-order contribution (<code>LO</code>) selected in the <code>CHANNELS</code> block. "
        "The higher-order contributions are selected in the <code>CHANNELS</code> block, as explained in the "
        "comment there, together with suitable <code>warmup</code> and <code>production</code> settings. "
        "Alternatively, the complete calculation can be run with the <code>nnlojet-run</code> workflow, "
        'see the <a href="manual.html">manual</a>. '
        "The PDF sets used in the runcards must be installed in LHAPDF.</p>",
        "<h3>Runcards by process</h3>",
        "<ul>",
    ]
    for proc, proc_desc in PROCESSES:
        out.append(f'  <li id="{html.escape(proc)}"><strong>{html.escape(proc)}</strong>: {html.escape(proc_desc)}')
        out.append("    <ul>")
        for card in cards[proc]:
            rel = card.relative_to(WEB).as_posix()
            out.append(
                f'      <li><a href="{html.escape(rel)}">{html.escape(card.name)}</a>{arxiv_link(card.stem)}: '
                f"{describe(card, texts[card])}</li>"
            )
        out.append("    </ul>")
        out.append("  </li>")
    out += [
        "</ul>",
        "<h3>Runcard features</h3>",
        "<p>Example runcards that use specific runcard options:</p>",
        "<ul>",
    ]
    for feature, pattern in FEATURES:
        regex = re.compile(pattern, re.I | re.M)
        users = [card for card, text in texts.items() if regex.search(strip_comments(text))]
        if not users:
            raise SystemExit(f"prepare_examples: no runcard uses the feature: {feature}")
        # > prefer illustrative runcards (with a header description), then sort by name
        users.sort(key=lambda c: (header_description(texts[c]) == "", c.parent.name.lower(), c.name.lower()))
        links = ", ".join(
            f'<a href="{html.escape(c.relative_to(WEB).as_posix())}">{html.escape(c.parent.name + "/" + c.name)}</a>'
            for c in users[:3]
        )
        out.append(f"  <li>{feature}: {links}</li>")
    out.append("</ul>")

    OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    ncards = sum(len(v) for v in cards.values())
    print(f"prepare_examples: wrote {OUTPUT.relative_to(WEB.parent)} ({ncards} runcards, {len(FEATURES)} features)")


if __name__ == "__main__":
    main()
