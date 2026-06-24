import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
import sys

# Agar file style.py yang ada di folder utama tetap bisa dibaca oleh halaman di folder pages
sys.path.append(str(Path(__file__).resolve().parents[1]))

try:
    import plotly.express as px
except Exception:
    px = None

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
    master = pd.read_csv(DATA_DIR / "master_dashboard_final.csv")
    climate_path = DATA_DIR / "master_climate_clean.csv"
    climate = pd.read_csv(climate_path) if climate_path.exists() else pd.DataFrame()
    return master, climate


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


def status_gdd(progress, tanggal_prediksi, target_gdd):
    if pd.isna(target_gdd):
        return "Parameter GDD belum tersedia"
    if tanggal_prediksi not in [None, "-"]:
        return "GDD tercapai"
    if progress >= 80:
        return "Mendekati target GDD"
    if progress >= 50:
        return "Akumulasi GDD sedang berkembang"
    return "Akumulasi GDD masih rendah"


def hitung_prediksi_gdd(climate, master, provinsi, tanggal_tanam, tbase, target_gdd):
    """
    Menghitung akumulasi GDD dari tanggal tanam sampai data iklim terakhir.
    Jika target GDD tercapai, tanggal pertama saat target tercapai dianggap sebagai tanggal potensi kemunculan OPT.
    """
    hasil_default = {
        "akumulasi_gdd": None,
        "progress": None,
        "tanggal_prediksi": None,
        "hari_ke": None,
        "sisa_gdd": None,
        "enso_prediksi": "-",
        "detail": pd.DataFrame(),
        "pesan": "Data iklim atau parameter GDD belum tersedia."
    }

    if climate.empty or pd.isna(tbase) or pd.isna(target_gdd) or target_gdd <= 0:
        return hasil_default

    climate = climate.copy()
    climate["DATE"] = pd.to_datetime(climate["DATE"], errors="coerce")
    climate = climate.dropna(subset=["DATE"])

    if "Provinsi" not in climate.columns or "Tavg_C" not in climate.columns:
        return hasil_default

    tanggal_tanam = pd.to_datetime(tanggal_tanam)
    climate_prov = climate[climate["Provinsi"].astype(str) == str(provinsi)].copy()
    climate_prov = climate_prov[climate_prov["DATE"] >= tanggal_tanam].sort_values("DATE")

    if climate_prov.empty:
        hasil_default["pesan"] = "Data iklim tidak tersedia setelah tanggal tanam yang dipilih."
        return hasil_default

    # Tambahkan ENSO ke data harian jika kolom Tahun/Triwulan tersedia
    if {"Tahun", "Triwulan"}.issubset(climate_prov.columns) and {"Tahun", "Triwulan", "Nino34"}.issubset(master.columns):
        enso_ref = (
            master[["Tahun", "Triwulan", "Nino34"]]
            .dropna(subset=["Nino34"])
            .drop_duplicates()
            .groupby(["Tahun", "Triwulan"], as_index=False)["Nino34"]
            .mean()
        )
        climate_prov = climate_prov.merge(enso_ref, on=["Tahun", "Triwulan"], how="left")
        climate_prov["Kondisi_ENSO"] = climate_prov["Nino34"].apply(klasifikasi_enso)
    else:
        climate_prov["Kondisi_ENSO"] = "-"

    climate_prov["GDD_Harian"] = (pd.to_numeric(climate_prov["Tavg_C"], errors="coerce") - float(tbase)).clip(lower=0)
    climate_prov["Akumulasi_GDD"] = climate_prov["GDD_Harian"].fillna(0).cumsum()

    akumulasi = float(climate_prov["Akumulasi_GDD"].iloc[-1])
    progress = min((akumulasi / float(target_gdd)) * 100, 100)
    sisa_gdd = max(float(target_gdd) - akumulasi, 0)

    tercapai = climate_prov[climate_prov["Akumulasi_GDD"] >= float(target_gdd)]
    tanggal_prediksi = None
    hari_ke = None
    enso_prediksi = "-"

    if not tercapai.empty:
        row_pred = tercapai.iloc[0]
        tanggal_prediksi = row_pred["DATE"].date()
        hari_ke = int((row_pred["DATE"] - tanggal_tanam).days)
        enso_prediksi = row_pred.get("Kondisi_ENSO", "-")

    return {
        "akumulasi_gdd": akumulasi,
        "progress": progress,
        "tanggal_prediksi": tanggal_prediksi,
        "hari_ke": hari_ke,
        "sisa_gdd": sisa_gdd,
        "enso_prediksi": enso_prediksi,
        "detail": climate_prov,
        "pesan": "OK"
    }


master, climate = load_data()

