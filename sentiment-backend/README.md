# Backend Python Analisis Sentimen

Backend ini dibuat dengan FastAPI untuk kebutuhan sistem analisis sentimen berbasis web dengan alur: upload dataset CSV, validasi kolom teks dan label, preprocessing Bahasa Indonesia, TF-IDF, training/testing model Naive Bayes, SVM, dan KNN, lalu penyajian hasil evaluasi.

## Fitur
- Login sederhana untuk demo (`admin@example.com` / `admin123`)
- Upload dataset CSV
- Deteksi otomatis kolom `text/ulasan/tweet/komentar` dan `label/sentimen/sentiment`
- Preview dataset dan pencarian data berdasarkan kata kunci
- Training model `naive_bayes`, `svm`, atau `knn`
- Evaluasi metrik: accuracy, precision, recall, F1-score, confusion matrix
- Prediksi teks baru dari model hasil training
- Penyimpanan metadata dataset dan hasil analisis ke SQLite

## Struktur dataset yang disarankan
```csv
text,label
"aplikasi ini sangat membantu",positif
"layanannya lambat dan sering error",negatif
"fiturnya biasa saja",netral
```

## Menjalankan proyek
```bash
cd output/sentiment-backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\\Scripts\\activate   # Windows PowerShell
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Dokumentasi interaktif tersedia di:
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

## Endpoint utama
- `POST /auth/login`
- `POST /datasets/upload`
- `GET /datasets`
- `GET /datasets/{dataset_id}/preview`
- `GET /datasets/{dataset_id}/search?keyword=...`
- `POST /analysis/run`
- `GET /analysis`
- `GET /analysis/{analysis_id}`
- `POST /predict`
- `GET /health`

## Contoh request analisis
```json
{
  "dataset_id": 1,
  "algorithm": "svm",
  "test_size": 0.2,
  "random_state": 42,
  "k_neighbors": 5
}
```

## Catatan
- Untuk dokumen PPL, backend ini sudah mengikuti kebutuhan umum: upload dataset, preprocessing, TF-IDF, perbandingan Naive Bayes/SVM/KNN, dan dashboard metrics.
- Jika label dataset berupa angka (`0,1,2`), kamu tetap bisa pakai langsung; kalau mau lebih rapi, ubah dulu menjadi `positif, netral, negatif`.
