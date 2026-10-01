"""Render the JIB submission edition and the journal-neutral preprint from one manuscript source.

Environment:
  ARCHIVE_DOI   Zenodo DOI of the public code/evidence release (omit until minted).
  PREPRINT_DOI  DOI of the preprint record itself (printed on the preprint edition).
  EDITION_DATE  Printed date (default: today).
"""
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from docx import Document
from docx.enum.text import WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'deliverables' / 'editions'
REPO_URL = 'https://github.com/otcan/metabolic-representation-qualification'
RELEASE_TAG = 'v1.0.0'
TITLE = 'Matched nulls and compact baselines qualify metabolic-state representations'
AUTHOR = 'Oğuzcan Ünver'
AFFILIATION = 'Metastate Bio Inc, 1207 Delaware Avenue, #1401, Wilmington, DE 19806, USA'
CORRESPONDENCE = 'can@metastate.bio; ORCID 0009-0007-2023-5084'
PAGE_BREAK = '\n```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```\n'
PANDOC_FROM = 'markdown+tex_math_single_backslash+tex_math_dollars+link_attributes'


def edition_date():
    if os.environ.get('EDITION_DATE'):
        return os.environ['EDITION_DATE']
    d = dt.date.today()
    return f'{d.day} {d:%B %Y}'


def availability(doi):
    archive = f' The exact release is archived at Zenodo (https://doi.org/{doi}).' if doi else ''
    return f"""## Data availability

ST002081 and ST000818 are available from the Metabolomics Workbench (https://doi.org/10.21228/M8ZM5P and https://doi.org/10.21228/M89M31) under CC BY 4.0. CCLE metabolomics, expression and annotation files are available from the original release [12] and are not redistributed. Human-GEM v2.0.0 is available under CC BY 4.0 [13,14]. Aggregate results, figure source data, run manifests and checksums are included in the code archive. Participant-linked losses and split maps are not redistributed.

## Code availability

The qualification-ladder workflow, extension analyses, tests and figure code are openly available under the Apache-2.0 licence at {REPO_URL} (release {RELEASE_TAG}).{archive} The earlier matched-null software is available as release v1.0.1 [15]. Both run on standard Python and are free of charge for academic and non-academic use.
"""


ETHICS = """## Ethical statement

**Acknowledgments:** Computational resources were provided by Metastate Bio Inc.

**Author contributions:** O.Ü. conceived the study, defined the research questions and claim boundaries, directed the computational programme, provided resources, interpreted the results and revised the manuscript. The author has accepted responsibility for the entire content of this manuscript and approved its submission.

**Research funding:** None declared.

**Competing interests:** O.Ü. is the founder of Metastate and is affiliated with Metastate Bio Inc, which develops commercial computational biology, biomarker and modelling products and services that could benefit from the publication of this work. The author declares no other competing interests.

**Informed consent and ethical approval:** Not applicable. This study reanalysed publicly available, de-identified data and involved no new recruitment, intervention or data collection. Ethical approval and informed consent for the source studies are described in the original publications and deposits [10,11].
"""


def front(edition, date, doi_pre):
    block = f'{AUTHOR}\\\n{AFFILIATION}\\\nCorrespondence: {CORRESPONDENCE}'
    if edition == 'preprint':
        doi = f' DOI: https://doi.org/{doi_pre}.' if doi_pre else ''
        return f'**Preprint — not peer reviewed.** Version 1.0, {date}. Licence: CC BY 4.0.{doi}\n\n{block}\n'
    return block + '\n'