# Deteksi nama kolom otomatis agar aman dari perbedaan nama kolom.
COL_PROV = pick_col(master, ["Provinsi", "provinsi", "province"])
COL_KOM = pick_col(master, ["Komoditas", "Jenis Komoditas", "jenis_komoditas", "jenis komoditas", "komoditas"])
COL_OPT = pick_col(master, ["OPT", "Jenis OPT", "jenis_opt", "jenis opt", "OPT_std", "opt"])
COL_LUAS = pick_col(master, ["Luas_Serangan", "Total Luas Serangan (Ha)", "Total Luas Serangan", "total_luas_serangan", "luas serangan"])
COL_GDD = pick_col(master, ["GDD", "Target GDD", "target_gdd", "gdd"])
COL_TBASE = pick_col(master, ["Tbase", "T_base", "Suhu Dasar", "suhu dasar", "tbase"])
COL_HUJAN = pick_col(master, ["PRCP", "Curah Hujan", "curah_hujan", "hujan"])
COL_NINO = pick_col(master, ["Nino34", "Nino 3.4", "nino34", "oni"])
COL_KAT = pick_col(master, ["Kategori", "kategori"])
COL_TRIGGER = pick_col(master, ["Trigger", "trigger"])
COL_PARAM = pick_col(master, ["Parameter_Tersedia", "parameter_tersedia", "Parameter Tersedia"])

required = {
    "Provinsi": COL_PROV,
    "Komoditas/Jenis Komoditas": COL_KOM,
    "OPT/Jenis OPT": COL_OPT,
    "Luas Serangan": COL_LUAS,
    "Nino34/ENSO": COL_NINO,
}
missing = [name for name, col in required.items() if col is None]

hero(
    "🌱 Prediksi GDD & Rekomendasi Mitigasi OPT",
    "Halaman ini menggabungkan prediksi berbasis Growing Degree Days (GDD), kondisi ENSO, dan saran pengendalian OPT."
)

if missing:
    st.error("Ada kolom penting yang belum ditemukan: " + ", ".join(missing))
    st.write("Kolom yang tersedia pada data saat ini:")
    st.write(list(master.columns))
    st.stop()

# Pastikan kolom numerik aman dipakai
for col in [COL_LUAS, COL_GDD, COL_TBASE, COL_HUJAN, COL_NINO]:
    if col is not None:
        master[col] = pd.to_numeric(master[col], errors="coerce")

master["Kondisi_ENSO"] = master[COL_NINO].apply(klasifikasi_enso)

st.markdown("### Filter Data")

col1, col2, col3, col4 = st.columns(4)

with col1:
    provinsi_options = sorted(master[COL_PROV].dropna().astype(str).unique())
    provinsi = st.selectbox("Pilih Provinsi", provinsi_options)

with col2:
    komoditas_list = sorted(
        master[master[COL_PROV].astype(str) == provinsi][COL_KOM].dropna().astype(str).unique()
    )
    komoditas = st.selectbox("Pilih Komoditas", komoditas_list)

with col3:
    opt_list = sorted(
        master[
            (master[COL_PROV].astype(str) == provinsi) &
            (master[COL_KOM].astype(str) == komoditas)
        ][COL_OPT].dropna().astype(str).unique()
    )
    opt = st.selectbox("Pilih OPT", opt_list)

with col4:
    if not climate.empty and "DATE" in climate.columns:
        tanggal_series = pd.to_datetime(climate["DATE"], errors="coerce").dropna()
        min_date = tanggal_series.min().date()
        max_date = tanggal_series.max().date()
        default_date = datetime(2024, 1, 1).date()
        if default_date < min_date or default_date > max_date:
            default_date = min_date
        tanggal_tanam = st.date_input(
            "Tanggal Tanam / Awal Akumulasi",
            value=default_date,
            min_value=min_date,
            max_value=max_date
        )
    else:
        tanggal_tanam = st.date_input("Tanggal Tanam / Awal Akumulasi", value=datetime(2024, 1, 1).date())

filtered = master[
    (master[COL_PROV].astype(str) == provinsi) &
    (master[COL_KOM].astype(str) == komoditas) &
    (master[COL_OPT].astype(str) == opt)
].copy()

if filtered.empty:
    st.warning("Data tidak ditemukan untuk kombinasi filter ini.")
    st.stop()

# Ambil parameter biologis yang paling lengkap untuk OPT terpilih
param_candidates = filtered.copy()
if COL_PARAM and COL_PARAM in param_candidates.columns:
    # Tetap aman jika kolom berupa boolean atau teks
    param_candidates = param_candidates[
        param_candidates[COL_PARAM].astype(str).str.lower().isin(["true", "1", "ya", "yes"])
        | param_candidates[COL_PARAM].eq(True)
    ]
if COL_GDD and COL_TBASE:
    param_candidates = param_candidates.dropna(subset=[COL_GDD, COL_TBASE], how="any")

if not param_candidates.empty:
    param_row = param_candidates.iloc[0]
