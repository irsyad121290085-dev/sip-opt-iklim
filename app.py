import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Sistem Informasi OPT Sumatera",
    page_icon="🌱",
    layout="wide"
)

DATA_DIR = Path(__file__).parent / "data"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_DIR / "master_dashboard_final.csv")

df = load_data()

st.title("🌱 Sistem Informasi OPT Perkebunan Sumatera")

st.markdown("""
Sistem ini mengintegrasikan data serangan OPT, temperatur, curah hujan,
indeks ENSO/Niño 3.4, dan prediksi risiko berbasis Growing Degree Days (GDD).

Gunakan menu di sidebar kiri untuk membuka dashboard historis, prediksi GDD,
database OPT, informasi OPT, dan analisis El Niño–La Niña.
""")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Provinsi", df["Provinsi"].nunique())

with col2:
    st.metric("Komoditas", df["Jenis Komoditas"].nunique())

with col3:
    st.metric("OPT", df["Jenis OPT"].nunique())

with col4:
    st.metric("Periode Data", f"{df['Tahun'].min()}-{df['Tahun'].max()}")

st.divider()

st.subheader("Ringkasan Kondisi ENSO dalam Data")

def klasifikasi_enso(x):
    if pd.isna(x):
        return "Tidak ada data"
    if x >= 0.5:
        return "El Niño"
    if x <= -0.5:
        return "La Niña"
    return "Netral"

df["Kondisi ENSO"] = df["Nino34"].apply(klasifikasi_enso)

enso_count = (
    df.drop_duplicates(subset=["Tahun", "Triwulan"])
      .assign(**{"Kondisi ENSO": lambda d: d["Nino34"].apply(klasifikasi_enso)})
      ["Kondisi ENSO"]
      .value_counts()
)

c1, c2, c3 = st.columns(3)
c1.metric("Periode El Niño", int(enso_count.get("El Niño", 0)))
c2.metric("Periode La Niña", int(enso_count.get("La Niña", 0)))
c3.metric("Periode Netral", int(enso_count.get("Netral", 0)))

st.info(
    "Klasifikasi sederhana: Nino34 ≥ 0,5 = El Niño; Nino34 ≤ -0,5 = La Niña; selain itu Netral. "
    "Untuk penetapan kejadian ENSO resmi, NOAA biasanya memakai syarat durasi beberapa musim berturut-turut."
)
