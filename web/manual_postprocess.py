#!/usr/bin/env python3
"""Adapt lwarp output to the existing website layout; do not edit paper sources."""
from __future__ import annotations

import html
import json
import re
from pathlib import Path

from lxml import etree
from lxml import html as lhtml

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / '_build' / 'manual'
RAW = BUILD / 'html'
OUT = BUILD / 'fragments'
# Preserve existing public page URLs, including References at manual7.html.
LEGACY = {
    'Introduction': 'manual1.html',
    'Antenna subtraction': 'manual2.html',
    'The NNLOJET framework': 'manual3.html',
    'Processes in NNLOJET': 'manual4.html',
    'Runcard syntax': 'manual5.html',
    'Using NNLOJET': 'manual6.html',
    'References': 'manual7.html',
    'Summary and support': 'manual-conclusion.html',
}


def manual_title() -> str:
    version = re.search(r'\\newcommand\{\\nnlojetversion\}\{([^}]+)\}',
                        (ROOT / 'manual' / 'NNLOJET.tex').read_text(encoding='utf-8'))
    if not version:
        raise SystemExit('Could not find \\nnlojetversion in manual/NNLOJET.tex.')
    return f'NNLOJET Manual v{version[1]}'


# Replaces the title block of the PDF (title, logo, collaboration) on the landing page.
INTRO = '''<h1>{title}</h1>
<p>The manual is also available as a <a href="nnlojet-manual.pdf" target="_blank" rel="noopener">PDF</a>.
If you use NNLOJET in a scientific publication, please cite the NNLOJET release paper:
A. Huss et al. (NNLOJET Collaboration), <i>NNLOJET: a parton-level event generator for jet cross
sections at NNLO QCD accuracy</i>, SciPost Phys. Codeb. 69,
<a href="https://doi.org/10.21468/SciPostPhysCodeb.69" target="_blank" rel="noopener">doi:10.21468/SciPostPhysCodeb.69</a>
[<a href="https://arxiv.org/abs/2503.22804" target="_blank" rel="noopener">arXiv:2503.22804</a>].</p>'''


def heading_title(text: str) -> str:
    text = re.sub(r'<span\b[^>]*class="sectionnumber"[^>]*>.*?</span>', '', text, flags=re.S)
    text = html.unescape(re.sub(r'<[^>]+>', '', text))
    return ' '.join(text.replace(r'\(', '').replace(r'\)', '').split())


def clean_fragment(text: str, title: str) -> str:
    """Retain the old script's inline-listing repairs, but protect preformatted code."""
    body = re.search(r'<body\b[^>]*>(.*?)</body>', text, re.S)
    if not body:
        raise ValueError('lwarp output is missing a body element')
    text = body.group(1)
    text = re.sub(r'<nav\b(?![^>]*class="toc")[^>]*>.*?</nav>', '', text, flags=re.S)
    text = re.sub(r'(<\/?)[hH]([456])\b', lambda m: m[1]+'h'+str(int(m[2])-2), text)
    text = text.replace('<h1>manual</h1>', f'<h1>{title}</h1>')
    # Do not reindent or collapse whitespace inside downloadable/example code.
    blocks: list[str] = []
    def keep_pre(m: re.Match[str]) -> str:
        blocks.append(m[0])
        return f'NNLOJET_PRE_BLOCK_{len(blocks)-1}_END'
    text = re.sub(r'<pre\b[^>]*>.*?</pre>', keep_pre, text, flags=re.S)
    for _ in range(2):
        text = re.sub(r'<div\b[^>]*>\s*</div>', '', text)
        text = re.sub(r'<p>\s*</p>', '', text)
    text = re.sub(r'[ \t]*\n[ \t]*', '\n', text)
    text = re.sub(r'(<span class="inlineprogramlisting">)([^<]*)</span>([^<]+)</span>', r'\1\2\3</span></span>', text)
    text = re.sub(r'(<span class="inlineprogramlisting">)([^<]*)</span>([^<]+)$', r'\1\2\3</span>', text, flags=re.M)
    code = r'(<span class="inlineprogramlisting">[^<]+</span>)'
    for _ in range(2):
        text = re.sub(r'</?p>\s*'+code, r'\1', text)
        text = re.sub(code+r'(\s*</?p>)+', r'\1', text)
    text = re.sub(r'\(\s*'+code, r'(\1', text)
    text = re.sub(code+r'\s*\)', r'\1)', text)
    text = re.sub(r'<(process_name|run_name|seed_number|t-cut|contribution|Observable)>', r'&lt;\1&gt;', text)
    # lwarp puts a line break after inline code, which shows as a space before punctuation.
    text = re.sub(r'</span>\s+(?=[,.;:)](?:\s|<|$))', '</span>', text)
    # Inside \textbf, lwarp leaves the code span empty and puts the word after it.
    text = re.sub(r'<span class="inlineprogramlisting"></span>([\w-]+)', r'<span class="inlineprogramlisting">\1</span>', text)
    # lwarp splits inline code at spaces (e.g. <var> = <val>): join the pieces again.
    split_code = r'(<span class="inlineprogramlisting">[^<]*)</span>\s+<span class="inlineprogramlisting">'
    while re.search(split_code, text):
        text = re.sub(split_code, r'\1 ', text)
    # The list marker has its own margin: drop the space after it, for aligned list items.
    text = re.sub(r'(<span class="listmarker"[^>]*>[^<]*</span>)\s+', r'\1', text)
    # A citation after ~ gets both a non-breaking and a normal space.
    text = re.sub(r'(\xa0|&nbsp;)\s+(?=\[\[\[)', r'\1', text)
    text = re.sub(r'<span\s+style="background:[^\"]*width:1012pt[^\"]*"\s*><!--.*?--></span>', '', text, flags=re.S)
    for i, block in enumerate(blocks):
        text = text.replace(f'NNLOJET_PRE_BLOCK_{i}_END', block)
    return text


