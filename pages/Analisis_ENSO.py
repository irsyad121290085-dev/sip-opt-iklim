import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Analisis ENSO",
    page_icon="🌊",
    layout="wide"
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_DIR / "master_dashboard_final.csv")

def klasifikasi_enso(x):
    if pd.isna(x):
        return "Tidak ada data"
    if x >= 0.5:
        return "El Niño"
    if x <= -0.5:
        return "La Niña"
    return "Netral"

df = load_data()
df["Kondisi ENSO"] = df["Nino34"].apply(klasifikasi_enso)

st.title("🌊 Analisis Pengaruh El Niño–La Niña terhadap OPT")

st.markdown("""
Halaman ini membandingkan luas serangan OPT pada tiga kondisi ENSO:
**El Niño**, **La Niña**, dan **Netral**. Klasifikasi dibuat dari nilai Nino34
yang sudah tersedia pada data.

- **El Niño**: Nino34 ≥ 0,5
- **La Niña**: Nino34 ≤ -0,5
- **Netral**: -0,5 < Nino34 < 0,5

Catatan: klasifikasi ini cukup untuk analisis dashboard. Untuk penetapan kejadian ENSO
resmi, perlu mempertimbangkan durasi beberapa musim berturut-turut.
""")

provinsi_opsi = ["Semua"] + sorted(df["Provinsi"].dropna().unique())
komoditas_opsi = ["Semua"] + sorted(df["Jenis Komoditas"].dropna().unique())
opt_opsi = ["Semua"] + sorted(df["Jenis OPT"].dropna().unique())

col_filter1, col_filter2, col_filter3 = st.columns(3)

with col_filter1:
    provinsi = st.selectbox("Provinsi", provinsi_opsi)

with col_filter2:
    komoditas = st.selectbox("Komoditas", komoditas_opsi)

with col_filter3:
    opt = st.selectbox("OPT", opt_opsi)

data = df.copy()

if provinsi != "Semua":
    data = data[data["Provinsi"] == provinsi]

if komoditas != "Semua":
    data = data[data["Jenis Komoditas"] == komoditas]

if opt != "Semua":
    data = data[data["Jenis OPT"] == opt]

if len(data) == 0:
    st.warning("Data tidak tersedia untuk filter yang dipilih.")
    st.stop()

st.divider()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Serangan", f"{data['Total Luas Serangan (Ha)'].sum():,.2f} Ha")

with col2:
    st.metric("Rata-rata Nino34", f"{data['Nino34'].mean():.2f}")

with col3:
    st.metric("Rata-rata Curah Hujan", f"{data['PRCP'].mean():.2f} mm")

with col4:
    st.metric("Rata-rata Tavg", f"{data['Tavg_C'].mean():.2f} °C")

st.subheader("Perbandingan Serangan OPT Berdasarkan Kondisi ENSO")

enso_summary = (
    data.groupby("Kondisi ENSO", as_index=False)
        .agg({
            "Total Luas Serangan (Ha)": "sum",
            "Tavg_C": "mean",
            "PRCP": "mean",
            "Nino34": "mean"
        })
        .sort_values("Total Luas Serangan (Ha)", ascending=False)
)

fig1 = px.bar(
    enso_summary,
    x="Kondisi ENSO",
    y="Total Luas Serangan (Ha)",
    hover_data=["Tavg_C", "PRCP", "Nino34"],
    title="Total Luas Serangan OPT pada El Niño, La Niña, dan Netral"
)

st.plotly_chart(fig1, use_container_width=True)

st.dataframe(enso_summary, use_container_width=True, hide_index=True)

st.subheader("Tren Tahunan ENSO dan Serangan OPT")

trend = (
    data.groupby(["Tahun", "Kondisi ENSO"], as_index=False)
        .agg({
            "Total Luas Serangan (Ha)": "sum",
            "Nino34": "mean",
            "PRCP": "mean",
            "Tavg_C": "mean"
        })
)

fig2 = px.line(
    trend,
    x="Tahun",
    y="Total Luas Serangan (Ha)",
    color="Kondisi ENSO",
    markers=True,
    title="Tren Serangan OPT per Tahun Berdasarkan ENSO"
)

st.plotly_chart(fig2, use_container_width=True)

st.subheader("Hubungan Nino34, Curah Hujan, Suhu, dan Luas Serangan")

scatter_data = (
    data.groupby(["Tahun", "Triwulan", "Provinsi", "Kondisi ENSO"], as_index=False)
        .agg({
            "Total Luas Serangan (Ha)": "sum",
            "Nino34": "mean",
            "PRCP": "mean",
            "Tavg_C": "mean"
        })
)

fig3 = px.scatter(
    scatter_data,
    x="Nino34",
    y="Total Luas Serangan (Ha)",
    size="PRCP",
    color="Kondisi ENSO",
    hover_data=["Tahun", "Triwulan", "Provinsi", "Tavg_C"],
    title="Scatter Nino34 vs Luas Serangan OPT"
)

st.plotly_chart(fig3, use_container_width=True)

st.subheader("Interpretasi Otomatis")

dominant = enso_summary.iloc[0]["Kondisi ENSO"]
max_attack = enso_summary.iloc[0]["Total Luas Serangan (Ha)"]

st.info(
    f"Pada filter saat ini, total luas serangan terbesar muncul pada kondisi **{dominant}** "
    f"dengan total sekitar **{max_attack:,.2f} Ha**. "
    "Hasil ini bersifat deskriptif, jadi belum otomatis berarti sebab-akibat. "
    "Untuk kesimpulan ilmiah, perlu uji korelasi atau regresi antara Nino34, curah hujan, suhu, GDD, dan luas serangan OPT."
)
