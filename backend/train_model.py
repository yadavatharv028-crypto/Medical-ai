
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import json


BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH  = os.path.join(BASE_DIR, "dataset", "disease_dataset.csv")
MODEL_PATH = os.path.join(BASE_DIR, "backend", "disease_model.pkl")
META_PATH  = os.path.join(BASE_DIR, "backend", "model_meta.json")

def train():
    print("=" * 60)
    print("  AI Medical Appointment & Disease Prediction System")
    print("  Model Training Script")
    print("=" * 60)

    #load file
    print("\n[1/5] Loading dataset …")
    df = pd.read_csv(DATA_PATH)
    print(f"      Rows: {len(df)}  |  Columns: {df.shape[1]}")


    print("[2/5] Preparing features & labels …")
    X = df.drop(columns=["Disease"])
    y = df["Disease"]

    # Encode string labels to integers
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    symptom_columns = list(X.columns)
    disease_classes = list(le.classes_)
    print(f"      Symptoms  : {len(symptom_columns)}")
    print(f"      Diseases  : {len(disease_classes)}")

    # train/test/split
    print("[3/5] Splitting data (80/20) …")
    # 
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
        )
    except ValueError:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y_encoded, test_size=0.2, random_state=42
        )
    print(f"      Train samples: {len(X_train)}  |  Test samples: {len(X_test)}")

    # here we train our model
    print("[4/5] Training Random Forest classifier …")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)

    # Evaluate
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"      Training accuracy : {model.score(X_train, y_train)*100:.1f} %")
    print(f"      Test     accuracy : {acc*100:.1f} %")


    print("[5/5] Saving model …")
    # Bundle model, encoder, and symptom list together
    bundle = {
        "model":    model,
        "encoder":  le,
        "symptoms": symptom_columns,
    }
    joblib.dump(bundle, MODEL_PATH)
    print(f"      Saved → {MODEL_PATH}")

    
    meta = {
        "symptoms": [str(s) for s in symptom_columns],
        "diseases": [str(d) for d in disease_classes],
        "accuracy": round(float(acc) * 100, 1),
    }
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"      Metadata → {META_PATH}")

    print("\n✓ Training complete!\n")
    return symptom_columns, disease_classes, acc


if __name__ == "__main__":
    train()
