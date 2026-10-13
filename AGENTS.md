# AGENTS.md

Gedeelde regels voor alle AI-agents die in dit project werken (Claude Code,
Copilot, Continue, etc.). Dit bestand is de enige bron van waarheid; andere
agent-bestanden verwijzen hiernaar.

## Projectcontext

- Doel: jaarverslagen en jaarrekeningen van Nederlandse zorgaanbieders (o.a. RHO's) verzamelen, omzetten en analyseren.
- `RHO/`: scripts en ruwe data (`raw/`) voor het ophalen en samenstellen van RHO-gegevens.
- `jaarverslag/`: PDF's en daaruit afgeleide Markdown/tabellen.
- `.archief/`: afgerond of tijdelijk materiaal. Niet weggooien.
- `.github/skills/`: herbruikbare skills (bron). `.claude/skills` is een symlink hiernaartoe.

## Communicatie

- Communiceer met de gebruiker in het Nederlands.
- Code, identifiers, commit-messages en technische documentatie in het Engels.
- Leg technische begrippen bij eerste gebruik kort en concreet uit.

## Werkwijze

- Bij alles groter dan een kleine fix: eerst een kort plan voorleggen en op akkoord wachten.
- Kleine, afgeronde stappen. Eén wijziging per keer; geen ongevraagde refactors.
- Lees eerst bestaande code, data en skills voordat je iets nieuws bouwt.
- Bij onduidelijkheid: vraag het, raad niet.
- Wordt een taak herhaalbaar? Overweeg een skill in `.github/skills/`.

## Verificatie

- "Klaar" betekent uitgevoerd en gecontroleerd. Toon de uitvoer, niet alleen een claim.
- Meld mislukte of overgeslagen stappen eerlijk.
- Cijfers en teksten uit jaarverslagen: vermeld altijd bron (document, pagina). Verzin of rond nooit zonder dat expliciet te melden.

## Veiligheid

- Lees, toon of commit nooit secrets (`.env`, `.credentials.json`, API-keys, SSH-sleutels).
- Geen destructieve acties (`rm -rf`, overschrijven, `git push --force`, `git reset --hard`) zonder expliciete bevestiging.
- Wijzig originele bronbestanden (PDF's, ruwe data in `raw/`) niet; werk op kopieën of afgeleide bestanden.
- Externe requests alleen naar domeinen die in een skill of in deze regels genoemd zijn.

## Git

- Kleine commits met duidelijke boodschap.
- Commit of push alleen als de gebruiker erom vraagt.

## Skills

- Skills staan in `.github/skills/<naam>/SKILL.md` met frontmatter (`name`, `description` met "Use when: ...").
- Houd het aantal skills beperkt en elke `description` specifiek, zodat de juiste skill gekozen wordt.
