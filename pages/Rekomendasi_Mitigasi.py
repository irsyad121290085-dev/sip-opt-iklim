import streamlit as st
import pandas as pd
from pathlib import Path
import sys

# Agar file style.py yang ada di folder utama tetap bisa dibaca oleh halaman di folder pages
sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    from style import apply_global_style, hero
except Exception:
    def apply_global_style():
        pass
    def hero(title, subtitle=""):
        st.title(title)
        if subtitle:
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


def pick_col(df, candidates):
    """Mencari nama kolom secara fleksibel, agar aman jika nama kolom berbeda."""
    lower_map = {str(c).strip().lower(): c for c in df.columns}
    for cand in candidates:
        key = cand.strip().lower()
        if key in lower_map:
            return lower_map[key]
    return None


def klasifikasi_enso(x):
    if pd.isna(x):
        return "Tidak ada data"
    if x >= 0.5:
        return "El Niño"
    if x <= -0.5:
        return "La Niña"
    return "Netral"


df = load_data()

# Deteksi nama kolom otomatis. Ini memperbaiki error KeyError: 'Provinsi'.
COL_PROV = pick_col(df, ["Provinsi", "provinsi", "province"])
COL_KOM = pick_col(df, ["Komoditas", "Jenis Komoditas", "jenis_komoditas", "jenis komoditas", "komoditas"])
COL_OPT = pick_col(df, ["OPT", "Jenis OPT", "jenis_opt", "jenis opt", "OPT_std", "opt"])
COL_LUAS = pick_col(df, ["Luas_Serangan", "Total Luas Serangan (Ha)", "Total Luas Serangan", "total_luas_serangan", "luas serangan"])
COL_GDD = pick_col(df, ["GDD", "gdd"])
COL_HUJAN = pick_col(df, ["PRCP", "Curah Hujan", "curah_hujan", "hujan"])
COL_NINO = pick_col(df, ["Nino34", "Nino 3.4", "nino34", "oni"])

required = {
    "Provinsi": COL_PROV,
    "Komoditas/Jenis Komoditas": COL_KOM,
    "OPT/Jenis OPT": COL_OPT,
    "Luas Serangan": COL_LUAS,
    "Nino34/ENSO": COL_NINO,
}
missing = [name for name, col in required.items() if col is None]

hero(
    "🌱 Rekomendasi Mitigasi OPT",
    "Saran pengendalian berbasis kondisi iklim, ENSO, GDD, dan luas serangan OPT."
)

if missing:
    st.error("Ada kolom penting yang belum ditemukan: " + ", ".join(missing))
    st.write("Kolom yang tersedia pada data saat ini:")
    st.write(list(df.columns))
    st.stop()

# Pastikan kolom numerik aman dipakai
for col in [COL_LUAS, COL_GDD, COL_HUJAN, COL_NINO]:
    if col is not None:
        df[col] = pd.to_numeric(df[col], errors="coerce")

df["Kondisi_ENSO"] = df[COL_NINO].apply(klasifikasi_enso)

st.markdown("### Filter Data")

col1, col2, col3 = st.columns(3)

with col1:
    provinsi_options = sorted(df[COL_PROV].dropna().astype(str).unique())
    provinsi = st.selectbox("Pilih Provinsi", provinsi_options)

with col2:
    komoditas_list = sorted(
        df[df[COL_PROV].astype(str) == provinsi][COL_KOM].dropna().astype(str).unique()
    )
    komoditas = st.selectbox("Pilih Komoditas", komoditas_list)

with col3:
    opt_list = sorted(
        df[
            (df[COL_PROV].astype(str) == provinsi) &
            (df[COL_KOM].astype(str) == komoditas)
        ][COL_OPT].dropna().astype(str).unique()
    )
    opt = st.selectbox("Pilih OPT", opt_list)

filtered = df[
    (df[COL_PROV].astype(str) == provinsi) &
    (df[COL_KOM].astype(str) == komoditas) &
    (df[COL_OPT].astype(str) == opt)
].copy()

if filtered.empty:
    st.warning("Data tidak ditemukan untuk kombinasi filter ini.")
    st.stop()

total_serangan = filtered[COL_LUAS].sum(skipna=True)
rata_gdd = filtered[COL_GDD].mean(skipna=True) if COL_GDD else 0
rata_hujan = filtered[COL_HUJAN].mean(skipna=True) if COL_HUJAN else 0
rata_nino = filtered[COL_NINO].mean(skipna=True)
kondisi_enso = klasifikasi_enso(rata_nino)

# Ambang sederhana, masih bisa disesuaikan lagi dengan kebutuhan analisis kamu
if total_serangan >= 500:
    risiko = "Tinggi"
elif total_serangan >= 100:
    risiko = "Sedang"
else:
    risiko = "Rendah"

st.markdown("### Ringkasan Risiko")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Luas Serangan", f"{total_serangan:,.2f} Ha")
m2.metric("Rata-rata GDD", f"{rata_gdd:,.2f}" if pd.notna(rata_gdd) else "Tidak ada data")
m3.metric("Rata-rata Curah Hujan", f"{rata_hujan:,.2f} mm" if pd.notna(rata_hujan) else "Tidak ada data")
m4.metric("Kondisi ENSO", kondisi_enso)

warna_risiko = {
    "Tinggi": "#ef4444",
    "Sedang": "#f59e0b",
    "Rendah": "#22c55e"
}.get(risiko, "#22c55e")

st.markdown(f"""
<div style="
background:white;
padding:20px;
border-radius:16px;
box-shadow:0 6px 18px rgba(0,0,0,0.08);
border-left:7px solid {warna_risiko};
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

    - Tingkatkan monitoring OPT karena tanaman dapat mengalami stres akibat kondisi kering.
    - Atur jadwal irigasi agar tanaman tidak kekurangan air.
    - Gunakan mulsa atau teknik konservasi kelembapan tanah.
    - Waspadai peningkatan OPT yang menyukai kondisi panas dan kering.
    - Hindari penggunaan pestisida berlebihan, terutama saat tanaman mengalami stres.
    """)
elif kondisi_enso == "La Niña":
    st.info("""
    **Kondisi La Niña terdeteksi.**

    - Perbaiki drainase lahan agar tidak terjadi genangan.
    - Tingkatkan kewaspadaan terhadap penyakit tanaman akibat kelembapan tinggi.
    - Lakukan sanitasi lahan dan buang sisa tanaman yang berpotensi menjadi sumber penyakit.
    - Pantau perkembangan OPT setelah periode hujan tinggi.
    - Gunakan pengendalian hayati atau mekanis sebelum menggunakan pestisida.
    """)
elif kondisi_enso == "Netral":
    st.success("""
    **Kondisi ENSO Netral.**

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

st.markdown("### Data yang Dipakai")
st.dataframe(
    filtered[[COL_PROV, COL_KOM, COL_OPT, COL_LUAS, COL_NINO] + ([COL_GDD] if COL_GDD else []) + ([COL_HUJAN] if COL_HUJAN else [])].head(100),
    use_container_width=True
)

st.caption(
    "Rekomendasi ini bersifat umum dan berbasis data historis. Keputusan pengendalian di lapangan tetap perlu mempertimbangkan hasil pengamatan langsung, ambang ekonomi, fase pertumbuhan tanaman, serta arahan petugas POPT atau penyuluh pertanian."
)