def journal_layout(text):
    """Move figures and tables out of the text flow as JIB requires; return body and back matter."""
    legends, tables = [], []

    def figure(m):
        caption = m.group(1)
        number = re.match(r'Figure (\d+)\.', caption).group(1)
        legends.append(caption)
        return f'[Figure {number} about here]\n'
    text = re.sub(r'!\[(Figure \d+\.[^\]]*?)\]\([^)]+\)(?:\{[^}]*\})?\n', figure, text, flags=re.S)

    def table(m):
        number = re.match(r'Table (\d+)\.', m.group(2)).group(1)
        tables.append(m.group(1) + '\n' + m.group(2))
        return f'[Table {number} about here]\n'
    text = re.sub(r'((?:^\|[^\n]*\|\n)+)\n(Table \d+\.[^\n]*)\n', table, text, flags=re.M)
    back = ''.join(PAGE_BREAK + t + '\n' for t in tables)
    back += PAGE_BREAK + '## Figure legends\n\n' + '\n\n'.join(legends) + '\n'
    return text, back, len(legends), len(tables)


def pandoc(src, docx):
    subprocess.run(['pandoc', str(src), '-f', PANDOC_FROM, '--resource-path', f'{ROOT / "manuscript"}:{ROOT}',
                    '-o', str(docx)], check=True)


def size_columns(table, total_cm):
    """Give each column a width proportional to its longest word and average text length."""
    cols = len(table.columns)
    need = []
    for c in range(cols):
        header = table.rows[0].cells[c].text
        body = [row.cells[c].text for row in table.rows[1:]]
        longest_cell = min(max((len(s) for s in body), default=4), 22)
        longest_header_word = max((len(w) for w in re.split(r'[\s-]+', header) if w), default=4)
        need.append(max(longest_cell, longest_header_word * 1.15, 4) * 0.21 + 0.45)
    scale = total_cm / sum(need)
    table.autofit = False
    widths = [w * scale for w in need]  # stretch or shrink to the text width
    grid = table._tbl.tblGrid
    for col, width in zip(grid.findall(qn('w:gridCol')), widths):
        col.set(qn('w:w'), str(int(width * 567)))
    tblPr = table._tbl.tblPr
    for tag in ('w:tblW', 'w:tblLayout'):
        for old in tblPr.findall(qn(tag)):
            tblPr.remove(old)
    tblW = OxmlElement('w:tblW'); tblW.set(qn('w:w'), str(int(total_cm * 567))); tblW.set(qn('w:type'), 'dxa')
    layout = OxmlElement('w:tblLayout'); layout.set(qn('w:type'), 'fixed')
    tblPr.append(tblW); tblPr.append(layout)
    for c, width in enumerate(widths):
        for row in table.rows:
            row.cells[c].width = Cm(width)


def style_docx(path, journal):
    d = Document(path)
    for section in d.sections:
        for side in ('left_margin', 'right_margin', 'top_margin', 'bottom_margin'):
            setattr(section, side, Cm(2.5))
        footer = section.footer.paragraphs[0]
        footer.alignment = 2
        field = OxmlElement('w:fldSimple'); field.set(qn('w:instr'), 'PAGE'); footer._p.append(field)
    for name in ('Normal', 'Body Text', 'First Paragraph', 'Compact', 'Image Caption'):
        try:
            style = d.styles[name]
        except KeyError:
            continue
        style.font.size = Pt(12 if journal else 10.5)
        if journal:
            style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.DOUBLE
    for p in d.paragraphs:
        if p._p.xpath('.//w:drawing'):
            p.paragraph_format.keep_with_next = True
        if p.style.name == 'Image Caption':
            p.paragraph_format.keep_together = True
            for r in p.runs:
                r.italic = False
    for t in d.tables:
        size_columns(t, 16.0)
        for row in t.rows:
            row._tr.get_or_add_trPr().append(OxmlElement('w:cantSplit'))
            for cell in row.cells:
                for p in cell.paragraphs:
                    p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                    for r in p.runs:
                        r.font.size = Pt(10)
    d.save(path)


