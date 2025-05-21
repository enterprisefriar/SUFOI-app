import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
import warnings

# Ignorer advarsler
warnings.filterwarnings("ignore")

# Konfigurer siden
st.set_page_config(
    page_title="SUFOI UFO Observationer",
    page_icon="🛸",
    layout="wide"
)

# Indlæs data
@st.cache_data
def load_data():
    df = pd.read_csv('data/sufoi_observations_cleaned.csv')
    # Konverter dato til datetime format hvis muligt
    try:
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
    except:
        pass
    return df

# Indlæs data
df = load_data()

# Udtræk postnumre fra lokation
df['postnr'] = df['location'].str.extract(r'(\d{4})').astype('str')

# Udtræk time fra start_time
df['hour'] = df['start_time'].apply(lambda x: int(x.split(':')[0]) if isinstance(x, str) and ':' in x else None)

# Sidehoved
st.title("🛸 SUFOI UFO Observationer i Danmark")
st.write("Analyse af UFO-observationer indrapporteret til SUFOI fra 1996 til 2024")

# Sidebar med filtre
st.sidebar.header("Filtre")

# År filter
min_year = int(df['year'].min())
max_year = int(df['year'].max())
year_range = st.sidebar.slider("Vælg årsinterval", min_year, max_year, (min_year, max_year))

# Farve filter
all_colors = sorted(df['colors'].dropna().unique())
colors = st.sidebar.multiselect("Vælg farver", all_colors)

# Land filter
all_countries = sorted(df['country'].dropna().unique()) if 'country' in df.columns else ["Danmark"]
countries = st.sidebar.multiselect("Vælg lande", all_countries, default=["Danmark"])

# Filtrer data baseret på valg
filtered_df = df.copy()

# Filtrer på år
filtered_df = filtered_df[(filtered_df['year'] >= year_range[0]) & (filtered_df['year'] <= year_range[1])]

# Filtrer på farver hvis valgt
if colors:
    color_filter = filtered_df['colors'].str.contains('|'.join(colors), na=False)
    filtered_df = filtered_df[color_filter]

# Filtrer på lande hvis valgt og kolonnen findes
if countries and 'country' in filtered_df.columns:
    filtered_df = filtered_df[filtered_df['country'].isin(countries)]

# Vis antal observationer
st.write(f"Antal observationer: {len(filtered_df)}")

# Opret to kolonner for de første visualiseringer
col1, col2 = st.columns(2)

