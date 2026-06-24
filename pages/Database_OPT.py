import streamlit as st
import pandas as pd
from pathlib import Path

st.set_page_config(
    page_title="Database OPT",
    page_icon="🦗",
    layout="wide"
)

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_DIR / "master_dashboard_final.csv")

df = load_data()

st.title("🦗 Database OPT")

st.markdown("""
Database parameter Organisme Pengganggu Tanaman (OPT)
yang digunakan pada sistem prediksi risiko berbasis iklim dan GDD.
""")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total OPT", df["Jenis OPT"].nunique())

with col2:
    st.metric("OPT Dengan Parameter", df[df["Parameter_Tersedia"] == True]["OPT_std"].nunique())

with col3:
    st.metric("OPT Tanpa Parameter", df[df["Parameter_Tersedia"] == False]["Jenis OPT"].nunique())

st.divider()

opt_db = (
    df.sort_values("Parameter_Tersedia", ascending=False)
      .drop_duplicates(subset=["Jenis OPT"])
)

opt_pilih = st.selectbox(
    "Pilih OPT",
    sorted(opt_db["Jenis OPT"].dropna().unique())
)

data = opt_db[opt_db["Jenis OPT"] == opt_pilih]

if len(data) == 0:
    st.error("Data OPT tidak ditemukan")
else:
    row = data.iloc[0]
    st.subheader(opt_pilih)

    if row["Parameter_Tersedia"] == False:
        st.warning("""
Parameter biologis OPT ini belum tersedia.

Sistem belum dapat melakukan prediksi GDD untuk OPT ini.
""")
        st.write("### Informasi Dasar")
        st.write("**Nama OPT:**", opt_pilih)

        if pd.notna(row["OPT_std"]):
            st.write("**Nama Standar:**", row["OPT_std"])
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.write("### Informasi Umum")
            st.write("**Nama Ilmiah:**", row["Nama Ilmiah"])
            st.write("**Kategori:**", row["Kategori"])
            st.write("**Trigger:**", row["Trigger"])

        with col2:
            st.write("### Parameter")
            st.write("**Tbase (°C):**", row["Tbase"])
            st.write("**GDD:**", row["GDD"])
            st.write("**Topt Min (°C):**", row["Topt_min"])
            st.write("**Topt Max (°C):**", row["Topt_max"])
            st.write("**RH Minimum (%):**", row["RH_min"])

        st.success("OPT ini dapat digunakan dalam modul prediksi GDD.")

st.divider()

st.subheader("📋 Daftar OPT")

mode = st.radio(
    "Filter",
    ["Semua OPT", "Hanya yang memiliki parameter"]
)

if mode == "Semua OPT":
    tabel = opt_db[["Jenis OPT", "OPT_std", "Kategori", "Parameter_Tersedia"]]
else:
    tabel = opt_db[opt_db["Parameter_Tersedia"] == True][
        ["Jenis OPT", "OPT_std", "Kategori", "Tbase", "GDD"]
    ]

st.dataframe(tabel, use_container_width=True)
