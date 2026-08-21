import os
import joblib
import numpy as np
import pandas as pd
from django.conf import settings
from django.utils import timezone


# Cache the loaded model bundle in memory
_MODEL_BUNDLE = None


def get_model_path():
    """
    Locates the trained Random Forest model in the backend or project root.
    """
    base_dir = str(getattr(settings, 'BASE_DIR', ''))
    if base_dir:
        model_path = os.path.join(base_dir, "ml", "models", "resource_optimizer.pkl")
        if os.path.exists(model_path):
            return model_path

    # Fallback to relative path from this file
    fallback_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    model_path = os.path.join(fallback_dir, "ml", "models", "resource_optimizer.pkl")
    return model_path


def load_ml_model():
    """
    Loads and caches the Random Forest model, label encoder, and feature list.
    """
    global _MODEL_BUNDLE
    if _MODEL_BUNDLE is not None:
        return _MODEL_BUNDLE

    model_path = get_model_path()
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained ML model not found at: {model_path}")

    _MODEL_BUNDLE = joblib.load(model_path)
    return _MODEL_BUNDLE


def predict_resource_action(resource, extra_metrics=None):
    """
    Extracts features from a Resource model instance and predicts
    the recommended optimization action (scale_up, scale_down, no_action).
    """
    bundle = load_ml_model()
    model = bundle["model"]
    encoder = bundle["encoder"]
    features = bundle["features"]

    extra = extra_metrics or {}

    # Map Resource model fields to model features
    cpu = float(resource.cpu_usage)
    mem = float(resource.memory_usage)
    net = float(resource.network_usage)
    disk = float(resource.storage_usage)

    # Calculate utilization metric
    utilization = round((cpu * 0.5 + mem * 0.5), 2)

    # Defaults for auxiliary metrics based on resource type
    default_vcpu = 4 if resource.resource_type in ['VM', 'DATABASE'] else 2
    default_ram = 16 if resource.resource_type in ['VM', 'DATABASE'] else 8
    default_price = 0.0928 if resource.resource_type in ['VM', 'DATABASE'] else 0.0464

    feature_dict = {
        "cpu_usage": extra.get("cpu_usage", cpu),
        "memory_usage": extra.get("memory_usage", mem),
        "net_io": extra.get("net_io", net),
        "disk_io": extra.get("disk_io", disk),
        "vCPU": extra.get("vCPU", default_vcpu),
        "RAM_GB": extra.get("RAM_GB", default_ram),
        "price_per_hour": extra.get("price_per_hour", default_price),
        "latency_ms": extra.get("latency_ms", 100.0 if cpu > 70 else 25.0),
        "throughput": extra.get("throughput", 800.0),
        "cost": extra.get("cost", round(default_price * 720, 2)),
        "utilization": extra.get("utilization", utilization),
    }

    # Ensure strictly exact feature ordering as used during training
    X = pd.DataFrame([[feature_dict[feat] for feat in features]], columns=features)

    # Run inference
    pred_encoded = model.predict(X)[0]
    pred_proba = model.predict_proba(X)[0]
    predicted_class = encoder.inverse_transform([pred_encoded])[0]
    confidence = float(np.max(pred_proba))

    return {
        "resource_id": resource.resource_id,
        "resource_name": resource.resource_name,
        "prediction": predicted_class,
        "confidence": round(confidence, 4),
        "timestamp": timezone.now().isoformat(),
    }
