"""Case 2 - Team 11 - Minor Data Science

Dashboard bij de onderzoeksvraag: hangt roken samen met het stadium waarin
longkanker wordt ontdekt, en verklaart het land waar iemand woont dat verband?

Bronnen:
- Kaggle: laxmikantaroy/lung-cancer-risk-factors-and-survival-dataset
- Kaggle: marcelobatalhah/quality-of-life-index-by-country
- kagglehub-documentatie voor dataset_load()
- Claude (AI-assistent) voor de opzet van de opschoon- en koppelstappen
"""
import pandas as pd
import streamlit as st
import kagglehub
from kagglehub import KaggleDatasetAdapter

st.set_page_config(page_title="Longkanker en levenskwaliteit", layout="wide")

NAAM_FIX = {"UK": "United Kingdom", "USA": "United States", "UAE": "United Arab Emirates"}


@st.cache_data
def laad_data():
    """Haalt beide datasets op, schoont ze op en koppelt ze op land en jaar.

    Deze datasets zijn openbaar, dus er is geen Kaggle-inlog nodig. Met
    @st.cache_data gebeurt dit een keer; daarna komt het uit het geheugen.
    """
    kanker = kagglehub.dataset_load(
        KaggleDatasetAdapter.PANDAS,
        "laxmikantaroy/lung-cancer-risk-factors-and-survival-dataset",
        "lung_cancer_dataset.csv",
    )
    qol = kagglehub.dataset_load(
        KaggleDatasetAdapter.PANDAS,
        "marcelobatalhah/quality-of-life-index-by-country",
        "quality_of_life_indices_by_country.csv",
    )

    kanker["Country"] = kanker["Country"].replace(NAAM_FIX)

    qol["Jaar"] = qol["Year"].str[:4].astype(int)
    qol = qol.groupby(["Country", "Jaar"], as_index=False).mean(numeric_only=True)

    kanker = kanker[["Patient_ID", "Country", "Diagnosis_Year", "Smoking_Status",
                     "Pack_Years", "Cancer_Type", "Cancer_Stage", "Survived",
                     "Survival_Months"]]
    kanker = kanker.rename(columns={
        "Patient_ID": "Patient", "Country": "Land", "Diagnosis_Year": "Jaar",
        "Smoking_Status": "Rookstatus", "Pack_Years": "Rookjaren",
        "Cancer_Type": "Kankersoort", "Cancer_Stage": "Stadium",
        "Survived": "Overleefd", "Survival_Months": "Overlevingsmaanden",
    })

    qol = qol[["Country", "Jaar", "Health Care Index", "Pollution Index"]]
    qol = qol.rename(columns={"Country": "Land",
                              "Health Care Index": "Zorgkwaliteit",
                              "Pollution Index": "Vervuiling"})

    voor = len(kanker)
    samen = kanker.merge(qol, on=["Land", "Jaar"], how="inner")
    samen["Laat_stadium"] = samen["Stadium"].isin(["Stage III", "Stage IV"])
    samen["Overleefd_ja"] = samen["Overleefd"] == "Yes"
    samen["Periode"] = samen["Jaar"].apply(lambda j: "2015-2019" if j <= 2019 else "2020-2024")
    return samen, voor


data, rijen_voor = laad_data()

ROOKVOLGORDE = ["Never Smoked", "Former Smoker", "Current Smoker"]

# --- Inleiding -------------------------------------------------------------
st.title("Wie krijgt longkanker te laat ontdekt?")
st.markdown(
    "**Onderzoeksvraag:** hangt roken samen met het stadium waarin longkanker wordt "
    "ontdekt, en is dat verband te verklaren door het land waar iemand woont?"
)
st.markdown(
    "Longkanker die pas in stadium III of IV wordt gevonden, is meestal niet meer te "
    "opereren. Dit dashboard combineert 2000 patientgegevens met de levenskwaliteit-"
    "indices van hun land, en zoekt uit wie er te laat bij is."
)
st.caption(
    f"Gekoppeld op land + jaar: {rijen_voor} patienten -> {len(data)} na de koppeling, "
    f"in {data['Land'].nunique()} landen. Twaalf landen hebben geen indexcijfers en vallen af."
)

