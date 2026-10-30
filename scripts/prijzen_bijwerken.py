"""Haalt de nieuwste voederwaardeprijzen (WUR) en de FrieslandCampina-garantieprijs op
en werkt prijzen.json bij. Draait in GitHub Actions (zie .github/workflows/publiceren.yml).

Gebruik: python scripts/prijzen_bijwerken.py prijzen.json
Exitcode 0 = gelukt (ook als er niets nieuws was), 1 = een bron kon niet gelezen worden.
"""
import datetime as dt
import html as htmlmod
import io
import json
import re
import sys
from zoneinfo import ZoneInfo

WUR_PAGINA = "https://www.wur.nl/nl/onderzoek/producten-diensten/voederwaardeprijzen-rundvee"
FC_PAGINA = "https://www.frieslandcampina.com/nl/eigendom-van-boeren/garantieprijs/"
MAANDEN = ["januari", "februari", "maart", "april", "mei", "juni", "juli",
           "augustus", "september", "oktober", "november", "december"]
HEADERS = {"User-Agent": "Mozilla/5.0 (rantsoen-app prijzen-update)"}


def getal(s):
    return float(s.replace(".", "").replace(",", "."))


def html_naar_tekst(html):
    html = re.sub(r"(?is)<(script|style|noscript)\b.*?</\1>", " ", html)
    html = re.sub(r"(?i)<br\s*/?>|</(p|div|tr|li|h\d|table|section)>", "\n", html)
    html = re.sub(r"(?s)<[^>]+>", " ", html)
    tekst = htmlmod.unescape(html).replace("\xa0", " ")
    return re.sub(r"[ \t\r\f\v]+", " ", tekst)


# ---------- WUR ----------
def wur_pdf_link(html):
    links = re.findall(r'href="([^"]+\.pdf)"', html, flags=re.I)
    links = [l for l in links if "oederwaardeprijzen" in l]
    if not links:
        raise ValueError("geen PDF-link gevonden op de WUR-pagina")
    link = links[0]  # de eerste link is 'het meest recente overzicht'
    if link.startswith("/"):
        link = "https://www.wur.nl" + link
    return link


def wur_uit_pdf_tekst(tekst):
    t = re.sub(r"[ \t]+", " ", tekst)
    # Tabel 1: jaren, datums, kVEM2022 en de eerste 'kg DVE-toeslag'-rij erna
    jaren = re.search(r"Jaar((?:\s+20\d\d)+)", t)
    datums = re.search(r"Datum((?:\s+\d{2}-\d{2})+)", t)
    kvem_rij = re.search(r"kVEM2022((?:\s+\d+,\d+)+)", t)
    if not (jaren and datums and kvem_rij):
        raise ValueError("tabel 1 niet gevonden in de WUR-PDF")
    dve_rij = re.search(r"kg DVE-toeslag((?:\s+\d+,\d+)+)", t[kvem_rij.end():])
    if not dve_rij:
        raise ValueError("DVE-toeslag niet gevonden in de WUR-PDF")
    kvem = getal(kvem_rij.group(1).split()[-1])
    dve = getal(dve_rij.group(1).split()[-1])
    dag, maand = datums.group(1).split()[-1].split("-")
    jaar = jaren.group(1).split()[-1]
    datum = f"{jaar}-{maand}-{dag}"
    # historie uit dezelfde tabel (laatste 11 publicaties)
    alle_datums = datums.group(1).split()
    alle_kvem = [getal(x) for x in kvem_rij.group(1).split()]
    alle_dve = [getal(x) for x in dve_rij.group(1).split()]
    historie = []
    if len(alle_datums) == len(alle_kvem) == len(alle_dve):
        jr = int(jaar)
        for d, k, v in reversed(list(zip(alle_datums, alle_kvem, alle_dve))):
            dd, mm = d.split("-")
            if historie and int(mm) > int(historie[-1]["datum"][5:7]):
                jr -= 1  # jaarwisseling, terug in de tijd
            historie.append({"datum": f"{jr}-{mm}-{dd}", "kvem": k, "dve": v})
        historie.reverse()
    mengvoer = {m.group(1): getal(m.group(2)) for m in re.finditer(r"melkvee\s+(90|105|120|150|180)\s+DVE\s+(\d+,\d{2})", t)}
    volgende = ""
    v = re.search(r"uiterlijk\s+\w+\s+(\d{1,2})\s+([a-z]+)\s+(20\d\d)", t, flags=re.I)
    if v and v.group(2).lower() in MAANDEN:
        volgende = f"{v.group(3)}-{MAANDEN.index(v.group(2).lower()) + 1:02d}-{int(v.group(1)):02d}"
    if not (5 < kvem < 80 and 10 < dve < 400):
        raise ValueError(f"onwaarschijnlijke WUR-waarden: kVEM {kvem}, DVE {dve}")
    return {"datum": datum, "kvem": kvem, "dveToeslag": dve, "volgende": volgende,
            "mengvoer": mengvoer, "historie": historie, "bron": WUR_PAGINA}


# ---------- FrieslandCampina ----------
MAAND_RE = r"(januari|februari|maart|april|mei|juni|juli|augustus|september|oktober|november|december)"


