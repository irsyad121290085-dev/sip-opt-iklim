import streamlit as st

st.title("ℹ️ Tentang Sistem")

st.markdown("""
### Data

- OPT Perkebunan Sumatera
- Temperatur Harian NOAA GSOD
- Curah Hujan NOAA GSOD
- ENSO/Niño 3.4

### Metode

**Growing Degree Days (GDD)**

GDD = Σ(Tavg − Tbase)

**Klasifikasi ENSO sederhana**

- Nino34 ≥ 0,5: El Niño
- Nino34 ≤ -0,5: La Niña
- -0,5 < Nino34 < 0,5: Netral

### Wilayah

- Aceh
- Sumatera Utara
- Sumatera Barat
- Riau
- Kepulauan Riau
- Jambi
- Sumatera Selatan
- Bengkulu
- Lampung
- Bangka Belitung

### Catatan

Sistem ini bersifat informatif dan prediktif awal. Hasil prediksi perlu divalidasi
dengan data lapangan, data budidaya, musim tanam, varietas tanaman, serta laporan OPT terbaru.
""")