def mark_list_terms(doc: lhtml.HtmlElement) -> None:
    """Highlight the runcard options defined by list items, e.g. `pol = DBLE`: ...

    These are the inline code snippets between the list marker and the first colon,
    if the item starts with code and the colon follows shortly after it.
    """
    for marker in doc.xpath('.//span[@class="listmarker"]'):
        if (marker.tail or '').strip():
            continue  # the item starts with text
        codes, text, node = [], '', marker.getnext()
        while node is not None and len(text) <= 60:
            if node.get('class') == 'inlineprogramlisting':
                codes.append(node)
            else:
                text += node.text_content()
            tail = node.tail or ''
            if ':' in tail or ':' in text:
                if codes and len(text + tail.split(':')[0]) <= 60:
                    for code in codes:
                        code.set('class', 'inlineprogramlisting term')
                break
            text += tail
            node = node.getnext()


def main() -> None:
    paths = [RAW / 'manual.html'] + sorted(
        (p for p in RAW.glob('manual*.html') if re.fullmatch(r'manual\d+\.html', p.name)),
        key=lambda p: int(re.search(r'\d+', p.stem)[0]))
    if len(paths) < 2:
        raise SystemExit('No split lwarp manual found; run web/make_manual.sh first.')
    manual_name = manual_title()
    mapping = {'manual.html': 'manual.html'}
    navigation = []
    documents = {}
    for path in paths:
        text = path.read_text(encoding='utf-8')
        documents[path.name] = text
        if path.name == 'manual.html':
            continue
        heading = re.search(r'<h([4-6])\b[^>]*>(.*?)</h\1>', text, re.S)
        if not heading:
            raise SystemExit(f'No main heading in {path.name}; review lwarp output.')
        title = heading_title(heading[2])
        filename = LEGACY.get(title, 'manual-'+re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')+'.html')
        if filename in mapping.values():
            raise SystemExit(f'Duplicate manual filename: {filename}')
        mapping[path.name] = filename
        navigation.append({'file': filename, 'title': title, 'level': int(heading[1]) - 3})
    if 'manual7.html' not in mapping.values():
        raise SystemExit('The References page could not be located.')
    OUT.mkdir(parents=True, exist_ok=True)
    names = re.compile(r'(?P<before>\b(?:href|src)\s*=\s*["\'])(?P<name>' + '|'.join(re.escape(n) for n in mapping) + r')(?=[#?"\'])')
    for old_name, raw_text in documents.items():
        text = clean_fragment(raw_text, manual_name)
        # Sub-pages (e.g. a runcard block): the page title becomes <h2>, as on chapter pages.
        level = next((p['level'] for p in navigation if p['file'] == mapping[old_name]), 1)
        if level > 1:
            text = re.sub(r'(</?)h([2-6])\b', lambda m: f'{m[1]}h{int(m[2]) - level + 1}', text)
        # Apply the mapping simultaneously: raw manual7 is not the references page.
        text = names.sub(lambda m: m['before'] + mapping[m['name']], text)
        def citation(m: re.Match[str]) -> str:
            content = html.unescape(m[1])
            if not re.fullmatch(r'[\d\s,–\-]+', content):
                raise ValueError(f'Unexpected citation encoding: {content!r}')
            return '[' + re.sub(r'\d+', lambda n: f'<a href="manual7.html#reference-{n[0]}">{n[0]}</a>', content) + ']'
        text = re.sub(r'\[\[\[(.*?)\]\]\]', citation, text, flags=re.S)
        if mapping[old_name] == 'manual7.html':
            text = re.sub(r'<span class="listmarker">\[(\d+)\]', r'<span class="listmarker" id="reference-\1">[\1]', text)
        # This replaces the old host-dependent Tidy pass with an explicit local parser.
        doc = lhtml.fragment_fromstring(text, create_parent='div')
        mark_list_terms(doc)
        if old_name == 'manual.html':
            blocks = [div for div in doc.xpath('.//div[@class="center"]')
                      if div.xpath('.//b[contains(., "NNLOJET Manual")] | .//img[contains(@src, "nnlogo")]')]
            if len(blocks) != 2:
                raise SystemExit('The title block of the manual has changed; review its HTML conversion.')
            intro = lhtml.fragments_fromstring(INTRO.format(title=html.escape(manual_name)))
            parent, index = blocks[0].getparent(), blocks[0].getparent().index(blocks[0])
            for block in blocks:
                block.drop_tree()
            for offset, element in enumerate(intro):
                parent.insert(index + offset, element)
        if mapping[old_name] == 'manual7.html':
            headings = doc.xpath('.//h2')
            if len(headings) > 1 and 'References' in headings[0].text_content():
                # Retain its link target while removing the duplicate B/7 References title.
                h = headings[0]
                anchor = etree.Element('a', id=h.get('id', 'references-start'))
                h.getparent().replace(h, anchor)
        # The References page has two headings (see above): keep only the TOC entry of the
        # last one, which is the heading that remains on the page.
        ref_links = [link for link in doc.xpath('.//nav[@class="toc"]//a')
                     if link.get('href', '').startswith('manual7.html')
                     and link.text_content().strip().endswith('References')]
        for link in ref_links[:-1]:
            entry = link.getparent() if link.getparent().tag == 'p' else link
            entry.drop_tree()
        # Suppress the artificial appendix letter on the reference TOC entry.
        for link in doc.xpath('.//nav[@class="toc"]//a'):
            if link.get('href', '').startswith('manual7.html'):
                for span in link.xpath('.//span'):
                    if span.text_content().strip() in {'B', '7', '8', '9'}:
                        span.drop_tree()
        # A page with sub-pages lists them at its end.
        position = next((i for i, p in enumerate(navigation) if p['file'] == mapping[old_name]), None)
        if position is not None:
            children = []
            for p in navigation[position+1:]:
                if p['level'] <= level:
                    break
                if p['level'] == level + 1:
                    children.append(p)
            if children:
                section = doc.xpath('.//section[@class="textbody"]')[-1]
                section.extend(lhtml.fragments_fromstring(
                    '<p>Continued on the following pages:</p><ul class="subpages">' + ''.join(
                        f'<li><a href="{html.escape(p["file"], quote=True)}">{html.escape(p["title"])}</a></li>'
                        for p in children) + '</ul>'))
        content = (html.escape(doc.text) if doc.text else '') + ''.join(
            lhtml.tostring(child, encoding='unicode', method='html') for child in doc)
        (OUT / mapping[old_name]).write_text(content, encoding='utf-8')
    (BUILD / 'navigation.json').write_text(json.dumps(navigation, indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
    # Use the MathJax initialization belonging to this lwarp version, not a stale copy.
    script = re.search(r'<script>\s*(.*?)</script>', documents['manual.html'], re.S)
    if not script or 'MathJax' not in script[1]:
        raise SystemExit('MathJax configuration was not found in lwarp output.')
    (BUILD / 'lwarp.js').write_text(script[1]+'\n', encoding='utf-8')
    print(f'Exported {len(paths)} manual pages and their navigation.')


if __name__ == '__main__':
    main()
