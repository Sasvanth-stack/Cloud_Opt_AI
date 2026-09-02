"""
train_model.py
==============
AI Cloud Resource Optimization - Random Forest Classifier
---------------------------------------------------------
Trains a model to predict the optimization action for a cloud resource:
  - scale_up        : Resource is overloaded, needs more capacity
  - scale_down      : Resource is idle/under-used, cost can be saved
  - no_action       : Resource is running optimally

Run:
    python train_model.py
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report,
)
from sklearn.preprocessing import LabelEncoder

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DATA_DIR   = os.path.join(BASE_DIR, "data")
MODEL_DIR  = os.path.join(BASE_DIR, "models")
CSV_PATH   = os.path.join(DATA_DIR, "Cloud_Dataset.csv")
MODEL_PATH = os.path.join(MODEL_DIR, "resource_optimizer.pkl")
META_PATH  = os.path.join(MODEL_DIR, "model_metadata.json")

os.makedirs(DATA_DIR,  exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# ─────────────────────────────────────────────
# STEP 1: GENERATE DATASET (if not present)
# ─────────────────────────────────────────────
def generate_dataset(n_samples=2000):
    """
    Generates a realistic synthetic cloud resource dataset.
    Labels are derived from resource usage rules — no target leakage.
    """
    np.random.seed(42)

    # Cloud providers and VM types
    providers = ["AWS", "GCP", "Azure"]
    regions   = ["us-east-1", "us-west-2", "eu-west-1", "ap-south-1"]
    vm_types  = ["t3.micro", "t3.medium", "t3.large", "m5.xlarge", "c5.2xlarge"]
    vcpu_map  = {"t3.micro": 2,  "t3.medium": 2,  "t3.large": 2,  "m5.xlarge": 4, "c5.2xlarge": 8}
    ram_map   = {"t3.micro": 1,  "t3.medium": 4,  "t3.large": 8,  "m5.xlarge": 16, "c5.2xlarge": 16}
    price_map = {"t3.micro": 0.0116, "t3.medium": 0.0464, "t3.large": 0.0928,
                 "m5.xlarge": 0.192, "c5.2xlarge": 0.340}

    records = []
    for _ in range(n_samples):
        vm   = np.random.choice(vm_types)
        prov = np.random.choice(providers)
        reg  = np.random.choice(regions)

        # Randomly choose a workload regime
        regime = np.random.choice(["high", "medium", "low"], p=[0.30, 0.40, 0.30])

        if regime == "high":
            cpu     = np.random.uniform(75, 100)
            mem     = np.random.uniform(70, 100)
            net_io  = np.random.uniform(500, 1500)
            disk_io = np.random.uniform(300, 900)
        elif regime == "medium":
            cpu     = np.random.uniform(30, 75)
            mem     = np.random.uniform(30, 70)
            net_io  = np.random.uniform(100, 500)
            disk_io = np.random.uniform(50, 300)
        else:  # low
            cpu     = np.random.uniform(0, 30)
            mem     = np.random.uniform(0, 30)
            net_io  = np.random.uniform(0, 100)
            disk_io = np.random.uniform(0, 50)

        vcpu       = vcpu_map[vm]
        ram        = ram_map[vm]
        price      = price_map[vm]
        latency    = np.random.uniform(5, 500)
        throughput = np.random.uniform(10, 2000)
        hours      = np.random.uniform(1, 720)
        cost       = round(price * hours, 4)
        utilization = round((cpu * 0.5 + mem * 0.5), 2)

        # Rule-based target label (no leakage — derived from same data)
        if cpu > 80 or mem > 80:
            target = "scale_up"
        elif cpu < 20 and mem < 20:
            target = "scale_down"
        else:
            target = "no_action"

        records.append({
            "cpu_usage":    round(cpu, 2),
            "memory_usage": round(mem, 2),
            "net_io":       round(net_io, 2),
            "disk_io":      round(disk_io, 2),
            "cloud_provider": prov,
            "region":       reg,
            "vm_type":      vm,
            "vCPU":         vcpu,
            "RAM_GB":       ram,
            "price_per_hour": price,
            "latency_ms":   round(latency, 2),
            "throughput":   round(throughput, 2),
            "cost":         cost,
            "utilization":  utilization,
            "target":       target,
        })

    df = pd.DataFrame(records)
    df.to_csv(CSV_PATH, index=False)
    print(f"[INFO] Dataset generated: {n_samples} rows -> {CSV_PATH}")
    return df


# ─────────────────────────────────────────────
# STEP 2: LOAD & INSPECT
# ─────────────────────────────────────────────
def load_and_inspect(df):
    print("\n" + "="*60)
    print("  DATASET INSPECTION")
    print("="*60)
    print(f"  Rows    : {df.shape[0]}")
    print(f"  Columns : {df.shape[1]}")
    print(f"\n  Column names:\n  {list(df.columns)}")
    print(f"\n  Missing values:\n{df.isnull().sum().to_string()}")
    print(f"\n  Target class distribution:")
    dist = df["target"].value_counts()
    for cls, cnt in dist.items():
        pct = cnt / len(df) * 100
        print(f"    {cls:<15}: {cnt:>5} rows  ({pct:.1f}%)")
    print("="*60)


# ─────────────────────────────────────────────
# STEP 3: CLEAN DATA
# ─────────────────────────────────────────────
def clean_data(df):
    before = len(df)
    df = df.drop_duplicates()
    after_dup = len(df)

    numeric_cols = ["cpu_usage", "memory_usage", "net_io", "disk_io",
                    "vCPU", "RAM_GB", "price_per_hour", "latency_ms",
                    "throughput", "cost", "utilization"]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=numeric_cols + ["target"])
    after_clean = len(df)

    print(f"\n[CLEAN] Rows before: {before} | After dup removal: {after_dup} | After NA drop: {after_clean}")
    return df


# ─────────────────────────────────────────────
# STEP 4: FEATURE SELECTION & ENCODING
# ─────────────────────────────────────────────
FEATURES = [
    "cpu_usage",
    "memory_usage",
    "net_io",
    "disk_io",
    "vCPU",
    "RAM_GB",
    "price_per_hour",
    "latency_ms",
    "throughput",
    "cost",
    "utilization",
]
TARGET = "target"


def prepare_data(df):
    X = df[FEATURES].copy()
    y = df[TARGET].copy()

    # Encode target labels
    le = LabelEncoder()
    y_encoded = le.fit_transform(y)

    print(f"\n[FEATURES] Selected: {FEATURES}")
    print(f"[TARGET]   Classes  : {list(le.classes_)}")
    return X, y_encoded, le


# ─────────────────────────────────────────────
# STEP 5: TRAIN
# ─────────────────────────────────────────────
def train_model(X_train, y_train):
    print("\n[TRAIN] Training RandomForestClassifier ...")
    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=None,
        min_samples_split=2,
        min_samples_leaf=1,
        random_state=42,
        n_jobs=-1,
    )
    model.fit(X_train, y_train)
    print("[TRAIN] Training complete.")
    return model


# ─────────────────────────────────────────────
# STEP 6: EVALUATE
# ─────────────────────────────────────────────
def evaluate_model(model, X_test, y_test, le):
    y_pred = model.predict(X_test)

    acc  = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, average="weighted", zero_division=0)
    rec  = recall_score(y_test, y_pred,    average="weighted", zero_division=0)
    f1   = f1_score(y_test, y_pred,        average="weighted", zero_division=0)
    cm   = confusion_matrix(y_test, y_pred)

    print("\n" + "="*60)
    print("  MODEL EVALUATION RESULTS")
    print("="*60)
    print(f"  Accuracy  : {acc:.4f}  ({acc*100:.2f}%)")
    print(f"  Precision : {prec:.4f}")
    print(f"  Recall    : {rec:.4f}")
    print(f"  F1-Score  : {f1:.4f}")
    print(f"\n  Confusion Matrix:")
    print(f"  Classes: {list(le.classes_)}")
    for i, row in enumerate(cm):
        print(f"    {le.classes_[i]:<15}: {row}")
    print(f"\n  Per-Class Report:")
    print(classification_report(y_test, y_pred, target_names=le.classes_))
    print("="*60)

    return {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1}


# ─────────────────────────────────────────────
# STEP 7: SAVE MODEL + METADATA
# ─────────────────────────────────────────────
def save_model(model, le, metrics):
    bundle = {
        "model":    model,
        "encoder":  le,
        "features": FEATURES,
    }
    joblib.dump(bundle, MODEL_PATH)

    metadata = {
        "model_type": "RandomForestClassifier",
        "features":   FEATURES,
        "target":     TARGET,
        "classes":    list(le.classes_),
        "metrics": {
            "accuracy":  round(metrics["accuracy"],  4),
            "precision": round(metrics["precision"], 4),
            "recall":    round(metrics["recall"],    4),
            "f1_score":  round(metrics["f1"],        4),
        },
        "n_estimators":    200,
        "train_test_split": "80/20",
        "random_state":     42,
    }
    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"\n[SAVE] Model saved    : {MODEL_PATH}")
    print(f"[SAVE] Metadata saved : {META_PATH}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("\n" + "#"*60)
    print("  AI Cloud Resource Optimization - ML Training")
    print("#"*60)

    # Load or generate dataset
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
        # If file loaded but is essentially empty (all NaN), regenerate
        if df.dropna(how="all").shape[0] <= 1:
            print("[WARN] Existing CSV is empty, generating fresh dataset...")
            df = generate_dataset(2000)
        else:
            print(f"[INFO] Loaded existing dataset: {CSV_PATH} ({len(df)} rows)")
    else:
        df = generate_dataset(2000)

    load_and_inspect(df)
    df = clean_data(df)

    X, y, le = prepare_data(df)

    # Train/Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"\n[SPLIT] Train size: {len(X_train)} | Test size: {len(X_test)}")

    model   = train_model(X_train, y_train)
    metrics = evaluate_model(model, X_test, y_test, le)
    save_model(model, le, metrics)

    print("\n[DONE] Model training pipeline complete!")
    print(f"       Run predictions with:  python predict.py")


if __name__ == "__main__":
    main()
