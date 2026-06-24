import streamlit as st
import pandas as pd
from pathlib import Path

try:
    from style import apply_global_style, hero
except:
    def apply_global_style():
        pass
    def hero(title, subtitle=""):
        st.title(title)
        st.write(subtitle)

st.set_page_config(
    page_title="Rekomendasi Mitigasi",
    page_icon="🌱",
    layout="wide"
)

apply_global_style()

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

@st.cache_data
def load_data():
    return pd.read_csv(DATA_DIR / "master_dashboard_final.csv")

df = load_data()

def klasifikasi_enso(x):
    if pd.isna(x):
        return "Tidak ada data"
    elif x >= 0.5:
        return "El Niño"
    elif x <= -0.5:
        return "La Niña"
    else:
        return "Netral"

df["Kondisi_ENSO"] = df["Nino34"].apply(klasifikasi_enso)

hero(
    "🌱 Rekomendasi Mitigasi OPT",
    "Saran pengendalian berbasis kondisi iklim, ENSO, GDD, dan luas serangan OPT."
)

st.markdown("### Filter Data")

col1, col2, col3 = st.columns(3)

with col1:
    provinsi = st.selectbox(
        "Pilih Provinsi",
        sorted(df["Provinsi"].dropna().unique())
    )

with col2:
    komoditas_list = sorted(df[df["Provinsi"] == provinsi]["Komoditas"].dropna().unique())
    komoditas = st.selectbox("Pilih Komoditas", komoditas_list)

with col3:
    opt_list = sorted(
        df[
            (df["Provinsi"] == provinsi) &
            (df["Komoditas"] == komoditas)
        ]["OPT"].dropna().unique()
    )
    opt = st.selectbox("Pilih OPT", opt_list)

filtered = df[
    (df["Provinsi"] == provinsi) &
    (df["Komoditas"] == komoditas) &
    (df["OPT"] == opt)
].copy()

total_serangan = filtered["Luas_Serangan"].sum() if "Luas_Serangan" in filtered.columns else 0
rata_gdd = filtered["GDD"].mean() if "GDD" in filtered.columns else 0
rata_hujan = filtered["PRCP"].mean() if "PRCP" in filtered.columns else 0
rata_nino = filtered["Nino34"].mean() if "Nino34" in filtered.columns else 0
kondisi_enso = klasifikasi_enso(rata_nino)

if total_serangan >= 500:
    risiko = "Tinggi"
elif total_serangan >= 100:
    risiko = "Sedang"
else:
    risiko = "Rendah"

st.markdown("### Ringkasan Risiko")

m1, m2, m3, m4 = st.columns(4)

m1.metric("Total Luas Serangan", f"{total_serangan:,.2f}")
m2.metric("Rata-rata GDD", f"{rata_gdd:,.2f}")
m3.metric("Rata-rata Curah Hujan", f"{rata_hujan:,.2f}")
m4.metric("Kondisi ENSO", kondisi_enso)

st.markdown(f"""
<div style="
background:white;
padding:20px;
border-radius:16px;
box-shadow:0 6px 18px rgba(0,0,0,0.08);
border-left:7px solid #22c55e;
">
<h3>Status Risiko: {risiko}</h3>
<p>
Wilayah <b>{provinsi}</b> pada komoditas <b>{komoditas}</b> dengan OPT <b>{opt}</b>
memiliki status risiko <b>{risiko}</b> berdasarkan total luas serangan yang tersedia pada data.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Saran Mitigasi Berdasarkan Kondisi ENSO")

if kondisi_enso == "El Niño":
    st.warning("""
    **Kondisi El Niño terdeteksi.**  
    Saran mitigasi:
    
    - Tingkatkan monitoring OPT karena tanaman dapat mengalami stres akibat kondisi kering.
    - Atur jadwal irigasi agar tanaman tidak kekurangan air.
    - Gunakan mulsa atau teknik konservasi kelembapan tanah.
    - Waspadai peningkatan OPT yang menyukai kondisi panas dan kering.
    - Hindari penggunaan pestisida berlebihan, terutama saat tanaman mengalami stres.
    """)

elif kondisi_enso == "La Niña":
    st.info("""
    **Kondisi La Niña terdeteksi.**  
    Saran mitigasi:
    
    - Perbaiki drainase lahan agar tidak terjadi genangan.
    - Tingkatkan kewaspadaan terhadap penyakit tanaman akibat kelembapan tinggi.
    - Lakukan sanitasi lahan dan buang sisa tanaman yang berpotensi menjadi sumber penyakit.
    - Pantau perkembangan OPT setelah periode hujan tinggi.
    - Gunakan pengendalian hayati atau mekanis sebelum menggunakan pestisida.
    """)

elif kondisi_enso == "Netral":
    st.success("""
    **Kondisi ENSO Netral.**  
    Saran mitigasi:
    
    - Lakukan monitoring OPT secara rutin.
    - Gunakan ambang pengendalian sebelum melakukan tindakan.
    - Terapkan pengendalian hama terpadu atau PHT.
    - Jaga kebersihan lahan dan rotasi tanaman bila memungkinkan.
    - Gunakan pestisida hanya jika serangan melewati ambang ekonomi.
    """)

else:
    st.error("""
    Data ENSO belum tersedia untuk pilihan ini.  
    Gunakan rekomendasi umum berbasis monitoring lapangan dan data historis serangan OPT.
    """)

st.markdown("### Rekomendasi Berdasarkan Tingkat Risiko")

if risiko == "Tinggi":
    st.error("""
    **Risiko Tinggi**
    
    - Lakukan inspeksi lapangan lebih intensif.
    - Prioritaskan wilayah dengan luas serangan terbesar.
    - Lakukan pengendalian mekanis, biologis, atau kultur teknis secepat mungkin.
    - Koordinasikan dengan petugas POPT atau penyuluh pertanian.
    - Pestisida dapat dipertimbangkan sebagai pilihan terakhir sesuai dosis dan aturan label.
    """)

elif risiko == "Sedang":
    st.warning("""
    **Risiko Sedang**
    
    - Tingkatkan frekuensi pengamatan lahan.
    - Identifikasi gejala awal serangan OPT.
    - Lakukan sanitasi lahan.
    - Gunakan perangkap, musuh alami, atau pengendalian hayati bila tersedia.
    - Hindari tindakan kimia sebelum serangan melewati ambang pengendalian.
    """)

else:
    st.success("""
    **Risiko Rendah**
    
    - Pertahankan monitoring rutin.
    - Jaga kondisi tanaman tetap sehat.
    - Lakukan pemupukan dan pengairan seimbang.
    - Simpan data pengamatan sebagai dasar peringatan dini.
    - Belum diperlukan tindakan pengendalian intensif.
    """)

st.markdown("### Catatan")
st.caption(
    "Rekomendasi ini bersifat umum dan berbasis data historis. "
    "Keputusan pengendalian di lapangan tetap perlu mempertimbangkan hasil pengamatan langsung, "
    "ambang ekonomi, fase pertumbuhan tanaman, serta arahan petugas POPT atau penyuluh pertanian."
)