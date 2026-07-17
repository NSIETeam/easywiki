"""
Prometheus 监控指标暴露, 用于 Grafana 可视化
"""
import time
from typing import Dict
from fastapi import Request, Response
from orgmind.config_production import METRICS_ENABLED


# 内存中的轻量指标 (生产环境替换为 prometheus_client)
_metrics: Dict[str, float] = {
    "http_requests_total": 0,
    "http_request_duration_seconds_sum": 0,
    "retrieve_requests_total": 0,
    "retrieve_cache_hits_total": 0,
    "memory_writes_total": 0,
    "errors_total": 0,
}


async def metrics_middleware(request: Request, call_next):
    if not METRICS_ENABLED:
        return await call_next(request)

    _metrics["http_requests_total"] += 1
    start = time.monotonic()

    if request.url.path == "/api/v1/retrieve":
        _metrics["retrieve_requests_total"] += 1

    response = await call_next(request)
    elapsed = time.monotonic() - start
    _metrics["http_request_duration_seconds_sum"] += elapsed

    if response.status_code >= 500:
        _metrics["errors_total"] += 1

    return response


def get_metrics() -> Dict[str, float]:
    return dict(_metrics)


def render_prometheus_metrics() -> str:
    """输出 Prometheus text 格式"""
    lines = []
    for name, value in _metrics.items():
        lines.append(f"# HELP {name} OrgMind metric")
        lines.append(f"# TYPE {name} counter")
        lines.append(f"{name} {value}")
    return "\n".join(lines) + "\n"
