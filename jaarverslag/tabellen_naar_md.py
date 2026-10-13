#!/usr/bin/env python3
"""Zet de platte-tekst tabellen in maasstad_jaarrekening_2025.md om naar echte
markdown-tabellen.

Methode: tabellen worden opnieuw uit de PDF gehaald met pdfplumber op
char-niveau. Spatie-chars worden genegeerd (die overbruggen cel-grenzen);
chars worden per visuele regel gegroepeerd (top ±2.5pt) en in cellen
gesplitst op x-gaps (>10pt). Binnen cellen worden woorden weer met spaties
samengevoegd (gap > 2.5pt). Gesplitste getallen ("1 33.980") worden
gerepareerd. Per tabel worden vaste kolomgrenzen (x-ranges) gebruikt die
uit de PDF zijn opgemeten. De platte-tekst tabellen in de MD worden vervangen.
"""
import re
import pdfplumber

PDF = 'pdf/maasstad_jaarrekening_2025.pdf'
MD = 'maasstad_jaarrekening_2025.md'

# ---------------------------------------------------------------
# Extractie-hulpfuncties
# ---------------------------------------------------------------

def group_lines(page):
    """Groepeer chars per visuele regel (spaties behouden voor leesbare tekst)."""
    lines = []
    for c in sorted(page.chars, key=lambda c: (c['top'], c['x0'])):
        if lines and abs(c['top'] - lines[-1][0]) <= 2.5:
            lines[-1][1].append(c)
        else:
            lines.append([c['top'], [c]])
    return lines

def split_cells(cs, gap=10):
    """Split chars van één regel in (x, tekst) cellen op x-gaps.
    Spatie-chars worden genegeerd bij de cel-splitsing (ze overbruggen
    anders cel-grenzen); binnen cellen worden woorden gescheiden op
    non-space gaps > 1.5pt."""
    nons = [c for c in cs if c['text'] != ' ']
    if not nons:
        return []
    nons.sort(key=lambda c: c['x0'])
    cells = []
    cur = [nons[0]]
    for c in nons[1:]:
        if c['x0'] - cur[-1]['x1'] > gap:
            cells.append(cur)
            cur = [c]
        else:
            cur.append(c)
    cells.append(cur)
    out = []
    for cell in cells:
        txt = cell[0]['text']
        for a, b in zip(cell, cell[1:]):
            txt += (' ' if b['x0'] - a['x1'] > 1.5 else '') + b['text']
        out.append((round(cell[0]['x0']), ' '.join(txt.split())))
    return out

def fix_num(s):
    """Verwijder spaties in gesplitste getallen: '1 33.980' -> '133.980'."""
    t = s.replace(' ', '')
    if re.fullmatch(r'-?\d{1,3}(?:\.\d{3})*(?:,\d+)?%?', t) and ('.' in t or t.rstrip('%').isdigit()):
        return t
    return s

def row_from_cells(cells, x_ranges):
    """Map cellen op kolommen via vaste x-ranges."""
    row = []
    for lo, hi in x_ranges:
        txt = ' '.join(t for x, t in cells if lo <= x < hi).strip()
        row.append(fix_num(txt))
    return row

FOOTER = ('Deloitte', 'Voor identificatie', 'Behorend bij', 'd.d. 27 mei')

HEADER_PAT = re.compile(
    r'^(?:Ref\.|x\s*€\s*1\.000|\(€\s*x\s*1\.000\)|€|'
    r'\d{2}-dec-\d{2}|\d{4})'
    r'(?:[\s€x1\.000\-dec]*)$'
)

def is_header_row(row):
    """Kopregels: alleen Ref./x € 1.000/jaar-cellen, geen omschrijving."""
    cells = [c for c in row if c]
    if not cells:
        return False
    if any(re.search(r'[a-zA-Z]{3,}', c) for c in cells):
        # 'Ref.' en 'dec' zijn korte labels; check specifiek
        pass
    # alle cellen moeten matchen op: Ref., x € 1.000, jaar (2025/2024), 31-dec-25
    for c in cells:
        if not re.fullmatch(r'(Ref\.|x\s*€\s*1\.000|\(€\s*x\s*1\.000\)|€|'
                            r'\d{2}-dec-\d{2}|\d{4}|x|€)', c):
            return False
    return True

def extract_table(page, x_ranges, top_from=None, top_to=None):
    """Extract tabelregels met vaste kolomgrenzen; kopregels worden gefilterd."""
    rows = []
    for top, cs in group_lines(page):
        if top_from is not None and top < top_from:
            continue
        if top_to is not None and top > top_to:
            continue
        txt = ''.join(c['text'] for c in cs)
        if any(txt.startswith(f) for f in FOOTER):
            continue
        row = row_from_cells(split_cells(cs), x_ranges)
        if not any(row):
            continue
        if is_header_row(row):
            continue
        rows.append(row)
    return rows