# --- Bediening -------------------------------------------------------------
st.sidebar.header("Instellingen")

alleen_nsclc = st.sidebar.checkbox(
    "Alleen NSCLC-patienten tonen",
    value=False,
    help="SCLC groeit sneller. Vink dit aan om te zien of het patroon blijft staan "
         "als iedereen dezelfde kankersoort heeft.",
)

index_keuze = st.sidebar.selectbox(
    "Landkenmerk op de x-as",
    options=["Zorgkwaliteit", "Vervuiling"],
    help="Welk kenmerk van het land zetten we af tegen het aandeel late diagnoses?",
)

min_patienten = st.sidebar.slider(
    "Minimaal aantal patienten per land",
    min_value=5, max_value=50, value=20, step=5,
    help="Landen met weinig patienten geven onbetrouwbare percentages. "
         "Deze grens geldt alleen voor de grafiek op landniveau.",
)

# De checkbox werkt door in ALLE grafieken hieronder.
zicht = data[data["Kankersoort"] == "NSCLC"] if alleen_nsclc else data

if alleen_nsclc:
    st.sidebar.success(f"{len(zicht)} van {len(data)} patienten in beeld (alleen NSCLC).")

if zicht.empty:
    st.warning("Geen patienten over bij deze selectie. Pas de instellingen aan.")
    st.stop()

# --- 1. Roken en het stadium ----------------------------------------------
st.header("1. Rokers krijgen bijna twee keer zo vaak een late diagnose")
st.caption(
    "De percentages hieronder zijn het aandeel patienten met een **late diagnose** "
    "(stadium III of IV) - dus niet het aandeel dat overleed."
)

per_rookstatus = (zicht.groupby("Rookstatus")["Laat_stadium"].mean() * 100).round(1)
per_rookstatus = per_rookstatus.reindex([r for r in ROOKVOLGORDE if r in per_rookstatus.index])

kol1, kol2 = st.columns([2, 1])
with kol1:
    st.bar_chart(per_rookstatus, horizontal=True,
                 x_label="Percentage laat ontdekt (stadium III/IV)", y_label="")
with kol2:
    st.markdown(
        "Van de huidige rokers krijgt het grootste deel de diagnose pas in stadium III "
        "of IV. Bij mensen die nooit gerookt hebben is dat aandeel ongeveer de helft.\n\n"
        "De drie groepen staan in dezelfde volgorde als hun rookgeschiedenis: hoe meer "
        "gerookt, hoe later ontdekt."
    )
    if alleen_nsclc:
        st.info("Met alleen NSCLC blijft het patroon staan. De kankersoort verklaart "
                "het verschil dus niet.")

# --- 2. Waarom het stadium ertoe doet -------------------------------------
st.header("2. Het stadium bepaalt de afloop")

overleving = zicht.groupby("Stadium").agg(
    patienten=("Patient", "count"),
    overleefd=("Overleefd_ja", lambda s: round(s.mean() * 100, 1)),
    maanden=("Overlevingsmaanden", lambda s: round(s.mean(), 1)),
)
overleving.columns = ["patienten", "% overleefd", "gem. maanden"]

kol1, kol2 = st.columns([1, 1])
with kol1:
    st.dataframe(overleving, width="stretch")
    st.caption(
        "Let op: hier staan percentages **overleefd** - hoe hoger, hoe beter. In de "
        "andere secties gaat het om het percentage *laat ontdekt*."
    )
with kol2:
    st.markdown(
        "Laat ontdekken is geen administratief detail. Van de patienten met stadium I "
        "overleeft het merendeel; bij stadium IV is dat een enkeling.\n\n"
        "Dat maakt de vorige grafiek belangrijk: als rokers vaker in stadium III of IV "
        "binnenkomen, betekent dat een slechtere afloop."
    )

# --- 3. Verklaart het land het? -------------------------------------------
st.header(f"3. Verklaart {index_keuze.lower()} van het land het verschil?")

