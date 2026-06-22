import io
import json
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

import joblib
import pandas as pd
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import MultinomialNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC

from .db import BASE_DIR, dumps, execute, fetch_all, fetch_one, init_db
from .preprocess import preprocess_text

app = FastAPI(title="Sentiment Analysis Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = BASE_DIR / "storage" / "uploads"
MODEL_DIR = BASE_DIR / "storage" / "models"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)
init_db()


class LoginPayload(BaseModel):
    email: str
    password: str


class AnalysisPayload(BaseModel):
    dataset_id: int
    algorithm: str = Field(pattern="^(naive_bayes|svm|knn)$")
    text_column: Optional[str] = None
    label_column: Optional[str] = None
    test_size: float = Field(default=0.2, gt=0.0, lt=0.5)
    random_state: int = 42
    k_neighbors: int = Field(default=5, ge=1, le=25)


class PredictPayload(BaseModel):
    analysis_id: int
    text: str


@app.get("/")
def root():
    return {
        "message": "Backend analisis sentimen aktif.",
        "docs": "/docs",
        "algorithms": ["naive_bayes", "svm", "knn"],
    }


@app.post("/auth/login")
def login(payload: LoginPayload):
    user = fetch_one(
        "SELECT id, name, email FROM users WHERE email = ? AND password = ?",
        (payload.email, payload.password),
    )
    if not user:
        raise HTTPException(status_code=401, detail="Email atau password salah")
    return {"message": "Login berhasil", "user": user}


@app.post("/datasets/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    text_column: Optional[str] = None,
    label_column: Optional[str] = None,
    user_id: int = 1,
):
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File harus berformat CSV")

    content = await file.read()
    try:
        df = pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Gagal membaca CSV: {exc}")

    if df.empty:
        raise HTTPException(status_code=400, detail="Dataset kosong")

    cols_lower = {c.lower(): c for c in df.columns}
    detected_text = text_column or cols_lower.get("text") or cols_lower.get("ulasan") or cols_lower.get("tweet") or cols_lower.get("komentar")
    detected_label = label_column or cols_lower.get("label") or cols_lower.get("sentimen") or cols_lower.get("sentiment")

    if not detected_text or not detected_label:
        raise HTTPException(
            status_code=400,
            detail="Kolom teks/label tidak ditemukan. Gunakan parameter text_column dan label_column.",
        )

    missing_values = df[[detected_text, detected_label]].isna().sum().sum()
    if missing_values:
        df = df.dropna(subset=[detected_text, detected_label]).reset_index(drop=True)

    unique_labels = sorted(df[detected_label].astype(str).str.strip().unique().tolist())
    if len(unique_labels) < 2:
        raise HTTPException(status_code=400, detail="Jumlah kelas label minimal 2")

    safe_name = f"{uuid4().hex}_{Path(file.filename).name}"
    stored_path = UPLOAD_DIR / safe_name
    df.to_csv(stored_path, index=False)

    dataset_id = execute(
        """
        INSERT INTO datasets (file_name, stored_path, row_count, text_column, label_column, uploaded_by)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (file.filename, str(stored_path), int(len(df)), detected_text, detected_label, user_id),
    )

    return {
        "message": "Dataset berhasil diunggah",
        "dataset_id": dataset_id,
        "row_count": int(len(df)),
        "columns": list(df.columns),
        "text_column": detected_text,
        "label_column": detected_label,
        "labels": unique_labels,
    }


@app.get("/datasets")
def list_datasets():
    return fetch_all(
        "SELECT id, file_name, row_count, text_column, label_column, uploaded_at FROM datasets ORDER BY id DESC"
    )


@app.get("/datasets/{dataset_id}/preview")
def preview_dataset(dataset_id: int, limit: int = Query(default=10, ge=1, le=50)):
    dataset = fetch_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")
    df = pd.read_csv(dataset["stored_path"])
    return {
        "dataset": {
            "id": dataset["id"],
            "file_name": dataset["file_name"],
            "row_count": dataset["row_count"],
            "text_column": dataset["text_column"],
            "label_column": dataset["label_column"],
        },
        "preview": df.head(limit).fillna("").to_dict(orient="records"),
    }


@app.get("/datasets/{dataset_id}/search")
def search_dataset(dataset_id: int, keyword: str, label: Optional[str] = None, limit: int = Query(default=20, ge=1, le=100)):
    dataset = fetch_one("SELECT * FROM datasets WHERE id = ?", (dataset_id,))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")
    df = pd.read_csv(dataset["stored_path"])
    text_col = dataset["text_column"]
    label_col = dataset["label_column"]
    filtered = df[df[text_col].astype(str).str.contains(keyword, case=False, na=False)]
    if label:
        filtered = filtered[filtered[label_col].astype(str).str.lower() == label.lower()]
    return {
        "total_found": int(len(filtered)),
        "results": filtered.head(limit).fillna("").to_dict(orient="records"),
    }


@app.post("/analysis/run")
def run_analysis(payload: AnalysisPayload):
    dataset = fetch_one("SELECT * FROM datasets WHERE id = ?", (payload.dataset_id,))
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset tidak ditemukan")

    df = pd.read_csv(dataset["stored_path"])
    text_col = payload.text_column or dataset["text_column"]
    label_col = payload.label_column or dataset["label_column"]

    if text_col not in df.columns or label_col not in df.columns:
        raise HTTPException(status_code=400, detail="Kolom teks/label tidak valid")

    df = df[[text_col, label_col]].dropna().copy()
    df[text_col] = df[text_col].astype(str)
    df[label_col] = df[label_col].astype(str).str.strip()
    df["processed_text"] = df[text_col].apply(preprocess_text)
    df = df[df["processed_text"].str.len() > 0].reset_index(drop=True)

    if len(df) < 10:
        raise HTTPException(status_code=400, detail="Dataset terlalu kecil setelah preprocessing")

    labels = sorted(df[label_col].unique().tolist())
    X_train, X_test, y_train, y_test = train_test_split(
        df["processed_text"],
        df[label_col],
        test_size=payload.test_size,
        random_state=payload.random_state,
        stratify=df[label_col],
    )

    classifier = build_classifier(payload.algorithm, payload.k_neighbors)
    model = Pipeline([
        ("tfidf", TfidfVectorizer(max_features=5000, ngram_range=(1, 2))),
        ("clf", classifier),
    ])
    model.fit(X_train, y_train)
    y_pred = model.predict(X_test)

    cm = confusion_matrix(y_test, y_pred, labels=labels)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "precision_macro": round(float(precision_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "recall_macro": round(float(recall_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "f1_macro": round(float(f1_score(y_test, y_pred, average="macro", zero_division=0)), 4),
        "train_size": int(len(X_train)),
        "test_size": int(len(X_test)),
        "confusion_matrix": cm.tolist(),
        "labels": labels,
        "classification_report": classification_report(y_test, y_pred, output_dict=True, zero_division=0),
    }

    analysis_id = execute(
        """
        INSERT INTO analyses (dataset_id, algorithm, test_size, metrics_json, labels_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload.dataset_id, payload.algorithm, payload.test_size, dumps(metrics), json.dumps(labels, ensure_ascii=False)),
    )

    model_path = MODEL_DIR / f"analysis_{analysis_id}_{payload.algorithm}.joblib"
    joblib.dump({
        "model": model,
        "algorithm": payload.algorithm,
        "labels": labels,
        "text_column": text_col,
        "label_column": label_col,
    }, model_path)

    return {
        "message": "Analisis berhasil dijalankan",
        "analysis_id": analysis_id,
        "algorithm": payload.algorithm,
        "metrics": metrics,
        "model_path": str(model_path),
    }