def extract_between(page, start_txt, end_txt, x_ranges):
    """Extract regels tussen twee tekstmarkeringen; kopregels gefilterd."""
    rows = []
    started = False
    for top, cs in group_lines(page):
        txt = ' '.join(''.join(c['text'] for c in cs).split())
        if not started:
            if txt.startswith(start_txt):
                started = True
            continue
        if txt.startswith(end_txt):
            break
        if any(txt.startswith(f) for f in FOOTER):
            continue
        row = row_from_cells(split_cells(cs), x_ranges)
        if not any(row):
            continue
        if is_header_row(row):
            continue
        rows.append(row)
    return rows

def md_table(rows, header):
    """Maak een markdown-tabel met header."""
    if not rows:
        return ''
    ncol = len(header)
    out = ['| ' + ' | '.join(header) + ' |',
           '|' + '|'.join(['---'] * ncol) + '|']
    for r in rows:
        r = (list(r) + [''] * ncol)[:ncol]
        out.append('| ' + ' | '.join(c.replace('|', '\\|') for c in r) + ' |')
    return '\n'.join(out)

# ---------------------------------------------------------------
# Hoofdprogramma
# ---------------------------------------------------------------

def main():
    pdf = pdfplumber.open(PDF)
    md = open(MD).read()
    lines = md.split('\n')

    tables = {}

    # ---- Balans (pdf 37-38): omschr | ref | 25 | 24 ----
    # x: omschr <340, ref ~361-371, 25 ~406-441, 24 ~485-520
    # page 37: top 110-600; page 38: top 110-427 (na 'Totaal passiva')
    balans = []
    balans += extract_table(
        pdf.pages[37],
        [(0, 340), (340, 400), (400, 470), (470, 620)],
        top_from=110, top_to=600,
    )
    balans += extract_table(
        pdf.pages[38],
        [(0, 340), (340, 400), (400, 470), (470, 620)],
        top_from=110, top_to=427,
    )
    # paginanummer-regels (alleen getal in laatste kolom) eruit
    balans = [r for r in balans
              if not (r[0] == '' and r[1] == '' and r[2] == ''
                      and re.fullmatch(r'\d{1,3}', (r[3] or '').strip()))]
    tables['balans'] = md_table(balans, ['Omschrijving', 'Ref.', '31-dec-25', '31-dec-24'])

    # ---- W&V (pdf 39): omschr | ref | 25 | 24 ----
    # x: omschr <290, ref ~299, 25 ~335-425, 24 ~458-533; tot top 519 (RESULTAAT BOEKJAAR)
    wv = extract_table(
        pdf.pages[39],
        [(0, 290), (290, 330), (330, 440), (440, 620)],
        top_from=110, top_to=520,
    )
    tables['wv'] = md_table(wv, ['Omschrijving', 'Ref.', '2025', '2024'])

    # ---- Kasstroom (pdf 41): omschr | ref | 25 | 24 ----
    # x: omschr <295, ref ~301-305, 25 ~331-360, 24 ~447-472; tot top 556
    ks = extract_table(
        pdf.pages[41],
        [(0, 295), (295, 325), (325, 440), (440, 620)],
        top_from=110, top_to=557,
    )
    tables['kasstroom'] = md_table(ks, ['Omschrijving', 'Ref.', '2025', '2024'])

    # ---- Resultaatbestemming (pdf 40): omschr | 25 | 24 ----
    # x: omschr <380, 25 ~391-410, 24 ~514-527; tot top 500 (14.110 9.432)
    rb = extract_table(
        pdf.pages[40],
        [(0, 385), (385, 465), (465, 620)],
        top_from=95, top_to=501,
    )
    tables['resultaatbestemming'] = md_table(rb, ['Toevoeging/(onttrekking)', '2025', '2024'])

    # ---- Mutatieoverzicht immaterieel (pdf 68) ----
    # x: omschr <260, kolommen ~263/324/372-383/462/497-508; top 590-763
    mi = extract_table(
        pdf.pages[68],
        [(0, 260), (260, 320), (320, 360), (360, 450), (450, 495), (495, 620)],
        top_from=590, top_to=763,
    )
    tables['mut_imm'] = md_table(mi, ['Omschrijving', 'Kosten op-richting aandelen', 'Kosten concessies/vergunningen', 'Kosten intellectuele eigendom', 'Goodwill derden', 'Totaal'])

    # ---- Mutatieoverzicht materieel (pdf 69) ----
    # x: omschr <210, kolommen ~215-216/281-282/342-344/410-411/478-480; top 135-390
    mm = extract_table(
        pdf.pages[69],
        [(0, 210), (210, 275), (275, 335), (335, 405), (405, 470), (470, 620)],
        top_from=135, top_to=390,
    )
    tables['mut_mat'] = md_table(mm, ['Omschrijving', 'Bedrijfsgebouwen en terreinen', 'Machines en installaties', 'Overige vaste bedrijfsmiddelen', 'In uitvoering/vooruitbet.', 'Totaal'])

    # ---- Mutatieoverzicht financieel (pdf 70) ----
    # x: omschr <340, kolommen ~353/445/519/583/625/701/745; top 155-222
    mf = extract_table(
        pdf.pages[70],
        [(0, 340), (340, 420), (420, 495), (495, 560), (560, 600), (600, 670), (670, 730), (730, 790)],
        top_from=155, top_to=222,
    )
    tables['mut_fin'] = md_table(mf, ['Omschrijving', 'Deelnemingen groepsmaatsch.', 'Deelnemingen overige', 'Vorderingen verbonden', 'Vorderingen participanten', 'Overige effecten', 'Overige vorderingen', 'Totaal'])

    # ---- Ratio's (pdf 24): top 120-190 (na kopregel op 108) ----
    # x: omschr <220, 25 ~255-262, 24 ~312-319
    ratio_rows = extract_table(
        pdf.pages[24],
        [(0, 220), (220, 300), (300, 400)],
        top_from=120, top_to=190,
    )
    tables['ratio'] = md_table(ratio_rows, ['Ratio', '2025', '2024'])

    # ---- Bezetting (pdf 22): top 620-670 (na kopregel op 614) ----
    bez_rows = extract_table(
        pdf.pages[22],
        [(0, 220), (220, 300), (300, 400)],
        top_from=620, top_to=670,
    )
    tables['bezetting'] = md_table(bez_rows, ['Bezetting', '2025', '2024'])

    # ---- Investeringen (pdf 23): top 585-695 (na kopregel op 579) ----
    inv_rows = extract_table(
        pdf.pages[23],
        [(0, 250), (250, 320), (320, 430), (430, 520)],
        top_from=585, top_to=695,
    )
    tables['investeringen'] = md_table(inv_rows, ['Investering', 'Jaarrekening', 'Thema', 'Bedrag (€ mln.)'])

    # ---- Financiële baten en lasten (pdf 77) ----
    # x: omschr <400, 25 ~410-428, 24 ~480-498
    fl_rows = extract_between(pdf.pages[77], 'De specificatie is als volgt:', 'Aandeel in de winst',
                              [(0, 400), (400, 460), (460, 540)])
    tables['fin_lasten'] = md_table(fl_rows, ['Specificatie', '2025', '2024'])

    # ---- Deelnemingen (pdf 77) ----
    dn_rows = extract_between(pdf.pages[77], 'Aandeel in de winst', 'Belastingen',
                              [(0, 400), (400, 460), (460, 540)])
    tables['deelnemingen'] = md_table(dn_rows, ['Specificatie', '2025', '2024'])

    # ---- Belastingen (pdf 77) ----
    bl_rows = extract_between(pdf.pages[77], 'Belastingen', 'Wet normering',
                               [(0, 400), (400, 460), (460, 540)])
    tables['belastingen'] = md_table(bl_rows, ['Specificatie', '2025', '2024'])

    # ---------------------------------------------------------------
    # MD vervangen
    # ---------------------------------------------------------------

    def find_line(needle, from_idx=0):
        """Zoek regel die met needle begint (geen inhoudsopgave met paginanr)."""
        for i in range(from_idx, len(lines)):
            l = lines[i].strip()
            if l.startswith(needle) and not re.search(r'\s\d{1,3}$', l):
                return i
        return None

    def replace_region(start, end, new_text):
        """Vervang lines[start:end] door nieuwe tabelregels."""
        nonlocal lines
        new_lines = new_text.split('\n')
        lines = lines[:start] + new_lines + lines[end:]

    # --- Balans: kop + '(na resultaatbestemming)' blijven; tabel eronder vervangen ---
    i = find_line('Balans per 31 december 2025', 2134)
    if i is not None:
        end = None
        for k in range(i, min(i + 250, len(lines))):
            if 'Totaal passiva' in lines[k]:
                end = k + 1
                break
        if end:
            replace_region(i + 2, end, tables['balans'])

    # --- W&V: tot en met RESULTAAT BOEKJAAR-regel ---
    i = find_line('Winst- en verliesrekening over 2025', 2134)
    if i is not None:
        end = None
        for k in range(i, min(i + 250, len(lines))):
            if 'RESULTAAT BOEKJAAR' in lines[k]:
                end = k + 1
                break
        if end:
            replace_region(i + 1, end, tables['wv'])

    # --- Kasstroom: tot en met laatste 'Mutatie geldmiddelen 24.611 11.178'-regel ---
    i = find_line('Kasstroomoverzicht over 2025', 2134)
    if i is not None:
        end = None
        for k in range(i, min(i + 250, len(lines))):
            if 'Mutatie geldmiddelen' in lines[k] and '24.611' in lines[k]:
                end = k + 1
        if end:
            replace_region(i + 1, end, tables['kasstroom'])

    # --- Resultaatbestemming: tot en met '14.110 9.432'-regel ---
    i = find_line('RESULTAATBESTEMMING', 2134)
    if i is not None:
        end = None
        for k in range(i, min(i + 250, len(lines))):
            if lines[k].strip() == '14.110 9.432':
                end = k + 1
                break
        if end:
            replace_region(i + 1, end, tables['resultaatbestemming'])

    # --- Mutatieoverzichten ---
    # mut_imm: tabel op pdf 68, top 590-763; eindigt op 'Boekwaarde per 31 december 2025'
    # mut_mat: tabel op pdf 69, top 135-390; eindigt op 'Afschrijvingspercentage'
    # mut_fin: tabel op pdf 70, top 155-222; eindigt op 'Boekwaarde per 31 december 2025'
    for needle, key, endneedle in [
        ('Mutatieoverzicht immateriële vaste activa', 'mut_imm', 'Boekwaarde per 31 december 2025'),
        ('Mutatieoverzicht materiële vaste activa', 'mut_mat', 'Afschrijvingspercentage'),
        ('Mutatieoverzicht financiële vaste activa', 'mut_fin', 'Boekwaarde per 31 december 2025'),
    ]:
        i = find_line(needle, 2134)
        if i is not None:
            end = None
            for k in range(i + 1, min(i + 250, len(lines))):
                if endneedle in lines[k]:
                    end = k + 1
                    break
            if end:
                replace_region(i + 1, end, tables[key])

    # --- Ratio's (Bestuursverslag) ---
    i = find_line("Ratio's 2025 2024")
    if i is not None:
        end = None
        for k in range(i, min(i + 20, len(lines))):
            if 'EBITDA marge' in lines[k]:
                end = k + 1
                break
        if end:
            replace_region(i, end, tables['ratio'])

    # --- Bezetting (Bestuursverslag) ---
    i = find_line('Bezetting 2025 2024')
    if i is not None:
        end = None
        for k in range(i, min(i + 20, len(lines))):
            if 'Niet patiënt gebonden' in lines[k]:
                end = k + 1
                break
        if end:
            replace_region(i, end, tables['bezetting'])

    # --- Investeringen (Bestuursverslag): tot en met 'Totaal'-regel ---
    i = find_line('Investering jaarrekening Thema Bedrag (€ mln.)')
    if i is not None:
        end = None
        for k in range(i, min(i + 30, len(lines))):
            if lines[k].strip().startswith('Totaal') and '€20,4' in lines[k]:
                end = k + 1
                break
        if end:
            replace_region(i, end, tables['investeringen'])

    # --- Financiële baten en lasten (Toelichting) ---
    i = find_line('De specificatie is als volgt: 2025 2024')
    if i is not None:
        end = None
        for k in range(i, min(i + 30, len(lines))):
            if 'Totaal financiële baten en lasten' in lines[k]:
                end = k + 1
                break
        if end:
            replace_region(i, end, tables['fin_lasten'])

    # --- Deelnemingen (Toelichting) ---
    i = find_line('Aandeel in de winst/verlies van ondernemingen waarin wordt')
    if i is not None:
        j = find_line('De specificatie is als volgt: 2025 2024', i + 1)
        if j is not None:
            end = None
            for k in range(j, min(j + 30, len(lines))):
                if 'Totaal resultaat deelneming' in lines[k]:
                    end = k + 1
                    break
            if end:
                replace_region(j, end, tables['deelnemingen'])

    # --- Belastingen (Toelichting) ---
    i = None
    for cand in range(3800, len(lines)):
        if lines[cand].strip() == 'Belastingen':
            i = cand
            break
    if i is not None:
        j = find_line('De specificatie is als volgt: 2025 2024', i + 1)
        if j is not None:
            end = None
            for k in range(j, min(j + 30, len(lines))):
                if 'Totaal 0 0' in lines[k]:
                    end = k + 1
                    break
            if end:
                replace_region(j, end, tables['belastingen'])

    open(MD, 'w').write('\n'.join(lines))
    print(f"Klaar. {len(tables)} tabellen geconverteerd:")
    for name, t in tables.items():
        n = len(t.split('\n')) if t else 0
        print(f"  {name}: {n} regels")

if __name__ == '__main__':
    main()