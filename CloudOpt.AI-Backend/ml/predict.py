"""
predict.py
==========
AI Cloud Resource Optimization - Prediction Script
---------------------------------------------------
Loads the trained Random Forest model and predicts the
optimization action for given cloud resource metrics.

Possible predictions:
  - scale_up    : Add more CPU/RAM to handle the load
  - scale_down  : Reduce resources to save cost
  - no_action   : Resource is running optimally

Run:
    python predict.py
"""

import os
import sys
import json
import joblib
import numpy as np
import pandas as pd

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "models", "resource_optimizer.pkl")
META_PATH  = os.path.join(BASE_DIR, "models", "model_metadata.json")


# ─────────────────────────────────────────────
# LOAD MODEL
# ─────────────────────────────────────────────
def load_model():
    if not os.path.exists(MODEL_PATH):
        print(f"[ERROR] Model not found at: {MODEL_PATH}")
        print("        Please run:  python train_model.py  first.")
        sys.exit(1)

    bundle = joblib.load(MODEL_PATH)
    model    = bundle["model"]
    encoder  = bundle["encoder"]
    features = bundle["features"]
    return model, encoder, features


# ─────────────────────────────────────────────
# PREDICT
# ─────────────────────────────────────────────
def predict(resource_data: dict) -> dict:
    """
    Accepts a dict of resource metrics and returns:
      {
        "predicted_action"    : "scale_up" | "scale_down" | "no_action",
        "prediction_confidence": 0.0 - 1.0,
        "all_class_probabilities": {...}
      }
    """
    model, encoder, features = load_model()

    # Build input DataFrame with correct column order
    row = {feat: resource_data.get(feat, 0.0) for feat in features}
    X = pd.DataFrame([row])

    # Predict
    pred_encoded   = model.predict(X)[0]
    pred_proba     = model.predict_proba(X)[0]
    predicted_class = encoder.inverse_transform([pred_encoded])[0]
    confidence      = float(np.max(pred_proba))

    # All class probabilities
    all_probs = {
        cls: round(float(prob), 4)
        for cls, prob in zip(encoder.classes_, pred_proba)
    }

    return {
        "predicted_action":         predicted_class,
        "prediction_confidence":    round(confidence, 4),
        "all_class_probabilities":  all_probs,
    }


# ─────────────────────────────────────────────
# DEMO: TEST WITH 3 EXAMPLE INPUTS
# ─────────────────────────────────────────────
EXAMPLES = [
    {
        "label": "HIGH Resource Usage (Overloaded Server)",
        "data": {
            "cpu_usage":      95.0,
            "memory_usage":   92.0,
            "net_io":        1200.0,
            "disk_io":        800.0,
            "vCPU":              4,
            "RAM_GB":           16,
            "price_per_hour": 0.192,
            "latency_ms":     450.0,
            "throughput":     120.0,
            "cost":           138.24,
            "utilization":     93.5,
        }
    },
    {
        "label": "LOW Resource Usage (Idle / Underutilized)",
        "data": {
            "cpu_usage":       4.0,
            "memory_usage":    6.0,
            "net_io":          15.0,
            "disk_io":          8.0,
            "vCPU":              2,
            "RAM_GB":            4,
            "price_per_hour": 0.0464,
            "latency_ms":      12.0,
            "throughput":    1800.0,
            "cost":             5.57,
            "utilization":      5.0,
        }
    },
    {
        "label": "MEDIUM Resource Usage (Running Optimally)",
        "data": {
            "cpu_usage":      52.0,
            "memory_usage":   58.0,
            "net_io":        320.0,
            "disk_io":       150.0,
            "vCPU":              4,
            "RAM_GB":            8,
            "price_per_hour": 0.0928,
            "latency_ms":     85.0,
            "throughput":    750.0,
            "cost":           44.54,
            "utilization":    55.0,
        }
    },
]


def run_demo():
    print("\n" + "#"*65)
    print("  AI Cloud Resource Optimization - Prediction Demo")
    print("#"*65)

    # Show model metadata
    if os.path.exists(META_PATH):
        with open(META_PATH) as f:
            meta = json.load(f)
        print(f"\n  Model     : {meta['model_type']}")
        print(f"  Accuracy  : {meta['metrics']['accuracy']*100:.2f}%")
        print(f"  F1-Score  : {meta['metrics']['f1_score']}")
        print(f"  Classes   : {meta['classes']}")
        print(f"  Features  : {meta['features']}")

    print("\n" + "="*65)

    for i, example in enumerate(EXAMPLES, 1):
        label  = example["label"]
        data   = example["data"]
        result = predict(data)

        action     = result["predicted_action"]
        confidence = result["prediction_confidence"]
        all_probs  = result["all_class_probabilities"]

        # Choose emoji/icon based on action
        icon = {"scale_up": "[UP]", "scale_down": "[DOWN]", "no_action": "[OK]"}.get(action, "[?]")

        print(f"\n  Example {i}: {label}")
        print(f"  {'-'*60}")
        print(f"  Input metrics:")
        print(f"    CPU Usage      : {data['cpu_usage']}%")
        print(f"    Memory Usage   : {data['memory_usage']}%")
        print(f"    Net I/O        : {data['net_io']} Mbps")
        print(f"    Disk I/O       : {data['disk_io']} MB/s")
        print(f"    Utilization    : {data['utilization']}%")
        print(f"    Cost           : ${data['cost']}")
        print(f"\n  Prediction Result:")
        print(f"    {icon} Action     : {action.upper()}")
        print(f"       Confidence : {confidence*100:.1f}%")
        print(f"       Probabilities:")
        for cls, prob in sorted(all_probs.items(), key=lambda x: -x[1]):
            bar = "#" * int(prob * 20)
            print(f"         {cls:<15}: {prob*100:5.1f}%  |{bar}")

    print("\n" + "="*65)
    print("  Demo complete. All 3 examples predicted successfully.")
    print("="*65 + "\n")


if __name__ == "__main__":
    run_demo()
