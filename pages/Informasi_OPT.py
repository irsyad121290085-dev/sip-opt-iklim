import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

st.set_page_config(
    page_title="Informasi OPT",
    page_icon="🦗",
    layout="wide"
)

# =========================
# LOAD DATA
# =========================

df = pd.read_csv(DATA_DIR / "master_priority_final_clean (1).csv")

df["Total Luas Serangan (Ha)"] = pd.to_numeric(
    df["Total Luas Serangan (Ha)"],
    errors="coerce"
).fillna(0)

# Koordinat pendekatan titik tengah provinsi Sumatera
koordinat_provinsi = {
    "ACEH": (4.6951, 96.7494),
    "SUMATERA UTARA": (2.1154, 99.5451),
    "SUMATERA BARAT": (-0.7399, 100.8000),
    "RIAU": (0.2933, 101.7068),
    "KEPULAUAN RIAU": (0.977629, 104.473874),
    "JAMBI": (-1.6101, 103.6131),
    "SUMATERA SELATAN": (-3.3194, 103.9144),
    "BENGKULU": (-3.7928, 102.2608),
    "LAMPUNG": (-4.5586, 105.4068),
    "KEPULAUAN BANGKA BELITUNG": (-2.7411, 106.4406),
    "BANGKA BELITUNG": (-2.7411, 106.4406),
}



st.title("🦗 Informasi OPT")

st.markdown("""
Dashboard ini menampilkan OPT utama berdasarkan komoditas,
provinsi terdampak, total luas serangan, dan parameter biologis OPT.
""")

# =========================
# KPI
# =========================

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Komoditas", df["Jenis Komoditas"].nunique())

with col2:
    st.metric("Total OPT", df["Jenis OPT Standar"].nunique())

with col3:
    st.metric(
        "Total Luas Serangan (Ha)",
        f"{df['Total Luas Serangan (Ha)'].sum():,.2f}"
    )

st.divider()

# =========================
# PILIH KOMODITAS
# =========================

komoditas_pilih = st.selectbox(
    "Pilih Jenis Komoditas",
    sorted(df["Jenis Komoditas"].dropna().unique())
)

df_komoditas = df[df["Jenis Komoditas"] == komoditas_pilih].copy()

st.subheader(f"Komoditas: {komoditas_pilih}")

opt_tersedia = (
    df_komoditas
    .sort_values(["Ranking OPT", "Total Luas Serangan (Ha)"], ascending=[True, False])
    ["Jenis OPT Standar"]
    .dropna()
    .unique()
)

if len(opt_tersedia) == 0:
    st.warning("Belum ada data OPT untuk komoditas ini.")
    st.stop()

# =========================
# PILIH OPT
# =========================

opt_pilih = st.selectbox(
    "Pilih Jenis OPT",
    opt_tersedia
)

df_opt = df_komoditas[df_komoditas["Jenis OPT Standar"] == opt_pilih].copy()

row = df_opt.sort_values("Total Luas Serangan (Ha)", ascending=False).iloc[0]

st.divider()

# =========================
# INFORMASI OPT
# =========================

st.subheader(f"Informasi OPT: {opt_pilih}")

col1, col2 = st.columns(2)

with col1:
    st.write("### Informasi Umum")
    st.write("**Jenis OPT Asli:**", row["Jenis OPT Asli"])
    st.write("**Nama Standar:**", row["Jenis OPT Standar"])
    st.write("**Nama Ilmiah:**", row["Nama Ilmiah"])
    st.write("**Kategori:**", row["Kategori"])
    st.write("**Trigger:**", row["Trigger"])
    st.write("**Referensi:**", row["Referensi"])

with col2:
    st.write("### Parameter Biologis")
    st.write("**Tbase (°C):**", row["Tbase"])
    st.write("**GDD:**", row["GDD"])
    st.write("**Topt Min (°C):**", row["Topt_min"])
    st.write("**Topt Max (°C):**", row["Topt_max"])
    st.write("**RH Minimum (%):**", row["RH_min"])

st.divider()

# =========================
# TOP 5 PROVINSI
# =========================

st.subheader("🏆 Provinsi Teratas Yang Terdampak")

top5 = (
    df_opt
    .groupby("Provinsi", as_index=False)["Total Luas Serangan (Ha)"]
    .sum()
    .sort_values("Total Luas Serangan (Ha)", ascending=False)
    .head(5)
)

col1, col2 = st.columns([1, 1])

with col1:
    st.dataframe(
        top5,
        use_container_width=True,
        hide_index=True
    )

with col2:
    st.bar_chart(
        top5.set_index("Provinsi")["Total Luas Serangan (Ha)"]
    )



# =========================
# PETA SEBARAN
# =========================

st.subheader("🗺️ Peta Sebaran Provinsi Yang Terdampak OPT")

map_data = top5.copy()

map_data["Provinsi_key"] = (
    map_data["Provinsi"]
    .astype(str)
    .str.strip()
    .str.upper()
)

map_data["lat"] = map_data["Provinsi_key"].map(
    lambda x: koordinat_provinsi.get(x, (None, None))[0]
)

map_data["lon"] = map_data["Provinsi_key"].map(
    lambda x: koordinat_provinsi.get(x, (None, None))[1]
)

map_data["luas_serangan"] = pd.to_numeric(
    map_data["Total Luas Serangan (Ha)"],
    errors="coerce"
).fillna(0)

map_data = map_data.dropna(subset=["lat", "lon"])

if len(map_data) == 0:
    st.warning("Koordinat provinsi belum tersedia untuk data terpilih.")
else:
    m = folium.Map(
        location=[map_data["lat"].mean(), map_data["lon"].mean()],
        zoom_start=5,
        tiles="OpenStreetMap"
    )

    for _, row in map_data.iterrows():
        luas = row["luas_serangan"]

        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=7,
            color="#dc2626",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.8,
            popup=folium.Popup(
                f"""
                <b>Provinsi:</b> {row['Provinsi']}<br>
                <b>Total Luas Serangan:</b> {luas:,.2f} Ha
                """,
                max_width=250
            ),
            tooltip=f"{row['Provinsi']} - {luas:,.2f} Ha"
        ).add_to(m)

    st_folium(
        m,
        width=None,
        height=520
    )

# =========================
# TABEL DETAIL
# =========================

st.divider()

st.subheader("📋 Detail Data OPT Terpilih")

st.dataframe(
    df_opt[
        [
            "Provinsi",
            "Jenis Komoditas",
            "Ranking Komoditas",
            "Jenis OPT Asli",
            "Ranking OPT",
            "Total Luas Serangan (Ha)",
            "Jenis OPT Standar",
            "Nama Ilmiah",
            "Kategori",
            "Trigger"
        ]
    ].sort_values("Total Luas Serangan (Ha)", ascending=False),
    use_container_width=True,
    hide_index=True
)