def to_pdf(docx_files, outdir):
    env = os.environ.copy()
    ipc = ROOT / 'work/doc-ipc'; ipc.mkdir(parents=True, exist_ok=True)
    env['TMPDIR'] = str(ipc)
    shim = ROOT / 'work/libreoffice_socket_path.so'
    if not shim.exists():
        subprocess.run(['gcc', '-shared', '-fPIC', '-o', str(shim), str(ROOT / 'scripts/libreoffice_socket_path.c'), '-ldl'],
                       check=True)
    env['LD_PRELOAD'] = str(shim)
    profile = ROOT / 'work/libreoffice-review-profile'
    subprocess.run(['libreoffice', '-env:UserInstallation=' + profile.as_uri(), '--headless', '--convert-to', 'pdf',
                    '--outdir', str(outdir), *map(str, docx_files)], env=env, check=True, capture_output=True, timeout=300)


def main():
    archive_doi = os.environ.get('ARCHIVE_DOI') or None
    preprint_doi = os.environ.get('PREPRINT_DOI') or None
    date = edition_date()
    source = (ROOT / 'manuscript/main.md').read_text()
    for marker in ('<!-- EDITION-FRONT-MATTER -->', '<!-- EDITION-DECLARATIONS -->'):
        assert source.count(marker) == 1, marker
    abstract = source.split('## Abstract\n', 1)[1].strip().split('\n\n', 1)[0]
    assert len(abstract.split()) <= 200, len(abstract.split())
    supplement = (ROOT / 'manuscript/supplement.md').read_text()
    outputs = []
    for edition in ('jib-submission', 'preprint'):
        journal = edition == 'jib-submission'
        folder = OUT / edition
        if folder.exists():
            shutil.rmtree(folder)
        folder.mkdir(parents=True)
        text = source.replace('<!-- EDITION-FRONT-MATTER -->', front('journal' if journal else 'preprint', date, preprint_doi))
        text = text.replace('<!-- EDITION-DECLARATIONS -->', availability(archive_doi) + '\n' + ETHICS)
        for bad in ('Internal', 'EDITION-', 'review package', 'author checklist', 'Academic'):
            assert bad not in text, (edition, bad)
        if journal:
            body, back, nfig, ntab = journal_layout(text)
            assert (nfig, ntab) == (3, 3), (nfig, ntab)
            text = body + back
        src = folder / 'manuscript.md'
        src.write_text(text)
        pandoc(src, folder / 'manuscript.docx')
        style_docx(folder / 'manuscript.docx', journal)
        sup = supplement
        if not journal:
            sup = re.sub(r'^(# [^\n]+\n)', r'\1\n**Preprint — not peer reviewed.** Version 1.0, ' + date + '.\n', sup, count=1)
        (folder / 'supplementary-information.md').write_text(sup)
        pandoc(folder / 'supplementary-information.md', folder / 'supplementary-information.docx')
        style_docx(folder / 'supplementary-information.docx', False)
        to_pdf([folder / 'manuscript.docx', folder / 'supplementary-information.docx'], folder)
        if journal:
            for n, stem in enumerate(['figure1-qualification-ladder', 'figure1-performance', 'figure2-comparisons'], 1):
                for ext in ('pdf', 'png'):
                    shutil.copy2(ROOT / 'figures' / f'{stem}.{ext}', folder / f'Figure{n}.{ext}')
            cover = ROOT / 'dossier/cover-letter-jib.md'
            pandoc(cover, folder / 'cover-letter.docx')
            style_docx(folder / 'cover-letter.docx', False)
            to_pdf([folder / 'cover-letter.docx'], folder)
        outputs += [p for p in folder.iterdir() if p.suffix in ('.docx', '.pdf', '.png')]
    (OUT / 'SHA256SUMS.txt').write_text(''.join(
        f'{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.relative_to(OUT)}\n' for p in sorted(outputs)))
    print(f'abstract {len(abstract.split())} words; archive DOI {archive_doi}; preprint DOI {preprint_doi}; '
          f'{len(outputs)} files')


if __name__ == '__main__':
    sys.exit(main())