# 1. KORT MED OBSERVATIONER
with col1:
    st.subheader("Geografisk fordeling af observationer")
    
    # Udtræk postnumre fra lokationskolonnen
    filtered_df['postnr'] = filtered_df['location'].str.extract(r'(\d{4})').astype(str)

    # Tæl antal observationer per postnummer
    postnr_counts = filtered_df.groupby('postnr').size().reset_index(name='antal')

    # Fjern rækker med manglende postnumre
    postnr_counts = postnr_counts[postnr_counts['postnr'] != 'nan']

    # Opret et simpelt datasæt med danske postnumre og deres koordinater
    postnr_coords = {
        '1000': (55.6761, 12.5683),  # København K
        '1050': (55.6761, 12.5683),  # København K
        '1100': (55.6761, 12.5683),  # København K
        '1200': (55.6761, 12.5683),  # København K
        '1300': (55.6761, 12.5683),  # København K
        '1400': (55.6761, 12.5683),  # København K
        '1500': (55.6761, 12.5683),  # København K
        '1600': (55.6761, 12.5683),  # København K
        '1700': (55.6761, 12.5683),  # København K
        '1800': (55.6761, 12.5683),  # København K
        '1900': (55.6761, 12.5683),  # København K
        '2000': (55.6828, 12.5307),  # Frederiksberg
        '2100': (55.7046, 12.5839),  # København Ø
        '2200': (55.6871, 12.5429),  # København N
        '2300': (55.6624, 12.5977),  # København S
        '2400': (55.6638, 12.5422),  # København NV
        '2450': (55.6638, 12.5422),  # København SV
        '2500': (55.6518, 12.4939),  # Valby
        '2600': (55.6771, 12.4587),  # Glostrup
        '2610': (55.6504, 12.3975),  # Rødovre
        '2620': (55.6504, 12.3675),  # Albertslund
        '2630': (55.6604, 12.3375),  # Taastrup
        '2640': (55.6704, 12.3075),  # Hedehusene
        '2650': (55.6304, 12.3375),  # Hvidovre
        '2660': (55.6104, 12.3375),  # Brøndby Strand
        '2670': (55.6004, 12.3075),  # Greve
        '2680': (55.5804, 12.2775),  # Solrød Strand
        '2690': (55.5604, 12.2475),  # Karlslunde
        '2700': (55.6734, 12.4262),  # Brønshøj
        '2720': (55.6934, 12.4562),  # Vanløse
        '2730': (55.7134, 12.4862),  # Herlev
        '2740': (55.7334, 12.5162),  # Skovlunde
        '2750': (55.7534, 12.5462),  # Ballerup
        '2760': (55.7734, 12.5762),  # Måløv
        '2770': (55.7934, 12.6062),  # Kastrup
        '2791': (55.6334, 12.6362),  # Dragør
        '2800': (55.7769, 12.5059),  # Lyngby
        '2820': (55.7569, 12.4759),  # Gentofte
        '2830': (55.7369, 12.4459),  # Virum
        '2840': (55.7169, 12.4159),  # Holte
        '2850': (55.8169, 12.5459),  # Nærum
        '2860': (55.8369, 12.5759),  # Søborg
        '2870': (55.8569, 12.6059),  # Dyssegård
        '2880': (55.9569, 12.5259),  # Bagsværd
        '2900': (55.7349, 12.3944),  # Hellerup
        '2920': (55.7549, 12.4244),  # Charlottenlund
        '2930': (55.7749, 12.4544),  # Klampenborg
        '2942': (55.7949, 12.4844),  # Skodsborg
        '2950': (55.8149, 12.5144),  # Vedbæk
        '2960': (55.8349, 12.5444),  # Rungsted Kyst
        '2970': (55.8549, 12.5744),  # Hørsholm
        '2980': (55.8749, 12.6044),  # Kokkedal
        '2990': (55.8949, 12.6344),  # Nivå
        '3000': (56.0392, 12.6118),  # Helsingør
        '3460': (55.9849, 12.5244),  # Birkerød
        '3500': (55.9349, 12.3044),  # Værløse
        '3520': (55.8849, 12.1744),  # Farum
        '3540': (55.8349, 12.0444),  # Lynge
        '3600': (55.9349, 12.3044),  # Frederikssund
        '4000': (55.4613, 11.7996),  # Roskilde
        '4100': (55.4513, 11.7896),  # Ringsted
        '4200': (55.4413, 11.7796),  # Slagelse
        '4300': (55.4313, 11.7696),  # Holbæk
        '4400': (55.4213, 11.7596),  # Kalundborg
        '4500': (55.4113, 11.7496),  # Nykøbing Sjælland
        '4600': (55.4013, 11.7396),  # Køge
        '4700': (55.3913, 11.7296),  # Næstved
        '4800': (55.3813, 11.7196),  # Nykøbing Falster
        '4900': (55.3713, 11.7096),  # Nakskov
        '5000': (55.4038, 10.4024),  # Odense
        '5200': (55.3938, 10.3924),  # Odense V
        '5230': (55.3838, 10.3824),  # Odense M
        '5250': (55.3738, 10.3724),  # Odense SV
        '5270': (55.3638, 10.3624),  # Odense N
        '5300': (55.3538, 10.3524),  # Kerteminde
        '5400': (55.3438, 10.3424),  # Bogense
        '5500': (55.3338, 10.3324),  # Middelfart
        '5600': (55.3238, 10.3224),  # Faaborg
        '5700': (55.3138, 10.3124),  # Svendborg
        '5800': (55.3038, 10.3024),  # Nyborg
        '5900': (55.2938, 10.2924),  # Rudkøbing
        '6000': (55.4904, 9.4731),   # Kolding
        '6100': (55.4804, 9.4631),   # Haderslev
        '6200': (55.4704, 9.4531),   # Aabenraa
        '6300': (55.4604, 9.4431),   # Gråsten
        '6400': (55.4504, 9.4331),   # Sønderborg
        '6500': (55.4404, 9.4231),   # Vojens
        '6600': (55.4304, 9.4131),   # Vejen
        '6700': (55.4204, 9.4031),   # Esbjerg
        '6800': (55.4104, 9.3931),   # Varde
        '6900': (55.4004, 9.3831),   # Skjern
        '7000': (55.7089, 9.5357),   # Fredericia
        '7100': (55.6989, 9.5257),   # Vejle
        '7200': (55.6889, 9.5157),   # Grindsted
        '7300': (55.6789, 9.5057),   # Jelling
        '7400': (55.6689, 9.4957),   # Herning
        '7500': (55.6589, 9.4857),   # Holstebro
        '7600': (55.6489, 9.4757),   # Struer
        '7700': (55.6389, 9.4657),   # Thisted
        '7800': (55.6289, 9.4557),   # Skive
        '7900': (55.6189, 9.4457),   # Nykøbing Mors
        '8000': (56.1572, 10.2107),  # Aarhus
        '8200': (56.1472, 10.2007),  # Aarhus N
        '8210': (56.1372, 10.1907),  # Aarhus V
        '8220': (56.1272, 10.1807),  # Brabrand
        '8230': (56.1172, 10.1707),  # Åbyhøj
        '8240': (56.1072, 10.1607),  # Risskov
        '8250': (56.0972, 10.1507),  # Egå
        '8260': (56.0872, 10.1407),  # Viby J
        '8270': (56.0772, 10.1307),  # Højbjerg
        '8300': (56.0672, 10.1207),  # Odder
        '8400': (56.0572, 10.1107),  # Ebeltoft
        '8500': (56.0472, 10.1007),  # Grenaa
        '8600': (56.0372, 10.0907),  # Silkeborg
        '8700': (56.0272, 10.0807),  # Horsens
        '8800': (56.0172, 10.0707),  # Viborg
        '8900': (56.0072, 10.0607),  # Randers
        '9000': (57.0488, 9.9217),   # Aalborg
        '9200': (57.0388, 9.9117),   # Aalborg SV
        '9210': (57.0288, 9.9017),   # Aalborg SØ
        '9220': (57.0188, 9.8917),   # Aalborg Øst
        '9230': (57.0088, 9.8817),   # Svenstrup J
        '9240': (56.9988, 9.8717),   # Nibe
        '9260': (56.9888, 9.8617),   # Gistrup
        '9280': (56.9788, 9.8517),   # Storvorde
        '9300': (56.9688, 9.8417),   # Sæby
        '9400': (56.9588, 9.8317),   # Nørresundby
        '9500': (56.9488, 9.8217),   # Hobro
        '9600': (56.9388, 9.8117),   # Aars
        '9700': (56.9288, 9.8017),   # Brønderslev
        '9800': (56.9188, 9.7917),   # Hjørring
        '9900': (56.9088, 9.7817),   # Frederikshavn
    }

    # Tilføj koordinater til postnumre
    postnr_map_data = []
    for _, row in postnr_counts.iterrows():
        postnr = row['postnr']
        if postnr in postnr_coords:
            lat, lon = postnr_coords[postnr]
            postnr_map_data.append({
                'postnr': postnr,
                'antal': row['antal'],
                'lat': lat,
                'lon': lon
            })

    # Opret dataframe til kortet
    if postnr_map_data:
        map_df = pd.DataFrame(postnr_map_data)
        
        # Opret kortet med Plotly
        fig = px.scatter_mapbox(
            map_df, 
            lat="lat", 
            lon="lon", 
            size="antal",
            color="antal",
            hover_name="postnr",
            hover_data=["antal"],
            color_continuous_scale=px.colors.sequential.Viridis,
            size_max=25,
            zoom=6,
            height=500,
            title="UFO-observationer fordelt på postnumre"
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            mapbox=dict(
                center=dict(lat=56.0, lon=10.0),  # Centrér kortet over Danmark
                zoom=6
            ),
            margin={"r":0, "t":30, "l":0, "b":0}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ikke nok postnumre med koordinater til at vise kortet.")

# 2. OBSERVATIONER I FORHOLD TIL DØGNET
with col2:
    st.subheader("Observationer i forhold til døgnet")
    
    # Beregn time-fordeling
    hour_counts = filtered_df['hour'].value_counts().reset_index()
    hour_counts.columns = ['time', 'antal']
    hour_counts = hour_counts.sort_values('time')
    
    # Opret figur med to y-akser
    fig = go.Figure()
    
    # Tilføj søjlediagram for observationer per time
    fig.add_trace(go.Bar(
        x=hour_counts['time'],
        y=hour_counts['antal'],
        name='Antal observationer',
        marker_color='blue'
    ))
    
    # Tilføj markører for gennemsnitlig solopgang og solnedgang
    # Dette er forenklet - ideelt set ville du beregne gennemsnit for de faktiske datoer
    fig.add_shape(
        type="line",
        x0=5, x1=5,  # Solopgang ca. kl. 5 (gennemsnit)
        y0=0, y1=hour_counts['antal'].max() if not hour_counts.empty else 100,
        line=dict(color="orange", width=2, dash="dash"),
        name="Gennemsnitlig solopgang"
    )
    
    fig.add_shape(
        type="line",
        x0=21, x1=21,  # Solnedgang ca. kl. 21 (gennemsnit)
        y0=0, y1=hour_counts['antal'].max() if not hour_counts.empty else 100,
        line=dict(color="red", width=2, dash="dash"),
        name="Gennemsnitlig solnedgang"
    )
    
    # Tilføj annotation
    if not hour_counts.empty:
        fig.add_annotation(
            x=5, y=hour_counts['antal'].max(),
            text="Solopgang",
            showarrow=True,
            arrowhead=1,
            ax=40, ay=-30
        )
        
        fig.add_annotation(
            x=21, y=hour_counts['antal'].max(),
            text="Solnedgang",
            showarrow=True,
            arrowhead=1,
            ax=-40, ay=-30
        )
    
    # Opdater layout
    fig.update_layout(
        title="UFO-observationer fordelt over døgnet",
        xaxis_title="Time på døgnet",
        yaxis_title="Antal observationer",
        legend_title="Forklaring",
        xaxis=dict(
            tickmode='linear',
            tick0=0,
            dtick=2
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)

# Opret to kolonner for de næste visualiseringer
col3, col4 = st.columns(2)

# 3. VARIGHED AF OBSERVATIONER
with col3:
    st.subheader("Varighed af observationer")
    
    # Konverter varighed til minutter for bedre visualisering
    filtered_df['duration_minutes'] = filtered_df['duration_seconds'] / 60
    
    # Fjern ekstreme værdier
    duration_df = filtered_df[filtered_df['duration_minutes'] > 0]
    duration_df = duration_df[duration_df['duration_minutes'] < 120]  # Begræns til 2 timer
    
    # Kategoriser varighed
    duration_bins = [0, 1, 5, 15, 30, 60, 120]
    duration_labels = ['<1 min', '1-5 min', '5-15 min', '15-30 min', '30-60 min', '1-2 timer']
    
    duration_df['duration_category'] = pd.cut(
        duration_df['duration_minutes'], 
        bins=duration_bins, 
        labels=duration_labels, 
        include_lowest=True
    )
    
    # Tæl observationer per kategori
    duration_counts = duration_df['duration_category'].value_counts().reset_index()
    duration_counts.columns = ['Varighed', 'Antal']
    
    # Sorter efter varighedskategori
    duration_counts['Varighed'] = pd.Categorical(
        duration_counts['Varighed'], 
        categories=duration_labels, 
        ordered=True
    )
    duration_counts = duration_counts.sort_values('Varighed')
    
    # Opret visualisering
    fig = px.bar(
        duration_counts, 
        x='Varighed', 
        y='Antal',
        color='Antal',
        color_continuous_scale=px.colors.sequential.Viridis,
        title="Fordeling af UFO-observationernes varighed"
    )
    
    st.plotly_chart(fig, use_container_width=True)

# 4. OBSERVATIONER PER MÅNED OG ÅR (HEATMAP)
with col4:
    st.subheader("Observationer per måned og år")
    
    # Udtræk måned fra dato
    if pd.api.types.is_datetime64_any_dtype(filtered_df['date']):
        filtered_df['month'] = filtered_df['date'].dt.month
    else:
        # Forsøg at udtrække måned fra dato-streng
        try:
            filtered_df['month'] = filtered_df['date'].str.extract(r'-(\d{2})-').astype(float)
        except:
            # Fallback hvis det ikke virker
            filtered_df['month'] = np.nan
    
    # Konverter år og måned til strenge for at undgå grupperingsproblemer
    filtered_df['year_str'] = filtered_df['year'].astype(str)
    filtered_df['month_str'] = filtered_df['month'].astype(str)

    # Tæl observationer per år og måned
    year_month_counts = filtered_df.groupby(['year_str', 'month_str']).size().reset_index(name='count')

    # Opret pivot-tabel manuelt
    pivot_data = {}
    for _, row in year_month_counts.iterrows():
        year = row['year_str']
        month = row['month_str']
        count = row['count']
        
        if year not in pivot_data:
            pivot_data[year] = {}
        
        pivot_data[year][month] = count

    # Konverter til DataFrame
    years = sorted(pivot_data.keys())
    months = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12']
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']

    # Opret tom DataFrame
    heatmap_data = []
    for year in years:
        for i, month in enumerate(months):
            count = pivot_data.get(year, {}).get(month, 0)
            heatmap_data.append({
                'År': year,
                'Måned': month_names[i],
                'Antal': count,
                'Måned_nr': i  # For at sortere månederne korrekt
            })

    heatmap_df = pd.DataFrame(heatmap_data)

    # Opret heatmap
    fig = px.density_heatmap(
        heatmap_df,
        x='Måned',
        y='År',
        z='Antal',
        color_continuous_scale='Viridis',
        category_orders={"Måned": month_names},
        labels={'Antal': 'Observationer'},
        title="UFO-observationer per måned og år"
    )

    fig.update_layout(
        xaxis_title="Måned",
        yaxis_title="År",
        xaxis={'categoryarray': month_names}
    )

    st.plotly_chart(fig, use_container_width=True)

# 5. FARVEFORDELING
st.subheader("Farvefordeling af UFO-observationer")

# Opdel farver (da nogle observationer har flere farver adskilt af komma)
color_data = []
for colors_str in filtered_df['colors'].dropna():
    for color in colors_str.split(','):
        color = color.strip()
        if color:
            color_data.append(color)

color_counts = pd.Series(color_data).value_counts().reset_index()
color_counts.columns = ['color', 'antal']
color_counts = color_counts.head(10)  # Top 10 farver

# Opret to kolonner for farvevisualisering
col5, col6 = st.columns(2)

with col5:
    # Søjlediagram for farver
    fig = px.bar(
        color_counts, 
        x='color', 
        y='antal',
        color='color',
        title="Top 10 farver observeret i UFO-observationer"
    )
    st.plotly_chart(fig, use_container_width=True)

with col6:
    # Cirkeldiagram for farver
    fig = px.pie(
        color_counts, 
        values='antal', 
        names='color', 
        title="Fordeling af farver i UFO-observationer",
        hole=0.4
    )
    st.plotly_chart(fig, use_container_width=True)

# Vis data tabel
st.subheader("Observationsdata")

# Tilføj søgefunktion
search_term = st.text_input("Søg i observationer (f.eks. by, farve, beskrivelse):")
if search_term:
    search_results = filtered_df[
        filtered_df.astype(str).apply(
            lambda row: row.str.contains(search_term, case=False).any(), 
            axis=1
        )
    ]
    st.dataframe(search_results)
else:
    st.dataframe(filtered_df)

# Download knap
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download filtrerede data som CSV",
    data=csv,
    file_name="ufo_observationer_filtreret.csv",
    mime="text/csv",
)

# Vis information om projektet
st.sidebar.markdown("---")
st.sidebar.info("""
### Om projektet
Denne app visualiserer data fra SUFOI's database over UFO-observationer i Danmark og omegn. 
Dataene er indsamlet fra SUFOI's hjemmeside og renset for at sikre konsistens og brugbarhed.

Data dækker perioden 1996-2024 med over 4.500 observationer.
""")
