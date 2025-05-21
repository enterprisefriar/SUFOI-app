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
        # Her indsættes din postnummer-koordinat mapping
        # Forkortet for læsbarhed
    }

    # Opret en DataFrame til st.map
    map_data = []
    for _, row in postnr_counts.iterrows():
        postnr = row['postnr']
        if postnr in postnr_coords:
            lat, lon = postnr_coords[postnr]
            # Tilføj et punkt for hver observation
            for _ in range(min(row['antal'], 10)):  # Begræns til 10 punkter per postnummer for at undgå overbelastning
                map_data.append({
                    'latitude': lat + (np.random.random() - 0.5) * 0.01,  # Tilføj lidt tilfældighed for at undgå overlap
                    'longitude': lon + (np.random.random() - 0.5) * 0.01
                })
    
    if map_data:
        map_df = pd.DataFrame(map_data)
        
        # Brug Streamlit's indbyggede kortfunktion
        st.map(map_df)
        
        # Vis også en tabel med top 10 postnumre med flest observationer
        st.subheader("Top 10 postnumre med flest observationer")
        top_postnr = postnr_counts.sort_values('antal', ascending=False).head(10)
        st.dataframe(top_postnr)
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

# Definer en farvepalet, der matcher de faktiske farvenavne
color_palette = {
    'rød': 'red',
    'grøn': 'green',
    'blå': 'blue',
    'gul': 'yellow',
    'hvid': 'lightgray',
    'sort': 'black',
    'orange': 'orange',
    'lilla': 'purple',
    'brun': 'brown',
    'grå': 'gray',
    'turkis': 'turquoise',
    'pink': 'pink',
    'sølv': 'silver'
}

# Opret to kolonner for farvevisualisering
col5, col6 = st.columns(2)

with col5:
    # Søjlediagram for farver
    fig = px.bar(
        color_counts, 
        x='color', 
        y='antal',
        color='color',
        color_discrete_map=color_palette,  # Brug vores farvepalet
        title="Top 10 farver observeret i UFO-observationer"
    )
    st.plotly_chart(fig, use_container_width=True)

with col6:
    # Cirkeldiagram for farver
    fig = px.pie(
        color_counts, 
        values='antal', 
        names='color', 
        color='color',
        color_discrete_map=color_palette,  # Brug vores farvepalet
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
