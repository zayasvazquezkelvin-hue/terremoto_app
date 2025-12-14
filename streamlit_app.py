import streamlit as st
import pandas as pd
from quakefeeds import QuakeFeed
import plotly.express as px
from datetime import datetime
import locale
import numpy as np

st.set_page_config(layout="wide")
st.title("Datos en Tiempo Real de los Terremotos en Puerto Rico y el Mundo")
st.divider()
token_id = "pk.eyJ1IjoibWVjb2JpIiwiYSI6IjU4YzVlOGQ2YjEzYjE3NTcxOTExZTI2OWY3Y2Y1ZGYxIn0.LUg7xQhGH2uf3zA57szCyw"
px.set_mapbox_access_token(token_id) 

# ----------------
# Configurar Fecha
# ----------------
try:
   locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8') 
except:
   try:
      locale.setlocale(locale.LC_TIME, 'Spanish_Spain')
   except:
      locale.setlocale(locale.LC_TIME, 'C.UTF-8')
# -----
# Tabla 
# -----

def generaTabla():
    feed = QuakeFeed("All","month")
    longitudes = [feed.location(i)[0] for i in range(len(feed))]
    latitudes = [feed.location(i)[1] for i in range(len(feed))]
    date = list(feed.event_times)
    depths = list(feed.depths)
    places = list(feed.places)
    magnitudes = list(feed.magnitudes)
    
    df = pd.DataFrame({
        "Fecha": pd.to_datetime(date, utc=True),
        "lon": pd.to_numeric(longitudes),
        "lat": pd.to_numeric(latitudes),
        "Lugar": places,
        "Magnitud": pd.to_numeric(magnitudes).round(2),
        "Profundidad": pd.to_numeric(depths).round(2)})
    
    
# ---------------    
# Formatear fecha
# ---------------

    df["Fecha "] = df["Fecha"].dt.strftime("%d de %B de %Y").str.capitalize()
    return df

# ----------------
# Mapas y gráficas
# ----------------

def generaMapa(df, center, zoom):
    fig = px.scatter_mapbox(
        df,
        color="Magnitud",
        lat="lat",
        lon="lon",
        custom_data=["Magnitud", "lat", "lon", "Fecha ", "Profundidad"],
        hover_name="Lugar",
        color_continuous_scale=px.colors.cyclical.IceFire,
        size_max=10,
        opacity=0.5,
        width=800,
        height=600,
        zoom=zoom,
        mapbox_style="dark",
        center=center)

# ----------------------------------
#Orden de la información del hoover#
# ----------------------------------
    
    fig.update_traces(
        hovertemplate=
       "<b>%{hovertext}</b><br>" +
       "Magnitud: %{customdata[0]:.2f}<br>" +
       "Latitud: %{customdata[1]:.4f}<br>" +
       "Longitud: %{customdata[2]:.4f}<br>" +
       "Fecha : %{customdata[3]}<br>" +
       "Profundidad: %{customdata[4]:.2f} km<br>" +
       "<extra></extra>")
    return fig




def generaMag(df):
    fig = px.histogram(df, x="Magnitud", color_discrete_sequence=["red"], width=300, height=600)
    return fig

def generaProf(df):
    fig = px.histogram(df, x="Profundidad", color_discrete_sequence=["red"], width=300, height=600)
    return fig

# ------------
# Cargar datos
# ------------

df = generaTabla()

# ----------------------------------------------------
# Filtrar eventos con magnitud negativa por prevención
# ----------------------------------------------------

df = df[df["Magnitud"] >= 0]

# -------
# Sidebar
# -------

st.sidebar.markdown("### Severidad")
categorias = ["todos", "significativo", "4.5", "2.5", "1.0"]
severidad = st.sidebar.selectbox("", categorias, index=0)

st.sidebar.markdown("### Periodo")
tiempo = ["mes", "semana", "día"]
Periodo = st.sidebar.selectbox("", tiempo)

st.sidebar.markdown("### Zona Geográfica")
Zoom_dict = {"Puerto Rico": 7.25, "Mundo": 1.0}
zona = st.sidebar.selectbox("", list(Zoom_dict.keys()))
zoom = Zoom_dict[zona]