def _laatste_rij(stuk, n_getallen, standaardjaar):
    """Zoek in een stuk tekst de rij met de hoogste maand in het hoogste jaar.
    Een jaartal telt als kopje als het op een eigen regel staat (zoals '2026' boven een tabel)."""
    koppen = [(m.start(), int(m.group(1))) for m in re.finditer(r"(?m)^[\s#]*(20\d\d)\s*$", stuk)]
    patroon = r"(?<![a-z])" + MAAND_RE + r"\s*\|?\s*" + r"\s*\|?\s*".join([r"€?\s*(\d{1,4},\d{2})"] * n_getallen)
    beste = None
    for m in re.finditer(patroon, stuk, flags=re.I):
        jaar = standaardjaar
        for pos, j in koppen:
            if pos < m.start():
                jaar = j
        sleutel = (jaar, MAANDEN.index(m.group(1).lower()))
        if beste is None or sleutel > beste[0]:
            beste = (sleutel, [getal(m.group(i + 2)) for i in range(n_getallen)])
    return beste


def fc_uit_tekst(tekst):
    t = tekst
    i_gar = t.lower().find("garantieprijs per maand")
    i_comp = t.lower().find("lactosewaarde", i_gar if i_gar >= 0 else 0)
    i_bio = t.lower().find("biologische", i_comp if i_comp >= 0 else 0)
    if i_gar < 0 or i_comp < 0:
        raise ValueError("tabellen niet gevonden op de FrieslandCampina-pagina")
    nu = dt.datetime.now(ZoneInfo("Europe/Amsterdam")).year
    gar = _laatste_rij(t[i_gar:i_comp], 1, nu)
    comp = _laatste_rij(t[i_comp:i_bio if i_bio > 0 else len(t)], 2, nu)
    if not gar or not comp:
        raise ValueError("garantieprijs of eiwit-/vetwaarde niet gevonden")
    if gar[0] != comp[0]:
        raise ValueError(f"maand van garantieprijs {gar[0]} en eiwit-/vetwaarde {comp[0]} verschillen")
    (jaar, mi), (garantie,) = gar[0], gar[1]
    eiwitwaarde, vetwaarde = comp[1]
    std = re.search(r"eiwit\s*\((\d,\d{1,2})\s*%\)\s*en\s*vet\s*\((\d,\d{1,2})\s*%\)", t, flags=re.I)
    std_eiwit, std_vet = (getal(std.group(1)), getal(std.group(2))) if std else (3.57, 4.49)
    controle = std_eiwit / 100 * eiwitwaarde + std_vet / 100 * vetwaarde
    if not (25 < garantie < 120) or abs(controle - garantie) > 0.15:
        raise ValueError(f"melkprijs klopt niet: garantie {garantie}, controle {controle:.2f}")
    return {"maand": f"{jaar}-{mi + 1:02d}", "garantieprijs": garantie, "eiwitwaarde": eiwitwaarde,
            "vetwaarde": vetwaarde, "stdEiwit": std_eiwit, "stdVet": std_vet, "bron": FC_PAGINA}


# ---------- Samenvoegen ----------
def samenvoegen(oud, wur=None, melk=None):
    nieuw = json.loads(json.dumps(oud))
    veranderd = False
    if wur and wur["datum"] > oud.get("wur", {}).get("datum", ""):
        hist = {h["datum"]: h for h in oud.get("wur", {}).get("historie", [])}
        for h in wur.get("historie", []):
            hist[h["datum"]] = h
        hist[wur["datum"]] = {"datum": wur["datum"], "kvem": wur["kvem"], "dve": wur["dveToeslag"]}
        wur["historie"] = [hist[k] for k in sorted(hist)][-12:]
        if not wur.get("mengvoer"):
            wur["mengvoer"] = oud.get("wur", {}).get("mengvoer", {})
        nieuw["wur"] = wur
        veranderd = True
    if melk and melk["maand"] > oud.get("melk", {}).get("maand", ""):
        hist = {h["maand"]: h for h in oud.get("melk", {}).get("historie", [])}
        hist[melk["maand"]] = {"maand": melk["maand"], "garantieprijs": melk["garantieprijs"]}
        melk["historie"] = [hist[k] for k in sorted(hist)][-6:]
        melk["integraal"] = None
        nieuw["melk"] = melk
        veranderd = True
    if veranderd:
        nieuw["bijgewerkt"] = dt.datetime.now(ZoneInfo("Europe/Amsterdam")).isoformat(timespec="seconds")
    return nieuw, veranderd


def main(pad):
    import requests
    from pypdf import PdfReader

    with open(pad, encoding="utf-8") as f:
        oud = json.load(f)
    fouten = []
    wur = melk = None
    try:
        pagina = requests.get(WUR_PAGINA, headers=HEADERS, timeout=60)
        pagina.raise_for_status()
        pdf_url = wur_pdf_link(pagina.text)
        pdf = requests.get(pdf_url, headers=HEADERS, timeout=60)
        pdf.raise_for_status()
        tekst = "\n".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf.content)).pages)
        wur = wur_uit_pdf_tekst(tekst)
        print(f"WUR {wur['datum']}: {wur['kvem']} ct/kVEM, {wur['dveToeslag']} ct DVE")
    except Exception as e:  # noqa: BLE001
        fouten.append(f"WUR: {e}")
    try:
        pagina = requests.get(FC_PAGINA, headers=HEADERS, timeout=60)
        pagina.raise_for_status()
        melk = fc_uit_tekst(html_naar_tekst(pagina.text))
        print(f"Melkprijs {melk['maand']}: € {melk['garantieprijs']}")
    except Exception as e:  # noqa: BLE001
        fouten.append(f"FrieslandCampina: {e}")
    nieuw, veranderd = samenvoegen(oud, wur, melk)
    if veranderd:
        with open(pad, "w", encoding="utf-8") as f:
            json.dump(nieuw, f, ensure_ascii=False, indent=1)
        print("prijzen.json bijgewerkt")
    else:
        print("Geen nieuwe prijzen")
    for fout in fouten:
        print("LET OP:", fout, file=sys.stderr)
    return 1 if fouten else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "prijzen.json"))
