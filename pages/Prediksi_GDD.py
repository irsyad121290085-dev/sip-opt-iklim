import streamlit as st
import pandas as pd
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@st.cache_data
def load_data():
    master = pd.read_csv(DATA_DIR / "master_dashboard_final.csv")
    ref = pd.read_csv(DATA_DIR / "dashboard_reference.csv")
    climate = pd.read_csv(DATA_DIR / "master_climate_clean.csv")
    return master, ref, climate

def klasifikasi_enso(x):
    if pd.isna(x):
        return "Tidak ada data"
    if x >= 0.5:
        return "El Niño"
    if x <= -0.5:
        return "La Niña"
    return "Netral"

master, ref, climate = load_data()
climate["DATE"] = pd.to_datetime(climate["DATE"])

st.set_page_config(layout="wide")

st.title("🌡️ Prediksi Risiko OPT Berbasis GDD")

st.markdown("""
Sistem memprediksi potensi kemunculan OPT prioritas berdasarkan data iklim harian,
parameter biologis OPT, akumulasi Growing Degree Days (GDD), dan informasi ENSO/Niño 3.4.
""")

tanggal_tanam = st.date_input("Tanggal Tanam", datetime(2021, 1, 1))

provinsi = st.selectbox(
    "Provinsi",
    sorted(ref["Provinsi"].dropna().unique())
)

komoditas = st.selectbox(
    "Komoditas",
    sorted(ref[ref["Provinsi"] == provinsi]["Jenis Komoditas"].dropna().unique())
)

data_opt = ref[
    (ref["Provinsi"] == provinsi)
    & (ref["Jenis Komoditas"] == komoditas)
]

if len(data_opt) == 0:
    st.warning("Data referensi tidak tersedia.")
    st.stop()

climate_prov = climate[climate["Provinsi"] == provinsi].sort_values("DATE").copy()
tanggal_tanam = pd.to_datetime(tanggal_tanam)
climate_prov = climate_prov[climate_prov["DATE"] >= tanggal_tanam]

if len(climate_prov) == 0:
    st.error("Data iklim tidak tersedia setelah tanggal tanam.")
    st.stop()

# Ambil Nino34 triwulan dari master untuk ditampilkan pada iklim harian
enso_ref = (
    master[["Tahun", "Triwulan", "Nino34"]]
    .drop_duplicates()
    .groupby(["Tahun", "Triwulan"], as_index=False)["Nino34"]
    .mean()
)
climate_prov = climate_prov.merge(enso_ref, on=["Tahun", "Triwulan"], how="left")
climate_prov["Kondisi ENSO"] = climate_prov["Nino34"].apply(klasifikasi_enso)

hasil = []

for _, row in data_opt.iterrows():
    opt = row["Jenis OPT"]

    param = (
        master[master["Jenis OPT"] == opt]
        .drop_duplicates(subset=["Jenis OPT"])
    )

    param = param[param["Parameter_Tersedia"] == True]

    if len(param) == 0:
        hasil.append({
            "OPT": opt,
            "Kategori": "-",
            "Target GDD": "-",
            "Tanggal Prediksi": "-",
            "Hari ke": "-",
            "Kondisi ENSO Saat Prediksi": "-",
            "Status": "Parameter biologis belum tersedia"
        })
        continue

    p = param.iloc[0]
    kategori = p["Kategori"]

    if kategori == "Serangga":
        tbase = p["Tbase"]
        target_gdd = p["GDD"]

        if pd.isna(tbase) or pd.isna(target_gdd):
            hasil.append({
                "OPT": opt,
                "Kategori": kategori,
                "Target GDD": "-",
                "Tanggal Prediksi": "-",
                "Hari ke": "-",
                "Kondisi ENSO Saat Prediksi": "-",
                "Status": "Parameter tidak lengkap"
            })
            continue

        akumulasi = 0
        tanggal_prediksi = None
        kondisi_enso_prediksi = "-"

        for _, iklim in climate_prov.iterrows():
            gdd_harian = max(iklim["Tavg_C"] - tbase, 0)
            akumulasi += gdd_harian

            if akumulasi >= target_gdd:
                tanggal_prediksi = iklim["DATE"]
                kondisi_enso_prediksi = iklim["Kondisi ENSO"]
                break

        if tanggal_prediksi is None:
            hasil.append({
                "OPT": opt,
                "Kategori": kategori,
                "Target GDD": round(target_gdd, 0),
                "Tanggal Prediksi": "Tidak tercapai",
                "Hari ke": "-",
                "Kondisi ENSO Saat Prediksi": "-",
                "Status": "Data iklim tidak cukup"
            })
        else:
            hari_ke = (tanggal_prediksi - tanggal_tanam).days

            hasil.append({
                "OPT": opt,
                "Kategori": kategori,
                "Target GDD": round(target_gdd, 0),
                "Tanggal Prediksi": tanggal_prediksi.date(),
                "Hari ke": hari_ke,
                "Kondisi ENSO Saat Prediksi": kondisi_enso_prediksi,
                "Status": "Potensi muncul"
            })

    elif kategori == "Penyakit":
        hasil.append({
            "OPT": opt,
            "Kategori": kategori,
            "Target GDD": "-",
            "Tanggal Prediksi": "-",
            "Hari ke": "-",
            "Kondisi ENSO Saat Prediksi": climate_prov["Kondisi ENSO"].mode().iloc[0],
            "Status": p["Trigger"]
        })
    else:
        hasil.append({
            "OPT": opt,
            "Kategori": kategori,
            "Target GDD": "-",
            "Tanggal Prediksi": "-",
            "Hari ke": "-",
            "Kondisi ENSO Saat Prediksi": "-",
            "Status": "Belum didukung"
        })

hasil_df = pd.DataFrame(hasil)

st.subheader(f"📋 Prediksi OPT Prioritas - {komoditas}")
st.dataframe(hasil_df, use_container_width=True)

st.subheader("📖 Interpretasi")

for _, row in hasil_df.iterrows():
    st.markdown(
        f"""
### {row['OPT']}

- **Kategori**: {row['Kategori']}
- **Tanggal Prediksi**: {row['Tanggal Prediksi']}
- **Kondisi ENSO Saat Prediksi**: {row['Kondisi ENSO Saat Prediksi']}
- **Status**: {row['Status']}
"""
    )

st.subheader("🌦️ Ringkasan Iklim Setelah Tanggal Tanam")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Rata-rata Tavg", f"{climate_prov['Tavg_C'].mean():.2f} °C")

with col2:
    st.metric("Rata-rata Tmax", f"{climate_prov['Tmax_C'].mean():.2f} °C")

with col3:
    st.metric("Total Curah Hujan", f"{climate_prov['PRCP'].sum():.1f} mm")

with col4:
    st.metric("ENSO Dominan", climate_prov["Kondisi ENSO"].mode().iloc[0])
