import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta
from astral import LocationInfo
from astral.sun import sun

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

# Funktion til at beregne solopgang/solnedgang
def get_sun_times(date, lat=55.6761, lon=12.5683):  # København som standard
    city = LocationInfo("Copenhagen", "Denmark", "Europe/Copenhagen", lat, lon)
    s = sun(city.observer, date=date)
    return s["sunrise"], s["sunset"]

# Funktion til at bestemme tid i forhold til solopgang/solnedgang
def time_relative_to_sun(row):
    if pd.isna(row['date']) or pd.isna(row['start_time']):
        return "Ukendt"
    
    try:
        # Konverter dato og tid til datetime
        date_obj = row['date']
        time_str = row['start_time']
        
        if isinstance(time_str, str) and ':' in time_str:
            hour, minute = map(int, time_str.split(':'))
            
            # Kombiner dato og tid
            time_obj = date_obj.replace(hour=hour, minute=minute)
            
            # Beregn solopgang og solnedgang
            sunrise, sunset = get_sun_times(date_obj)
            
            # Definer tidsperioder
            dawn_start = sunrise - timedelta(hours=1)
            dusk_end = sunset + timedelta(hours=1)
            
            if time_obj < dawn_start:
                return "Nat"
            elif dawn_start <= time_obj < sunrise:
                return "Solopgang"
            elif sunrise <= time_obj < sunset:
                return "Dag"
            elif sunset <= time_obj < dusk_end:
                return "Solnedgang"
            else:
                return "Nat"
        
        return "Ukendt"
    except:
        return "Ukendt"

# Funktion til at udtrække time fra start_time
def extract_hour(time_str):
    if pd.isna(time_str) or not isinstance(time_str, str):
        return None
    
    try:
        if ':' in time_str:
            return int(time_str.split(':')[0])
        return None
    except:
        return None

# Indlæs data
df = load_data()

# Udtræk postnumre fra lokation
df['postnr'] = df['location'].str.extract(r'(\d{4})').astype('str')

# Udtræk time fra start_time
df['hour'] = df['start_time'].apply(extract_hour)

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
    
    # Opret en simpel dataframe med postnumre og antal observationer
    postnr_counts = filtered_df['postnr'].value_counts().reset_index()
    postnr_counts.columns = ['postnr', 'antal']
    
    # Tilføj danske postnumre med koordinater (dette er en forenklet version - du skal have en komplet liste)
    # Dette er et eksempel - du skal erstatte det med en faktisk postnummer-koordinat mapping
    postnr_coords = {
        '1000': (55.6761, 12.5683),  # København
        '2000': (55.6828, 12.5307),  # Frederiksberg
        '2100': (55.7046, 12.5839),  # København Ø
        '2200': (55.6871, 12.5429),  # København N
        '2300': (55.6624, 12.5977),  # København S
        '2400': (55.6638, 12.5422),  # København NV
        '2500': (55.6518, 12.4939),  # Valby
        '2600': (55.6771, 12.4587),  # Glostrup
        '2700': (55.6734, 12.4262),  # Brønshøj
        '2800': (55.7769, 12.5059),  # Lyngby
        '2900': (55.7349, 12.3944),  # Hellerup
        '3000': (56.0392, 12.6118),  # Helsingør
        '4000': (55.4613, 11.7996),  # Roskilde
        '5000': (55.4038, 10.4024),  # Odense
        '6000': (55.4904, 9.4731),   # Kolding
        '7000': (55.7089, 9.5357),   # Fredericia
        '8000': (56.1572, 10.2107),  # Aarhus
        '9000': (57.0488, 9.9217),   # Aalborg
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
            height=400
        )
        
        fig.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0, "t":0, "l":0, "b":0}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Ikke nok postnumre med koordinater til at vise kortet. Tilføj flere postnumre med koordinater.")

# 2. OBSERVATIONER I FORHOLD TIL SOLOPGANG/SOLNEDGANG
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
        y0=0, y1=hour_counts['antal'].max(),
        line=dict(color="orange", width=2, dash="dash"),
        name="Gennemsnitlig solopgang"
    )
    
    fig.add_shape(
        type="line",
        x0=21, x1=21,  # Solnedgang ca. kl. 21 (gennemsnit)
        y0=0, y1=hour_counts['antal'].max(),
        line=dict(color="red", width=2, dash="dash"),
        name="Gennemsnitlig solnedgang"
    )
    
    # Tilføj annotation
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
    
    # Opret pivot-tabel
    year_month_counts = filtered_df.groupby(['year', 'month']).size().reset_index(name='count')

    # Opret en tom pivot-tabel med alle år og måneder
    years = sorted(filtered_df['year'].unique())
    months = list(range(1, 13))

    # Initialiser en tom DataFrame med nuller
    pivot_data = {year: {month: 0 for month in months} for year in years}

    # Fyld data ind
    for _, row in year_month_counts.iterrows():
        if pd.notna(row['year']) and pd.notna(row['month']):
            year = int(row['year'])
            month = int(row['month'])
            if year in pivot_data and month in pivot_data[year]:
                pivot_data[year][month] = row['count']

    # Konverter til DataFrame
    year_month_pivot = pd.DataFrame(pivot_data).T  # Transpose for at få år som rækker

    # Omdøb måneder
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'Maj', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Okt', 11: 'Nov', 12: 'Dec'
    }
    year_month_pivot = year_month_pivot.rename(columns=month_names)
