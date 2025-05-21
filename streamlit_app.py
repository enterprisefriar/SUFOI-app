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
    df = pd.read_csv('data/sufoi_observations_with_coords.csv')
    # Konverter dato til datetime format hvis muligt
    try:
        df['date'] = pd.to_datetime(df['date'], format='%d-%m-%Y', errors='coerce')
    except:
        pass
    return df

# Indlæs data
df = load_data()

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
    
    # Filtrer data til kun at inkludere rækker med gyldige koordinater
    map_data = filtered_df.dropna(subset=['latitude', 'longitude'])
    
    # Tilføj validering af koordinater hvis ikke allerede gjort
    if 'valid_coords' not in map_data.columns:
        # Danmarks omtrentlige grænser
        map_data = map_data[
            (map_data['latitude'] >= 54.5) & 
            (map_data['latitude'] <= 58.0) & 
            (map_data['longitude'] >= 8.0) & 
            (map_data['longitude'] <= 13.0)
        ]
    else:
        map_data = map_data[map_data['valid_coords'] == True]
    
    if not map_data.empty:
        # Tjek hvilke kolonner der er tilgængelige
        available_columns = map_data.columns.tolist()
        
        # Definer grupperings-kolonner baseret på hvad der er tilgængeligt
        groupby_columns = ['latitude', 'longitude']  # Disse skal være der
        
        # Tilføj postnr og by hvis de findes
        if 'postnr' in available_columns:
            groupby_columns.append('postnr')
        if 'by' in available_columns:
            groupby_columns.append('by')
        
        # Aggreger data per lokation
        city_counts = map_data.groupby(groupby_columns).size().reset_index(name='antal')
        
        # Opret Plotly-kort med variabel punktstørrelse
        hover_data = ['antal']
        if 'postnr' in city_counts.columns:
            hover_data.append('postnr')
        
        hover_name = 'by' if 'by' in city_counts.columns else None
        
        # Brug en anden kortprovider og juster indstillingerne
        fig = px.scatter_mapbox(
            city_counts,
            lat="latitude",
            lon="longitude",
            size="antal",  # Størrelse baseret på antal observationer
            color="antal",  # Farve baseret på antal observationer
            hover_name=hover_name,
            hover_data=hover_data,
            color_continuous_scale=px.colors.sequential.Plasma,  # Ændret farveskala
            size_max=35,  # Øget maksimal punktstørrelse
            mapbox_style="carto-positron",  # Ændret kortprovider
            title="UFO-observationer fordelt geografisk"
        )
        
        # Simplere update_layout for at undgå fejl
        fig.update_layout(
            margin={"r":0, "t":30, "l":0, "b":0},
            mapbox_style="carto-positron",
            mapbox=dict(
                center=dict(lat=56.0, lon=9.5),
                zoom=6.5
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Vis statistik om observationer på kortet
        st.write(f"Viser {len(map_data)} observationer fra {len(city_counts)} lokationer på kortet.")
        
        # Vis også en tabel med top 10 lokationer med flest observationer
        st.subheader("Top 10 lokationer med flest observationer")
        top_locations = city_counts.sort_values('antal', ascending=False).head(10)
        st.dataframe(top_locations)
    else:
        st.info("Ingen observationer med gyldige koordinater at vise på kortet.")

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
            filtered_df['month'] = filtered_df['date'].str.extract(r'-(\d{2})-').astype(int)
        except:
            # Fallback hvis det ikke virker
            filtered_df['month'] = np.nan
    
    # Konverter år og måned til strenge for at undgå grupperingsproblemer
    filtered_df['year_str'] = filtered_df['year'].astype(str)
    filtered_df['month_int'] = filtered_df['month'].astype(int, errors='ignore')
    
    # Simpel løsning - bare tæl observationer per år og måned
    year_month_counts = filtered_df.dropna(subset=['year_str', 'month_int']).groupby(['year_str', 'month_int']).size().reset_index(name='count')
    
    # Omdøb kolonner
    year_month_counts.columns = ['År', 'Måned', 'Antal']
    
    # Tilføj månedsnavne
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
    year_month_counts['Månedsnavn'] = year_month_counts['Måned'].apply(lambda x: month_names[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else 'Ukendt')
    
    # Opret heatmap direkte fra denne DataFrame
    fig = px.density_heatmap(
        year_month_counts, 
        x='Månedsnavn', 
        y='År', 
        z='Antal',
        color_continuous_scale='Viridis',
        category_orders={"Månedsnavn": month_names},
        labels={'Antal': 'Observationer'},
        title="UFO-observationer per måned og år"
    )
    
    # Opdater layout
    fig.update_layout(
        xaxis_title="Måned",
        yaxis_title="År"
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
