# Sistem Informasi OPT Sumatera - Revisi ENSO

Revisi utama:
1. Menambahkan halaman `Analisis_ENSO.py`.
2. Menambahkan klasifikasi kondisi ENSO: El Niño, La Niña, Netral.
3. Memperbaiki path file agar aman di Windows, Linux, dan Streamlit Cloud.
4. Menambahkan `folium` dan `streamlit-folium` ke requirements.
5. Menambahkan filter ENSO pada Dashboard Historis.
6. Menambahkan informasi ENSO pada Prediksi GDD.

Cara menjalankan:
```bash
pip install -r requirements.txt
streamlit run app.py
```

Catatan:
- Data `master_dashboard_final.csv` sudah memiliki kolom `Nino34`.
- Klasifikasi sederhana:
  - Nino34 >= 0.5 = El Niño
  - Nino34 <= -0.5 = La Niña
  - selain itu = Netral
