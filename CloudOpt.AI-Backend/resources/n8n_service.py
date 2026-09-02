import os
import json
import logging
import requests
from django.conf import settings
from .ml_service import predict_resource_action

logger = logging.getLogger(__name__)

# Default n8n production webhook URL (can be overridden via environment variable)
DEFAULT_N8N_WEBHOOK_URL = os.environ.get(
    'N8N_WEBHOOK_URL',
    'http://localhost:5678/webhook/cloud-optimization'
)


def generate_fallback_ai_analysis(resource, prediction, confidence):
    """
    Generates structured AI analysis based on prediction and resource telemetry
    if n8n response is asynchronous or lacks detailed fields.
    """
    pred = (prediction or 'no_action').lower()
    cpu = float(resource.cpu_usage)
    mem = float(resource.memory_usage)

    if pred == 'scale_up':
        return {
            "recommendation": f"Scale up {resource.resource_id} from current {resource.resource_type} configuration to higher compute tier.",
            "priority": "High" if cpu > 90 or mem > 90 else "Medium",
            "reason": f"Sustained heavy utilization detected (CPU: {cpu}%, RAM: {mem}%). Workload demands additional compute and memory headroom.",
            "risk": "High risk of latency degradation, request queue backlog, and possible service outage if traffic surges.",
            "what_if": "If scaled up, CPU saturation will drop below 60%, eliminating throughput bottlenecks and SLA violation risk."
        }
    elif pred == 'scale_down':
        return {
            "recommendation": f"Downsize or decommission {resource.resource_id} to eliminate unneeded compute capacity.",
            "priority": "Medium",
            "reason": f"Resource is severely underutilized with CPU at {cpu}% and RAM at {mem}%, generating unnecessary cloud spend.",
            "risk": "Zero risk to system reliability; current workload fits comfortably within a smaller instance tier.",
            "what_if": "Downsizing will yield immediate monthly FinOps cost reduction with no disruption to active traffic."
        }
    else:
        return {
            "recommendation": f"Maintain current provisioning for {resource.resource_id}.",
            "priority": "Low",
            "reason": f"Resource operates within the optimal efficiency threshold (CPU: {cpu}%, RAM: {mem}%).",
            "risk": "Minimal risk. System metrics remain balanced and stable.",
            "what_if": "No action required. Current resource allocation matches workload demands perfectly."
        }


def trigger_n8n_optimization(resource, extra_metrics=None, webhook_url=None):
    """
    1. Runs the existing Random Forest ML prediction on the resource.
    2. Builds the standardized JSON payload.
    3. POSTs the payload to n8n webhook (http://localhost:5678/webhook/cloud-optimization).
    4. Parses the AI Agent response and returns a structured result.
    """
    # 1. Run Random Forest ML prediction using existing ML service
    ml_result = predict_resource_action(resource, extra_metrics=extra_metrics)
    prediction = ml_result.get("prediction", "no_action")
    confidence = ml_result.get("confidence", 0.0)

    # 2. Build the exact JSON payload
    payload = {
        "resource_id": resource.resource_id,
        "resource_name": resource.resource_name,
        "cpu_usage": float(resource.cpu_usage),
        "memory_usage": float(resource.memory_usage),
        "storage_usage": float(resource.storage_usage),
        "network_usage": float(resource.network_usage),
        "prediction": prediction,
        "confidence": confidence,
    }

    target_url = webhook_url or DEFAULT_N8N_WEBHOOK_URL
    n8n_response_data = None
    n8n_connected = False

    # 3. POST to n8n webhook with reasonable timeout
    try:
        response = requests.post(
            target_url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=25
        )
        if response.status_code in [200, 201, 202]:
            n8n_connected = True
            try:
                n8n_response_data = response.json()
            except Exception:
                n8n_response_data = {"raw_response": response.text}
        else:
            logger.warning(f"n8n webhook returned HTTP {response.status_code}: {response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to connect to n8n webhook at {target_url}: {str(e)}")

    # 4. Extract or assemble AI analysis
    ai_analysis = None
    if n8n_response_data and isinstance(n8n_response_data, dict):
        # Case A: n8n returned structured ai_analysis
        if "ai_analysis" in n8n_response_data and isinstance(n8n_response_data["ai_analysis"], dict):
            ai_analysis = n8n_response_data["ai_analysis"]
        # Case B: n8n returned top-level fields
        elif "recommendation" in n8n_response_data:
            ai_analysis = {
                "recommendation": n8n_response_data.get("recommendation", ""),
                "priority": n8n_response_data.get("priority", "Medium"),
                "reason": n8n_response_data.get("reason", ""),
                "risk": n8n_response_data.get("risk", ""),
                "what_if": n8n_response_data.get("what_if", ""),
            }

    # Case C: Fallback to structured heuristics if n8n response is generic (e.g. "Workflow was started")
    if not ai_analysis:
        ai_analysis = generate_fallback_ai_analysis(resource, prediction, confidence)

    return {
        "resource_id": resource.resource_id,
        "prediction": prediction,
        "confidence": confidence,
        "ai_analysis": ai_analysis,
        "n8n_status": {
            "connected": n8n_connected,
            "webhook_url": target_url,
            "raw_response": n8n_response_data
        }
    }
