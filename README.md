# Case 2 — Longkanker en levenskwaliteit

Team 11 · Minor Data Science

**Onderzoeksvraag:** hangt roken samen met het stadium waarin longkanker wordt ontdekt,
en is dat verband te verklaren door het land waar iemand woont?

## Wat er in staat

| Bestand | Inhoud |
|---|---|
| `app.py` | het Streamlit-dashboard |
| `analyse.ipynb` | de dataverzameling, verkenning en analyse, met uitleg per cel |
| `requirements.txt` | de benodigde packages |

## Zelf draaien

```bash
pip install -r requirements.txt
streamlit run app.py
```

De data wordt door het script zelf opgehaald bij Kaggle. Beide datasets zijn openbaar,
dus er is geen inlog of API-sleutel nodig.

## Databronnen

| Bron | Inhoud |
|---|---|
| [laxmikantaroy/lung-cancer-risk-factors-and-survival-dataset](https://www.kaggle.com/datasets/laxmikantaroy/lung-cancer-risk-factors-and-survival-dataset) | 2000 patiëntgegevens: rookstatus, stadium, overleving |
| [marcelobatalhah/quality-of-life-index-by-country](https://www.kaggle.com/datasets/marcelobatalhah/quality-of-life-index-by-country) | levenskwaliteit-indices per land per jaar |

Gekoppeld op **land + jaar**: 2000 patiënten → 1291 na de koppeling, in 48 landen.
Twaalf landen ontbreken in de levenskwaliteit-data en vallen af.

## Bevindingen

- Rokers krijgen hun diagnose veel vaker pas in stadium III of IV (66,5% tegen 37,7%
  bij mensen die nooit gerookt hebben).
- Dat stadium bepaalt de afloop: 70% overleeft stadium I, 4,4% overleeft stadium IV.
- Drie alternatieve verklaringen houden geen stand: het land (correlaties rond nul),
  de kankersoort (patroon blijft binnen NSCLC), en een dodelijkere ziekte (binnen
  hetzelfde stadium overleven rokers even vaak).

## Beperkingen

De kankerdataset is vrijwel zeker synthetisch — 2000 rijen, oplopende patiëntnummers en
nul ontbrekende waarden komen in echte registraties niet voor. De uitkomsten zijn
oefenmateriaal, geen uitspraak over de werkelijkheid.

## Bronvermelding

Naast de twee datasets en de kagglehub-documentatie is Claude (AI-assistent) gebruikt
voor de opzet van de opschoon- en koppelstappen en van het dashboard, aangepast aan onze
data. De uitleg per cel staat in `analyse.ipynb`.
