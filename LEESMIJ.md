# Rantsoen & Voersaldo – losse app

Deze map is de complete app. Hij draait zonder Claude. Alle gegevens (bedrijven, voeders, kuilanalyses, rantsoenen, logo's) worden op de telefoon zelf bewaard.

De app moet één keer op een website staan, zodat je hem op de telefoon kunt installeren. Daarna werkt hij ook zonder internet. Met internet haalt hij zelf de nieuwste prijzen op.

Hieronder staat hoe je de app gratis online zet met GitHub. Dat doe je één keer, op een computer; het kost ongeveer een kwartier.

---

## 1. App online zetten (eenmalig, op de computer)

1. Maak een gratis account op **github.com** (knop *Sign up*).
2. Klik rechtsboven op **+** → **New repository**.
   - *Repository name*: bijvoorbeeld `rantsoen`
   - Kies **Public**. Alleen de app en de prijzen komen hierin te staan, geen bedrijfsgegevens.
   - Klik **Create repository**.
3. Ga in de repository naar **Settings** → **Pages**. Kies bij *Source*: **GitHub Actions**.
4. Ga terug naar het tabblad **Code** en klik op **uploading an existing file** (of **Add file** → **Upload files**).
   Sleep **alle bestanden en mappen uit deze map** in het venster: `index.html`, `manifest.webmanifest`, `sw.js`, `prijzen.json`, `LEESMIJ.md`, en de mappen `icons`, `scripts` en `.github`. Klik **Commit changes**.
5. Controleer of de map `.github` is meegekomen. Mac en Windows verbergen mappen die met een punt beginnen.
   Staat hij niet in de lijst, maak het bestand dan zelf aan:
   - **Add file** → **Create new file**.
   - Naam: `.github/workflows/publiceren.yml`.
   - Plak de inhoud van dat bestand uit deze map erin en klik **Commit changes**.
6. Open het tabblad **Actions**. Na een minuut staat er een groen vinkje bij *Publiceren en prijzen bijwerken*.
   Je app staat nu op: `https://JOUW-GEBRUIKERSNAAM.github.io/rantsoen/`

## 2. Op de telefoon installeren

**iPhone**
1. Open het adres in **Safari**.
2. Tik onderin op de deelknop (vierkantje met pijl omhoog).
3. Kies **Zet op beginscherm** en tik op **Voeg toe**.

**Android**
1. Open het adres in **Chrome**.
2. Tik op **Installeren** in de melding onderin, of op de drie puntjes → **App installeren** / **Toevoegen aan startscherm**.

De app staat nu met een eigen icoon op het beginscherm en opent zonder adresbalk.

## 3. Jullie gegevens uit de Claude-versie overzetten

Je hebt van Claude het bestand `rantsoen-backup-uit-claude.json` gekregen. Daarin staan Melkveebedrijf Van Raaij (met logo) en het Voorbeeldbedrijf.

1. Zet het bestand op de telefoon, bijvoorbeeld door het naar jezelf te mailen en de bijlage te bewaren in *Bestanden* (iPhone) of *Downloads* (Android).
2. Open de app → **Bedrijf** → **Back-up terugzetten** → kies het bestand → **Ja, terugzetten**.

**Upload dit bestand niet naar GitHub**: de repository is openbaar.

## 4. Back-ups

Alles staat alleen op de telefoon. Is de telefoon kapot of kwijt, dan zijn de gegevens weg.

- Maak regelmatig een back-up via **Bedrijf** → **Back-up maken**, en bewaar die in je mail of cloudopslag.
- Met dezelfde back-up zet je alles over naar een andere telefoon.
- Gebruik je de app op twee telefoons, dan zijn dat twee aparte kopieën; wijzigingen gaan niet automatisch over.

## 5. Prijzen

- Op de **1e en 15e van elke maand** haalt GitHub automatisch de nieuwste WUR-voederwaardeprijzen en de FrieslandCampina-garantieprijs op en zet ze in `prijzen.json`.
- Opent de app met internet, dan neemt hij nieuwere prijzen vanzelf over. Op het tabblad Prijzen kun je ook op **Nu ophalen** tikken.
- Direct bijwerken kan ook: tabblad **Actions** → *Publiceren en prijzen bijwerken* → **Run workflow**.
- **Mislukt het ophalen**, bijvoorbeeld doordat WUR of FrieslandCampina hun website hebben veranderd, dan krijgt de run een waarschuwing en blijven de oude prijzen staan. Vul de prijzen dan zelf in: app → **Prijzen** → **Zelf invullen**.
- GitHub zet geplande taken uit als er in een openbare repository 60 dagen niets verandert. Omdat de prijzen elke maand wijzigen, gebeurt dat normaal niet. Staat de taak toch uit, zet hem dan weer aan onder **Actions**.

## 6. De app aanpassen

Wil je later een nieuwe versie van de app gebruiken?

1. Vervang `index.html` in de repository.
2. Verhoog in `sw.js` het versienummer, bijvoorbeeld `rantsoen-v1` → `rantsoen-v2`.

De telefoons halen de nieuwe versie op als de app de volgende keer met internet opent.

## Bestanden

| Bestand | Wat het doet |
|---|---|
| `index.html` | de app zelf |
| `manifest.webmanifest`, `icons/` | naam en icoon voor installatie op de telefoon |
| `sw.js` | zorgt dat de app zonder internet werkt |
| `prijzen.json` | de actuele voer- en melkprijzen |
| `scripts/prijzen_bijwerken.py` | haalt nieuwe prijzen op |
| `.github/workflows/publiceren.yml` | zet de app online en draait de prijsupdate |

Bronnen van de prijzen: Wageningen Livestock Research (voederwaardeprijzen rundvee) en FrieslandCampina (garantieprijs). Normen: CVB Tabellenboek Voeding Herkauwers (VEM2022). De app is een rekenhulp; bespreek grote wijzigingen in het rantsoen met je voeradviseur.