st.sidebar.divider()
mapa = st.sidebar.checkbox("Mostrar mapa")
evento = st.sidebar.checkbox("Mostrar tabla con 5 eventos")
st.sidebar.divider()
cantidad_eventos = st.sidebar.slider("Cantidad de eventos", min_value=5, max_value=20, value=5)

st.sidebar.divider()
st.sidebar.markdown(
    """Aplicación desarrollada por:<br> 
    <i>Kelvin Zayas Vázquez <br> 
    INGE3016<br>
    Universidad de Puerto Rico en Humacao<i>""",
    unsafe_allow_html=True
)

# -----------------------------
# Filtrar por severidad
# -----------------------------
if severidad == "todos":
    df_filtrado = df.copy()
elif severidad == "significativo":
    df_filtrado = df[df["Magnitud"] > 4.5]
else:
    df_filtrado = df[df["Magnitud"] == float(severidad)]

# -----------------------------
# Filtrar por periodo
# -----------------------------
hoy = pd.Timestamp.utcnow()
if Periodo == "mes":
    fecha_limite = hoy - pd.Timedelta(days=30)
    df_filtrado = df_filtrado[df_filtrado["Fecha"] >= fecha_limite]
elif Periodo == "semana":
    fecha_limite = hoy - pd.Timedelta(days=7)
    df_filtrado = df_filtrado[df_filtrado["Fecha"] >= fecha_limite]
elif Periodo == "día":
    df_filtrado = df_filtrado[df_filtrado["Fecha"].dt.date == hoy.date()]

# ------------------------
# Clasificación de Richter
# ------------------------
def clasificar_richter(mag):
    if 0.0<= mag < 2.0: return "micro"
    elif 2.0 <= mag < 4.0: return "menor"
    elif 4.0 <= mag < 5.0: return "ligero"
    elif 5.0 <= mag < 6.0: return "moderado"
    elif 6.0 <= mag < 7.0: return "fuerte"
    elif 7.0 <= mag < 8.0: return "mayor"
    elif 8.0 <= mag < 10: return "épico"
    else: return "legendario"

df_filtrado["Clasificación"] = df_filtrado["Magnitud"].apply(clasificar_richter)

# ------------
# Estadísticas
# ------------
st.markdown(f"<div style='text-align:center'>Fecha de petición: {hoy.strftime('%d de %B de %Y %H:%M:%S')}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center'>Cantidad de eventos: {len(df_filtrado)}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center'>Promedio de magnitudes: {df_filtrado['Magnitud'].mean():.2f}</div>", unsafe_allow_html=True)
st.markdown(f"<div style='text-align:center'>Promedio de profundidades: {df_filtrado['Profundidad'].mean():.2f} km</div>", unsafe_allow_html=True)
st.write(" " )

# -----------------
# Tabla con eventos
# -----------------

if evento:
    if len(df_filtrado) <= cantidad_eventos:
        df_mostrar = df_filtrado.copy()
    else:
        df_mostrar = df_filtrado.sample(n=cantidad_eventos, random_state=42)
    df_mostrar = df_mostrar.sort_values(by="Fecha", ascending=False)
    st.dataframe(df_mostrar[["Fecha ", "Lugar", "Magnitud", "Profundidad", "Clasificación"]].reset_index(drop=True))

# ---------------------------
# Gráficas y mapa en columnas
# ---------------------------
col1, col2, col3 = st.columns([1.0,1.0,3.5])
with col1:
    st.markdown("<p style='font-size:13px'>Histograma de Magnitudes</>",unsafe_allow_html=True )
    st.write(generaMag(df_filtrado))
with col2:
    st.markdown("<p style='font-size:13px'>Histograma de Profundidades", unsafe_allow_html=True)
    st.write(generaProf(df_filtrado))
with col3:
    if mapa:
        center = dict(lat=18.25178, lon=-66.254512)
        st.subheader(" ")
        st.write(generaMapa(df_filtrado, center, zoom))