else:
    param_row = filtered.iloc[0]

target_gdd = param_row[COL_GDD] if COL_GDD else None
tbase = param_row[COL_TBASE] if COL_TBASE else None
kategori = param_row[COL_KAT] if COL_KAT else "-"
trigger = param_row[COL_TRIGGER] if COL_TRIGGER and pd.notna(param_row.get(COL_TRIGGER)) else "-"

gdd_result = hitung_prediksi_gdd(climate, master, provinsi, tanggal_tanam, tbase, target_gdd)

total_serangan = filtered[COL_LUAS].sum(skipna=True)
rata_hujan = filtered[COL_HUJAN].mean(skipna=True) if COL_HUJAN else 0
rata_nino = filtered[COL_NINO].mean(skipna=True)
kondisi_enso = klasifikasi_enso(rata_nino)
akumulasi_gdd = gdd_result["akumulasi_gdd"]
progress_gdd = gdd_result["progress"]
tanggal_prediksi = gdd_result["tanggal_prediksi"]
hari_ke = gdd_result["hari_ke"]

# Ambang sederhana, masih bisa disesuaikan lagi dengan kebutuhan analisis kamu
if total_serangan >= 500:
    risiko_historis = "Tinggi"
elif total_serangan >= 100:
    risiko_historis = "Sedang"
else:
    risiko_historis = "Rendah"

status_gdd_text = status_gdd(progress_gdd or 0, tanggal_prediksi, target_gdd)

# Risiko gabungan: historis + GDD
if risiko_historis == "Tinggi" or status_gdd_text == "GDD tercapai":
    risiko_gabungan = "Tinggi"
elif risiko_historis == "Sedang" or status_gdd_text == "Mendekati target GDD":
    risiko_gabungan = "Sedang"
else:
    risiko_gabungan = "Rendah"

st.markdown("### Ringkasan Risiko Gabungan")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Luas Serangan", f"{total_serangan:,.2f} Ha")
m2.metric("Target GDD OPT", f"{target_gdd:,.0f}" if pd.notna(target_gdd) else "Belum tersedia")
m3.metric("Akumulasi GDD", f"{akumulasi_gdd:,.1f}" if akumulasi_gdd is not None else "Tidak ada data")
m4.metric("Status Risiko", risiko_gabungan)

m5, m6, m7, m8 = st.columns(4)
m5.metric("Tbase", f"{tbase:,.1f} °C" if pd.notna(tbase) else "Belum tersedia")
m6.metric("Progress GDD", f"{progress_gdd:,.1f}%" if progress_gdd is not None else "Tidak ada data")
m7.metric("Prediksi Kemunculan", str(tanggal_prediksi) if tanggal_prediksi else "Belum tercapai")
m8.metric("ENSO", kondisi_enso)

warna_risiko = {
    "Tinggi": "#ef4444",
    "Sedang": "#f59e0b",
    "Rendah": "#22c55e"
}.get(risiko_gabungan, "#22c55e")

prediksi_text = "belum mencapai target GDD pada rentang data iklim yang tersedia"
if tanggal_prediksi:
    prediksi_text = f"diperkirakan mencapai target GDD pada <b>{tanggal_prediksi}</b> atau sekitar <b>hari ke-{hari_ke}</b> setelah tanggal tanam"

st.markdown(f"""
<div style="
background:white;
padding:20px;
border-radius:16px;
box-shadow:0 6px 18px rgba(0,0,0,0.08);
border-left:7px solid {warna_risiko};
">
<h3>Status Risiko Gabungan: {risiko_gabungan}</h3>
<p>
Wilayah <b>{provinsi}</b> pada komoditas <b>{komoditas}</b> dengan OPT <b>{opt}</b>
memiliki risiko historis <b>{risiko_historis}</b>. Berdasarkan tanggal tanam <b>{tanggal_tanam}</b>,
akumulasi GDD {prediksi_text}. Kondisi ENSO rata-rata pada data terpilih adalah <b>{kondisi_enso}</b>.
</p>
</div>
""", unsafe_allow_html=True)

st.markdown("### Prediksi GDD OPT Terpilih")

if pd.isna(target_gdd) or pd.isna(tbase):
    st.warning(
        "Parameter GDD/Tbase untuk OPT ini belum tersedia. "
        "Rekomendasi tetap dapat diberikan berdasarkan data historis serangan, curah hujan, dan ENSO."
    )
