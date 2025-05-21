import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

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

# Opret to kolonner
col1, col2 = st.columns(2)

# Observationer per år
with col1:
    st.subheader("Observationer per år")
    yearly_data = filtered_df.groupby('year').size().reset_index(name='antal')
    
    fig = px.bar(yearly_data, x='year', y='antal', 
                 title="UFO-observationer per år",
                 labels={'year': 'År', 'antal': 'Antal observationer'})
    st.plotly_chart(fig, use_container_width=True)

# Observationer per måned
with col2:
    st.subheader("Observationer per måned")
    
    # Hvis dato er i datetime format
    if pd.api.types.is_datetime64_any_dtype(filtered_df['date']):
        filtered_df['month'] = filtered_df['date'].dt.month
        monthly_data = filtered_df.groupby('month').size().reset_index(name='antal')
    else:
        # Forsøg at udtrække måned fra dato-streng
        try:
            filtered_df['month'] = filtered_df['date'].str.extract(r'-(\d{2})-').astype(float)
            monthly_data = filtered_df.groupby('month').size().reset_index(name='antal')
        except:
            # Fallback hvis det ikke virker
            monthly_data = pd.DataFrame({'month': range(1, 13), 'antal': [0]*12})
    
    # Tilføj månedsnavne
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'Maj', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dec']
    monthly_data['month_name'] = monthly_data['month'].apply(
        lambda x: month_names[int(x)-1] if pd.notna(x) and 1 <= int(x) <= 12 else 'Ukendt'
    )
    
    fig = px.bar(monthly_data, x='month_name', y='antal', 
                 title="UFO-observationer per måned",
                 labels={'month_name': 'Måned', 'antal': 'Antal observationer'},
                 category_orders={"month_name": month_names})
    st.plotly_chart(fig, use_container_width=True)

# Farvefordeling
st.subheader("Farvefordeling")

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

fig = px.pie(color_counts, values='antal', names='color', 
             title="Top 10 farver observeret",
             hole=0.4)
st.plotly_chart(fig, use_container_width=True)

# Kort over observationer
st.subheader("Geografisk fordeling")
st.write("Bemærk: Dette kort viser kun observationer med postnumre")

# Udtræk postnumre fra lokationskolonnen
filtered_df['postnr'] = filtered_df['location'].str.extract(r'(\d{4})')

# Opret et simpelt kort baseret på postnumre
postnr_counts = filtered_df.groupby('postnr').size().reset_index(name='antal')
postnr_counts = postnr_counts.dropna()

# Vis data tabel
st.subheader("Observationsdata")
st.dataframe(filtered_df)

# Download knap
csv = filtered_df.to_csv(index=False).encode('utf-8')
st.download_button(
    label="Download filtrerede data som CSV",
    data=csv,
    file_name="ufo_observationer_filtreret.csv",
    mime="text/csv",
)