@app.get("/analysis")
def list_analyses():
    rows = fetch_all(
        """
        SELECT a.id, a.dataset_id, d.file_name, a.algorithm, a.test_size, a.created_at
        FROM analyses a
        JOIN datasets d ON d.id = a.dataset_id
        ORDER BY a.id DESC
        """
    )
    return rows


@app.get("/analysis/{analysis_id}")
def analysis_detail(analysis_id: int):
    row = fetch_one(
        """
        SELECT a.id, a.dataset_id, d.file_name, a.algorithm, a.test_size, a.metrics_json, a.created_at
        FROM analyses a
        JOIN datasets d ON d.id = a.dataset_id
        WHERE a.id = ?
        """,
        (analysis_id,),
    )
    if not row:
        raise HTTPException(status_code=404, detail="Hasil analisis tidak ditemukan")
    row["metrics"] = json.loads(row.pop("metrics_json"))
    return row


@app.post("/predict")
def predict_text(payload: PredictPayload):
    analysis = fetch_one("SELECT * FROM analyses WHERE id = ?", (payload.analysis_id,))
    if not analysis:
        raise HTTPException(status_code=404, detail="Analisis tidak ditemukan")

    model_path = MODEL_DIR / f"analysis_{payload.analysis_id}_{analysis['algorithm']}.joblib"
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model tidak ditemukan")

    bundle = joblib.load(model_path)
    model = bundle["model"]
    processed = preprocess_text(payload.text)
    if not processed:
        raise HTTPException(status_code=400, detail="Teks kosong setelah preprocessing")
    prediction = model.predict([processed])[0]
    result: Dict[str, object] = {"processed_text": processed, "prediction": prediction}
    if hasattr(model.named_steps["clf"], "predict_proba"):
        proba = model.predict_proba([processed])[0]
        result["probabilities"] = {label: round(float(score), 4) for label, score in zip(model.classes_, proba)}
    return result


@app.get("/health")
def health_check():
    return {"status": "ok"}


def build_classifier(algorithm: str, k_neighbors: int):
    if algorithm == "naive_bayes":
        return MultinomialNB()
    if algorithm == "svm":
        return LinearSVC()
    if algorithm == "knn":
        return KNeighborsClassifier(n_neighbors=k_neighbors, metric="cosine")
    raise HTTPException(status_code=400, detail="Algoritma tidak didukung")