else:
    g1, g2 = st.columns([1, 2])
    with g1:
        st.info(f"""
        **Parameter Biologis**

        - **Kategori OPT**: {kategori}
        - **Tbase**: {tbase:.1f} °C
        - **Target GDD**: {target_gdd:.0f}
        - **Status GDD**: {status_gdd_text}
        - **Sisa GDD**: {gdd_result['sisa_gdd']:.1f} jika target belum tercapai
        - **ENSO saat prediksi**: {gdd_result['enso_prediksi']}
        """)
    with g2:
        detail_gdd = gdd_result["detail"]
        if px is not None and not detail_gdd.empty and "Akumulasi_GDD" in detail_gdd.columns:
            fig = px.line(
                detail_gdd,
                x="DATE",
                y="Akumulasi_GDD",
                title="Akumulasi GDD Sejak Tanggal Tanam"
            )
            fig.add_hline(y=float(target_gdd), line_dash="dash", annotation_text="Target GDD")
            fig.update_layout(height=360)
            st.plotly_chart(fig, use_container_width=True)
        elif not detail_gdd.empty:
            st.dataframe(detail_gdd[["DATE", "GDD_Harian", "Akumulasi_GDD"]].tail(30), use_container_width=True)

st.markdown("### Saran Mitigasi Berdasarkan GDD")

if pd.isna(target_gdd) or pd.isna(tbase):
    st.warning("""
    **Parameter GDD belum tersedia.**

    - Gunakan hasil pengamatan lapangan dan data historis luas serangan sebagai dasar awal.
    - Lengkapi parameter biologis OPT, terutama Tbase dan target GDD, agar prediksi kemunculan lebih kuat.
    - Untuk sementara, tingkatkan monitoring pada periode dengan luas serangan historis tinggi.
    """)
elif status_gdd_text == "GDD tercapai":
    st.error("""
    **Target GDD sudah tercapai.**

    - Lakukan inspeksi lapangan secepatnya pada tanaman inang.
    - Periksa gejala awal serangan OPT sesuai jenis OPT terpilih.
    - Pasang perangkap atau lakukan pengamatan populasi jika OPT termasuk serangga.
    - Siapkan pengendalian mekanis, biologis, atau kultur teknis sebelum serangan meluas.
    - Pestisida hanya digunakan jika serangan melewati ambang pengendalian dan sesuai anjuran label.
    """)
elif status_gdd_text == "Mendekati target GDD":
    st.warning("""
    **Akumulasi GDD mendekati target.**

    - Tingkatkan frekuensi monitoring karena potensi kemunculan OPT mulai meningkat.
    - Lakukan pengamatan 2–3 kali per minggu pada titik rawan.
    - Bersihkan gulma atau sisa tanaman yang dapat menjadi tempat berkembang OPT.
    - Siapkan tindakan pengendalian dini agar respons lebih cepat saat gejala muncul.
    """)
elif status_gdd_text == "Akumulasi GDD sedang berkembang":
    st.info("""
    **Akumulasi GDD masih dalam tahap perkembangan.**

    - Monitoring tetap dilakukan secara rutin.
    - Catat perubahan suhu, hujan, dan gejala awal pada tanaman.
    - Prioritaskan pencegahan melalui sanitasi lahan, pemupukan seimbang, dan pengairan yang baik.
    """)
else:
    st.success("""
    **Akumulasi GDD masih rendah.**

    - Risiko berbasis GDD masih relatif rendah.
    - Pertahankan monitoring dasar dan simpan data pengamatan sebagai bahan peringatan dini.
    - Belum diperlukan pengendalian intensif kecuali ditemukan gejala di lapangan.
    """)

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

st.markdown("### Rekomendasi Berdasarkan Tingkat Risiko Gabungan")

if risiko_gabungan == "Tinggi":
    st.error("""
    **Risiko Tinggi**

    - Lakukan inspeksi lapangan lebih intensif.
    - Prioritaskan wilayah dengan luas serangan terbesar dan fase GDD yang sudah tercapai.
    - Lakukan pengendalian mekanis, biologis, atau kultur teknis secepat mungkin.
    - Koordinasikan dengan petugas POPT atau penyuluh pertanian.
    - Pestisida dapat dipertimbangkan sebagai pilihan terakhir sesuai dosis dan aturan label.
    """)
elif risiko_gabungan == "Sedang":
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

st.markdown("### Data Historis yang Dipakai")

kolom_tampil = [COL_PROV, COL_KOM, COL_OPT, COL_LUAS, COL_NINO]
for c in [COL_GDD, COL_TBASE, COL_HUJAN, COL_KAT, COL_TRIGGER]:
    if c and c not in kolom_tampil:
        kolom_tampil.append(c)

st.dataframe(filtered[kolom_tampil].head(100), use_container_width=True)

st.caption(
    "Catatan: Prediksi GDD pada halaman ini memakai data iklim historis harian yang tersedia pada database, "
    "bukan prakiraan cuaca real-time. Rekomendasi bersifat pendukung keputusan awal. Keputusan pengendalian di lapangan tetap perlu mempertimbangkan hasil pengamatan langsung, ambang ekonomi, fase pertumbuhan tanaman, serta arahan petugas POPT atau penyuluh pertanian."
)