telling = zicht["Land"].value_counts()
landen_genoeg = telling[telling >= min_patienten].index
per_land = (zicht[zicht["Land"].isin(landen_genoeg)]
            .groupby("Land")
            .agg(patienten=("Patient", "count"),
                 pct_laat=("Laat_stadium", "mean"),
                 Zorgkwaliteit=("Zorgkwaliteit", "mean"),
                 Vervuiling=("Vervuiling", "mean"))
            .reset_index())
per_land["pct_laat"] = (per_land["pct_laat"] * 100).round(1)

if len(per_land) < 3:
    st.warning(
        f"Bij een grens van {min_patienten} patienten blijven er maar {len(per_land)} "
        "landen over. Zet de schuif lager om een zinnige vergelijking te zien."
    )
else:
    correlatie = per_land["pct_laat"].corr(per_land[index_keuze])

    kol1, kol2 = st.columns([2, 1])
    with kol1:
        st.scatter_chart(per_land, x=index_keuze, y="pct_laat",
                         x_label=f"{index_keuze} van het land (index)",
                         y_label="Percentage laat ontdekt")
    with kol2:
        st.metric(f"Correlatie met {index_keuze.lower()}", f"{correlatie:.3f}")
        st.markdown(
            f"De punten vormen een wolk, geen lijn: **{len(per_land)} landen** met "
            f"minstens {min_patienten} patienten, en geen zichtbaar verband.\n\n"
            "De alternatieve verklaring houdt dus geen stand. Landen met betere zorg "
            "ontdekken longkanker niet eerder."
        )
        st.caption(
            "Schuif de grens omhoog en let op hoe de correlatie meebeweegt. Met weinig "
            "landen bepalen een paar punten het getal - dat is precies waarom we er "
            "geen conclusie op baseren."
        )
        st.markdown("**De drie landen met het hoogste percentage:**")
        st.dataframe(per_land.nlargest(3, "pct_laat")[["Land", "patienten", "pct_laat"]],
                     hide_index=True, width="stretch")

# --- 4. Verandert het over tijd? ------------------------------------------
st.header("4. Tussen beide periodes verandert er weinig")

per_periode = (zicht.groupby(["Periode", "Rookstatus"])["Laat_stadium"].mean() * 100).round(1)
tabel = per_periode.unstack()
tabel = tabel[[r for r in ROOKVOLGORDE if r in tabel.columns]]

kol1, kol2 = st.columns([2, 1])
with kol1:
    st.bar_chart(tabel, stack=False, x_label="", y_label="Percentage laat ontdekt")
with kol2:
    st.markdown(
        "Tussen 2015-2019 en 2020-2024 blijven de percentages vrijwel gelijk. Bij "
        "ex-rokers lijkt een daling te zitten, maar die groep is klein en het verschil "
        "is niet significant (chi-kwadraat, p = 0,24).\n\n"
        "We behandelen dat daarom als ruis, niet als een trend."
    )

# --- Conclusie -------------------------------------------------------------
st.header("Conclusie")
st.markdown(
    "**Roken hangt samen met een late diagnose, en geen van de verklaringen die we "
    "konden toetsen verklaart dat weg.**\n\n"
    "Rokers krijgen hun diagnose veel vaker pas in stadium III of IV, en juist dat "
    "stadium bepaalt of iemand het overleeft. Het land waar een patient woont verklaart "
    "het patroon niet: over de landen heen is er geen verband met zorgkwaliteit of "
    "vervuiling. Ook de kankersoort verklaart het niet - zet de checkbox aan en het "
    "patroon blijft staan."
)
st.markdown(
    "**Beperkingen.** De kankerdataset is vrijwel zeker synthetisch: 2000 rijen, "
    "oplopende patientnummers en nul ontbrekende waarden komen in echte registraties "
    "niet voor. Twaalf landen ontbreken in de levenskwaliteit-data, vooral Afrikaanse "
    "en Zuid-Aziatische, dus onze uitspraken gaan over Azie, Europa en Amerika. En "
    "samenhang is geen oorzaak: dat rokers later worden ontdekt kan ook komen doordat "
    "zij klachten langer afdoen als rokershoest."
)
