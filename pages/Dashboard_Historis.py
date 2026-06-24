import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@st.cache_data
def load_data():
    df = pd.read_csv(DATA_DIR / "master_dashboard_final.csv")
    ref = pd.read_csv(DATA_DIR / "dashboard_reference.csv")
    return df, ref

def klasifikasi_enso(x):
    if pd.isna(x):
        return "Tidak ada data"
    if x >= 0.5:
        return "El Niño"
    if x <= -0.5:
        return "La Niña"
    return "Netral"

df, ref = load_data()
df["Kondisi ENSO"] = df["Nino34"].apply(klasifikasi_enso)

st.title("📊 Dashboard Historis OPT dan Iklim")

provinsi = st.sidebar.selectbox(
    "Provinsi",
    sorted(ref["Provinsi"].dropna().unique())
)

komoditas = st.sidebar.selectbox(
    "Komoditas",
    sorted(ref[ref["Provinsi"] == provinsi]["Jenis Komoditas"].dropna().unique())
)

opt = st.sidebar.selectbox(
    "OPT",
    sorted(
        ref[
            (ref["Provinsi"] == provinsi)
            & (ref["Jenis Komoditas"] == komoditas)
        ]["Jenis OPT"].dropna().unique()
    )
)

opsi_enso = ["Semua"] + sorted(df["Kondisi ENSO"].dropna().unique())
filter_enso = st.sidebar.selectbox("Kondisi ENSO", opsi_enso)

data = df[
    (df["Provinsi"] == provinsi)
    & (df["Jenis Komoditas"] == komoditas)
    & (df["Jenis OPT"] == opt)
].copy()

if filter_enso != "Semua":
    data = data[data["Kondisi ENSO"] == filter_enso]

if len(data) == 0:
    st.warning("Data tidak tersedia untuk filter yang dipilih.")
    st.stop()

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Serangan", f"{data['Total Luas Serangan (Ha)'].sum():,.2f} Ha")
col2.metric("Rata-rata Tavg", f"{data['Tavg_C'].mean():.2f} °C")
col3.metric("Rata-rata Curah Hujan", f"{data['PRCP'].mean():.2f} mm")
col4.metric("Rata-rata Nino34", f"{data['Nino34'].mean():.2f}")
col5.metric("Kondisi Dominan", data["Kondisi ENSO"].mode().iloc[0])

st.divider()

grafik_tahun = (
    data.groupby(["Tahun", "Kondisi ENSO"], as_index=False)
        ["Total Luas Serangan (Ha)"].sum()
)

fig1 = px.line(
    grafik_tahun,
    x="Tahun",
    y="Total Luas Serangan (Ha)",
    color="Kondisi ENSO",
    markers=True,
    title="Serangan OPT Tahunan Berdasarkan Kondisi ENSO"
)

st.plotly_chart(fig1, use_container_width=True)

grafik_triwulan = (
    data.groupby(["Tahun", "Triwulan"], as_index=False)
        .agg({
            "Total Luas Serangan (Ha)": "sum",
            "Tavg_C": "mean",
            "PRCP": "mean",
            "Nino34": "mean"
        })
)

fig2 = px.bar(
    grafik_triwulan,
    x="Triwulan",
    y="Total Luas Serangan (Ha)",
    color="Tahun",
    barmode="group",
    title="Serangan OPT per Triwulan"
)

st.plotly_chart(fig2, use_container_width=True)

st.subheader("Data Terfilter")
st.dataframe(data, use_container_width=True)
